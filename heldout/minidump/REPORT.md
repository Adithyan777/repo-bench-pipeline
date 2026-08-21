# REPORT — minidump
Tables in this report are generated from `output/minidump/report_summary.json`. Narrative paragraphs are DRAFTED and marked with `AUTHOR` comments for a human to finish.
Base commit (original HEAD, P3 mines at/under this): `4d22796e57203b37467a150e451b9879b45aeb3b`

> Note: the following expected artifacts were not present when this report was built (their rows read `-`): selection.

## 1. What was broken and how the pipeline fixes each class

<!-- AUTHOR: WRITE: Summarize each class of problem the pipeline detected and the automated fix, grounded in the tables below. -->

**Environment & hygiene**

| Aspect | Value |
| --- | --- |
| Packaging style | setup.py |
| Python version | 3.12 |
| Test framework | none |
| Extras folded into lock | [] |
| Dropped (unresolvable) extras | [] |
| Unresolved inferred imports | [] |
| Image tag | bench-minidump |
| Image digest | sha256:778d4c1941c1e7474cc99856197e33f5ff505ca7533e553448620637dd98f098 |
| Baseline | failed=0, passed=55, tests=55 |
| Quarantined tests | 0 |

**Generated tests (mutation gate)**

| Metric | Value |
| --- | --- |
| Modules selected | 5 |
| Functions targeted | 30 |
| Functions kept | 3 |
| Functions weak/dropped | 0 |
| Mutants killed / valid | 11/12 |
| Mutation score | 0.917 |
| Suite after | failed=0, passed=55, tests=55 |

**Lint / format**

| Metric | Value |
| --- | --- |
| pyproject created | False |
| Files changed | 51 |
| Unfixable findings | 703 |
| Files given noqa | 36 |
| Codes | B007=1, B018=1, B904=1, E501=138, E721=3, E722=10, F403=43, F405=213, F811=1, F821=3, F841=6, UP031=281, W291=1, W293=1 |
| ruff clean in container | False |
| Reverted (regression) | False |

**Knowledge layer (accuracy)**

| Metric | Value |
| --- | --- |
| Source modules | 50 |
| Graph node/edge counts | edges={'calls': 227, 'contains': 676, 'imports': 79, 'inherits': 19, 'tested_by': 77}, nodes=726, total_edges=1078 |
| Graph edge precision | calls=1.0, contains=1.0, imports=1.0, inherits=1.0, tested_by=1.0 |
| Graph mismatches | 0 |
| OKF pages verified / draft | 84/66 |
| OKF semantic precision | callees=1.0, raises=0.282, side_effects=0.8 |
| OKF by-construction (callers/link) | callers=1.0, link=1.0 |
| OKF unchecked (prose) | inputs, outputs, invariants |
| OKF conformance | True |

_by-construction (callers / internal links) are graph-derived and reported separately from independently re-derived semantic checks (callees / raises / side_effects)._

## 2. Design decisions & trade-offs

<!-- AUTHOR: WRITE: Explain the key automated-vs-manual decisions and trade-offs (LLM proposes / code disposes; mutation gate; strict right-reason classifier; determinism from gates). -->

## 3. Task-candidate selection: mined, rejected, and why

<!-- AUTHOR: WRITE: Describe what was mined and rejected and on what grounds, citing the funnel counts and the final selection below. -->

**Excision funnel** (every function considered → status/reject reason)

| Status / reject reason | Count |
| --- | --- |
| rejected:low-complexity | 1 |
| rejected:private | 193 |
| rejected:test-code | 64 |
| rejected:too-short | 2 |
| rejected:uncovered | 299 |
| screened_out | 3 |
| selected | 5 |
| surplus | 1 |

**History funnel** (every commit considered → status/reject reason)

| Status / reject reason | Count |
| --- | --- |
| built | 1 |
| rejected:dependency-changing | 21 |
| rejected:docs-or-ci-only | 13 |
| rejected:no-source-change | 6 |
| rejected:no-verifier-tests | 1 |
| rejected:non-pr-merge | 4 |
| rejected:root-commit | 1 |
| rejected:superseded-by-merge | 1 |
| rejected:too-large | 3 |
| rejected:too-many-files | 6 |
| rejected:too-small | 20 |
| rejected:uncovered-and-no-tests | 41 |

**Validation**

| Metric | Value |
| --- | --- |
| Tasks validated | 6 |
| VALID | 6 |

**Instruction authoring**

