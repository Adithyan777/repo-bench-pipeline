"""repo_graph.json: deterministic static knowledge graph (docs/pipeline-2-knowledge.md).

Nodes: source modules/classes/functions (tests never become nodes) with file, span and,
for functions, signature/docstring/complexity/coverage/test refs. Edges: imports,
contains, calls, inherits, tested_by; every edge carries ``evidence {file, line}``.
Repo-relative paths, sorted, no timestamps: byte-identical across runs.
"""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.config import DEFAULT, Config

_NODE_RANK = {"module": 0, "class": 1, "function": 2, "method": 2}


def build_graph(
    symbols: dict,
    test_map: dict[str, list[str]] | None = None,
    coverage: dict[str, float] | None = None,
    config: Config = DEFAULT,
) -> dict:
    test_map = test_map or {}
    coverage = coverage or {}
    # Source node = importable library source (``is_source`` from symbols.py); older
    # indexes without the field fall back to not-test / not-nonsource_files.
    nonsource = set(config.graph.nonsource_files)
    source_modules = {
        m["name"]
        for m in symbols["modules"]
        if m.get("is_source", not m["is_test"] and m["file"] not in nonsource)
    }

    tested_by = _invert_test_map(test_map)  # func qual -> [test_id]
    test_locations = _test_locations(symbols)  # test_id -> {file, line}

    nodes = _nodes(symbols, source_modules, coverage, tested_by)
    edges = _edges(symbols, source_modules, tested_by, test_locations)

    node_ids = {n["id"] for n in nodes}
    edges = [e for e in edges if e["source"] in node_ids]  # never dangle a source

    edge_counts: dict[str, int] = {}
    for edge in edges:
        edge_counts[edge["type"]] = edge_counts.get(edge["type"], 0) + 1

    return {
        "metadata": {
            "complexity_metric": config.graph.complexity_metric,
            "diversity_unit": _diversity_unit(len(source_modules), config),
            "module_count": len(symbols["modules"]),
            "source_module_count": len(source_modules),
            "counts": {"nodes": len(nodes), "edges": edge_counts, "total_edges": len(edges)},
        },
        "nodes": nodes,
        "edges": edges,
    }


def _diversity_unit(source_modules: int, config: Config) -> str:
    if source_modules >= config.graph.large_repo_module_threshold:
        return "subpackage"
    return config.graph.diversity_unit


# --- nodes --------------------------------------------------------------------


def _nodes(symbols, source_modules, coverage, tested_by) -> list[dict]:
    nodes: list[dict] = []
    for mod in symbols["modules"]:
        if mod["name"] not in source_modules:
            continue
        nodes.append(
            {
                "id": mod["name"],
                "type": "module",
                "file": mod["file"],
                "line": 1,
                "is_public": not mod["name"].split(".")[-1].startswith("_"),
                "docstring": mod["docstring"],
            }
        )
    for cls in symbols["classes"]:
        if cls["module"] not in source_modules:
            continue
        nodes.append(
            {
                "id": cls["qualname"],
                "type": "class",
                "file": cls["file"],
                "line": cls["line"],
                "end_line": cls["end_line"],
                "is_public": cls["is_public"],
                "docstring": cls["docstring"],
                "decorators": cls["decorators"],
            }
        )
    for fn in symbols["functions"]:
        if fn["module"] not in source_modules:
            continue
        nodes.append(
            {
                "id": fn["qualname"],
                "type": "method" if fn["is_method"] else "function",
                "file": fn["file"],
                "line": fn["line"],
                "end_line": fn["end_line"],
                "signature": fn["signature"],
                "is_public": fn["is_public"],
                "docstring": fn["docstring"],
                "complexity": fn["complexity"],
                "decorators": fn["decorators"],
                "coverage": coverage.get(fn["qualname"]),
                "tested_by": sorted(tested_by.get(fn["qualname"], [])),
            }
        )
    return _dedupe_nodes(nodes)


