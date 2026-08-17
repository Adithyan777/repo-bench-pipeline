# AI Task Benchmark Pipeline

Repo-agnostic pipeline that takes a Python repository, makes it reproducible
(pinned, containerized, tested, lint-clean), emits a machine-readable knowledge
layer (`repo_graph.json` + `.okf/`), and mines 10 validated benchmark tasks
for AI coding agents.

Status: **S1 foundation in place** (fixtures, package skeleton, resumable state,
Docker runner + image build, LLM client with record/replay, agent loop). Pipeline
stages (P1–P3) land from S2 on. See [`docs/PROGRESS.md`](docs/PROGRESS.md).

## Documents

| Doc | What |
|---|---|
| [`docs/DESIGN.md`](docs/DESIGN.md) | Full system design: architecture, all three pipelines, harness, LLM usage, build order |
| [`docs/PROGRESS.md`](docs/PROGRESS.md) | Per-session handoff: step status and notes |
| [`HEURISTICS.md`](HEURISTICS.md) | **Every** heuristic, threshold, filter, flag and default in the pipeline. All values live in [`pipeline/config.py`](pipeline/config.py). Reviewed with the author before submission. |
| `REPORT.md` | (to be written) required assignment report |
| `transcripts/` | (to be curated) pipeline LLM transcripts + dev session prompts |

## Entry point (planned)

```
./run.sh <repo_url_or_path> [--stage hygiene|knowledge|tasks|all] [--force <step>] [--fresh]
```

Requires: Docker, Python 3.12, `uv`, and env vars `LLM_BASE_URL`, `LLM_API_KEY`,
`LLM_MODEL_BIG`, `LLM_MODEL_SMALL` (OpenAI-compatible endpoint, open-source models).

## Development

```
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements-dev.txt
.venv/bin/python -m pytest          # single test command; needs Docker running
```

Tests run against real fixture repos, real Docker, and real git. LLM calls are
replayed from committed cassettes (`tests/cassettes/`) — no network, no tokens. To
(re)record cassettes once against the live endpoint (needs `.env` + Docker):

```
LLM_MODE=record .venv/bin/python scripts/record_cassettes.py
```

## Assignment

See `assignment_sde_ benchmarking_problem_statement.pdf`. Sample target repo:
https://github.com/mahmoud/glom (`github-repo-url.txt`).
