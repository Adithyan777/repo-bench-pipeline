# Design decisions

Each entry: the decision, why it was made, what was considered instead, and
what the choice costs.


## Python-only behind an adapter

**Decision**: support only Python target repos, with all language-specific
logic behind an `EcosystemAdapter` interface (`pipeline/ecosystems/base.py`,
~11 methods). Non-Python repos are detected and rejected with a clear message.

**Why**: the assignment's sample repo is Python. Building one adapter well
(with real integration tests) beats splitting effort across languages.

**Alternatives**: multi-language from the start; language detection with a
generic fallback.

**Consequence**: adding JavaScript or another ecosystem means implementing
the adapter interface. The rest of the pipeline (agent loop, harness, funnels,
docker runner) is already ecosystem-agnostic.


## Own agent loop

**Decision**: a ~120-line agent loop in Python (`pipeline/agent/loop.py`)
using OpenAI-compatible function calling, reused across all stages.

**Why**: zero external harness dependencies. The loop is small enough to
audit and test directly.

**Alternatives considered**: [pi](https://github.com/anthropics/pi) (Node
dependency, TypeScript runtime); mini-swe-agent (wanted no external harness);
PiPy (bundled inside SuperQode, not standalone).

**Consequence**: the loop is simple (ends on no tool calls or turn cap; tool
errors returned as text) but lacks features like memory or self-correction.
Kept behind `AgentRunner` so a more capable harness could be swapped in.


## Open-source models, two tiers

**Decision**: open-source models only, served via an OpenAI-compatible endpoint
(Baseten). Two tiers: BIG (moonshotai/Kimi-K2.6, thinking enabled) for
authoring, coding, agents, and review; SMALL (deepseek-ai/DeepSeek-V4-Flash-0731,
reasoning low) for classification and lookup.

**Why**: the assignment is for building evaluation infrastructure for AI models.
Using proprietary models would create a dependency that conflicts with that
purpose. Two tiers save tokens: classification calls do not need a large
thinking model.

**Alternatives**: single model for everything (simpler, more expensive);
proprietary models (better quality, wrong dependency).

**Consequence**: model IDs are env vars, so swapping models requires only a
`.env` change. Per-step tier assignment is in `config.STEP_MODEL`.


## LLM proposes, deterministic code disposes

**Decision**: every LLM output passes a code gate before being accepted.
Determinism comes from the gates, not from model temperature or seeds.

Examples: mutation kill for test-gen, right-reason classifier for the harness,
leak check for instructions, schema validation for JSON extraction, neutrality
check + bounded rewrite for history verifiers.

**Why**: LLM outputs are non-deterministic. Reproducible pipeline behavior
requires that the final decision is always made by deterministic code. The
LLM is a proposal engine; code is the arbiter.

**Alternatives**: rely on temperature=0 for reproducibility (not guaranteed
by API contracts); run everything twice and diff (doubles cost).

**Consequence**: every new step needs its own gate. The gate design is the
hard part; the LLM call is usually straightforward.


## Heuristics centralized in config.py

**Decision**: every threshold, flag, filter value, and default lives in
`pipeline/config.py` as a typed dataclass field. No magic numbers in the
code.

**Why**: scattered constants make it impossible to review or tune the
pipeline. A single file means one place to audit, one `--set` interface to
override, and one document (docs/configuration.md) to explain them all.

**Alternatives**: per-module constants; YAML config file.

**Consequence**: `config.py` is large (~680 lines, 19 dataclasses). Worth it
for auditability.


## Real integration tests

**Decision**: pipeline tests use real Docker, real uv, real git, and real
fixture repos built with reproducible history. LLM calls are replayed from
committed cassettes. No mocks except for the LLM endpoint.

**Why**: mocks for Docker, git, or uv would not catch the real integration
failures (image build issues, lockfile format changes, git edge cases). The
fixture repos (`tests/fixtures/build_mini_pkg.py`) encode specific scenarios
(bugfix commits, PR merges, no-manifest repos) so tests exercise real
pipeline paths.

**Alternatives**: mock everything (faster, less trustworthy); use the real
LLM (expensive, non-deterministic).

**Consequence**: tests require a running Docker daemon. The full suite takes
~4 minutes; slow tests are marked and skippable.


## Throwaway container execution

**Decision**: every command against target code runs in a throwaway container
(`docker run --rm --network none`), one fresh workdir per unit of work.

**Why**: no shared state between runs (deterministic), no network access
(sandboxed), same image graders will use (reproducible).

**Alternatives**: long-lived container with `docker exec` (state leaks
between runs); host execution with a virtualenv (no sandboxing).

**Consequence**: higher overhead per command (container startup). Acceptable
for a pipeline that runs tens of commands, not thousands.


## Task sources and quotas

**Decision**: three task sources with hard quotas. History-derived (>= 4):
real commits where input/ is the parent state and solution/ is the commit
state. Excision (<= 4): a covered function's body is removed, tests define
the behavior. Net-new (<= 2): not built (cut by decision, since
history + excision already yield >10 VALID).

**Why**: the assignment requires exactly 10 tasks spanning >= 4 modules, with
at least 4 history-derived. History and excision tasks have real provenance
(a commit SHA or an existing function), which is stronger evidence than
synthesized tasks.

**Alternatives**: build net-new tasks too (more effort, weaker provenance).

**Consequence**: net-new is designed and has config (`netnew.*`) but the
funnel and builder were never implemented. If a repo yields too few
history + excision candidates, net-new would need to be built.


