# Heuristics, thresholds, flags, and defaults

Values live in `pipeline/config.py` (dotted paths below are `Config` attribute paths, e.g. `testgen.top_k_modules` means `Config().testgen.top_k_modules`); env vars listed separately. This file is the single canonical reference. It must be linked from README.md.

All values are **PROPOSED** and require user confirmation before finalization.


## Heuristics and thresholds

### P1: Detection

| Config key | Default | What it does | Why | Status |
|---|---|---|---|---|
| `detect.supported_ecosystems` | `("python",)` | Ecosystems the pipeline can handle | Python-only behind EcosystemAdapter; non-Python exits loudly | PROPOSED -- needs user confirmation |
| `detect.python_version_cap` | `"3.12"` | Maximum Python version chosen for the target repo | 3.12 has the best wheel coverage; 3.13 breaks some C-extension deps | PROPOSED -- needs user confirmation |
| `detect.python_version_default` | `"3.12"` | Fallback when repo metadata has no version info | Safe default with broad compatibility | PROPOSED -- needs user confirmation |
| `detect.manifest_markers` | `("pyproject.toml", "setup.py", "setup.cfg", "requirements.in", "requirements.txt")` | Files checked (in priority order) to determine packaging style | Covers all common Python packaging patterns | PROPOSED -- needs user confirmation |
| `detect.import_alias_table` | `{"yaml": "PyYAML", "cv2": "opencv-python", "PIL": "Pillow", "sklearn": "scikit-learn", "bs4": "beautifulsoup4", "dateutil": "python-dateutil", "attr": "attrs", "dotenv": "python-dotenv", "jwt": "PyJWT", "Crypto": "pycryptodome"}` | Maps import names to PyPI package names for repos with no manifest | Deterministic resolution before LLM fallback | PROPOSED -- needs user confirmation |
| `detect.test_tools` | `("pytest", "coverage", "pytest-json-report")` | Test tools always added to the lock | Needed for baseline runs and structured reports | PROPOSED -- needs user confirmation |
| `detect.dev_tools` | `("ruff",)` | Dev tools always added to the lock | Lint/format stage needs ruff | PROPOSED -- needs user confirmation |
| `detect.git_version_tools` | `("setuptools-git-versioning", "setuptools_scm", "setuptools-scm", "hatch-vcs", "versioneer", "dunamai", "pdm-backend")` | Build-system markers meaning the version is derived from git metadata | such repos keep .git in the build context + install git so the version resolves (env fix, not a source edit) (S2) | PROPOSED -- needs user confirmation |

### P1: Compose detection signals

| Config key | Default | What it does | Why | Status |
|---|---|---|---|---|
| `detect.service_import_signals` | `{"psycopg2": "postgres", "asyncpg": "postgres", "redis": "redis", "pymongo": "mongo", "celery": "broker", "kombu": "broker"}` | Maps Python imports/deps to required services | Deterministic service detection from code | PROPOSED -- needs user confirmation |
| `detect.service_env_signals` | `("DATABASE_URL", "REDIS_URL")` | Env var names in .env.example that signal service needs | Catches service deps not visible from imports alone | PROPOSED -- needs user confirmation |

### P1: Pinning

| Config key | Default | What it does | Why | Status |
|---|---|---|---|---|
| `pin.resolver` | `"uv"` | Resolver used for dependency locking (`uv pip compile`) | Faster than pip-tools, reads setup.py/requirements/pyproject directly | PROPOSED -- needs user confirmation |
| `pin.generate_hashes` | `True` | Pass `--generate-hashes` to the resolver | Integrity verification on install | PROPOSED -- needs user confirmation |
| `pin.emit_constraints_txt` | `True` | Also emit `constraints.txt` alongside the lock | So setup.py installs resolve identically | PROPOSED -- needs user confirmation |
| `pin.lock_filename` | `"requirements.lock.txt"` | Name of the generated lockfile | pip-installable, distinct from repo's own requirements.txt | PROPOSED -- needs user confirmation |
| `pin.requirements_in_filename` | `"pipeline-requirements.in"` | Name of the synthesized canonical requirements input | pipeline-owned; must NOT overwrite a repo's own requirements.in (S2) | PROPOSED -- needs user confirmation |
| `pin.constraints_filename` | `"constraints.txt"` | Name of the emitted constraints file | so setup.py installs resolve identically (S2) | PROPOSED -- needs user confirmation |
| `pin.include_extras` | `("test", "tests", "testing", "dev")` | Manifest extras folded into the lock when present | test suites' deps often live in a `test` extra (e.g. glom) (S2) | PROPOSED -- needs user confirmation |
| `pin.alias_reask_attempts` | `1` | Re-asks for a corrected PyPI name when an inferred import fails to resolve, before dropping it | LLM proposes, uv disposes: verify mappings against real PyPI, bounded re-ask (S2) | PROPOSED -- needs user confirmation |

### P1: Docker

| Config key | Default | What it does | Why | Status |
|---|---|---|---|---|
| `docker.image_name_prefix` | `"bench-"` | Prefix for built images (e.g. `bench-glom`) | One image per target repo, namespaced | PROPOSED -- needs user confirmation |
| `docker.base_image` | `"python:{py}-slim"` | Base image template (digest-pinned at build time) | Slim for smaller images; `{py}` filled from detected version | PROPOSED -- needs user confirmation |
| `docker.pin_base_image_digest` | `True` | Pin the base image to a specific sha256 digest | Deterministic builds | PROPOSED -- needs user confirmation |
| `docker.network_none_for_runs` | `True` | Pass `--network none` on all test/verifier container runs | Sandbox: no network access during code execution | PROPOSED -- needs user confirmation |
| `docker.default_cmd_timeout_s` | `900` | Per-command timeout (seconds) for `docker run` | Prevents hung processes; 15 min covers large test suites | PROPOSED -- needs user confirmation |
| `docker.harness_parallel_workers` | `4` | ThreadPoolExecutor workers for parallel harness docker runs | Throughput vs host resources balance | PROPOSED -- needs user confirmation |
| `docker.compose_supported_services` | `("postgres", "redis")` | Service types the pipeline can template docker-compose for | Scope limit; anything else reported as unsupported | PROPOSED -- needs user confirmation |
| `docker.compose_service_images` | `{"postgres": "postgres:16.4", "redis": "redis:7.4"}` | Pinned service images for compose (digest-pinned at generation time) | Deterministic service versions | PROPOSED -- needs user confirmation |
| `agent.docker_repair_max_attempts` | `3` | Max agent attempts to fix a failing docker build/test | Bound repair cost; 3 covers most fixable issues | PROPOSED -- needs user confirmation |

### P1: Baseline

| Config key | Default | What it does | Why | Status |
|---|---|---|---|---|
| `baseline.framework_priority` | `("pytest", "unittest")` | Detection order for test frameworks | pytest is most common; unittest as fallback | PROPOSED -- needs user confirmation |
| `baseline.env_fix_attempts` | `1` | Automatic env-fix attempts (e.g. add missing extra) before quarantine | One quick try; more would be speculative | PROPOSED -- needs user confirmation |
| `baseline.quarantine_file` | `"tests/quarantine.txt"` | Path for generated `--deselect` list | Quarantined tests reported in REPORT.md; never deleted | PROPOSED -- needs user confirmation |
| `baseline.treat_collection_broken_as_no_tests_after_repair` | `True` | If collection still broken after one repair attempt, treat as "no tests" | Triggers test-gen bootstrap instead of stalling | PROPOSED -- needs user confirmation |
| `baseline.report_filename` | `".pytest-report.json"` | pytest-json-report output path (read from the container workdir) | structured pass/fail + failure reason for classification (S2) | PROPOSED -- needs user confirmation |
| `baseline.agent_fix_allowed_globs` | `("tests/**", "test/**", "conftest.py", "Dockerfile", ".dockerignore", "requirements.in", "requirements.lock.txt", "constraints.txt", "pipeline-requirements.in")` | Paths the agent-fix step may change; edits outside are reverted + audited | the agent must never patch the code under test (S2) | PROPOSED -- needs user confirmation |
| `agent.baseline_fix_max_attempts` | `1` | Bounded agent-fix attempts for pre-existing broken tests | Audited repair; capped to avoid rabbit holes | PROPOSED -- needs user confirmation |

