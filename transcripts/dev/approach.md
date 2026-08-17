# Development approach

How the pipeline was built, from design through implementation and review.


## Design phase

A single orchestrator model ran a structured design interview ("grill") that
produced the system design contract before any code was written. The contract
covered architecture (stages, steps, Docker model, agent loop, LLM tiers),
every threshold centralized in one config file with documentation, the task
format and harness rules, the report structure, and a decision log with
rejected alternatives.

The grill's output became `docs/DESIGN.md`, which every subsequent
implementation session re-read as its first step.


## Build order

Implementation was split into dependency-ordered steps. Each step ran in its
own coding-agent session.

1. **Foundations**: fixture repos with reproducible git history, package
   skeleton, resumable state, Docker runner + image build, LLM client
   (tiers, schema-forced JSON, retries, usage accounting, record/replay),
   agent loop + tools. Foundation tests.

2. **P1 core**: ecosystem detection, requirements synthesis, uv lock,
   Dockerfile/compose generation, image build with repair agent, baseline
   suite + quarantine.

3. **P2 static**: symbol index (AST), history index, test map, coverage,
   hotspots, repo graph, graph self-verification. No LLM in this layer.

4. **P3 excision + harness**: excision funnel, task builder, validation
   harness (fail-before, right-reason classifier, pass-after, determinism,
   collateral, static gate). First end-to-end validated task.

5. **P3 history**: history funnel, history task builder with verifier
   authoring, neutrality check + bounded rewrite, instruction authoring
   with leak gates, difficulty labelling.

6. **P1 test-gen**: AST mutation operators, mutation driver, generation loop
   with per-target mutation gate. Wired as a resumable hygiene step after
   baseline.

7. **P2 OKF**: OKF v0.2 bundle (static skeleton + BIG-authored contracts,
   cached by content hash), static claim verifier, `okf(path)` agent tool.

8. **Finalization**: lint step, final selection with quotas, report builder,
   transcripts curation, image label/prune, `.gitignore` for deliverables.

Net-new tasks (step 8 in the original plan) were cut by decision.

The ordering was chosen so each step could be tested against real outputs
from the previous one. The harness came before history tasks (step 4 before
5) so the first history task could be validated immediately.


## Session discipline

Each coding session started by re-reading the contract documents (`DESIGN.md`,
`config.py`, `PROGRESS.md`). The session did its step, updated the progress
log, and left changes staged for author review.

Closely related steps (e.g., P1 core parts) reused a warm session after
context compaction for faster iteration. The strongest available model was
used for the harness-heavy step (step 4), where correctness of the
right-reason classifier and evidence format mattered most.


## Review protocol

Every implementation step was reviewed by an independent reviewer subagent.
The review checked:
- Correctness against the contract (do the gates match the spec?).
- Security (can the agent escape the sandbox? Are secrets logged?).
- Test quality (do the tests exercise real paths or just mock everything?).
- Conformance (are thresholds in config.py? Are outputs in the right format?).

The orchestrator then verified the reviewer's findings against the actual
code and outputs, applied fixes, and re-verified. Only then was the step
committed. This caught several real bugs (see `review-rounds.md` for the
full list).


## Verification, not assumption

A recurring principle: verify against the code, do not assume the contract
is satisfied. Examples:
- `uv pip compile` output was parsed and checked, not assumed to match
  the documented format.
- Graph verification re-derives edges by an independent code path, not by
  re-running the same builder.
- The harness re-copies the canonical verifier into the workdir before
  judging, never trusting what is already there.
- Generated tests are gated by mutation kills, not coverage numbers.


## Final glom run

The committed artifacts come from a single `./run.sh <glom> --fresh` pass
run by the author. The run accumulated over an initial run (that hit an API
payment error mid-testgen and resumed) and a second `--fresh` run with a
larger history target. The second run's summary block
(`glom-run.log`) is the authoritative source for timings and token counts.
