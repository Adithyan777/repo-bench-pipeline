# REPORT -- glom

Tables in this report are generated from `output/glom/report_summary.json`.
Base commit (original HEAD, P3 mines at/under this): `50e06d16bae9bd921e694be87c9c0be16c59eec8`

## 1. What was broken and how the pipeline fixes each class

glom ships with a `setup.py` manifest, unpinned dependencies, no lockfile, no
Dockerfile, and no ruff/black configuration. Its test suite (pytest, 202 tests)
passes, but there is no mechanism to reproduce the exact dependency set or run
the suite in an isolated environment.

The pipeline addresses four classes of problems:

**Unpinned dependencies.** `setup.py` lists `boltons>=19.3.0`, `attrs`, and
`face>=20.1.1` with no upper bounds. The pipeline synthesizes
`pipeline-requirements.in`, runs `uv pip compile --generate-hashes`, and
produces `requirements.lock.txt` (13 pins with hashes) plus `constraints.txt`.
A fresh `pip install --no-deps --require-hashes` reproduces the exact
environment.

**No containerization.** The pipeline writes a digest-pinned Dockerfile
(`python:3.12-slim@sha256:...`), builds `bench-glom`, and runs all tests
inside throwaway containers with `--network none`. The image built on the
first attempt with no repair agent needed.

**Coverage gaps in the test suite.** 4 modules were ranked for test generation.
The agent produced tests for glom.cli (3 functions, 10/12 mutants killed) and
glom.streaming (1 function, 4/4 mutants killed). Two modules (glom.core,
glom.grouping) were dropped because the agent spent its turn budget reading
without writing. Suite after generation: 240 tests, verify-twice identical.

**No lint configuration.** ruff was run with rules (E, F, W, I, B, UP). 34
files would change, 265 unfixable findings across 23 files. The lint step was
reverted because 7 `test_error.py::*_stack` tests assert exact rendered source
lines; any formatting change to `core.py` breaks them. All findings are
recorded in `lint.json`.

**Environment & hygiene**

| Aspect | Value |
| --- | --- |
| Packaging style | setup.py |
| Python version | 3.12 |
| Test framework | pytest |
| Extras folded into lock | - |
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

## 2. Design decisions and trade-offs

The pipeline's central principle is "LLM proposes, deterministic code disposes."
Every LLM output passes through a code gate before being accepted: generated
tests must kill AST mutants, instructions must pass a leak check against the
solution diff, verifier tests must survive a neutrality review, OKF claims must
survive AST re-checking, and task verdicts must pass a strict right-reason
classifier. Determinism comes from these gates, not from model temperature
or seeds.

This has a direct trade-off: gate design is where the engineering effort goes,
and overly strict gates reject valid work. The right-reason classifier on glom
correctly rejected one excision task (exc-glom.cli-mw_handle_target) where the
`face` CLI wrapper swallowed the excision error, producing an
`error_before_repo_call` instead of a behavioral assertion failure. That is the
classifier doing its job. But the same strictness means new-API feature commits
must use the `getattr` convention rather than a direct import, which requires
the rewrite agent to understand the pattern.

The two-tier model split (BIG for authoring/agents, SMALL for classification)
saved tokens. Commit classification (11k tokens) and excision screening (6k
tokens) ran on the SMALL tier. Everything else (test-gen, neutrality rewrites,
instruction authoring, OKF contracts) ran on the BIG tier, where test-gen alone
consumed 550k tokens, about 70% of the total.

The mutation gate for test generation is more expensive than a coverage
threshold, but it is the only automated evidence that tests catch bugs.
Coverage alone would accept a test that imports a module and calls a function
without assertions. The mutation gate mirrors how graders evaluate test quality
(inject bugs, check if tests catch them).

All thresholds are centralized in `pipeline/config.py` (19 dataclasses, ~680
lines) with `--set section.key=value` overrides at runtime. No magic numbers
in the code. Full rationale in [docs/decisions.md](docs/decisions.md).

## 3. Task-candidate selection: mined, rejected, and why

