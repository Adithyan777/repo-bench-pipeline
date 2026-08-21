# Configuration

All thresholds, flags, and defaults live in `pipeline/config.py`. Override any
value at runtime with `--set section.key=value`. Environment variables control
secrets and model IDs only.

The source of truth is always `config.py`; this document adds rationale and
glom observations.

Notation: **policy** = a design decision unlikely to change per repo;
**tuning** = a knob you might adjust for different repos or cost targets.
"Fired on glom" / "never fired" notes come from the final glom run.

## Operational knobs

The most commonly tuned values, accessible via `--set` or dedicated CLI flags.


| Key                               | Default   | CLI shortcut          | Purpose                                                                    |
| --------------------------------- | --------- | --------------------- | -------------------------------------------------------------------------- |
| `testgen.agent_max_turns`         | 12        | `--set`               | Turns per test-gen agent run. Higher helps large modules, but costs tokens |
| `testgen.max_agent_runs_per_repo` | 10        | `--set`               | Total write + retry agent runs across all modules                          |
| `testgen.top_k_modules`           | 5         | `--set`               | Modules ranked for test generation                                         |
| `history.build_target`            | 10        | `--set`               | History tasks to build (headroom so selection can choose)                  |
| `history.shortlist_size`          | 20        | `--set`               | History candidates shortlisted after classify                              |
| `history.max_agent_runs_per_repo` | 6         | `--set`               | Verifier/rewrite agent runs for history tasks                              |
| `history.agent_max_turns`         | 12        | `--set`               | Turns per history agent (BIG tier, expensive)                              |
| `harness.min_failing_tests`       | 1         | `--min-failing-tests` | Minimum failing tests in fail-before                                       |
| `harness.determinism_runs`        | 3         | `--set`               | Repeat count for determinism check                                         |
| `selection.total_tasks`           | 10        | `--set`               | Total tasks to select                                                      |
| `llm.max_tokens_per_repo`         | 5,000,000 | `--set`               | Per-repo token budget; run aborts on exceed                                |
| `okf.max_function_pages`          | 150       | `--set`               | Cap on individual function pages in the OKF bundle                         |
| `lint.format`                     | true      | `--set`               | Whether ruff format runs alongside ruff check (`--no-lint` sets `lint.enabled=false`, it is not a shortcut for this key) |
| `testgen.enabled`                 | true      | `--no-testgen`        | Enable/disable test generation                                             |
| `lint.enabled`                    | true      | `--no-lint`           | Enable/disable lint step                                                   |


Example: `./run.sh <repo> --set testgen.top_k_modules=3 --set history.build_target=15`

## Environment variables


| Variable          | Required | Default                              | Purpose                        |
| ----------------- | -------- | ------------------------------------ | ------------------------------ |
| `LLM_BASE_URL`    | yes      | (none)                               | OpenAI-compatible endpoint URL |
| `LLM_API_KEY`     | yes      | (none)                               | API key for the endpoint       |
| `LLM_MODEL_BIG`   | no       | `moonshotai/Kimi-K2.6`               | BIG-tier model ID              |
| `LLM_MODEL_SMALL` | no       | `deepseek-ai/DeepSeek-V4-Flash-0731` | SMALL-tier model ID            |
| `LLM_MODE`        | no       | `live`                               | `live`, `record`, or `replay`  |


Set these in `.env` (loaded automatically, never committed).

## Model tiers and step assignment

Two tiers: **BIG** (authoring, coding, agents, review) and **SMALL**
(classification, lookup). Per-tier reasoning levels in `TIER_REASONING`:
small = `low`, big = `high`.

Reasoning parameters are translated per model via `MODEL_CAPS`:

- `moonshotai/Kimi-K2.6`: `enable_thinking` (boolean).
- `deepseek-ai/DeepSeek-V4-Flash-0731`: `reasoning_effort` (string).

`STEP_MODEL` assigns each pipeline step to a tier:


| Step                                | Tier  | Note |
| ----------------------------------- | ----- | ---- |
| `p1.pin.import_to_pypi`             | small | |
| `p1.docker.repair_agent`            | big   | |
| `p1.baseline.classify_failure`      | small | |
| `p1.baseline.fix_agent`             | big   | |
| `p1.testgen.write_tests_agent`      | big   | |
| `p1.testgen.mutation_retry_agent`   | big   | |
| `p1.lint.fix_unfixable`             | big   | defined, never invoked -- lint records per-line `noqa` instead of calling an LLM |
| `p2.okf.module_purpose`             | big   | |
| `p2.okf.function_contracts`         | big   | |
| `p3.history.classify_commit`        | small | |
| `p3.excision.screen_candidate`      | small | |
| `p3.netnew.propose_features`        | big   | defined, never invoked -- net-new tasks were not built |
| `p3.build.verifier_agent`           | big   | |
| `p3.build.neutrality_check_rewrite` | big   | |
| `p3.build.netnew_impl_agent`        | big   | defined, never invoked -- net-new tasks were not built |
| `p3.build.write_instruction`        | big   | |
| `p3.build.review_instruction`       | big   | |
| `p3.build.golden_rationale`         | big   | |
| `p3.build.difficulty_label`         | big   | |
| `report.draft_sections`             | big   | |


