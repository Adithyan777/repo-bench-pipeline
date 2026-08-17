# Pipeline 3: tasks

Generates, validates, and selects 10 benchmark tasks. Steps: excision_funnel,
build_excision, history_funnel, build_history, validate, instruct, manifest,
select.


## Task folder layout

Every task lives in `tasks/<repo>/<task_id>/`:

```
<task_id>/
  task.json           # id, title, instruction, provenance, module, difficulty
  input/              # repo tree as the solver sees it
  solution/           # repo tree with the correct code
  verifier/           # test files + conftest ancestors + run.sh
  goldenSolution.md   # LLM-authored "why correct" rationale
  evidence/           # machine-generated validation artifacts
    verdict.json      # VALID/INVALID + reasons
    fail_before.log   # verifier output against input/
    pass_after.log    # verifier output against solution/
    determinism.json  # per-test repeated results
    collateral.json   # broader suite results on solution/
```

Task IDs: `exc-<module>-<function>` (excision) or `hist-<sha7>` (history).


## Excision funnel

**Purpose**: select functions whose body can be removed to create a focused
red-to-green task.

**How it works**: every function in the symbol index is evaluated against hard
filters, then a SMALL-model screen.

Hard filters (reject reasons):
- `uncovered`: no covering tests at baseline.
- `few-covering-tests`: fewer than `min_covering_tests` (2) passing baseline tests.
- `too-central`: more than `max_covering_tests` (40) covering tests. Excising
  central dispatch code fails most of the suite.
- `too-short`: fewer than `min_lines` (8) lines.
- `too-long`: more than `max_lines` (80) lines.
- `low-complexity`: complexity below `min_complexity` (3).
- `private`: `_`-prefixed name (when `public_only` is true).
- `private-parent`: method on a `_Private` class (when `require_public_parent` is true).
- `test-code`: function inside a test file.
- `init-module`: function in `__init__.py` (re-export shims).
- `private-verifier-imports`: covering tests import private repo symbols (pre-gate,
  before any LLM spend).

SMALL-model screen: asks "does the docstring leak the implementation? Is it
trivially inferable?" Walks candidates in batched chunks until `build_target`
(5) survive. Decisions persist by content hash.

Ranking: `covering_tests * complexity`, distributed round-robin over modules
for diversity.

**Artifacts**: `output/<repo>/tasks/candidates.json` (every function with
status and reject reason).

**Config**: `excision.min_covering_tests`, `excision.max_covering_tests`,
`excision.min_lines`, `excision.max_lines`, `excision.min_complexity`,
`excision.public_only`, `excision.require_public_parent`,
`excision.build_target`, `excision.reject_private_verifier_imports`.

**On glom**: 536 functions considered. 497 rejected by hard filters (234 test-code,
196 private, 27 few-covering-tests, 21 too-short, 15 low-complexity, 8
private-parent, 7 too-central, 3 uncovered). 1 screened out by SMALL model.
5 selected for building, 19 surplus.


## build_excision

**Purpose**: build one excision task folder.

**How it works**: byte-exact body splice replaces the function body with
`raise NotImplementedError("excised")`. Verifier = the covering tests plus
conftest ancestors plus `run.sh`. If fewer than `min_assertions_touching_fn`
(3) assertions touch the function, a BIG agent adds edge-case tests.

- `input/`: repo tree with function body excised.
- `solution/`: the full repo tree.
- `verifier/`: covering test files + conftest ancestors + `run.sh`.

**Config**: `excision.excision_body`, `excision.strip_docstring`,
`excision.min_assertions_touching_fn`, `excision.copy_conftests`.


## History funnel

**Purpose**: select commits whose change makes a good benchmark task (a real
bug fix or feature, with tests that prove it).

**How it works**: all commits at/under `base_sha` go through hard filters,
signal scoring, SMALL-model classification, then diversity-aware shortlisting.

Hard filter reject reasons:
- `root-commit`: no parent, so no `input/` tree.
- `superseded-by-merge`: constituent commits of a surviving PR merge.
- `docs-or-ci-only`: changes only paths matching `ignore_paths` (.md, .rst,
  .github/, docs/, CHANGELOG*).
- `dependency-changing`: modifies setup.py, requirements*, pyproject.
- `no-source-change`: no `.py` changes in source directories.
- `too-small`: fewer than `min_source_lines_changed` (3) lines.
- `too-large`: more than `max_source_lines_changed` (300) lines or more than
  `max_source_files_changed` (6) files.
- `uncovered-and-no-tests`: functions touched have no coverage and the commit
  adds no tests.
- `unparseable`: AST parse failure at the commit.
- `non-pr-merge`: non-PR merge commits (back-merges) diff against an arbitrary
  first parent.
- `reverted`: identified by revert message or reverse patch-id.

