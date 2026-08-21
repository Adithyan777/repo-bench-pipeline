# REPORT — toolz
Tables in this report are generated from `output/toolz/report_summary.json`. Narrative paragraphs are DRAFTED and marked with `AUTHOR` comments for a human to finish.
Base commit (original HEAD, P3 mines at/under this): `568c2b8393973cd172a466546c9d95779c452438`

## 1. What was broken and how the pipeline fixes each class

The hygiene suite reports 186 passed tests with zero failures, quarantines, or skips. Linting is clean with no regressed files, unfixable issues, or noqa suppressions, and the container image was rebuilt during the run. Test generation retained 5 functions across 2 selected modules, achieving a mutation score of 0.889 with 16 of 18 valid mutants killed.

<!-- AUTHOR: review and edit the drafted paragraph above. -->

**Environment & hygiene**

| Aspect | Value |
| --- | --- |
| Packaging style | pyproject |
| Python version | 3.12 |
| Test framework | pytest |
| Extras folded into lock | [] |
| Dropped (unresolvable) extras | [] |
| Unresolved inferred imports | [] |
| Image tag | bench-toolz |
| Image digest | sha256:ea390db0b06a75508772ea648c158ae15d4d1ea5b2764103f4ec7f9352f828a5 |
| Baseline | failed=0, passed=186, quarantined=0, skipped=0, tests=186 |
| Quarantined tests | 0 |

**Generated tests (mutation gate)**

| Metric | Value |
| --- | --- |
| Modules selected | 2 |
| Functions targeted | 5 |
| Functions kept | 5 |
| Functions weak/dropped | 0 |
| Mutants killed / valid | 16/18 |
| Mutation score | 0.889 |
| Suite after | failed=0, passed=186, tests=186 |

**Lint / format**

| Metric | Value |
| --- | --- |
| pyproject created | False |
| Files changed | 1 |
| Unfixable findings | 0 |
| Files given noqa | 0 |
| Codes | - |
| ruff clean in container | True |
| Reverted (regression) | False |

**Knowledge layer (accuracy)**

| Metric | Value |
| --- | --- |
| Source modules | 16 |
| Graph node/edge counts | edges={'calls': 79, 'contains': 161, 'imports': 23, 'tested_by': 853}, nodes=177, total_edges=1116 |
| Graph edge precision | calls=1.0, contains=1.0, imports=1.0, tested_by=1.0 |
| Graph mismatches | 0 |
| OKF pages verified / draft | 104/32 |
| OKF semantic precision | callees=1.0, raises=0.25, side_effects=0.984 |
| OKF by-construction (callers/link) | callers=1.0, link=1.0 |
| OKF unchecked (prose) | inputs, outputs, invariants |
| OKF conformance | True |

_by-construction (callers / internal links) are graph-derived and reported separately from independently re-derived semantic checks (callees / raises / side_effects)._

## 2. Design decisions & trade-offs

The excision funnel screened 391 candidates and selected 5, with the largest rejections coming from test-code (251), private (55), and few-covering-tests (38). The history funnel processed 1,025 commits and built 7 tasks, filtering out the majority for docs-or-ci-only changes (211), no-source-change (218), and uncovered-and-no-tests (167). Final task assembly produced 12 instructions with zero failed difficulty labels, zero leak rejections, and 10 reused from prior iterations.

<!-- AUTHOR: review and edit the drafted paragraph above. -->

## 3. Task-candidate selection: mined, rejected, and why

Twelve tasks were selected from five distinct modules: toolz.dicttoolz, toolz.functoolz, toolz.itertoolz, toolz.sandbox.core, and toolz.sandbox.parallel. The mix comprises 4 excision and 6 history tasks, with a difficulty spread of 4 easy, 5 medium, and 1 hard against a target of 2 easy, 5 medium, and 3 hard. All 12 tasks passed validation with no rejection reasons recorded.

<!-- AUTHOR: review and edit the drafted paragraph above. -->

**Excision funnel** (every function considered → status/reject reason)

| Status / reject reason | Count |
| --- | --- |
| rejected:few-covering-tests | 38 |
| rejected:init-module | 1 |
| rejected:low-complexity | 14 |
| rejected:private | 55 |
| rejected:test-code | 251 |
| rejected:too-long | 2 |
| rejected:too-short | 15 |
| rejected:uncovered | 8 |
| rejected:verifier-imports-private | 7 |
| screened_out | 1 |
| selected | 5 |
| surplus | 12 |

**History funnel** (every commit considered → status/reject reason)

