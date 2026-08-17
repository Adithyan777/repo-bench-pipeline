"""Step 4.2: write an Open Knowledge Format (OKF v0.2) bundle for the repo.

The bundle under ``knowledge/.okf/`` is a directory of cross-linked Markdown pages
with YAML frontmatter:

    .okf/
      index.md                       (reserved) progressive-disclosure listing
      repo.md                        entrypoints, test command, layout, conventions
      modules/<mod>.md               purpose + public API + callers/callees + tests
      functions/<mod>/<qualname>.md   contract + links to callers/callees/tests
      log.md                         (reserved) generation log

The STATIC skeleton (structure, signatures, resources, callers/callees/tests) comes
entirely from repo_graph.json + symbol_index -- deterministic, no model. The BIG model
writes ONLY the module purpose and the per-function contract; each claim is persisted by
content hash so a rerun is 0-token and byte-identical. ``okf_verify`` then re-checks the
model's claims against the AST/graph and stamps ``verified``.

Determinism: pages are emitted in sorted order and ``generated.at`` is pinned to the base
commit's date (stable for a given repo state), so two runs are byte-identical.

Frontmatter values are emitted as inline JSON (``key: <json>``) -- valid YAML that any
consumer parses, and that ``parse_frontmatter`` reads back with ``json.loads``.
"""

from __future__ import annotations

import builtins
import hashlib
import json
import posixpath
import re
import shutil
import subprocess
from pathlib import Path

from pipeline.config import Config

MODULE_PURPOSE_STEP = "p2.okf.module_purpose"
FUNCTION_CONTRACTS_STEP = "p2.okf.function_contracts"
PROMPT_VERSION = "s7.1"

_FIELD_ORDER = [
    "okf_version", "type", "title", "description", "resource",
    "tags", "sources", "generated", "verified", "status", "stale_after",
]  # fmt: skip


# --- frontmatter (JSON-valued YAML) -------------------------------------------