Signal scoring: fix keywords (+1.0), adds tests (+2.0), public function (+1.0),
single function (+1.0), module diversity (+0.5), reverted (-3.0).

SMALL-model classification: labels each commit as bugfix, feature, refactor,
chore, or test-only, plus `self_contained` and `verifiable` flags. Only
`bugfix` and `feature` are kept. Batched, decisions persist by content hash.
Walks scored survivors until `shortlist_size` (20) are kept, classifying at
most `classify_max_commits` (60).

**Artifacts**: `output/<repo>/tasks/history_candidates.json`.

**Config**: `history.min_source_lines_changed`, `history.max_source_lines_changed`,
`history.max_source_files_changed`, `history.keep_kinds`, `history.shortlist_size`,
`history.build_target`, `history.classify_max_commits`,
`history.reject_non_pr_merges`, `history.reject_reverted`.

**On glom**: 1,050 commits considered. Major reject categories: docs-or-ci-only
(136), uncovered-and-no-tests (135), no-source-change (128), dependency-changing
(97). 441 scored survivors, 20 shortlisted, 9 built.


## build_history

**Purpose**: build one history task folder from a real commit.

**How it works**:
- `input/`: `git archive` at parent commit (PR merge uses first parent).
- `solution/`: `git archive` at the commit.
- Both get an additive hygiene overlay (Dockerfile, lock, constraints) that
  never overwrites historical files.
- The diff between input/ and solution/ is the real historical change.
- Verifier: the commit's own added/changed test functions (by AST diff).

**Static gates before any BIG call**:
- Tests passing on input/ are dropped (they would not fail-before).
- `min_failing_tests` must remain.
- Environmental drift check: if the commit's dependencies no longer resolve
  in the pinned image, the task is rejected as `env-drift`.

**Neutrality check**: a BIG model reviews the verifier tests for
implementation-specificity (does the test assert public interface behavior, or
internal details?). Flagged tests get a bounded rewrite (up to
`neutrality_rewrite_max_attempts`). Per-repo agent budgets cap total spend.

**No tests in the commit**: a BIG verifier agent (may see the diff, only
`verifier/` writable) authors tests.

**New-API features**: commits that introduce a new public symbol use the
`getattr` convention in verifier tests (`getattr(mod, name, None)`) so the
test produces an `AssertionError` on `input/` (a valid fail reason) instead
of an `ImportError` (invalid).

**Artifacts**: task folder under `tasks/<repo>/<task_id>/`.

**Config**: `history.neutrality_check`, `history.neutrality_rewrite_max_attempts`,
`history.max_agent_runs_per_repo`, `history.agent_max_turns`,
`history.verifier_agent_when_no_tests`, `history.allow_new_symbol_features`.

**On glom**: 9 built. Rejects during build: 5 verifier-fails-on-solution
(env drift on old commits), 3 verifier-not-implementation-neutral
(rewrite unchanged), 1 verifier-on-input:error_before_repo_call.
9 VALID.


## validate (harness)

**Purpose**: machine-validate each task and produce evidence.

**How it works**: the harness runs in-container on fresh workdirs with the
canonical verifier re-copied before each run:

1. **fail-before**: run verifier against `input/`. Must fail for the
   right reason (see valid/invalid lists below). At least `min_failing_tests`
   (1) tests must fail.

2. **pass-after**: run verifier against `solution/`. Must pass.

3. **determinism**: run fail-before and pass-after `determinism_runs` (3)
   times. Every test must produce the same result every time.

4. **collateral**: run the task's full baseline suite against `solution/`.
   No test that passed at baseline may now fail.

5. **static gate**: verifier tests may only import public symbols that exist
   in `input/`.

### Right-reason classification

The classifier categorizes each test failure. The harness enforces strict
lists:

**Valid fail reasons** (task is testing real behavior):
- `AssertionError`: an assertion about behavior failed.
- `pytest.raises`: a `pytest.raises` context caught the wrong exception
  or no exception.
- `NotImplementedError`: the excised body was reached.
- `exception_in_repo_code`: any exception whose traceback passed through
  repo code (not just test/framework code).

**Invalid fail reasons** (task is broken, not testing behavior):
- `ImportError` / `ModuleNotFoundError`: a module is missing.
- `SyntaxError`: syntax error during import.
- `AttributeError@import`: attribute error during module import.
- `collection_error`: pytest collection failed.
- `collected_0_items`: no tests collected.
- `fixture_not_found`: a pytest fixture is missing.
- `error_before_repo_call`: test errors before any repo code runs.
- `no_failing_test`: nothing failed.
- `no_report`: the test report was not generated.

A task with any invalid fail reason is marked INVALID and excluded from
selection.

