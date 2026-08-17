# AI task benchmark pipeline

Takes a Python repository, pins its dependencies, containerizes it, runs and
extends its test suite, builds a machine-readable knowledge layer, and mines
10 validated benchmark tasks for AI coding agents.

```
./run.sh https://github.com/mahmoud/glom
```

Three stages run in sequence: **hygiene** (pin, containerize, baseline, test-gen,
lint), **knowledge** (repo graph, coverage indexes, OKF bundle), and **tasks**
(excision + history funnels, build, validate, instruct, select). Each step is
resumable. All target-code execution happens inside a throwaway Docker container
with no network access. LLM decisions are cached by content hash, so reruns on
an unchanged repo cost zero tokens.


## Results on glom

| Metric | Value |
|---|---|
| Wall clock (full `--fresh` run) | ~13 min |
| LLM tokens | 779,614 total (big 762,657 / small 16,957) |
| Baseline tests | 202 passing, 0 quarantined |
| Generated tests kept | 4 functions across 2 modules (14/16 mutants killed) |
| Suite after test-gen | 240 tests passing (verify-twice identical) |
| Graph | 378 nodes, 4,612 edges; verification precision 1.0 all edge types |
| OKF | 164 pages (106 verified / 44 draft); conformant |
| Tasks built | 14 (5 excision, 9 history); 13 VALID |
| Selected 10 | 4 excision + 6 history, 4 distinct modules |
| Difficulty spread | easy 5, medium 4, hard 1 |


## Quick start

