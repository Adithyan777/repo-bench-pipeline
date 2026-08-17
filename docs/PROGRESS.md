# Progress

Handoff file between implementation sessions. One session per step, sequential.
Every session: read `docs/DESIGN.md`, `HEURISTICS.md`, `pipeline/config.py`, this file; do its step; update its row + notes; leave changes staged (author commits).

Legend: `todo` · `in-progress` · `review` (awaiting author review) · `done`

| Step | Scope | Status | Session notes |
|---|---|---|---|
| S1 | Steps 0+1: fixture repos (`tests/fixtures/mini_pkg`, `mini_pkg_notests`), package skeleton, `state` (resumability), `docker.run_in_container` + image build, LLM client (big/small, reasoning per tier, schema-forced JSON, retries, usage log, record/replay), agent loop + tools, foundation tests | review | See `### S1`. `pytest` → 32 passed (Docker live). Cassettes recorded (1049 tokens). Kimi-K2.6 tool-calling-with-thinking day-1 check PASSED. |
| S2 | Step 2+2b: P1 core — detect → synthesize requirements → uv lock → Dockerfile/compose → build → baseline + quarantine; `ecosystems/python.py`; run on glom, then toolz + minidump | todo | |
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