def emit_frontmatter(fm: dict) -> str:
    ordered = [k for k in _FIELD_ORDER if k in fm] + [k for k in fm if k not in _FIELD_ORDER]
    lines = "\n".join(f"{k}: {json.dumps(fm[k])}" for k in ordered)
    return f"---\n{lines}\n---\n"


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """(frontmatter dict, body). Empty dict if there is no ``---`` block."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    fm: dict = {}
    for line in text[4:end].splitlines():
        if not line.strip():
            continue
        key, _, rest = line.partition(": ")
        try:
            fm[key] = json.loads(rest)
        except json.JSONDecodeError:
            fm[key] = rest
    return fm, text[end + 5 :]


def page(fm: dict, body: str) -> str:
    return emit_frontmatter(fm) + body


# --- graph model --------------------------------------------------------------


class Graph:
    """Read-only views over repo_graph.json used to build the skeleton."""

    def __init__(self, graph: dict):
        self.nodes = {n["id"]: n for n in graph["nodes"]}
        self.edges = graph["edges"]
        self._callers: dict[str, list[str]] = {}
        self._callees: dict[str, list[str]] = {}
        self._contains: dict[str, list[str]] = {}
        for e in self.edges:
            if e["type"] == "calls":
                self._callers.setdefault(e["target"], []).append(e["source"])
                self._callees.setdefault(e["source"], []).append(e["target"])
            elif e["type"] == "contains":
                self._contains.setdefault(e["source"], []).append(e["target"])

    def callers(self, qual: str) -> list[str]:
        return sorted(set(self._callers.get(qual, [])))

    def callees(self, qual: str) -> list[str]:
        return sorted(set(self._callees.get(qual, [])))

    def tests(self, qual: str) -> list[str]:
        return sorted(self.nodes.get(qual, {}).get("tested_by", []))

    def module_members(self, module: str) -> list[dict]:
        """Functions/classes/methods whose id sits under ``module``, sorted by id."""
        out = []
        for nid, n in self.nodes.items():
            if n["type"] in ("function", "method", "class") and _module_of(nid, n) == module:
                out.append(n)
        return sorted(out, key=lambda n: n["id"])


def _module_of(nid: str, node: dict) -> str:
    if node["type"] == "module":
        return nid
    if node["type"] == "method":
        return nid.rsplit(".", 2)[0]
    return nid.rsplit(".", 1)[0]


def modules(graph: Graph) -> list[dict]:
    return sorted(
        (n for n in graph.nodes.values() if n["type"] == "module"), key=lambda n: n["id"]
    )


def select_function_pages(graph: Graph, config: Config) -> list[dict]:
    """public functions/methods + any whose complexity >= min_private_page_complexity,
    capped at max_function_pages (highest-complexity first). Trivial private helpers and
    dunders are left to their module page."""
    okf = config.okf
    worthy = [
        n
        for n in graph.nodes.values()
        if n["type"] in ("function", "method")
        and (n["is_public"] or (n.get("complexity") or 0) >= okf.min_private_page_complexity)
    ]
    worthy.sort(key=lambda n: (not n["is_public"], -(n.get("complexity") or 0), n["id"]))
    picked = worthy[: okf.max_function_pages]
    return sorted(picked, key=lambda n: n["id"])


# --- resources / links --------------------------------------------------------


def resource(node: dict) -> str:
    start = node.get("line", 1)
    end = node.get("end_line", start)
    return f"/{node['file']}#L{start}-L{end}"


def _module_page_rel(module: str) -> str:
    return f"modules/{module}.md"


def _function_page_rel(qual: str, module: str) -> str:
    return f"functions/{module}/{qual}.md"


def _link(title: str, rel_from: str, rel_to: str) -> str:
    return f"[{title}]({_relpath(rel_from, rel_to)})"


def _relpath(rel_from: str, rel_to: str) -> str:
    return posixpath.relpath(rel_to, posixpath.dirname(rel_from))


# --- LLM claims (purpose + contracts), persisted by content hash --------------

_PURPOSE_SCHEMA = {
    "type": "object",
    "properties": {"purpose": {"type": "string"}},
    "required": ["purpose"],
}

_CONTRACTS_SCHEMA = {
    "type": "object",
    "properties": {
        "contracts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "qualname": {"type": "string"},
                    "inputs": {"type": "string"},
                    "outputs": {"type": "string"},
                    "raises": {"type": "array", "items": {"type": "string"}},
                    "side_effects": {"type": "string"},
                    "invariants": {"type": "string"},
                },
                "required": ["qualname", "inputs", "outputs", "raises", "side_effects"],
            },
        }
    },
    "required": ["contracts"],
}


def _key(config: Config, *parts: str) -> str:
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()[: 16]


def _cached(llm, decisions, key, step, prompt, schema):
    if decisions is not None and key in decisions:
        return decisions[key]
    if llm is None:
        return None
    result = llm.complete_json(step, [{"role": "user", "content": prompt}], schema)
    if decisions is not None:
        decisions[key] = result
    return result


def _purpose_prompt(module: str, node: dict, members: list[dict], feedback: str = "") -> str:
    api = "\n".join(
        f"- {m['id'].split('.')[-1]}: {m.get('signature', '')} {(m.get('docstring') or '')[:120]}"
        for m in members
        if m["is_public"]
    )
    return (
        f"Summarize the PURPOSE of the Python module `{module}` in 1-3 sentences for an "
        f"engineer navigating the codebase. Module docstring: {node.get('docstring') or '(none)'}\n"
        f"Public API:\n{api or '(none)'}\n"
        "Describe what the module is for, not each function. No code. Ground every statement "
        "in the docstring and the listed API ONLY; do NOT infer the purpose from the module "
        "name. If the module exposes no meaningful public API or the source does not support "
        "a specific claim, say so briefly (e.g. 'internal helpers with no public API')." + feedback
    )


_IDENT_RE = re.compile(r"`([A-Za-z_][\w.]*)`")


def _module_identifiers(module: str, members: list[dict]) -> set[str]:
    ids = set(module.split("."))
    for m in members:
        ids.add(m["id"].split(".")[-1])
    return ids


def _hallucinated_identifiers(purpose: str, allowed: set[str]) -> list[str]:
    """Backticked code identifiers in the purpose that are not in the module (and not a
    Python builtin) — a name the model invented rather than read from the source."""
    bad = []
    for tok in _IDENT_RE.findall(purpose):
        leaf = tok.split(".")[-1]
        if leaf in allowed or hasattr(builtins, leaf):
            continue
        bad.append(tok)
    return sorted(set(bad))


def _contracts_prompt(module: str, fns: list[tuple[dict, str]]) -> str:
    blocks = []
    for n, src in fns:
        blocks.append(f"### {n['id']}\nsignature: {n.get('signature', '')}\n{src}")
    return (
        f"For each function of module `{module}` below, write a behavioral contract: "
        "inputs (what each parameter means), outputs (what is returned), raises (list of "
        "exception TYPE NAMES it can raise, [] if none), side_effects (\"none\" or a short "
        "phrase), invariants (a property that always holds, or \"\"). Base every field ONLY "
        "on the code shown. Return one entry per qualname.\n\n" + "\n\n".join(blocks)
    )


def _function_source(repo: Path, node: dict) -> str:
    try:
        lines = (repo / node["file"]).read_text(errors="replace").splitlines()
    except OSError:
        return ""
    return "\n".join(lines[node["line"] - 1 : node.get("end_line", node["line"])])


def _chunks(fns: list[tuple[dict, str]], config: Config) -> list[list[tuple[dict, str]]]:
    budget = config.llm.okf_module_chunk_tokens * config.agent.chars_per_token
    out, cur, size = [], [], 0
    for item in fns:
        n = len(item[1])
        if cur and size + n > budget:
            out.append(cur)
            cur, size = [], 0
        cur.append(item)
        size += n
    if cur:
        out.append(cur)
    return out


def author_claims(graph: Graph, repo: Path, pages: list[dict], llm, config, decisions):
    """module -> purpose; qualname -> contract.

    LLM calls are batched per module and CHUNKED so a module's contracts never exceed
    ``llm.okf_module_chunk_tokens`` in one prompt. Each call's decision key is the hash of
    the exact rendered prompt (+ model + prompt version), so a prompt change re-runs only
    the affected call and everything else is reused 0-token. A chunk's returned contracts
    are scoped to that chunk's qualnames (the model cannot leak entries for other funcs)."""
    by_module: dict[str, list[dict]] = {}
    for n in pages:
        by_module.setdefault(_module_of(n["id"], n), []).append(n)
    purposes: dict[str, str] = {}
    contracts: dict[str, dict] = {}
    model = config.model_for(MODULE_PURPOSE_STEP)
    for module in sorted({_module_of(m["id"], m) for m in modules(graph)} | set(by_module)):
        mnode = graph.nodes.get(module, {"docstring": None})
        members = graph.module_members(module)
        allowed = _module_identifiers(module, members)
        prompt = _purpose_prompt(module, mnode, members)
        pkey = _key(config, PROMPT_VERSION, model, "purpose", prompt)
        res = _cached(llm, decisions, pkey, MODULE_PURPOSE_STEP, prompt, _PURPOSE_SCHEMA)
        if res:
            bad = _hallucinated_identifiers(res["purpose"], allowed)
            if bad:  # names the model invented -> regenerate once with the offenders named
                fb = f"\n\nDo NOT mention these names; not in this module: {', '.join(bad)}."
                prompt2 = _purpose_prompt(module, mnode, members, fb)
                key2 = _key(config, PROMPT_VERSION, model, "purpose", prompt2)
                res2 = _cached(llm, decisions, key2, MODULE_PURPOSE_STEP, prompt2, _PURPOSE_SCHEMA)
                if res2 and not _hallucinated_identifiers(res2["purpose"], allowed):
                    res = res2
                else:
                    res = None  # still hallucinating -> no purpose rather than a wrong one
            if res:
                purposes[module] = res["purpose"]
        fns = [(n, _function_source(repo, n)) for n in by_module.get(module, [])]
        for chunk in _chunks(fns, config):
            chunk_quals = {n["id"] for n, _ in chunk}
            # Chunk-level contract cache keyed by the per-function spans in the chunk, so a
            # source change re-runs only the chunk it touches; unrelated chunks reuse.
            ckey = _key(config, PROMPT_VERSION, "contracts", module,
                        *[f"{n['id']}:{src}" for n, src in chunk])
            res = _cached(llm, decisions, ckey, FUNCTION_CONTRACTS_STEP,
                          _contracts_prompt(module, chunk), _CONTRACTS_SCHEMA)
            for c in (res or {}).get("contracts", []):
                if c["qualname"] in chunk_quals:  # scope output to this chunk's functions
                    contracts[c["qualname"]] = c
    return purposes, contracts