## LLM (`llm.`*)


| Key                           | Default           | Type   | Meaning                                                   | When to change                                          |
| ----------------------------- | ----------------- | ------ | --------------------------------------------------------- | ------------------------------------------------------- |
| `temperature`                 | 0.0               | tuning | Sampling temperature for all calls                        | Raise for more diverse test generation                  |
| `max_schema_retries`          | 3                 | tuning | Retries when schema validation fails client-side          | Raise if the endpoint frequently returns malformed JSON |
| `accept_fenced_json_fallback` | true              | policy | Parse fenced JSON from text if tool-call extraction fails | Disable to enforce strict tool-call compliance          |
| `api_max_retries`             | 5                 | tuning | Retries with exponential backoff on API errors            | Raise for unreliable endpoints                          |
| `api_backoff_base_s`          | 1.0               | tuning | Base delay for exponential backoff                        |                                                         |
| `request_timeout_s`           | 300               | tuning | Per-request timeout                                       | Raise for slow endpoints                                |
| `disk_cache`                  | false             | tuning | Prompt-to-response disk cache (`--llm-cache`)             | Enable during development for faster iteration          |
| `disk_cache_dir`              | `.llm_cache`      | policy | Cache directory                                           |                                                         |
| `max_tokens_per_repo`         | 5,000,000         | tuning | Per-repo token budget; aborts when exceeded               | Lower to cap cost per repo                              |
| `classify_batch_size`         | 15                | tuning | Commits or excision candidates per SMALL-model call       |                                                         |
| `okf_module_chunk_tokens`     | 12,000            | tuning | Modules larger than this are chunked by class/function    |                                                         |
| `big_max_tokens`              | 8,192             | tuning | Output token ceiling for BIG calls (includes thinking)    |                                                         |
| `small_max_tokens`            | 2,048             | tuning | Output token ceiling for SMALL calls                      |                                                         |
| `cassette_dir`                | `tests/cassettes` | policy | Record/replay fixture directory                           |                                                         |


## Agent (`agent.*`)


| Key                          | Default | Type   | Meaning                                                               | When to change               |
| ---------------------------- | ------- | ------ | --------------------------------------------------------------------- | ---------------------------- |
| `max_turns`                  | 25      | tuning | Default agent turn cap (overridden per stage)                         |                              |
| `max_tokens_per_tool_result` | 8,000   | tuning | Tool results are truncated to this                                    | Raise if agents miss context |
| `chars_per_token`            | 4       | policy | Approximate chars-per-token for truncation budget                     |                              |
| `grep_max_matches`           | 100     | tuning | Maximum grep matches returned to the model                            |                              |
| `run_tool_timeout_s`         | 600     | tuning | Per-command timeout for the `run` tool                                |                              |
| `docker_repair_max_attempts` | 3       | tuning | Build-repair agent iterations                                         |                              |
| `baseline_fix_max_attempts`  | 1       | tuning | Baseline-fix agent iterations. Never fired on glom (all tests passed) |                              |
| `testgen_max_retries`        | 2       | tuning | Retries with mutant feedback per module                               |                              |


## Docker (`docker.*`)


| Key                          | Default                                       | Type   | Meaning                                          |
| ---------------------------- | --------------------------------------------- | ------ | ------------------------------------------------ |
| `image_name_prefix`          | `bench-`                                      | policy | Image tag prefix: `bench-<repo>`                 |
| `base_image`                 | `python:{py}-slim`                            | policy | Base image template, digest-pinned at build time |
| `pin_base_image_digest`      | true                                          | policy | Resolve and pin the base image digest            |
| `network_none_for_runs`      | true                                          | policy | `--network none` for all test/verifier runs      |
| `default_cmd_timeout_s`      | 900                                           | tuning | Per-command timeout inside containers            |
| `harness_parallel_workers`   | 4                                             | tuning | ThreadPool workers for parallel validation       |
| `compose_supported_services` | `(postgres, redis)`                           | policy | Services the compose template supports           |
| `compose_service_images`     | `{postgres: postgres:16.4, redis: redis:7.4}` | policy | Pinned service images                            |


## Detection (`detect.*`)


