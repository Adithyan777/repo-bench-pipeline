"""Graph self-verification (docs/pipeline-2-knowledge.md): sample edges, re-derive them by an
independent code path, report precision per edge type + mismatches.

imports/contains/inherits: second AST parse; calls: independent call-site resolution
(same target module, not just same name); tested_by: raw coverage contexts must cover
a line in the function span. Symbol existence is optionally checked by importing inside
the container; import failures are reported apart from attribute mismatches.
"""

from __future__ import annotations

import ast
import json
import math
from dataclasses import dataclass, field
from pathlib import Path

from pipeline.config import DEFAULT, Config
from pipeline.docker.runner import fresh_workdir, run_in_container
from pipeline.ecosystems.symbols import module_name


@dataclass
class _Ctx:
    repo: Path
    symbols: dict
    coverage_contexts: dict
    quals: set[str]  # every function+class qualname in the repo
    modules: set[str]  # every module name
    packages: set[str]  # module names that are packages (for relative imports)
    cache: dict = field(default_factory=dict)  # file -> (text, tree)


def verify_graph(
    repo: Path,
    graph: dict,
    symbols: dict,
    coverage_contexts: dict | None = None,
    image: str | None = None,
    config: Config = DEFAULT,
) -> dict:
    repo = Path(repo)
    ctx = _Ctx(
        repo=repo,
        symbols=symbols,
        coverage_contexts=coverage_contexts or {},
        quals={c["qualname"] for c in symbols["classes"]}
        | {f["qualname"] for f in symbols["functions"]},
        modules={m["name"] for m in symbols["modules"]},
        packages={m["name"] for m in symbols["modules"] if m["is_package"]},
    )
    sample = _sample(graph["edges"], config.graph.verification_sample_edges)

    by_type: dict[str, dict] = {}
    mismatches: list[dict] = []
    for edge in sample:
        verdict, reason = _recheck(edge, ctx)
        stats = by_type.setdefault(
            edge["type"], {"sampled": 0, "confirmed": 0, "mismatch": 0, "unverifiable": 0}
        )
        stats["sampled"] += 1
        stats[verdict] += 1
        if verdict == "mismatch":
            mismatches.append(
                {
                    "type": edge["type"],
                    "source": edge["source"],
                    "target": edge["target"],
                    "reason": reason,
                }
            )
    for stats in by_type.values():
        decided = stats["confirmed"] + stats["mismatch"]
        stats["precision"] = round(stats["confirmed"] / decided, 3) if decided else None

    return {
        "sample_size": len(sample),
        "sample_edges_requested": config.graph.verification_sample_edges,
        "by_edge_type": dict(sorted(by_type.items())),
        "symbol_existence": _check_symbols(repo, graph, image),
        "mismatches": sorted(mismatches, key=lambda m: (m["type"], m["source"], m["target"])),
    }


def _edge_key(edge: dict) -> tuple:
    return (edge["type"], edge["source"], edge["target"], edge["evidence"]["line"])


def _sample(edges: list[dict], budget: int) -> list[dict]:
    """Deterministic sample: sorted edges, first ``per_type`` of each edge type."""
    by_type: dict[str, list[dict]] = {}
    for edge in sorted(edges, key=_edge_key):
        by_type.setdefault(edge["type"], []).append(edge)
    if not by_type:
        return []
    per_type = max(1, math.ceil(budget / len(by_type)))
    picked: list[dict] = []
    for group in by_type.values():
        picked.extend(group[:per_type])
    return picked[:budget] if budget else picked


# --- per-edge re-derivation ---------------------------------------------------


def _recheck(edge: dict, ctx: _Ctx) -> tuple[str, str]:
    handler = {
        "imports": _recheck_import,
        "contains": _recheck_contains,
        "inherits": _recheck_inherits,
        "calls": _recheck_calls,
        "tested_by": _recheck_tested_by,
    }.get(edge["type"])
    if handler is None:
        return "unverifiable", "unknown edge type"
    return handler(edge, ctx)


def _recheck_import(edge: dict, ctx: _Ctx) -> tuple[str, str]:
    """Second parse of the file's imports (absolute + relative); edge target must be among
    the resolved intra-repo modules."""
    _, tree = _load(ctx, edge["evidence"]["file"])
    if tree is None:
        return "unverifiable", "unparseable"
    module = module_name(ctx.repo, ctx.repo / edge["evidence"]["file"])
    targets: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                targets |= {".".join(parts[:i]) for i in range(1, len(parts) + 1)} & ctx.modules
        elif isinstance(node, ast.ImportFrom):
            source = _import_source(node, module, ctx)
            if not source:
                continue
            if source in ctx.modules:
                targets.add(source)
            targets |= {f"{source}.{a.name}" for a in node.names} & ctx.modules
    if edge["target"] in targets:
        return "confirmed", ""
    return "mismatch", f"no import of {edge['target']} in {edge['evidence']['file']}"


