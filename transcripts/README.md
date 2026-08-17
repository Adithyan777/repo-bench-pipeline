# transcripts/

LLM call transcripts and development session logs. The bulky per-call transcripts are gitignored; only the curated dev logs are committed.

## Layout

| Directory | Committed | What it contains |
|---|---|---|
| `pipeline/` | No | Auto-generated per-call LLM transcripts, one JSON file per `LLMClient.chat()` call. Organized by stage. Regenerated on every run |
| `agent/` | No | Agent trajectory files (full message lists per agent run), organized by step name |
| `dev/` | Yes | Curated development logs (see below) |

## dev/

| File | What it contains |
|---|---|
| [approach.md](dev/approach.md) | Development methodology: design phase, build order, session discipline, review protocol |
| [build-prompts.md](dev/build-prompts.md) | The shape of a session prompt with one representative example |
| [review-rounds.md](dev/review-rounds.md) | What reviews caught and how it was fixed, per implementation step |
