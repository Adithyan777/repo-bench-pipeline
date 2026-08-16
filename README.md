# AI Task Benchmark Pipeline

Repo-agnostic pipeline that takes a Python repository, makes it reproducible
(pinned, containerized, tested, lint-clean), emits a machine-readable knowledge
layer (`repo_graph.json` + `.okf/`), and mines 10 validated benchmark tasks
for AI coding agents.

Status: **design complete, implementation not started.**

## Documents

| Doc | What |
|---|---|
| [`docs/DESIGN.md`](docs/DESIGN.md) | Full system design: architecture, all three pipelines, harness, LLM usage, build order |
| [`HEURISTICS.md`](HEURISTICS.md) | **Every** heuristic, threshold, filter, flag and default in the pipeline. All values live in [`pipeline/config.py`](pipeline/config.py). Reviewed with the author before submission. |
| `REPORT.md` | (to be written) required assignment report |
| `transcripts/` | (to be curated) pipeline LLM transcripts + dev session prompts |

## Entry point (planned)

```
./run.sh <repo_url_or_path> [--stage hygiene|knowledge|tasks|all] [--force <step>] [--fresh]
```

Requires: Docker, Python 3.12, `uv`, and env vars `LLM_BASE_URL`, `LLM_API_KEY`,
`LLM_MODEL_BIG`, `LLM_MODEL_SMALL` (OpenAI-compatible endpoint, open-source models).

## Assignment

See `assignment_sde_ benchmarking_problem_statement.pdf`. Sample target repo:
https://github.com/mahmoud/glom (`github-repo-url.txt`).
