# Review rounds

Each implementation step was reviewed by an independent reviewer subagent.
The author verified findings against the code and applied fixes. This is a
summary of what the reviews caught and how it was addressed.


## Foundations

Clean pass. 32 tests green with Docker running. Kimi-K2.6 function-calling
with thinking enabled worked correctly on the first attempt (no fallback to
GLM-5.2 needed).


## P1 core (hygiene)

The review caught a real safety bug. On toolz (a git-versioned repo), the
baseline agent-fix patched the library's own source code to make a version
test pass. This happened because the image lacked `git` and `.dockerignore`
excluded `.git`, so `toolz.__version__` resolved to `0.0.1`.

Fixes applied:
- Git-versioned repos now keep `.git` in the build context and install `git`
  in the image (environment fix, not a source edit).
- The agent-fix step is restricted to allowed path globs (tests, config,
  dependency files). Edits outside those paths are reverted and audited.
- Environment failures with no actionable missing dependency go to quarantine,
  never the agent.
- The pipeline's own `pipeline-requirements.in` never overwrites a repo's
  existing file of the same name.
- Input hashes now invalidate when test or import files change.

A second round confirmed all fixes. glom, toolz, minidump, and fixture repos
all passed, twice-identical.


## P2 static (knowledge)

Two review rounds hardened several areas:

- **Relative imports**: resolution was order-dependent. Fixed by two-pass
  module registration (register all modules first, then resolve).
- **Call re-resolution in the verifier**: the graph verifier was re-using
  the builder's call list instead of independently re-deriving via `ast.Call`.
  Fixed.
- **test_map precision**: test-to-function mapping used approximate nodeid
  matching. Fixed by writing an in-container pytest plugin that sets the
  coverage context to each test's exact nodeid.
- **Pipeline code fingerprint**: this was the most important catch. The
  resumability system skipped steps based on repo content alone, without
  hashing the pipeline's own code. A bug fix to the graph builder would
  leave stale artifacts in place. Fixed by including a code fingerprint in
  every step's input hash.

After fixes: precision 1.0 on all edge types, 0 mismatches, graph
byte-identical across runs. No LLM in this layer.


## P3 excision + harness

Fixes from the review:

- `verifier/run.sh` was using a relative cd. Fixed to `cd` then `exec`.
- The funnel now pre-gates candidates whose covering tests import private
  repo symbols, before any LLM spend.
- The strict right-reason classifier now enforces against the exact
  valid/invalid reason lists from config (previously it was more lenient).
- `harness.min_failing_tests` was added to reject tasks where the verifier
  has too few failing tests to be meaningful.
- Environment hashes (Dockerfile digest, lockfile hash) are recorded in the
  verdict for reproducibility.
- Screen decisions are persisted and reused (0-token reruns).

Result: glom 4/5 VALID, toolz 5/5 VALID.


## P3 history + instructions

Two review rounds on the history funnel and builder (5a), one on instructions
(5b).

5a fixes:
- PR-merge handling: only merges with a PR number in the subject are
  candidates. Non-PR merges (back-merges) are rejected because they diff
  against an arbitrary first parent.
- Revert detection via revert message and reverse `git patch-id`.
- Neutrality check + bounded rewrite for verifier tests that assert
  implementation details.
- Per-repo agent budgets, added after a 25-turn Kimi neutrality rewrite
  cost ~150k tokens.
- Agent turn cap reduced from 25 to 12 for BIG-tier agents.
- The getattr convention for new-symbol features (the author asked about
  this specifically).

5b fixes:
- Instruction leak gate refinements: `leak_api_names_only` (only gate
  API-like names, not locals/params) and `exempt_diff_lines_in_tests`
  (lines that appear in both the diff and the verifier tests are exempt,
  since the solver already sees them). These removed false positive
  rejections.

Result: 12 VALID tasks, 12 final instructions, easy 6 / medium 4 / hard 2.


## P1 test-gen + mutators

Fixes from the review:

- Generated tests are excluded from input hashes and ranking coverage, so
  reruns are 0-token and byte-identical.
- Kill definition tightened: a kill requires at least 1 test failure with
  collection intact (verified via the json-report, not just the exit code).
- Honest whole-file drops: when a module's tests kill zero mutants, the
  entire file is dropped (no partial-file surgery to inflate the count).
- Scripted-endpoint tests (no cassettes) for the container-driven agent,
  consistent with the verifier-agent test pattern.

Result on glom (`top_k=3`): 4 functions kept, `glom.core` dropped, 14/16
mutants killed.


## P2 OKF + claim verifier

Fixes from the review:

- Stamp `verified` only when at least one claim was actually checked (with
  a `checks` list in the evidence). Previously, all graph-derived pages
  were auto-verified.
- Callers and internal links are now reported as by-construction, not
  independently verified.
- Callees upgraded to a real `ast.Call` re-check instead of relying on the
  graph's caller list.
- `generated.at` pinned to the base commit date (not wall-clock) for
  byte-identical reruns.

Follow-up fix: source-module classification was including `docs/conf.py`
and example scripts as source modules. Fixed by adding `docs`, `examples`,
`scripts` to `graph.nonsource_dirs`. This reduced glom's source module count
from 12 to 11 and toolz from 20 to 16.

Result: glom 105/45 verified/draft (later 106/44 on the final run), callees
precision 1.0, raises ~0.75, side_effects ~0.87.


## Finalization

The finalization session (lint, selection, report, transcripts, housekeeping)
was reviewed as a single unit. The final live glom run was executed by the
author; all committed artifacts come from that single `--fresh` pass.