| Key                      | Default                                                                                                                                                                                    | Type   | Meaning                                                         | Glom                               |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------ | --------------------------------------------------------------- | ---------------------------------- |
| `supported_ecosystems`   | `(python,)`                                                                                                                                                                                | policy | Only Python behind EcosystemAdapter                             | fired                              |
| `python_version_cap`     | `3.12`                                                                                                                                                                                     | policy | Maximum Python version chosen. 3.12 has the best wheel coverage | fired: capped from classifiers     |
| `python_version_default` | `3.12`                                                                                                                                                                                     | policy | Fallback when no version info                                   |                                    |
| `manifest_markers`       | pyproject.toml, setup.py, setup.cfg, requirements.in, requirements.txt                                                                                                                     | policy | Files checked in priority order                                 | fired: setup.py detected           |
| `import_alias_table`     | yaml->PyYAML, cv2->opencv-python, PIL->Pillow, sklearn->scikit-learn, bs4->beautifulsoup4, dateutil->python-dateutil, attr->attrs, dotenv->python-dotenv, jwt->PyJWT, Crypto->pycryptodome | policy | Import-to-PyPI mappings for no-manifest repos                   | never fired on glom (has manifest) |
| `test_tools`             | `(pytest, coverage, pytest-json-report)`                                                                                                                                                   | policy | Always added to the lock                                        | fired                              |
| `dev_tools`              | `(ruff,)`                                                                                                                                                                                  | policy | Always added to the lock                                        | fired                              |
| `service_import_signals` | psycopg2->postgres, asyncpg->postgres, redis->redis, pymongo->mongo, celery->broker, kombu->broker                                                                                         | policy | Import-to-service mapping for compose detection                 | never fired on glom                |
| `service_env_signals`    | `(DATABASE_URL, REDIS_URL)`                                                                                                                                                                | policy | Env vars checked for service detection                          | never fired on glom                |
| `git_version_tools`      | setuptools-git-versioning, setuptools_scm, setuptools-scm, hatch-vcs, versioneer, dunamai, pdm-backend                                                                                     | policy | Build tools that need `.git` + git in the image                 | fired on toolz, not glom           |


## Pinning (`pin.*`)


| Key                        | Default                       | Type   | Meaning                                                                         |
| -------------------------- | ----------------------------- | ------ | ------------------------------------------------------------------------------- |
| `resolver`                 | `uv`                          | policy | `uv pip compile`                                                                |
| `generate_hashes`          | true                          | policy | `--generate-hashes` for supply-chain verification                               |
| `emit_constraints_txt`     | true                          | policy | Also emit constraints.txt (hashes stripped)                                     |
| `lock_filename`            | `requirements.lock.txt`       | policy | Output lockfile name                                                            |
| `requirements_in_filename` | `pipeline-requirements.in`    | policy | Pipeline-owned; never overwrites repo's own file                                |
| `constraints_filename`     | `constraints.txt`             | policy | Constraints file name                                                           |
| `include_extras`           | `(test, tests, testing, dev)` | tuning | Manifest extras folded into the lock. Retried without on failure                |
| `alias_reask_attempts`     | 1                             | tuning | SMALL-model re-asks for PyPI names on unresolvable imports. Never fired on glom |


## Baseline (`baseline.*`)


| Key                       | Default                                                                                                                                  | Type   | Meaning                                                                                           |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------- |
| `framework_priority`      | `(pytest, unittest)`                                                                                                                     | policy | Detection order                                                                                   |
| `quarantine_file`         | `tests/quarantine.txt`                                                                                                                   | policy | `--deselect` list                                                                                 |
| `report_filename`         | `.pytest-report.json`                                                                                                                    | policy | pytest-json-report output, read from workdir                                                      |
| `agent_fix_allowed_globs` | tests/, test/, conftest.py, Dockerfile, .dockerignore, requirements.in, requirements.lock.txt, constraints.txt, pipeline-requirements.in | policy | Agent-fix may only edit these; edits outside are reverted. Never fired on glom (all tests passed) |


## Test generation (`testgen.*`)


| Key                           | Default                                                                                                           | Type   | Meaning                                                                                         | Glom                                       |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------- | ------ | ----------------------------------------------------------------------------------------------- | ------------------------------------------ |
| `top_k_modules`               | 5                                                                                                                 | tuning | Modules ranked for generation                                                                   | fired: 4 modules met threshold             |
| `top_n_functions_per_module`  | 6                                                                                                                 | tuning | Functions per module passed to agent                                                            |                                            |
| `min_function_lines`          | 3                                                                                                                 | tuning | Functions shorter than this are skipped                                                         |                                            |
| `complexity_weight`           | 5.0                                                                                                               | tuning | `(1 + complexity/5)` in the ranking score                                                       |                                            |
| `public_bonus`                | 1.5                                                                                                               | tuning | Public functions score 1.5x                                                                     |                                            |
| `private_min_complexity`      | 5                                                                                                                 | tuning | `_private` only included if complexity >= this                                                  |                                            |
| `skip_dunder`                 | true                                                                                                              | policy | Skip `__init_`_, `__repr__`, etc.                                                               |                                            |
| `skip_init_reexports`         | true                                                                                                              | policy | Skip functions in `__init__.py`                                                                 |                                            |
| `skip_cli_main`               | true                                                                                                              | policy | Skip CLI main() functions                                                                       |                                            |
| `generated_tests_dir`         | `tests/generated`                                                                                                 | policy | Default output directory                                                                        |                                            |
| `example_tests_in_prompt`     | 2                                                                                                                 | tuning | Existing tests shown for style                                                                  |                                            |
| `mutants_per_function`        | 4                                                                                                                 | tuning | AST mutants injected per target function                                                        | fired: 14/16 mutants killed                |
| `min_mutants_killed`          | 1                                                                                                                 | policy | Minimum kills to keep tests. Gate = at least 1 test failed with collection intact               | fired                                      |
| `mutators`                    | comparison_flip, comparison_boundary, arithmetic_swap, and_or_swap, return_none, constant_tweak, statement_delete | policy | AST mutation operators                                                                          | fired                                      |
| `enabled`                     | true                                                                                                              | policy | `--no-testgen` disables                                                                         |                                            |
| `place_beside_existing_tests` | true                                                                                                              | tuning | Place generated tests next to existing ones                                                     |                                            |
| `generated_subdir`            | `generated`                                                                                                       | policy | Subdir name for generated tests                                                                 |                                            |
| `max_agent_runs_per_repo`     | 10                                                                                                                | tuning | Total agent runs across all modules. Caps the token cost of exploring large modules             | fired                                      |
| `agent_max_turns`             | 12                                                                                                                | tuning | Per-agent turn cap. A 30-turn attempt on glom.core still produced nothing, so 12 stays | fired on glom.core (`testgen.json` records `stopped: reached max turns`); glom.grouping is also `dropped_no_file` but with an empty summary |
| `mutant_timeout_s`            | 120                                                                                                               | tuning | A mutant run past this is treated as not-a-kill                                                 |                                            |
| `run_output_chars`            | 2,000                                                                                                             | tuning | Agent-visible tail of a failed test run                                                         |                                            |
| `example_test_chars`          | 1,500                                                                                                             | tuning | Per existing test shown for style                                                               |                                            |
| `summary_chars`               | 500                                                                                                               | tuning | Persisted agent summary                                                                         |                                            |


