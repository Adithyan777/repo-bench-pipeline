# Progress

Handoff file between implementation sessions. One session per step, sequential.
Every session: read `docs/DESIGN.md`, `HEURISTICS.md`, `pipeline/config.py`, this file; do its step; update its row + notes; leave changes staged (author commits).

Legend: `todo` · `in-progress` · `review` (awaiting author review) · `done`

| Step | Scope | Status | Session notes |
|---|---|---|---|
| S1 | Steps 0+1: fixture repos (`tests/fixtures/mini_pkg`, `mini_pkg_notests`), package skeleton, `state` (resumability), `docker.run_in_container` + image build, LLM client (big/small, reasoning per tier, schema-forced JSON, retries, usage log, record/replay), agent loop + tools, foundation tests | review | See `### S1`. `pytest` → 32 passed (Docker live). Cassettes recorded (1049 tokens). Kimi-K2.6 tool-calling-with-thinking day-1 check PASSED. |
| S2 | Step 2+2b: P1 core — detect → synthesize requirements → uv lock → Dockerfile/compose → build → baseline + quarantine; `ecosystems/python.py`; run on glom, then toolz + minidump | review | See `### S2` (+ round-2 fixes). glom/toolz/minidump/fixtures green; glom & toolz twice-identical ✓; toolz 0-LLM/no-agent after F1. `pytest` → 72 passed / 3 slow. |
| S3 | Step 3: P2 static — repo_graph.json, history_index, test_map, coverage, hotspots, graph self-verification | review | See `### S3` (+ review-round fixes). mini_pkg/glom/toolz/minidump all built; graph byte-identical twice; verification precision 1.0 on every edge type, 0 mismatches. `pytest` → 96 passed / 3 slow. NO LLM. |
| S4 | Step 4: excision funnel + validation harness end-to-end → first VALID task; task folder format, evidence, verdict, tasks.json writer | review | See `### S4`. `--stage tasks` wired (funnel → build → validate → manifest). glom **4/5 VALID**, toolz **5/5** (after review fixes), mini_pkg 3/3 in tests (relaxed thresholds). Harness idempotent. `pytest` → 124 passed / 3 slow, `ruff check .` clean. LLM: SMALL screen (decisions persisted + reused) + one bounded top-up agent. |
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

### S3

**Ordering deviation (approved by author).** The prompt/DESIGN 4.1 listed the graph before the
index files, but graph nodes carry coverage % / test refs and the `tested_by` edges — all derived
from test_map/coverage (a container run). So the knowledge runner runs
**`symbol_index → indexes → graph → verify`** (indexes before graph). DESIGN Step 3 + 4.1 wording
updated to match. **NO LLM anywhere in this layer.**

**Complexity metric (approved).** Own McCabe branch counter (`graph.complexity_metric =
"branch_count"`, `ecosystems/symbols.py:_complexity`), not radon — dependency-free, version-stable,
deterministic. Counted constructs documented in HEURISTICS.md.

**What exists (real, tested)**
- `ecosystems/symbols.py` — the ONLY ecosystem-specific S3 code (`PythonAdapter.symbol_index` calls
  it). Pure AST: per module → classes/functions/methods (file, qualname, span, signature via
  `ast.unparse`, docstring, complexity, is_public, decorators), module/local imports, inheritance,
  and intra-repo call sites **resolved by name only** (Name → top-level def / from-import; `self.m`
  → enclosing class method; `alias.f` → imported module symbol). Calls not resolvable to a repo
  symbol go in `unresolved_calls`, **never guessed**. Test files indexed but flagged `is_test`
  (kept out of the source node set). Also `functions_in_source`/`path_to_module` for historical
  blobs. Import target resolution is deferred to a finalize pass so it is independent of file order.
- `knowledge/graph.py` → `repo_graph.json` (DESIGN 4.1). Nodes = source modules/classes/functions;
  edges = imports/contains/calls/inherits/tested_by, **every edge carries `evidence{file,line}`**.
  Coverage % + `tested_by` joined from indexes. `setup.py` (and any `graph.nonsource_files`) excluded
  from nodes. Nodes deduped by id (a module that rebinds a name keeps the final definition — e.g.
  toolz `examples/fib.py` defines `fib` 3×). Fully sorted + repo-relative paths + no timestamps →
  **byte-identical across runs** (verified on mini_pkg and glom).