# --- page rendering -----------------------------------------------------------


def _tags(module: str) -> list[str]:
    return sorted(set(module.split(".")))


def _provenance(config: Config) -> dict:
    return {"by": config.okf.generated_by_actor.format(model=config.model_for(MODULE_PURPOSE_STEP))}


def _member_link(graph, page_ids, rel_from, qual) -> str:
    """A markdown link to qual's page if it has one, else inline code."""
    if qual in page_ids:
        module = _module_of(qual, graph.nodes[qual])
        return _link(qual, rel_from, _function_page_rel(qual, module))
    return f"`{qual}`"


def render_module(graph, module, mnode, members, purpose, page_ids, at, config) -> str:
    rel = _module_page_rel(module)
    fm = {
        "type": "python-module",
        "title": module,
        "description": (purpose or mnode.get("docstring") or module).split("\n")[0][:200],
        "resource": f"/{mnode['file']}#L1",
        "sources": [{"resource": f"/{mnode['file']}#L1"}],
        "tags": _tags(module),
        "generated": {**_provenance(config), "at": at},
        "verified": [],
        "status": config.okf.unverified_status,
    }
    lines = [f"# Module `{module}`\n", "## Purpose\n" + (purpose or "_(no summary)_") + "\n"]
    fns = [m for m in members if m["type"] in ("function", "method")]
    documented = [m for m in fns if m["id"] in page_ids]
    summarized = [m for m in fns if m["id"] not in page_ids]
    if documented:
        lines.append("## API\n")
        for m in documented:
            link = _member_link(graph, page_ids, rel, m["id"])
            lines.append(f"- {link} — `{m.get('signature', m['id'].split('.')[-1])}`")
        lines.append("")
    if summarized:
        lines.append("## Internal helpers\n")
        for m in summarized:
            lines.append(f"- `{m.get('signature', m['id'].split('.')[-1])}`")
        lines.append("")
    callees = sorted({c for m in members for c in graph.callees(m["id"])})
    if callees:
        lines.append("## Calls\n" + ", ".join(f"`{c}`" for c in callees) + "\n")
    tests = sorted({t for m in members for t in graph.tests(m["id"])})
    if tests:
        lines.append("## Tested by\n" + "\n".join(f"- `{t}`" for t in tests) + "\n")
    return page(fm, "\n".join(lines))