def _recheck_contains(edge: dict, ctx: _Ctx) -> tuple[str, str]:
    defined = _defined_qualnames(ctx, edge["evidence"]["file"])
    if edge["target"] in defined:
        return "confirmed", ""
    return "mismatch", f"{edge['target']} not defined in {edge['evidence']['file']}"


def _recheck_inherits(edge: dict, ctx: _Ctx) -> tuple[str, str]:
    _, tree = _load(ctx, edge["evidence"]["file"])
    if tree is None:
        return "unverifiable", "unparseable"
    module = module_name(ctx.repo, ctx.repo / edge["evidence"]["file"])
    classes = [n for n in _lookup_all(tree, module, edge["source"]) if isinstance(n, ast.ClassDef)]
    if not classes:
        return "mismatch", f"class {edge['source']} not found"
    base_leaf = edge["target"].split(".")[-1]
    for cls in classes:
        if any(base_leaf == ast.unparse(b).split(".")[-1] for b in cls.bases):
            return "confirmed", ""
    return "mismatch", f"{edge['source']} does not inherit {base_leaf}"


def _recheck_calls(edge: dict, ctx: _Ctx) -> tuple[str, str]:
    _, tree = _load(ctx, edge["evidence"]["file"])
    if tree is None:
        return "unverifiable", "unparseable"
    module = module_name(ctx.repo, ctx.repo / edge["evidence"]["file"])
    funcs = [
        n
        for n in _lookup_all(tree, module, edge["source"])
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    if not funcs:
        return "mismatch", f"caller {edge['source']} not found"
    tables = _import_tables(tree, module, ctx)
    enclosing = edge["source"].rsplit(".", 1)[0]  # a method's class, if any
    enclosing = enclosing if enclosing in ctx.quals else None
    targets: set[str] = set()
    for func in funcs:
        for call in _own_calls(func):
            resolved = _resolve_call(call.func, tables, ctx, enclosing)
            if resolved:
                targets.add(resolved)
    if edge["target"] in targets:
        return "confirmed", ""
    resolved = sorted(targets)[:4]
    return "mismatch", f"{edge['source']} does not resolve a call to {edge['target']} ({resolved})"


def _recheck_tested_by(edge: dict, ctx: _Ctx) -> tuple[str, str]:
    fn = next((f for f in ctx.symbols["functions"] if f["qualname"] == edge["source"]), None)
    if fn is None:
        return "mismatch", f"unknown function {edge['source']}"
    span = set(range(fn["line"], fn["end_line"] + 1))
    base = edge["target"]  # base nodeid; coverage contexts may carry a [param] suffix
    file_data = ctx.coverage_contexts.get("files", {}).get(fn["file"], {})
    for line_str, contexts in file_data.get("contexts", {}).items():
        if int(line_str) in span and any(c.split("[", 1)[0] == base for c in contexts if c):
            return "confirmed", ""
    if not ctx.coverage_contexts:
        return "unverifiable", "no coverage contexts"
    return "mismatch", f"{base} did not cover {edge['source']}"


# --- independent call resolution ----------------------------------------------


def _import_tables(tree: ast.Module, module: str, ctx: _Ctx) -> dict:
    """Independent rebuild of the module's name-resolution tables (absolute + relative)."""
    from_imports: dict[str, str] = {}
    aliases: dict[str, str] = {}
    top_defs: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.asname:
                    aliases[a.asname] = a.name
                else:
                    aliases[a.name.split(".")[0]] = a.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom):
            source = _import_source(node, module, ctx)
            if source is None:
                continue
            for a in node.names:
                from_imports[a.asname or a.name] = f"{source}.{a.name}"
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            top_defs[node.name] = f"{module}.{node.name}"
    return {"from": from_imports, "alias": aliases, "top": top_defs}


def _import_source(node: ast.ImportFrom, module: str, ctx: _Ctx) -> str | None:
    if node.level == 0:
        return node.module
    parts = module.split(".")
    if module not in ctx.packages:
        parts = parts[:-1]  # a module's package is its parent
    drop = node.level - 1
    if drop > len(parts):
        return None
    base = ".".join(parts[: len(parts) - drop] if drop else parts)
    if not base:
        return node.module
    return f"{base}.{node.module}" if node.module else base


