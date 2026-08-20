# transcripts/

LLM call transcripts, the console log of the glom run, and development session logs. All of it is committed as evidence.

## Layout

| Path | Committed | What it contains |
|---|---|---|
| `pipeline/` | Yes | Auto-generated per-call LLM transcripts (236 files), one JSON file per `LLMClient.chat()` call. Organized by stage. Regenerated on every run |
| `agent/` | Yes | Agent trajectory files (12 files: full message lists per agent run), organized by step name |
| `glom-console.log` | Yes | Console log of the glom run: per-step durations, the `[summary]` blocks, and the wall-clock record |
| `dev/` | Yes | Curated development logs (see below) |

## dev/

| File | What it contains |
|---|---|
| [approach.md](dev/approach.md) | Development methodology: design phase, build order, session discipline, review protocol |
| [build-prompts.md](dev/build-prompts.md) | The shape of a session prompt with one representative example |
| [review-rounds.md](dev/review-rounds.md) | What reviews caught and how it was fixed, per implementation step |