### P1: Test generation

| Config key | Default | What it does | Why | Status |
|---|---|---|---|---|
| `testgen.top_k_modules` | `5` | Number of top under-covered modules to target | Focuses effort on the most impactful gaps | PROPOSED -- needs user confirmation |
| `testgen.top_n_functions_per_module` | `6` | Functions per module handed to the agent | Keeps agent context focused; top-N by score | PROPOSED -- needs user confirmation |
| `testgen.min_function_lines` | `3` | Skip functions shorter than this | Trivial functions aren't worth generating tests for | PROPOSED -- needs user confirmation |
| `testgen.complexity_weight` | `5.0` | Divisor in score term `(1 + complexity/weight)` | Controls how much cyclomatic complexity boosts ranking | PROPOSED -- needs user confirmation |
| `testgen.public_bonus` | `1.5` | Multiplier for public functions in the ranking score | Public API matters more for behavioral testing | PROPOSED -- needs user confirmation |
| `testgen.private_min_complexity` | `5` | `_private` functions included only if complexity >= this | Skip trivial internals; keep complex ones | PROPOSED -- needs user confirmation |
| `testgen.skip_dunder` | `True` | Skip `__dunder__` methods | Dunder methods rarely need generated tests | PROPOSED -- needs user confirmation |
| `testgen.skip_init_reexports` | `True` | Skip `__init__.py` re-exports | Re-exports have no logic to test | PROPOSED -- needs user confirmation |
| `testgen.skip_cli_main` | `True` | Skip CLI `main()` functions | CLI entry points need integration tests, not unit tests | PROPOSED -- needs user confirmation |
| `testgen.generated_tests_dir` | `"tests/generated"` | Output directory for generated test files | Separate from existing tests for clarity | PROPOSED -- needs user confirmation |
| `testgen.example_tests_in_prompt` | `2` | Number of existing tests shown to the agent for style | Enough to match conventions without flooding context | PROPOSED -- needs user confirmation |
| `testgen.mutants_per_function` | `4` | Approx number of mutants injected per targeted function | Enough to test discrimination; not so many it's slow | PROPOSED -- needs user confirmation |
| `testgen.min_mutants_killed` | `1` | Min mutants a generated test must kill to be kept | Proves test is meaningful; mirrors graders' bug-injection eval | PROPOSED -- needs user confirmation |
| `testgen.mutators` | `("comparison_flip", "comparison_boundary", "arithmetic_swap", "and_or_swap", "return_none", "constant_tweak", "statement_delete")` | AST mutation operators applied | Covers the most common real-bug patterns | PROPOSED -- needs user confirmation |
| `agent.testgen_max_retries` | `2` | Retries with mutation-survival feedback | Gives the agent a fair shot at writing discriminating tests | PROPOSED -- needs user confirmation |
| `testgen.enabled` | `True` | Master switch for the step (`--no-testgen` sets False) | Fast reruns can skip generation | PROPOSED -- needs user confirmation |
| `testgen.place_beside_existing_tests` | `True` | Put generated tests in a `generated/` subdir of the repo's primary test dir (else `generated_tests_dir`) | Guarantees the repo's own runner collects them (glom uses `glom/test/`, not `tests/`) | PROPOSED -- needs user confirmation |
| `testgen.max_agent_runs_per_repo` | `10` | Cap on write+retry agent runs across all modules | Bounds token/time spend per repo | PROPOSED -- needs user confirmation |
| `testgen.agent_max_turns` | `12` | Per-agent tool-turn cap | Same bound P3 build agents use | PROPOSED -- needs user confirmation |
| `testgen.generated_subdir` | `"generated"` | Subdir name for generated tests + marker excluded from input hashes / ranking coverage | Keeps generated tests out of their own ranking so reruns are idempotent | PROPOSED -- needs user confirmation |
| `testgen.mutant_timeout_s` | `120` | A mutant run past this is `invalid`, not a kill | An infinite-loop mutant must not count as discrimination | PROPOSED -- needs user confirmation |
| `testgen.lock_filename` | `".testgen.lock"` | Run-dir lock; fail fast if another process holds it | Prevents two concurrent test-gen runs corrupting the repo | PROPOSED -- needs user confirmation |
| test-gen ranking score | `uncovered_ratio * log(1+total_lines) * (1 + complexity/complexity_weight) * public_bonus` | Only candidates with `score > 0` (some uncovered lines) are selectable; `uncovered_ratio = missed_in_span / measurable_in_span` from testgen's own in-container coverage run | Prioritizes large, complex, public, uncovered code; never re-tests fully-covered functions | PROPOSED -- needs user confirmation |

### P1: Lint

| Config key | Default | What it does | Why | Status |
|---|---|---|---|---|
| `lint.tool` | `"ruff"` | Lint/format tool | Single tool for both lint and format | PROPOSED -- needs user confirmation |
| `lint.rules` | `("E", "F", "W", "I", "B", "UP")` | Ruff lint rules enabled | Conservative set: catches real issues without style noise | PROPOSED -- needs user confirmation |
| `lint.autofix` | `True` | Run `ruff check --fix` | Auto-fix what ruff can | PROPOSED -- needs user confirmation |
| `lint.format` | `True` | Run `ruff format` | Consistent formatting | PROPOSED -- needs user confirmation |
| `lint.allow_noqa_for_unfixable` | `True` | Add per-file `# noqa` for unfixable errors | Leaves repo lint-clean without manual work | PROPOSED -- needs user confirmation |
| `lint.llm_fix_unfixable` | `False` | Use LLM (BIG) to fix lint errors ruff can't auto-fix | Optional; default off since noqa + report is safer | PROPOSED -- needs user confirmation |
| `lint.never_lint_historical_trees` | `True` | Skip lint/format on trees used by P3 history tasks | Would pollute the real diff between input/ and solution/ | PROPOSED -- needs user confirmation |

### P2: Graph

| Config key | Default | What it does | Why | Status |
|---|---|---|---|---|
| `graph.edge_types` | `("imports", "contains", "calls", "inherits", "tested_by")` | Edge types in repo_graph.json | Covers the relationships graders verify | PROPOSED -- needs user confirmation |
| `graph.resolve_calls_intra_repo_only` | `True` | Only resolve calls to symbols defined in the repo | Unresolved calls listed separately, never guessed | PROPOSED -- needs user confirmation |
| `graph.verification_sample_edges` | `200` | Number of edges sampled for self-verification | Enough for statistical confidence without excessive runtime | PROPOSED -- needs user confirmation |
| `graph.diversity_unit` | `"file"` | Default diversity unit: `"file"` or `"subpackage"` | Source file for glom-sized repos; subpackage for big repos | PROPOSED -- needs user confirmation |
| `graph.large_repo_module_threshold` | `200` | Module count at which diversity unit switches to subpackage | Below 200 modules, per-file diversity is meaningful | PROPOSED -- needs user confirmation |
| `graph.complexity_metric` | `"branch_count"` | Cyclomatic-complexity method | Our own McCabe branch counter (no radon dependency): deterministic, version-stable (S3) | PROPOSED -- needs user confirmation |
| `graph.test_dir_names` | `("test", "tests")` | Dirs whose `.py` files are indexed as tests, not source | test files feed `tested_by` but are never source nodes (S3) | PROPOSED -- needs user confirmation |
| `graph.test_file_globs` | `("test_*.py", "*_test.py")` | Filename globs also treated as tests | catches test files outside a tests dir (S3) | PROPOSED -- needs user confirmation |
| `graph.nonsource_files` | `("setup.py",)` | `.py` files excluded from graph nodes | packaging/build scripts run side effects on import and pollute diversity counts (S3) | PROPOSED -- needs user confirmation |

**McCabe branch counter** (`graph.complexity_metric = "branch_count"`, implemented in `ecosystems/symbols.py:_complexity`): complexity = `1 + decision points`. Counted, per function body (nested defs excluded — they own their own count): each `if`/`elif`, `for`/`async for`, `while`, `except` handler, ternary (`IfExp`), each comprehension clause and each `if` within a comprehension, each `match` case, and each boolean operator beyond the first in a `and`/`or` chain. Chosen over radon so the number is dependency-free and identical across environments (determinism requirement).

