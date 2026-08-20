# REPORT — glom
Tables in this report are generated from `output/glom/report_summary.json`. Narrative paragraphs are DRAFTED and marked with `AUTHOR` comments for a human to finish.
Base commit (original HEAD, P3 mines at/under this): `50e06d16bae9bd921e694be87c9c0be16c59eec8`

## 1. What was broken and how the pipeline fixes each class

<!-- AUTHOR: WRITE: Summarize each class of problem the pipeline detected and the automated fix, grounded in the tables below. -->

**Environment & hygiene**

| Aspect | Value |
| --- | --- |
| Packaging style | setup.py |
| Python version | 3.12 |
| Test framework | pytest |
| Extras folded into lock | ['test'] |
| Dropped (unresolvable) extras | [] |
| Unresolved inferred imports | [] |
| Image tag | bench-glom |
| Image digest | sha256:dca64ba3b7231cf251c64edacf424e4859c1e7c526e29755074fe6623c21d998 |
| Baseline | failed=0, passed=239, quarantined=0, skipped=0, tests=239 |
| Quarantined tests | 0 |

**Generated tests (mutation gate)**

| Metric | Value |
| --- | --- |
| Modules selected | 4 |
| Functions targeted | 9 |
| Functions kept | 4 |
| Functions weak/dropped | 0 |
| Mutants killed / valid | 14/16 |
| Mutation score | 0.875 |
| Suite after | failed=0, passed=239, tests=239 |

**Lint / format**

| Metric | Value |
| --- | --- |
| pyproject created | True |
| Files changed | 34 |
| Unfixable findings | 265 |
| Files given noqa | 23 |
| Codes | B007=5, B008=2, B015=2, B017=1, B018=7, B020=2, B023=2, B028=1, B904=20, B905=4, E402=3, E501=63, E711=3, E712=2, E721=2, E722=2, E731=19, E741=1, F401=57, F811=1, F841=5, UP031=61 |
| ruff clean in container | False |
| Reverted (regression) | True |

**Knowledge layer (accuracy)**

| Metric | Value |
| --- | --- |
| Source modules | 11 |
| Graph node/edge counts | edges={'calls': 235, 'contains': 367, 'imports': 16, 'inherits': 17, 'tested_by': 3977}, nodes=378, total_edges=4612 |
| Graph edge precision | calls=1.0, contains=1.0, imports=1.0, inherits=1.0, tested_by=1.0 |
| Graph mismatches | 0 |
| OKF pages verified / draft | 106/44 |
| OKF semantic precision | callees=1.0, raises=0.753, side_effects=0.868 |
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
| rejected:few-covering-tests | 27 |
| rejected:low-complexity | 15 |
| rejected:private | 196 |
| rejected:private-parent | 8 |
| rejected:test-code | 234 |
| rejected:too-central | 7 |
| rejected:too-short | 21 |
| rejected:uncovered | 3 |
| screened_out | 1 |
| selected | 5 |
| surplus | 19 |

**History funnel** (every commit considered → status/reject reason)

| Status / reject reason | Count |
| --- | --- |
| built | 9 |
| classified_out | 17 |
| rejected:commit-tests-pass-on-input | 2 |
| rejected:dependency-changing | 97 |
| rejected:docs-or-ci-only | 136 |
| rejected:no-source-change | 128 |
| rejected:non-pr-merge | 39 |
| rejected:root-commit | 1 |
| rejected:superseded-by-merge | 37 |
| rejected:too-large | 8 |
| rejected:too-small | 64 |
| rejected:uncovered-and-no-tests | 135 |
| rejected:unparseable | 1 |
| rejected:verifier-fails-on-solution | 5 |
| rejected:verifier-not-implementation-neutral | 3 |
| rejected:verifier-on-input:error_before_repo_call | 1 |
| surplus | 367 |

**Validation**

| Metric | Value |
| --- | --- |
| Tasks validated | 14 |
| VALID | 13 |

**Instruction authoring**

| Metric | Value |
| --- | --- |
| Tasks | 13 |
| Final | 13 |
| Failed | 0 |
| Regenerations | 0 |
| Difficulty spread | easy=8, hard=1, medium=4 |

**Final selection (the 10)**

| Metric | Value |
| --- | --- |
| Selected | excision=4, history=6, net-new=0 |
| Difficulty spread | easy=5, hard=1, medium=4 (target easy=2, hard=3, medium=5) |
| Distinct modules | glom.core, glom.grouping, glom.matching, glom.reduction |

Selected task ids: `exc-glom.core-format_target_spec_trace`, `exc-glom.reduction-Fold.glomit`, `exc-glom.grouping-GROUP`, `exc-glom.matching-Check.glomit`, `hist-94b6375`, `hist-e515fb3`, `hist-0d75aab`, `hist-4a48227`, `hist-a32abdd`, `hist-c2acc2b`

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
python -m pipeline.validate tasks/glom/<task_id>

# 5. the pipeline's own tests
.venv/bin/python -m pytest
.venv/bin/python -m pytest -m slow
.venv/bin/ruff check .
```

## 5. Scale: what breaks at 100 repos

**Measured cost of this run**

| Metric | Value |
| --- | --- |
| Total LLM tokens | 779614 |
| Reasoning tokens | 30499 |
| Agent runs | 11 |

**LLM tokens by step**

| Step | Tokens |
| --- | --- |
| p1.testgen.write_tests_agent | 550696 |
| p3.build.neutrality_check_rewrite | 117768 |
| p2.okf.function_contracts | 41200 |
| p2.okf.module_purpose | 14505 |
| p3.build.write_instruction | 12156 |
| p3.build.review_instruction | 11614 |
| p3.build.golden_rationale | 11183 |
| p3.history.classify_commit | 11034 |
| p3.excision.screen_candidate | 5923 |
| report.draft_sections | 2723 |
| p3.build.difficulty_label | 812 |

**Per-stage timing (s)**

| Stage | Duration | Skipped |
| --- | --- | --- |
| baseline | 2.24 | False |
| build | - | True |
| compose | - | True |
| detect | - | True |
| dockerfile | - | True |
| lint | - | True |
| pin | - | True |
| testgen | 23.61 | False |

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
