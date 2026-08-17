# Pipeline 2: knowledge

Builds the static knowledge layer from the hygiene-clean repo. The graph and
indexes are fully deterministic (two runs produce byte-identical files). The
OKF bundle uses a BIG model for prose, cached by content hash. Steps:
symbol_index, indexes, graph, verify, okf.


## symbol_index

**Purpose**: deterministic Python AST index of all source symbols.

**How it works**: walks `.py` files under package roots or `src/`. Extracts
modules, classes, functions, and methods with file, qualname, line span,
signature, docstring, complexity (an internal McCabe branch counter, no
external dependency), decorators. Also extracts imports (including relative
imports, resolved via two-pass module registration) and intra-repo call sites
resolved by name. Unresolved calls are kept, never guessed. Test files are
indexed separately.

Source excludes: `docs/`, `examples/`, `scripts/`, `build/`, `dist/`,
`setup.py`, and test directories. Configurable via `graph.nonsource_dirs`,
`graph.nonsource_files`, `graph.test_dir_names`.

**Artifacts**: `knowledge/symbol_index.json`.

**Config**: `graph.nonsource_dirs`, `graph.nonsource_files`,
`graph.test_dir_globs`, `knowledge.source_roots`.

**On glom**: 11 source modules indexed.


## indexes

**Purpose**: coverage, test mapping, history index, hotspots.

**How it works**:

- **test_map.json**: runs `coverage run -m pytest` in-container with a small
  pipeline-owned pytest plugin (`_kn_ctx_plugin`) that sets the coverage
  context to each test's nodeid. Parses the coverage JSON to map each test
  nodeid to the source functions it exercised.

- **coverage.json**: per-function coverage percentages from the same run.

- **history_index.json**: for every original commit (at/under `base_sha`),
  records the source functions touched by diffing AST spans parsed at that
  commit. Uses `--no-renames` to avoid false matches. Flags manifest changes,
  PR/merge commits.

- **hotspots.json**: change frequency per function across the original history.

Ordering: indexes must precede the graph because graph nodes carry coverage
percentages and test references derived from the indexes.

**Artifacts**: `knowledge/test_map.json`, `knowledge/coverage.json`,
`knowledge/history_index.json`, `knowledge/hotspots.json`.

**Config**: `knowledge.coveragerc_filename`, `knowledge.ctx_plugin_module`,
`knowledge.pr_number_regex`, `knowledge.source_roots`.

**On glom**: test_map covers 232 functions. The index run takes ~130 seconds
(parsing AST spans at each of 1,050 commits).

**Edge case**: doctests are excluded from the test_map because the coverage
context plugin only sees pytest nodeids, not doctest invocations.


## graph

**Purpose**: build `repo_graph.json`, the machine-readable knowledge graph.

**How it works**: assembles nodes (modules, classes, functions) and edges
(imports, contains, calls, inherits, tested_by) from the symbol index, test
map, and coverage data. Every edge carries `evidence: {file, line}` so each
claim is verifiable against source.

The graph is sorted and contains no timestamps, so two runs on the same repo
produce byte-identical output.

**Artifacts**: `knowledge/repo_graph.json`.

**Config**: `graph.edge_types`, `graph.resolve_calls_intra_repo_only`,
`graph.diversity_unit`, `graph.large_repo_module_threshold`.

**On glom**: 378 nodes, 4,612 edges (calls 235, contains 367, imports 16,
inherits 17, tested_by 3,977).


## verify

**Purpose**: independent self-verification of the graph.

**How it works**: samples edges and re-derives them by an independent code
path. For each edge type:
- Imports: re-parse the source file's imports.
- Calls: re-scan `ast.Call` nodes.
- Symbols: import the module in-container and confirm each symbol exists.
- Tested_by: re-derive from raw coverage contexts.

Reports precision per edge type and total mismatches.

**Artifacts**: `knowledge/graph_verification.json`.

**Config**: `graph.verification_sample_edges`.

**On glom**: precision 1.0 on all edge types, 129/129 symbols confirmed
present, 0 mismatches.


## okf

**Purpose**: write the `.okf/` knowledge bundle (OKF v0.2).

**How it works**: generates a directory of cross-linked Markdown pages with
YAML frontmatter. The structure:

```
.okf/
  index.md          # root listing
  repo.md           # entrypoints, test command, conventions
  modules/          # one page per source module
    <mod>.md        # purpose, public API, links
  functions/        # one page per function (up to max_function_pages)
    <mod>/
      <qualname>.md # contract: inputs, outputs, raises, side_effects,
                    #   invariants; callers, callees, tests
  log.md            # provenance log
```

The static skeleton (structure, signatures, callers/callees/tests) comes from
the graph. The BIG model writes only module purposes and function contracts.
Each model output is cached by content hash, so reruns are 0-token.

A hallucination guard checks module purpose claims. Function pages are
selected by `public_or_top_complexity` (public functions, plus private
functions above `min_private_page_complexity`), capped at
`max_function_pages`.

**okf_verify** re-checks the model's claims against the AST and graph:
- **raises**: checks whether claimed exceptions appear in the function body
  (including negative checks for "does not raise").
- **side_effects**: checks whether claimed IO/mutation calls appear.
- **callees**: re-derives via `ast.Call`.
- **callers/links**: reported as true-by-construction (graph-derived), not
  independently verified.

A page is stamped `verified` only if at least one claim was actually checked
and passed. Unchecked claim kinds (inputs, outputs, invariants) are listed.
Pages with no checkable claims or failed checks stay `draft`.

**Artifacts**: `knowledge/.okf/` (the bundle), `knowledge/okf.json`,
`knowledge/okf_decisions.json`, `knowledge/okf_verification.json`.

**Config**: `okf.enabled`, `okf.max_function_pages`,
`okf.min_private_page_complexity`, `okf.side_effect_call_names`,
`okf.okf_version`.

**On glom**: 164 pages (106 verified, 44 draft). OKF conformance: true.
Semantic precision: callees 1.0, raises ~0.75, side_effects ~0.87.
Callers/links by-construction: 1.0. Unchecked: inputs, outputs, invariants.
The conservative approach (implicit or under-claimed exceptions stay `draft`)
is intentional. Honest draft labels are preferred over over-claimed verification.
