# pipeline/

The benchmark pipeline. Takes a repo URL or local path, runs three stages (hygiene, knowledge, tasks), and produces 10 validated benchmark tasks plus a report.

Entry point: `./run.sh <repo> [--stage hygiene|knowledge|tasks|all]`, which calls `python -m pipeline.cli`.

## Modules

| File | What it does |
|---|---|
| `cli.py` | Argument parsing, stage dispatch, config overrides (`--set section.key=value`), `--force`/`--fresh` flags |
| `config.py` | All thresholds, flags, model tiers, and defaults. Documented in `HEURISTICS.md` at the repo root |
| `state.py` | Resumability: per-step status + input hashing in `output/<repo>/state.json`. Steps skip when inputs and code fingerprint are unchanged |
| `log.py` | Console progress lines (`HH:MM:SS [stage/step] msg`); `--quiet` keeps stage-level lines only |
| `validate.py` | Standalone harness runner: `python -m pipeline.validate <task_dir> [...]`. Exits 0 only if every task is VALID |
| `__init__.py` | Package docstring only |

## Subpackages

| Package | Purpose |
|---|---|
| `agent/` | Agent loop (OpenAI function calling) and sandboxed tool definitions |
| `docker/` | Container execution (network-isolated `docker run`) and image build with digest-pinned bases |
| `ecosystems/` | `EcosystemAdapter` interface and the Python implementation. All language-specific logic lives here |
| `hygiene/` | Stage 1: detect ecosystem, pin deps, build image, run baseline suite, generate tests, lint |
| `knowledge/` | Stage 2: repo graph, coverage/test map, history index, hotspots, OKF knowledge bundle |
| `llm/` | OpenAI-compatible LLM client with tiered models, schema-forced JSON, usage accounting, record/replay cassettes |
| `report/` | Aggregates all stage artifacts into `report_summary.json` and `REPORT.md` |
| `tasks/` | Stage 3: candidate funnels (excision + history), task builders, validation harness, instruction authoring, difficulty labelling, selection |

## How it's used

```
./run.sh https://github.com/mahmoud/glom          # all stages
./run.sh ./local-repo --stage hygiene --fresh      # one stage, ignore cache
python -m pipeline.validate tasks/glom/hist-abc1234
```

## Console output

Plain stdout, one line per event, no dependencies. Every step prints `start`, then
`done in <s> (<n> LLM tokens)` (tokens spent by that step) or `skipped (unchanged)`;
inner events (build repair attempts, baseline quarantine, per-module testgen, per-task
build/validate/instruct verdicts, selection) print between them. The run ends with a
`[summary/...]` block: per-stage step durations, tokens by model tier, VALID count, the
selected task ids. `--quiet` keeps only stage boundaries and the summary.

```
12:01:15 [hygiene/build] done in 12.2s (0 LLM tokens) outcome=built attempts=0
12:41:30 [tasks/validate] hist-4a8f5e0 VALID (fail-before 1, pass-after 1, det 3/3)
```

## Not here

- Thresholds and knob docs: `HEURISTICS.md` (repo root)
- Design contract: `docs/DESIGN.md`
- Test suite: `tests/`
