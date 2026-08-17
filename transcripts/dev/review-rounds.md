# Review-round summaries

Each implementation session ended in one or more author review rounds (GO /
GO-with-fixes / NO-GO). This is a curated digest; the full per-round detail lives in
`docs/PROGRESS.md` under each `### S<n>` heading.

## S1 — foundation
GO. 32 tests green with Docker live; cassettes recorded (1049 tokens). Kimi-K2.6
tool-calling-with-thinking day-1 check PASSED (no GLM fallback needed).

## S2 — P1 core
NO-GO → fixed. Round 2 caught a real safety bug: a git-versioned repo (toolz) made the
agent-fix patch SOURCE. Fixes: git-versioned repos keep `.git` + install git (env fix,
not a source edit); agent-fix restricted to allowed globs with everything else reverted;
`env`-with-no-actionable-dep goes to quarantine, never the agent; pipeline-owned
`pipeline-requirements.in` never overwrites a repo's own; input hashes invalidate on
test/import change. Deferred (flagged): collection-broken branch (F6), a few string
literals (F10). Result: glom/toolz/minidump/fixtures green, twice-identical.

## S3 — P2 static
GO-with-fixes ×2. Rounds hardened relative-import resolution (order-independent),
independent call re-resolution in the verifier, exact-nodeid test_map via an in-container
pytest plugin, and — the real bug — a pipeline-code fingerprint in every step's input hash
so an analyzer fix invalidates stale artifacts. Precision 1.0, 0 mismatches on all four
repos; graph byte-identical across runs. No LLM in this layer.

## S4 — P3 excision + harness
GO-with-fixes. `verifier/run.sh` cd+exec; funnel pre-gate rejects candidates whose tests
import private repo symbols before any LLM spend; strict right-reason classifier enforced
against the valid/invalid reason lists; `min_failing_tests`; environment hashes in the
verdict; screen decisions persisted + reused (0-token reruns). glom 4/5, toolz 5/5 VALID.

## S5 — P3 history + instruction gates
GO-with-fixes ×2 (5a) + GO-with-fixes (5b). 5a: PR-merge handling, revert detection,
neutrality check + bounded rewrite, the getattr convention for new-symbol features (author
Q2), per-repo agent budgets, agent turn cap after a 25-turn Kimi rewrite cost ~150k
tokens. 5b: instruction author (never sees the diff) + leak gates (a)/(b) + BIG reviewer +
difficulty labeling; gate refinements (`leak_api_names_only`, `exempt_diff_lines_in_tests`)
removed false positives. Fresh glom: 12 VALID → 12 final, spread easy 6 / medium 4 / hard 2.

## S6 — P1 test-gen + mutators
GO-with-fixes. Generated tests excluded from input hashes + ranking coverage (resume
0-token, byte-identical); kill = ≥1 test failed with collection intact (json-report);
honest whole-file zero-kill drops (no coverage theater); scripted-endpoint tests (no
cassettes) for the container-driven agent. glom `top_k=3`: 4 kept, `glom.core` dropped.

## S7 — P2 OKF + claim verifier
GO-with-fixes. Stamp `verified` only when ≥1 claim was actually checked (`checks:[...]`);
callers/links reported as by-construction, callees upgraded to a real ast.Call re-check;
`generated.at` pinned to the base commit date for byte-identical reruns. Follow-up:
source-module classification fix so `docs/conf.py` + example scripts are no longer indexed
as source (glom 12→11, toolz 20→16 modules; no deliverable affected).

## Session B — finalization
This session (lint, selection, report, transcripts, housekeeping, tests). The final live
glom run is executed by the author; all committed run artifacts come from that single
`--fresh` pass.
