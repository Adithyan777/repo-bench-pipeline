# System design: AI task benchmark pipeline

## Assignment and acceptance bar

Take-home for "Founding Software Engineer: AI Task Benchmark & Evaluation Infrastructure."

Build an automated, repo-agnostic pipeline in three mandatory stages. Final output: 10 validated benchmark tasks derived from a target repository. The sample target repo is [glom](https://github.com/mahmoud/glom). The pipeline will also run against a held-out repo the candidate has not seen. The PDF says: "Design for the general case. Hard-coded fixes that only work on the sample repo will score poorly."

Acceptance means: fresh clone, `docker build` succeeds, container test run passes, twice in a row with identical results, on both glom and the held-out repo.

Evaluation dimensions: held-out generality, determinism, environment quality, generated test quality (graders inject bugs to see if tests catch them), knowledge layer accuracy, task quality (real provenance, no solution leaks, verifiers accept alternative implementations, claims reproduce), engineering judgment, and AI-tool leverage with verification. A 30-minute walkthrough call follows submission: run the pipeline live, defend the design.

Rules: own work, AI assistance encouraged, no PRs/issues to the target repo.


## What glom actually looks like

Python library, ~9.4k LOC in `glom/`. Key modules: core.py (2595 lines), matching.py (1054), tutorial.py, streaming.py, mutation.py, reduction.py, grouping.py, cli.py, _version.py, and others. Tests already exist in `glom/test/` with ~180 test functions across test_basic, test_match, test_error, test_path_and_t, test_mutation, test_streaming, test_cli, test_reduction, test_grouping, etc.

1049 commits. ~140 fix-ish commits by keyword. Example: `6fd4134 fix Path.__getitem__ off-by-one (GH-299), add test extra to setup.py`, parent `e515fb3`.

Packaging: setup.py with unpinned `install_requires=['boltons>=19.3.0','attrs','face>=20.1.1']`, extras (toml, yaml, test); requirements.in + pip-compiled requirements.txt generated with Python 3.7 (pins attrs==24.2.0, boltons==24.1.0, face==24.0.0, pytest==7.4.4, PyYAML, tox, coverage<=7.2.7). tox.ini (envlist py37-py314, pypy3), pytest.ini (doctest flags), .tox-coveragerc, CI matrix 3.7-3.14. No Dockerfile, no ruff/flake8/black config, no pyproject.toml.

glom is therefore MORE hygienic than the PDF's generic description. The pipeline must handle both "has tests" and "no tests" repos.


## Guiding principles

1. **LLM proposes, deterministic code disposes.** LLMs write tests, contracts, and instructions. Code gates (mutation survival, leak checks, right-reason classification, harness verdicts) decide what ships.
2. **Determinism from gates, not models.** `temperature 0`, but no `seed` (pointless on OSS serving stacks). Repeatable outcomes come from the validation harness and hard filters, not from hoping the model returns the same text.
3. **Audit everything.** Every agent action, LLM call, files changed, diffs, and outcomes are logged to `transcripts/` and `output/audit/`. REPORT.md's "automated vs manual" section is generated from this data.
4. **Heuristics centralized.** Every threshold, filter, flag, and default lives in `pipeline/config.py` and is documented in a single `HEURISTICS.md`. No scattered magic numbers.
5. **Real integration tests.** The pipeline's own tests run against real fixture repos, real Docker, real uv, real git history. LLM calls are replayed from recorded real responses. No mocks except the LLM endpoint.


## Top-level decisions

| Decision | Choice | Rationale |
|---|---|---|
| Pipeline language | Python | -- |
| Target ecosystem | Python only, behind `EcosystemAdapter` | Non-Python: detect and exit with clear message |
| LLMs | Open-source only (training data use case). Served via Baseten, OpenAI-compatible endpoint. Two tiers: BIG = `moonshotai/Kimi-K2.6` (thinking on), SMALL = `deepseek-ai/DeepSeek-V4-Flash-0731` (reasoning `low`). Overridable via env vars. | No proprietary models |
| Agent harness | Own modular agent loop in Python. Behind `AgentRunner` interface so pi (`pi --rpc`) could be swapped in later. | Not pi/Node, not mini-swe-agent, not PiPy. Reused across all stages. ~200 lines. |
| Execution | Fully unattended: `./run.sh <repo_url_or_path>` produces everything. Human review after. REPORT documents any manual curation. | -- |
| Sandboxing | LLM calls from host. ALL code execution (tests, lint, agent bash/run tool) inside the repo's Docker container. | -- |
| Testing philosophy | Real integration tests against fixture repos, real docker/uv/git. Mocks only for LLM endpoint via record/replay of real responses. | -- |

### The held-out-repo language question

The PDF says the pipeline "takes a path or URL to any repository of the same language ecosystem" (section 3) and "Any language for the pipeline itself; the target repo's ecosystem dictates the hygiene tooling" (section 8). Nowhere does it explicitly promise the held-out repo is Python.

Decision: build Python-only behind an `EcosystemAdapter` interface. Detect ecosystem at startup and fail loudly with a clear message if not Python.


## Architecture

### Repo layout and entrypoint

```
run.sh <repo_url_or_path> [--stage hygiene|knowledge|tasks|all] [--force <step>] [--fresh] [flags]
pipeline/
  cli.py            # entry, stages, arg parsing
  config.py         # ALL thresholds + flags + per-step model map (documented in HEURISTICS.md)
  state.py          # resumability: output/<repo>/state.json, input hashing
  llm/              # openai-compat client (big/small), schema-forced JSON, retries, cache flag, usage log
  agent/            # modular tool loop + tools (read_file/grep/show_symbol/callers/callees/tests_for/show_commit/okf/run/write_file)
  docker/           # run_in_container, image build
  ecosystems/base.py  # EcosystemAdapter
  ecosystems/python.py
  hygiene/          # detect, pin, dockerfile, compose, baseline, testgen, mutate, lint
  knowledge/        # graph, indexes (history/test_map/coverage/hotspots), okf, verify
  tasks/            # funnels (history/excision/netnew), builders, harness (validate), select, manifest
  report/           # report_data.json -> REPORT.md skeleton
tests/              # pipeline's own tests: fixtures/mini_pkg, fixtures/mini_pkg_notests,
                    # real docker/uv/git integration tests, LLM record/replay
output/<repo>/      # repo/, knowledge/ (repo_graph.json, .okf/, indexes), audit/,
                    # report_data.json, state.json
tasks/<repo>/<task_id>/ ; tasks.json
REPORT.md  HEURISTICS.md  README.md  transcripts/
```


### EcosystemAdapter

The adapter isolates every ecosystem-specific operation behind ~11 methods. Everything else (agent loop, harness, funnels, okf writer, docker runner) is ecosystem-agnostic. Adding a JS adapter means implementing these methods.

```
detect(repo) -> bool
python_version(repo)
synthesize_requirements(repo) -> requirements.in
lock(repo) -> lockfile
dockerfile(repo, lock) -> str
test_command(repo) -> str
test_framework_bootstrap(repo)
lint_and_format(repo) -> report
parse_test_report(path) -> {test_id: status, reason}
symbol_index(repo) -> AST facts (functions, classes, imports, calls)
mutators()
```


### Docker execution model

Every command runs as:

```
docker run --rm --network none \
  -v <fresh workdir>:/repo -w /repo \
  <image> bash -c "<cmd>"
```

with a per-command timeout. A fresh workdir is created per unit of work (`cp -r` or `git worktree`). Nothing is shared between runs. This is parallel-safe.

Rejected alternative: long-lived container + `docker exec` (state leaks between runs).

Single helper: `run_in_container(workdir, cmd, timeout) -> (exit_code, stdout, stderr)`, used by the adapter, agent `run` tool, and validation harness. Graders' documented commands use the same image.

One image per target repo (e.g. `bench-glom`). Source is bind-mounted at runtime, not baked in. Exception: a history task at a commit with genuinely different deps gets a re-lock and per-task image variant, with the digest recorded in that task's `verdict.json`.

LLM agent repair loop if build/test fails: agent reads the build log, edits Dockerfile/requirements.in, retries. Max ~3 attempts. Fully logged and audited.


### Agent loop

```
Agent(system_prompt, tools, model, max_turns=25, max_tokens_per_tool_result~8k)
```

Uses OpenAI-compatible function calling. Goal given as the user message. The loop ends when the model replies with no tool calls; that final text is the summary (no `done` tool). Tool errors are returned as text to the model. Hard stop on turn/token cap. Result: `{files_changed, summary, trajectory_path}`. Every turn logged to `transcripts/`. Behind the `AgentRunner` interface (pi swappable). ~200 lines of code.


### Progressive-disclosure agent toolset

Shared by P1 test-gen and P3 builders:

- `read_file(path, lines?)` -- read source files
- `grep(pattern)` -- search the repo
- `show_symbol(qualname)` -- look up a function/class from the graph
- `callers(qualname)` / `callees(qualname)` -- call graph navigation
- `tests_for(qualname)` -- find tests covering a symbol
- `show_commit(sha)` -- inspect a commit
- `okf(path)` -- read an OKF knowledge page
- `run(cmd)` -- executes ONLY in the Docker container
- `write_file(path, content)` -- write files

Backed by repo_graph + .okf + git. No arbitrary host bash. The agent pulls exactly what it needs. This is cheap, works for large repos, and matches OKF's progressive-disclosure design.


### LLM client and tiers

**Models (Baseten, OpenAI-compatible):** BIG = `moonshotai/Kimi-K2.6` with thinking ON; SMALL = `deepseek-ai/DeepSeek-V4-Flash-0731` with `reasoning_effort=low`. Defaults in `config.py`, overridable via `LLM_MODEL_BIG` / `LLM_MODEL_SMALL`.

**Reasoning effort.** Some OSS models on Baseten accept a `reasoning_effort` extension (passed via `extra_body`); reasoning comes back in `message.reasoning_content` and is billed as completion tokens. Support differs per model:

| Model | `reasoning_effort` values | Disable thinking |
|---|---|---|
| `deepseek-ai/DeepSeek-V4-Flash-0731` | `none, minimal, low, medium, high (default), xhigh, max` | `reasoning_effort: "none"` |
| `zai-org/GLM-5.2` | `none, high, max` (others -> HTTP 400) | `reasoning_effort: "none"` |
| `moonshotai/Kimi-K2.6` | not supported; thinking on/off only | `extra_body.chat_template_args.enable_thinking=false` |

We normalize to our own enum `off | low | high | max` and set it **per tier** (`TIER_REASONING` in `config.py`: SMALL -> `low`, BIG -> `high` = thinking on), translated per model via `MODEL_CAPS`. No per-step reasoning knobs: two models, two settings. Day-1 check: verify tool calling works with thinking on for Kimi-K2.6 (fallback BIG: `zai-org/GLM-5.2` at `high`).

Env vars: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL_BIG`, `LLM_MODEL_SMALL`.

Uses the OpenAI Python SDK. JSON-schema outputs via forced tool-call (more reliable on OSS models than `response_format`). Fenced-JSON-in-text accepted as fallback. Every tool call validated against schema; validation errors returned to model, max 2 retries. Exponential backoff on API errors. `temperature 0`. No `seed` (pointless on OSS serving stacks; determinism comes from gates).

Disk cache of prompt-to-response by hash, behind a flag (`--llm-cache`, default off). Prompt-cache friendliness: stable prefix first (system prompt, repo/module context, tool schemas), varying part last, byte-identical system prompt within a stage.

Token accounting per stage written to `output/audit/llm_usage.json`. `MAX_LLM_TOKENS_PER_REPO` cap. Per-step model override map in `config.py`.

Tier rule: classification/lookup uses SMALL; authoring/coding/agents/review uses BIG.

| # | Stage | Step | Mode | Tier |
|---|---|---|---|---|
| 1 | P1 pin | Unknown import to PyPI name | direct JSON | SMALL |
| 2 | P1 docker | Build/install repair loop | agent | BIG |
| 3 | P1 baseline | Classify pre-existing failure: env vs genuine | direct JSON | SMALL |
| 4 | P1 baseline | Bounded fix of broken tests | agent | BIG |
| 5 | P1 test-gen | Write tests for ranked functions | agent | BIG |
| 6 | P1 test-gen | Retry with mutation feedback | agent (continuation) | BIG |
| 7 | P1 lint | Fix non-auto-fixable lint errors (optional) | direct/agent | BIG |
| 8 | P2 okf | Module purpose + public API summary | direct JSON | BIG |
| 9 | P2 okf | Per-function contracts (batched per module) | direct JSON | BIG |
| 10 | P3 history | Classify surviving commits | direct JSON batched | SMALL |
| 11 | P3 excision | Screen candidates (docstring leak / trivial) | direct JSON batched | SMALL |
| 12 | P3 net-new | Propose feature candidates | direct JSON | BIG |
| 13 | P3 build | Author/repair verifier tests | agent | BIG |
| 14 | P3 build | Neutrality check/rewrite of commit's own tests | direct/agent | BIG |
| 15 | P3 build | Implement net-new solution | agent | BIG |
| 16 | P3 build | Write instruction (no diff shown) | direct JSON | BIG |
| 17 | P3 build | Leak/quality review of instruction | direct JSON | BIG |
| 18 | P3 build | Difficulty label + justification (batched) | direct JSON | BIG |
| 18b | P3 build | goldenSolution.md "why correct" prose (`p3.build.golden_rationale`; sees the diff) | direct JSON | BIG |
| 19 | report | Draft REPORT sections from audit data (optional) | direct | BIG |

Estimated volume for glom: ~25-35 agent runs, ~100-150 direct calls.


### Transcripts and audit

- `transcripts/pipeline/<stage>/<call_id>.json` -- auto-written for every LLM/agent call (prompt, tools, responses, outcome, tokens).
- `transcripts/dev/` -- Claude Code session notes and prompts used to build the pipeline (this grill session summary + key prompts), curated by hand at the end.
- `output/audit/agent_actions.jsonl` -- `{stage, goal, files_changed, diff, attempts, outcome}` per agent action + full trajectory in transcripts/.
- `output/audit/llm_usage.json` -- token accounting per stage.


### Resumability and scale hooks

Each step writes artifacts plus `state.json`:

```json
{
  "step_name": {
    "status": "done",
    "input_hash": "abc123...",
    "finished_at": "2026-08-17T12:00:00Z"
  }
}
```

A step is skipped if its output exists and the input hash is unchanged. Downstream steps rerun on change. Flags: `--force <step>` reruns a specific step; `--fresh` reruns everything. Graders see a full run on a fresh clone.

Scale hooks implemented (the four agreed):

1. Per-repo output directories.
2. Step resumability via input hashing.
3. Parallel harness execution (ThreadPoolExecutor over docker runs).
4. Per-stage cost/time in `report_data` + `MAX_LLM_TOKENS_PER_REPO` cap.

Everything beyond these (job queue, image registry, triage, monorepos, human review sampling, non-Python support) is discussed in REPORT.md's scale section only.


---

## Pipeline 1: Hygiene

### Detection (step 3.1)

Detect ecosystem (Python) and packaging style: `pyproject.toml [project]`, `setup.py`/`setup.cfg`, `requirements.txt`/`.in`, `poetry [tool.poetry]`, or nothing.

Python version: highest CPython compatible with repo metadata (`python_requires`, classifiers, CI matrix), capped at 3.12; default 3.12 if unknown. Rationale: 3.12 has the best wheel coverage; 3.13 breaks some C-extension dependencies.


### Pinning (step 3.2)

Normalize any manifest into one canonical `requirements.in`-like input via "input synthesizers":

| Packaging style | Synthesizer |
|---|---|
| pyproject.toml | Read `[project].dependencies` |
| setup.py | Read `install_requires` (via build backend / `uv pip compile setup.py`) |
| requirements.in or .txt | Use directly |
| poetry | Translate / `poetry export` |
| Nothing | Infer third-party imports via AST + alias table (yaml->PyYAML, cv2->opencv-python, etc.) with LLM fallback (SMALL) for unknown mappings |

Include runtime deps + test tools (pytest, coverage, pytest-json-report/junit) + dev tools (ruff).

Single resolver: `uv pip compile --generate-hashes --python-version X` produces `requirements.lock.txt` (pip-installable, fully pinned with hashes). Also emit `constraints.txt` so `setup.py` installs resolve identically.

uv facts: `uv lock` needs `pyproject.toml` with `[project]`; `uv pip compile` reads setup.py/requirements/pyproject directly; poetry is not natively read by uv.

Rejected alternatives: pip-tools (slower, weaker pyproject support); using the repo's own tool first (3x code paths).


### Dockerfile (step 3.3)

Templated Dockerfile:

```dockerfile
FROM python:3.X-slim@sha256:<digest>
# pinned base image digest
COPY requirements.lock.txt .
RUN pip install --no-deps -r requirements.lock.txt
# install repo
RUN pip install --no-deps -e .
CMD ["pytest", "..."]
```

Plus `.dockerignore`.

Compose detection is deterministic. The pipeline looks for:

- Imports/deps: psycopg2/asyncpg/sqlalchemy+postgres URL -> postgres; redis -> redis; pymongo -> mongo; celery/kombu -> broker.
- Config files: existing `docker-compose*.yml`, `.env.example` with `DATABASE_URL`/`REDIS_URL`, conftest fixtures with hosts/ports.
- Test signals: `ConnectionRefused` in baseline output.

If detected: emit `docker-compose.yml` with app service + pinned service images (e.g. `postgres:16.4@sha256:...`) + env wiring + `depends_on`/healthchecks. Test command becomes `docker compose run --rm app <cmd>`.

Scope: templates for postgres + redis only. Anything else detected is reported as unsupported. For glom, none of this fires.


### Baseline tests (step 3.5)

Detect framework: pytest (`pytest.ini`/`tox.ini`/`conftest`/tests dir/`setup.cfg`) > unittest > none.

Run baseline in container with structured report (pytest json-report or junitxml) producing `baseline.json`:

```json
{"test_id": "pass|fail|error", "reason": "..."}
```

Handling by outcome:

- **All pass**: continue.
- **Some fail**: classify with LLM (SMALL) as env-related (missing optional dep, network, py-version) vs genuine. One automatic env-fix attempt (add missing extra, rerun). One BOUNDED agent-fix attempt (audited). Otherwise quarantine via generated `--deselect` list (`tests/quarantine.txt`) and report in REPORT.md. Never delete tests. Never fake results.
- **Collection broken** (import errors, 0 collected): one repair attempt, then treated as "no tests."
- **No tests**: bootstrap pytest layout (`tests/`, `conftest.py`); test-gen becomes mandatory; baseline is trivially empty-pass.

Baseline JSON also feeds P3 (which tests are stable).

Every agent action (Dockerfile repair, test fix, test-gen, verifier authoring) is audited: `output/audit/agent_actions.jsonl` per action, plus full trajectory in `transcripts/`. REPORT's "automated vs manual" section is generated from this.


### Test generation (step 3.6)

Ranking is deterministic:

1. `coverage run -m pytest` then `coverage json` to get missed lines per file.
2. AST walk every function/method: file, qualname, start/end line, is_public, cyclomatic complexity (via radon or simple branch counter), has_docstring, param count.
3. Join: `uncovered_ratio = missed_lines_in_span / span_lines`.
4. Score = `uncovered_ratio * log(1+total_lines) * (1 + complexity/5) * public_bonus * not_dunder * not_test_file`.
5. Filters: skip `__init__.py` re-exports, CLI `main()`, functions < 3 lines, anything in test dirs, `_private` unless high complexity, module-level scripts.
6. Group by module. Top K modules (K=5 default, configurable). Within each module, top N functions.

Agent (BIG) receives source, module imports, and 2 examples of the existing test style. Writes `tests/generated/test_<mod>.py`.

Mutation gate: tests must pass on real code AND kill at least 1 of ~4 injected mutants per targeted function. Mutations use our own AST mutators (not mutmut):

- Comparison flip/boundary: `<` to `<=`, `<` to `>`
- Arithmetic swap: `+1` to `-1`
- and/or swap
- `return` to `return None`
- Constant tweak: `True` to `False`
- Statement delete

Mutants are applied in-container on a fresh copy. Feedback loop: up to 2 retries with "mutant X survived, assert the boundary" feedback. Tests that kill nothing are dropped. The same mutators are reused by P3 to prove verifiers discriminate.

Rationale: the mutation gate is the only automated evidence that tests are meaningful. It mirrors the graders' "inject bugs" evaluation approach.


### Lint and format (step 3.7)

ruff (lint + format), conservative rule set: E, F, W, I, B, UP. Run `ruff check --fix` then `ruff format`. Config in pyproject.toml. Remaining unfixable errors get per-file `# noqa` only if truly unfixable, and are reported. Optional LLM fix (BIG) for lint errors ruff cannot auto-fix.

Rejected: black+isort+flake8 (three tools); mypy (untyped repos produce hundreds of unfixable errors).

Historical trees used by P3 tasks are never lint/formatted (would pollute the real diff).


### Output layout for the transformed repo (step 3.8)

`output/<repo-name>/repo/` = clean clone. Pipeline changes committed as separate labeled commits (pin / docker / tests / lint). P3 mines ONLY original history: commits before our first pipeline commit, identified by a SHA marker.


---

## Pipeline 2: Knowledge layer

### repo_graph.json (step 4.1)

100% deterministic, static analysis. No LLM. Built AFTER the index data files (4.3):
the coverage %, test refs and `tested_by` edges below are joined in from
test_map/coverage, so the run order is symbol_index → indexes → graph → verify.

Nodes: module, class, function/method. Each carries: file, line span, signature, docstring, complexity, coverage %, test refs.

Edges:

| Edge type | How resolved |
|---|---|
| imports | AST import statements |
| contains | module-to-class, class-to-method |
| calls | Intra-repo, AST name-resolved. Unresolved calls listed separately, never guessed. |
| inherits | Class inheritance |
| tested_by | Test-to-function mapping |

Every edge carries `evidence: {file, line}` so graders can verify against source.

Module definition: one `.py` file = one module; package = dir with `__init__.py`. Diversity unit = source file for glom-sized repos; top-level subpackage for big repos.

Self-verification: a script samples N edges and re-derives them independently (regex import check, runtime import to confirm symbols exist, dynamic call trace from tests for `calls` edges). Output: `graph_verification.json` with precision stats for REPORT.


### .okf/ (step 4.2)

Open Knowledge Format follows the Google Cloud spec v0.2 (June 2026). OKF is a directory of Markdown files with YAML frontmatter, cross-linked via markdown links.

Spec link: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md

OKF spec facts:
- Reserved files: `index.md` (progressive-disclosure listing) and `log.md`.
- Required frontmatter: `type`.
- Recommended frontmatter: `title`, `description`, `resource` (URI of asset), `tags`.
- Provenance: `sources[] {resource (required), id, title, author, usage_count, last_modified}`.
- Trust: `generated {by, at}`, `verified [{by, at}]`.
- Lifecycle: `status: draft|stable|deprecated`, `stale_after`.
- Actor convention: `<producer>/<version>` for tools, `human:<id>`, `process:<id>`.
- Trust tiers: no verified field = unverified; non-human verified = machine-confirmed; human verified = human-reviewed.
- Links: `[title](/bundle/relative/path.md)`.
- Conformance: every non-reserved .md has parseable frontmatter with non-empty `type`; consumers must not reject for unknown fields or broken links.
- Reference implementation exists (okf-rs, Rust) but we don't depend on it.

Our .okf structure:

```
.okf/
  index.md                            # root
  repo.md                             # entrypoints, test cmd, conventions
  modules/<mod>.md                    # purpose, public API, links
  functions/<mod>/<qualname>.md       # contracts + links to callers/callees/tests
  log.md
```

Function pages are created for public + top-complexity functions, capped at ~150 files. Others are summarized in their module page.

Each function page includes a contract: `{inputs, outputs, raises, side_effects, invariants}` plus links to callers, callees, and tests.

Frontmatter we emit: `type` (python-module, python-function, etc.), `title`, `description`, `resource` (`/path#Lx-Ly`), `sources`, `generated {by: "pipeline/<model>", at}`, `verified []`, `tags`, `status`.

LLM (BIG) writes ONLY purpose and contracts. The static skeleton comes from the graph. A static claim verifier then re-checks: `raises` claims intersected with AST raise statements, callers intersected with graph, signature correctness. Verified claims get `verified: [{by: "process:okf-verifier"}]`. Unsupported claims stay `status: draft`.

Context strategy for LLM calls: per-module calls receive module source + direct deps' signatures (from graph) + related tests. Modules exceeding N tokens are chunked by class/function. Parallelizable. Never whole-repo-in-one-prompt.


### Index data files for P3 (step 4.3)

All deterministic, no LLM.

- `history_index.json`: per commit in ORIGINAL history: sha, parent, message, files changed, +/- lines, touched functions (diff line ranges intersected with AST), test files touched, is_merge, pr_number if in message. No LLM labels here (labels live in P3, only for filter survivors).
- `test_map.json`: test_id to functions executed (pytest run with coverage dynamic contexts, joined with AST).
- `coverage.json`: per-function coverage %.
- `hotspots.json`: change frequency per function.


---

## Pipeline 3: Task generation

### Overall shape (step 5.1)

Deterministic candidate funnels (code) produce candidates. LLM (SMALL) classifies and ranks them. Per-candidate task-builder agents (BIG, with tools) construct the task. A deterministic validation harness verifies. Selection picks the best 10. `tasks.json` is written.

Task mining is NOT a free-roaming agent (non-reproducible, expensive, hard to explain). Building each task IS agentic.

Every rejected candidate gets a `reject_reason` string in `candidates.json`, which feeds REPORT's "what you rejected and on what grounds" section.

Quota and mix: net-new max 2 (user preference over the spec's max 3), excision max 4, history fills the rest (at least 4 required). Build extra candidates (~8 history, ~5 excision, ~3 net-new), validate all, then select the best 10 with module diversity (at least 4 modules) and difficulty spread (~2 easy, ~5 medium, ~3 hard).


### History-derived funnel (step 5.2)

Hard filters (all deterministic code):

- Drop merge commits (handled specially: PR merge uses input=first parent, solution=merge; plain commit uses parent/commit).
- Drop if no non-test `.py` file touched.
- Drop if only docs/CI/version/changelog changed.
- Drop if diff < 3 or > 300 source lines.
- Drop if > 6 source files touched.
- Drop if touched functions have zero coverage in test_map AND commit adds no tests.
- Drop if either state doesn't parse (AST).
- Drop if commit touches manifest (setup.py/requirements*/pyproject): `reject_reason: dependency-changing` (optionally re-lock instead).
- Drop if it's one of our pipeline commits.

Signal score (deterministic):

- Message matches `fix|bug|GH-\d+|#\d+|error|incorrect|regression|edge case` (+)
- Adds/changes tests in same commit (++, ready-made verifier)
- Touched function is public / in okf (+)
- Single-function diff (+)
- Module diversity bonus
- Later reverted (-)

LLM classify (SMALL, batched ~15 per call):

```json
{
  "kind": "bugfix|feature|refactor|chore|test-only",
  "self_contained": true,
  "verifiable_via_tests": true,
  "behavior_change_summary": "...",
  "difficulty_guess": "..."
}
```

Keep bugfix or feature with `self_contained && verifiable_via_tests`. Shortlist top ~15 (aim to validate 5-6 history tasks for a safe margin above the required 4).

Build:

- `input/` = full tree at parent commit.
- `solution/` = full tree at the commit.
- Hygiene overlay on BOTH (Dockerfile, requirements.lock.txt, .dockerignore, ruff config): ADDITIVE ONLY. Never overwrite a file existing in the historical tree. Never run ruff on historical trees. So `input/` to `solution/` diff == the historical fix exactly.
- Verifier = tests added/changed by the commit (agent checks and rewrites for implementation-neutrality; BIG). If no tests were added by the commit, the agent authors tests.
- Old-commit dependency drift: reuse the current lock; fallback: re-lock at that commit (per-task image variant).

S5a implementation notes: only PR merges (a `#N` in the subject) are candidates among merges (`input/` = first parent); the commits on a surviving PR merge's branch are `superseded-by-merge`. Reverts are a hard reject (`reverted-by`) when named in a later revert body or matched by reverse `git patch-id`. The SMALL classifier walks the score-ranked survivors in batches until `shortlist_size` are kept (cap `classify_max_commits`), decisions persisted by content hash. Build gates run in the container BEFORE any BIG call and reject with a reason instead of producing an INVALID task: static gate on `verifier/` vs `input/`, verifier on `solution/` (import/collection failure = `env-drift`, other failing tests dropped), verifier on `input/` (invalid fail reason = reject, passing tests dropped, `harness.min_failing_tests` must remain); the shortlist is walked until `build_target` tasks are built. Verifier tests are the commit's added/changed test FUNCTIONS (AST diff, whole file at commit state overlaid, nodeids selected) + conftest ancestors; the collateral baseline is the suite run on `input/` (the parent), not HEAD's baseline. Re-locking at an old commit is out of scope: `env-drift` is recorded, never worked around.


### Excision funnel (step 5.3)

Select candidates from test_map + graph (deterministic code): covered by at least 2 tests, 8-80 lines, complexity >= 3, public.

Also rejected (S4): functions covered by more than `excision.max_covering_tests` tests (`too-central` -- excising glom's `TargetRegistry.get_handler` fails ~112 tests, not a focused task), methods on `_Private` classes, functions defined in `__init__.py`. Only tests that PASSED at the P1 baseline count as covering. Ranking = covering tests x complexity, round-robin over modules; the SMALL screen sees the top `build_target x screen_pool_multiplier` and the first `build_target` survivors are built. Every function considered lands in `output/<repo>/tasks/candidates.json` with a status and `reject_reason`.

Screen with LLM (SMALL): "Does the docstring spell out the implementation?" and "Is it a trivial wrapper whose callers make it obvious?" Reject if yes.

Build (code): AST rewrite replaces the function body with `raise NotImplementedError("excised")`, keeping signature + docstring. Flag `--excision-hard` (configurable) also strips the docstring, so the contract lives only in the tests and the instruction.

- `input/` = excised tree.
- `solution/` = original tree.
- Verifier = existing covering tests (+ agent-added edge-case tests if fewer than ~3 assertions touch the function).
- Fail-before: `NotImplementedError` inside behavior tests (a valid failure reason; the symbol still exists, so no import error).


### Net-new funnel (step 5.4)

LLM (BIG) proposes candidates per module from .okf module pages + public API: "natural missing capability, testable in 5 or fewer tests, 60 lines or fewer." Prefer features touching an existing module (e.g. a new glom spec type) over standalone utils. Code checks the feature doesn't already exist (grep/graph).

Agent (BIG) implements `solution/` + authors verifier tests. `input/` = current repo. Target: 2 validated (max 2 per user decision).


### Validation harness (step 5.5)

Invoked as `python -m pipeline.validate <task_dir>`. Pure code, runs in container.

Steps:

1. **Fail-before**: mount `input/` + `verifier/` in container, run verifier cmd. Must FAIL. Output: `evidence/fail_before.log`.

2. **Right-reason classifier** (STRICT): parse pytest junitxml/json-report per test. Every failing test must fail via one of:
   - `AssertionError`
   - `pytest.raises` mismatch
   - `NotImplementedError` (excision tasks)
   - Exception raised inside the function under test during a behavior test

   ZERO tolerance for: collection errors, `ImportError`/`ModuleNotFoundError`/`SyntaxError`/`AttributeError` at import time, "collected 0 items", fixture-not-found, or a test raising before calling repo code. Any of these: INVALID.

3. **Pass-after**: mount `solution/` + `verifier/` in container, run verifier cmd. Must PASS. Output: `evidence/pass_after.log`.

4. **Determinism**: repeat steps 1 and 3 N=3 times. Verdicts must be identical across runs. Output: `evidence/determinism.json {runs: 3, fail_before: [...], pass_after: [...]}`.

5. **Collateral**: run the repo's full suite on `solution/` vs P1 baseline. No newly failing test. Output: `evidence/collateral.json`. Runs for excision tasks too (uniformity).

6. **Verdict**: `evidence/verdict.json {valid, checks, timestamp, image_digest}`. The `validation_status` field in `tasks.json` is READ from `verdict.json`, never hand-typed.

The harness ALWAYS re-copies the canonical `verifier/` into the workspace before judging (so a solving agent that edits tests cannot hack the verdict). Harness runs tasks in parallel (ThreadPoolExecutor over docker runs).

Alternative-implementation evidence: static gate only. Verifier tests may only import public symbols that exist in `input/`. Rejected alternative: agent-written alternative solutions per task.

S4 implementation notes: `verifier/` mirrors repo-relative paths (`verifier/glom/test/test_x.py`, plus `conftest.py` ancestors and a `run.sh`), so "re-copy the canonical verifier" is a directory overlay onto the fresh workdir. The static gate judges `from <repo module> import <name>` statements over modules that exist in `input/` (private name or missing name -> INVALID); modules it cannot see statically (toolz's `tlz` builds submodules at import time) are left to the container runs. `verdict.json` records the LIVE image digest and whether it matches `task.json` but does not gate on it (`harness.gate_on_image_digest=False`): a rebuild from the same pinned Dockerfile yields a new image Id, and pinning would invalidate every task after any rebuild. A missing image is always INVALID. `determinism_runs` counts the primary run.


### task.json and instruction (step 5.6)

task.json fields:

```json
{
  "id": "...",
  "title": "...",
  "provenance": {
    "type": "history|excision|net-new",
    "commit": "...",
    "parent": "...",
    "pr": "..."
  },
  "difficulty": "easy|medium|hard",
  "difficulty_rationale": "...",
  "files_in_scope": ["..."],
  "instruction": "...",
  "verifier_cmd": "...",
  "image_digest": "..."
}
```

`files_in_scope` = files touched by the solution diff + their direct importers/tests (from graph). Multi-file fixes have all touched files in scope. Never a single line pointer.

Instruction structure:

1. Goal.
2. Observable behavior with 1-2 concrete input-to-output examples COPIED from verifier tests.
3. Constraints.
4. How success is measured (verifier command).

The instruction authoring agent/call (BIG) is NOT shown the diff. It sees: `input/` tree, verifier tests, okf contract, behavior summary. This is structural leak prevention.

Instruction gates:

- **(a) Code leak check**: no line of solution diff (5 or more tokens) appears in the instruction. No identifiers newly introduced by the diff are named unless they appear in the public API or tests.
- **(b) Reviewer (BIG)**: scores "solvable by transcription?" and "self-contained?" Regenerate on fail.

Verifier visibility flag: `--verifier-visibility visible|hidden`, default `visible` (matches PDF layout; hack-proof via harness re-copy). Hidden mode: only the instruction is in the workspace; instruction must carry the full contract.

Difficulty assignment: code computes features (files touched, functions touched, callers count, cross-module edges, diff size, similar-named functions nearby, test count). LLM (BIG) assigns a label + 1-2 sentence justification that must cite at least 1 computed feature. Selection aims for spread.

goldenSolution.md: diff (code) + "why correct" paragraph (LLM).

S5b implementation notes: the author sees the touched functions' signatures + docstrings AS THEY ARE IN `input/`, the verifier test sources, the behavior summary (history) / excised-contract note (excision), files_in_scope, the verifier command and the visibility phrase; the diff and `solution/` are never in its prompt. Gate (a) is pure code over the input->solution diff of the touched source files (only ADDED lines are gated — removed lines already exist in `input/` — with >= 5 tokens, minus lines that also appear in the verifier tests; plus API-like identifiers introduced by the diff outside input/'s public API and the tests), applied to instruction and title; gate (b) is a BIG reviewer (`solvable_by_transcription`, `self_contained`, `implementation_neutral`, issues). Both feed the next attempt; after `max_regenerations` the task is `instruction_status: failed`. The "why correct" prose is a separate BIG call (`p3.build.golden_rationale`) that may see the diff. Difficulty features come from the diff + `repo_graph.json`; labels are batched; a rationale that cites no feature is regenerated once, then `difficulty_status: failed`. Every decision is persisted by content hash (`output/<repo>/tasks/instructions.json`). `task.json.module` (primary touched module) and `modules[]` are always set.

Dockerfile + lock present inside `input/` and `solution/` (overlay). Image digest recorded in `task.json` and `verdict.json`. Each task is self-contained and re-buildable.


---

## REPORT.md production

Pipeline generates `output/<repo>/report_data.json` containing: what was detected/changed, quarantines, candidates + rejections, quotas, gates hit, LLM usage, and per-stage timings.

A REPORT.md skeleton is generated with tables filled from `report_data.json`. Narrative sections (design/trade-offs, scale, gaps) are hand-written by the author + Claude at the end.

Rejected: fully LLM-generated report.


---

## Build order

Principle: build first what would force a redesign if it failed. Reach one validated task end-to-end as soon as possible. The pipeline's own tests are real integration tests (fixture repos, real docker/uv/git; LLM record/replay only).

### Step 0: Fixture repos

Create `tests/fixtures/mini_pkg/` (tiny Python lib, 3 modules, some tests, git history with 5-6 commits including one bugfix + one dep change) and `mini_pkg_notests/`.

### Step 1: Foundation

Skeleton, config.py, state/resume, `run_in_container`, LLM client (record/replay), agent loop.

Test: real container run; agent solves a toy task with a replayed transcript.

### Step 2: P1 core

Detect, synthesize, uv lock, Dockerfile, build, baseline (quarantine path).

Test: mini_pkg and mini_pkg_notests build + baseline JSON as expected; then glom.

### Step 2b: Dry-run P1 on a second real repo

Started here and rerun continuously.

### Step 3: P2 static

symbol_index, then the index data files (history_index, test_map, coverage, hotspots),
then repo_graph, then graph self-verification. Order note: repo_graph nodes carry
coverage % / test refs and there is a `tested_by` edge, all derived from
test_map/coverage — so the indexes are built BEFORE the graph
(`symbol_index → indexes → graph → verify`), not after it as an earlier draft of
section 4.1 implied.

Test: mini_pkg graph == expected edges; test_map matches known coverage.

### Step 4: P3 excision + harness end-to-end

Test: excise known mini_pkg function -> VALID; broken verifier (import error) -> INVALID; flaky test -> determinism fail.

### Step 5: P3 history

Funnel + build + agent verifiers + instruction + leak gate + difficulty.

Test: mini_pkg bugfix commit surfaces; chore rejected with reason; task validates.

### Step 6: P1 test-gen + mutators

Test: mutators produce parseable code; weak test survives, strong test kills.

### Step 7: P2 okf + claim verifier

Test: frontmatter conforms; verifier catches planted false "raises".

### Step 8: P3 net-new

Test: e2e on mini_pkg with replayed LLM.

### Step 9: Integration

Lint/format, task selection & quotas, tasks.json, report_data -> REPORT skeleton, transcripts curation, HEURISTICS.md.

Test: selection respects quotas/diversity on synthetic candidates.

### Step 10: Full held-out dry-run

Run on 2 repos (one small pure-Python lib with tests + history, e.g. boltons-sized or smaller; one with NO tests), fresh clone, twice, diff results.

### Alternative reorders considered

- Test-gen earlier (after step 2).
- OKF before history.
- All-10-tasks-first (4 -> 5 -> 8).
- Continuous held-out loop from step 2b onward.
- Strict P1 -> P2 -> P3 sequential (argued against: harness/format problems found late).


---

## Held-out dry-run plan

Two repo shapes:

1. Small pure-Python lib with tests + git history (boltons/attrs-sized or smaller).
2. One with NO tests to exercise the bootstrap path.

Concrete picks (surveyed 2026-08-17 via GitHub API + shallow clones):

| Shape | Primary | Backup | Why |
|---|---|---|---|
| A: has tests + history | `pytoolz/toolz` (~7k LOC, 16 source modules, 29 test files, 1230 commits, **pyproject-only**, requires-python >=3.9, no runtime deps) | `jd/tenacity` (~6k LOC, 11 modules, 6 test files, 614 commits, pyproject + setuptools_scm dynamic version, requires-python >=3.10) | Different packaging style from glom's setup.py; deep bugfix history; enough modules for the >=4-module diversity rule |
| B: no tests | `skelsec/minidump` (~7.6k LOC, 45 source modules, zero tests, setup.py + pyproject, python_requires >=3.6, no runtime deps, offline binary parsing) | `baopng/NSGA-II` (7 modules, ~330 LOC, setup.py/cfg, deps tqdm+matplotlib, only 13 commits -> P1 only) | Exercises pytest bootstrap + test-gen from zero; deterministic and testable |

Rejected: single-module libs (`dbader/schedule`, `astanin/python-tabulate`, `leviathan0992/Pylsy`) fail the >=4-module rule; hardware libs (jetson-gpio, sense-hat, DHT11, pi-rc522) and network-bound libs (pywit, googlesearch, certstream, TweeterPy, Arjun, Photon) make generated tests depend on mocks/network.

Process: fresh clone, run full pipeline twice, diff results. Run from step 2b onward during development to catch generality problems early.


---

## Open items / TBD

- **Heuristics review**: all thresholds in HEURISTICS.md are PROPOSED and require user confirmation before finalization.
