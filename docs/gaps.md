# Known gaps

Each gap: what it is, why it exists, evidence from the glom run, and what a
fix would look like.


## 1. Net-new tasks not generated

**What**: the net-new task source (propose a feature the repo lacks, implement
it, write tests) was designed but never built.

**Why**: history + excision already yield >10 VALID tasks on glom. The
assignment allows 0 to 3 net-new tasks. Building the full propose/implement/
verify pipeline was cut to focus on quality of the other two sources.

**Evidence**: `netnew.*` config exists; no code in `pipeline/tasks/` implements
the funnel or builder.

**Next step**: propose features from the `.okf/` contract gaps, agent-implement
in a fresh branch, validate with the existing harness.


## 2. Lint reverted on glom

**What**: the lint step was reverted. The repo ships un-linted.

**Why**: 7 `glom/test/test_error.py::*_stack` tests assert exact rendered
source lines. Any edit to `core.py` (including ruff formatting) breaks them.
The revert policy (docs/decisions.md) says acceptance is never traded for
cosmetics.

**Evidence**: `output/glom/hygiene/lint.json` records `regressed: true`,
34 files would change, 265 unfixable findings.

**Next step**: per-file lint exclusions derived from tests that assert on
source text, or accept the gap on repos with line-pinned test assertions.


## 3. Test-gen drops large modules

**What**: test generation failed on glom.core (2,595 lines) and glom.grouping.
The agent spent its turn budget reading the module and never wrote a test file.

**Why**: the agent explores a large module's imports and call graph before
writing, and 12 turns are not enough for modules of this size. A 30-turn
budget was tried during development with the same result.

**Evidence**: `output/glom/hygiene/testgen.json` records both modules as
`dropped_no_file`, glom.core with the summary `stopped: reached max turns` and
glom.grouping with an empty one; `transcripts/glom-console.log` shows
`agent wrote no file` for both.
Testgen tokens (~550k) are ~70% of the run's total; one unproductive module
can burn >100k tokens exploring.

**Next step**: two-phase agent (write a skeleton first, then fill in), or
per-function prompts that give the agent a single target at a time.


## 4. OKF verification is partial

**What**: raises precision is ~0.75, side_effects ~0.87. Callers and internal
links are by-construction (graph-derived). Inputs, outputs, and invariants are
unchecked.

**Why**: raises and side_effects are checked via AST (does the function body
contain a `raise X` or call `open()`?). Implicit exceptions (a function that
raises `TypeError` only through a stdlib call) produce false negatives, leaving
the page as `draft`. Checking inputs/outputs/invariants would require symbolic
execution or test-derived evidence.

**Evidence**: `output/glom/knowledge/okf_verification.json` reports precision
per claim kind.

**Next step**: symbolic checks (trace exception propagation through calls),
or test-derived evidence (run the function with known inputs and check
outputs).


## 5. test_map excludes doctests

**What**: the test_map (test nodeid -> source function) does not include
doctests.

**Why**: the coverage context plugin sets context to each test's pytest
nodeid. Doctests do not have pytest-style nodeids, so their coverage is
attributed to no context.

**Evidence**: `test_map.json` contains only pytest test nodeids.

**Next step**: a doctest-aware coverage context, or a secondary pass that
attributes doctest coverage by file.


## 6. Old-commit dependency drift

**What**: history tasks at old commits may fail to build because their
dependencies no longer resolve in the pinned image. A tree that cannot even
collect is recorded as `env-drift`; a tree that collects but whose own tests do
not pass on its solution is recorded as `verifier-fails-on-solution`. Either
way the candidate is rejected, never re-locked.

**Why**: re-locking at an old commit would require running `uv pip compile`
against that commit's manifest, which may reference yanked or removed packages.
The cost and complexity were not justified for the 5 glom candidates lost
this way.

**Evidence**: `output/glom/tasks/history_candidates.json` shows 5
`verifier-fails-on-solution` rejects and no `env-drift(...)` reason: on glom
the drift showed up as the commit's own tests failing on its solution tree in
today's image, not as a collection failure.

**Next step**: attempt re-lock at the old commit with a fallback to the
current lock, and record whether the re-lock succeeded.


## 7. Collection-broken baseline path

**What**: the "one repair attempt, then treat as no tests" path for a
completely broken test suite (import errors at collection, 0 tests collected)
is not implemented.

**Why**: no in-scope repo hit it. All fixture repos and target repos either
had a working suite or no tests at all. The inert config flags for this path
were removed during finalization.

**Evidence**: no test covers this path. The bootstrapping path (no tests at
all) is covered.

**Next step**: implement the path when a repo triggers it. The baseline
section of [pipeline-1-hygiene.md](pipeline-1-hygiene.md) describes the
intended behavior.


## 8. Git in images is not byte-reproducible

**What**: repos with git-derived versions (setuptools-scm, hatch-vcs) install
`git` via `apt-get` in the Docker image. `apt-get` pulls the latest package
version, so the image is not byte-reproducible across builds.

**Why**: the version resolves correctly, and the image digest is recorded in
`build.json` and `verdict.json`. Pinning the `git` package version would
require maintaining a separate apt pin, adding complexity for marginal benefit.

**Evidence**: `hygiene/build.json` records the image digest. Observed during
development on toolz (git-versioned; no artifacts committed), not on glom.

**Next step**: pin the git package version in the Dockerfile, or accept the
gap and document it.


## 9. Difficulty skew

**What**: the achieved difficulty spread (easy 5, medium 4, hard 1) does not
match the soft target (easy 2, medium 5, hard 3).