Prerequisites: Docker (running), Python 3.12, [uv](https://docs.astral.sh/uv/),
an OpenAI-compatible LLM endpoint.

```bash
# clone and set up
git clone <this-repo> && cd lh2ai-assignment
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements-dev.txt
cp .env.example .env          # fill in LLM_BASE_URL + LLM_API_KEY

# full pipeline
./run.sh https://github.com/mahmoud/glom

# or one stage at a time (resumable)
./run.sh <repo> --stage hygiene
./run.sh <repo> --stage knowledge
./run.sh <repo> --stage tasks
```

Models default to open-source Kimi-K2.6 (BIG tier) and DeepSeek-V4-Flash
(SMALL tier) via Baseten. Override with `LLM_MODEL_BIG` / `LLM_MODEL_SMALL`
in `.env`.


## What happens per stage

**Hygiene** (detect, pin, dockerfile, compose, build, baseline, testgen, lint):
detects packaging style and Python version, pins all dependencies with hashes
via `uv pip compile`, writes a digest-pinned Dockerfile, builds a `bench-<repo>`
image, runs the baseline suite in-container, generates tests for under-covered
functions (mutation-gated), and runs ruff lint/format (reverted if any test
regresses). Outputs: `output/<repo>/repo/` (transformed clone with labeled
commits), `output/<repo>/hygiene/*.json`.

**Knowledge** (symbol_index, indexes, graph, verify, okf): builds a
deterministic repo graph from AST analysis (nodes for modules/classes/functions,
edges for imports/calls/contains/inherits/tested_by, each with file+line
evidence), coverage indexes and test map, history index, hotspots, and an
OKF v0.2 knowledge bundle with LLM-authored function contracts. Outputs:
`output/<repo>/knowledge/repo_graph.json`, `.okf/`, verification files.

**Tasks** (excision_funnel, build_excision, history_funnel, build_history,
validate, instruct, manifest, select): funnels candidate functions and commits,
builds task folders (`input/`, `solution/`, `verifier/`, evidence), validates
each (fail-before with right-reason check, pass-after, determinism, collateral),
writes LLM-authored instructions (leak-gated, reviewer-checked), labels
difficulty, and selects exactly 10 under hard quotas. Outputs:
`tasks/<repo>/<task_id>/`, `tasks/<repo>/tasks.json`, root `tasks.json`,
`output/<repo>/REPORT.md`.


## CLI flags

| Flag | Effect |
|---|---|
| `--stage hygiene\|knowledge\|tasks\|all` | Run one stage (default: all) |
| `--fresh` | Ignore all cached state, rerun everything |
| `--force STEP` | Rerun a specific step (repeatable) |
| `--set section.key=value` | Override a config value (repeatable) |
| `--no-testgen` | Skip test generation |
| `--no-lint` | Skip lint/format |
| `--no-report-draft` | Skip the LLM narrative draft in REPORT.md |
| `--verify-twice` | Run the test suite a second time after hygiene |
| `--excision-hard` | Strip docstrings from excised functions |
| `--verifier-visibility visible\|hidden` | Solver sees verifier tests or not |
| `--min-failing-tests N` | Minimum failing tests for a valid fail-before |
| `--llm-cache` | Enable prompt-to-response disk cache |
| `--prune-images` | Remove dangling images with this pipeline's label |
| `--quiet` | Stage-level progress only |


## Operational knobs (via `--set`)

These are the most commonly tuned values. The full reference with defaults,
rationale, and glom observations is in [docs/configuration.md](docs/configuration.md).

| Key | Default | What it controls |
|---|---|---|
| `testgen.agent_max_turns` | 12 | Turns per test-gen agent run |
| `testgen.max_agent_runs_per_repo` | 10 | Total agent runs (write + retry) across all modules |
| `testgen.top_k_modules` | 5 | Modules ranked for test generation |
| `history.build_target` | 10 | History tasks to build (headroom for selection) |
| `history.shortlist_size` | 20 | History candidates shortlisted after classify |
| `history.max_agent_runs_per_repo` | 6 | Verifier/rewrite agent runs per repo |
| `history.agent_max_turns` | 12 | Turns per history agent run |
| `harness.min_failing_tests` | 1 | Minimum failing tests in fail-before |
| `harness.determinism_runs` | 3 | Repeat count for determinism check |
| `selection.total_tasks` | 10 | Tasks to select |
| `selection.min_history` | 4 | Minimum history tasks in the final 10 |
| `selection.max_excision` | 4 | Maximum excision tasks |
| `selection.min_distinct_modules` | 4 | Minimum distinct modules across the 10 |
| `llm.max_tokens_per_repo` | 5,000,000 | Per-repo token budget (abort on exceed) |
| `okf.max_function_pages` | 150 | Cap on individual function pages in the OKF bundle |
| `lint.format` | true | Whether ruff format runs alongside ruff check |

Example: `./run.sh <repo> --set testgen.top_k_modules=3 --set history.build_target=15`


## Validate a task standalone

Each task folder is self-contained. To re-validate on a fresh machine:

```bash
# build the image from the task's own Dockerfile
docker build -t <image_tag> tasks/<repo>/<task_id>/input

# run the harness
python -m pipeline.validate tasks/<repo>/<task_id>
```

The harness runs fail-before (with right-reason classification), pass-after,
determinism (3x by default), and collateral checks. It re-copies the canonical
`verifier/` into the workdir before each run. Results go to
`<task>/evidence/verdict.json`.


## Pipeline tests

```bash
.venv/bin/python -m pytest              # default: skips slow
.venv/bin/python -m pytest -m slow      # multi-build container tests
.venv/bin/ruff check .
```

Tests use real Docker, real uv, real git, and real fixture repos built with
reproducible history. LLM calls are replayed from committed cassettes (no
network, no tokens). Last full run: 199 passed, 1 skipped, 3 deselected;
slow: 3 passed; ruff clean.


## Deliverables map

| Path | Committed | Description |
|---|---|---|
| `pipeline/` | yes | Pipeline source |
| `tests/` | yes | Integration tests, fixtures, cassettes |
| `docs/` | yes | Architecture, pipeline docs, configuration, decisions, gaps |
| `transcripts/dev/` | yes | Development methodology, prompts, review rounds |
| `tasks.json` (root) | yes | The final 10 selected tasks |
| `tasks/glom/<id>/` | yes | The 10 selected task folders |
| `tasks/glom/tasks.json` | yes | Full manifest of all built tasks |
| `output/glom/knowledge/repo_graph.json` | yes | Static knowledge graph |
| `output/glom/knowledge/.okf/` | yes | OKF v0.2 knowledge bundle |
| `output/glom/report_summary.json` | yes | Aggregated run data |
| `REPORT.md` | yes | Assignment report (six sections) |
| `output/glom/repo/` | no | Transformed clone (regenerable) |
| `output/glom/hygiene/`, `tasks/`, `audit/` | no | Step records, caches (regenerable) |
| `transcripts/pipeline/`, `transcripts/agent/` | no | Per-call LLM transcripts (regenerable) |


## Documentation index

| Document | Contents |
|---|---|
| [docs/architecture.md](docs/architecture.md) | Stages, resumability, Docker model, agent loop, LLM client |
| [docs/pipeline-1-hygiene.md](docs/pipeline-1-hygiene.md) | Hygiene stage: each step, edge cases, glom outcomes |
| [docs/pipeline-2-knowledge.md](docs/pipeline-2-knowledge.md) | Knowledge stage: graph, indexes, OKF, verification |
| [docs/pipeline-3-tasks.md](docs/pipeline-3-tasks.md) | Tasks stage: funnels, harness rules, instructions, selection |
| [docs/configuration.md](docs/configuration.md) | Every config key with default, meaning, and rationale |
| [docs/decisions.md](docs/decisions.md) | Design decisions with rejected alternatives |
| [docs/gaps.md](docs/gaps.md) | Known gaps with evidence and next steps |
| [REPORT.md](REPORT.md) | Assignment report |


## Folder READMEs

Each subfolder has its own README describing its files and purpose:
`pipeline/`, `pipeline/*/`, `tests/`, `tests/fixtures/`, `tests/cassettes/`,
`scripts/`, `transcripts/`, `tasks/`, `output/`.
