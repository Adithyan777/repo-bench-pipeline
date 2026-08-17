# tests/

Integration tests for the pipeline. These use real Docker, real uv, and real git. LLM calls go through cassettes (recorded responses) or scripted endpoints, never the live API.

## Test files

| File | What it covers |
|---|---|
| `test_state.py` | `state.py`: skip-if-unchanged, `--force`, `--fresh`, on-disk persistence |
| `test_docker.py` | Docker runner + image build against real containers |
| `test_llm.py` | LLM client: reasoning translation, schema-forced JSON + retry, usage accounting, replay mode |
| `test_agent.py` | Agent loop solves a toy task end-to-end with replayed LLM + real container |
| `test_fixtures.py` | The fixture repos (`mini_pkg`, `mini_pkg_notests`) build reproducibly and encode the intended git history |
| `test_hygiene.py` | P1 core: detection, pin/lock (real uv), Docker image build, baseline. Multi-build tests are `slow` |
| `test_knowledge.py` | P2: symbol index, repo graph, indexes, graph verification, graph-backed tools. Real AST/git/Docker, no LLM |
| `test_tasks.py` | P3: excision funnel + task builder + validation harness + `tasks.json`. Real Docker for the harness, SMALL-model screen replayed from cassettes |
| `test_history.py` | History funnel + task builder. Real fixture git history, real AST diffs, real Docker. Classify/neutrality replayed from `tasks_fixture` cassettes |
| `test_instruction.py` | Instruction authoring, leak gates, golden rationale, difficulty. Pure-code gates tested directly; author/reviewer loops use scripted endpoints |
| `test_testgen.py` | Test generation + mutation gate. Deterministic parts (ranking, mutators) run offline. Generation loop uses a scripted endpoint with real Docker/mutation runs |
| `test_lint.py` | Lint step: real hygiene run with lint enabled. Verifies repo ends ruff-clean, labeled commit exists, image rebuilds, suite stays green |
| `test_okf.py` | OKF bundle + claim verifier + `okf(path)` tool. Offline tests against a hand-built graph; one cassette-backed test through the full knowledge stage |
| `test_report.py` | Report builder: `report_data` completeness, REPORT.md sections, robustness to missing artifacts, cached draft path. No Docker; LLM is a tiny fake |
| `test_select.py` | Final selection: quotas, diversity, difficulty spread, determinism, infeasible cases. Pure, no Docker/LLM |
| `conftest.py` | Shared fixtures. Builds `mini_pkg` / `mini_pkg_notests` on demand. `docker_available` session fixture. `mini_env` runs a full hygiene+knowledge pass shared across task/harness/history tests |
| `_smoke.py` | Shared request builders used by both the cassette recorder and the tests. Guarantees recorder and replay produce byte-identical requests so cassette keys match |

## Subdirectories

| Directory | Purpose |
|---|---|
| `fixtures/` | Fixture repo builders (see `fixtures/README.md`) |
| `cassettes/` | Recorded LLM responses for replay (see `cassettes/README.md`) |

## Running

```
.venv/bin/python -m pytest              # all tests (Docker required for most)
.venv/bin/python -m pytest -m slow      # only slow (multi-build) tests
.venv/bin/python -m pytest -m docker    # only Docker-dependent tests
```

## Markers

- `docker`: requires a running Docker daemon
- `slow`: multi-build or long-running

## Not here

- Cassette recording: `scripts/record_cassettes.py`
- Pipeline source: `pipeline/`