def render_function(graph, node, module, contract, page_ids, at, config) -> str:
    rel = _function_page_rel(node["id"], module)
    leaf = node["id"].split(".")[-1]
    fm = {
        "type": "python-function",
        "title": leaf,
        "description": (
            node.get("docstring") or (contract or {}).get("outputs") or leaf
        ).split("\n")[0][:200],
        "resource": resource(node),
        "sources": [{"resource": resource(node)}],
        "tags": _tags(module),
        "generated": {**_provenance(config), "at": at},
        "verified": [],
        "status": config.okf.unverified_status,
    }
    lines = [f"# `{node['id']}`\n", f"`{node.get('signature', leaf)}`\n"]
    if node.get("docstring"):
        lines.append("> " + node["docstring"].replace("\n", "\n> ") + "\n")
    c = contract or {}
    lines.append("## Contract\n")
    lines.append(f"- **inputs**: {c.get('inputs', '_(unspecified)_')}")
    lines.append(f"- **outputs**: {c.get('outputs', '_(unspecified)_')}")
    lines.append(f"- **raises**: {', '.join(c.get('raises') or []) or 'none'}")
    lines.append(f"- **side_effects**: {c.get('side_effects', 'unspecified')}")
    if c.get("invariants"):
        lines.append(f"- **invariants**: {c['invariants']}")
    lines.append("")
    for label, ids in (("Callers", graph.callers(node["id"])),
                       ("Callees", graph.callees(node["id"]))):
        present = [i for i in ids if i in graph.nodes]
        if present:
            links = ", ".join(_member_link(graph, page_ids, rel, i) for i in present)
            lines.append(f"## {label}\n{links}\n")
    tests = graph.tests(node["id"])
    if tests:
        lines.append("## Tested by\n" + "\n".join(f"- `{t}`" for t in tests) + "\n")
    return page(fm, "\n".join(lines))


def render_repo(ctx, graph, at, config) -> str:
    repo_name = ctx.run_dir.name
    test_cmd = _test_command(ctx)
    mods = modules(graph)
    fm = {
        "type": "python-repo",
        "title": repo_name,
        "description": f"Knowledge bundle for {repo_name} ({len(mods)} modules).",
        "resource": "/",
        "tags": [repo_name],
        "generated": {**_provenance(config), "at": at},
        "verified": [],
        "status": config.okf.unverified_status,
    }
    lines = [f"# `{repo_name}`\n", f"- **test command**: `{test_cmd}`",
             f"- **modules**: {len(mods)}\n", "## Layout\n"]
    for m in mods:
        lines.append(f"- `{m['id']}` — `{m['file']}`")
    return page(fm, "\n".join(lines))


