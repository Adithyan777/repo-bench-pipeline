# pipeline/hygiene/

Stage 1 (P1): bring the target repo to a reproducible, green-suite baseline inside a pinned Docker image.

## Files

| File | What it does |
|---|---|
| `runner.py` | Chains the steps in order: detect, pin, dockerfile, compose, build, baseline, testgen, lint. Each step is resumable via `state.py`. Pipeline edits are committed as labeled git commits; the original HEAD is recorded so later stages mine only original history |
| `context.py` | `HygieneContext`: shared run context holding paths, config, adapter, LLM client, audit helpers. `build_context` provisions the run directory (`output/<repo>/`) and clones the repo |
| `detect.py` | Ecosystem + packaging-style + Python-version detection |
| `pin.py` | Synthesizes `requirements.in` from the detected manifest, then produces a fully pinned lock via `uv lock`. No-manifest repos get deps from an AST import scan with an optional LLM fallback for import-to-PyPI name mapping |
| `dockerfile.py` | Renders the digest-pinned Dockerfile and `.dockerignore` into the repo clone |
| `compose.py` | Detects service dependencies (postgres, redis) from imports, `.env.example` URLs, and existing compose files. Writes a `docker-compose.yml` template for supported services |
| `build.py` | Builds the repo image. On failure, runs a bounded LLM repair agent (read_file/grep/write_file, no `run` since no image exists yet) that edits the Dockerfile or requirements, then rebuilds |
| `baseline.py` | Runs the test suite in-container. Classifies failures as env vs genuine. Env failures with a missing dep get one automatic fix (add dep, re-lock, rebuild). Genuine failures get one bounded agent fix (restricted to test/config/dep files). Remaining failures are quarantined. Never deletes a test or fakes a pass |
| `testgen.py` | Generates tests for under-covered functions. A BIG agent writes tests, then each target goes through a mutation gate: tests must pass on real code and kill a minimum fraction of injected mutants. Tests that prove nothing are dropped |
| `mutate.py` | Mutation driver: given a function's line span and the adapter's AST mutators, produces whole-file mutants. Deterministic operator interleaving, no randomness |
| `lint.py` | Runs ruff check/format in-container on a throwaway copy. Syncs changes back, rebuilds the image, and reruns the suite. If a formatting change regresses a test, the tree is reverted |

## Outputs

Written to `output/<repo>/hygiene/`:

- `detect.json`, `pin.json`, `dockerfile.json`, `compose.json`, `build.json`, `baseline.json`, `testgen.json` (step records)
- `test_command.txt`
- `pipeline_base.json`
- `testgen_decisions.json`, `testgen_targets.json`

The working repo clone lives at `output/<repo>/repo/`.

## Not here

- Ecosystem-specific logic (adapter methods): `pipeline/ecosystems/`
- Knowledge-layer artifacts: `pipeline/knowledge/`