Two task sources were used: excision (remove a function body, tests define
behavior) and history (a real commit's change). Net-new tasks were designed but
not built, since the other two sources yielded more than enough valid tasks.

**Excision.** Every function in the symbol index (536 total, excluding one
uncollected function) was evaluated. The largest rejection categories: test-code
(234, functions inside test files), private (196, `_`-prefixed names), and
few-covering-tests (27, fewer than 2 passing baseline tests). 7 functions were
rejected as too-central (more than 40 covering tests; excising them would fail
most of the suite). 1 was screened out by the SMALL model (docstring leaks the
implementation). 5 were selected for building, 19 left as surplus.

Of the 5 built, 4 were VALID. The 1 INVALID task (exc-glom.cli-mw_handle_target)
failed because the `face` CLI framework wraps the target function, and the
`NotImplementedError` from the excised body is caught by the CLI wrapper before
reaching the test. The strict classifier sees `error_before_repo_call`.

**History.** 1,050 commits were considered. The funnel is aggressive: 136
rejected as docs-or-CI-only, 135 as uncovered-and-no-tests, 128 as
no-source-change, 97 as dependency-changing, 64 as too-small, 39 as non-PR
merges, 37 as superseded-by-merge. After hard filters and scoring, 441
survivors were classified by the SMALL model (17 classified out as
refactor/chore/test-only). 20 were shortlisted, 9 built. During building, 5
were rejected for verifier-fails-on-solution (env drift on old commits), 3 for
verifier-not-implementation-neutral (rewrite unchanged), and 1 for
error_before_repo_call. All 9 built tasks were VALID.

**Selection.** 13 VALID tasks from 14 built (4 excision + 9 history). The
selector picked 10 under hard quotas: >= 4 history (achieved: 6), <= 4
excision (achieved: 4), >= 4 distinct modules (achieved: 4: glom.core,
glom.grouping, glom.matching, glom.reduction). Difficulty spread easy 5 /
medium 4 / hard 1 (soft target was 2/5/3; the eligible pool skews easy).

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
| Tasks validated | - |
| VALID | - |

**Instruction authoring**

| Metric | Value |
| --- | --- |
| Tasks | - |
| Final | - |
| Failed | - |
| Regenerations | - |
| Difficulty spread | - |

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
git clone https://github.com/Adithyan777/repo-bench-pipeline.git && cd repo-bench-pipeline
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

The glom run took ~13 minutes wall clock and consumed ~780k tokens across 11
agent runs. Testgen accounts for ~70% of the tokens. At these rates, 100 repos
would cost roughly 78M tokens and 22 hours of sequential wall time. Several
things break at that scale.

**Token cost.** At ~780k tokens per repo, 100 repos would consume ~78M tokens.
The per-repo budget (`llm.max_tokens_per_repo`, default 5M) already caps
runaway repos, but the average cost is dominated by test-gen agents exploring
large modules. Per-function prompts (instead of per-module) would reduce
context size and cost.

**Wall clock.** Agent steps are sequential within a repo: build_history alone
took 220 seconds on glom. A job queue (e.g., Celery with per-repo workers)
would parallelize across repos. Within a repo, the validation harness already
parallelizes (`docker.harness_parallel_workers=4`), but funnels and build steps
are sequential.

**Image storage.** One `bench-<repo>` image per repo, each ~150 MB based on
`python:3.12-slim`. 100 images = ~15 GB before layer sharing. An image
registry (push after build, pull on validate) would decouple build and
validation machines. `--prune-images` handles dangling images but active
images accumulate.

**Flaky repos.** Repos with flaky tests, broken dependencies, or unusual
packaging hit the repair agent more often. The pipeline hard-stops after
quarantine if tests still fail. At scale, a triage step (skip repos that fail
hygiene after one attempt) would avoid wasting resources.

**Human review.** The pipeline produces machine-verified evidence
(verdict.json, graph_verification.json, okf_verification.json) that can be
sampled rather than reviewed exhaustively. At 100 repos, reviewing all 1,000
tasks is not practical. A sampling strategy (review 10% of tasks, all flagged
instructions, all INVALID tasks) would scale.

**What to build differently.** A job queue for per-repo parallelism. An image
registry for storage. Prompt caching for repeated context (OKF contract prompts
send the same function signature multiple times). Per-function test-gen prompts
instead of per-module. A triage step that skips consistently failing repos.

## 6. Honest gaps

Each gap has a detailed entry in [docs/gaps.md](docs/gaps.md).

- **Net-new tasks not generated.** History + excision fill the 10. Net-new is designed but unbuilt.
- **Lint reverted on glom.** 7 test_error.py tests assert exact source lines; formatting breaks them.
- **Test-gen drops large modules.** glom.core and glom.grouping: agent explores without writing.
- **OKF verification is partial.** raises ~0.75, side_effects ~0.87; inputs/outputs/invariants unchecked.
- **test_map excludes doctests.** Coverage context plugin sees only pytest nodeids.
- **Old-commit dependency drift.** Recorded as env-drift, never re-locked (2 candidates lost).
- **Collection-broken baseline path.** Not implemented; no repo triggered it.
- **Git in images is not byte-reproducible.** `apt-get git` pulls latest; digests recorded.
- **Difficulty skew.** easy 5 / medium 4 / hard 1 vs target 2/5/3; eligible pool skews easy.
- **Verifier visibility defaults to visible.** Hack-proof via harness re-copy; `--verifier-visibility hidden` available.
- **New-API imports stay INVALID by design.** getattr convention is required.
- **Single ecosystem.** Python only, behind the adapter interface.
- **SyntaxWarning silenced globally.** From target-code AST parsing.
- **Held-out fresh-clone results.** [To be filled after held-out runs.]
- **Testgen tokens dominate cost.** ~70% of total; per-function prompts would help.