def _first_line(text: str | None, fallback: str = "") -> str:
    return (text or fallback).split("\n")[0][:160]


def render_index(ctx, graph, pages, purposes, config) -> str:
    """Reserved page: no ``generated`` frontmatter (only okf_version), a progressive-
    disclosure listing as ``* [title](./path) - description``."""
    repo_name = ctx.run_dir.name
    fm = {"okf_version": config.okf.okf_version}
    lines = [f"# OKF bundle — `{repo_name}`\n",
             f"OKF v{config.okf.okf_version} progressive-disclosure knowledge for `{repo_name}`.\n",
             "## Start here\n",
             "* [Repository overview](./repo.md) - test command, layout and modules\n",
             "## Modules\n"]
    for m in modules(graph):
        desc = _first_line(purposes.get(m["id"]) or m.get("docstring"), "module")
        lines.append(f"* [{m['id']}](./{_module_page_rel(m['id'])}) - {desc}")
    lines.append(f"\n## Function pages\n\n{len(pages)} function contracts under `functions/`.")
    return page(fm, "\n".join(lines))


def render_log(ctx, n_modules: int, n_functions: int, at, config) -> str:
    """Reserved page: a date-grouped generation log."""
    model = config.model_for(MODULE_PURPOSE_STEP)
    date = at.split("T")[0] if at else "unknown-date"
    lines = ["# Log\n", f"## {date}\n",
             f"- generated by `pipeline/{model}`: repo.md, {n_modules} module pages, "
             f"{n_functions} function pages."]
    return "\n".join(lines) + "\n"


def _test_command(ctx) -> str:
    path = ctx.hygiene_dir / "test_command.txt"
    if path.is_file():
        return path.read_text().strip().splitlines()[0] if path.read_text().strip() else ""
    return ctx.adapter.test_command(ctx.repo)


def _base_at(ctx) -> str:
    base = ""
    pb = ctx.hygiene_dir / "pipeline_base.json"
    if pb.is_file():
        base = json.loads(pb.read_text()).get("base_sha", "")
    if base and (ctx.repo / ".git").exists():
        try:
            return subprocess.run(
                ["git", "-C", str(ctx.repo), "show", "-s", "--format=%cI", base],
                capture_output=True, text=True, check=True,
            ).stdout.strip()
        except subprocess.CalledProcessError:
            pass
    return ""


# --- build --------------------------------------------------------------------


def bundle_dir(ctx) -> Path:
    return ctx.knowledge_dir / ctx.config.okf.bundle_dirname


def build_okf(ctx, graph_json: dict, llm=None, decisions=None) -> dict:
    """Write the .okf bundle; return a manifest of the pages written."""
    config = ctx.config
    graph = Graph(graph_json)
    at = _base_at(ctx)
    pages = select_function_pages(graph, config)
    purposes, contracts = author_claims(graph, ctx.repo, pages, llm, config, decisions)

    page_ids = {n["id"] for n in pages}
    out = bundle_dir(ctx)
    _reset_dir(out)
    written: list[str] = []

    def write(rel: str, text: str) -> None:
        target = out / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        written.append(rel)

    mods = modules(graph)
    for m in mods:
        module = m["id"]
        write(_module_page_rel(module),
              render_module(graph, module, m, graph.module_members(module),
                            purposes.get(module), page_ids, at, config))
    for n in pages:
        module = _module_of(n["id"], n)
        write(_function_page_rel(n["id"], module),
              render_function(graph, n, module, contracts.get(n["id"]), page_ids, at, config))
    write("repo.md", render_repo(ctx, graph, at, config))
    write("index.md", render_index(ctx, graph, pages, purposes, config))
    write("log.md", render_log(ctx, len(mods), len(pages), at, config))
    return {
        "bundle": str(out.relative_to(ctx.run_dir)),
        "generated_at": at,
        # module_pages + function_pages + repo.md + index.md + log.md == pages
        "counts": {
            "modules": len(mods),
            "function_pages": len(pages),
            "reserved_pages": 3,  # repo.md, index.md, log.md (not module/function pages)
            "pages": len(written),
        },
        "pages": sorted(written),
    }


def _reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