## Lint (`lint.*`)


| Key                        | Default               | Type   | Meaning                                  |
| -------------------------- | --------------------- | ------ | ---------------------------------------- |
| `enabled`                  | true                  | policy | `--no-lint` disables                     |
| `rules`                    | `(E, F, W, I, B, UP)` | policy | Ruff rule sets                           |
| `autofix`                  | true                  | policy | `ruff check --fix`                       |
| `format`                   | true                  | policy | `ruff format` alongside check            |
| `allow_noqa_for_unfixable` | true                  | policy | Per-line `# noqa` for unfixable findings |


## Graph (`graph.*`)


| Key                             | Default                                            | Type   | Meaning                                                                                |
| ------------------------------- | -------------------------------------------------- | ------ | -------------------------------------------------------------------------------------- |
| `edge_types`                    | imports, contains, calls, inherits, tested_by      | policy | Edge types in the graph                                                                |
| `resolve_calls_intra_repo_only` | true                                               | policy | Only resolve calls to intra-repo symbols                                               |
| `verification_sample_edges`     | 200                                                | tuning | Edges sampled for self-verification                                                    |
| `diversity_unit`                | `file`                                             | tuning | `file` for small repos, `subpackage` for large                                         |
| `large_repo_module_threshold`   | 200                                                | tuning | Switch to subpackage diversity above this                                              |
| `complexity_metric`             | `branch_count`                                     | policy | Internal McCabe counter, no external dependency                                        |
| `test_dir_names`                | `(test, tests)`                                    | policy | Directories treated as test code                                                       |
| `test_file_globs`               | `(test_*.py, *_test.py)`                           | policy | Glob patterns for test files                                                           |
| `nonsource_files`               | `(setup.py,)`                                      | policy | Excluded from graph nodes                                                              |
| `nonsource_dirs`                | docs, doc, examples, example, scripts, build, dist | policy | Excluded from source. Changed after `docs/conf.py` was indexed as source on early runs |


## Knowledge (`knowledge.*`)


| Key                      | Default                    | Type   | Meaning                                          |
| ------------------------ | -------------------------- | ------ | ------------------------------------------------ |
| `coveragerc_filename`    | `.coveragerc-knowledge`    | policy | Pipeline-owned, does not clobber repo's          |
| `coverage_json_filename` | `.knowledge-coverage.json` | policy | In-container coverage output                     |
| `ctx_plugin_module`      | `_kn_ctx_plugin`           | policy | Per-test coverage context plugin                 |
| `graph_filename`         | `repo_graph.json`          | policy |                                                  |
| `symbols_filename`       | `symbol_index.json`        | policy |                                                  |
| `history_filename`       | `history_index.json`       | policy |                                                  |
| `test_map_filename`      | `test_map.json`            | policy |                                                  |
| `coverage_filename`      | `coverage.json`            | policy |                                                  |
| `hotspots_filename`      | `hotspots.json`            | policy |                                                  |
| `verification_filename`  | `graph_verification.json`  | policy |                                                  |
| `pr_number_regex`        | `(?:GH-\|#)(\d+)`          | policy | PR number extraction from commit subjects        |
| `source_roots`           | `(src,)`                   | policy | src-layout roots stripped from module names      |
| `show_commit_max_chars`  | 4,000                      | tuning | Output cap for the `show_commit` tool            |
| `code_fingerprint_files` | (see config.py)            | policy | Pipeline files hashed into knowledge step inputs |


## OKF (`okf.*`)


