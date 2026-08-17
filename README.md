# AI Task Benchmark Pipeline

Repo-agnostic pipeline that takes a Python repository, makes it reproducible
(pinned, containerized, tested, lint-clean), emits a machine-readable knowledge
layer (`repo_graph.json` + `.okf/`), and mines 10 validated benchmark tasks
for AI coding agents.

Status: **all three pipelines working end-to-end.** P1 hygiene (detect → pin/lock →
Dockerfile → build → baseline → test-gen → lint, resumable), P2 knowledge
(`symbol_index → indexes → repo_graph → verify → okf`), and P3 tasks (excision +
history funnels → build → validate → instruct → manifest → **select** → report). A full
`./run.sh <repo> --fresh` produces the repo-root **`tasks.json`** (the final 10),
**`REPORT.md`**, the transformed clone, and the knowledge bundle. Skip flags:
`--no-testgen`, `--no-lint`, `--no-report-draft`. See [`docs/PROGRESS.md`](docs/PROGRESS.md).

## Documents

| Doc | What |
|---|---|
| [`docs/DESIGN.md`](docs/DESIGN.md) | Full system design: architecture, all three pipelines, harness, LLM usage, build order |
| [`docs/PROGRESS.md`](docs/PROGRESS.md) | Per-session handoff: step status and notes |
| [`HEURISTICS.md`](HEURISTICS.md) | **Every** heuristic, threshold, filter, flag and default in the pipeline. All values live in [`pipeline/config.py`](pipeline/config.py). |
| [`docs/HEURISTICS_REVIEW.md`](docs/HEURISTICS_REVIEW.md) | Compact review sheet: which config keys fired on glom, which never fired, which changed from the proposal |
| `REPORT.md` | Required assignment report (six sections; tables auto-filled, narrative drafted for the author to edit) |
| [`transcripts/dev/`](transcripts/dev/) | Curated dev session log, prompts, and review-round summaries |

## Run everything (fresh clone)

```bash
# 0. setup
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements-dev.txt
cp .env.example .env          # fill in LLM_BASE_URL + LLM_API_KEY

# 1. full pipeline: hygiene -> knowledge -> tasks -> select -> REPORT.md
./run.sh https://github.com/mahmoud/glom --fresh

# or per stage (resumable; --force <step> / --fresh override the cache)
./run.sh <repo_url_or_path> --stage hygiene [--verify-twice]
./run.sh <repo_url_or_path> --stage knowledge
./run.sh <repo_url_or_path> --stage tasks
```

Requires: Docker, Python 3.12, `uv`, and an OpenAI-compatible endpoint via
`LLM_BASE_URL` + `LLM_API_KEY` (see [`.env.example`](.env.example)). Models default to
open-source Kimi-K2.6 (BIG) / DeepSeek-V4-Flash (SMALL); override with
`LLM_MODEL_BIG` / `LLM_MODEL_SMALL`. All target-code execution happens inside the
pinned `bench-<repo>` container; LLM calls run from the host only.

Useful flags: `--no-testgen`, `--no-lint`, `--no-report-draft`, `--verify-twice`,
`--excision-hard`, `--verifier-visibility visible|hidden`, `--min-failing-tests N`,
`--set section.key=value`, and `--prune-images` (removes ONLY dangling images carrying
this pipeline's own build label — never your other images/containers).

## Deliverables (what a full run produces / what is committed)

| Path | Committed? |
|---|---|
| `tasks.json` (root) — the final 10 | yes |
| `tasks/<repo>/<id>/` — the 10 selected task folders (see `output/<repo>/tasks/selection.json`) | yes (the selected ones) |
| `REPORT.md`, `HEURISTICS.md`, `docs/`, `transcripts/dev/` | yes |
| `output/<repo>/knowledge/repo_graph.json` + `.okf/` | yes |
| `output/<repo>/repo/` (transformed clone), `report_data.json`, raw `transcripts/pipeline/` | no (regenerable; ignored) |

## Hygiene stage detail

Produces `output/<repo>/`: a pinned + containerized clone under `repo/` with labeled
pipeline commits (pin/containerize → baseline → generated tests → lint/format), step
records under `hygiene/`, and `report_data.json`. The container test command is
`python -m pytest -q` inside the built `bench-<repo>` image. The **lint** step writes a
`[tool.ruff]` config into pyproject.toml (creating a minimal one, without breaking a
setup.py install), runs `ruff check --fix` + `ruff format` inside that image, adds
`# noqa` for anything unfixable, then rebuilds the image and re-runs the suite twice —
if a formatting change regressed a baseline-passing test the tree is reverted (recorded
in `hygiene/lint.json`), so acceptance is never traded for cosmetics. Historical task
trees (built later from `git archive`) are never linted, so a history task's
`input/`→`solution/` diff stays the real historical change.

## Generate, validate, and select tasks

```
./run.sh <repo_url_or_path> --stage tasks
# funnels -> build -> validate -> instruct -> manifest -> select -> REPORT.md
```

The **select** step reads `tasks/<repo>/tasks.json` (every built task) and picks exactly
`selection.total_tasks` VALID + final tasks honoring the quotas (`min_history`,
`max_excision`, `max_netnew`, `min_distinct_modules`) with the difficulty spread as a
soft objective, then writes the repo-root **`tasks.json`** (the 10) and
`output/<repo>/tasks/selection.json` (why each eligible task was picked or not). An
infeasible quota is a hard error, never a silent short-fall. The **report** builder then
aggregates every stage's artifacts into `output/<repo>/report_summary.json` (leaving the
runner's per-stage `report_data.json` untouched) and renders `REPORT.md`; regenerate it
standalone with `python -m pipeline.report <repo> [--no-draft]`.

Writes `tasks/<repo>/<task_id>/{task.json,input/,solution/,verifier/,goldenSolution.md,evidence/}`
(`exc-<module>-<name>` excision tasks, `hist-<sha7>` history tasks whose `input/`/`solution/`
are the trees at the parent/commit plus the hygiene overlay) and `tasks/<repo>/tasks.json`
(whose `validation_status` is read from each task's `evidence/verdict.json`). Every candidate
considered, with its reject reason, is in `output/<repo>/tasks/candidates.json` (functions)
and `output/<repo>/tasks/history_candidates.json` (commits). VALID tasks get an LLM-authored
instruction (leak-gated and reviewed; the author never sees the diff), a "why correct" note in
`goldenSolution.md` and a difficulty label with cited features (`--verifier-visibility
visible|hidden` changes the instruction's wording); decisions persist in
`output/<repo>/tasks/instructions.json` so reruns cost no tokens.

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
