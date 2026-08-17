# Development session prompts

The pipeline was built across sequential implementation sessions (S1–S7 + a
finalization session, "B"), each handed off via `docs/PROGRESS.md`. Every session
began by re-reading `docs/DESIGN.md`, `HEURISTICS.md`, `pipeline/config.py`, and
`docs/PROGRESS.md`, did one build-order step, updated its PROGRESS row, and left the
changes for author review.

The verbatim design grill that produced the whole design lives in
[`design-session-log.md`](design-session-log.md). The per-session review-round
outcomes are summarized in [`review-rounds.md`](review-rounds.md). Below are the
session scopes (S1–S7 reconstructed from the PROGRESS handoff; Session B verbatim).

## S1 — Foundations (build-order steps 0+1)
Fixture repos (`tests/fixtures/mini_pkg`, `mini_pkg_notests`), package skeleton,
resumable `state`, `docker.run_in_container` + image build, LLM client (big/small,
reasoning per tier, schema-forced JSON, retries, usage log, record/replay), agent
loop + tools, foundation tests.

## S2 — P1 core (steps 2+2b)
Detect → synthesize requirements → uv lock → Dockerfile/compose → build → baseline +
quarantine; `ecosystems/python.py`; real runs on glom, then toolz + minidump.

## S3 — P2 static (step 3)
`repo_graph.json`, `history_index`, `test_map`, `coverage`, `hotspots`, graph
self-verification. Ordering `symbol_index → indexes → graph → verify`. No LLM.

## S4 — P3 excision + harness (step 4)
Excision funnel + validation harness end-to-end → first VALID task; task folder
format, evidence, verdict, `tasks.json` writer.

## S5 — P3 history (step 5)
History-derived funnel + task-builder agent (verifier authoring/neutrality,
instruction + leak gates, difficulty). 5a: funnel + builder. 5b: instruction, leak
gates, difficulty.

## S6 — P1 test-gen + mutators (step 6)
AST mutation operators + ecosystem-agnostic mutation driver + generation loop with a
per-target mutation gate; wired as a resumable hygiene step after baseline.

## S7 — P2 OKF + claim verifier (step 7)
OKF v0.2 `.okf/` bundle (static skeleton + BIG-authored purpose/contracts, cached by
hash), static claim verifier, `okf(path)` agent tool. Plus a source-module
classification fix (`docs/conf.py` and example scripts no longer indexed as source).

## Session B — Finalization (build-order step 9) — verbatim

> You are implementing Session B (build-order step 9, finalization) of the AI Task
> Benchmark pipeline. S1–S7 are committed. Net-new tasks (S8) are CUT by decision —
> do not build them. This session turns the pipeline's outputs into the submission.
>
> Scope: (1) LINT/FORMAT (P1, DESIGN 3.7) — `PythonAdapter.lint_and_format` → ruff
> `--fix` + `ruff format` on `output/<repo>/repo`, `[tool.ruff]` in pyproject, noqa
> for unfixable, `hygiene/lint.json`; wired as hygiene step `lint` after testgen
> (resumable, `--no-lint`); never touch historical task trees. (2) FINAL SELECTION
> (DESIGN 5.1/5.6) — `tasks/select.py`: pick exactly `selection.total_tasks`
> VALID+final tasks honoring quotas + difficulty spread; write root `tasks.json` +
> `selection.json`; `--select` as the final tasks step. (3) REPORT — `report/build.py`
> → `report_data.json` + `REPORT.md` (six required sections; tables auto-filled;
> narrative drafted + marked for author). (4) TRANSCRIPTS — `transcripts/dev/`.
> (5) HOUSEKEEPING — image label/prune by label; `.gitignore` flip for the deliverable
> set; README current; remove dead flags. (6) FINAL GLOM RUN — `./run.sh <glom>
> --fresh` end-to-end (run by the author). (7) TESTS. (8) DOCS.
>
> RULES: verify don't assume; ALL target-code execution via `run_in_container`; LLM
> from host only; never print/commit secrets; do NOT commit — leave staged; stop and
> ask if blocked on an author decision.

_(The full Session B prompt is in the author's records; the paragraph above is the
scope summary carried into the work.)_
