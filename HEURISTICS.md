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
| `(not in config.py yet)` | `uncovered_ratio * log(1+total_lines) * (1 + complexity/5) * public_bonus * not_dunder * not_test_file` | Ranking formula for test-gen candidates (composed from component weights above) | Prioritizes large, complex, public, uncovered code | PROPOSED -- needs user confirmation |

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
| `harness.valid_fail_reasons` | `("AssertionError", "pytest.raises", "NotImplementedError", "exception_in_function_under_test")` | Error types accepted as valid fail-before reasons | These indicate the test is checking real behavior | PROPOSED -- needs user confirmation |
| `harness.invalid_fail_reasons` | `("ImportError", "ModuleNotFoundError", "SyntaxError", "AttributeError@import", "collection_error", "collected_0_items", "fixture_not_found", "error_before_repo_call")` | Error types that make a fail-before verdict INVALID | These indicate broken setup, not behavioral failure | PROPOSED -- needs user confirmation |
| `harness.run_collateral_for_excision` | `True` | Run collateral check for excision tasks too | Uniformity across task types | PROPOSED -- needs user confirmation |
| `harness.recopy_canonical_verifier` | `True` | Re-copy canonical verifier/ into workspace before judging | Prevents a solving agent from hacking the verdict by editing tests | PROPOSED -- needs user confirmation |
| `harness.verifier_may_only_import_public_symbols_in_input` | `True` | Static gate: verifier tests may only import public symbols in input/ | Alternative-implementation evidence without running agent alt-solutions | PROPOSED -- needs user confirmation |
| `harness.verifier_visibility` | `"visible"` | `--verifier-visibility visible\|hidden` | `visible` matches PDF layout; hack-proof via harness re-copy | PROPOSED -- needs user confirmation |

### P3: Instruction and leak prevention

| Config key | Default | What it does | Why | Status |
|---|---|---|---|---|
| `instruction.show_diff_to_author` | `False` | Whether the instruction-authoring agent sees the solution diff | Structural leak prevention: agent sees input/ tree, tests, okf, summary only | PROPOSED -- needs user confirmation |
| `instruction.leak_min_tokens` | `5` | Min token length for a solution-diff line to trigger leak check | Very short lines (e.g. `pass`) are too generic to be leaks | PROPOSED -- needs user confirmation |
| `instruction.forbid_new_identifiers_from_diff` | `True` | No identifiers newly introduced by the diff may appear in instruction | Unless they appear in public API or tests | PROPOSED -- needs user confirmation |
| `instruction.examples_from_verifier` | `2` | Number of input-to-output examples copied from verifier tests into instruction | Concrete examples ground the instruction | PROPOSED -- needs user confirmation |
| `instruction.max_regenerations` | `2` | Max instruction regenerations on leak/quality review failure | Bound cost of the review loop | PROPOSED -- needs user confirmation |
| `instruction.files_in_scope_include_importers_and_tests` | `True` | files_in_scope includes direct importers + tests from graph | Gives the solver enough context without over-scoping | PROPOSED -- needs user confirmation |

### P3: Difficulty

| Config key | Default | What it does | Why | Status |
|---|---|---|---|---|
| `difficulty.features` | `("files_touched", "functions_touched", "callers_count", "cross_module_edges", "diff_size", "similar_named_functions_nearby", "test_count")` | Code-computed features fed to the LLM for difficulty labeling | Objective inputs the LLM must cite in its justification | PROPOSED -- needs user confirmation |
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

### Agent configuration

| Config key | Default | What it does | Why | Status |
|---|---|---|---|---|
| `agent.max_turns` | `25` | Max tool-call turns per agent run | Hard stop to prevent runaway agents | PROPOSED -- needs user confirmation |
| `agent.max_tokens_per_tool_result` | `8000` | Truncation limit for tool output returned to model | Keeps context usage bounded | PROPOSED -- needs user confirmation |
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
| `p3.build.difficulty_label` | direct JSON | BIG |
| `report.draft_sections` | direct | BIG |

Estimated volume for glom: ~25-35 agent runs, ~100-150 direct calls.

### Environment variables

| Env var | Default | Purpose | Status |
|---|---|---|---|
| `LLM_BASE_URL` | `""` (required) | Baseten OpenAI-compatible endpoint | PROPOSED -- needs user confirmation |
| `LLM_API_KEY` | `""` (required) | API key for the serving endpoint | PROPOSED -- needs user confirmation |
| `LLM_MODEL_BIG` | `moonshotai/Kimi-K2.6` (thinking on) | Model ID for BIG tier (authoring/coding/agents/review) | PROPOSED -- needs user confirmation |
| `LLM_MODEL_SMALL` | `deepseek-ai/DeepSeek-V4-Flash-0731` (reasoning low) | Model ID for SMALL tier (classification/lookup) | PROPOSED -- needs user confirmation |
