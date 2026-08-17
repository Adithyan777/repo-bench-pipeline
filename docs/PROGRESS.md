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
| S5 | Step 5: history funnel + task-builder agent (verifier authoring/neutrality, instruction + leak gates, difficulty) | review | See `### S5`. 5a done: history funnel + builder wired into `--stage tasks` (excision AND history). glom **8/8 history VALID** (15 shortlisted, 8 built; 12/13 overall), toolz 5/5 (2 via the new-symbol getattr convention), mini_pkg 2/2 (bugfix + PR merge). Full `pytest` → 141 passed / 3 deselected; `-m slow` → 3 passed; `ruff check .` clean. 5b (instruction/leak gates/difficulty) pending review. |
| S6 | Step 6: P1 test-gen + AST mutators + mutation gate | review | See `### S6` (+ review-round fixes). `testgen` step wired after baseline (own commit, `--no-testgen`). Real runs (testgen-step tokens): mini_pkg_notests 0→34 (15/15 mutants, 46k), glom `top_k=3` 202→248 (4 kept, `glom.core` dropped, 14/16 valid, 238k), minidump 0→120 (24 kept, 92/93, 1.018M). Kill = ≥1 test failed w/ collection OK (json-report); resume proven 0-token + `testgen.json` byte-identical. Honest drops (no theater). Full `pytest` → 165 passed / 3 deselected (4:21); `-m slow` → 3 passed / 165 deselected; `ruff check .` clean. Scripted-endpoint tests (no cassettes, per verifier-agent precedent). |
| S7 | Step 7: P2 .okf/ writer + claim verifier | review | See `### S7` (+ review-round fixes). `okf` knowledge step after `verify` (`okf.enabled`); OKF v0.2 bundle at `knowledge/.okf/`, static skeleton from the graph + BIG-authored purpose/contracts (cached by hash → 0-token, byte-identical reruns), claim verifier stamps `verified`(with `checks`)/`draft` + `okf_verification.json` (semantic precision + by_construction + unchecked kinds + conformance), `okf(path)` tool sandboxed. Runs (verified/draft): glom 105/45, toolz 111/27, minidump 97/53, mini_pkg 10/2; callees/callers/link 1.0, raises honest-low (implicit/under-claimed exceptions stay draft). `test_okf.py` 11 tests (offline + s7_okf cassette). Full `pytest` → 177 passed / 1 skipped / 3 deselected (3:13); `-m slow` → 3 passed; `ruff check .` clean (incl. the `docs/conf.py` source-module fix). |
| S8 | Step 8: net-new funnel + builder | todo | |
| S9 | Step 9 (Session B): lint/format, final selection & quotas, root tasks.json, report_data → REPORT.md, transcripts curation, housekeeping, HEURISTICS review sheet | review | See `### S9`. New: hygiene `lint` step (ruff in-container, pyproject, rebuild+suite verify, `--no-lint`); `tasks/select.py` (deterministic 10 under quotas + soft spread, root `tasks.json` + `selection.json`, `--select` final tasks step, infeasible→error); `report/build.py` (report_data.json → six-section REPORT.md, drafted narrative marked for author, `python -m pipeline.report`); image label + prune-by-label (`--prune-images`); deleted 2 inert baseline flags; added `--min-failing-tests`; `transcripts/dev/` + `docs/HEURISTICS_REVIEW.md`; `.gitignore` flip for the deliverable set. Full `pytest` → **195 passed / 1 skipped / 3 deselected (3:50)**; `-m slow` → **3 passed**; `ruff check .` clean. **The final live glom `--fresh` run is executed by the author.** |
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

### S5

#### 5a — history-derived funnel + builder (review)

**Scope delivered.** `pipeline/tasks/history.py` (funnel), `pipeline/tasks/build_history.py`
(builder), runner steps `history_funnel → build_history` between the excision steps and
`validate → manifest`; `--stage tasks` now produces both `exc-*` and `hist-*` tasks, both
listed in `tasks.json`, both candidate files feed `report_data.tasks`. Harness unchanged.
No instruction/leak gates/difficulty yet (5b): history tasks carry `instruction_status:
"template-S5a"`, `difficulty: null`, `goldenSolution.md` has the real `parent→commit` diff +
a `TODO-S5b` "why correct" line.

**Funnel (code + git, then SMALL).** Over `knowledge/history_index.json` (original history
at/under `base_sha`, so pipeline commits are excluded by construction). Hard rejects, in
order: `root-commit`, `non-pr-merge` (merges without a `#N` are back-merges whose first-parent
diff is arbitrary; PR merges are candidates with `input/` = first parent, exactly as
DESIGN), `docs-or-ci-only` (every file matches `history.ignore_paths`), `dependency-changing`
(`touches_manifest`), `no-source-change` (no non-test `.py` outside ignore_paths — test-only
commits land here), `too-many-files`, `too-small`/`too-large` (`git diff --numstat` over the
source files only), `uncovered-and-no-tests` (touched functions ∩ baseline-passing test_map
empty AND no test file touched), `unparseable(<file>@input|solution)` (AST at both states),
`reverted-by(<sha7>)` (a later commit naming it in a `This reverts commit` body, or carrying
the exact reverse `git patch-id --stable`; forward ids for the whole history come from ONE
`git log -p --diff-merges=first-parent | git patch-id` pass), `superseded-by-merge(<sha7>)`
(commits on a surviving PR merge's branch: the merge is the complete unit — the fixture's
fix + test split across two commits is exactly this case). Score = `fix_keyword` (regex on
the subject) + `adds_tests` + `public_fn` + `single_function` (+ `reverted` penalty when
`reject_reverted=False`), all recorded in `score_breakdown`. SMALL classify
(`p3.history.classify_commit`, `complete_json`, batched `llm.classify_batch_size`, per commit:
subject, files, touched functions, source diff capped at `classify_diff_max_chars`) walks the
score-ranked survivors until `shortlist_size` are kept (cap `classify_max_commits`; the rest
`surplus/not-classified`); keep = kind ∈ `keep_kinds` ∧ `self_contained` ∧
`verifiable_via_tests` (`classified_out` with `kind:<k>` / `not-self-contained` /
`not-verifiable-via-tests`). Decisions persist in `history_candidates.json`
(`classify_key` = sha256(sha + prompt block)) and are reused on rerun (glom rerun: 30 reused,
0 calls). Shortlist = greedy top-`shortlist_size` by score with `score_module_diversity` for
unrepresented modules, bugfix beating feature on ties.

**Builder (per shortlisted commit, walking the shortlist until `build_target` are built).**
`input/` = `git archive <first parent>`, `solution/` = `git archive <commit>` (never the working
tree); hygiene overlay ADDITIVE on both (the recorded pipeline commit's files ∪
`tasks.hygiene_overlay_files`, minus `tree_ignore` — the fixture's pipeline commit had
committed `mini_pkg.egg-info/`, filtered out; a file present in the historical tree is never
overwritten; no lint) — asserted in tests: `input/`→`solution/` differing files == `git diff
--name-only parent commit`, byte-identical to `git show`. Verifier: (a) the commit's
added/changed test FUNCTIONS by AST diff of each touched test file (`ast.dump` comparison,
formatting-only edits do not count) — the file at commit state is overlaid at its
repo-relative path (+ conftest ancestors at commit state), the changed nodeids are the
verifier command; (b) no test change → ONE bounded BIG agent
(`p3.build.verifier_agent`, `history.agent_max_turns=12`) writes `<nearest test
dir>/test_hist_<sha7>.py` from the behavior summary + touched contracts (signature +
docstring at solution) + the source diff (verifier author may see the diff); only that file
is kept; cached under `output/<repo>/tasks/agent_cache/<key>/` and reused on rerun.
Build-time gates, all in-container and BEFORE any BIG call: static gate `verifier/` vs
`input/` (`verifier-imports-non-public-or-missing(...)`), verifier on `solution/` (any
import/collection/syntax failure → `env-drift(<reasons>)`; tests failing for other reasons
are dropped, `dropped_tests.failing_on_solution`), verifier on `input/` (an invalid STRICT
reason → `verifier-on-input:<reason>`; tests passing on input dropped,
`dropped_tests.passing_on_input`; fewer than `harness.min_failing_tests` left →
`commit-tests-pass-on-input` / `agent-authored-pass-on-input`). Then, for commit tests, the
BIG neutrality check (`p3.build.neutrality_check_rewrite`, `complete_json`: `{neutral,
issues[], flagged_tests[]}` over the test sources, touched contracts and the identifiers the
diff introduces); flagged → ONE bounded agent rewrite of the flagged files (audited, cached),
re-gated on solution+input; still failing → `neutrality-rewrite-failed`; agent left the files
untouched → `verifier-not-implementation-neutral`. Decisions (`neutrality`, rewrite outcome,
agent no-output outcomes) persist in `built_history.json._decisions` by content hash. Then
ONE full-suite run on `input/` gives the collateral baseline (`collateral.source:
"input-run"`; tests the commit itself removed/renamed in its test files are excluded) —
comparing the commit against ITS parent, since HEAD's baseline lists tests that do not exist
at old commits and misses tests already broken by env drift there. `task.json` adds
`provenance{type:"history", commit, parent, pr_number, is_merge, message, files,
source_files, touched_functions, modules, verifier_source, classification}`,
`verifier_on_solution`, `dropped_tests`, `neutrality`, `verifier_agent`, `overlay_files`;
`files_in_scope` = touched source + test files + verifier files + direct importers of the
touched modules (`build_excision.files_in_scope`, generalized). Task ids `hist-<sha7>`.