| Key                           | Default                                                                                                    | Type   | Meaning                                                                                                   | Glom                   |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------- | ------ | --------------------------------------------------------------------------------------------------------- | ---------------------- |
| `enabled`                     | true                                                                                                       | policy |                                                                                                           | fired                  |
| `okf_version`                 | `0.2`                                                                                                      | policy | OKF spec version                                                                                          |                        |
| `max_function_pages`          | 150                                                                                                        | tuning | Cap on individual function pages                                                                          | fired: 164 total pages |
| `function_page_selector`      | `public_or_top_complexity`                                                                                 | policy | Which functions get their own page                                                                        |                        |
| `min_private_page_complexity` | 2                                                                                                          | tuning | Private/dunder below this are summarized only                                                             | fired                  |
| `generated_by_actor`          | `pipeline/{model}`                                                                                         | policy | Provenance actor string                                                                                   |                        |
| `verifier_actor`              | `process:okf-verifier`                                                                                     | policy |                                                                                                           |                        |
| `unverified_status`           | `draft`                                                                                                    | policy | Status for pages with no verified claims                                                                  |                        |
| `verified_status`             | `stable`                                                                                                   | policy | Status for pages with >=1 verified claim. Changed: was any-claim, now requires at least one check to pass |                        |
| `side_effect_call_names`      | open, print, write, writelines, remove, unlink, mkdir, system, popen, run, request, urlopen, connect, send | policy | Names that count as IO/mutation side effects                                                              | fired                  |


## History funnel (`history.*`)


| Key                                 | Default                                            | Type   | Meaning                                                           | Glom                               |
| ----------------------------------- | -------------------------------------------------- | ------ | ----------------------------------------------------------------- | ---------------------------------- |
| `min_source_lines_changed`          | 3                                                  | tuning | Commits with fewer changed lines are rejected                     | fired: 64 too-small                |
| `max_source_lines_changed`          | 300                                                | tuning |                                                                   | fired: 8 too-large                 |
| `max_source_files_changed`          | 6                                                  | tuning |                                                                   |                                    |
| `require_coverage_or_added_tests`   | true                                               | policy |                                                                   | fired: 135 uncovered-and-no-tests  |
| `reject_manifest_changes`           | true                                               | policy |                                                                   | fired: 97 dependency-changing      |
| `ignore_paths`                      | docs/, .md, .rst, .github/, CHANGELOG, _version.py | policy |                                                                   | fired: 136 docs-or-ci-only         |
| `fix_keyword_regex`                 | `fix\|bug\|GH-\d+\|...`                            | tuning | Keywords that boost a commit's score                              |                                    |
| `score_fix_keyword`                 | 1.0                                                | tuning |                                                                   |                                    |
| `score_adds_tests`                  | 2.0                                                | tuning |                                                                   |                                    |
| `score_public_fn`                   | 1.0                                                | tuning |                                                                   |                                    |
| `score_single_function`             | 1.0                                                | tuning |                                                                   |                                    |
| `score_module_diversity`            | 0.5                                                | tuning |                                                                   |                                    |
| `score_reverted_penalty`            | -3.0                                               | tuning |                                                                   |                                    |
| `keep_kinds`                        | `(bugfix, feature)`                                | policy | Classifier labels kept. Rejects refactor, chore, test-only        | fired: 17 classified_out           |
| `shortlist_size`                    | 20                                                 | tuning |                                                                   | fired                              |
| `build_target`                      | 10                                                 | tuning | Tasks to build; headroom for select                               | fired: 9 built                     |
| `pr_merge_input_is_first_parent`    | true                                               | policy | PR merge: input/ uses first parent                                |                                    |
| `reject_non_pr_merges`              | true                                               | policy | Non-PR merges diff against arbitrary parents                      | fired: 39                          |
| `reject_root_commits`               | true                                               | policy | No parent = no input/ tree                                        | fired: 1                           |
| `prefer_pr_merge_over_constituents` | true                                               | policy | Merge supersedes its constituent commits                          | fired: 37                          |
| `reject_reverted`                   | true                                               | policy | Reverted commits dropped via revert message + reverse patch-id    |                                    |
| `classify_diff_max_chars`           | 3,000                                              | tuning | Diff shown to the SMALL classifier                                |                                    |
| `classify_max_commits`              | 60                                                 | tuning | Stop classifying after this many                                  |                                    |
| `reuse_classify_decisions`          | true                                               | policy | Decisions persist by content hash                                 |                                    |
| `neutrality_check`                  | true                                               | policy | BIG checks verifier tests for implementation-specificity          | fired                              |
| `neutrality_rewrite_max_attempts`   | 1                                                  | tuning | Bounded rewrite attempts                                          |                                    |
| `max_agent_runs_per_repo`           | 6                                                  | tuning | BIG agent budget. Added after a 25-turn rewrite cost ~150k tokens | fired                              |
| `max_neutrality_rewrites_per_repo`  | 2                                                  | tuning | Beyond this, reject on flag. Added with agent budgets             |                                    |
| `agent_max_turns`                   | 12                                                 | tuning | BIG turns are expensive; 12 bounds a single verifier/rewrite agent                          | fired                              |
| `allow_new_symbol_features`         | true                                               | policy | New-API features verified via getattr convention                  | observed during development on toolz (no artifacts committed); applicable on glom |
| `verifier_agent_when_no_tests`      | true                                               | policy | BIG writes verifier when commit adds no tests                     |                                    |
| `verifier_agent_max_attempts`       | 1                                                  | tuning |                                                                   |                                    |
| `collateral_baseline_from_input`    | true                                               | policy | Collateral baseline = tests passing on input/                     |                                    |
| `reuse_agent_outputs`               | true                                               | policy | Verifier files cached by content hash                             |                                    |