| Status / reject reason | Count |
| --- | --- |
| built | 7 |
| classified_out | 6 |
| rejected:commit-tests-pass-on-input | 1 |
| rejected:dependency-changing | 54 |
| rejected:docs-or-ci-only | 211 |
| rejected:env-drift | 5 |
| rejected:no-source-change | 218 |
| rejected:non-pr-merge | 36 |
| rejected:reverted-by | 3 |
| rejected:root-commit | 1 |
| rejected:superseded-by-merge | 45 |
| rejected:too-large | 7 |
| rejected:too-many-files | 4 |
| rejected:too-small | 157 |
| rejected:uncovered-and-no-tests | 167 |
| rejected:unparseable | 23 |
| rejected:verifier-fails-on-solution | 2 |
| rejected:verifier-imports-non-public-or-missing | 1 |
| rejected:verifier-not-implementation-neutral | 2 |
| rejected:verifier-on-input:error_before_repo_call | 2 |
| surplus | 278 |

**Validation**

| Metric | Value |
| --- | --- |
| Tasks validated | 12 |
| VALID | 12 |

**Instruction authoring**

| Metric | Value |
| --- | --- |
| Tasks | 12 |
| Final | 12 |
| Failed | 0 |
| Regenerations | 0 |
| Difficulty spread | easy=6, hard=1, medium=5 |

**Final selection (the 10)**

| Metric | Value |
| --- | --- |
| Selected | excision=4, history=6, net-new=0 |
| Difficulty spread | easy=4, hard=1, medium=5 (target easy=2, hard=3, medium=5) |
| Distinct modules | toolz.dicttoolz, toolz.functoolz, toolz.itertoolz, toolz.sandbox.core, toolz.sandbox.parallel |

Selected task ids: `exc-toolz.dicttoolz-merge`, `exc-toolz.dicttoolz-merge_with`, `exc-toolz.itertoolz-groupby`, `exc-toolz.sandbox.parallel-fold`, `hist-2bd9139`, `hist-386c750`, `hist-639043e`, `hist-699e0c2`, `hist-8cdc7fe`, `hist-b8aca17`

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
python -m pipeline.validate tasks/toolz/<task_id>

# 5. the pipeline's own tests
.venv/bin/python -m pytest
.venv/bin/python -m pytest -m slow
.venv/bin/ruff check .
```

## 5. Scale: what breaks at 100 repos

**Measured cost of this run**

| Metric | Value |
| --- | --- |
| Total LLM tokens | 100069 |
| Reasoning tokens | 10213 |
| Agent runs | 11 |

**LLM tokens by step**

| Step | Tokens |
| --- | --- |
| p2.okf.function_contracts | 33319 |
| p1.testgen.write_tests_agent | 23943 |
| p3.build.neutrality_check_rewrite | 13342 |
| p2.okf.module_purpose | 8792 |
| p3.build.write_instruction | 6950 |
| p3.build.golden_rationale | 6753 |
| p3.build.review_instruction | 6607 |
| p3.build.difficulty_label | 363 |

**Per-stage timing (s)**

| Stage | Duration | Skipped |
| --- | --- | --- |
| baseline | 2.0 | False |
| build | - | True |
| build_excision | 5.82 | False |
| build_history | 70.82 | False |
| compose | - | True |
| detect | - | True |
| dockerfile | - | True |
| excision_funnel | 0.06 | False |
| graph | 0.03 | False |
| history_funnel | 40.09 | False |
| indexes | 117.62 | False |
| instruct | 11.86 | False |
| lint | 12.93 | False |
| manifest | 0.0 | False |
| okf | 1.85 | False |
| pin | 0.26 | False |
| select | 0.0 | False |
| symbol_index | 0.23 | False |
| testgen | 82.58 | False |
| validate | 37.9 | False |
| verify | 0.83 | False |

_Timings and token counts come from the runner's `report_data.json`; steps that were skipped as up-to-date record no duration. The console log of the full run is the authoritative wall-clock record._

The repository contains 16 source modules. The knowledge base holds 155 total pages (136 function pages, 3 reserved), of which 104 are verified and 32 remain in draft. The excision funnel rejected 391 candidates to select 5 targets, while the history funnel evaluated over a thousand commits to yield 7 built tasks, demonstrating high selectivity at both sourcing stages.

<!-- AUTHOR: review and edit the drafted paragraph above. -->

## 6. Honest gaps

The achieved difficulty spread skews easier than targeted (4 easy vs. 2 target, 1 hard vs. 3 target), indicating a gap in sourcing hard tasks. OKF semantic precision for raises is low at 0.25, and claims for inputs, outputs, and invariants are completely unchecked. No net-new tasks were selected, and 12 surplus excision candidates were deferred, suggesting room for broader module coverage.

<!-- AUTHOR: review and edit the drafted paragraph above. -->

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