- `knowledge/indexes.py` → `history_index.json` (ORIGINAL commits at/under `base_sha` via
  `git rev-list`; touched functions resolved by parsing the file **as it was at that commit**
  (`git show sha:path`) and intersecting `--unified=0` diff hunks with those AST spans — never HEAD
  spans (with `--no-renames`); manifest-touch flag; PR number; merge flag), `test_map.json` +
  `coverage.json` (ONE container run: `coverage run -m pytest` with an in-container pytest plugin
  that sets each test's coverage context to its exact pytest nodeid, then
  `coverage json --show-contexts -i`, joined to source spans), `hotspots.json` (change frequency
  from history).
- `knowledge/verify.py` → `graph_verification.json`. Samples edges (even share per type,
  deterministic), re-derives each by a DIFFERENT path (imports=regex, contains=second parse,
  inherits=second parse, calls=second parse of the exact caller — qualname-aware, handles
  same-named methods across classes and redefinitions), tested_by=test_map membership; **symbol
  existence by importing each module IN THE CONTAINER**. Import failures (optional/platform deps,
  doc/build scripts) are reported as `unimportable_modules`, separate from real `missing_attr`
  mismatches, so cross-platform code (minidump's Windows modules) never dings precision.
- `knowledge/runner.py` + `--stage knowledge` in `cli.py` (`--stage all` = hygiene → knowledge).
  Resumable via `state.py` (input hashes over source tree / baseline+build / knowledge artifacts),
  per-step timing into `report_data.json`.
- Agent tools implemented (were stubbed in S1): `show_symbol`, `callers`, `callees`, `tests_for`
  (graph-backed), `show_commit` (history_index, git fallback). `okf` **stays stubbed** (S7).
  `graph_tools(ctx)` in `agent/tools.py`; `ToolContext` gained `knowledge_dir` + `repo_root`.

**Per-repo results (real runs)**

| Repo | src mods | nodes | contains | calls | imports | inherits | tested_by | unresolved calls | test_map (tests) | verify precision | symbol-existence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mini_pkg | 5 | 22 | 17 | 2 | 3 | 0 | 20 | 20 | 11 | 1.0 all | 14/14 (1.0) |
| glom | 12 | 379 | 367 | 235 | 16 | 17 | 3710 | 2502 | 194 | 1.0 all | 129/129 (1.0), 1 unimportable (docs `conf.py`) |
| toolz | 20 | 183 | 165 | 81 | 27 | 0 | 853 | 1425 | 182 | 1.0 all | 124/124 (1.0), 4 unimportable (docs conf + example scripts) |
| minidump | 50 | 726 | 676 | 227 | 80 | 19 | 0 | 1959 | 0 (no tests) | 1.0 all | 194/194 (1.0), 7 unimportable (Windows-only) |

(Counts above are from FRESH outputs after the round-2 fixes: relative-import resolution raised
glom imports 9→16 / inherits 13→17 / calls 198→235, toolz imports 12→27, minidump imports 54→80.)

- 0 mismatches on every repo; 0 duplicate node ids; graph byte-identical across two runs.
- test_map is now keyed by the **exact pytest nodeid** (a tiny in-container pytest plugin switches
  coverage's context per test), so **parametrized/inherited cases are captured distinctly** — all
  202 glom test contexts are seen. glom's test_map is 194 of 202 because the other 8 tests execute
  no indexed source function (e.g. CLI/error-message tests), not because of a context collapse.
  (The earlier "doctests" note was wrong — the gap was the dynamic-context collapse of parametrized
  tests, now fixed.) `tested_by` edges collapse a test's parametrizations to one base nodeid.
- minidump has no tests → test_map/coverage empty by design (`coverage_status: no_tests`); graph
  still complete.
- "unresolved calls" are high because they include every builtin/stdlib/external/method-on-local
  call (e.g. `len`, `self.x.append`, `pytest.raises`) — by design these are listed, never invented
  as edges.

**Exact test command**
```
.venv/bin/python -m pytest            # fast: AST + real git + one docker coverage round-trip
.venv/bin/python -m pytest -m slow    # hygiene multi-build resumability/quarantine
```
Result: **98 passed, 3 deselected** (fast) + **3 passed** (slow). ruff clean. `tests/test_knowledge.py`
holds the S3 tests: expected mini_pkg nodes/edges (hand-written), unresolved-not-guessed, relative +
aliased + dotted imports, `import pkg.sub` top-package binding, comprehension complexity, inheritance
edge, deterministic bytes, test_map/coverage join, parametrized-collapse of `tested_by`, history
(bugfix+manifest, at-that-commit spans, rename both-sides, deleted-file + merge, src-layout naming),
hotspots, verify confirms clean + catches wrong-module-same-leaf + tested_by-from-contexts, the agent
tools incl. sha validation, and a docker e2e that runs real container coverage and asserts
test_map/coverage/tested_by/verification + byte-identical graph.

**Config/heuristics added** (config.py + PROPOSED HEURISTICS rows): `graph.complexity_metric`,
`graph.test_dir_names`, `graph.test_file_globs`, `graph.nonsource_files`, and the whole
`KnowledgeConfig` (coverage context + artifact filenames). McCabe counted constructs documented.

**Things S4 must know**
- Everything lives in `output/<repo>/knowledge/`: `repo_graph.json`, `symbol_index.json`,
  `history_index.json`, `test_map.json`, `coverage.json`, `hotspots.json`, `graph_verification.json`.
  `knowledge.runner.knowledge_paths(run_dir)` returns these paths.
- **repo_graph.json**: `{metadata, nodes[], edges[]}`. Node = `{id (qualname), type
  (module|class|function|method), file, line, end_line, signature, docstring, complexity, is_public,
  decorators, coverage, tested_by[]}`. Edge = `{type, source, target, evidence{file,line}}`. IDs are
  dotted qualnames (`glom.core.Path.__init__`); source file paths are repo-relative.
- **test_map.json**: `{pytest_nodeid: [source function qualname, ...]}` — join the harness's stable
  test set (`hygiene/baseline.json`) with these to know which tests exercise a touched function
  (the P3 history "coverage or added tests" filter). **excision** picks functions covered by
  `>= min_covering_tests` — invert test_map (or read a function node's `tested_by`).
- **coverage.json**: `{qualname: percent}` over the function's measurable body lines (includes the
  `def` line, so a never-called function reads ~50%, not 0 — a low-vs-high signal, not absolute).
- **history_index.json** (P3 mining source): per original commit `{sha, parents[], message,
  is_merge, pr_number, files_changed[], insertions, deletions, test_files_touched[],
  touches_manifest, touched_functions[]}`. Use `touches_manifest` for the dependency-changing drop
  and `touched_functions` ∩ `test_map` for the coverage filter. History is at/under `base_sha` only.
- **hotspots.json**: `{qualname: change_count}` for signal scoring.
- Run everything against `bench-<repo>` via `run_in_container`; NO host execution of target code.

**Stubbed / deferred**
- `okf` agent tool + `.okf/` writer → S7. mutators/lint/testgen unchanged (S6/S9).
- **F6** (collection-broken branch, inert baseline flags) — not in S3's way; still flagged for S6.
- Graph-tool wiring into a live agent run is deferred to the first stage that needs it (S5 builders);
  S3 implements + unit-tests the tools but no agent runs this session.

#### S3 review round — GO-with-fixes applied

1. **history_index rename handling**: both `git diff` calls pass `--no-renames`, so a rename is
   attributed on both sides (removed + added function spans). Added a rename commit to
   `build_mini_pkg.py` (geometry→shapes) + a test. Re-checked glom `fc58761` (stream→streaming): now
   lists both `glom.stream.*` and `glom.streaming.*` (33 functions).
2. **Relative imports**: `symbol_index` resolves `from . import x` / `from ..pkg import y` against the
   module's package (level>0). Test: relative + aliased imports resolve.
3. **`import pkg.sub` binds only the top package**; dotted call chains (`pkg.sub.func()`) resolve by
   walking Attribute nodes, else unresolved. Test included.
4. **verify — calls** now independently RE-RESOLVES the target module (not leaf-name only), including
   `self.method` and relative imports, so a wrong-module/same-leaf edge is caught (test). **tested_by**
   is re-derived from the persisted raw coverage contexts (`coverage_contexts.json`). Removed the
   unimplemented "dynamic support" claim.
5. **test_map keyed by exact pytest nodeids** via an in-container pytest plugin
   (`coverage.Coverage.current().switch_context(item.nodeid)`) — no pytest-cov dependency (verified
   absent; `coverage` present). Parametrized/inherited cases captured distinctly (all 202 glom
   contexts). Corrected the PROGRESS "doctests" mis-statement.
6. **Complexity**: fixed the unreachable comprehension branch — `if`s inside comprehensions now count
   (`+1` for the `for` clause, `+1` per `if`), matching HEURISTICS. Test added.
7. **show_commit**: validates the sha with `re.fullmatch(r"[0-9a-fA-F]{4,40}")`, passes `--`, rejects
   empty/prefix-injection; output cap moved to `knowledge.show_commit_max_chars`. Test added.
8. **src/ layout**: `path_to_module` strips `knowledge.source_roots` so history/hotspots qualnames
   match the graph's package-aware naming (`src/pkg/mod.py → pkg.mod`). Test with a src-layout fixture.
9. **Nits**: tool filenames come from `config.knowledge.*`; PR/manifest regex + prefixes in config +
   HEURISTICS; probe file renamed `_kn_probe.py`; tools docstring refreshed; single tool registration
   (`stub_tools` removed — graph tools with no `knowledge_dir` raise the clear error); `_sample`
   documented as first-N-after-sort per edge type; `run_coverage` returns an explicit
   `coverage_status` (ok/no_output/no_tests) instead of a silent `{}`.
10. **Tests**: at-that-commit spans, rename/merge/deleted-file history, relative+aliased imports,
    `import pkg.sub`, comprehension complexity, src-layout, unresolved-calls-in-artifact.

Note: the stricter independent call re-resolution briefly surfaced apparent mismatches on
toolz/minidump — all were `self.method` calls the verifier's resolver didn't yet handle (indexer was
correct). After adding self + relative-import handling to the verifier, all four repos are back to
**precision 1.0, 0 mismatches**. The mini_pkg fixture is now 8 commits (added standalone
geometry→shapes rename); source module count 4→5 (adds `mini_pkg.shapes`).

#### S3 review round 2 — GO-with-fixes applied

- **A. Relative imports made order-independent.** `symbol_index` now runs a true first pass that
  registers every module (name + `is_package` from the path) BEFORE any import is parsed, so
  `_relative_base` can never read an unregistered record. (The live code already resolved glom's
  `from .core import`; the None the reviewer saw came from the stale artifact — see B.) New test:
  a module that sorts BEFORE its package sibling and uses `from .zzz import` still resolves the
  import edge + the call. Fresh glom now has **16** imports / **17** inherits / **235** calls.
- **B. Pipeline-code fingerprint in every step's input hash (the real bug).** The old
  `symbol_index` hash covered only source files, so the round-1 relative-import fix never
  invalidated glom's `output` artifact — I'd forced only `indexes/graph/verify`, so the graph was
  built on pre-fix symbols. Now `state.code_fingerprint()` hashes the analyzer sources
  (`knowledge.code_fingerprint_files` for knowledge, `hygiene_code_files` for hygiene) into every
  step's input hash, so a code change invalidates its artifacts. Re-ran all four repos from fresh
  (table above). Test: `code_fingerprint` changes when a file's content changes.
- **verify imports re-check** rewritten from regex to an INDEPENDENT second parse that re-resolves
  each import statement (absolute + relative) — a regex could not read `from .core import` and was
  falsely flagging the new relative-import edges. Back to precision 1.0 on all four.
- **show_commit**: uses `git show … --end-of-options <sha>`. The reviewer's literal `--` BEFORE the
  sha would make git treat the sha as a pathspec (`git show -- <sha>` prints nothing — verified);
  `--end-of-options` achieves the intent (sha can never be parsed as an option) and is git-correct.
- Full suite **98 passed / 3 slow**, ruff clean. All knowledge artifacts regenerated from fresh
  outputs; glom graph byte-identical across recompute.

### S4

**Scope delivered.** Excision funnel → task builder → validation harness → `tasks.json`, wired as
`--stage tasks` (`--stage all` = hygiene → knowledge → tasks). Only LLM use: the SMALL screen
(batched) and, when a candidate has fewer than `excision.min_assertions_touching_fn` assertions,
ONE bounded BIG top-up agent (fired once this session, on the mini_pkg fixture). No agent-authored
instructions, no leak gates, no difficulty, no history/net-new funnels — all S5+.

**What exists (real, tested)**
- `tasks/excision.py` — deterministic funnel over `symbol_index.json` + `test_map.json` +
  `hygiene/baseline.json` (only baseline-PASSING tests count as covering; parametrized cases
  collapse to base nodeids). Rejects with a reason (`test-code`, `init-module`, `private`,
  `private-parent`, `uncovered`, `few-covering-tests(n<k)`, `too-central(n>k)`, `too-short`,
  `too-long`, `low-complexity`), scores survivors `covering_tests × complexity`, ranks round-robin
  over modules, screens the top `build_target × screen_pool_multiplier` with the SMALL model
  (`p3.excision.screen_candidate`, `{docstring_leaks_impl, trivially_inferable, reason}` per
  function; reject reasons `docstring-leaks-implementation` / `trivially-inferable`), keeps the
  first `build_target` survivors (`selected`), the rest `surplus`. Everything considered lands in
  `output/<repo>/tasks/candidates.json`.
- `ecosystems/source_ops.py` (Python-specific, next to `symbols.py`) — `excise_function` splices the
  body by line span (decorators, multi-line signature, docstring, comments and every other def stay
  byte-identical; nested defs go with the body; one-liners → `ExciseError`), `module_bound_names`
  (top-level bindings incl. `try/if` blocks + star-import expansion, for the static gate),
  `verifier_imports`, `count_assertions`, `test_functions_in`.
- `tasks/build_excision.py` — `tasks/<repo>/<task_id>/`: `solution/` = `output/<repo>/repo` tree
  minus `.git`/caches; `input/` = same tree with the target body → `excision_body` (docstring kept
  unless `--excision-hard`); `verifier/` = the covering test files at their repo-relative paths +
  `conftest.py` ancestors + `run.sh`; `goldenSolution.md` = unified diff input→solution + a
  mechanical "why correct" (LLM prose marked TODO-S5); `task.json` (schema below) with a
  structural non-leaking instruction (`instruction_status: "template-S4"`, `difficulty: null`).
  Top-up agent (`p3.build.verifier_agent`, BIG): works on a throw-away copy of `solution/` with
  concrete + graph tools, may only contribute ONE new file
  `<test dir>/test_excision_<name>.py`; everything else it touches is discarded; audited to
  `agent_actions.jsonl`; `excision.verifier_agent_max_attempts` bounds it.
- `tasks/classify.py` — STRICT right-reason classifier over pytest-json-report (shape verified
  in the real image, 11 failure modes probed): valid = `AssertionError` / `Failed: DID NOT RAISE` /
  `NotImplementedError` / any exception whose traceback passed through a repo (non-test) frame;
  invalid = collector failures (`ImportError`/`SyntaxError`/`collection_error`), `collected_0_items`
  (`summary.total == 0`), `fixture_not_found`, `error_before_repo_call` (incl. import errors in a
  test body). ALL failing tests must be valid.
- `tasks/harness.py` + `pipeline/validate.py` — `python -m pipeline.validate <task_dir>...` /
  `validate_task(task_dir)`. Per task: image present (digest recorded; see deviations) → fail-before
  on `input/` (+ canonical `verifier/` overlaid, always) → right-reason → pass-after on `solution/`
  → determinism (`determinism_runs` total runs each, compares `{exit_code, nodeid→outcome}`) →
  collateral (repo's baseline suite on `solution/`, no baseline-passing test may fail; runs for
  excision too) → static gate (verifier `from <repo module> import <name>`: name must exist in
  `input/` and not start with `_`). Evidence: `fail_before.log`, `pass_after.log`,
  `collateral.log` (real container stdout/stderr), `determinism.json`, `collateral.json`,
  `verdict.json`. Tasks validate in parallel (`docker.harness_parallel_workers`).
- `tasks/manifest.py` — `tasks/<repo>/tasks.json`; `validation_status` READ from
  `evidence/verdict.json` (`VALID`/`INVALID`/`UNVALIDATED`), never set by hand.
- `tasks/runner.py` — steps `excision_funnel → build_excision → validate → manifest`, resumable,
  `tasks.code_fingerprint_files` in every input hash; stale `exc-*` folders from an earlier build
  are pruned; timings under `report_data.stages`, counts under `report_data.tasks`, LLM usage
  merged into `audit/llm_usage.json` (client `write_usage` now merges per-step instead of
  overwriting other stages).
- Adapter additions: `verifier_command(nodeids)`, `with_report(cmd, report)`,
  `parse_test_report_data`; `docker.image.image_id`; `HygieneContext.tasks_dir` +
  `build_context(llm_stage=...)` (cassette/transcript stage per pipeline stage).

**Per-repo results (fresh outputs from the final code)**

| Repo | functions considered | rejected by reason (deterministic) | screened out (SMALL) | built | VALID | INVALID (reason) | screen tokens | validate wall |
|---|---|---|---|---|---|---|---|---|
| glom | 497 | private 196, test-code 195, few-covering-tests 28, too-short 21, low-complexity 14, private-parent 8, too-central 7, uncovered 4 (pre-gate: 0) | 0 of 15 | 5 | **4** (`exc-glom.core-format_target_spec_trace`, `exc-glom.grouping-GROUP`, `exc-glom.matching-Check.glomit`, `exc-glom.reduction-Fold.glomit`) | 1: `exc-glom.cli-mw_get_target` (fail-reason:error_before_repo_call) | 5871 first run; **0 on rerun** (15 decisions reused) | 21 s (5 tasks in parallel, 3 determinism runs + collateral each) |
| toolz | 375 | test-code 217, private 55, few-covering-tests 38, too-short 16, low-complexity 14, uncovered 8, **verifier-imports-private 6** (`_signatures`), init-module 1, too-long 1 | 5 of 15 (backfilled to target) | 5 | **5** (`merge_with`, `update_in`, `memoize`, `groupby`, `sandbox.parallel.fold`) | 0 | 6602 | 28 s |
| mini_pkg (defaults) | 26 | test-code 11, too-short 5, few-covering-tests 4, private 3, uncovered 3 | — | 0 | 0 | — | 0 | — |
| mini_pkg (tests, `min_lines=3 min_complexity=1`, cassette) | 26 | test-code 11, few-covering-tests 4, private 3, uncovered 3 | 2 (trivially-inferable: ceil_div, Registry.register) | 3 | **3** (`clamp`, `display_width`, `truncate`) | — | 1134 (cassette) | 7 s |
| minidump | — | no tests → `test_map` empty → 0 candidates by construction (not run) | — | — | — | — | — | — |

`verifier_on_input` (recorded at build time, in `task.json` + `tasks.json`): glom
format_target_spec_trace 28 failing / 0 passing, GROUP 6/0, Check.glomit 6/21, Fold.glomit 12/0,
mw_get_target 10/0; toolz merge_with 9/0, update_in 6/0, memoize 10/0, groupby 9/0, fold 1/1.

- glom INVALID `exc-glom.cli-mw_get_target`: `fail-reason:error_before_repo_call` — the CLI tests
  drive the command through face's `CommandChecker`, which catches the excision
  `NotImplementedError` and raises its own `CheckError` from site-packages, so no repo frame is in
  the traceback. STRICT is doing its job (the test does not visibly fail for the excision reason).
- toolz: six candidates whose covering tests import the private `toolz._signatures` module /
  `_is_valid_args` helpers are now rejected by the funnel pre-gate (`verifier-imports-private`)
  before any LLM spend (before the review they reached the harness and failed its static gate);
  the screen backfilled past 5 screened-out candidates and all 5 built tasks are VALID.
- mini_pkg: nothing in the fixture meets the default `min_lines=8`/`min_complexity=3` (largest
  covered public function is 7 lines) → **0 candidates by default** (recorded, every function has
  a reason). The tests use `--set excision.min_lines=3 --set excision.min_complexity=1`
  (`tests/_smoke.mini_pkg_excision_config`, top-up agent disabled there); an earlier live fixture
  run (since removed from `output/`) exercised the top-up agent for `truncate` (2 assertions):
  5 tests added, 16.6k BIG tokens, audited.
- Harness re-run on the same folder is idempotent: `python -m pipeline.validate
  tasks/glom/exc-glom.core-format_target_spec_trace` twice → identical `verdict.json` minus
  `timestamps` (asserted in the tests as well).
- The SMALL screen is NOT byte-stable across runs at temperature 0 (one toolz candidate flipped
  between two runs) — expected per DESIGN ("determinism from gates, not models"). Screen decisions
  are therefore persisted in `candidates.json` (`screen_key` = content hash) and reused on rerun
  unless `--force excision_funnel`/`--fresh`: verified live — a rerun of glom after a code change
  re-ran the funnel with 15 reused decisions, zero LLM calls and the identical selection.

**Deviations / decisions (flag for author)**
1. `verdict.json` records the LIVE image Id and `digest_matches_task` but does not gate on it
   (`harness.gate_on_image_digest=False`): every rebuild from the same pinned Dockerfile yields a
   new Id (bench-mini_pkg's live Id already differs from `output/mini_pkg/hygiene/build.json`), so
   gating would invalidate every task after any rebuild. A missing image is always INVALID.
2. Static gate scope: only `from <repo module> import <name>` over modules that exist in `input/`
   is judged; `import pkg.sub`/dynamic modules (toolz's `tlz` builds submodules at import time —
   a first pass falsely flagged it) are left to the container runs.
3. New PROPOSED heuristics: `excision.max_covering_tests=40` (glom `get_handler` is covered by 112
   tests; excising it fails the whole suite), `require_public_parent`, `skip_init_modules`,
   `screen_pool_multiplier`, `rank_module_round_robin`, `copy_conftests`,
   `verifier_agent_max_attempts`; harness `require_at_least_one_failing_test`,
   `gate_on_image_digest`, evidence filenames; `TasksConfig` (layout). All in HEURISTICS.md.
4. `verifier/` layout mirrors repo-relative paths so "re-copy the canonical verifier" is a
   directory overlay (DESIGN 5.5 note added). `determinism_runs` counts the primary run.
5. `tasks/` is gitignored for now (author decision Q1); the final `tasks/glom` + `tasks.json`
   are committed in S9. `ruff` excludes `tasks` and `output`.

**Schemas S5 must know**
- `task.json`: `{id, title, repo, base_sha, provenance{type:"excision", target, file,
  span[line,end_line], excised_lines[start,end], docstring_kept}, difficulty: null,
  difficulty_rationale: null, files_in_scope[], instruction, instruction_status:"template-S4",
  verifier_cmd (plain, documented: "python -m pytest -q <nodeids>"), verifier_tests[],
  verifier_files[], verifier_visibility, assertions_touching_fn, verifier_agent{...}|null,
  collateral{cmd, report, baseline_passing[]}|null, image_tag, image_digest}`. The harness adds
  `-p no:cacheprovider --json-report ...` via `adapter.with_report`.
- `evidence/verdict.json`: `{task_id, valid, checks{image, fail_before, right_reason{ok, invalid[],
  tests{nodeid→{reason, valid, detail}}}, pass_after, determinism, collateral, static_gate},
  reasons[], repeat_count, image_tag, image_digest (live), task_image_digest, timestamps{started,
  finished}}`. `determinism.json`: `{runs, identical, fail_before[{exit_code, outcomes}],
  pass_after[...]}`. `collateral.json`: `{cmd, exit_code, baseline_passing, still_passing,
  newly_failing[], report_present}`.
- `output/<repo>/tasks/candidates.json`: `{selected[], ranked[], counts{status|rejected:reason →
  n}, candidates[{qualname, module, file, line, end_line, span, complexity, is_method, parent,
  signature, docstring, covering_tests[], score, status, reject_reason, screen}]}` (feeds REPORT).
  `built.json`: `{qualname → {task_dir, task_id} | {task_dir: null, reject_reason}}`.
- `tasks/<repo>/tasks.json`: `{repo, tasks[{id, title, source_type, module, difficulty,
  provenance, verifier_cmd, validation_status, validation_reasons[], path}]}`.
- History-funnel builders should reuse `build_excision._collateral`, `_files_in_scope`, the
  `verifier/` overlay convention, `Harness` unchanged (only `provenance.type` differs) and
  `manifest.write_manifest`. LLM instruction/leak gates/difficulty replace `_instruction` and the
  `template-S4` marker; `goldenSolution.md` "why correct" prose replaces the TODO-S5 line.

**Exact test command**
```
.venv/bin/python -m pytest            # fast: + tests/test_tasks.py (17 unit + 9 docker)
.venv/bin/python -m pytest -m slow
.venv/bin/ruff check .
```
Result: **124 passed, 3 deselected** (fast) + **3 passed** (slow). `ruff check .` clean at the repo root.
`tests/test_tasks.py`: AST splice byte-preservation (decorators, multi-line signature, nested def,
docstring keep/strip, one-liner error), classifier valid/invalid matrix (incl. collector
ImportError/SyntaxError, 0 collected, fixture-not-found, third-party wrapper), funnel reasons on the
fixture (defaults → all rejected with reasons; relaxed → clamp ranked first; baseline-passing set
restricts covering tests; too-central/private-parent/init-module), screen via the `s4_screen`
cassette (1134 tokens recorded once), static gate, manifest-from-verdict, prune; docker: full
`--stage tasks` e2e on mini_pkg (3 VALID, all evidence files, provenance/instruction/golden checks,
resumable second run skips every step, harness idempotent), verifier importing a solution-only
symbol → INVALID (`fail-reason:ImportError` + static gate), flaky verifier → `nondeterministic`,
broken `ceil_div` in solution → `collateral-breakage`, tampered `input/tests` defeated by the
verifier re-copy (and caught when re-copy is disabled), private import → static gate,
`python -m pipeline.validate` CLI; the top-up agent path with a scripted endpoint (only the one
file kept, audit written).

**LLM spend this session:** ~75k tokens total (incl. the review-round reruns: glom 5.9k, toolz 6.6k, one earlier toolz/glom pass each) — pre-review figure was ~56k (Baseten): SMALL screen ~46k across all runs (glom 3× ~4.5k, toolz 3× ~3.5k,
mini_pkg 2× ~1.1k, cassette 1.1k) + BIG top-up agent 28k (two mini_pkg fixture runs, 11.6k +
16.6k). Zero LLM calls in the harness.

#### S4 review round — GO-with-fixes applied

1. **`verifier/run.sh`** now `cd`s to its own directory (it is overlaid onto the workdir root) and is
   `+x`; test executes it in the container on `solution/` (exit 0) and `input/` (exit 1).
2. **ruff** `extend-exclude += tasks, output`; `tasks/` gitignored (Q1) and `tasks/glom` unstaged;
   stray `tasks/mini_pkg`, `tasks/toolz` and the manual-run `output/mini_pkg/tasks` artifacts
   removed. `ruff check .` clean at the repo root.
3. **Funnel pre-gate** `excision.reject_private_verifier_imports`: covering test files that import a
   private repo module/symbol (any dotted component starting with `_`; same AST rule as the harness
   static gate, `source_ops.private_repo_imports`) reject the candidate with
   `verifier-imports-private(<file>: ...)`. The static gate gained the `private-module` reason.
   The screen now walks the ranking in batches until `build_target` survivors are found (backfill;
   `screen_pool_multiplier` removed). toolz: 6 pre-gated, 5 screened out, 5 built, **5/5 VALID**.
4. **`source_ops.read_source`/`write_source`** use strict UTF-8 with `newline=""`; test: CRLF + tab
   indented file round-trips byte-identical outside the excised body.
5. **`harness.min_failing_tests`** (config + HEURISTICS; replaces the boolean); the builder runs
   the verifier on `input/` once at build time and records `verifier_on_input {exit_code,
   n_failing, n_passing}` in `task.json` and `tasks.json`; top-up tests that do not fail on input
   are dropped (`verifier_agent.dropped_passing_on_input`).
6. **README** "Validate a task standalone" (`docker build -t <image_tag> <task>/input` +
   `python -m pipeline.validate <task>`); `harness.build_image_if_missing` (default False) builds
   the tag from `input/Dockerfile` when absent.
7. **Classifier reasons are enforced** against `harness.valid_fail_reasons` /
   `invalid_fail_reasons` (unknown reason → `ValueError`; validity must agree with the lists);
   renamed `exception_in_function_under_test → exception_in_repo_code`; `AttributeError@import`
   only at collection, a test-body `AttributeError` is `error_before_repo_call`; `no_failing_test`
   and `no_report` added to the invalid list. Setup-phase and collateral decisions documented in
   HEURISTICS.
8. **Lows**: raw json reports kept under `evidence/*.report.json`; collateral treats a
   baseline-passing test that is skipped/not collected on `solution/` as failure-to-run
   (`not_run`, fails the check); `candidates.json` counts/selected recomputed after an
   unsplittable candidate (`unsplittable(...)` reason); stray `__all__` dropped.
- **Q2**: `verdict.json.environment_hashes` = sha256 of `input/Dockerfile` and the lock;
  `gate_on_image_digest` stays False. **Q4**: screen decisions persisted (`screen_key`) and reused
  unless forced; unit test with a counting fake endpoint (backfill + zero calls on rerun) and a
  live glom rerun (15 reused, 0 calls). Not done / noted: `harness.min_failing_tests` is not yet
  surfaced as a CLI flag (use `--set`); the top-up agent's dropped-on-input rule is exercised only
  by the unit path (no live candidate needed it after the pre-gate).
