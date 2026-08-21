# Held-out fresh-clone runs

Evidence from running the pipeline, unmodified, on two repos it had never
seen: `pytoolz/toolz` and `skelsec/minidump`. Both runs started from a fresh
clone of this repository on 2026-08-21, set up exactly as the README quick
start. The full account -- including the three generality bugs toolz exposed
and why minidump is honestly infeasible -- is in
[docs/gaps.md section 14](../docs/gaps.md).

Per repo:

| File | What it is |
|---|---|
| `run.log` | Complete console log (for toolz: all five attempts, including the failures that motivated each fix) |
| `REPORT.md`, `report_summary.json` | Generated report over the run's artifacts |
| `tasks.json` | Manifest of every task built, with validation and instruction status |
| `selection.json` (toolz only) | The selected 10 with quota accounting |
| `tasks/` | Task folders: the selected 10 for toolz; all 6 built for minidump (selection was infeasible, so none are "selected") |

Each task folder is self-contained and validates standalone:

```bash
python -m pipeline.validate heldout/toolz/tasks/<task_id>
```

Outcomes: toolz -- 12 tasks built, 12/12 VALID, 10 selected (4 excision +
6 history, 5 modules). minidump -- 6 built, 6/6 VALID, selection correctly
reported infeasible (sparse test coverage starves both funnels).