### P2: Knowledge indexes (P3 data files)

| Config key | Default | What it does | Why | Status |
|---|---|---|---|---|
| `knowledge.ctx_plugin_module` | `"_kn_ctx_plugin"` | pytest plugin (written into the build context, loaded with `-p`) that sets coverage's context to each test's exact pytest nodeid via `coverage.Coverage.current().switch_context` | captures parametrized/inherited cases distinctly; no pytest-cov dependency (S3) | PROPOSED -- needs user confirmation |
| `knowledge.coveragerc_filename` | `".coveragerc-knowledge"` | pipeline-owned coverage config written into the build context | must not clobber a repo's own `.coveragerc`; passed via `--rcfile` (S3) | PROPOSED -- needs user confirmation |
| `knowledge.coverage_json_filename` | `".knowledge-coverage.json"` | in-container `coverage json --show-contexts -i` output | `-i` skips transient doctest sources (e.g. glom `.rst` snippets) that would abort the report (S3) | PROPOSED -- needs user confirmation |
| `knowledge.coverage_contexts_filename` | `"coverage_contexts.json"` | persisted raw per-line test contexts | verify re-derives `tested_by` from these (S3) | PROPOSED -- needs user confirmation |
| `knowledge.pr_number_regex` | `r"(?:GH-\|#)(\d+)"` | extracts a PR/issue number from a commit subject | history index provenance (S3) | PROPOSED -- needs user confirmation |
| `knowledge.manifest_name_prefixes` | `("requirements",)` | filename prefixes (plus `detect.manifest_markers`) that count as a manifest touch | history `touches_manifest` flag (S3) | PROPOSED -- needs user confirmation |
| `knowledge.source_roots` | `("src",)` | src-layout roots stripped when naming a historical module | keeps history qualnames consistent with the graph's package-aware naming (S3) | PROPOSED -- needs user confirmation |
| `knowledge.show_commit_max_chars` | `4000` | output cap for the `show_commit` tool's git fallback | bounds tool-result size (S3) | PROPOSED -- needs user confirmation |
| `knowledge.graph_filename` | `"repo_graph.json"` | graph artifact name in `output/<repo>/knowledge/` | -- | PROPOSED -- needs user confirmation |
| `knowledge.symbols_filename` | `"symbol_index.json"` | raw AST facts artifact name | consumed by graph/indexes/verify (S3) | PROPOSED -- needs user confirmation |
| `knowledge.history_filename` | `"history_index.json"` | per-commit index artifact name | P3 history funnel input (S3) | PROPOSED -- needs user confirmation |
| `knowledge.test_map_filename` | `"test_map.json"` | test_id → functions artifact name | P3 coverage-of-touched-functions filter (S3) | PROPOSED -- needs user confirmation |
| `knowledge.coverage_filename` | `"coverage.json"` | per-function coverage % artifact name | test-gen ranking + excision eligibility (S3) | PROPOSED -- needs user confirmation |
| `knowledge.hotspots_filename` | `"hotspots.json"` | per-function change frequency artifact name | P3 signal scoring (S3) | PROPOSED -- needs user confirmation |
| `knowledge.verification_filename` | `"graph_verification.json"` | self-verification report artifact name | precision stats REPORT cites (S3) | PROPOSED -- needs user confirmation |
| `knowledge.code_fingerprint_files` | symbols.py + knowledge/{graph,indexes,verify,runner}.py | analyzer sources hashed into every knowledge step's input hash | a code fix must invalidate its artifacts, not just input changes (S3) | PROPOSED -- needs user confirmation |
| `hygiene_code_files` | ecosystems/python.py + hygiene/{detect,pin,dockerfile,compose,build,baseline}.py | analyzer sources hashed into every hygiene step's input hash | same resumability guard for P1 (S3) | PROPOSED -- needs user confirmation |

### P2: OKF

| Config key | Default | What it does | Why | Status |
|---|---|---|---|---|
| `okf.okf_version` | `"0.2"` | OKF spec version followed | Google Cloud spec v0.2 (June 2026) | PROPOSED -- needs user confirmation |
| `okf.max_function_pages` | `150` | Max individual function .md pages generated | Keeps .okf/ manageable; remainder summarized in module page | PROPOSED -- needs user confirmation |
| `okf.function_page_selector` | `"public_or_top_complexity"` | Which functions get their own page | Public + high-complexity functions carry the most value | PROPOSED -- needs user confirmation |
| `okf.generated_by_actor` | `"pipeline/{model}"` | Actor string in `generated.by` frontmatter | OKF convention for tool-produced content | PROPOSED -- needs user confirmation |
| `okf.verifier_actor` | `"process:okf-verifier"` | Actor string when static verifier stamps a claim | OKF convention for process-verified claims | PROPOSED -- needs user confirmation |
| `okf.unverified_status` | `"draft"` | Status for claims the verifier could not confirm | Unsupported claims stay draft until human review | PROPOSED -- needs user confirmation |
| `llm.okf_module_chunk_tokens` | `12000` | Max tokens per module before chunking by class/function | Fits within model context window for per-module calls | PROPOSED -- needs user confirmation |

### P3: History funnel

