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

**Evidence**: `glom-run.log` shows `agent wrote no file` for both modules.
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
dependencies no longer resolve in the pinned image. These are recorded as
`env-drift` and rejected, never re-locked.

**Why**: re-locking at an old commit would require running `uv pip compile`
against that commit's manifest, which may reference yanked or removed packages.
The cost and complexity were not justified for the 2 glom candidates lost
this way.

**Evidence**: `history_candidates.json` shows 5 `verifier-fails-on-solution`
rejects, some caused by env drift.

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

**Next step**: implement the path when a repo triggers it. The design is
documented in DESIGN.md section 3.5.


## 8. Git in images is not byte-reproducible

**What**: repos with git-derived versions (setuptools-scm, hatch-vcs) install
`git` via `apt-get` in the Docker image. `apt-get` pulls the latest package
version, so the image is not byte-reproducible across builds.

**Why**: the version resolves correctly, and the image digest is recorded in
`build.json` and `verdict.json`. Pinning the `git` package version would
require maintaining a separate apt pin, adding complexity for marginal benefit.

**Evidence**: `hygiene/build.json` records the image digest. Fired on toolz
(git-versioned), not on glom.

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

[To be filled after held-out runs.]


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
