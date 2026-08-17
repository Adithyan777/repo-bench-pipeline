# pipeline/llm/

OpenAI-compatible LLM client for Baseten-served open-source models. Handles tiered model selection, schema-forced JSON extraction, usage accounting, and record/replay for tests.

## Files

| File | What it does |
|---|---|
| `client.py` | `LLMClient`: selects model and reasoning level per step (via `config.STEP_MODEL` / `MODEL_CAPS`). `chat()` for raw completions. `complete_json()` forces a tool call matching a JSON schema, validates client-side, retries on validation failure, falls back to fenced JSON in text. Exponential backoff on API errors. Usage accounting including reasoning tokens, written to `output/<repo>/audit/llm_usage.json`. A transcript per call is saved to `transcripts/pipeline/<stage>/`. Per-repo token budget enforced. Secrets (`LLM_BASE_URL`, `LLM_API_KEY`) come from env, never logged |
| `cassette.py` | Record/replay store. A cassette is a committed JSON fixture of one request+response pair, keyed by a stable hash of the canonicalized request. Tests run in `replay` mode and never hit the network |

## Models

- BIG: `moonshotai/Kimi-K2.6` (thinking on). Used for authoring, coding, agents, review.
- SMALL: `deepseek-ai/DeepSeek-V4-Flash-0731` (reasoning low). Used for classification, lookup.

Per-step assignment is in `config.STEP_MODEL`. Model-specific reasoning parameter translation (Kimi uses `enable_thinking`, DeepSeek uses `reasoning_effort`) is handled in `_reasoning_extra_body`.

## Modes

Set via `LLM_MODE` env var:

- `live` (default): real API calls
- `record`: real API calls, responses saved as cassettes
- `replay`: responses loaded from cassettes, no network

## Not here

- Cassette fixtures for tests: `tests/cassettes/`
- Cassette recording script: `scripts/record_cassettes.py`