| Metric | Value |
| --- | --- |
| Tasks | 6 |
| Final | 6 |
| Failed | 0 |
| Regenerations | 0 |
| Difficulty spread | easy=5, medium=1 |

**Final selection (the 10)**

| Metric | Value |
| --- | --- |
| Selected | - |
| Difficulty spread | - (target -) |
| Distinct modules | - |

Selected task ids: 

## 4. How to run everything

Exact commands (fresh clone). See README for full detail.

```bash
# 0. setup
git clone https://github.com/Adithyan777/repo-bench-pipeline.git
cd repo-bench-pipeline
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements-dev.txt
cp .env.example .env    # add LLM_BASE_URL + LLM_API_KEY

# 1. full pipeline (hygiene -> knowledge -> tasks -> select -> report)
./run.sh https://github.com/mahmoud/glom --fresh

# 2. per stage
./run.sh <repo> --stage hygiene
./run.sh <repo> --stage knowledge
./run.sh <repo> --stage tasks

# 3. run the documented container test twice (acceptance)
./run.sh <repo> --stage hygiene --verify-twice

# 4. validate a selected task standalone (paths from tasks.json)
python -m pipeline.validate tasks/minidump/<task_id>

# 5. the pipeline's own tests
.venv/bin/python -m pytest
.venv/bin/python -m pytest -m slow
.venv/bin/ruff check .
```

## 5. Scale: what breaks at 100 repos

**Measured cost of this run**

| Metric | Value |
| --- | --- |
| Total LLM tokens | 926163 |
| Reasoning tokens | 66809 |
| Agent runs | 7 |

**LLM tokens by step**

| Step | Tokens |
| --- | --- |
| p1.testgen.write_tests_agent | 494604 |
| p1.testgen.mutation_retry_agent | 366396 |
| p2.okf.function_contracts | 48429 |
| p2.okf.module_purpose | 16734 |

**Per-stage timing (s)**

| Stage | Duration | Skipped |
| --- | --- | --- |
| baseline | 0.0 | False |
| build | 12.68 | False |
| compose | 0.01 | False |
| detect | 0.01 | False |
| dockerfile | 2.56 | False |
| graph | 0.02 | False |
| indexes | 25.56 | False |
| lint | 9.36 | False |
| okf | 149.71 | False |
| pin | 0.85 | False |
| symbol_index | 0.23 | False |
| testgen | 687.84 | False |
| verify | 1.03 | False |

_Timings and token counts come from the runner's `report_data.json`; steps that were skipped as up-to-date record no duration. The console log of the full run is the authoritative wall-clock record._

<!-- AUTHOR: WRITE: Given the timings/tokens above, describe what breaks at 100 repos and what you would build differently (job queue, image registry, triage, human-review sampling). -->

## 6. Honest gaps

<!-- AUTHOR: WRITE: State the de-scoped/known-weak items with next steps. -->

- Net-new tasks are not generated; history + excision fill the 10.
- `apt-get git` in git-versioned images makes those images not byte-reproducible (env fix so the version resolves; digests are recorded, not gated).
- OKF `raises`/`side_effects` precision is conservative (implicit/under-claimed exceptions stay `draft`); `callers`/internal links are true-by-construction, not independent evidence.
- `test_map` excludes doctests.
- Test-gen coverage-theater guard: whole-file zero-kill drop (no per-test trimming).
- Verifier visibility defaults to `visible` (hack-proof via harness re-copy).
- History new-symbol features rely on the getattr convention; pure new-symbol imports on `input/` remain INVALID by the strict classifier's design.
- Old-commit dependency drift is rejected, never re-locked: `env-drift` when the tree cannot collect in the pinned image, `verifier-fails-on-solution` when the commit's own tests do not pass on its own solution tree.
- The collection-broken baseline path (one repair → treat as no tests) is not implemented — no in-scope repo hit it; the inert flags for it were removed.
- The lint step rebuilds the image and runs the suite twice to prove the linted tree still builds green; a change that regresses a test reverts the whole step. Some repos assert on exact rendered source lines in their tests (on the sample repo, `test_error.py::*_stack`), so any edit to the asserted file breaks them and the repo ships un-linted with every finding recorded in `lint.json`.
- Test-gen drops a module when the agent spends its turn budget reading a large module without writing a test file; no retry with a larger budget is attempted automatically (see the `dropped_no_file` modules in `testgen.json`).
<!-- AUTHOR: expand each gap with a concrete next step. -->
