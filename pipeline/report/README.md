# pipeline/report/

Aggregates artifacts from all stages into `report_summary.json` and renders `REPORT.md`.

## Files

| File | What it does |
|---|---|
| `build.py` | `collect()` walks `output/<repo>/` (including the runner's `report_data.json`) and assembles `report_summary.json`. `render()` turns that into a six-section `REPORT.md` with auto-filled tables. Narrative paragraphs are optionally drafted by a BIG model call (cached by content hash) and marked `AUTHOR` for a human to finish. Missing artifacts omit their rows rather than inventing data |
| `__main__.py` | Standalone entry point: `python -m pipeline.report <repo> [--no-draft]`. Reads from `output/<repo>/`, writes `report_summary.json` + `REPORT.md` |

## Outputs

- `output/<repo>/report_summary.json`
- `REPORT.md` at the repo root

## How it's used

Called automatically at the end of the tasks stage. Can also be run standalone to regenerate the report without rerunning the pipeline.
