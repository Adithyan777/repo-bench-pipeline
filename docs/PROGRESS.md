# Progress

Handoff file between implementation sessions. One session per step, sequential.
Every session: read `docs/DESIGN.md`, `HEURISTICS.md`, `pipeline/config.py`, this file; do its step; update its row + notes; leave changes staged (author commits).

Legend: `todo` · `in-progress` · `review` (awaiting author review) · `done`

| Step | Scope | Status | Session notes |
|---|---|---|---|
| S1 | Steps 0+1: fixture repos (`tests/fixtures/mini_pkg`, `mini_pkg_notests`), package skeleton, `state` (resumability), `docker.run_in_container` + image build, LLM client (big/small, reasoning per tier, schema-forced JSON, retries, usage log, record/replay), agent loop + tools, foundation tests | review | See `### S1`. `pytest` → 32 passed (Docker live). Cassettes recorded (1049 tokens). Kimi-K2.6 tool-calling-with-thinking day-1 check PASSED. |
| S2 | Step 2+2b: P1 core — detect → synthesize requirements → uv lock → Dockerfile/compose → build → baseline + quarantine; `ecosystems/python.py`; run on glom, then toolz + minidump | review | See `### S2` (+ round-2 fixes). glom/toolz/minidump/fixtures green; glom & toolz twice-identical ✓; toolz 0-LLM/no-agent after F1. `pytest` → 72 passed / 3 slow. |
| S3 | Step 3: P2 static — repo_graph.json, history_index, test_map, coverage, hotspots, graph self-verification | todo | |
| S4 | Step 4: excision funnel + validation harness end-to-end → first VALID task; task folder format, evidence, verdict, tasks.json writer | todo | |
| S5 | Step 5: history funnel + task-builder agent (verifier authoring/neutrality, instruction + leak gates, difficulty) | todo | |
| S6 | Step 6: P1 test-gen + AST mutators + mutation gate | todo | |
| S7 | Step 7: P2 .okf/ writer + claim verifier | todo | |
| S8 | Step 8: net-new funnel + builder | todo | |
| S9 | Step 9: lint/format, selection & quotas, tasks.json, report_data → REPORT skeleton, transcripts curation, HEURISTICS review with author | todo | |
| S10 | Step 10: held-out dry-run on toolz + minidump, fresh clone, twice, diff; fix generality bugs | todo | |

## Notes per session

Append under a `### S<n>` heading: what exists, what is stubbed, known issues, thresholds added to `config.py`/`HEURISTICS.md`, exact test command, anything the next session must know.

### S1

**Environment / setup**
- Project venv: `uv venv --python 3.12 .venv` then `uv pip install -r requirements-dev.txt`
  (openai 3.1.0, jsonschema 4.26.0, pytest 9.1.1, ruff 0.16.3 — pinned).
- Docker: OrbStack. `run_in_container` uses `python:3.12-slim`; images pull on first use.

**What exists (real, tested)**
- `tests/fixtures/build_mini_pkg.py`: reproducible builder for both fixture repos.
  Deterministic SHAs (fixed author/committer + per-commit dates). `.git` dirs are NOT
  committed — the builder recreates them; `conftest.py` builds on demand if missing.
  Both fixture repos are gitignored.
  - `mini_pkg/`: 3 modules (calc/core/text), setup.py with one dep (`wcwidth`), pytest
    tests covering some (not all) functions, 6 commits: init → text feature → **docs-only**
    → **dep change (wcwidth)** → **bugfix `ceil_div` off-by-one + test in same commit** →
    **refactor**. The bug is invisible to the pre-existing tests and only caught by the
    test added in the fix commit (good history-task material for S5).
  - `mini_pkg_notests/`: 3 modules, **no tests, no manifest**; imports `yaml` (alias →
    PyYAML) and `wcwidth` (identity) to exercise the AST-inferred-deps path in S2.
- `pipeline/` skeleton per DESIGN "Repo layout": `cli.py`, `config.py`, `state.py`,
  `docker/`, `llm/`, `agent/`, `ecosystems/base.py`, and importable empty `hygiene/`,
  `knowledge/`, `tasks/`, `report/`. `run.sh` wraps `python -m pipeline.cli`.
