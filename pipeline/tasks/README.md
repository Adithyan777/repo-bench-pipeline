# pipeline/tasks/

Stage 3 (P3): generate, validate, and select benchmark tasks from the knowledge-enriched repo.

## Files

| File | What it does |
|---|---|
| `runner.py` | Chains the full stage: excision funnel, excision build, history funnel, history build, validate, instruct, manifest, select. Difficulty labelling runs inside instruct, not as its own step. Resumable via `state.py` with code fingerprints in every step's input hash |
| `excision.py` | Excision funnel: deterministic candidate selection from knowledge artifacts, then a SMALL-model screen. Every function gets a status and reject reason |
| `history.py` | History funnel: deterministic hard filters + signal scoring over `history_index.json`, then a SMALL-model classify (batched, decisions persisted by content hash), then a diversity-aware shortlist |
| `build_excision.py` | Builds one excision task folder: `input/` (repo tree with function body spliced out), `solution/` (the full tree), `verifier/` (covering test files + conftest ancestors + `run.sh`) |
| `build_history.py` | Builds one history task folder: `input/` (full tree at parent commit via `git archive`), `solution/` (full tree at the commit). Both get the hygiene overlay additively (Dockerfile, lock) without overwriting historical files. Verifier is the commit's added/changed test functions, or a bounded BIG agent if the commit has no tests |
| `harness.py` | Validation harness: `validate_task(task_dir) -> verdict`. Runs in-container on fresh workdirs. Checks fail-before (right-reason classification), pass-after, determinism (`harness.determinism_runs`, 3 by default), collateral damage, static gate. Writes evidence to `<task>/evidence/` and `verdict.json` |
| `classify.py` | Right-reason classifier over a pytest JSON report. Categorizes each test failure as import error, attribute error, assertion error, etc. |
| `instruction.py` | LLM-authored task instruction with leak gates. The BIG author sees only `input/`, verifier tests, and the public contract. A pure-code leak check against the solution diff and a BIG reviewer gate the output. Golden rationale (`goldenSolution.md`) may see the diff |
| `difficulty.py` | Difficulty labelling (easy/medium/hard). Code computes features from the graph and diff; a BIG call assigns the label with a rationale that must cite a computed feature |
| `manifest.py` | Writes `tasks/<repo>/tasks.json` from all built tasks. Reads validation status from each task's `evidence/verdict.json` |
| `select.py` | Final selection: picks exactly N VALID tasks honoring hard quotas (min history, max excision, min distinct modules) and soft difficulty spread. Deterministic. Writes root `tasks.json` and `selection.json` |

## Outputs

- `output/<repo>/tasks/` (candidates.json, history_candidates.json, built.json, instructions.json, selection files)
- `tasks/<repo>/<task_id>/` folders (task.json, input/, solution/, verifier/, goldenSolution.md, evidence/)
- `tasks/<repo>/tasks.json` (all built tasks)
- Root `tasks.json` (the final selected set)

## Not here

- Standalone validation CLI: `pipeline/validate.py` (`python -m pipeline.validate`)
- Source-level excision logic: `pipeline/ecosystems/source_ops.py`