def _dedupe_nodes(nodes: list[dict]) -> list[dict]:
    """One node per id; a redefined symbol keeps its final (runtime-live) definition."""
    by_id: dict[str, dict] = {}
    for node in nodes:
        current = by_id.get(node["id"])
        if current is None or node.get("line", 0) > current.get("line", 0):
            by_id[node["id"]] = node
    return sorted(by_id.values(), key=lambda n: (_NODE_RANK[n["type"]], n["id"]))


# --- edges --------------------------------------------------------------------


def _edges(symbols, source_modules, tested_by, test_locations) -> list[dict]:
    edges: list[dict] = []

    for mod in symbols["modules"]:
        if mod["name"] not in source_modules:
            continue
        seen_imports: dict[tuple[str, str], int] = {}
        for imp in mod["imports"]:
            target = imp["target_module"]
            if target in source_modules and target != mod["name"]:
                key = (mod["name"], target)
                # one edge per module pair; keep the earliest import line as evidence
                if key not in seen_imports or imp["line"] < seen_imports[key]:
                    seen_imports[key] = imp["line"]
        for (source, target), line in seen_imports.items():
            edges.append(_edge("imports", source, target, mod["file"], line))

    for cls in symbols["classes"]:
        if cls["module"] not in source_modules:
            continue
        edges.append(_edge("contains", cls["module"], cls["qualname"], cls["file"], cls["line"]))
        for base in cls["bases"]:
            if base["target"] in {c["qualname"] for c in symbols["classes"]}:
                edges.append(
                    _edge("inherits", cls["qualname"], base["target"], cls["file"], cls["line"])
                )

    for fn in symbols["functions"]:
        if fn["module"] not in source_modules:
            continue
        parent_file = fn["file"]
        edges.append(_edge("contains", fn["parent"], fn["qualname"], parent_file, fn["line"]))
        for call in fn["calls"]:
            edges.append(_edge("calls", fn["qualname"], call["target"], fn["file"], call["line"]))
        for test_id in tested_by.get(fn["qualname"], []):
            loc = test_locations.get(test_id, {"file": test_id.split("::")[0], "line": 1})
            edges.append(_edge("tested_by", fn["qualname"], test_id, loc["file"], loc["line"]))

    # keep contains edges only when the container is itself a source node
    valid = source_modules | {c["qualname"] for c in symbols["classes"]}
    edges = [e for e in edges if e["type"] != "contains" or e["source"] in valid]
    return sorted(
        edges,
        key=lambda e: (e["type"], e["source"], e["target"], e["evidence"]["line"]),
    )


def _edge(edge_type: str, source: str, target: str, file: str, line: int) -> dict:
    return {
        "type": edge_type,
        "source": source,
        "target": target,
        "evidence": {"file": file, "line": line},
    }


# --- test joins ---------------------------------------------------------------


def _base_nodeid(nodeid: str) -> str:
    """Drop a parametrization suffix: `test_x[p]` -> `test_x`."""
    return nodeid.split("[", 1)[0]


def _invert_test_map(test_map: dict[str, list[str]]) -> dict[str, list[str]]:
    """func qual -> distinct test functions; parametrized cases collapse to the base nodeid."""
    out: dict[str, set[str]] = {}
    for test_id, funcs in test_map.items():
        base = _base_nodeid(test_id)
        for func in funcs:
            out.setdefault(func, set()).add(base)
    return {k: sorted(v) for k, v in out.items()}


def _test_locations(symbols: dict) -> dict[str, dict]:
    """base pytest nodeid (`path::Class::method`) -> {file, line} for tested_by evidence."""
    out: dict[str, dict] = {}
    test_modules = {m["name"] for m in symbols["modules"] if m["is_test"]}
    for fn in symbols["functions"]:
        if fn["module"] not in test_modules:
            continue
        within = fn["qualname"][len(fn["module"]) + 1 :]  # qualname minus "module."
        nodeid = fn["file"] + "::" + within.replace(".", "::")
        out[nodeid] = {"file": fn["file"], "line": fn["line"]}
    return out


# --- io -----------------------------------------------------------------------


def write_graph(graph: dict, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph, indent=2, sort_keys=True))
    return path