def _resolve_call(func, tables: dict, ctx: _Ctx, enclosing: str | None) -> str | None:
    if isinstance(func, ast.Name):
        cand = tables["top"].get(func.id) or tables["from"].get(func.id)
        return cand if cand in ctx.quals else None
    if isinstance(func, ast.Attribute):
        attrs: list[str] = []
        node: ast.AST = func
        while isinstance(node, ast.Attribute):
            attrs.append(node.attr)
            node = node.value
        if not isinstance(node, ast.Name):
            return None
        attrs.append(node.id)
        attrs.reverse()
        base = attrs[0]
        if base == "self" and enclosing and len(attrs) == 2:
            cand = f"{enclosing}.{attrs[1]}"
            return cand if cand in ctx.quals else None
        if base in tables["alias"]:
            head = tables["alias"][base].split(".")
        elif base in tables["from"] and tables["from"][base] in ctx.modules:
            head = tables["from"][base].split(".")
        else:
            return None
        cand = ".".join(head + attrs[1:])
        return cand if cand in ctx.quals else None
    return None


# --- container symbol existence -----------------------------------------------


def _check_symbols(repo, graph, image) -> dict:
    if image is None:
        return {"checked": 0, "present": 0, "missing_attr": [], "skipped": "no image"}
    targets = _symbol_targets(graph)
    probe = _PROBE.format(payload=json.dumps(targets))
    with fresh_workdir(repo) as work:
        (work / "_kn_probe.py").write_text(probe)
        result = run_in_container(work, "python _kn_probe.py", image)
    try:
        report = json.loads(result.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {"checked": len(targets), "error": result.stderr[:400], "present": 0}
    present = report["present"]
    missing_attr = report["missing_attr"]
    decided = present + len(missing_attr)
    return {
        "checked": decided,
        "present": present,
        "missing_attr": sorted(missing_attr),
        "unimportable_modules": sorted(report["import_errors"]),
        "precision": round(present / decided, 3) if decided else None,
    }


def _symbol_targets(graph: dict) -> list[dict]:
    out: list[dict] = []
    for node in graph["nodes"]:
        if node["type"] == "module":
            out.append({"module": node["id"], "attr": None})
        elif node["type"] == "class":
            module, _, name = node["id"].rpartition(".")
            out.append({"module": module, "attr": name})
        elif node["type"] == "function" and "." in node["id"]:
            module, _, name = node["id"].rpartition(".")
            out.append({"module": module, "attr": name})
    seen, uniq = set(), []
    for item in sorted(out, key=lambda d: (d["module"], d["attr"] or "")):
        key = (item["module"], item["attr"])
        if key not in seen:
            seen.add(key)
            uniq.append(item)
    return uniq


_PROBE = '''
import importlib, json
targets = json.loads("""{payload}""")
present, missing_attr, import_errors = 0, [], set()
for t in targets:
    try:
        mod = importlib.import_module(t["module"])
    except Exception:
        import_errors.add(t["module"])
        continue
    if t["attr"] is None or hasattr(mod, t["attr"]):
        present += 1
    else:
        missing_attr.append(t["module"] + "::" + t["attr"])
print(json.dumps({{"present": present, "missing_attr": missing_attr,
                  "import_errors": sorted(import_errors)}}))
'''


# --- parsing helpers ----------------------------------------------------------


def _load(ctx: _Ctx, rel: str) -> tuple[str, ast.Module | None]:
    if rel not in ctx.cache:
        text = (ctx.repo / rel).read_text(errors="replace")
        try:
            tree: ast.Module | None = ast.parse(text)
        except SyntaxError:
            tree = None
        ctx.cache[rel] = (text, tree)
    return ctx.cache[rel]


def _defined_qualnames(ctx: _Ctx, rel: str) -> set[str]:
    _, tree = _load(ctx, rel)
    if tree is None:
        return set()
    module = module_name(ctx.repo, ctx.repo / rel)
    out: set[str] = set()

    def visit(body, parent):
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out.add(f"{parent}.{node.name}")
            elif isinstance(node, ast.ClassDef):
                out.add(f"{parent}.{node.name}")
                visit(node.body, f"{parent}.{node.name}")

    visit(tree.body, module)
    return out


def _lookup_all(tree, module: str, qualname: str) -> list:
    """All def/class nodes matching a qualname path (a name may be redefined; return all)."""
    parts = qualname[len(module) + 1 :].split(".") if qualname.startswith(module + ".") else []
    if not parts:
        return []
    bodies = [tree.body]
    matched: list = []
    for part in parts:
        matched = [
            n
            for body in bodies
            for n in body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and n.name == part
        ]
        if not matched:
            return []
        bodies = [n.body for n in matched]
    return matched


def _own_calls(func):
    """Call nodes made directly by `func`, not by nested defs."""
    calls: list = []

    def walk(node):
        for _field, value in ast.iter_fields(node):
            for item in value if isinstance(value, list) else [value]:
                if not isinstance(item, ast.AST):
                    continue
                if isinstance(item, ast.Call):
                    calls.append(item)
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    continue
                walk(item)

    walk(func)
    return calls


def write_verification(report: dict, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True))
    return path