**Why**: difficulty labels are computed from 7 graph/diff features (files_touched,
functions_touched, callers_count, cross_module_edges, diff_size,
similar_named_functions_nearby, test_count). The eligible task pool on glom
skews easy because most selected tasks touch a single function in a single
file with few callers.

**Evidence**: `selection.json` shows `achieved_spread` vs `target_spread`.

**Next step**: prefer harder candidates in the funnels (e.g., score
cross-module commits higher), or accept that the spread is a soft objective.


## 10. Verifier visibility defaults to visible

**What**: verifier tests are visible to the solver by default. A solver could
read the tests and reverse-engineer the solution.

**Why**: visible tests let the solver understand what behavior is expected.
The harness re-copies the canonical `verifier/` before judging, so the solver
cannot modify the tests to fake a pass.

**Evidence**: `--verifier-visibility hidden` changes the instruction wording
but does not change what the harness runs.

**Next step**: no code change needed. Use `--verifier-visibility hidden` for
harder benchmarks.


## 11. New-API imports stay INVALID by design

**What**: history commits where the verifier test does a top-level
`import new_symbol` (rather than using `getattr`) fail with `ImportError`
on `input/`, which the strict classifier rejects as INVALID.

**Why**: the `getattr` convention is the supported pattern. Relaxing the
classifier for `ImportError` would weaken the gate for all other tasks
where `ImportError` genuinely indicates a broken task.

**Evidence**: the rewrite agent converts top-level imports to `getattr` where
possible. Commits that cannot be converted stay INVALID.

**Next step**: none needed. This is a deliberate design choice.


## 12. Single ecosystem (Python)

**What**: only Python target repos are supported.

**Why**: see docs/decisions.md. Building one adapter well beats splitting
effort.

**Evidence**: `detect.supported_ecosystems = ("python",)`.

**Next step**: implement `EcosystemAdapter` for JavaScript, Go, etc.


## 13. SyntaxWarning from target code silenced globally

**What**: `SyntaxWarning` from parsing target code (e.g., invalid escape
sequences in older Python files) is silenced globally during AST analysis.

**Why**: these warnings are noise from the target repo, not pipeline bugs.
Silencing them keeps the console output clean.

**Next step**: scope the suppression to the AST parsing functions only.


## 14. Held-out fresh-clone results

Run on 2026-08-21 from a fresh clone of the published repository into a clean
directory (setup exactly as the README quick start), against two repos the
pipeline had never seen: `pytoolz/toolz` and `skelsec/minidump`.

**toolz — 10/10 selected.** Hygiene and knowledge passed unchanged on the first
attempt (240 baseline tests, 177-node graph with verification mismatches 0,
conformant OKF). The tasks stage surfaced three real generality bugs, each
fixed and covered by a new unit test:

1. **Schema-retry feedback was empty for forced tool calls.** The excision
   screen died after retries: the model's invalid output lives in
   `tool_calls`, but the retry echoed `message.content` (empty), so the model
   never saw what to correct and drifted into double-encoding the array as a
   JSON string. Fixed: echo the raw tool arguments, decode double-encoded
   top-level properties, `max_schema_retries` 2 -> 3.
2. **Leak-gate exemptions computed from truncated test source.** The
   "add `peek`" history task requires the instruction to name `peek` (the
   verifier tests call it), and names appearing in the verifier tests are
   exempt by design -- but the exemption set was built from test source already
   truncated to `tests_max_chars`, and `test_peek` sat past the cut. All three
   authoring attempts were rejected. Fixed: truncate for prompts only; build
   exemption sets from the full source.
3. **Cached instruction failures were reused on rerun.** After fixing (2) the
   rerun replayed the cached "failed" decision instead of retrying. Fixed:
   reuse final decisions only -- the step re-runs only when code or config
   changed, and a prior failure may be exactly what that change fixed.

One knob was needed: `--set history.max_agent_runs_per_repo=16` (default 6,
tuned on glom) -- the verifier-rewrite agent budget ran out before enough
history candidates were repaired. Final result: 12 tasks built, 12/12 VALID,
10 selected (4 excision + 6 history, 5 distinct modules, easy 4 / medium 5 /
hard 1). Tasks-stage rerun cost ~102k tokens; cached decisions made the
repeated attempts nearly free.

**minidump — honest infeasibility.** The full pipeline ran end-to-end with no
errors (~18 min, ~926k tokens, of which testgen 861k) and everything it built
is sound: 6/6 tasks VALID, all instructions final on the first attempt. But
the repo's sparse test suite starves both funnels: 299 of 568 excision
candidates rejected as uncovered, and 41 of 118 history commits rejected
uncovered-and-no-tests, leaving a shortlist of 2. Selection correctly reports
`infeasible: only 6 eligible VALID+final tasks, need 10` instead of shipping
filler. This is the scenario documented in docs/decisions.md where the cut
net-new source would be required to reach 10 tasks on a coverage-poor repo.

Nothing from either held-out run is committed; the fixes above are.


## 15. Testgen tokens dominate cost

**What**: test generation consumed ~550k tokens on glom, about 70% of the
run's total. One unproductive module (glom.core) can burn >100k tokens
exploring without writing anything.

**Why**: the BIG agent reads the target module, its imports, and its callers
before attempting to write tests. Large modules consume many tokens in
context. Per-repo agent budgets (`testgen.max_agent_runs_per_repo`) cap the
total, but individual modules can still be expensive.

**Evidence**: `output/glom/audit/llm_usage.json` shows
`p1.testgen.write_tests_agent: 550,696` tokens.

**Next step**: per-function prompts (smaller context), two-phase agent (write
a skeleton first), or a pre-screen that skips modules above a line-count
threshold.
