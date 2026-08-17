# DECISIONS DUMP — AI Task Benchmark Pipeline (source of truth for design docs)

Everything below was decided in a grill session between the user (Adithyan) and Claude on 2026-08-17. Nothing here is optional prose; every fact must survive into the design doc.

## 0. Assignment context (from the PDF)

- Take-home: "Founding Software Engineer — AI Task Benchmark & Evaluation Infrastructure".
- Build an automated, repo-agnostic pipeline in 3 mandatory stages; final output = 10 validated benchmark tasks derived from a target repo.
- Sample target repo: https://github.com/mahmoud/glom . Pipeline will ALSO be run against a held-out repo we haven't seen. "Design for the general case. Hard-coded fixes that only work on the sample repo will score poorly."
- PDF §3: pipeline "takes a path or URL to any repository of the same language ecosystem". §8: "Any language for the pipeline itself; the target repo's ecosystem dictates the hygiene tooling." Nowhere does it explicitly promise the held-out repo is Python. Decision: build Python-only behind an `EcosystemAdapter` interface; detect ecosystem and fail loudly if not Python.
- Pipeline 1 (Hygiene): dependency pinning (exact versions, lockfile, deterministic fresh-clone install), containerization (Dockerfile + compose if services; build + test suite runs in container with single documented command), test generation (detect modules lacking coverage, generate meaningful unit tests asserting real behavior — graders will inject bugs to check tests catch them), linting/formatting (standard config, repo left lint-clean). Acceptance: fresh clone, docker build succeeds, container test run passes, twice in a row identical, on sample AND held-out repo.
- Pipeline 2 (Knowledge Layer): structured knowledge layer, machine input for Pipeline 3, not human docs. Deliverables mention `repo_graph.json` and `.okf/`. Graded: "Graph edges verified against source; OKF claims verified against code."
- Pipeline 3 (Task Generation): exactly 10 validated tasks. Sources: History-derived (merged PR/commit fixing bug or adding feature; input/=parent-commit state, solution/=post-merge state, golden=real diff) REQUIRED ≥4 of 10; Excision red→green (working covered function, remove implementation leaving signature+contract, tests define behavior, golden=original impl) MAX 4 of 10; Net-new feature (capability repo lacks, defined entirely by tests we author) MAX 3 of 10 (user decided we target max 2). Diversity: tasks span ≥4 distinct modules.
- Task folder: `tasks/<task_id>/ task.json (id,title,instruction,provenance,difficulty,files_in_scope) input/ solution/ verifier/ (tests+run command) goldenSolution.md (diff + why correct) evidence/`.
- Instruction quality: implementation-neutral, no solution leak, self-contained.
- Validation evidence per task (mandatory, machine-generated): fail-before for the RIGHT reason (assertion about behavior; import/syntax/missing-file failures don't count), pass-after, determinism across repeated runs (state repeat count), no collateral breakage of broader suite. Must be a validation harness that runs over any task folder and emits a verdict; graders re-run.
- Difficulty: easy/medium/hard + 1–2 sentence justification (cross-module reasoning, business-logic knowledge, misleading similar code, coordinated multi-file changes). No need to run agents.
- `tasks.json` at root indexing all 10: id, title, source type, module, difficulty, provenance (commit SHA or excision target), verifier command, validation status.
- Deliverables: `pipeline/` (all 3 stages, one entry point e.g. `./run.sh <repo_url_or_path>`), `output/` (transformed sample repo + repo_graph.json + .okf/), `tasks/` + `tasks.json`, `REPORT.md`, `transcripts/` (key agent prompts and/or session logs).
- REPORT.md required sections: (1) what was broken and how pipeline fixes each class; (2) design decisions & trade-offs — automated vs manual and why; (3) how task-candidate selection works: mined, rejected, on what grounds; (4) how to run everything: exact commands per stage and container test run; (5) scale answer: what breaks at 100 repos, what to build differently; (6) honest gaps.
- Evaluation dimensions: held-out generality, determinism, environment quality, generated test quality (catch injected bugs, not coverage theater), knowledge layer accuracy, task quality (real provenance, no leaks, verifiers accept alternative implementations, claims reproduce), engineering judgment, AI-tool leverage with verification.
- 30-min walkthrough call afterwards: run pipeline live, defend design.
- Rules: own work; AI assistance encouraged; no PRs/issues upstream.

## 1. Facts about glom (observed 2026-08-17)

- Python library, ~9.4k LOC in `glom/`; modules: core.py (2595 lines), matching.py (1054), tutorial.py, streaming.py, mutation.py, reduction.py, grouping.py, cli.py, _version.py, etc. Tests already exist: `glom/test/` with ~180 test functions across test_basic, test_match, test_error, test_path_and_t, test_mutation, test_streaming, test_cli, test_reduction, test_grouping, etc. So "test generation" for glom = filling coverage gaps, not from-zero.
- 1049 commits; ~140 fix-ish commits by keyword. Example: `6fd4134 fix Path.__getitem__ off-by-one (GH-299), add test extra to setup.py`, parent `e515fb3`.
- Packaging: setup.py with unpinned `install_requires=['boltons>=19.3.0','attrs','face>=20.1.1']`, extras (toml, yaml, test); requirements.in + pip-compiled requirements.txt generated with Python 3.7 (pins attrs==24.2.0, boltons==24.1.0, face==24.0.0, pytest==7.4.4, PyYAML, tox, coverage<=7.2.7). tox.ini (envlist py37–py314, pypy3), pytest.ini (doctest flags), .tox-coveragerc, CI matrix 3.7–3.14. No Dockerfile, no ruff/flake8/black config, no pyproject.toml.
- glom is therefore MORE hygienic than the PDF's generic description; pipeline must handle both "has tests" and "no tests" repos.

## 2. Top-level decisions

- Pipeline language: Python.
- Target support: Python only, behind `EcosystemAdapter`. Non-Python → detect and exit with clear message.
- Timeline: ASAP (no fixed days).
- LLMs: open-source models ONLY (this is for training data; no proprietary models). Served via Baseten, OpenAI-compatible endpoint. Two tiers: BIG and SMALL. Exact model IDs TBD by user (env vars).
- Agentic harness: our OWN modular agent loop in Python (not pi/Node, not mini-swe-agent, not PiPy which is bundled inside SuperQode). Reused across all stages. Kept behind an `AgentRunner` interface so pi (`pi --rpc`) could be swapped in later.
- Fully unattended: `./run.sh <repo_url_or_path>` produces everything; human review AFTER; REPORT documents manual curation.
- Sandboxing: LLM calls from host; ALL code execution (tests, lint, agent bash/run tool) inside the repo's Docker container.
- HEURISTICS rule (user feedback, strong): every heuristic/threshold/filter anywhere in the pipeline (P1 dependency detection, test-gen ranking, P3 funnels, etc.) AND every flag/default must be (a) centralized in `pipeline/config.py`, (b) documented in ONE `HEURISTICS.md` (sections: Heuristics & thresholds; Flags & defaults) referenced from README, (c) reviewed/confirmed with the user at the end. No scattered magic numbers.
- Testing philosophy for the pipeline's own code: REAL integration tests against real things (tiny fixture repos, real `docker run`, real `uv`, real git history) — mocks only for the LLM endpoint via record/replay of real responses.

## 3. Pipeline 1 — Hygiene decisions

### 3.1 Detection
- Detect ecosystem (Python) and packaging style: pyproject.toml `[project]`, setup.py/setup.cfg, requirements.txt/.in, poetry `[tool.poetry]`, or nothing.
- Python version: highest CPython compatible with repo metadata (`python_requires`, classifiers, CI matrix), capped at 3.12; default 3.12 if unknown. Rationale: 3.12 has best wheel coverage; 3.13 breaks some C-ext deps.

### 3.2 Pinning
- Normalize any manifest into ONE canonical `requirements.in`-like input via "input synthesizers": pyproject → read deps; setup.py → read install_requires (via build backend / `uv pip compile setup.py`); requirements.in/txt → use; poetry → translate/`poetry export`; nothing → infer third-party imports via AST + alias table (yaml→PyYAML, cv2→opencv-python, …) with LLM fallback for unknown mappings.
- Include runtime deps + test tools (pytest, coverage, pytest-json-report/junit) + dev tools (ruff).
- Single resolver: `uv pip compile --generate-hashes --python-version X` → `requirements.lock.txt` (pip-installable, fully pinned with hashes). Also emit `constraints.txt` so setup.py installs resolve identically. uv facts: `uv lock` needs pyproject `[project]`; `uv pip compile` reads setup.py/requirements/pyproject directly; poetry not natively read.
- Rejected: pip-tools (slower, weaker pyproject); using repo's own tool first (3x code paths).

### 3.3 Docker
- Templated Dockerfile: `FROM python:3.X-slim@sha256:<digest>` (pinned digest), copy lock, `pip install --no-deps -r requirements.lock.txt`, install repo (`pip install --no-deps -e .` or equivalent), CMD = test command. `.dockerignore`.
- ONE image per target repo (e.g. `bench-glom`); source is bind-mounted at runtime, not baked in. Exception: history task at a commit with genuinely different deps → re-lock + per-task image variant, digest recorded in that task's verdict.json.
- LLM agent repair loop only if build/test fails: agent reads build log, edits Dockerfile/requirements.in, retries; max ~3 attempts; fully logged/audited.
- Compose: detect service needs deterministically — imports/deps (psycopg2/asyncpg/sqlalchemy+postgres URL → postgres; redis → redis; pymongo → mongo; celery/kombu → broker), config files (existing docker-compose*.yml, .env.example with DATABASE_URL/REDIS_URL, conftest fixtures with hosts/ports), test signals (ConnectionRefused in baseline). If detected: emit docker-compose.yml with app service + pinned service images (e.g. postgres:16.4@sha256:…) + env wiring + depends_on/healthchecks; test command becomes `docker compose run --rm app <cmd>`. Scope: implement templates for postgres + redis only; anything else detected → reported as unsupported. For glom none fires.

### 3.4 Docker execution model
- Every command = `docker run --rm --network none -v <fresh workdir>:/repo -w /repo <image> bash -c "<cmd>"` with per-command timeout. Fresh workdir per unit of work (cp -r or git worktree); nothing shared; parallel-safe. Rejected: long-lived container + docker exec (state leaks).
- Single helper `run_in_container(workdir, cmd, timeout) -> (exit_code, stdout, stderr)` used by adapter, agent `run` tool, harness.
- Graders' documented commands use the same image.

### 3.5 Baseline tests
- Detect framework: pytest (pytest.ini/tox.ini/conftest/tests dir/setup.cfg) > unittest > none.
- Run baseline in container with structured report (pytest json-report or junitxml) → `baseline.json {test_id: pass/fail/error, reason}`.
- All pass → continue. Some fail → classify (LLM small): env (missing optional dep, network, py-version) vs genuine; one automatic env-fix attempt (add missing extra, rerun); one BOUNDED agent-fix attempt (audited); else quarantine via generated `--deselect` list (`tests/quarantine.txt`) and report in REPORT.md. Never delete tests, never fake. Collection-broken suite (import errors / 0 collected) → one repair attempt then treated as "no tests".
- No tests → bootstrap pytest layout (`tests/`, `conftest.py`); test-gen becomes mandatory; baseline trivially empty-pass.
- Baseline JSON also feeds P3 (which tests are stable).
- Every agent action (Dockerfile repair, test fix, test-gen, verifier authoring…) is audited: `output/audit/agent_actions.jsonl` = {stage, goal, files_changed, diff, attempts, outcome} + full trajectory in transcripts/. REPORT's "automated vs manual" is generated from this.

### 3.6 Test generation
- Ranking (deterministic): `coverage run -m pytest` → `coverage json` → missed lines per file; AST walk → every function/method (file, qualname, start/end line, is_public, cyclomatic complexity via radon or simple branch counter, has_docstring, param count); join → `uncovered_ratio = missed_lines_in_span / span_lines`. Score = `uncovered_ratio * log(1+total_lines) * (1 + complexity/5) * public_bonus * not_dunder * not_test_file`. Filters: skip `__init__.py` re-exports, CLI main(), functions < 3 lines, anything in test dirs, `_private` unless high complexity, module-level scripts. Group by module, top-K modules (K=5 default, configurable), within module top-N functions handed to agent with source, module imports, 2 examples of existing test style.
- Agent (BIG) writes `tests/generated/test_<mod>.py`.
- Gate: tests pass on real code AND kill ≥1 of ~4 injected mutants per targeted function. Mutation = own AST mutators (not mutmut): comparison flip/boundary (< ↔ <=, < ↔ >), arithmetic swap (+1 ↔ -1), and/or swap, return→None, constant tweak (True↔False), statement delete. Applied in container on a fresh copy. Feedback loop: up to 2 retries with "mutant X survived — assert the boundary" feedback; drop tests that kill nothing. Mutators reused by P3 to prove verifiers discriminate.
- Rationale: mutation gate is the only automated evidence that tests are meaningful and mirrors graders' "inject bugs" evaluation.

### 3.7 Lint/format
- ruff (lint + format), conservative rule set (E, F, W, I, B, UP), `--fix`, `ruff format`; config in pyproject.toml. Remaining unfixable errors → per-file `# noqa` only if unfixable, and reported. Optional LLM fix for lint errors ruff can't auto-fix. Rejected: black+isort+flake8 (three tools), mypy (untyped repos → hundreds of unfixable errors).
- Never lint/format historical trees used by P3 tasks (would pollute the real diff).

### 3.8 Output layout for the transformed repo
- `output/<repo-name>/repo/` = clean clone; pipeline changes committed as separate labeled commits (pin / docker / tests / lint). P3 mines ONLY original history (commits before our first pipeline commit, identified by SHA marker).

## 4. Pipeline 2 — Knowledge layer decisions

### 4.1 repo_graph.json (100% deterministic, static analysis)
- Nodes: module, class, function/method with file, line span, signature, docstring, complexity, coverage %, test refs.
- Edges: imports, contains, calls (intra-repo, AST name-resolved; unresolved calls listed separately, never guessed), inherits, tested_by.
- Every edge carries `evidence: {file, line}` so graders can verify.
- Module definition: one `.py` file = one module; package = dir with `__init__.py`. Diversity unit = source file for glom-sized repos; top-level subpackage for big repos.
- Self-verification: script samples N edges, re-derives independently (regex import check, runtime import to confirm symbols exist, dynamic call trace from tests for `calls` edges) → `graph_verification.json` with precision stats for REPORT.

### 4.2 .okf/ (Open Knowledge Format — Google Cloud spec v0.2, June 2026)
- OKF = directory of Markdown files with YAML frontmatter, cross-linked via markdown links; reserved `index.md` (progressive-disclosure listing) and `log.md`. Frontmatter: required `type`; recommended `title`, `description`, `resource` (URI of asset), `tags`; provenance `sources[] {resource(required), id, title, author, usage_count, last_modified}`; trust `generated {by, at}`, `verified [{by, at}]`; lifecycle `status: draft|stable|deprecated`, `stale_after`. Actor convention: `<producer>/<version>` for tools, `human:<id>`, `process:<id>`. Trust tiers: no verified → unverified; non-human verified → machine-confirmed; human → human-reviewed. Links: `[title](/bundle/relative/path.md)`. Conformance: every non-reserved .md has parseable frontmatter with non-empty `type`; consumers must not reject for unknown fields/broken links. Spec: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md . Reference impl exists (okf-rs, Rust) but we don't depend on it.
- Our structure: `.okf/index.md` (root) → `repo.md` (entrypoints, test cmd, conventions) → `modules/<mod>.md` (purpose, public API, links) → `functions/<mod>/<qualname>.md` for public + top-complexity functions (cap ~150 files; others summarized in module page) with contract {inputs, outputs, raises, side_effects, invariants} + links to callers/callees/tests → `log.md`.
- Frontmatter we emit: type (python-module|python-function|…), title, description, resource (`/path#Lx-Ly`), sources, generated {by: "pipeline/<model>", at}, verified [], tags, status.
- LLM (BIG) writes ONLY purpose + contracts; static skeleton from graph. Static claim verifier re-checks: `raises` ∩ AST raise statements, callers ∩ graph, signature; stamps `verified: [{by: "process:okf-verifier"}]`; unsupported claims stay `status: draft`.
- Context strategy: per-module calls: module source + direct deps' signatures (from graph) + related tests; chunk modules > N tokens by class/function; parallelizable. Never whole-repo-in-one-prompt.

### 4.3 Index data files for P3 (deterministic, no LLM)
- `history_index.json`: per commit in ORIGINAL history: sha, parent, message, files changed, +/- lines, touched functions (diff line ranges ∩ AST), test files touched, is_merge, pr_number if in message. NO LLM label here (label lives in P3, only for filter survivors — placement decision, not capability removal).
- `test_map.json`: test_id → functions executed (pytest run with coverage dynamic contexts, joined with AST).
- `coverage.json`: per-function coverage %.
- `hotspots.json`: change frequency per function.

### 4.4 Progressive-disclosure agent toolset (shared by P1 test-gen and P3 builders)
- Tools: `read_file(path, lines?)`, `grep(pattern)`, `show_symbol(qualname)`, `callers(qualname)`/`callees(qualname)`, `tests_for(qualname)`, `show_commit(sha)`, `okf(path)`, `run(cmd)` (executes ONLY in the Docker container), `write_file(path, content)`. Backed by repo_graph + .okf + git. No arbitrary host bash.
- Rationale: agent pulls exactly what it needs; cheap; works for large repos; matches OKF's index.md progressive-disclosure design.

## 5. Pipeline 3 — Task generation decisions

### 5.1 Overall shape
- Deterministic candidate funnels (code) → LLM classify/rank (SMALL) → per-candidate task-builder agent (BIG, with tools) → deterministic validation harness → selection → tasks.json. Task mining is NOT a free-roaming agent (non-reproducible, expensive, hard to explain); building each task IS agentic.
- Every rejected candidate gets a `reject_reason` string in `candidates.json` → feeds REPORT "what you rejected and on what grounds".
- Quota/mix: net-new max 2, excision max 4, history fills the rest (≥4). Build extra candidates (approx 8 history / 5 excision / 3 net-new), validate all, then select best 10 with module diversity (≥4 modules) and difficulty spread (~2 easy / 5 medium / 3 hard).

### 5.2 History-derived funnel
- Hard filters (code): drop if merge commit handled specially (PR merge: input=first parent, solution=merge; plain commit: parent/commit); no non-test `.py` touched; only docs/CI/version/changelog; diff < 3 or > 300 source lines; > 6 source files; touched functions have zero coverage in test_map AND commit adds no tests; doesn't parse (AST) at either state; touches manifest (setup.py/requirements*/pyproject) → `reject_reason: dependency-changing` (optionally re-lock instead); is one of our pipeline commits.
- Signal score (code): message matches `fix|bug|GH-\d+|#\d+|error|incorrect|regression|edge case` (+); adds/changes tests in same commit (++, ready-made verifier); touched fn public / in okf (+); single-function diff (+); module diversity bonus; later reverted (−).
- LLM classify (SMALL, batched ~15/call): {kind: bugfix|feature|refactor|chore|test-only, self_contained: bool, verifiable_via_tests: bool, behavior_change_summary, difficulty_guess}. Keep bugfix|feature with self_contained && verifiable_via_tests.
- Shortlist top ~15 (aim to validate 5–6 history tasks for a safe ≥4).
- Build: input/ = full tree at parent, solution/ = full tree at commit; hygiene overlay on BOTH (Dockerfile, requirements.lock.txt, .dockerignore, ruff config) — ADDITIVE ONLY: never overwrite a file existing in the historical tree; never run ruff on historical trees; so input↔solution diff == the historical fix exactly. Verifier = tests added/changed by the commit (agent checks/rewrites for implementation-neutrality; BIG) else agent-authored tests. Old-commit dependency drift: reuse current lock; fallback re-lock at that commit (per-task image variant).

### 5.3 Excision funnel
- Select (code) from test_map + graph: covered by ≥2 tests, 8–80 lines, complexity ≥3, public.
- Screen (SMALL): "does the docstring spell out the implementation?" and "is it a trivial wrapper whose callers make it obvious?" → reject.
- Build (code): AST rewrite → replace body with `raise NotImplementedError("excised")`, keep signature + docstring. Flag `--excision-hard` (configurable) also strips docstring → contract lives only in tests + instruction. input/ = excised tree, solution/ = original. Verifier = existing covering tests (+ agent-added edge-case tests if < ~3 assertions touch the function). Fail-before is NotImplementedError inside behavior tests (valid reason; symbol still exists so no import error).

### 5.4 Net-new funnel
- BIG proposes candidates per module from .okf module pages + public API: "natural missing capability, testable in ≤5 tests, ≤60 lines"; prefer features touching an existing module (e.g. new glom spec type) over standalone utils. Code checks it doesn't already exist (grep/graph). Agent (BIG) implements solution/ + authors verifier tests. input/ = current repo. Target 2 validated (max 2 per user).

### 5.5 Validation harness (`python -m pipeline.validate <task_dir>`, pure code, container)
1. Fail-before: mount input/ + verifier/ → run verifier cmd → must FAIL → `evidence/fail_before.log`.
2. Right-reason classifier (STRICT): parse pytest junitxml/json-report per test; every failing test must fail via AssertionError / pytest.raises mismatch / NotImplementedError (excision) / exception raised inside function under test during a behavior test; ZERO collection errors, zero ImportError/ModuleNotFoundError/SyntaxError/AttributeError at import time, "collected 0 items", fixture-not-found, or test raising before calling repo code. Otherwise INVALID.
3. Pass-after: mount solution/ + verifier/ → must PASS → `evidence/pass_after.log`.
4. Determinism: repeat 1 and 3 N=3 times; verdicts identical → `evidence/determinism.json {runs:3, fail_before:[...], pass_after:[...]}`.
5. Collateral: run the repo's full suite on solution/ vs P1 baseline → no newly failing test → `evidence/collateral.json`. Run for excision too (uniformity).
6. `evidence/verdict.json {valid, checks, timestamp, image_digest}`; `tasks.json` validation_status is READ from verdict.json, never hand-typed.
- Harness ALWAYS re-copies the canonical `verifier/` into the workspace before judging (so a solving agent editing tests can't hack the verdict). Harness runs tasks in parallel (ThreadPoolExecutor over docker runs).
- Alternative-implementation evidence: static gate only — verifier tests may only import public symbols that exist in input/. (Rejected: agent-written alt solutions per task.)

### 5.6 task.json + instruction
- Fields: id, title, provenance {type, commit, parent, pr | excision target}, difficulty, difficulty_rationale, files_in_scope, instruction, verifier_cmd, image_digest.
- files_in_scope = files touched by solution diff + their direct importers/tests (from graph); multi-file fixes have all touched files in scope; never a single line pointer.
- Instruction = (1) goal, (2) observable behavior with 1–2 concrete input→output examples COPIED from verifier tests, (3) constraints, (4) how success is measured (verifier command).
- Authoring agent/call (BIG) is NOT shown the diff — it sees input/ tree, verifier tests, okf contract, behavior summary (structural leak prevention). Then gates: (a) code leak check: no line of solution diff (≥5 tokens) appears in instruction; no identifiers newly introduced by the diff are named unless in public API/tests; (b) reviewer (BIG) scores "solvable by transcription?" and "self-contained?"; regenerate on fail.
- Verifier visibility flag `--verifier-visibility visible|hidden`, default visible (matches PDF layout; hack-proof via harness re-copy). Hidden mode: only instruction in workspace; instruction must carry full contract.
- Difficulty: code computes features (files touched, functions touched, callers count, cross-module edges, diff size, similar-named functions nearby, test count) → BIG assigns label + 1–2 sentence justification that must cite ≥1 computed feature. Selection aims for spread.
- goldenSolution.md: diff (code) + "why correct" paragraph (LLM).
- Dockerfile + lock present inside input/ and solution/ (overlay); image digest recorded in task.json and verdict.json → task self-contained/re-buildable.

## 6. LLM usage map & tiers

Env: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL_BIG`, `LLM_MODEL_SMALL`; OpenAI python SDK; JSON-schema outputs via forced tool-call (more reliable on OSS than response_format), fenced-JSON-in-text accepted as fallback; validate every tool call against schema, return validation error to model, max 2 retries; exponential backoff on API errors; temperature 0; NO seed (pointless on OSS serving stacks; determinism comes from gates). Disk cache of prompt→response by hash BEHIND A FLAG (`--llm-cache`, default off). Prompt-cache friendliness: stable prefix first (system prompt → repo/module context → tool schemas), varying part last, byte-identical system prompt within a stage. Token accounting per stage → `output/audit/llm_usage.json`; `MAX_LLM_TOKENS_PER_REPO` cap. Per-step model override map in `config.py`.

Tier rule (user): classification/lookup → SMALL; authoring/coding/agents/review → BIG.

| # | Stage | Step | Mode | Tier |
|---|---|---|---|---|
| 1 | P1 pin | unknown import → PyPI name | direct JSON | SMALL |
| 2 | P1 docker | build/install repair loop | agent | BIG |
| 3 | P1 baseline | classify pre-existing failure env vs genuine | direct JSON | SMALL |
| 4 | P1 baseline | bounded fix of broken tests | agent | BIG |
| 5 | P1 test-gen | write tests for ranked functions | agent | BIG |
| 6 | P1 test-gen | retry with mutation feedback | agent (continuation) | BIG |
| 7 | P1 lint | fix non-auto-fixable lint errors (optional) | direct/agent | BIG |
| 8 | P2 okf | module purpose + public API summary | direct JSON | BIG |
| 9 | P2 okf | per-function contracts (batched per module) | direct JSON | BIG |
| 10 | P3 history | classify surviving commits | direct JSON batched | SMALL |
| 11 | P3 excision | screen candidates (docstring leak / trivial) | direct JSON batched | SMALL |
| 12 | P3 net-new | propose feature candidates | direct JSON | BIG |
| 13 | P3 build | author/repair verifier tests | agent | BIG |
| 14 | P3 build | neutrality check/rewrite of commit's own tests | direct/agent | BIG |
| 15 | P3 build | implement net-new solution | agent | BIG |
| 16 | P3 build | write instruction (no diff shown) | direct JSON | BIG |
| 17 | P3 build | leak/quality review of instruction | direct JSON | BIG |
| 18 | P3 build | difficulty label + justification | direct JSON | BIG |
| 19 | report | draft REPORT sections from audit data (optional) | direct | BIG |

Estimated glom volume: ~25–35 agent runs, ~100–150 direct calls.

## 7. Agent loop design (own, modular)
- `Agent(system_prompt, tools, model, max_turns=25, max_tokens_per_tool_result≈8k)`; OpenAI-compat function calling; goal given as user message; loop ends when model replies with NO tool calls — that final text is the summary (NO `done` tool). Tool errors returned as text to the model. Hard stop on turn/token cap. Result = {files_changed, summary, trajectory_path}. Every turn logged to transcripts/. Behind `AgentRunner` interface (pi swappable). ~200 lines.

## 8. Transcripts & audit
- `transcripts/pipeline/<stage>/<call_id>.json` auto-written for every LLM/agent call (prompt, tools, responses, outcome, tokens).
- `transcripts/dev/` = our own Claude Code session notes/prompts used to build the pipeline (this grill session summary + key prompts), curated by hand at end.
- `output/audit/agent_actions.jsonl`, `output/audit/llm_usage.json`.

## 9. Repo layout & entrypoint
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
  report/           # report_data.json → REPORT.md skeleton
tests/              # pipeline's own tests: fixtures/mini_pkg, fixtures/mini_pkg_notests, real docker/uv/git integration tests, LLM record/replay
output/<repo>/      # repo/, knowledge/ (repo_graph.json, .okf/, indexes), audit/, report_data.json, state.json
tasks/<repo>/<task_id>/ ; tasks.json
REPORT.md  HEURISTICS.md  README.md  transcripts/
```
- Resumability: each step writes artifacts + `state.json {step: {status, input_hash, finished_at}}`; skip if output exists and input hash unchanged; downstream reruns on change; `--force <step>`, `--fresh`. Graders see a full run on fresh clone.
- Scale hooks (the 4 agreed): per-repo output dirs; step resumability; parallel harness (ThreadPool); per-stage cost/time in report_data + `MAX_LLM_TOKENS_PER_REPO`. Everything else (job queue, image registry, triage, monorepos, human review sampling, non-Python) is written about only.

## 10. EcosystemAdapter interface
`detect(repo)->bool`, `python_version(repo)`, `synthesize_requirements(repo)->requirements.in`, `lock(repo)->lockfile`, `dockerfile(repo, lock)->str`, `test_command(repo)->str`, `test_framework_bootstrap(repo)`, `lint_and_format(repo)->report`, `parse_test_report(path)->{test_id: status, reason}`, `symbol_index(repo)->AST facts (functions, classes, imports, calls)`, `mutators()`. Everything else (agent loop, harness, funnels, okf writer, docker runner) is ecosystem-agnostic. JS adapter = implement these ~11 methods.

## 11. REPORT.md production
- Pipeline generates `output/<repo>/report_data.json` (detected/changed, quarantines, candidates+rejects, quotas, gates hit, LLM usage, per-stage timings) and a REPORT.md skeleton with tables filled from it; narrative sections (design/trade-offs, scale, gaps) hand-written by user + Claude at the end. Rejected: fully LLM-generated report.

## 12. Build order (agreed) — with rationale and real tests
Principle: build first what would force a redesign if it failed; reach one validated task end-to-end ASAP; pipeline's own tests are real integration tests (fixture repos, real docker/uv/git; LLM record/replay only).

0. Fixture repos: `tests/fixtures/mini_pkg/` (tiny Python lib, 3 modules, some tests, git history 5–6 commits incl. one bugfix + one dep change) and `mini_pkg_notests/`.
1. Foundation: skeleton, config.py, state/resume, run_in_container, LLM client (record/replay), agent loop. Test: real container run; agent solves toy task with replayed transcript.
2. P1 core: detect → synthesize → uv lock → Dockerfile → build → baseline (quarantine path). Test: mini_pkg & mini_pkg_notests build + baseline JSON as expected; then glom.
2b. Dry-run P1 on a second real repo, started here and rerun continuously.
3. P2 static: repo_graph, history_index, test_map, coverage, hotspots, graph self-verification. Test: mini_pkg graph == expected edges; test_map matches known coverage.
4. P3 excision + harness end-to-end. Test: excise known mini_pkg fn → VALID; broken verifier (import error) → INVALID; flaky test → determinism fail.
5. P3 history: funnel + build + agent verifiers + instruction + leak gate + difficulty. Test: mini_pkg bugfix commit surfaces; chore rejected with reason; task validates.
6. P1 test-gen + mutators. Test: mutators produce parseable code; weak test survives, strong test kills.
7. P2 okf + claim verifier. Test: frontmatter conforms; verifier catches planted false "raises".
8. P3 net-new. Test: e2e on mini_pkg with replayed LLM.
9. Lint/format, task selection & quotas, tasks.json, report_data → REPORT skeleton, transcripts curation, HEURISTICS.md. Test: selection respects quotas/diversity on synthetic candidates.
10. Full held-out dry-run on 2 repos (one small pure-Python lib with tests + history, e.g. boltons-sized or smaller; one with NO tests), fresh clone, twice, diff results.

Alternative reorders (documented for the record): test-gen earlier (after 2); okf before history; all-10-tasks-first (4→5→8); continuous held-out loop; strict P1→P2→P3 (argued against: harness/format problems found late).

## 13. Held-out dry-run repos
- Two shapes: (a) small pure-Python lib with tests + git history (boltons/attrs-sized or smaller); (b) one with NO tests to exercise bootstrap path. Concrete picks later.
