# Build prompts

Each implementation session received a prompt with a consistent structure.
This document describes the shape of that prompt and includes one
representative example (the finalization session).


## Prompt shape

Every session prompt followed this template:

1. **Role and context**: "You are implementing step N of the AI Task Benchmark
   pipeline. Steps 1 through N-1 are committed."

2. **Contract references**: "Read `docs/DESIGN.md`, `HEURISTICS.md`,
   `pipeline/config.py`, and `docs/PROGRESS.md` before starting."

3. **Scope**: a numbered list of what this session builds, with references to
   the specific DESIGN.md sections and config keys involved. Each item names
   the module to create or modify, the inputs it reads, the outputs it writes,
   and how it wires into the existing pipeline.

4. **Rules**: a short list of invariants.
   - Verify, do not assume.
   - All target-code execution via `run_in_container`.
   - LLM calls from the host only.
   - Never print or commit secrets.
   - Every threshold goes into `config.py` with a documented row in
     `HEURISTICS.md`.
   - Real integration tests only (real Docker, real uv, real git).
   - Do not commit; leave changes staged for author review.
   - Stop and ask if blocked on an author decision.

5. **What the next session needs to know**: explicit notes about where outputs
   land, what APIs the next step should call, and any known open issues.


## Representative example: finalization session

The finalization session (the last implementation step) received this scope
summary:

> Scope: (1) LINT/FORMAT (P1, DESIGN 3.7): `PythonAdapter.lint_and_format`
> with ruff `--fix` + `ruff format` on `output/<repo>/repo`, `[tool.ruff]`
> in pyproject, noqa for unfixable, `hygiene/lint.json`; wired as hygiene
> step `lint` after testgen (resumable, `--no-lint`); never touch historical
> task trees. (2) FINAL SELECTION (DESIGN 5.1/5.6): `tasks/select.py`: pick
> exactly `selection.total_tasks` VALID+final tasks honoring quotas +
> difficulty spread; write root `tasks.json` + `selection.json`. (3) REPORT:
> `report/build.py` producing `report_data.json` + `REPORT.md` (six required
> sections; tables auto-filled; narrative drafted + marked for author).
> (4) TRANSCRIPTS: `transcripts/dev/`. (5) HOUSEKEEPING: image label/prune
> by label; `.gitignore` flip for the deliverable set; README current; remove
> dead flags.

This is representative of the level of specificity in each session prompt:
concrete module paths, config keys, output locations, and explicit constraints
(e.g., "never touch historical task trees"). The rules section was identical
across all sessions.
