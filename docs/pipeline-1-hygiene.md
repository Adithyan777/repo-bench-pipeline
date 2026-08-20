# Pipeline 1: hygiene

Brings a target repo to a reproducible, green-suite baseline inside a pinned
Docker image. Steps run in order: detect, pin, dockerfile, compose, build,
baseline, testgen, lint. Each step is resumable.


## detect

**Purpose**: identify ecosystem, packaging style, Python version, test framework.

**How it works**: checks for manifest files in priority order (pyproject.toml
`[project]` > poetry > setup.py > setup.cfg > requirements > none). Python
version is the highest CPython <= `detect.python_version_cap` (default 3.12)
satisfying `python_requires` and classifiers; defaults to 3.12 when the repo
has no version metadata.

Non-Python repos are rejected with a clear message.

**Artifacts**: `hygiene/detect.json` (packaging_style, python_version,
test_framework, extras).

**Config**: `detect.supported_ecosystems`, `detect.python_version_cap`,
`detect.python_version_default`, `detect.manifest_markers`.

**On glom**: detected setup.py, Python 3.12 (classifiers list >3.12, capped),
pytest.


## pin

**Purpose**: produce a fully pinned, hashed lockfile from whatever the repo
ships.

**How it works**: synthesizes a single `pipeline-requirements.in` (never
overwrites a repo's own file) from the detected manifest. Folds in extras
named `test`, `tests`, `testing`, `dev` when present, with a retry-without on
failure. Adds pipeline tools (pytest, coverage, pytest-json-report, ruff).
Runs `uv pip compile --generate-hashes` to produce `requirements.lock.txt`
plus `constraints.txt`.

For repos with no manifest: an AST import scan extracts third-party imports,
maps them through a built-in alias table (yaml -> PyYAML, cv2 -> opencv-python,
etc.), uses a SMALL-model call for unknown mappings, verifies each with `uv`,
re-asks once on failure, then drops and records any that still fail
(`unresolved_imports` in the step record).

Manifest dependencies are never dropped.

**Artifacts**: `pipeline-requirements.in`, `requirements.lock.txt`,
`constraints.txt`, `hygiene/pin.json`.

**Config**: `pin.resolver`, `pin.generate_hashes`, `pin.include_extras`,
`pin.alias_reask_attempts`, `detect.import_alias_table`.

**On glom**: 0 LLM tokens (manifest present), 13 pins, no unresolved imports.


## dockerfile

**Purpose**: write a digest-pinned Dockerfile and `.dockerignore`.

**How it works**: renders a Dockerfile from `python:{version}-slim` with the
base image digest pinned via `docker pull`. Installs with
`pip install --no-deps --require-hashes -r requirements.lock.txt`.
When the version is git-derived (setuptools-scm, hatch-vcs, etc.), `.git` is
kept in the build context and `git` is installed via `apt-get` so the version
resolves.

**Artifacts**: `Dockerfile`, `.dockerignore`, `hygiene/dockerfile.json` (base
digest).

**Config**: `docker.base_image`, `docker.pin_base_image_digest`,
`detect.git_version_tools`.

**Edge case (toolz, observed during development; no artifacts committed)**: a
git-versioned repo's version failed because
`.dockerignore` dropped `.git` and the slim image has no `git`. Fixed by
detecting `git_version_tools` in the build deps and keeping `.git` + installing
git.


## compose

**Purpose**: detect service dependencies (postgres, redis) and write a
docker-compose.yml template if needed.

**How it works**: checks imports (psycopg2, asyncpg, redis), `.env.example`
URLs (DATABASE_URL, REDIS_URL), and existing compose files. Writes a template
for supported services (postgres, redis). Detection only; the template is
generated, not actively used by the pipeline's own test runs.

**Config**: `detect.service_import_signals`, `detect.service_env_signals`,
`docker.compose_supported_services`, `docker.compose_service_images`.

**On glom**: no services detected.


## build

**Purpose**: build the `bench-<repo>` Docker image.

**How it works**: runs `docker build` with the `bench-pipeline=1` label. On
failure, a bounded LLM repair agent (BIG tier, up to 3 attempts) reads the
build log and edits the Dockerfile or requirements. The agent has `read_file`,
`grep`, and `write_file` tools but no `run` (no image exists yet to run in).
Edits are audited.

**Artifacts**: `hygiene/build.json` (image_tag, image_digest, attempts).

**Config**: `agent.docker_repair_max_attempts`.

**On glom**: built on first attempt, 0 LLM tokens.


## baseline

**Purpose**: run the existing test suite in-container and establish a passing
baseline.

**How it works**: detects test framework (pytest > unittest > none). Runs with
`pytest-json-report` for structured output. Classifies failures as environment
(missing optional dep, network, version mismatch) or genuine. Pipeline for
failures:
1. Environment failure with a missing dep: add dep, re-lock, rebuild.
2. Genuine failures: one bounded agent fix restricted to `tests/**`, `conftest.py`,
   Dockerfile, and dependency files. Source edits outside allowed paths are reverted
   and audited.
3. Remaining failures: quarantined via `--deselect` (never deleted, never faked).
4. Still failing after quarantine: hard stop.

No test framework at all: bootstraps a pytest layout, baseline passes trivially,
test-gen becomes the primary source of tests.

**Artifacts**: `hygiene/baseline.json` (per-test status, quarantined list,
classifications), `test_command.txt`.

**Config**: `baseline.framework_priority`, `baseline.quarantine_file`,
`baseline.agent_fix_allowed_globs`, `agent.baseline_fix_max_attempts`.

**On glom**: 202 tests passing, 0 quarantined, 0 LLM tokens. Note that
`baseline.json` is re-recorded after test generation (`testgen_refreshed:
true`), so the committed record holds the post-generation count of 239; 202 is
the suite as glom shipped it.


## testgen

**Purpose**: generate tests for under-covered functions, gated by mutation
testing.

**How it works**:

1. **Ranking** (deterministic): runs `coverage run -m pytest` + `coverage json`
   in-container. Scores each function by
   `uncovered_ratio * log(1 + lines) * (1 + complexity/5) * public_bonus`.
   Filters out `__init__.py` re-exports, CLI main(), functions < 3 lines,
   dunder methods, test code, and `_private` functions below
   `private_min_complexity`. Groups by module, takes the top-K modules, top-N
   functions per module.

2. **Agent** (BIG tier): writes `tests/generated/test_<mod>.py` (or beside
   existing tests if `place_beside_existing_tests` is true). Sees the target
   function source, module imports, and examples of existing test style.

3. **Mutation gate**: tests must pass on real code AND kill at least 1 of 4
   AST mutants per targeted function. Mutant operators: comparison_flip,
   comparison_boundary, arithmetic_swap, and_or_swap, return_none,
   constant_tweak, statement_delete. A kill is a real test failure with
   collection intact (checked via json-report). Retries up to 2 times with
   mutant feedback. Tests that kill nothing are dropped entirely.

Generated tests are excluded from the ranking coverage so reruns are 0-token.
Decisions persist per module.

**Artifacts**: `hygiene/testgen.json`, `testgen_targets.json`,
`testgen_decisions.json`; test files in the repo clone.

**Config**: `testgen.top_k_modules`, `testgen.top_n_functions_per_module`,
`testgen.mutants_per_function`, `testgen.min_mutants_killed`,
`testgen.max_agent_runs_per_repo`, `testgen.agent_max_turns`,
`testgen.mutators`, `testgen.enabled`.

**On glom**: 4 modules ranked, 9 target functions. Kept glom.cli (3/3
functions, 10/12 mutants killed) and glom.streaming (1/1, 4/4). Dropped
glom.core and glom.grouping: the agent never wrote a test file
(`dropped_no_file`). `testgen.json` records `stopped: reached max turns` for
glom.core; glom.grouping's summary is empty. Suite after: 239 tests passing,
verify-twice identical. Testgen tokens: ~550k (70% of the run's total).

**Edge case**: a 30-turn budget was tried for glom.core during development.
The agent still explored without writing. The prompt now includes a "write
early" instruction, and the per-repo budget (`max_agent_runs_per_repo`) caps
total agent cost.


## lint

**Purpose**: run ruff lint + format, leaving the repo lint-clean when possible.

**How it works**: runs `ruff check --fix` and `ruff format` in-container on a
copy of the repo. Writes a minimal `[tool.ruff.lint]` section into
`pyproject.toml` if absent (does not break a `setup.py` install). Applies
per-line `# noqa` for unfixable findings. Syncs the changes back to the clone,
rebuilds the image, and runs the full suite twice.

If any formatting or lint change regresses a baseline-passing test, the entire
step is reverted. The repo ships un-linted with all findings recorded in
`hygiene/lint.json`.

Historical task trees are never linted. A history task's input-to-solution diff
stays the real historical change.

Pipeline commits inside the repo clone:
- `pipeline: pin dependencies and containerize`
- `pipeline: baseline and quarantine`
- `pipeline: generated tests`
- `pipeline: lint and format`

The original HEAD is recorded in `hygiene/pipeline_base.json` so later stages
mine only pre-pipeline history.

**Artifacts**: `hygiene/lint.json` (files_changed, unfixable, noqa counts,
regressed flag).

**Config**: `lint.enabled`, `lint.rules`, `lint.autofix`, `lint.format`,
`lint.allow_noqa_for_unfixable`.

**On glom**: 34 files would change, 265 unfixable findings across 23 files.
REVERTED because 7 `glom/test/test_error.py::*_stack` tests assert exact
rendered source lines; any edit to `core.py` (including formatting) breaks
them. Recorded in `lint.json` (regressed: true). The repo ships un-linted.