| Config key | Default | What it does | Why | Status |
|---|---|---|---|---|
| `history.min_source_lines_changed` | `3` | Min source-line diff to keep a commit | Smaller diffs are trivial (typos, version bumps) | PROPOSED -- needs user confirmation |
| `history.max_source_lines_changed` | `300` | Max source-line diff to keep a commit | Larger diffs are too complex to be a single task | PROPOSED -- needs user confirmation |
| `history.max_source_files_changed` | `6` | Max source files touched by a commit | More files = harder to scope as one task | PROPOSED -- needs user confirmation |
| `history.require_coverage_or_added_tests` | `True` | Drop if touched functions have zero coverage AND commit adds no tests | No way to verify the task | PROPOSED -- needs user confirmation |
| `history.reject_manifest_changes` | `True` | Drop commits touching setup.py/requirements*/pyproject | Reason: `dependency-changing`; optionally re-lock instead | PROPOSED -- needs user confirmation |
| `history.ignore_paths` | `("docs/", "*.md", "*.rst", ".github/", "CHANGELOG*", "*_version.py")` | Path patterns that don't count as source changes | Filters out docs/CI/version/changelog-only commits | PROPOSED -- needs user confirmation |
| `history.fix_keyword_regex` | `r"fix\|bug\|GH-\d+\|#\d+\|error\|incorrect\|regression\|edge case"` | Regex patterns in commit message that boost signal score | These keywords correlate with verifiable behavior changes | PROPOSED -- needs user confirmation |
| `history.score_fix_keyword` | `1.0` | Score weight for fix-keyword match | Positive signal for taskable commits | PROPOSED -- needs user confirmation |
| `history.score_adds_tests` | `2.0` | Score weight for commit adding/changing tests | Strong signal: ready-made verifier | PROPOSED -- needs user confirmation |
| `history.score_public_fn` | `1.0` | Score weight for touching a public function | Public functions are better task targets | PROPOSED -- needs user confirmation |
| `history.score_single_function` | `1.0` | Score weight for single-function diffs | Easier to scope as a task | PROPOSED -- needs user confirmation |
| `history.score_module_diversity` | `0.5` | Score bonus for module diversity across candidates | Encourages spread across modules | PROPOSED -- needs user confirmation |
| `history.score_reverted_penalty` | `-3.0` | Penalty if the commit was later reverted | Reverted commits are poor task material | PROPOSED -- needs user confirmation |
| `history.keep_kinds` | `("bugfix", "feature")` | LLM-classified commit kinds that pass the filter | Refactor/chore/test-only don't make good tasks | PROPOSED -- needs user confirmation |
| `history.shortlist_size` | `15` | Top candidates after filtering + scoring | Aim to validate 5-6 history tasks for safe margin above required 4 | PROPOSED -- needs user confirmation |
| `history.build_target` | `8` | Approx candidates to actually build and validate | Overshoot to ensure >= 4 valid after harness | PROPOSED -- needs user confirmation |
| `history.pr_merge_input_is_first_parent` | `True` | For PR merges, input/ = first parent (not second) | First parent is the pre-merge mainline state | PROPOSED -- needs user confirmation |
| `history.reject_non_pr_merges` | `True` | Merges without a PR number in the subject are rejected (`non-pr-merge`); PR merges are candidates diffed against their first parent | glom: 39 "Merge branch 'master' into <topic>" back-merges whose first-parent diff is arbitrary (S5a) | PROPOSED -- needs user confirmation |
| `history.reject_root_commits` | `True` | The root commit (no parent) is rejected (`root-commit`) | No `input/` tree exists for it (S5a) | PROPOSED -- needs user confirmation |
| `history.prefer_pr_merge_over_constituents` | `True` | Commits on the branch of a KEPT (classified-in) PR merge (`git rev-list p1..p2`) are `superseded-by-merge(<sha7>)` after classification; they stand alone whenever the merge itself is rejected or classified out | The merge is the complete unit (fix + tests may be split across commits); avoids building the same change twice. glom: 140 superseded (S5a) | PROPOSED -- needs user confirmation |
| `history.reject_reverted` / `history.revert_message_regex` | `True` / `^Revert\b\|This reverts commit ([0-9a-f]{7,40})` | A commit named in a later revert body, or whose exact reverse patch (`git patch-id --stable`) appears later, is rejected `reverted-by(<sha7>)`; when False it only takes `score_reverted_penalty` | DESIGN lists "later reverted" both as a hard filter and as a score penalty; the flag picks (S5a) | PROPOSED -- needs user confirmation |
| `history.classify_diff_max_chars` | `3000` | Source diff shown per commit to the SMALL classifier (tests excluded, truncated) | ~15 commits x 3k chars per call stays well inside the SMALL context (S5a) | PROPOSED -- needs user confirmation |
| `history.classify_max_commits` | `60` | The classifier walks the score-ranked survivors in `llm.classify_batch_size` batches until `shortlist_size` are kept, never past this many commits (rest: `not-classified`) | Bounds SMALL spend; glom's 301 survivors would cost ~20 calls (S5a) | PROPOSED -- needs user confirmation |
| `history.reuse_classify_decisions` | `True` | Classify decisions persist in `history_candidates.json` (`classify_key` = sha256(sha + prompt block)) and are reused on rerun unless `--force history_funnel`/`--fresh` | Reruns are 0-token; the SMALL model is not byte-stable at temperature 0 (S5a) | PROPOSED -- needs user confirmation |
| `history.neutrality_check` / `history.neutrality_rewrite_max_attempts` | `True` / `1` | BIG check of the commit's own tests (public interface vs private/new identifiers/implementation details); when flagged, ONE bounded agent rewrite of the flagged test files (audited, cached by content hash); if still not neutral -> reject `verifier-not-implementation-neutral` / `neutrality-rewrite-failed` | DESIGN 5.2 "agent checks and rewrites for implementation-neutrality" (S5a) | PROPOSED -- needs user confirmation |
| `history.verifier_agent_when_no_tests` / `history.verifier_agent_max_attempts` / `history.agent_test_file_prefix` | `True` / `1` / `"test_hist_"` | Commits without test changes get ONE bounded BIG agent that writes `<test dir>/test_hist_<sha7>.py` (only that file is kept); tests that pass on `input/` are dropped, `harness.min_failing_tests` must remain else `agent-authored-pass-on-input` | DESIGN 5.2 "if no tests were added by the commit, the agent authors tests" (S5a) | PROPOSED -- needs user confirmation |
| `history.max_agent_runs_per_repo` / `history.max_neutrality_rewrites_per_repo` | `6` / `2` | Per build step: total agent runs (verifier author + rewrites) and, within that, rewrites (neutrality + new-symbol); beyond either, the case is a plain reject (`budget-exhausted`). Cached/reused runs do not count | Bounds BIG spend per repo (S5a review) | PROPOSED -- needs user confirmation |
| `history.neutrality_recheck_after_rewrite` | `True` | After a rewrite, ONE more `complete_json` neutrality judgement of the rewritten tests; still flagged -> `verifier-not-implementation-neutral(rewrite:still-not-neutral)`. An agent that hits `agent_max_turns` has no reviewed end state: its files are discarded (`rewrite:max-turns`) | The rewrite is only trusted when the checker accepts it (S5a review) | PROPOSED -- needs user confirmation |
| `history.prompt_new_names_max` | `20` | Change-introduced identifiers listed in agent prompts | Bounded prompt (S5a review) | PROPOSED -- needs user confirmation |
| `history.allow_new_symbol_features` | `True` | Verifier convention for API the change introduces: never a module-level import of a name absent from `input/`; instead `getattr(existing_public_module, name, None)` + presence assert + behavior assert (AssertionError on input = right reason). Commit tests importing such a name are routed to the rewrite agent (`new_symbol_rewrite`) instead of rejected; the verifier agent and the neutrality prompts carry the rule; the static gate accepts getattr on an existing public module and flags `getattr(<repo module>, "_private")` | Lets feature commits become VALID without weakening the strict classifier (S5a review, author Q2) | PROPOSED -- needs user confirmation |
| `history.agent_max_turns` | `12` | Turn cap for the P3 verifier-author and neutrality-rewrite agents (below `agent.max_turns=25`) | A BIG turn with thinking is ~10k tokens; the first glom run let one rewrite hit 25 turns (~150k tokens) (S5a) | PROPOSED -- needs user confirmation |
| `history.agent_diff_max_chars` | `6000` | Source diff shown to the verifier agent (the VERIFIER author may see the diff; the INSTRUCTION author never does) | Bounded prompt (S5a) | PROPOSED -- needs user confirmation |
| `history.collateral_baseline_from_input` | `True` | Collateral baseline for a history task = tests that PASS on `input/` in one build-time container run of the full suite (HEAD quarantine deselected) | The HEAD baseline lists tests that do not exist at old commits and misses tests broken by env drift there; comparing the commit against ITS parent is the meaningful "no collateral breakage" (S5a) | PROPOSED -- needs user confirmation |
| `history.reuse_agent_outputs` | `True` | Agent-produced verifier files are cached under `output/<repo>/tasks/agent_cache/<key>/` and reused on rerun (`reused: true`) | Reruns cost no tokens even for agent steps (S5a) | PROPOSED -- needs user confirmation |
| (build-time gates, no knob) | -- | Before any LLM: static gate on `verifier/` vs `input/`; verifier on `solution/` (collection/import failure -> `env-drift(<reasons>)`, other failures drop those tests); verifier on `input/` (an invalid fail reason -> `verifier-on-input:<reason>`, passing tests dropped). Build walks the shortlist in order until `build_target` tasks are built (backfill past rejects) | Reject for knowable reasons at build time instead of paying for validation; keeps VALID count near `build_target` (S5a) | PROPOSED -- needs user confirmation |
| `llm.classify_batch_size` | `15` | Commits (or excision candidates) per SMALL-model classification call | Balances throughput vs context-window usage | PROPOSED -- needs user confirmation |

### P3: Excision funnel

