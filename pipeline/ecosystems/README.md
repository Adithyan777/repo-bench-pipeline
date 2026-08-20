# pipeline/ecosystems/

The only place language-ecosystem-specific logic lives. Everything else in the pipeline (agent loop, harness, funnels, docker runner) is ecosystem-agnostic.

## Files

| File | What it does |
|---|---|
| `base.py` | `EcosystemAdapter` abstract base class: ~11 methods (detect, packaging info, synthesize requirements, write Dockerfile, test command, parse test report, lint, mutators, symbol index). Adding a new language means implementing this interface |
| `python.py` | `PythonAdapter`: detects packaging style (setup.py, pyproject.toml, requirements.txt, bare), infers Python version, synthesizes `requirements.in`, runs `uv pip compile --generate-hashes`, writes a digest-pinned Dockerfile, parses pytest JSON reports, runs ruff lint/format in-container, provides AST-based mutators |
| `symbols.py` | Deterministic Python AST indexing. Extracts modules, classes, functions (file, qualname, line span, signature, docstring, complexity, decorators), imports (including relative), and intra-repo call sites resolved by name. Complexity is an internal McCabe branch counter (no external dependency). Test files are indexed separately |
| `source_ops.py` | Pure-AST source operations for task generation: `excise_function` (line-span splice replacing a function body), `module_bound_names` (top-level names for the harness static gate), `count_assertions`, `verifier_imports` |

## How it's used

`PythonAdapter` is constructed per-repo by `hygiene/context.py` and passed through every stage. The symbol index feeds the knowledge graph; `source_ops` feeds the excision task builder and the harness.

## Not here

- Orchestration of detect/pin/build/baseline steps: `pipeline/hygiene/`
- Repo graph construction: `pipeline/knowledge/graph.py`