- `ecosystems/base.py`: `EcosystemAdapter` ABC (11 methods) — interface only.
- `state.py`: `output/<repo>/state.json`, per-step `{status,input_hash,finished_at}`,
  content-based `hash_inputs`, `should_run` skip-if-unchanged, `--force`, `--fresh`.
- `docker/`: `run_in_container(workdir, cmd, image, timeout, network_none)` →
  `CommandResult`; kills the container and returns exit 124 on timeout; `--network none`
  by default. `fresh_workdir` context manager (copytree per unit of work).
  `build_image(context_dir, tag)` → image id; `resolve_base_digest(ref)` → `repo@sha256:…`.
- `llm/`: OpenAI-compatible client. Secrets from `LLM_BASE_URL`/`LLM_API_KEY` (read from
  `.env`), never logged. Tier + model per step via `config.model_for`/`reasoning_for`; reasoning
  translated per model via `MODEL_CAPS` (DeepSeek `reasoning_effort`; Kimi
  `chat_template_args.enable_thinking`). `complete_json` = forced tool call + client-side
  jsonschema validation + error-back-to-model retry (`max_schema_retries`) + fenced-JSON
  fallback. Exponential backoff on API errors. Usage accounting incl.
  `completion_tokens_details.reasoning_tokens` → `audit/llm_usage.json`;
  `max_tokens_per_repo` cap. Transcript per call under `transcripts/pipeline/<stage>/`.
  Record/replay via `LLM_MODE` + cassettes under `tests/cassettes/<stage>/`.
- `agent/`: `Agent(llm, step, system_prompt, tools, files_changed, …)` behind
  `AgentRunner`. OpenAI function calling; loop ends on no-tool-calls (no `done` tool);
  tool errors returned as text; hard stop on `max_turns`; tool results truncated to
  `max_tokens_per_tool_result`. Result `{files_changed, summary, trajectory_path}`,
  trajectory written under `transcripts/agent/<step>/`. Tools: `read_file`, `grep`,
  `write_file`, `run` (only via `run_in_container`). Graph/okf tools (`show_symbol`,
  `callers`, `callees`, `tests_for`, `show_commit`, `okf`) registered as stubs that raise
  `NotImplementedError` with a clear message.
  - Sandbox guards: `read_file`/`write_file` reject paths escaping the workdir; `grep`
    skips symlinks and any file resolving outside the workdir (test:
    `test_grep_does_not_follow_symlink_outside_workdir`).

**What is stubbed / deferred**
- `cli.py` parses all documented flags and sets up run dir + state, but stage dispatch
  raises "not implemented yet (S2+)". No stage logic yet.
  - **Sharp edge:** `cli.apply_overrides` mutates the module-global `DEFAULT` config in
    place (it operates on `DEFAULT`, not a copy). Fine for a single CLI run; if S2+ ever
    constructs multiple configs in one process, give each run its own `Config()` instead.
- Graph/okf agent tools raise until S3 (graph) / S7 (okf).
- `Agent` takes `step` (not a bare `model`) as the model selector — it maps to model +
  reasoning via config, honoring the two-tier design. Same object, clearer wiring.

**Config / heuristics added** (all PROPOSED in HEURISTICS.md)
- `llm.big_max_tokens=8192`, `llm.small_max_tokens=2048` (Kimi thinking headroom),
  `llm.cassette_dir="tests/cassettes"`.