| Config key | Default | What it does | Why | Status |
|---|---|---|---|---|
| `excision.min_covering_tests` | `2` | Min tests covering a function to be eligible | Need enough tests to define expected behavior | PROPOSED -- needs user confirmation |
| `excision.min_lines` | `8` | Min function body lines | Shorter functions are trivially reconstructible | PROPOSED -- needs user confirmation |
| `excision.max_lines` | `80` | Max function body lines | Longer functions make unreasonably hard tasks | PROPOSED -- needs user confirmation |
| `excision.min_complexity` | `3` | Min cyclomatic complexity | Below this the function is too simple for a meaningful task | PROPOSED -- needs user confirmation |
| `excision.public_only` | `True` | Only excise public functions | Private functions can't be verified without internal knowledge | PROPOSED -- needs user confirmation |
| `excision.min_assertions_touching_fn` | `3` | Threshold below which agent adds edge-case tests | Ensures verifier has enough signal to discriminate | PROPOSED -- needs user confirmation |
| `excision.excision_body` | `'raise NotImplementedError("excised")'` | Replacement body for excised functions | Clear signal in fail-before; symbol still importable (no ImportError) | PROPOSED -- needs user confirmation |
| `excision.strip_docstring` | `False` | `--excision-hard` flag: also strip docstring from excised function | Makes task harder; contract lives only in tests + instruction | PROPOSED -- needs user confirmation |
| `excision.build_target` | `5` | Approx candidates to build and validate | Overshoot to ensure enough valid after harness (max 4 selected) | PROPOSED -- needs user confirmation |
| `excision.max_covering_tests` | `40` | Reject functions covered by more base tests than this (`too-central`) | Central dispatch/registry code (glom `get_handler`: 112 tests) fails nearly the whole suite when excised -- not a focused task (S4) | PROPOSED -- needs user confirmation |
| `excision.require_public_parent` | `True` | A method whose class is `_Private` is rejected (`private-parent`) | `is_public` is per leaf name; `_ArgValuator.mode` is not public API (S4) | PROPOSED -- needs user confirmation |
| `excision.skip_init_modules` | `True` | Functions defined in `__init__.py` are rejected (`init-module`) | Re-export/shim modules; excising them breaks imports package-wide (S4) | PROPOSED -- needs user confirmation |
| `excision.verifier_agent_max_attempts` | `1` | Bounded top-up agent runs (BIG) per candidate when assertions < `min_assertions_touching_fn` | Bounded, audited to agent_actions.jsonl; only the one new test file is kept (S4) | PROPOSED -- needs user confirmation |
| `excision.reject_private_verifier_imports` | `True` | Pre-gate: a candidate whose covering test files import private repo symbols/modules (`pkg._x`, `from m import _y`) is rejected (`verifier-imports-private(<file>: ...)`) before the screen | Same AST rule as the harness static gate; no LLM spent on tasks that would fail it (toolz `_signatures`) (S4) | PROPOSED -- needs user confirmation |
| `excision.reuse_screen_decisions` | `True` | Screen decisions are persisted in `candidates.json` keyed by a content hash (`sha256(qualname + source)`) and reused on rerun; ignored on `--force excision_funnel` / `--fresh` | Reruns spend no tokens on unchanged candidates and stay stable even though the model is not byte-stable at temperature 0 (S4) | PROPOSED -- needs user confirmation |
| `(screen batching)` | -- | The SMALL screen walks the ranking in `llm.classify_batch_size` chunks until `build_target` survivors are found (backfills past screened-out candidates); the rest are `surplus` | `build_target` is met when enough candidates exist; spend is bounded by the ranking length (S4) | PROPOSED -- needs user confirmation |
| `excision.rank_module_round_robin` | `True` | Rank by `covering_tests * complexity`, then round-robin over modules | Module diversity: glom `core.py` holds 14/29 survivors and must not take every slot (S4) | PROPOSED -- needs user confirmation |
| `excision.copy_conftests` | `True` | Copy every `conftest.py` above a verifier test file into `verifier/` | Fixtures still resolve when the canonical verifier is re-copied over a workdir (S4) | PROPOSED -- needs user confirmation |
| `(measurement)` | span | "lines" = `end_line - def line + 1` (decorators excluded, docstring included), as the symbol index records it | One definition shared by the funnel and this file; mini_pkg's largest covered public function is 7 -> fixture runs use `--set excision.min_lines=3 --set excision.min_complexity=1` (S4) | PROPOSED -- needs user confirmation |

### P3: Net-new funnel

| Config key | Default | What it does | Why | Status |
|---|---|---|---|---|
| `netnew.max_tests` | `5` | Max tests a proposed net-new feature should need | Keeps tasks scoped and verifiable | PROPOSED -- needs user confirmation |
| `netnew.max_solution_lines` | `60` | Max implementation lines for a proposed feature | Prevents overly ambitious tasks | PROPOSED -- needs user confirmation |
| `netnew.prefer_existing_module` | `True` | Prefer features touching an existing module over standalone utils | Better integration with the codebase (e.g. new glom spec type) | PROPOSED -- needs user confirmation |
| `netnew.proposals_per_module` | `2` | Number of feature proposals requested per module | Gives selection enough variety | PROPOSED -- needs user confirmation |
| `netnew.build_target` | `3` | Approx candidates to build and validate | Overshoot to ensure 2 valid after harness | PROPOSED -- needs user confirmation |
| `netnew.validated_target` | `2` | Target number of validated net-new tasks | User decision; spec allows up to 3 | PROPOSED -- needs user confirmation |

### P3: Validation harness