**Artifacts**: `evidence/verdict.json`, `evidence/fail_before.log`,
`evidence/pass_after.log`, `evidence/determinism.json`,
`evidence/collateral.json`, raw `.report.json` files.

**Config**: `harness.determinism_runs`, `harness.strict_fail_reason`,
`harness.valid_fail_reasons`, `harness.invalid_fail_reasons`,
`harness.min_failing_tests`, `harness.recopy_canonical_verifier`,
`harness.verifier_visibility`.

**On glom**: 14 tasks validated. 13 VALID, 1 INVALID
(exc-glom.cli-mw_handle_target: the `face` CLI wrapper swallows the excision
error, so the strict classifier sees `error_before_repo_call`).

### Standalone validate

A task folder is self-contained. To re-validate:

```bash
docker build -t <image_tag> tasks/<repo>/<task_id>/input
python -m pipeline.validate tasks/<repo>/<task_id>
```

The harness builds the image from `input/Dockerfile` if missing (when
`harness.build_image_if_missing` is set). Exits 0 only if every task passed
is VALID.


## instruct

**Purpose**: write an implementation-neutral instruction, a golden rationale,
and a difficulty label for each VALID task.

### Instruction authoring

The BIG author sees only the input-side code (signatures, docstrings), verifier
tests, a masked behavior summary, the scope, and the verifier command. It never
sees the diff or the solution.

Two leak gates:
- **Gate (a)**: no line from the solution diff (>= `leak_min_tokens` tokens)
  may appear in the instruction. Lines also present in verifier tests are
  exempt.
- **Gate (b)**: no new identifier introduced by the diff may appear. Only
  API-like names (not locals/params) are checked, and names shorter than
  `leak_min_identifier_chars` (3) are ignored.

A BIG reviewer checks: is this a mechanical transcription of the tests? A
copy-paste edit? Is it self-contained? Implementation-neutral?

Failed instructions are regenerated up to `max_regenerations` (2). If still
failing, the task keeps a structural template and `instruction_status` is
set to `failed`.

Task titles are gated against the diff to prevent leaking commit messages
that contain implementation details.

### Golden rationale

`goldenSolution.md` explains why the solution is correct. This is the only
LLM call that may see the diff.

### Difficulty labelling

Code computes features from the graph and diff: `files_touched`,
`functions_touched`, `callers_count`, `cross_module_edges`, `diff_size`,
`similar_named_functions_nearby`, `test_count`. A BIG call assigns easy,
medium, or hard with a rationale that must cite at least one computed feature
by name=value.

**Artifacts**: `task.json` (updated with instruction, title, difficulty),
`goldenSolution.md`, `output/<repo>/tasks/instructions.json`.

**Config**: `instruction.show_diff_to_author` (false),
`instruction.leak_min_tokens`, `instruction.forbid_new_identifiers_from_diff`,
`instruction.max_regenerations`, `instruction.title_max_chars`,
`difficulty.features`, `difficulty.justification_must_cite_feature`,
`difficulty.target_spread`.

**On glom**: 13 VALID tasks, 13 final instructions. 0 regenerations, 0 leak
or reviewer rejections. Difficulty: easy 5, medium 4, hard 1 (soft target
was easy 2, medium 5, hard 3; the eligible pool skews easy).


## manifest

**Purpose**: write `tasks/<repo>/tasks.json` listing all built tasks.

Reads `validation_status` from each task's `evidence/verdict.json`.


## select

**Purpose**: pick exactly 10 VALID tasks under hard quotas.

**Quotas** (hard constraints):
- `min_history` >= 4 history tasks.
- `max_excision` <= 4 excision tasks.
- `max_netnew` <= 2 net-new tasks.
- `min_distinct_modules` >= 4 distinct modules across the 10.

**Soft objective**: difficulty spread (default target: easy 2, medium 5,
hard 3). The selector prefers candidates with more failing-on-input tests.
Deterministic (same inputs always produce the same selection).

An infeasible quota combination is a hard error (`SelectionInfeasible`),
never a silent shortfall.

Writes the root `tasks.json` (the final 10) and
`output/<repo>/tasks/selection.json` (why each eligible task was picked or
skipped).

**Config**: `selection.total_tasks`, `selection.min_history`,
`selection.max_excision`, `selection.max_netnew`,
`selection.min_distinct_modules`, `difficulty.target_spread`.

**On glom**: selected 10 = 6 history + 4 excision. Modules: glom.core,
glom.grouping, glom.matching, glom.reduction. Difficulty: easy 5, medium 4,
hard 1. Selected IDs: exc-glom.core-format_target_spec_trace,
exc-glom.reduction-Fold.glomit, exc-glom.grouping-GROUP,
exc-glom.matching-Check.glomit, hist-94b6375, hist-e515fb3, hist-0d75aab,
hist-4a48227, hist-a32abdd, hist-c2acc2b.