## Excision funnel (`excision.*`)


| Key                               | Default                                | Type   | Meaning                                                                                   | Glom                         |
| --------------------------------- | -------------------------------------- | ------ | ----------------------------------------------------------------------------------------- | ---------------------------- |
| `min_covering_tests`              | 2                                      | tuning | Minimum passing baseline tests covering the function                                      | fired: 27 few-covering-tests |
| `max_covering_tests`              | 40                                     | tuning | Excising central code fails the whole suite. Added after glom's `get_handler` (112 tests) | fired: 7 too-central         |
| `min_lines`                       | 8                                      | tuning |                                                                                           | fired: 21 too-short          |
| `max_lines`                       | 80                                     | tuning |                                                                                           |                              |
| `min_complexity`                  | 3                                      | tuning |                                                                                           | fired: 15 low-complexity     |
| `public_only`                     | true                                   | policy |                                                                                           | fired: 196 private           |
| `require_public_parent`           | true                                   | policy | Method on `_Private` class is not public API                                              | fired: 8 private-parent      |
| `skip_init_modules`               | true                                   | policy | **init**.py re-export shims                                                               |                              |
| `min_assertions_touching_fn`      | 3                                      | tuning | Below this, agent adds edge-case tests                                                    |                              |
| `excision_body`                   | `raise NotImplementedError("excised")` | policy | Replacement body                                                                          |                              |
| `strip_docstring`                 | false                                  | policy | `--excision-hard` strips docstrings. Never fired (default)                                |                              |
| `build_target`                    | 5                                      | tuning | Tasks to build                                                                            | fired                        |
| `reject_private_verifier_imports` | true                                   | policy | Pre-gate before any LLM spend                                                             |                              |
| `rank_module_round_robin`         | true                                   | policy | Diversity via round-robin over modules                                                    |                              |
| `copy_conftests`                  | true                                   | policy | Copy conftest ancestors so fixtures resolve                                               |                              |


## Net-new (`netnew.`*)

Net-new tasks were cut by decision (history + excision yield >10 VALID).
These defaults are present but never fired.


| Key                      | Default | Type   |
| ------------------------ | ------- | ------ |
| `max_tests`              | 5       | tuning |
| `max_solution_lines`     | 60      | tuning |
| `prefer_existing_module` | true    | policy |
| `proposals_per_module`   | 2       | tuning |
| `build_target`           | 3       | tuning |
| `validated_target`       | 2       | tuning |


## Harness (`harness.*`)


| Key                                                | Default                                                                                                                                                                          | Type   | Meaning                                                                            | Glom                               |
| -------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ---------------------------------------------------------------------------------- | ---------------------------------- |
| `determinism_runs`                                 | 3                                                                                                                                                                                | tuning | Repeat count for determinism check                                                 | fired                              |
| `strict_fail_reason`                               | true                                                                                                                                                                             | policy | Enforce valid/invalid reason lists                                                 | fired: caught the CLI wrapper case |
| `valid_fail_reasons`                               | AssertionError, pytest.raises, NotImplementedError, exception_in_repo_code                                                                                                       | policy | Accepted fail reasons                                                              |                                    |
| `invalid_fail_reasons`                             | ImportError, ModuleNotFoundError, SyntaxError, AttributeError@import, collection_error, collected_0_items, fixture_not_found, error_before_repo_call, no_failing_test, no_report | policy | Rejection reasons                                                                  | fired: error_before_repo_call      |
| `run_collateral_for_excision`                      | true                                                                                                                                                                             | policy | Run broader suite on solution/                                                     |                                    |
| `recopy_canonical_verifier`                        | true                                                                                                                                                                             | policy | Re-copy verifier/ before each run (hack-proof)                                     | fired                              |
| `verifier_may_only_import_public_symbols_in_input` | true                                                                                                                                                                             | policy | Static gate on verifier imports                                                    |                                    |
| `verifier_visibility`                              | `visible`                                                                                                                                                                        | policy | `--verifier-visibility visible\|hidden`. Never changed from default                 |                                    |
| `min_failing_tests`                                | 1                                                                                                                                                                                | tuning | `--min-failing-tests`. At least this many tests must fail on input/                | fired                              |
| `build_image_if_missing`                           | false                                                                                                                                                                            | policy | Build from task's own Dockerfile if image tag not found. Never fired (default off) |                                    |
| `gate_on_image_digest`                             | false                                                                                                                                                                            | policy | Reject on image digest mismatch. Never fired (default off)                         |                                    |


## Tasks layout (`tasks.*`)


