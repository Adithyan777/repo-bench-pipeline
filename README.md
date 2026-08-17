# AI Task Benchmark Pipeline

Repo-agnostic pipeline that takes a Python repository, makes it reproducible
(pinned, containerized, tested, lint-clean), emits a machine-readable knowledge
layer (`repo_graph.json` + `.okf/`), and mines 10 validated benchmark tasks
for AI coding agents.

Status: **P1 hygiene working end-to-end** (detect → pin/lock → Dockerfile → build →
baseline, resumable). Verified green on glom, toolz, minidump, and the fixtures.
Knowledge (P2) and tasks (P3) land from S3 on. See [`docs/PROGRESS.md`](docs/PROGRESS.md).

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

## Run the hygiene stage

```
./run.sh <repo_url_or_path> --stage hygiene [--verify-twice] [--fresh] [--force <step>]
# e.g. ./run.sh https://github.com/mahmoud/glom --stage hygiene --verify-twice
```

Produces `output/<repo>/`: a pinned + containerized clone under `repo/`, step records
under `hygiene/` (incl. the documented test command in `hygiene/test_command.txt`), and
`report_data.json`. The container test command is `python -m pytest -q` inside the built
`bench-<repo>` image.

## Generate and validate tasks

```
./run.sh <repo_url_or_path> --stage tasks   # excision + history funnels -> build -> validate -> tasks.json
```

Writes `tasks/<repo>/<task_id>/{task.json,input/,solution/,verifier/,goldenSolution.md,evidence/}`
(`exc-<module>-<name>` excision tasks, `hist-<sha7>` history tasks whose `input/`/`solution/`
are the trees at the parent/commit plus the hygiene overlay) and `tasks/<repo>/tasks.json`
(whose `validation_status` is read from each task's `evidence/verdict.json`). Every candidate
considered, with its reject reason, is in `output/<repo>/tasks/candidates.json` (functions)
and `output/<repo>/tasks/history_candidates.json` (commits).

### Validate a task standalone

A task folder is self-contained: `input/` carries the pinned `Dockerfile` + lock. To
re-judge one on a fresh machine:

```
docker build -t <image_tag> tasks/<repo>/<task_id>/input      # image_tag is in task.json
python -m pipeline.validate tasks/<repo>/<task_id> [more task dirs...]
# or let the harness build it: python -m pipeline.validate --set harness.build_image_if_missing=true <task_dir>
```

The harness runs, inside that image and on a fresh copy each time: fail-before on `input/`
(strict right-reason check), pass-after on `solution/`, `harness.determinism_runs` repeats,
the repo's full baseline suite on `solution/` (collateral), and a static gate on what the
verifier imports. It always re-copies the canonical `verifier/` over the workdir before
judging, and writes `evidence/{fail_before.log,pass_after.log,determinism.json,collateral.json,verdict.json}`.
Inside a workdir, `sh verifier/run.sh` (overlaid at the root: `sh run.sh`) runs the
verifier tests exactly as the harness does.

## Development

```
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements-dev.txt
.venv/bin/python -m pytest          # fast: unit + real uv/docker/git (needs Docker)
.venv/bin/python -m pytest -m slow  # multi-build container tests
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
