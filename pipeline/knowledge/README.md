# pipeline/knowledge/

Stage 2 (P2): build the static knowledge layer from the hygiene-clean repo. All outputs are deterministic (two runs on the same repo produce byte-identical files). No LLM is used for the graph or indexes; the OKF bundle uses a BIG model for prose only.

## Files

| File | What it does |
|---|---|
| `runner.py` | Chains: symbol_index, indexes, graph, verify, okf, okf_verify. Each step is resumable. Ordering note: indexes (coverage, test_map) must precede the graph because graph nodes carry coverage % and test refs derived from them |
| `graph.py` | Builds `repo_graph.json`. Nodes: source modules, classes, functions (with file, line span, signature, docstring, complexity, coverage, test refs). Edges: imports, contains, calls, inherits, tested_by. Every edge carries `evidence {file, line}`. Sorted, no timestamps |
| `indexes.py` | `history_index.json`: every commit in original history with touched functions resolved by diffing AST spans at each commit. `test_map.json` / `coverage.json`: from one `coverage run -m pytest` container run with dynamic contexts. `hotspots.json`: change frequency per function |
| `verify.py` | Graph self-verification: samples edges, re-derives them by an independent code path, and reports precision per edge type. Writes `graph_verification.json` |
| `okf.py` | Writes the `.okf/` bundle (OKF v0.2): cross-linked Markdown pages with YAML frontmatter. The static skeleton (structure, signatures, callers/callees/tests) comes from the graph. The BIG model writes only module purposes and function contracts, persisted by content hash for 0-token reruns |
| `okf_verify.py` | Re-checks the model's OKF claims against the AST and graph: raises, side_effects, callees. Stamps verified pages; writes `okf_verification.json` |

## Outputs

Written to `output/<repo>/knowledge/`:

- `repo_graph.json`, `symbol_index.json`
- `history_index.json`, `test_map.json`, `coverage.json`, `hotspots.json`
- `graph_verification.json`
- `.okf/` (index.md, repo.md, modules/, functions/, log.md)
- `okf.json`, `okf_decisions.json`, `okf_verification.json`

## Not here

- Symbol extraction from Python AST: `pipeline/ecosystems/symbols.py`
- Graph-backed agent tools (show_symbol, callers, etc.): `pipeline/agent/tools.py`