**Per-repo results (fresh outputs from the final code)**

| Repo | commits | hard-rejected by reason | survivors → classified → kept → shortlisted | attempted → built (reject reasons) | VALID | tokens |
|---|---|---|---|---|---|---|
| glom | 1049 | superseded-by-merge 140, docs-or-ci-only 136, uncovered-and-no-tests 135, no-source-change 128, dependency-changing 96, too-small 64, non-pr-merge 39, too-large 8, root-commit 1, unparseable 1 | 301 → 30 (2 SMALL calls) → 23 (classified_out 7: kind 7) → 15 | 15 → **6** (verifier-fails-on-solution 4, commit-tests-pass-on-input 3, verifier-not-implementation-neutral 1, verifier-on-input:error_before_repo_call 1) | **6/6** (`hist-99e2ece`, `hist-a32abdd`, `hist-c2acc2b`, `hist-e355bce`, `hist-e515fb3`, `hist-e6a06a5`; all `commit-tests`) | classify 22.0k; neutrality: 7 checks ≈ 7k + 2 rewrite agents (first run 301k at 25 turns — one hit the cap; after `agent_max_turns=12` the retried one cost 74k) |
| toolz | 1230 | no-source-change 218, docs-or-ci-only 211, superseded-by-merge 206, uncovered-and-no-tests 167, too-small 157, dependency-changing 54, non-pr-merge 36, unparseable 23 (py2 syntax), too-large 7, too-many-files 4, reverted-by 3, root-commit 1 | 143 → 30 → 25 (classified_out 5) → 15 | 15 → **3** (verifier-imports-non-public-or-missing 5 — features adding new public symbols the pre-change tree lacks; env-drift(SyntaxError) 2 — 2013-era trees; verifier-fails-on-solution 2 — drift-polluted tests; verifier-on-input:error_before_repo_call 2; commit-tests-pass-on-input 1) | **3/3** (`hist-2bd9139`, `hist-386c750`, `hist-5a7e078`) | classify 19.7k; neutrality 20.9k (3 checks + 1 rewrite) |
| mini_pkg (fixture, cassette) | 11 | root-commit 1, docs-or-ci-only 1, dependency-changing 1, uncovered-and-no-tests 2, no-source-change 1 (test-only PR commit), superseded-by-merge 1 (the PR's source commit) | 4 → 4 (1 call) → 3 (refactor classified_out) → 3 | 3 → **2** (`Add text module`: verifier-on-input:ModuleNotFoundError — a new-module feature) | **2/2** (`hist-<bugfix>` ceil_div, `hist-<merge>` PR #7 with `input/` = first parent) | 2.1k classify + 1.0k neutrality (recorded once) |

Timings: glom funnel 61-67 s (301 survivors × numstat/parse/reverse-patch-id git calls),
build_history 254 s first run (incl. two agents) / 127 s rerun, validate 11 tasks 50-57 s;
toolz funnel 68 s, build 63 s. glom `--stage tasks` twice: identical selection, `classify_reused
30`, zero SMALL calls; the only rerun spend was the retried rewrite agent (its "unchanged"
outcome is now persisted too, so a third run costs 0).

- glom rejects worth reading: `verifier-fails-on-solution` ×4 are commits whose changed tests
  fail even at their own commit in the current image (boltons/PyYAML/3.12 repr drift in
  `test_error.py`/`test_match.py`, matches the probe); `commit-tests-pass-on-input` ×3 are
  test edits that do not discriminate the change; `85a7a3a` (`**` root-element iteration) was
  flagged for referencing the change-introduced `PATH_STAR` flag and the rewrite agent left
  the file untouched → rejected, recorded. `hist-e355bce` was INVALID on the first run
  (`collateral-breakage`: the commit renamed `test_match.py::test`, which passed at the parent
  → `not_run`); tests removed/renamed by the commit in its own test files are now excluded from
  the input-run baseline → VALID.
- toolz: the shortlist is exhausted at 3 built (target 8); most losses are structural
  (feature commits whose tests import the new symbol → INVALID by the strict classifier's
  design, see below; py2-era trees). Not hacked around.
- mini_pkg: the ceil_div fix is `+2/-1` (a pure one-liner would be `too-small(2<3)` under
  DESIGN's `< 3` rule — the fixture fix now uses `divmod`); the PR merge builds from its FIRST
  parent and its constituents are `superseded-by-merge` / `no-source-change`.

**Deviations / decisions (flag for author)**
1. Merges: only PR merges (`#N` in the subject) are candidates; other merges rejected
   (`history.reject_non_pr_merges`). Constituents of a surviving PR merge are superseded
   (`prefer_pr_merge_over_constituents`).
2. Reverted commits are a hard reject (`reject_reverted=True`); DESIGN listed "later
   reverted" both as a filter and as a score penalty — the flag picks (penalty when False).
3. Feature commits that add NEW public symbols cannot become VALID: their tests import the
   symbol → `ImportError`/`ModuleNotFoundError` on `input/`, which the STRICT classifier
   rejects by design (DESIGN 5.5 "zero tolerance"). The build-time gate records it
   (`verifier-imports-non-public-or-missing` / `verifier-on-input:ModuleNotFoundError`); no
   workaround. History tasks are therefore mostly bugfixes / behavior changes of existing
   symbols. If the author wants new-symbol features as tasks, the classifier rule (not the
   funnel) is the thing to relax.
4. Collateral baseline for history tasks = the suite on `input/` at build time (one extra
   container run per built task), not HEAD's baseline (`history.collateral_baseline_from_input`).
5. Old-commit dependency drift: recorded as `env-drift(<reasons>)`; re-locking at that
   commit (per-task image variant) is out of scope, as agreed.
6. Neutrality: agent turn cap `history.agent_max_turns=12` (a 25-turn Kimi rewrite cost
   ~150k tokens). Rewrite/no-output outcomes are persisted so reruns never re-run an agent.
7. `.gitignore` had `tasks/` (matched `pipeline/tasks/` too — new modules were silently
   ignored); now `/tasks/`.

**Exact test command**
```
.venv/bin/python -m pytest -m "not docker and not slow"   # 114 passed
.venv/bin/python -m pytest -m docker                       # 30 collected; tests/test_tasks.py + tests/test_history.py = 15 passed (~4 min)
.venv/bin/ruff check .
```
`tests/test_history.py`: source ops (AST test-function diff, new identifiers, contracts);
funnel on the fixture history (every reject reason, score breakdown, ranking, PR-merge input =
first parent, size/merge knobs); revert detection on a synthetic repo (revert message + reverse
patch-id, penalty mode); classify backfill/persistence/zero-call rerun with a fake endpoint +
cassette replay (refactor → `kind:refactor`, bugfix kept); shortlist diversity/tie rule;
`commit_test_nodeids` on the fixture; archive + additive overlay == git diff exactly, no
overwrite, no lint; test-dir affinity + contracts; docker: agent-authored verifier via a
scripted endpoint (non-discriminating test dropped, audit, cache reuse with zero calls),
agent tests passing on input → reject, synthetic env-drift (solution cannot collect), flagged
neutrality with rewrite disabled → reject + persisted decision, commit-tests build + run.sh +
new-module feature reject. `tests/test_tasks.py` e2e now covers both source types (7 VALID),
every history reject reason, evidence files, provenance/parent/first-parent, resumable
second run (all six steps skipped) and a forced funnel rerun with zero LLM calls. Cassettes:
`tests/cassettes/s5_tasks/` (screen + classify + 2 neutrality, 4.2k tokens; recorded by
running the real stage on the fixture — `scripts/record_cassettes.py`); `s4_screen` removed
(the fixture's `clamp` changed with the PR merge and the tape is re-recorded in `s5_tasks`).

**LLM spend (5a, round 1):** ≈ 505k tokens CUMULATIVE across all runs (glom 330k first run,
of which 301k = two neutrality rewrite agents at 25 turns; glom rerun 74k = the capped retry;
toolz 47k; mini_pkg cassette 4.2k). The last glom run alone was 102k (`llm_usage._total` for
that run); funnel/build reruns with persisted decisions cost 0.

**Review round (author decisions applied)**
- Q1: `history.reject_reverted=True` stays (hard reject).
- Q2: `history.allow_new_symbol_features=True` — the getattr convention: a verifier never
  imports a name absent from `input/` at module level; it imports an existing public module
  and does `fn = getattr(mod, "name", None); assert fn is not None` + behavior asserts, so
  the pre-change tree fails with `AssertionError` (a right reason). Commit tests whose only
  static-gate violations are `symbol-missing-in-input` are routed to a bounded rewrite agent
  (`new_symbol_rewrite`, same step/budget as the neutrality rewrite); the verifier agent
  and the neutrality/rewrite prompts carry the rule (`NEW_SYMBOL_RULE`); the static gate
  accepts getattr on an existing public module and flags `getattr(<repo module>,
  "_private")` (dunders excluded). Rewrite/no-output outcomes are persisted by content hash.
- Q3: rewrite kept at 1 attempt / `agent_max_turns=12`, plus
  `history.max_neutrality_rewrites_per_repo=2` (per build step; beyond → plain reject with
  `rewrite:budget-exhausted`; cached/reused rewrites do not count).
- Fixture: commit 12 "Add core.first helper" (new public function, test imports it at
  module level). In the cassette e2e the budget is 0 (agent runs cannot replay: container
  output differs per run) → recorded reject
  `verifier-imports-symbol-missing-in-input(mini_pkg.core.first; rewrite:budget-exhausted)`;
  the docker test `test_build_new_symbol_feature_via_getattr_convention` drives the rewrite
  with a scripted endpoint → task builds → harness VALID with `AssertionError` as the reason,
  and the exhausted-budget reject.
- Re-runs: **glom** unchanged 6/6 history VALID — its 15-shortlist holds only 2 feature
  commits, neither is a missing-symbol case (`24c21dc` CLI test → `error_before_repo_call`
  through face; `ed56c05` tests fail on solution = drift), so **0 glom feature commits
  changed status**; the one flagged bugfix (`85a7a3a`) was retried under the new prompt (12
  turns, unchanged → still rejected, ~16k). **toolz** is where the rule bites: 5 of its 15
  shortlisted are features that top-level-import the new symbol; 2 were rewritten by the
  agent (`hist-639043e` `functoolz.apply`, `hist-8cdc7fe` `sandbox.core.unzip`: verifier now
  `getattr(toolz.functoolz, 'apply', None)` + asserts, fail-before reason `AssertionError`)
  and are **VALID** → toolz **5/5 history VALID** (was 3/3); 2 more hit the per-repo budget
  (`rewrite:budget-exhausted`, recorded), 1 imports a private helper (plain reject). Cost:
  ~103k tokens for the two toolz rewrites (~50k each at 12 turns).
- Static-gate false-positive guard: the getattr rule only fires on names bound to repo
  modules in the verifier file, so repo tests probing `_attrs` of instances (glom/toolz
  suites do) are unaffected — all 5 glom + 5 toolz excision tasks still VALID.

**Per-repo after the review round:** glom 6/6 history (10/11 overall), toolz 5/5 history
(10/10 overall), mini_pkg 2/2 (+1 recorded budget reject). LLM spend for the round: ≈ 4.6k
(cassette re-record) + 16k (glom) + 103k (toolz).

#### 5a review round 2 — fixes 1–9 applied

1. `tests/test_hygiene.py` baseline count → 13 (fixture now has 13 tests). Whole suite run:
   `.venv/bin/python -m pytest` → **141 passed, 3 deselected in 212.85s (0:03:32)**;
   `.venv/bin/python -m pytest -m slow` → **3 passed, 141 deselected in 49.92s**.
2. Nodeids are rebuilt from `source_ops.test_nodeid_suffixes()` (`Class::name`) after a
   rewrite, for agent-authored files and for the commit-removed-tests rule; `test_functions_in`
   is no longer used in `build_history.py`.
3. `history.max_agent_runs_per_repo=6` (verifier-author + rewrite agents per build step;
   cached/reused runs do not count) alongside `history.max_neutrality_rewrites_per_repo=2` (the
   rewrite sub-budget); both documented in HEURISTICS; `budget-exhausted` outcomes recorded.
4. A rewrite (or verifier-author) agent that hits `agent_max_turns` without a clean summary has
   its files discarded (`rewrite:max-turns` / `max-turns`); after a kept rewrite ONE
   `complete_json` re-check runs on the rewritten tests
   (`history.neutrality_recheck_after_rewrite`; `rewrite:still-not-neutral` reject); the
   neutrality prompt now states that exception type / identity / chaining observable by a
   caller IS behavior. Reject strings carry the rewrite outcome:
   `verifier-not-implementation-neutral(rewrite:<unchanged|disabled|max-turns|still-not-neutral|budget-exhausted>)`.
   `hist-e6a06a5` re-evaluated: it is now `surplus` / `not-classified` — see the ranking note
   below (its PR merge is what got built).
5. Every test file touched by the commit is overlaid at commit state (helpers, fixtures,
   conftests included, deleted files skipped); only the changed nodeids are selected.
6. `superseded-by-merge` is applied AFTER classification and only to constituents of a KEPT
   PR merge (`history.supersede_constituents`); constituents of rejected/classified-out merges
   stand alone. glom: 140 → 45 superseded, toolz 206 → 45.
7. Kept-but-not-shortlisted candidates carry `reject_reason: "kept-not-shortlisted"`
   (unclassified ones keep `not-classified`); `public_fn` uses the symbol index's `is_public`
   for the node (fallback: every component below the module public); the `10**9` sentinel is
   gone.
8. Agent trajectories go to the LLM client's `transcripts_dir` (`BuildInputs.transcripts_dir`);
   literals moved to config (`tasks.title_max_chars`, `tasks.instruction_tests_listed`,
   `tasks.audit_goal_chars`, `tasks.audit_summary_chars`, `tasks.content_key_chars`,
   `history.prompt_new_names_max`); `.DS_Store` gitignored.
9. Spend note corrected above (505k cumulative, last run 102k); reason strings below are
   verbatim from `history_candidates.json` / `built_history.json`.
- Also: the new-symbol rewrite now probes the solution tree for env-drift BEFORE spending an
  agent (this run wasted two toolz rewrites on 2013-era trees that then failed
  `env-drift(SyntaxError)`).

**Per-repo after round 2 (fresh runs, verbatim reasons)**

| Repo | funnel counts | attempted → built (reject_reason: n) | VALID | this run's tokens |
|---|---|---|---|---|
| glom | `rejected:docs-or-ci-only` 136, `rejected:uncovered-and-no-tests` 135, `rejected:no-source-change` 128, `rejected:dependency-changing` 96, `rejected:too-small` 64, `rejected:superseded-by-merge` 45, `rejected:non-pr-merge` 39, `rejected:too-large` 8, `classified_out` 8, `rejected:root-commit` 1, `rejected:unparseable` 1, `shortlisted` 15, `surplus` 373 | 15 → **8**: `verifier-on-input:error_before_repo_call` 2 (`032f252`, `24c21dc`), `commit-tests-pass-on-input` 2 (`bd2e529`, `dd28dc4`), `verifier-fails-on-solution` 2 (`3cdf4e7`, `e70637c`), `verifier-not-implementation-neutral(rewrite:unchanged)` 1 (`de604f5`) | **8/8** (`hist-0d75aab`, `hist-4a48227`, `hist-8289b94` PR #170, `hist-85a7a3a`, `hist-94b6375` PR #196, `hist-99e2ece`, `hist-c2acc2b`, `hist-e515fb3`); overall 12/13 | 274k (`p3.build.neutrality_check_rewrite` 256k: new checks + 3 rewrite agents at ≤12 turns; classify 11k new batch) |
| toolz | `rejected:no-source-change` 218, `rejected:docs-or-ci-only` 211, `rejected:uncovered-and-no-tests` 167, `rejected:too-small` 157, `rejected:dependency-changing` 54, `rejected:superseded-by-merge` 45, `rejected:non-pr-merge` 36, `rejected:unparseable` 23, `rejected:too-large` 7, `classified_out` 5, `rejected:too-many-files` 4, `rejected:reverted-by` 3, `rejected:root-commit` 1, `shortlisted` 15, `surplus` 284 | 15 → **5**: `env-drift(SyntaxError)` 4 (`0d3639b`, `3b7c54a`, `a55ce46`, `bf0f253` — the last two after a wasted rewrite, now probed first), `verifier-fails-on-solution` 2, `verifier-imports-non-public-or-missing(toolz.functoolz._num_required_args)` / `(...core._num_required_args)` 2, `verifier-on-input:error_before_repo_call` 1, `commit-tests-pass-on-input` 1 | **5/5** (`hist-2bd9139`, `hist-386c750`, `hist-5a7e078`, `hist-639043e` + `hist-8cdc7fe` via reused getattr rewrites); overall 10/10 | 317k (308k neutrality: two 12-turn rewrites ≈ 150k each — a Kimi turn with tool output is ~12k tokens; bounded by the per-repo budgets) |
| mini_pkg (cassette, 12 commits) | `rejected:root-commit` 1, `rejected:docs-or-ci-only` 1, `rejected:dependency-changing` 1, `rejected:uncovered-and-no-tests` 2, `rejected:no-source-change` 1, `rejected:superseded-by-merge` 1 (after classify), `classified_out` 1 (`kind:refactor`) | 4 → **2**: `verifier-on-input:ModuleNotFoundError` (`Add text module`), `verifier-imports-symbol-missing-in-input(mini_pkg.core.first; rewrite:budget-exhausted)` (`Add core.first`, budget 0 in the cassette run; VALID under the scripted-agent docker test) | **2/2** | 4.9k (re-recorded) |

Ranking note (glom): with `public_fn` now taken from the symbol index and supersede applied
after classification, the classifier's 30-commit window shifted: two PR merges (`8289b94`
error-branches, `94b6375` arg-mode) are now kept and built (both VALID) and their constituents
— including round-1's `hist-e6a06a5`, `hist-a32abdd`, `hist-e355bce` — are `surplus /
not-classified` (never reached by the classifier under `classify_max_commits=60`) rather than
superseded; `85a7a3a` (round-1 `verifier-not-implementation-neutral`) is now judged neutral
under the "exception identity is behavior" prompt and is VALID.

#### 5b — instruction, leak gates, difficulty (review)

**What exists.** `pipeline/tasks/instruction.py`: `task_facts(task_dir)` (contract = touched
functions' signature + docstring AS IN `input/`, verifier test sources, behavior summary /
excised-contract note, the input->solution diff of the touched source files — never shown to
the author), author (`p3.build.write_instruction`, BIG, `complete_json` -> `{title,
instruction}` with `## Goal` / `## Observable behavior` (`instruction.examples_from_verifier`
examples copied from the tests) / `## Constraints` / `## How success is measured`), gate (a)
pure code (`diff_leaks`: added diff lines with >= `leak_min_tokens` tokens present
whitespace-normalized in the text, lines also present in the tests exempt;
`identifier_leaks`: API-like names the diff introduces — defs/classes/imports/attribute
stores — that are neither in `input/`'s public API nor in the tests, whole-word match), gate
(b) BIG reviewer (`p3.build.review_instruction` -> `{solvable_by_transcription,
self_contained, implementation_neutral, issues[]}`); issues are fed back and the author is
re-run up to `instruction.max_regenerations` times; still failing -> `instruction_status:
"failed"` (kept in tasks.json, excluded by selection). `golden_rationale`
(`p3.build.golden_rationale`, BIG, may see the diff) replaces the `TODO-S5` line in
`goldenSolution.md` with `## Why correct`. `pipeline/tasks/difficulty.py`: `features()` from
the diff + `repo_graph.json` (`files_touched, functions_touched, callers_count,
cross_module_edges, diff_size, similar_named_functions_nearby, test_count`), `label_tasks()`
batched BIG (`p3.build.difficulty_label`, `difficulty.batch_size`), rationale must cite a
feature (`cites_feature`: name with `_`/spaces or `<name-stem>… <value>`), regenerated once,
then `difficulty_status: "failed"`. Runner step `instruct` (after `validate`, before
`manifest`): VALID tasks only (`instruction.only_valid_tasks`), writes `title, instruction,
instruction_status, instruction_review, instruction_attempts, verifier_visibility (current
flag), difficulty, difficulty_rationale, difficulty_features, difficulty_status` into
`task.json`; every decision persisted in `output/<repo>/tasks/instructions.json` by content
hash (author key = what the author sees; a loosened gate reuses decisions, a tightened one
needs `--force instruct`); the validate/instruct input hashes use `task.json` MINUS these
fields so the step does not invalidate itself. `task.json.module` (primary touched module:
excision target's module; history: the source file with the most changed lines) and
`modules[]` are set by both builders and copied into `tasks.json` (fallback from provenance
for old folders) — never null. `tasks.json` also carries `instruction_status`.

**Real runs (glom, final code).** 12 VALID tasks -> `instruct` 115 s: **10 final / 2 failed**
(`hist-94b6375` arg-mode PR: three drafts named the change-introduced API `arg_val` / `mode`
that the tests do not name -> gate (b); `hist-99e2ece` "replace assert with TypeError": the
reviewer judged all three drafts `solvable_by_transcription` — a one-line change whose
faithful description is the change). 7 regenerations (3 leak-gate, 6 reviewer rejections
across attempts). Difficulty: **easy 5 / medium 5 / hard 2**, 0 failed cite checks (2 batched
calls). Before the two gate refinements (`leak_api_names_only`, `exempt_diff_lines_in_tests`)
the same run had 3 failed: `hist-8289b94` was tripped by the local names `child`/`branches`
used as English in prose and `hist-0d75aab` regenerated into a final draft. toolz (run before
the refinements): 10 VALID -> 9 final / 1 failed (`hist-639043e`: a data literal `(20, 501,
16000)` shared by the docstring and the tests tripped gate (a) three times — the exemption
now covers it), spread easy 5 / medium 4 / hard 1, 5 regenerations. mini_pkg (cassette): 7
final / 0 failed, all difficulties cited.

Tokens (this run, glom): write 76k, review 56k, golden 38k, difficulty 4.5k ≈ 175k; toolz
≈ 160k; cassette re-record 24.8k. Timings: instruct 107–115 s per repo (BIG latency).

Exemplar (`tasks/glom/hist-c2acc2b/task.json`, `collateral.baseline_passing` elided):
```json
{
  "base_sha": "30b477ab65560914a38f331614947d0894701044",
  "collateral": {
    "baseline_passing": [
      "glom/test/test_basic.py::test_abstract_iterable",
      "glom/test/test_basic.py::test_api_repr",
      "glom/test/test_basic.py::test_bbformat",
      "... (138 total)"
    ],
    "cmd": "python -m pytest -p no:cacheprovider -q --json-report --json-report-file=.pytest-report.json",
    "report": ".pytest-report.json",
    "source": "input-run"
  },
  "difficulty": "medium",
  "difficulty_features": {
    "callers_count": 5,
    "cross_module_edges": 41,
    "diff_size": 17,
    "files_touched": 1,
    "functions_touched": 3,
    "similar_named_functions_nearby": 5,
    "test_count": 1
  },
  "difficulty_rationale": "The task touches 3 functions with `callers_count=5`, requires correctly formatting slice indices (including tuples of slices), and spans 17 lines of changes, indicating non-trivial repr logic to fix without breaking existing callers.",
  "difficulty_status": "final",
  "dropped_tests": {
    "failing_on_solution": [],
    "passing_on_input": []
  },
  "files_in_scope": [
    "glom/__init__.py",
    "glom/core.py",
    "glom/grouping.py",
    "glom/matching.py",
    "glom/mutation.py",
    "glom/reduction.py",
    "glom/streaming.py",
    "glom/test/test_path_and_t.py"
  ],
  "id": "hist-c2acc2b",
  "image_digest": "sha256:d7716116e9a8638a73aa11cd326995e607f63ad6197ddf0f69d9aa0fe7fd10af",
  "image_tag": "bench-glom",
  "instruction": "## Goal\n\nFix the `repr` of `T` specifications that use slice indexing (including tuples of slices) so that the slice is formatted as valid Python syntax instead of showing the raw `slice` object.\n\n## Observable behavior\n\n```python\nassert repr(T['a'].b.c()) == \"T['a'].b.c()\"\nassert repr(T[1:]) == \"T[1:]\"\n```\n\n## Constraints\n\n- Only identifiers visible in the public contract or tests may be referenced: `_BBRepr.repr1`, `_format_t`, `T`, `Path`.\n- The fix must make the verifier test `test_path_t_roundtrip` pass.\n\n## How success is measured\n\n```\npython -m pytest -q glom/test/test_path_and_t.py::test_path_t_roundtrip\n```",
  "instruction_attempts": [
    {
      "attempt": 1,
      "issues": [],
      "review": {
        "implementation_neutral": true,
        "issues": [],
        "self_contained": true,
        "solvable_by_transcription": false
      }
    }
  ],
  "instruction_review": {
    "implementation_neutral": true,
    "issues": [],
    "self_contained": true,
    "solvable_by_transcription": false
  },
  "instruction_status": "final",
  "module": "glom.core",
  "modules": [
    "glom.core"
  ],
  "neutrality": {
    "checked": true,
    "decision": {
      "flagged_tests": [],
      "issues": [],
      "neutral": true
    },
    "key": "8a4c39c404e99b3d",
    "reused": true,
    "step": "p3.build.neutrality_check_rewrite"
  },
  "new_symbol_rewrite": null,
  "overlay_files": {
    "input": [
      ".dockerignore",
      "Dockerfile",
      "constraints.txt",
      "pipeline-requirements.in",
      "requirements.lock.txt"
    ],
    "solution": [
      ".dockerignore",
      "Dockerfile",
      "constraints.txt",
      "pipeline-requirements.in",
      "requirements.lock.txt"
    ]
  },
  "provenance": {
    "classification": {
      "behavior_change_summary": "Fixes the repr of T[slice] specs so that slice indices (including tuples of slices) are formatted correctly instead of showing the raw slice object.",
      "difficulty_guess": "easy",
      "kind": "bugfix",
      "self_contained": true,
      "sha": "c2acc2b",
      "verifiable_via_tests": true
    },
    "commit": "c2acc2b4fa5ef90bbb781fa03e4e5095dd8f0d8c",
    "files": [
      "glom/core.py",
      "glom/test/test_path_and_t.py"
    ],
    "is_merge": false,
    "message": "fixing T[slice] repr",
    "modules": [
      "glom.core"
    ],
    "parent": "00293b2d8c1d9e084148b15f17f2c7338fc0e740",
    "pr_number": null,
    "source_files": [
      "glom/core.py"
    ],
    "touched_functions": [
      "glom.core._BBRepr.repr1",
      "glom.core._format_slice",
      "glom.core._format_t"
    ],
    "type": "history",
    "verifier_source": "commit-tests"
  },
  "repo": "glom",
  "title": "Fix T[slice] repr to format slice indices correctly",
  "verifier_agent": null,
  "verifier_cmd": "python -m pytest -q glom/test/test_path_and_t.py::test_path_t_roundtrip",
  "verifier_files": [
    "glom/test/test_path_and_t.py",
    "run.sh"
  ],
  "verifier_on_input": {
    "exit_code": 1,
    "n_failing": 1,
    "n_passing": 0
  },
  "verifier_on_solution": {
    "exit_code": 0,
    "n_failing": 0,
    "n_passing": 1
  },
  "verifier_tests": [
    "glom/test/test_path_and_t.py::test_path_t_roundtrip"
  ],
  "verifier_visibility": "visible"
}
```

**Tests.** `tests/test_instruction.py` (8): facts/contract from `input/`, gate (a) diff-line
leak + test-line exemption, gate (b) new API identifier (private helper caught, public/test
names allowed, locals not gated unless `leak_api_names_only=False`), author regeneration
with feedback + persistence (0 calls on rerun), bounded regeneration -> `failed`, hidden vs
visible visibility phrase, golden prose applied and TODO markers gone, features on the
mini_pkg graph (incl. callers/similar names), `cites_feature`, difficulty regenerate-once-
then-fail + persistence, excision facts. `tests/test_tasks.py` e2e (cassette): every VALID
task `instruction_status == "final"`, no `template-*` marker, `module`/`modules` set, the
ceil_div history instruction contains neither `quotient` nor `divmod`, `## Why correct`
present, difficulty final with all features, `instructions.json` written, second run skips all
7 steps. Cassettes `s5_tasks` re-recorded (32 tapes, 24.8k tokens: screen, classify, 2
neutrality, 7 author, 7 review, 7 golden, 1 difficulty batch).

**Things S6–S9 must know.**
- S8 net-new: build `input/` (current tree) + `solution/` + `verifier/` with the same folder
  convention, write `provenance{type:"net-new", ...}`, `module`/`modules`, `verifier_tests`,
  `files_in_scope`, then reuse `harness.validate_task`, `instruction.task_facts` (needs
  `provenance.source_files` + `touched_functions`, or add a `net-new` branch in
  `task_facts` for the summary), `write_instruction`, `golden_rationale`, `apply_golden`,
  `difficulty.features/label_tasks` — the runner's `instruct` step already covers any task
  dir listed by `_task_dirs` (extend it with a `built_netnew.json`).
- S9 selection reads from `tasks.json`: `validation_status == "VALID"`, `instruction_status
  == "final"`, `difficulty` (may be null when `difficulty_status == "failed"` — treat as
  unlabeled), `module` (primary, never null) / `modules[]` for diversity, `source_type`,
  `verifier_on_input`, `provenance`. Excision tasks: `instruction_status` was `template-S4`
  before 5b; INVALID tasks keep their template marker (never selected).
- S6/S7: `p3.build.golden_rationale` is a new BIG step in `STEP_MODEL`; `.okf` pages (S7)
  can be added to the author's contract block (`task_facts` -> `contract`).

#### 5b review round — GO-with-fixes applied

1. `apply_golden` idempotent (drops TODO markers and any previous `## Why correct` section);
   double-apply tested.
2. `instruction.exempt_diff_lines_in_tests` actually wired (`leak_issues` passes
   `exempt=facts.tests_source`); tested through `leak_issues`.
3. The classifier's `behavior_change_summary` is masked of forbidden change-introduced names
   (`mask_names`) before it enters the author and difficulty prompts; `api_names()` now
   includes module-level constants (`MIN_MODE`-style, tested).
4. A failed instruction keeps the template instruction/title in `task.json` (drafts, issues
   and reviews live only in `instructions.json`); the title is gated by the same leak checks;
   feedback to the author never echoes a leaked line/identifier (counts + guidance only,
   details in the record). `hist-94b6375` regenerated → final.
5. `--force instruct` (or `--fresh`) discards `instructions.json`; the decision key includes
   a hash of the prompt constants (`PROMPT_VERSION` + system prompts).
6. Reviewer: `states_mechanical_edit` question added; copied examples are declared required
   (not transcription); the author sees a "touched-function contract" with `(internal)`
   markers instead of a "public contract"; the author is told not to copy prompt-meta lines.
   `hist-99e2ece` re-evaluated → final ("Invoke.star raises TypeError instead of
   AssertionError…", one reviewer regeneration overall in the run).
7. `cross_module_edges` counts only edges with a touched FUNCTION endpoint; `cites_feature`
   requires name AND value; `_key` uses `config.tasks.content_key_chars`; the S4 golden
   boilerplate line is gone (5b writes `## Why correct`); `difficulty_status` in
   `tasks.json`; excision template examples deduped; HEURISTICS wording; DESIGN notes only
   ADDED diff lines are gated.

**Fresh glom run (`--stage tasks --force instruct`):** 12 VALID → **12 final / 0 failed**,
1 regeneration (reviewer), 0 leak-gate rejections; difficulty **easy 6 / medium 4 / hard 2**,
0 cite failures. Spend for the instruct step: write 53.5k + review 50.3k + golden 48.6k +
difficulty 4.6k ≈ **157k tokens** (the run also rebuilt/validated because
`instruction.py` is in the code fingerprint — 0 tokens there). Cassettes re-recorded (21.6k).

Suite (verbatim): `.venv/bin/python -m pytest` → **150 passed, 3 deselected in 303.89s
(0:05:03)**; `.venv/bin/python -m pytest -m slow` → **3 passed, 150 deselected in 60.89s
(0:01:00)**; `ruff check .` clean.

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

### S6

Step 6: P1 test generation + AST mutators + mutation gate. Wired as a resumable hygiene
step `testgen` after `baseline` (its own `pipeline: generated tests` commit); `--stage
hygiene` runs it; `--no-testgen` / `testgen.enabled=False` skips it.

What exists:
- `pipeline/ecosystems/python.py` `PythonAdapter.mutators()` + 7 AST operators
  (`comparison_flip/comparison_boundary/arithmetic_swap/and_or_swap/return_none/
  constant_tweak/statement_delete`). Each takes a function span, mutates one site,
  re-emits via `ast.unparse` re-indented; `statement_delete` never removes the def/class
  itself. `pipeline/hygiene/mutate.py` = ecosystem-agnostic driver: splices mutants back
  by line range (rest of file byte-identical), deterministic interleave-then-take-N
  selection.
- `pipeline/hygiene/testgen.py`:
  - `rank_targets` — deterministic. Joins testgen's OWN in-container coverage run
    (`knowledge.indexes.run_coverage`, missed lines per file) with the AST symbol index:
    `score = uncovered_ratio * log(1+lines) * (1 + complexity/complexity_weight) *
    public_bonus`, `uncovered_ratio = missed_in_span / measurable_in_span`. Filters
    (dunder, init re-export, cli main, too-small, private-low-complexity, no-executable-
    lines) and only `score > 0` candidates are selectable (never re-tests covered code).
    Emits `hygiene/testgen_targets.json` (every function's score + skip reason).
  - Generation loop — BIG agent (`p1.testgen.write_tests_agent`) per selected module,
    tools `read_file/grep/write_file/run` (run only in-container), writes ONLY the
    generated file; per-target mutation gate (pass on real code AND kill
    >= `min_mutants_killed`); surviving mutants drive `p1.testgen.mutation_retry_agent`
    up to `agent.testgen_max_retries`; whole file dropped if it fails on real code or
    kills zero mutants; weak-only test functions trimmed. Every outcome audited to
    `agent_actions.jsonl` and reused by content hash (`hygiene/testgen_decisions.json`,
    0-token reruns). `hygiene/testgen.json` = per-module/-function kept/weak + mutants
    killed/total.
- Generated tests live in a `generated/` subdir of each repo's PRIMARY test dir so the
  repo's own `pytest -q` collects them (glom → `glom/test/generated/`, mini_pkg →
  `tests/generated/`, bootstrap → `tests/generated/`).

Real runs (live BIG agent, real Docker). Tokens are the **testgen-step only**
(`p1.testgen.*` in `llm_usage.json`; the file `_total` also carries earlier sessions):

| repo | coverage | modules sel | targets | functions kept | mutants killed/valid | testgen tokens |
|---|---|---|---|---|---|---|
| mini_pkg_notests | bootstrap (0 tests) | 3 | 4 | 4 (3/3 modules) | 15/15 | 46k |
| glom (`top_k=3`) | 202-test suite | 3 | 8 | 4 (`glom.core` dropped) | 14/16 | 238k |
| minidump | bootstrap (0 tests) | 5 | 30 | 24 (`aminidumpreader` dropped) | 92/93 | 1.018M |

Documented command still green with generated tests: mini_pkg_notests 0→34 passed,
glom 202→248 passed, minidump 0→120 passed. `glom.core` and minidump's async reader were
honestly DROPPED (agent tests failed on the real code / proved nothing) rather than
shipped as coverage theater — the mutation gate working as designed. glom run with
`--set testgen.top_k_modules=3` to bound spend. minidump's `_total` equals its testgen
total (no earlier LLM steps); it was launched twice in S6 (a bad fixture-path attempt with
no LLM calls, then the real URL run) — only the real run's tokens count.

Review-round fixes (all applied):
1. Generated tests excluded from testgen + baseline input hashes AND from the ranking
   coverage run (`--ignore=<gen_dir>`); `_primary_test_dir` ignores the generated subdir so
   `gen_dir` never nests. **Resume proven**: `--stage hygiene` twice on mini_pkg_notests →
   second run skips testgen, `testgen.json` byte-identical, 0 new tokens.
2. After generation testgen runs the documented suite once (`baseline._run_suite`), records
   `suite_after` + `twice_identical` in `testgen.json`, and re-records `baseline.json`
   (`testgen_refreshed: true`) since the stable test set grew.
3. `_revert_disallowed(repo, gen_dir, allowed)`: tracked edits checked out, untracked files
   removed and emptied parents pruned (`-uall` so a fresh gen_dir is not collapsed/rmtree'd),
   any gen_dir file that is not an allowed module test file removed; `reverted` audited.
4. `testgen_decisions.json` persisted after every module.
5. Kill = ≥1 test **failed with collection intact** (pytest-json-report), not exit!=0;
   timeouts / broken collection are `mutant-invalid` (excluded from denominator, not kills).
6. `cov.status not in (ok, no_tests)` → skip with recorded status (no ranking on garbage);
   `no_tests` is the legitimate bootstrap path and still proceeds.
7. Lows: distinct drop labels (`dropped_no_file`/`dropped_failed_on_real`/`dropped_zero_kill`);
   run-dir lock file; `no_mutants` status for undedentable/mutant-less spans; magic numbers →
   config; one shared `append_agent_action` helper (context.py, used by baseline + testgen);
   theater-trimming removed (fragile; whole-file zero-kill drop already prevents theater);
   test cruft removed.

Deviations from the S6 sketch (all noted in DESIGN 3.6 "Implementation notes"):
1. Test-gen computes its OWN coverage in-container (it is P1, before the P2 knowledge
   layer builds `coverage.json`); it does not read `knowledge/coverage.json`.
2. Generated tests placed beside existing tests (see above), not always `tests/generated`.
3. Write agent gets `read_file/grep/write_file/run` only, not the P2 graph tools
   (`show_symbol/callers/tests_for`) — the graph is not built yet; all facts are in the
   prompt (DESIGN 3.6 already specifies in-prompt facts).
4. The container-driven agent is tested with a SCRIPTED endpoint (real Docker + real
   mutation), not cassettes — same precedent as the P3 verifier agent; a tool loop that
   branches on container output cannot be replayed byte-for-byte. So NO new cassette stage.

Tests (`tests/test_testgen.py`, 14): each mutator parses/differs/keeps its def; driver
leaves the rest of the file byte-identical; ranking skip reasons + selection + score>0 +
uncovered-ratio; disabled no-op; `_revert_disallowed` undoes source edits + new dirs + stray
gen files (git-only, offline); weak-survives/strong-kills (real container); generation keeps
strong + drops zero-kill (scripted agent, real Docker). Shared `mini_env` fixture + three
pre-S6 hygiene/knowledge tests run with `testgen.enabled=False` so the S5 cassette stage is
undisturbed.

Suite (whole repo, once at end of the review round): `pytest` → 165 passed / 3 deselected
(4:21); `-m slow` → 3 passed / 165 deselected; `ruff check .` clean.

Config added: `testgen.enabled/place_beside_existing_tests/generated_subdir/
max_agent_runs_per_repo/agent_max_turns/mutant_timeout_s/run_output_chars/example_test_chars/
summary_chars/{targets,results,decisions,lock}_filename/commit_label`; `run_coverage` gained
an `ignore` param; `testgen.py`+`mutate.py` in `hygiene_code_files`; `--no-testgen` CLI flag.
HEURISTICS rows added.

Things S7+ must know: generated tests are a pipeline commit AFTER `base_sha`, so P3/history
mining (at/under base_sha) is unaffected. `hygiene/testgen.json` carries the mutation
scores REPORT should cite. The collateral baseline for FUTURE tasks now includes generated
tests (recorded in the commit); existing built tasks are self-contained (own trees) and
were NOT re-validated. Not done: generated tests are not fed back into P2 coverage/test_map
unless the knowledge stage is re-run (go through the runner, don't hand-edit).

### S7

Step 7: P2 `.okf/` Open Knowledge Format bundle + static claim verifier + `okf(path)`
agent tool. Wired as a resumable knowledge step `okf` after `verify`; `okf.enabled=False`
skips it.

What exists:
- `pipeline/knowledge/okf.py` — writes `knowledge/.okf/` (OKF v0.2): reserved `index.md`
  (okf_version + progressive-disclosure listing) and `log.md`; `repo.md` (test command +
  layout); `modules/<mod>.md` (purpose + API + internal helpers + calls + tests);
  `functions/<mod>/<qualname>.md` (contract + callers/callees/tests links). The STATIC
  skeleton (structure, signatures, resources `/(path)#Lx-Ly`, callers/callees/tests) is
  100% graph/symbol-derived; the BIG model authors ONLY `purpose` (per module) and the
  per-function contract `{inputs, outputs, raises, side_effects, invariants}`
  (`p2.okf.module_purpose` / `p2.okf.function_contracts`, batched per module, chunked by
  `llm.okf_module_chunk_tokens`). Every claim persisted by content hash
  (`okf_decisions.json`) → 0-token, byte-identical reruns. Frontmatter = inline JSON
  (valid YAML, no pyyaml dep). Function pages: public OR complexity >=
  `okf.min_private_page_complexity`, capped at `max_function_pages`; trivial helpers
  summarized in the module page. Links emitted only to pages that exist (no dangling
  links). `generated.at` pinned to the base commit date (stable → byte-identical).
- `pipeline/knowledge/okf_verify.py` — re-derives claims from AST/graph and stamps each
  page: all claims supported → `verified: [{by: process:okf-verifier, at}]` + `status:
  stable`; else stays `draft` with the unsupported claims recorded. Checks: `raises` ∩
  explicit AST `raise` (function + one-hop intra-repo callee); `side_effects: none` vs
  global/nonlocal writes, attribute stores, IO-like calls; callers/callees links ∩ graph
  edges; `.md` links resolve. Plus an OKF conformance check (every non-reserved page has
  parseable frontmatter with non-empty `type`; `index.md` has `okf_version`).
  `okf_verification.json` = per-claim-type precision + unsupported list + conformance.
- `okf(path)` agent tool (`pipeline/agent/tools.py`) reads one bundle page, sandboxed to
  the `.okf` dir (path escape → error).

Real runs (BIG model live). Numbers below are post-review-round (stricter verifier).
Semantic precision = independently re-derived from source; by-construction (callers, `.md`
links) is graph-derived and reported separately.

| repo | pages (mod / fn) | verified / draft | semantic: callees / raises / side_effects | by_construction |
|---|---|---|---|---|
| mini_pkg | 20 (5 / 12) | 10 / 2 | 1.0 / 0.67 / 1.0 | callers 1.0 |
| glom | 165 (12 / 150) | 105 / 45 | 1.0 / 0.79 / 0.86 | callers 1.0, link 1.0 |
| toolz | 161 (20 / 138) | 111 / 27 | 1.0 / 0.31 / 0.99 | callers 1.0, link 1.0 |
| minidump | 203 (50 / 150) | 97 / 53 | 1.0 / 0.35 / 0.83 | callers 1.0, link 1.0 |

All conformant. Bundle byte-identical across two runs (decisions cache → 0-token rerun,
verified on mini_pkg + glom). `pages` counts every `.md` (module + function + the 3
reserved repo/index/log pages); `counts.modules`/`function_pages` break it down.

`callees` is a real check (each linked callee must appear as an `ast.Call` in the function
— an independent re-parse, not the graph edge) and lands at 1.0. Low `raises` precision on
toolz/minidump is EXPECTED and honest: the model claims implicit exceptions (a dict `[]` →
KeyError, an operator → TypeError) with no explicit `raise`, and now also gets flagged for
claiming `none` when the body DOES raise; the static verifier conservatively leaves those
pages `draft` (OKF trust tier "unverified", not "wrong"). Drafts rose vs the first cut
(glom 25→45 etc.) because a page is now stamped only when >= 1 claim was actually checked
(pages of pure `inputs`/`outputs`/`invariants` prose are no longer auto-verified). REPORT
should cite the semantic precisions.

Review-round fixes (all applied; glom rebuild spent 0 tokens on contracts — reused — and a
one-time re-author of the 12 module purposes after the purpose-key change; a further
rebuild is 0-token + byte-identical):
1. Stamp `verified` only when >= 1 claim was actually checked; the entry carries
   `checks: [...]`; `okf_verification.json` lists `unchecked_claim_kinds`
   (inputs/outputs/invariants); negative-raises check (claims `none` but own body raises →
   unsupported). DESIGN drops "signature correctness verified".
2. callers/`.md` links reported under `by_construction` (graph-derived, not independent);
   `callees` upgraded to a real `ast.Call` re-parse check (semantic).
3. `index.md`: no `generated` frontmatter (only okf_version); body is
   `* [title](./path) - description`. `log.md` date-grouped. Module-page count fixed
   (uses the actual module pages written).
4. Lows: purpose decision key = hash of the RENDERED prompt (contract key kept content-
   stable so contracts reuse 0-token); chunk-level contract cache documented; LLM output
   scoped to the chunk's qualnames; per-function span context (DESIGN 4.2); `_find_def`
   imported from `source_ops`; unused params / inline imports removed; description =
   docstring first line else contract outputs; missing `base_sha` → `generated.at: ""`;
   deduped HEURISTICS row; decisions persisted in `try/finally`.

Determinism decision: `generated.at`/`verified.at` are pinned to the base commit's ISO
date (stable for a repo state) rather than wall-clock, so two runs are byte-identical
(documented in DESIGN 4.2).

Tests (`tests/test_okf.py`, 11): frontmatter round-trip + real-YAML round-trip (pyyaml
via importorskip, runs in-container); skeleton matches graph; private-low-complexity
summarized not paged; determinism byte-identical + second-run-makes-zero-LLM-calls (stub
counter); verifier stamps checked claims + records `checks`/`unchecked_claim_kinds`;
page-with-only-unverifiable-fields not stamped; verifier catches planted false `raises` +
false caller; `okf(path)` reads + sandboxes path/symlink escapes; and one cassette-replay
of the real module-purpose/function-contract calls (stage `s7_okf`). Shared `mini_env` +
`test_knowledge_e2e` set `okf.enabled=False` (BIG model, no cassette).

Suite (whole repo, after the conf.py fix): `pytest` → 177 passed / 1 skipped (pyyaml)
/ 3 deselected (3:13); `-m slow` → 3 passed / 178 deselected; `ruff check .` clean.

Post-review follow-up (source-module classification): `docs/conf.py` (and example/build
scripts) were being indexed as source modules and getting hallucinated OKF pages. Fixed at
the root: `symbols.is_source_path` — a module is source only if it lives under a package
root (a dir with `__init__.py`) or a `knowledge.source_roots` entry, is not a test, not a
packaging script (`graph.nonsource_files`), and not under `graph.nonsource_dirs`
(`docs/`, `examples/`, `scripts/`, `build/`, ...). `symbol_index` now emits `is_source`;
the graph's source-node set, test-gen's `_source_functions`, and the excision funnel all
gate on it. Module counts before → after: mini_pkg 5→5, glom 12→**11** (`conf` gone), toolz
20→**16** (`conf`/`fib`/`graph`/`wordcount` gone; real `toolz`/`tlz` kept), minidump 50→50.
Confirmed no effect on deliverables: no test-gen target was ever a docs/script function;
the only excision candidates from these modules (toolz `examples/fib.py`,
`examples/wordcount.py`) were already `rejected: uncovered` and never became tasks.
Also hardened the OKF purpose prompt (ground claims in docstring+API, do not infer from the
module name, say so when there's no meaningful API) with a hallucination guard: a purpose
naming a backticked identifier absent from the module is regenerated once, then dropped.
Test `test_docs_conf_is_not_a_source_module` + `test_purpose_hallucination_guard` cover it.

Things S8+ must know: the bundle lives at `output/<repo>/knowledge/.okf/`, manifest
`knowledge/okf.json`, verification `knowledge/okf_verification.json`; `knowledge_paths()`
exposes `okf` + `okf_manifest`. Per the S5 hand-off, `.okf` pages can be added to an
author's contract block via `instruction.task_facts` — that integration is NOT yet wired
(deferred). The `okf` step is resumable and its LLM decisions are cached, so re-running
`--stage knowledge` costs no tokens unless the graph or prompt version changes.

### S9 (Session B — finalization)

Turns the pipeline's outputs into the submission. **Net-new (S8) is CUT by decision** —
not built; history + excision fill the 10. The final live glom `--fresh` run is executed
by the author, so all committed run artifacts come from that single pass.

**What exists (new this session):**

- **Lint (P1, DESIGN 3.7).** `pipeline/hygiene/lint.py` + `PythonAdapter.lint_and_format(tree, run)`.
  ruff runs INSIDE the pinned image (exact pinned ruff, no host execution) on a throwaway
  copy; a `[tool.ruff.lint]` config is written into pyproject.toml (minimal, no
  `[build-system]`, only when absent; existing ruff config respected); `ruff check --fix` +
  `ruff format`; `# noqa` for unfixable (`lint.allow_noqa_for_unfixable`). Changed `.py` +
  config synced back host-side; the image is REBUILT (proving a fresh `docker build` still
  works, updating `build.json`'s digest) and the suite run twice — a regression reverts the
  tree and records `regressed` in `hygiene/lint.json` (files/codes/counts/noqa). Wired as a
  resumable hygiene step after `testgen` (own commit `pipeline: lint and format`, code
  fingerprint, `--no-lint`). Input hash is keyed on the PRE-lint state (Dockerfile/lock +
  baseline/testgen artifacts + `repr(lint)`) so an already-linted tree is not re-linted on
  resume. **Decision (documented):** generated tests ARE linted (committed after `base_sha`,
  so P3 mining is unaffected); historical task trees are never linted. Smoke-verified on
  mini_pkg (ruff-clean in-container, pyproject created, image rebuilt, suite green, commit
  present; resume skips).
- **Selection (P3, DESIGN 5.1/5.6).** `pipeline/tasks/select.py`, wired as the final tasks
  step `select`. Deterministic: rank by failing-on-input desc / id; reserve the
  `min_history` floor, fill by preference under `max_excision`/`max_netnew`, swap to reach
  `min_distinct_modules` and toward `difficulty.target_spread` (SOFT). Writes the repo-root
  **`tasks.json`** (PDF fields + a `python -m pipeline.validate`-able `path`) and
  `tasks/<repo>/selection.json` (every eligible task, picked/not + why). Infeasible quota →
  `SelectionInfeasible` (hard error, never a silent short-fall). Root `tasks.json` is written
  at `tasks_root.parent` (repo root for a real run; the tmp base under tests → no pollution).
- **Report (DESIGN "REPORT.md production").** `pipeline/report/build.py`: `collect()`
  aggregates every stage's artifacts (detected/changed, quarantines, dropped extras,
  image digest, test-gen mutation score, lint counts, graph/okf precision + by_construction,
  funnel counts + reject reasons, instruct/difficulty stats, per-stage timings, LLM tokens by
  step, agent-run audit) into an enriched `report_data.json`; `render()` produces the six
  required sections with tables auto-filled; `draft_narrative()` is ONE BIG
  `report.draft_sections` call (cached by hash) whose short grounded paragraphs are marked
  with `AUTHOR` comments to finish. Runs at the end of a CLI tasks run (not inside
  `run_tasks`, so tests calling `run_tasks` directly don't draft/pollute) and standalone via
  `python -m pipeline.report <repo> [--no-draft]`. A drafting failure never breaks the run.
- **Transcripts.** `transcripts/dev/`: `design-session-log.md` (copy of
  `docs/decisions-raw.md`), `prompts.md` (S1–S7 scopes + Session B verbatim), `review-rounds.md`.
  The bulky per-call `transcripts/pipeline/` + `transcripts/agent/` (2101 files, mixed-repo)
  stay gitignored as regenerable audit — the curated dev log is the committed transcript.
- **Housekeeping.** Image build carries the label `bench-pipeline=1`; `prune_dangling_bench_images()`
  + `--prune-images` remove ONLY dangling images with that label (never tagged `bench-*` or
  other images — the user's earlier concern). Deleted the two inert baseline flags
  (`env_fix_attempts`, `treat_collection_broken_as_no_tests_after_repair`) + their HEURISTICS
  rows (the collection-broken path is a documented gap, not a live flag). Added the
  `--min-failing-tests` CLI flag. `.gitignore` flipped so the deliverable set is committable
  (root `tasks.json`, `tasks/glom/`, `transcripts/dev/`, `output/glom/knowledge/repo_graph.json`
  + `.okf/`) while `output/<repo>/repo` trees, other repos' outputs, `report_data.json`, and
  raw transcripts stay ignored. `.env.example` added; README "How to run" fully updated.
- **HEURISTICS review sheet.** `docs/HEURISTICS_REVIEW.md` groups config keys as (a) fired on
  glom / (b) never fired / (c) changed from the proposal, one line each.

**Tests added:** `tests/test_select.py` (10: quotas, diversity, spread-hits-target,
determinism, three infeasible cases, root_entry PDF fields, run_selection writer),
`tests/test_report.py` (6: report_data completeness/all sections, six-section render, robust
to missing artifacts, cached-draft zero-second-call, build writes REPORT.md), `tests/test_lint.py`
(4: real hygiene run with lint → ruff-clean in-container + commit + rebuild + suite green,
resume skips, disabled no-op, image label + prune-only-our-dangling). The shared fixtures
(`mini_env`, `_offline_cfg`, `mini_pkg_excision_config`, knowledge e2e) now also set
`lint.enabled=False` (like testgen/okf) so cassette stages + span/nodeid assertions run on
unformatted source; the tasks-fixture config sets feasible selection quotas + `draft=False`.

**Config added:** `lint.enabled`; `ReportConfig` (report md/data/decisions filenames,
`draft_narrative`, `draft_max_chars`); `docker.image.BUILD_LABEL` + `prune_dangling_bench_images`;
CLI flags `--no-lint`/`--no-report-draft`/`--min-failing-tests`/`--prune-images`. Removed:
`baseline.env_fix_attempts`, `baseline.treat_collection_broken_as_no_tests_after_repair`.
`lint.py` in `hygiene_code_files`; `select.py` in `tasks.code_fingerprint_files`. HEURISTICS
rows added/removed to match; DESIGN 3.7 + "REPORT.md production" updated.

**Suite (verbatim):** `.venv/bin/python -m pytest` → **195 passed, 1 skipped, 3 deselected in
230.97s (0:03:50)** (skip = pyyaml round-trip, runs in-container); `-m slow` → **3 passed, 196
deselected in 43.28s**; `.venv/bin/ruff check .` → **All checks passed!**

**For the author's final glom run:** `./run.sh https://github.com/mahmoud/glom --fresh`
produces the committed artifacts in one pass (hygiene→knowledge→tasks→select, then REPORT.md
via the CLI). Then the documented container test twice + `python -m pipeline.validate` on the
10 selected (paths in root `tasks.json`). Everything else this session is left **staged, not
committed**, for author review.
