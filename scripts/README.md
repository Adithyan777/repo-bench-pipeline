# scripts/

Utility scripts for development and test infrastructure.

## Files

| File | What it does |
|---|---|
| `record_cassettes.py` | Records LLM cassettes against the real API endpoint. Run with `LLM_MODE=record .venv/bin/python scripts/record_cassettes.py`. Skips stages that already have cassettes unless `--rerecord <stage>` (or `--rerecord all`) is passed. Requires `.env` with `LLM_BASE_URL` and `LLM_API_KEY`, plus a running Docker daemon for the tasks stage |

## Not a tool

| Path | What it is |
|---|---|
| `_record_workdir/` | Scratch directory left behind by the agent cassette recording step. Not part of any tool or workflow. Gitignored |