| Config key | Default | What it does | Why | Status |
|---|---|---|---|---|
| `harness.determinism_runs` | `3` | Number of repeat runs to check determinism | Catches flaky tests without excessive runtime | PROPOSED -- needs user confirmation |
| `harness.strict_fail_reason` | `True` | Enforce right-reason classification on fail-before | STRICT mode: any invalid fail reason -> INVALID task | PROPOSED -- needs user confirmation |
| `harness.valid_fail_reasons` | `("AssertionError", "pytest.raises", "NotImplementedError", "exception_in_repo_code")` | Reasons accepted for a failing fail-before test (`exception_in_repo_code` = any exception whose traceback passed through a repo, non-test frame) | These indicate the test is checking real behavior; the classifier may ONLY emit reasons from this list or the invalid list (enforced, `ValueError` otherwise) | PROPOSED -- needs user confirmation |
| `harness.invalid_fail_reasons` | `("ImportError", "ModuleNotFoundError", "SyntaxError", "AttributeError@import", "collection_error", "collected_0_items", "fixture_not_found", "error_before_repo_call", "no_failing_test", "no_report")` | Reasons that make a fail-before verdict INVALID | Broken setup, not behavioral failure. `ImportError`/`ModuleNotFoundError`/`SyntaxError` = raised in a test body or at collection; `AttributeError@import` = at collection; an `AttributeError` in a test body is `error_before_repo_call` (S4) | PROPOSED -- needs user confirmation |
| `harness.run_collateral_for_excision` | `True` | Run collateral check for excision tasks too | Uniformity across task types | PROPOSED -- needs user confirmation |
| `harness.recopy_canonical_verifier` | `True` | Re-copy canonical verifier/ into workspace before judging | Prevents a solving agent from hacking the verdict by editing tests | PROPOSED -- needs user confirmation |
| `harness.verifier_may_only_import_public_symbols_in_input` | `True` | Static gate: verifier tests may only import public symbols in input/ | Alternative-implementation evidence without running agent alt-solutions | PROPOSED -- needs user confirmation |
| `harness.verifier_visibility` | `"visible"` | `--verifier-visibility visible\|hidden` | `visible` matches PDF layout; hack-proof via harness re-copy | PROPOSED -- needs user confirmation |
| `harness.report_filename` | `".pytest-report.json"` | json-report written inside the fresh workdir by every verifier run | Structured per-test outcomes for the right-reason classifier and the determinism compare (S4) | PROPOSED -- needs user confirmation |
| `harness.min_failing_tests` | `1` | Fail-before must have at least this many failing tests (`no_failing_test` otherwise); `n_failing`/`n_passing` on input are recorded in `task.json.verifier_on_input` (build time) and `tasks.json` | An input that (mostly) passes its own verifier is not a task (S4) | PROPOSED -- needs user confirmation |
| `harness.build_image_if_missing` | `False` | If the task's `image_tag` is not present locally, build it from `<task>/input/Dockerfile` before validating | Standalone re-validation on a fresh machine (README "Validate a task standalone"); off by default so a typo'd tag never silently builds (S4) | PROPOSED -- needs user confirmation |
| `harness.raw_report_suffix` | `".report.json"` | The raw pytest-json-report of fail-before / pass-after / collateral is kept next to each log (`fail_before.report.json`, ...) | Graders can re-derive every classification from the raw report (S4) | PROPOSED -- needs user confirmation |
| `(setup phase)` | -- | A test with `outcome == "error"` is judged on its `setup` phase (fixture resolution/execution): `fixture '<x>' not found` -> `fixture_not_found`; a fixture that raises is classified like a call-phase exception (repo frame -> valid, else `error_before_repo_call`) | pytest-json-report puts fixture errors in `setup` (no `call` key); a fixture that calls the excised function legitimately fails for the excision reason (S4) | PROPOSED -- needs user confirmation |
| `(collateral)` | -- | A baseline-passing test that is now skipped or not collected on `solution/` counts as failure-to-run (`not_run`, listed separately) and fails the collateral check | Same environment; a test that stops running is a regression signal (S4) | PROPOSED -- needs user confirmation |
| `(environment hashes)` | -- | `verdict.json.environment_hashes` = sha256 of `input/Dockerfile` and `input/<lock>`; the image Id is recorded but not gated | Pins WHAT was built even though image Ids change on rebuild (S4) | PROPOSED -- needs user confirmation |
| `harness.gate_on_image_digest` | `False` | If True, a live image Id != task.json digest makes the task INVALID; else it is only recorded (`checks.image.digest_matches_task`) | A rebuild from the same pinned Dockerfile yields a new image Id (layer timestamps), so gating would invalidate every task after any rebuild; a missing image is always INVALID (S4) | PROPOSED -- needs user confirmation |
| `harness.evidence_dirname`, `fail_before_log`, `pass_after_log`, `collateral_log`, `determinism_filename`, `collateral_filename`, `verdict_filename` | `"evidence"`, `"fail_before.log"`, `"pass_after.log"`, `"collateral.log"`, `"determinism.json"`, `"collateral.json"`, `"verdict.json"` | Evidence file names under `<task>/evidence/` | Assignment layout; `tasks.json` reads `verdict.json` (S4) | PROPOSED -- needs user confirmation |
| `(classifier rule)` | -- | A failing test is valid iff its exception passed through a repo (non-test) frame, or it is an `AssertionError` / `Failed: DID NOT RAISE` raised in the test; `outcome=error` is judged on the `setup` phase; failed collectors -> `collection_error`/`ImportError`/`SyntaxError`; `summary.total == 0` -> `collected_0_items` | Verified against pytest-json-report 1.5.0 in the image: `crash.path` is the raising file, `traceback[-1].message` is the exception type. A third-party wrapper that swallows the repo exception (glom `test_cli_*` via face's `CommandChecker`) is `error_before_repo_call` -> INVALID under STRICT (S4) | PROPOSED -- needs user confirmation |
| `(determinism)` | -- | `determinism_runs` is the TOTAL number of fail-before and of pass-after runs (the primary run counts); runs compare `{exit_code, nodeid -> outcome}` | Same evidence, no extra runs beyond N (S4) | PROPOSED -- needs user confirmation |
| `(static gate scope)` | -- | Any import of a private repo module/symbol (any dotted component starting with `_`: `pkg._impl`, `from m import _y`) is a violation (`private-module` / `private-symbol`); `from <module> import <name>` over modules that exist in `input/` is also checked for existence (`symbol-missing-in-input`); `import pkg.sub` of modules not visible statically is left to the container runs | toolz's `tlz` builds its submodules at import time; existence is proven by fail-before/pass-after (S4) | PROPOSED -- needs user confirmation |

### P3: Task layout (`tasks.*`)

| Config key | Default | What it does | Why | Status |
|---|---|---|---|---|
| `tasks.tasks_root` | `"tasks"` | `tasks/<repo>/<task_id>/` folders and `tasks/<repo>/tasks.json` | DESIGN layout; the repo-root `tasks.json` over the final 10 is S9 (S4) | PROPOSED -- needs user confirmation |
| `tasks.manifest_filename` | `"tasks.json"` | Per-repo manifest name | Assignment (S4) | PROPOSED -- needs user confirmation |
| `tasks.candidates_filename` | `"candidates.json"` | `output/<repo>/tasks/candidates.json`: every function considered, with status + `reject_reason` | Feeds REPORT "what you rejected and why" (S4) | PROPOSED -- needs user confirmation |
| `tasks.task_json`, `tasks.golden_solution`, `tasks.verifier_run_script` | `"task.json"`, `"goldenSolution.md"`, `"run.sh"` | Task folder file names | Assignment layout (S4) | PROPOSED -- needs user confirmation |
| `tasks.excision_id_prefix` | `"exc"` | Task ids `exc-<module>-<name>` (e.g. `exc-glom.core-format_target_spec_trace`) | Deterministic, readable, filesystem-safe (S4) | PROPOSED -- needs user confirmation |
| `tasks.history_id_prefix` / `tasks.history_candidates_filename` | `"hist"` / `"history_candidates.json"` | Task ids `hist-<sha7>`; every commit considered lands in `output/<repo>/tasks/history_candidates.json` with status + `reject_reason` (build bookkeeping in `built_history.json`) | Deterministic ids; feeds REPORT (S5a) | PROPOSED -- needs user confirmation |
| `tasks.history_instruction_status_template` | `"template-S5a"` | `instruction_status` marker on history tasks until the LLM instruction (S5b) replaces it | Same role as `template-S4` (S5a) | PROPOSED -- needs user confirmation |
| `tasks.module` / `tasks.modules[]` (fields, no knob) | -- | `task.json.module` = primary touched module (excision: the target's module; history: the source file with the most changed lines), `modules[]` = all touched modules; `tasks.json` copies both and never has a null module | S9 selection groups by module (S5b) | PROPOSED -- needs user confirmation |
| `tasks.title_max_chars`, `tasks.instruction_tests_listed`, `tasks.audit_goal_chars`, `tasks.audit_summary_chars`, `tasks.content_key_chars` | `100`, `12`, `500`, `300`, `16` | Task title truncation, nodeids listed in the structural instruction, agent goal/summary excerpts kept in `agent_actions.jsonl`, sha256 prefix length of content-hash keys | Former literals, centralized (S5a review) | PROPOSED -- needs user confirmation |
| `tasks.hygiene_overlay_files` | `("Dockerfile", ".dockerignore", "requirements.lock.txt", "pipeline-requirements.in", "constraints.txt")` | Hygiene artifacts overlaid ADDITIVELY onto historical `input/`/`solution/` trees (plus whatever the recorded pipeline commit added, minus `tree_ignore`); a file present in the historical tree is never overwritten, historical trees are never linted | DESIGN 5.2: `input/`->`solution/` diff == the historical change exactly (S5a) | PROPOSED -- needs user confirmation |
| `tasks.tree_ignore` | `(".git", "__pycache__", "*.egg-info", ".pytest_cache")` | Skipped when copying the repo tree into `input/` and `solution/` | Self-contained folders; never ship `.git` (S4) | PROPOSED -- needs user confirmation |
| `tasks.instruction_status_template` | `"template-S4"` | `task.json.instruction_status` marker for the structural (non-LLM) instruction | LLM-authored instruction + leak gates + difficulty land in S5 (S4) | PROPOSED -- needs user confirmation |
| `tasks.code_fingerprint_files` | `("pipeline/tasks/excision.py", "pipeline/tasks/build_excision.py", "pipeline/tasks/history.py", "pipeline/tasks/build_history.py", "pipeline/tasks/harness.py", "pipeline/tasks/manifest.py", "pipeline/tasks/runner.py", "pipeline/tasks/classify.py", "pipeline/ecosystems/source_ops.py")` | Pipeline sources hashed into every tasks step's input hash | A code change invalidates artifacts (S3 lesson) (S4) | PROPOSED -- needs user confirmation |

### P3: Instruction and leak prevention

| Config key | Default | What it does | Why | Status |
|---|---|---|---|---|
| `instruction.show_diff_to_author` | `False` | Whether the instruction-authoring agent sees the solution diff | Structural leak prevention: agent sees input/ tree, tests, okf, summary only | PROPOSED -- needs user confirmation |
| `instruction.leak_min_tokens` | `5` | Min token length for a solution-diff line to trigger leak check | Very short lines (e.g. `pass`) are too generic to be leaks | PROPOSED -- needs user confirmation |
| `instruction.forbid_new_identifiers_from_diff` | `True` | No identifiers newly introduced by the diff may appear in instruction | Unless they appear in public API or tests | PROPOSED -- needs user confirmation |
| `instruction.examples_from_verifier` | `2` | Number of input-to-output examples copied from verifier tests into instruction | Concrete examples ground the instruction | PROPOSED -- needs user confirmation |
| `instruction.max_regenerations` | `2` | Max instruction regenerations on leak/quality review failure | Bound cost of the review loop | PROPOSED -- needs user confirmation |
| `instruction.files_in_scope_include_importers_and_tests` | `True` | files_in_scope includes direct importers + tests from graph | Gives the solver enough context without over-scoping | PROPOSED -- needs user confirmation |
| `instruction.only_valid_tasks` | `True` | The instruct step (author + gates + golden rationale + difficulty) runs only on tasks whose `verdict.json` is valid; INVALID tasks keep their `template-*` marker | They are never selected; no BIG spend on them (S5b) | PROPOSED -- needs user confirmation |
| `instruction.tests_max_chars` / `instruction.diff_max_chars` | `12000` / `8000` | Verifier test sources shown to the author/reviewer; diff shown to the golden-rationale call (the only LLM call that sees the diff) | Bounded prompts (S5b) | PROPOSED -- needs user confirmation |
| `instruction.title_max_chars` | `80` | Title returned by the author is truncated to this | Short manifest titles (S5b) | PROPOSED -- needs user confirmation |
| `instruction.leak_api_names_only` | `True` | Gate (b) considers API-like names the diff introduces (defs, classes, imports, attribute stores) rather than every binding; local variables/parameters (`child`, `branches`) read as English in prose and tripped it on glom | Fewer false positives while still catching new helpers/attributes (S5b) | PROPOSED -- needs user confirmation |
| `instruction.exempt_diff_lines_in_tests` | `True` | Gate (a) ignores diff lines that also appear in the verifier tests (an example copied from the tests is required by the format, and the solver sees the tests) | toolz `hist-639043e` failed three times on a data literal shared by the docstring and the tests (S5b) | PROPOSED -- needs user confirmation |
| (instruction decision key) | -- | `instructions.json` records are keyed by what the author sees (contract, tests, summary, visibility, model) plus a hash of the prompt constants (`PROMPT_VERSION`, system prompts) — not by the gate config, so a loosened gate reuses final decisions; a tightened gate or a re-judgement needs `--force instruct` (also honoured: `--fresh`) | 0-token reruns (S5b) | PROPOSED -- needs user confirmation |
| (reviewer questions, no knob) | -- | `solvable_by_transcription` (copied test examples are required, not transcription; a behavioral statement of a small change is not transcription), `states_mechanical_edit` (names the concrete edit instead of behavior), `self_contained`, `implementation_neutral`; any true/false flag in the wrong direction rejects the draft | DESIGN 5.6 gate (b) (S5b review) | PROPOSED -- needs user confirmation |
| `instruction.leak_min_identifier_chars` | `3` | Diff-introduced identifiers shorter than this are not gated | `x`, `i`, `ok` are too generic to be leaks (S5b) | PROPOSED -- needs user confirmation |
| `instruction.status_final` / `instruction.status_failed` / `instruction.decisions_filename` | `"final"` / `"failed"` / `"instructions.json"` | `task.json.instruction_status` values written by the instruct step; every author/review/golden/difficulty decision is persisted in `output/<repo>/tasks/instructions.json` by content hash (0-token reruns) | S9 selection reads `instruction_status == "final"` (S5b) | PROPOSED -- needs user confirmation |
| `instruction.visible_phrase` / `instruction.hidden_phrase` | see config | Sentence the author must carry for `--verifier-visibility visible|hidden` ("verifier tests are in `verifier/`" vs "hidden tests check…, the instruction carries the full contract") | DESIGN 5.6 visibility flag (S5b) | PROPOSED -- needs user confirmation |
| (leak gate rule, no knob) | -- | Applied to the instruction AND the title. (a) any ADDED solution-diff line (removed lines are not gated: they are in `input/`) with >= `leak_min_tokens` tokens (`\w+` or punctuation) appearing whitespace-normalized in the text, unless the line is also in the verifier tests; (b) any API-like name the diff introduces (defs, classes, imports, attribute stores, module-level constants) that is neither in input/'s public API (module names, top-level bindings, public function/class names) nor in the verifier tests, whole-word match. Feedback to the author never echoes the leaked line/name (details stay in `instructions.json`); the classifier's behavior summary is masked of forbidden names before it enters any prompt; a failed task keeps its template instruction/title in `task.json` (drafts only in `instructions.json`) | DESIGN 5.6 gate (a)/(b) (S5b) | PROPOSED -- needs user confirmation |

### P3: Difficulty

| Config key | Default | What it does | Why | Status |
|---|---|---|---|---|
| `difficulty.features` | `("files_touched", "functions_touched", "callers_count", "cross_module_edges", "diff_size", "similar_named_functions_nearby", "test_count")` | Code-computed features fed to the LLM for difficulty labeling | Objective inputs the LLM must cite in its justification | PROPOSED -- needs user confirmation |
| `difficulty.max_regenerations` | `1` | A rationale that cites no computed feature is regenerated once (feedback in the prompt), then the task gets `difficulty: null`, `difficulty_status: "failed"` | DESIGN 5.6 "must cite at least 1 computed feature" (S5b) | PROPOSED -- needs user confirmation |
| `difficulty.batch_size` | `10` | Tasks labelled per BIG call (features + contract + summary per task) | Batched BIG calls (S5b) | PROPOSED -- needs user confirmation |
| `difficulty.similar_name_min_token_chars` | `3` | Name tokens (split on `_` / camelCase) shorter than this do not make two functions "similar-named" | Avoids `is`, `to`, `a` matches (S5b) | PROPOSED -- needs user confirmation |
| (feature definitions, no knob) | -- | `files_touched` = source files differing input->solution; `functions_touched`; `callers_count` = graph `calls` edges into the touched functions; `cross_module_edges` = `calls`/`imports` edges crossing a module boundary with a touched FUNCTION as an endpoint; `diff_size` = non-blank +/- lines; `similar_named_functions_nearby` = other functions in the touched modules sharing a name token; `test_count` = verifier tests. Cite check = feature name (with `_` or spaces) AND its value within 20 chars (`callers_count=12`, `diff size of 3`, `12 callers count`); name alone or value alone does not count | DESIGN 5.6 feature list (S5b) | PROPOSED -- needs user confirmation |
| `difficulty.justification_must_cite_feature` | `True` | LLM justification must cite >= 1 computed feature | Grounds the label in observable data | PROPOSED -- needs user confirmation |
| `difficulty.target_spread` | `{"easy": 2, "medium": 5, "hard": 3}` | Target difficulty distribution in the final 10 tasks | Ensures variety for evaluation; approximate, not strict | PROPOSED -- needs user confirmation |

### P3: Task selection

| Config key | Default | What it does | Why | Status |
|---|---|---|---|---|
| `selection.total_tasks` | `10` | Total tasks to select | Assignment requirement: exactly 10 | PROPOSED -- needs user confirmation |
| `selection.min_history` | `4` | Min history-derived tasks in the final 10 | Assignment requirement: >= 4 | PROPOSED -- needs user confirmation |
| `selection.max_excision` | `4` | Max excision tasks in the final 10 | Assignment requirement | PROPOSED -- needs user confirmation |
| `selection.max_netnew` | `2` | Max net-new tasks in the final 10 | User decision (PDF allows 3) | PROPOSED -- needs user confirmation |
| `selection.min_distinct_modules` | `4` | Min distinct modules across the 10 selected tasks | Assignment requirement: tasks span >= 4 distinct modules | PROPOSED -- needs user confirmation |


## Flags and defaults

### Pipeline flags (CLI)

| Flag | Maps to | Default | What it does | Why | Status |
|---|---|---|---|---|---|
| `--stage` | `(CLI flag, not in config.py)` | `all` | Run a specific stage: `hygiene`, `knowledge`, `tasks`, or `all` | Allows incremental runs during development | PROPOSED -- needs user confirmation |
| `--force <step>` | `(CLI flag, not in config.py)` | (none) | Force rerun of a specific step even if output exists | Overrides resumability for debugging | PROPOSED -- needs user confirmation |
| `--fresh` | `(CLI flag, not in config.py)` | `false` | Rerun everything from scratch | For grader full-run; ignores state.json | PROPOSED -- needs user confirmation |
| `--llm-cache` | `llm.disk_cache` | `False` | Enable disk cache of prompt-to-response by hash | Speeds up reruns during development; off by default for production | PROPOSED -- needs user confirmation |
| `--excision-hard` | `excision.strip_docstring` | `False` | Strip docstring from excised functions (not just body) | Harder tasks; contract lives only in tests + instruction | PROPOSED -- needs user confirmation |
| `--verifier-visibility` | `harness.verifier_visibility` | `"visible"` | `visible` or `hidden`: whether verifier tests appear in the task workspace | `visible` matches PDF layout; hack-proof via harness re-copy | PROPOSED -- needs user confirmation |
| `--set section.key=value` | (any Config path) | -- | Override any config value from the CLI | Avoid touching code for threshold experiments | PROPOSED -- needs user confirmation |

### LLM configuration

| Config key | Default | What it does | Why | Status |
|---|---|---|---|---|
| `llm.temperature` | `0.0` | Temperature for all LLM calls | Maximizes consistency; determinism enforced by gates, not model output | PROPOSED -- needs user confirmation |
| `llm.max_schema_retries` | `2` | Retries when a tool call fails schema validation | Gives the model a fair chance to self-correct | PROPOSED -- needs user confirmation |
| `llm.accept_fenced_json_fallback` | `True` | Accept fenced-JSON-in-text when forced tool-call fails | More reliable fallback on OSS models | PROPOSED -- needs user confirmation |
| `llm.api_max_retries` | `5` | Exponential-backoff retries on API errors | Resilience against transient serving failures | PROPOSED -- needs user confirmation |
| `llm.api_backoff_base_s` | `1.0` | Base delay (seconds) for exponential backoff | Starting point for retry timing | PROPOSED -- needs user confirmation |
| `llm.request_timeout_s` | `300` | Per-request timeout (seconds) for LLM API calls | Prevents indefinite hangs on slow responses | PROPOSED -- needs user confirmation |
| `llm.disk_cache` | `False` | Enable disk cache of prompt-to-response by hash | Flag: `--llm-cache`; off by default for production | PROPOSED -- needs user confirmation |
| `llm.disk_cache_dir` | `".llm_cache"` | Directory for the prompt-response cache | Keeps cache local to the project | PROPOSED -- needs user confirmation |
| `llm.max_tokens_per_repo` | `5000000` | Hard cap on total tokens (input+output) per repo run | Cost control; abort repo when exceeded | PROPOSED -- needs user confirmation |
| `llm.classify_batch_size` | `15` | Commits or excision candidates per SMALL-model call | Balances throughput vs context-window usage | PROPOSED -- needs user confirmation |
| `llm.okf_module_chunk_tokens` | `12000` | Max tokens per module before chunking by class/function | Fits within model context window | PROPOSED -- needs user confirmation |
| `llm.big_max_tokens` | `8192` | Output-token ceiling for BIG-tier calls | Kimi thinking-on can spend hundreds of completion tokens before the answer; needs headroom (S1) | PROPOSED -- needs user confirmation |
| `llm.small_max_tokens` | `2048` | Output-token ceiling for SMALL-tier calls | Classification/lookup outputs are short (S1) | PROPOSED -- needs user confirmation |
| `llm.cassette_dir` | `"tests/cassettes"` | Directory of record/replay fixtures used by tests | Offline, deterministic tests via `LLM_MODE=replay` (S1) | PROPOSED -- needs user confirmation |

### Agent configuration

| Config key | Default | What it does | Why | Status |
|---|---|---|---|---|
| `agent.max_turns` | `25` | Max tool-call turns per agent run | Hard stop to prevent runaway agents | PROPOSED -- needs user confirmation |
| `agent.max_tokens_per_tool_result` | `8000` | Truncation limit for tool output returned to model | Keeps context usage bounded | PROPOSED -- needs user confirmation |
| `agent.chars_per_token` | `4` | Approx chars/token used to convert the tool-result token budget into a char cap | Cheap truncation without a tokenizer dependency (S1) | PROPOSED -- needs user confirmation |
| `agent.grep_max_matches` | `100` | Cap on matches the `grep` tool returns to the model | Bounds tool-result size on large repos (S1) | PROPOSED -- needs user confirmation |
| `agent.run_tool_timeout_s` | `600` | Timeout (seconds) for agent `run` tool (executes inside container) | Prevents hung commands within agent loops | PROPOSED -- needs user confirmation |
| `agent.docker_repair_max_attempts` | `3` | Max agent attempts to fix a failing docker build/test | Bound repair cost; 3 covers most fixable issues | PROPOSED -- needs user confirmation |
| `agent.baseline_fix_max_attempts` | `1` | Bounded agent-fix attempts for pre-existing broken tests | Audited repair; capped to avoid rabbit holes | PROPOSED -- needs user confirmation |
| `agent.testgen_max_retries` | `2` | Retries with mutation-survival feedback | Gives the agent a fair shot at writing discriminating tests | PROPOSED -- needs user confirmation |

### Reasoning per tier (`TIER_REASONING`, normalized `off|low|high|max`)

Translated per model by `MODEL_CAPS` in `pipeline/config.py` (DeepSeek: `reasoning_effort` none/low/high/max; GLM-5.2: none/high/max, `low`->`high`; Kimi-K2.6: thinking on/off only via `chat_template_args.enable_thinking`).

| Tier | Reasoning | Effect on chosen model | Status |
|---|---|---|---|
| `small` | `low` | DeepSeek-V4-Flash-0731 `reasoning_effort=low` | PROPOSED -- needs user confirmation |
| `big` | `high` | Kimi-K2.6 thinking ON | PROPOSED -- needs user confirmation |

### LLM tier assignment (which step uses which model)

Tier rule: classification/lookup uses SMALL; authoring/coding/agents/review uses BIG.

Per-step model override map lives in `config.py` as `STEP_MODEL` (accessed via `Config.step_model`).

| STEP_MODEL key | Mode | Tier |
|---|---|---|
| `p1.pin.import_to_pypi` | direct JSON | SMALL |
| `p1.docker.repair_agent` | agent | BIG |
| `p1.baseline.classify_failure` | direct JSON | SMALL |
| `p1.baseline.fix_agent` | agent | BIG |
| `p1.testgen.write_tests_agent` | agent | BIG |
| `p1.testgen.mutation_retry_agent` | agent (continuation) | BIG |
| `p1.lint.fix_unfixable` | direct/agent | BIG |
| `p2.okf.module_purpose` | direct JSON | BIG |
| `p2.okf.function_contracts` | direct JSON | BIG |
| `p3.history.classify_commit` | direct JSON batched | SMALL |
| `p3.excision.screen_candidate` | direct JSON batched | SMALL |
| `p3.netnew.propose_features` | direct JSON | BIG |
| `p3.build.verifier_agent` | agent | BIG |
| `p3.build.neutrality_check_rewrite` | direct/agent | BIG |
| `p3.build.netnew_impl_agent` | agent | BIG |
| `p3.build.write_instruction` | direct JSON | BIG |
| `p3.build.review_instruction` | direct JSON | BIG |
| `p3.build.golden_rationale` | direct JSON | BIG |
| `p3.build.difficulty_label` | direct JSON (batched) | BIG |
| `report.draft_sections` | direct | BIG |

Estimated volume for glom: ~25-35 agent runs, ~100-150 direct calls.

### Environment variables

| Env var | Default | Purpose | Status |
|---|---|---|---|
| `LLM_BASE_URL` | `""` (required) | OpenAI-compatible endpoint (read from `.env`) | PROPOSED -- needs user confirmation |
| `LLM_API_KEY` | `""` (required) | API key for the serving endpoint; never logged or written to disk | PROPOSED -- needs user confirmation |
| `LLM_MODE` | `"live"` | `live` \| `record` \| `replay`. Tests use `replay` (cassettes); recording spends tokens once (S1) | PROPOSED -- needs user confirmation |
| `LLM_MODEL_BIG` | `moonshotai/Kimi-K2.6` (thinking on) | Model ID for BIG tier (authoring/coding/agents/review) | PROPOSED -- needs user confirmation |
| `LLM_MODEL_SMALL` | `deepseek-ai/DeepSeek-V4-Flash-0731` (reasoning low) | Model ID for SMALL tier (classification/lookup) | PROPOSED -- needs user confirmation |