| Key                      | Default                                                                                     | Type   |
| ------------------------ | ------------------------------------------------------------------------------------------- | ------ |
| `tasks_root`             | `tasks`                                                                                     | policy |
| `manifest_filename`      | `tasks.json`                                                                                | policy |
| `task_json`              | `task.json`                                                                                 | policy |
| `golden_solution`        | `goldenSolution.md`                                                                         | policy |
| `verifier_run_script`    | `run.sh`                                                                                    | policy |
| `excision_id_prefix`     | `exc`                                                                                       | policy |
| `history_id_prefix`      | `hist`                                                                                      | policy |
| `tree_ignore`            | .git, pycache, .egg-info, .pytest_cache                                                     | policy |
| `hygiene_overlay_files`  | Dockerfile, .dockerignore, requirements.lock.txt, pipeline-requirements.in, constraints.txt | policy |
| `code_fingerprint_files` | (see config.py)                                                                             | policy |


## Instruction (`instruction.*`)


| Key                                | Default | Type   | Meaning                                                                      | Glom             |
| ---------------------------------- | ------- | ------ | ---------------------------------------------------------------------------- | ---------------- |
| `show_diff_to_author`              | false   | policy | The instruction author never sees the diff                                   |                  |
| `leak_min_tokens`                  | 5       | tuning | Diff lines with >= this many tokens must not appear in instruction           | fired            |
| `forbid_new_identifiers_from_diff` | true    | policy | New identifiers from diff must not appear                                    | fired            |
| `examples_from_verifier`           | 2       | tuning | Verifier tests shown to the author                                           |                  |
| `max_regenerations`                | 2       | tuning | Retries on leak/review failure                                               | 0 needed on glom |
| `title_max_chars`                  | 80      | tuning | Task title truncation                                                        |                  |
| `leak_min_identifier_chars`        | 3       | tuning | Shorter new identifiers are too generic to gate                              |                  |
| `leak_api_names_only`              | true    | policy | Only gate API-like names, not locals/params. Added to reduce false positives |                  |
| `exempt_diff_lines_in_tests`       | true    | policy | Diff lines also in verifier tests are exempt (solver sees them anyway)       |                  |
| `tests_max_chars`                  | 12,000  | tuning | Verifier test source shown to author/reviewer                                |                  |
| `diff_max_chars`                   | 8,000   | tuning | Diff shown to golden-rationale prompt (the only call that sees it)           |                  |


## Difficulty (`difficulty.*`)


| Key                               | Default                                                                                                                    | Type   | Meaning                                                                                         | Glom                   |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ------ | ----------------------------------------------------------------------------------------------- | ---------------------- |
| `features`                        | files_touched, functions_touched, callers_count, cross_module_edges, diff_size, similar_named_functions_nearby, test_count | policy | Features computed from graph and diff                                                           | fired                  |
| `justification_must_cite_feature` | true                                                                                                                       | policy | Rationale must cite a feature by name=value                                                     | fired: 0 cite failures |
| `max_regenerations`               | 1                                                                                                                          | tuning | Retry if rationale lacks a cited feature                                                        |                        |
| `batch_size`                      | 10                                                                                                                         | tuning | Tasks per BIG call                                                                              |                        |
| `similar_name_min_token_chars`    | 3                                                                                                                          | tuning | Name tokens shorter than this are not counted as similar                                        |                        |
| `target_spread`                   | easy=2, medium=5, hard=3                                                                                                   | tuning | Soft objective for selection. Glom achieved easy=5, medium=4, hard=1 (eligible pool skews easy) |                        |


## Selection (`selection.*`)


| Key                    | Default | Type   | Meaning                                                           | Glom              |
| ---------------------- | ------- | ------ | ----------------------------------------------------------------- | ----------------- |
| `total_tasks`          | 10      | policy | Exactly this many selected                                        | fired             |
| `min_history`          | 4       | policy | Hard minimum history tasks                                        | fired: 6 selected |
| `max_excision`         | 4       | policy | Hard maximum excision tasks                                       | fired: 4 selected |
| `max_netnew`           | 2       | policy | Hard maximum net-new tasks. Changed from 3 (PDF) to 2 by decision | 0 (cut)           |
| `min_distinct_modules` | 4       | policy | Hard minimum distinct modules                                     | fired: 4 modules  |


## Report (`report.*`)


| Key                    | Default               | Type   | Meaning                                                             |
| ---------------------- | --------------------- | ------ | ------------------------------------------------------------------- |
| `report_md_filename`   | `REPORT.md`           | policy | Output filename under `output/<repo>/`                              |
| `report_data_filename` | `report_data.json`    | policy | Runner's per-stage file (read only)                                 |
| `summary_filename`     | `report_summary.json` | policy | Aggregate output                                                    |
| `draft_narrative`      | true                  | policy | One BIG call to draft narrative sections. `--no-report-draft` skips |
| `draft_max_chars`      | 6,000                 | tuning | Compact data summary shown to the drafter                           |




## Appendix: filenames and bookkeeping keys

The keys below are artifact names, status strings, prompt-size caps and
bookkeeping flags. They are rarely worth changing, but they are keys, so they
are listed here to keep "every key" true. Defaults are as in `config.py`.