## getattr convention for new-API features

**Decision**: history commits that introduce a new public symbol use the
`getattr` convention in verifier tests:
`getattr(mod, name, None)` so the test produces an `AssertionError` on
`input/` (a valid fail reason) instead of an `ImportError` (invalid).

**Why**: the strict right-reason classifier rejects `ImportError` because
it indicates a broken task, not a behavioral difference. A new symbol
genuinely does not exist on `input/`, so the test must check for its
absence via `getattr` rather than importing it directly.

**Alternatives**: relax the classifier for new-symbol imports (weakens the
gate for all other tasks); skip new-API commits entirely (loses valid
feature tasks).

**Consequence**: the rewrite agent must understand the convention. Commits
that top-level `import` a new symbol on `input/` stay INVALID by design.


## Verifier visible + re-copy

**Decision**: verifier tests default to `visible` (the solver can see them).
The harness always re-copies the canonical `verifier/` over the workdir
before judging, so a solver cannot modify the tests to fake a pass.

**Why**: visible verifiers let the solver understand what behavior is
expected. Re-copying makes this safe: the solver's changes to `verifier/`
are overwritten.

**Alternatives**: `hidden` mode (the solver never sees the tests; instruction
carries the full contract).

**Consequence**: `--verifier-visibility hidden` changes the instruction's
wording but does not change what the harness runs.


## Instruction author never sees the diff

**Decision**: the BIG model that writes the task instruction sees only the
input-side code (signatures, docstrings), the verifier tests, and a masked
behavior summary. It never sees the diff or the solution.

**Why**: if the author sees the solution, the instruction is likely to
describe "what changed" rather than "what the code should do." This leaks
implementation details to the solver.

Two code gates enforce this: gate (a) rejects instructions containing lines
from the diff (>= 5 tokens), and gate (b) rejects instructions containing
new identifiers introduced by the diff.

**Alternatives**: let the author see the diff and rely on the reviewer to
catch leaks (more fragile).

**Consequence**: the golden rationale (`goldenSolution.md`) is the only LLM
call that may see the diff.


## Test-gen mutation gate (not coverage alone)

**Decision**: generated tests must pass on real code AND kill at least 1 of 4
AST mutants per targeted function. Tests that kill nothing are dropped.

**Why**: coverage alone does not prove tests are meaningful. A test that
imports a module and calls a function with no assertions achieves coverage
but catches no bugs. The mutation gate mirrors the graders' approach of
injecting bugs to see if tests catch them.

**Alternatives**: coverage threshold only (easier, weaker); full mutation
testing with mutmut (slow, external dependency).

**Consequence**: test-gen is more expensive (4 mutant runs per function,
up to 2 retries with feedback). On glom, testgen consumed ~70% of the run's
total tokens. Some modules (glom.core, glom.grouping) were dropped when the
agent could not produce tests that killed mutants.


## OKF honesty: draft over over-claim

**Decision**: OKF pages are stamped `verified` only when at least one claim
was actually checked (raises, side_effects, or callees) and passed. Pages
with no checkable claims or failed checks stay `draft`. Callers and internal
links are reported as by-construction (graph-derived), not independently
verified.

**Why**: over-claiming verification weakens the trust signal. A `draft` label
is honest; a false `verified` label is misleading.

**Alternatives**: stamp all graph-derived pages as verified (inflates the
count); verify all claim kinds including inputs/outputs/invariants
(requires symbolic execution or test-derived evidence, not implemented).

**Consequence**: raises precision is ~0.75 and side_effects ~0.87 on glom.
Implicit exceptions (e.g., a function that raises `TypeError` only via a
stdlib call) stay `draft`.


## Lint revert policy

**Decision**: if a ruff lint or format change regresses a baseline-passing
test, the entire lint step is reverted. The repo ships un-linted with all
findings recorded.

**Why**: acceptance (green test suite, identical twice) is never traded for
cosmetics.

**Alternatives**: per-file lint exclusions derived from tests that assert on
source text (more surgical, not implemented); accept the regression (violates
acceptance criteria).

**Consequence**: on glom, the lint step was reverted because 7
`test_error.py::*_stack` tests assert exact rendered source lines. Any edit
to `core.py` breaks them.


## Resumability by fingerprint

**Decision**: each step's input hash includes a fingerprint of the pipeline's
own source files. A code change invalidates stale artifacts.

**Why**: without the code fingerprint, a bug fix to (say) the graph builder
would leave stale graph artifacts in place because the repo inputs had not
changed. This was caught in review: the original implementation skipped steps
based only on repo content.

**Alternatives**: always rerun (wasteful); manual `--fresh` (error-prone).

**Consequence**: the fingerprint file lists are in `Config.hygiene_code_files`,
`KnowledgeConfig.code_fingerprint_files`, and
`TasksConfig.code_fingerprint_files`.


## Per-repo agent budgets

**Decision**: `testgen.max_agent_runs_per_repo` and
`history.max_agent_runs_per_repo` cap the total number of BIG-tier agent
runs per repo.

**Why**: a single large module can burn >100k tokens exploring without
producing useful output. On an early glom run, a 25-turn Kimi neutrality
rewrite cost ~150k tokens. Per-repo budgets bound the worst case.

**Alternatives**: per-module budgets (finer-grained, harder to tune);
no budget (unbounded cost on difficult repos).

**Consequence**: `agent_max_turns` was also reduced from 25 to 12 for the
same reason. The test-gen prompt now includes a "write early" instruction.