- `agent.chars_per_token=4`, `agent.grep_max_matches=100` (moved out of code constants).
- Env vars: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODE`. (Baseten-specific `BASETEN_*` names
  dropped — one generic env pair, no provider coupling.)

**Exact test command**
```
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r requirements-dev.txt
.venv/bin/python -m pytest
```
Result: **32 passed** in ~11s, with the Docker daemon running. `ruff check` clean.

**Cassettes — recorded and committed**
- `tests/cassettes/s1_smoke/` (1 file) + `tests/cassettes/s1_agent/` (2 turns).
- Recording spend: **1049 tokens total** — `p1.pin.import_to_pypi` 327 (DeepSeek),
  `p1.docker.repair_agent` 722 incl. 121 reasoning (Kimi, thinking on).
- **Day-1 check PASSED:** Kimi-K2.6 drives OpenAI function-calling correctly with thinking
  on (write_file → run → summary), so no GLM-5.2 fallback needed for BIG agents.
- Re-record if the smoke prompts change: `LLM_MODE=record .venv/bin/python
  scripts/record_cassettes.py` (needs `.env` + Docker). Shared request-building lives in
  `tests/_smoke.py` so recorder and tests match by cassette key. Cassettes are secret-free
  (the API key rides in HTTP headers, never in the recorded request).

**Things S2 must know**
- Use `run_in_container(workdir, cmd, image, …)` for ALL code execution — image is a
  required arg (one `bench-<repo>` image per target). `fresh_workdir` gives isolation.
- `EcosystemAdapter` is the only place ecosystem-specific code belongs; implement
  `ecosystems/python.py` against `base.py`.
- Every new threshold/flag → `config.py` + a PROPOSED row in HEURISTICS.md. No inline
  magic numbers.
- All heuristic values remain PROPOSED pending the author's HEURISTICS review (S9).

### S2

**What exists (real, tested)**
- `ecosystems/python.py` — `PythonAdapter` (ALL Python/packaging logic). Constructed with
  `work_dir` (the repo clone, where requirements.in/lock/constraints/Dockerfile/.dockerignore
  are written) and an optional `llm`. Implements detect, `packaging()` (pyproject[project] /
  poetry / setup.py / setup.cfg / requirements / none), `python_version` (requires-python via
  `packaging.SpecifierSet`, else classifiers, capped at 3.12), `synthesize_requirements`,
  `lock` (single `uv pip compile` path: manifest + synthesized tools requirements.in, extras
  folded in), `write_dockerfile`, `test_command`/`reporting_command`, `test_framework`(+bootstrap),
  `parse_test_report` (pytest-json-report). `infer_third_party_imports` (AST) + alias table +
  SMALL-model fallback for no-manifest repos. Poetry deps translated (caret/tilde → specifiers).
  `lint_and_format`/`symbol_index`/`mutators` raise NotImplementedError (S9/S3/S6).
- `hygiene/` — one resumable module per step: `detect`, `pin`, `dockerfile`, `compose`
  (detection-only, postgres/redis template), `build` (build image once + bounded repair agent),
  `baseline` (in-container run → classify → env-fix → agent-fix → quarantine). `runner.py`
  orchestrates through `state.py` with per-step timing, commits pipeline edits as labeled commits,
  records the original `base_sha`, writes `report_data.json` + `llm_usage.json`.
- `cli.py` wires `--stage hygiene` (loads `.env`), plus `--verify-twice`. `run.sh` works E2E.

**Resolver choice (verified, not assumed)**: `uv pip compile --generate-hashes --python-version X
--no-header [--extra ...] <manifest> requirements.in -o requirements.lock.txt`. uv reads
setup.py/pyproject[project]/requirements directly and does NOT emit the project itself into the
lock; the synthesized requirements.in adds pytest/coverage/pytest-json-report/ruff. constraints.txt
= lock with hashes stripped. Report format: **pytest-json-report** (richer failure reason than
junitxml → better env-vs-genuine classification).

**Output layout / where S3 finds things** (per `output/<repo>/`):
- `repo/` — clean clone with pipeline commits on top; `hygiene/pipeline_base.json` has
  `base_sha` (original HEAD) — **P3 mines only commits at/under base_sha**.
- `hygiene/detect.json` (packaging_style, python_version, test_framework, extras),
  `pin.json` (pins), `dockerfile.json` (pinned base digest), `compose.json`, `build.json`
  (`image_tag`, `image_digest`), `baseline.json` (per-test status+reason, quarantined,
  classifications), `test_command.txt` (the documented command).
- `audit/agent_actions.jsonl` (only if a repair/fix agent ran), `audit/llm_usage.json`.
- `report_data.json` (per-stage timing + llm_usage). Image tag = `bench-<repo>`.
- `runner.hygiene_paths(run_dir)` returns these paths for S3.

**Per-repo results (2b, real runs)**

| Repo | Style | Py | Image built | Baseline | Quarantined | Twice-identical | LLM tokens |
|---|---|---|---|---|---|---|---|
| mini_pkg | setup.py | 3.12 | yes | 11 passed | 0 | yes | 0 |
| mini_pkg_notests | none (AST) | 3.12 | yes | 0 (bootstrapped) | — | — | 414 (alias) |
| glom | setup.py | 3.12 | yes | **202 passed** | 0 | **yes** | 0 |
| toolz | pyproject | 3.12 | yes | 186 passed | 0 | yes | 0 |
| minidump | setup.py | 3.12 | yes | 0 (bootstrapped) | — | — | 0 |

glom is the acceptance target: image builds, baseline all-pass, identical twice. Total real-run
LLM spend: **414 tokens** (one SMALL alias call on mini_pkg_notests).

**CORRECTION (was mis-reported):** the FIRST toolz run was NOT clean. toolz derives its version
from git tags (`setuptools-git-versioning`); `.dockerignore` dropped `.git` and slim has no git,
so `toolz.__version__` resolved to `0.0.1` and `test_has_version` failed. It classified as `env`
but with no `missing_dep`, so the **agent-fix ran (76,883 tokens) and patched SOURCE**
(`toolz/__init__.py`) — exactly the failure the F1 fixes prevent. After the fixes below, toolz
builds with git available and the version resolving: **186 passed, 0 quarantined, 0 LLM, no
agent, source untouched** (verified `git diff` on `toolz/`).

**Thresholds added** (config.py + PROPOSED in HEURISTICS.md): `pin.include_extras`,
`pin.alias_reask_attempts`, `pin.requirements_in_filename`, `pin.constraints_filename`,
`baseline.report_filename`.

**Exact test command**
```
.venv/bin/python -m pytest            # fast: unit + real uv/docker/git; skips `slow`
.venv/bin/python -m pytest -m slow    # resumability, run-twice, quarantine (multi-build)
```
Result: **72 passed, 3 deselected** (fast) + **3 passed** (slow). ruff clean.

**Cassettes — recorded and committed.** `s2_pin` (import→PyPI, `serial`→`pyserial`, 412 tokens),
`s2_baseline` (classify: yaml→env/PyYAML, math→genuine, 518 tokens), `s2_reask` (re-ask on
unresolvable invented import, 470 tokens). Re-record with
`LLM_MODE=record .venv/bin/python scripts/record_cassettes.py`; request builders live in
`tests/_smoke.py` (`run_alias_map`, `run_classify`, `run_reask`) so recorder/tests match by key.
S2 cassette spend: **1400 tokens**.

**Review fixes applied**
- setup.cfg-only repos are now handled correctly: **uv cannot read setup.cfg alone** (verified),
  so the adapter parses `install_requires`/`extras_require`/`python_requires` via `configparser`
  into requirements.in and writes a `setup.py` shim (`from setuptools import setup; setup()`) so
  `pip install -e .` works. Tests: `test_detect_setup_cfg_only`, `test_pin_setup_cfg_only`.
- Extras fallback: if `uv pip compile` fails **with** extras, `lock()` retries once **without**
  them; dropped extras are recorded in `pin.json`, appended to `detect.json`, and surfaced in
  `report_data.json`. Test: `test_lock_drops_unresolvable_extra`.
- `base.py` docstring now documents the adapter construction contract `(config, work_dir, llm)`.

**Import→PyPI mapping (`p1.pin.import_to_pypi`) — propose → resolve → re-ask (implemented)**:
the mapping is a SMALL classification call (model maps `serial`→`pyserial`), NOT a pip-probing
agent (per-import probing is expensive). The deterministic verifier is `uv pip compile` against
real PyPI. `lock()` now closes the loop (principle #1: LLM proposes, code disposes): on an
unresolvable **inferred** import, it parses uv's "not found in the package registry" error,
re-asks the model once (`pin.alias_reask_attempts=1`) with the error, retries the lock; if it still
won't resolve it **drops** the import and records it in `pin.json:unresolved_imports` +
`detect.json` + `report_data` — the repo continues, never fails on a bad guess. Manifest deps are
never dropped (only names in the inferred map). Test: `test_alias_reask_then_drop` (cassette
`s2_reask`, 470 tokens).

**Stubbed / deferred**: lint/format (S9), test-gen + mutators (S6), symbol_index/graph (S3),
knowledge/tasks stages. compose emits templates for postgres/redis only (else "unsupported").

**Things S3 must know**
- Build on `output/<repo>/repo` (has git + pipeline commits). Mine history at/under
  `hygiene/pipeline_base.json:base_sha` only.
- Image tag `bench-<repo>` / digest in `build.json`; run everything via `run_in_container`.
- `baseline.json` has the stable test set (status per nodeid) P3 needs.
- `PythonAdapter.symbol_index` is the S3 entry point (currently raises NotImplementedError).

#### S2 review round 2 — NO-GO fixes applied

- **F1 baseline/agent safety** (toolz): (b) git-derived versions detected via
  `detect.git_version_tools`; such repos keep `.git` in the build context and install `git`
  in the image so the version resolves at build (ENV fix, no source edit) — toolz now
  186-pass/0-LLM/no-agent. (c) the agent-fix may ONLY change
  `baseline.agent_fix_allowed_globs` (tests/config/deps); any edit outside is reverted
  (tracked → `git checkout`, untracked → removed) and recorded. (d) failures classified `env`
  with no actionable `missing_dep` go to **quarantine, never the agent**; the agent-fix now
  targets only `genuine` failures. (e) `agent_actions.jsonl` records goal, files_changed,
  reverted_disallowed, diff, attempts, and the real (re-run-verified) outcome.
- **F2** `synthesize_requirements` writes a pipeline-owned file
  (`pin.requirements_in_filename="pipeline-requirements.in"`) so a repo's own `requirements.in`
  is never overwritten. Test: `test_synthesize_does_not_overwrite_repo_requirements_in`.
- **F3** `parse_test_report` maps skipped/xfailed/xpassed → `skip`, excluded from failures.
  Test: `test_parse_report_maps_skips`.
- **F4** LLM-provided package names are validated (`valid_requirement` = packaging.Requirement
  + name regex) before being written; invalid names are dropped and recorded as unresolved.
  Tests: `test_valid_requirement`, `test_infer_drops_invalid_mapping`.
- **F5** input hashes: pin now hashes setup.cfg (that style) + the AST import set (style none);
  baseline hashes conftest + the whole tests dir + test*.py. Tests:
  `test_pin_hash_invalidates_on_import_change`, `test_baseline_hash_invalidates_on_test_change`.
- **F7** `_env_fix` catches lock/build failure → records `env_fix_failed` and falls through to
  quarantine; refreshes `build.json` digest on a successful rebuild. Test:
  `test_env_fix_failure_falls_through`.
- **F8** repo name sanitized for run-dir + docker tag (`sanitize_name`: lowercase,
  `[^a-z0-9._-]→-`, reject empty/`.`/`..`). Test: `test_sanitize_name`.
- **F9** `record_cassettes.py` skips stages that already have cassettes unless
  `--rerecord <stage>` (or `--rerecord all`); stops the multi-turn s1_agent churn.

**Deferred (with rationale) — for a later session:**
- **F6** collection-broken path + `baseline.treat_collection_broken_as_no_tests_after_repair` /
  `baseline.env_fix_attempts` are currently INERT (baseline handles no-tests and a single
  env-fix, but does not yet implement the "collection broken → one repair → treat as no tests"
  branch, and `env_fix_attempts` is not read as a loop count). Either implement the branch or
  delete the flags in S3/S6 cleanup. No repo in scope hit collection-broken.
- **F10** magic numbers / ecosystem leakage: a few string literals remain in the hygiene layer
  (e.g. `"Dockerfile"`, `".dockerignore"`, report phase names, the `apt-get git` line). Docker
  filenames are conventional, but the agent-fix allowed-globs duplicate some names; consolidate
  into config/adapter in cleanup. The hygiene layer stays ecosystem-agnostic except where it
  calls the adapter.
- **F11** remaining test gaps: no real requirements-only or poetry-only END-TO-END build test
  (unit-level detect/pin/translate covered); compose emission only unit-tested; the git-versioning
  build is validated by the real toolz run, not a fixture. Add fixtures in S3+ as needed.