| Key                                                | Default                             | Meaning                                                                   |
| -------------------------------------------------- | ----------------------------------- | ------------------------------------------------------------------------- |
| `testgen.targets_filename`                         | `testgen_targets.json`              | Ranked target functions, under `output/<repo>/hygiene/`                   |
| `testgen.results_filename`                          | `testgen.json`                      | Per-module outcome and mutation counts                                    |
| `testgen.decisions_filename`                        | `testgen_decisions.json`            | Agent decisions cached by content hash                                    |
| `testgen.lock_filename`                             | `.testgen.lock`                     | Marker that keeps a single test-gen run per tree                          |
| `testgen.commit_label`                              | `pipeline: generated tests`         | Message of the pipeline commit that lands generated tests                 |
| `knowledge.coverage_contexts_filename`              | `coverage_contexts.json`            | Per-test coverage contexts feeding `test_map.json`                        |
| `knowledge.manifest_name_prefixes`                  | `(requirements,)`                   | Filename prefixes treated as dependency manifests when reading history    |
| `okf.bundle_dirname`                                | `.okf`                              | Bundle directory under `output/<repo>/knowledge/`                         |
| `okf.manifest_filename`                             | `okf.json`                          | Page manifest and counts                                                  |
| `okf.verification_filename`                         | `okf_verification.json`             | Re-derived claim checks and per-claim precision                           |
| `okf.decisions_filename`                            | `okf_decisions.json`                | Contract-authoring decisions cached by content hash                       |
| `history.revert_message_regex`                      | `^Revert\b\|This reverts commit ...`| Detects reverted commits so they are rejected                             |
| `history.prompt_new_names_max`                      | 20                                  | New identifiers listed to the neutrality-rewrite agent                    |
| `history.neutrality_recheck_after_rewrite`          | true                                | Re-run the neutrality check on a rewritten verifier                       |
| `history.agent_test_file_prefix`                    | `test_hist_`                        | Prefix for verifier files an agent writes for a history task              |
| `history.agent_diff_max_chars`                      | 6,000                               | Diff budget in a history agent prompt                                     |
| `excision.verifier_agent_max_attempts`              | 1                                   | Verifier-agent attempts per excision candidate                            |
| `excision.reuse_screen_decisions`                   | true                                | Reuse cached SMALL screening verdicts across runs                         |
| `harness.evidence_dirname`                          | `evidence`                          | Evidence directory inside a task folder                                   |
| `harness.fail_before_log`                           | `fail_before.log`                   | Console log of the fail-before run                                        |
| `harness.pass_after_log`                            | `pass_after.log`                    | Console log of the pass-after run                                         |
| `harness.collateral_log`                            | `collateral.log`                    | Console log of the collateral run                                         |
| `harness.raw_report_suffix`                         | `.report.json`                      | Suffix pairing each log with its pytest JSON report                       |
| `harness.report_filename`                           | `.pytest-report.json`               | In-container pytest JSON report name                                      |
| `harness.determinism_filename`                      | `determinism.json`                  | Repeat-run comparison                                                     |
| `harness.collateral_filename`                       | `collateral.json`                   | Collateral-damage comparison                                              |
| `harness.verdict_filename`                          | `verdict.json`                      | Final per-task verdict                                                    |
| `tasks.candidates_filename`                         | `candidates.json`                   | Excision funnel record                                                    |
| `tasks.history_candidates_filename`                 | `history_candidates.json`           | History funnel record                                                     |
| `tasks.instruction_status_template`                 | `template`                          | Builder's placeholder instruction status (excision)                       |
| `tasks.history_instruction_status_template`         | `template`                          | Builder's placeholder instruction status (history)                        |
| `tasks.title_max_chars`                             | 100                                 | Cap on a builder-written task title                                       |
| `tasks.instruction_tests_listed`                    | 12                                  | Verifier node ids listed inside an instruction                            |
| `tasks.audit_goal_chars`                            | 500                                 | Agent goal text kept in the audit record                                  |
| `tasks.audit_summary_chars`                         | 300                                 | Agent summary kept in the audit record                                    |
| `tasks.content_key_chars`                           | 16                                  | Hash prefix length for content-keyed decision caches                      |
| `instruction.only_valid_tasks`                      | true                                | Author instructions for VALID tasks only; INVALID keep their template     |
| `instruction.files_in_scope_include_importers_and_tests` | true                          | "Files in scope" lists importers and tests, not just the changed file     |
| `instruction.status_final`                          | `final`                             | Status written when an instruction passes leak + reviewer gates           |
| `instruction.status_failed`                         | `failed`                            | Status written when it does not                                           |
| `instruction.decisions_filename`                    | `instructions.json`                 | Instruction, difficulty and rationale records, keyed by content hash      |
| `instruction.hidden_phrase`                         | (sentence)                          | Sentence appended when verifier visibility is `hidden`                    |
| `instruction.visible_phrase`                        | (sentence)                          | Sentence appended when verifier visibility is `visible`                   |
| `report.decisions_filename`                         | `report_decisions.json`             | Narrative drafts cached by data-summary hash                              |
| `step_model`                                        | (see STEP_MODEL above)              | Top-level map of pipeline step to model tier                              |
| `hygiene_code_files`                                | (hygiene sources)                   | Top-level list fingerprinted so a hygiene code change invalidates its artifacts |
