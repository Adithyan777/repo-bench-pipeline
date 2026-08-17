# tests/cassettes/

Recorded LLM request/response pairs for deterministic test replay. Tests run with `LLM_MODE=replay` and load responses from here instead of calling the live API.

## Layout

Each subdirectory corresponds to a recording stage. Files are named by the sha256 hash of the canonicalized request.

| Directory | What it records |
|---|---|
| `llm_smoke/` | Direct schema-forced JSON call (SMALL tier) |
| `agent_toy/` | Agent loop solving a toy task |
| `pin_alias/` | Import-to-PyPI alias mapping |
| `baseline_classify/` | Baseline failure classification |
| `pin_reask/` | Schema retry (validation failure -> re-ask) |
| `tasks_fixture/` | Full tasks stage on `mini_pkg`: excision screen, history classify, neutrality check, instruction, difficulty |
| `okf_fixture/` | OKF module-purpose and function-contract calls |

## Format

Each `.json` file contains:

```json
{
  "request": { ... },
  "response": { ... }
}
```

The request is the canonicalized (but not secret-bearing) request body. The response is the full `ChatCompletion` object as returned by the OpenAI SDK.

## Recording new cassettes

```
LLM_MODE=record .venv/bin/python scripts/record_cassettes.py
LLM_MODE=record .venv/bin/python scripts/record_cassettes.py --rerecord pin_alias
```

See `scripts/record_cassettes.py` for details.
