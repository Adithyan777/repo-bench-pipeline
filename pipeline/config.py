"""All heuristics, thresholds, flags and defaults. Documented in HEURISTICS.md.

Overridable via ``--set section.key=value``. Env vars: secrets and model IDs only.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Literal

# --- LLM ---

LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "")  # Baseten OpenAI-compatible endpoint
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_MODEL_BIG = os.environ.get("LLM_MODEL_BIG", "moonshotai/Kimi-K2.6")  # Baseten slug; thinking on
LLM_MODEL_SMALL = os.environ.get(
    "LLM_MODEL_SMALL", "deepseek-ai/DeepSeek-V4-Flash-0731"
)  # Baseten slug

Tier = Literal["big", "small"]
Reasoning = Literal["off", "low", "high", "max"]  # normalized; translated per model in llm/

# How each model receives `Reasoning`. GLM rejects values outside {none,high,max};
# Kimi has no reasoning_effort, only a thinking toggle.
MODEL_CAPS: dict[str, dict] = {
    "deepseek-ai/DeepSeek-V4-Flash-0731": {
        "reasoning_param": "reasoning_effort",
        "map": {"off": "none", "low": "low", "high": "high", "max": "max"},
    },
    "zai-org/GLM-5.2": {
        "reasoning_param": "reasoning_effort",
        "map": {"off": "none", "low": "high", "high": "high", "max": "max"},
    },
    "moonshotai/Kimi-K2.6": {
        "reasoning_param": "enable_thinking",  # bool via chat_template_args
        "map": {"off": False, "low": True, "high": True, "max": True},
    },
}

# classification/lookup -> small; authoring/coding/agents/review -> big
STEP_MODEL: dict[str, Tier] = {
    # Pipeline 1
    "p1.pin.import_to_pypi": "small",
    "p1.docker.repair_agent": "big",
    "p1.baseline.classify_failure": "small",
    "p1.baseline.fix_agent": "big",
    "p1.testgen.write_tests_agent": "big",
    "p1.testgen.mutation_retry_agent": "big",
    "p1.lint.fix_unfixable": "big",
    # Pipeline 2
    "p2.okf.module_purpose": "big",
    "p2.okf.function_contracts": "big",
    # Pipeline 3
    "p3.history.classify_commit": "small",
    "p3.excision.screen_candidate": "small",
    "p3.netnew.propose_features": "big",
    "p3.build.verifier_agent": "big",
    "p3.build.neutrality_check_rewrite": "big",
    "p3.build.netnew_impl_agent": "big",
    "p3.build.write_instruction": "big",
    "p3.build.review_instruction": "big",
    "p3.build.golden_rationale": "big",  # goldenSolution.md "why correct" (may see the diff)
    "p3.build.difficulty_label": "big",
    # Report
    "report.draft_sections": "big",
}

# Per tier, translated via MODEL_CAPS.
TIER_REASONING: dict[Tier, Reasoning] = {"small": "low", "big": "high"}


@dataclass
class LLMConfig:
    temperature: float = 0.0
    max_schema_retries: int = 2  # server does not enforce tool schemas
    accept_fenced_json_fallback: bool = True
    api_max_retries: int = 5  # exponential backoff on API errors
    api_backoff_base_s: float = 1.0
    request_timeout_s: int = 300
    disk_cache: bool = False  # --llm-cache
    disk_cache_dir: str = ".llm_cache"
    max_tokens_per_repo: int = 5_000_000  # abort repo when exceeded
    classify_batch_size: int = 15  # commits / excision candidates per small-model call
    okf_module_chunk_tokens: int = 12_000  # chunk modules larger than this by class/function
    # Per-tier output-token ceiling; BIG needs headroom for thinking tokens.
    big_max_tokens: int = 8_192
    small_max_tokens: int = 2_048
    cassette_dir: str = "tests/cassettes"  # record/replay fixtures for tests (LLM_MODE)

    def max_tokens_for(self, tier: Tier) -> int:
        return self.big_max_tokens if tier == "big" else self.small_max_tokens


@dataclass
class AgentConfig:
    max_turns: int = 25
    max_tokens_per_tool_result: int = 8_000
    chars_per_token: int = 4  # approx chars/token for tool-result truncation budget
    grep_max_matches: int = 100  # cap on grep tool matches returned to the model
    run_tool_timeout_s: int = 600  # `run` tool executes only inside the container
    docker_repair_max_attempts: int = 3
    baseline_fix_max_attempts: int = 1  # bounded agent fix of pre-existing failing tests
    testgen_max_retries: int = 2  # retries with mutation feedback


# --- Docker ---


@dataclass
class DockerConfig:
    image_name_prefix: str = "bench-"  # one image per target repo: bench-<repo>
    base_image: str = "python:{py}-slim"  # digest-pinned at build time
    pin_base_image_digest: bool = True
    network_none_for_runs: bool = True  # --network none for all test/verifier runs
    default_cmd_timeout_s: int = 900
    harness_parallel_workers: int = 4  # ThreadPool over docker runs
    compose_supported_services: tuple[str, ...] = ("postgres", "redis")
    compose_service_images: dict[str, str] = field(
        default_factory=lambda: {"postgres": "postgres:16.4", "redis": "redis:7.4"}
    )  # digest-pinned at generation time


# --- Pipeline 1: hygiene ---


@dataclass
class DetectConfig:
    supported_ecosystems: tuple[str, ...] = ("python",)
    python_version_cap: str = "3.12"
    python_version_default: str = "3.12"
    # Files that mark packaging style, in priority order
    manifest_markers: tuple[str, ...] = (
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "requirements.in",
        "requirements.txt",
    )
    # Import-name -> PyPI-name aliases for repos with no manifest (AST inference)
    import_alias_table: dict[str, str] = field(
        default_factory=lambda: {
            "yaml": "PyYAML",
            "cv2": "opencv-python",
            "PIL": "Pillow",
            "sklearn": "scikit-learn",
            "bs4": "beautifulsoup4",
            "dateutil": "python-dateutil",
            "attr": "attrs",
            "dotenv": "python-dotenv",
            "jwt": "PyJWT",
            "Crypto": "pycryptodome",
        }
    )
    # Test/dev tools always added to the lock
    test_tools: tuple[str, ...] = ("pytest", "coverage", "pytest-json-report")
    dev_tools: tuple[str, ...] = ("ruff",)
    # Compose detection signals
    service_import_signals: dict[str, str] = field(
        default_factory=lambda: {
            "psycopg2": "postgres",
            "asyncpg": "postgres",
            "redis": "redis",
            "pymongo": "mongo",
            "celery": "broker",
            "kombu": "broker",
        }
    )
    service_env_signals: tuple[str, ...] = ("DATABASE_URL", "REDIS_URL")
    # Git-derived-version build tools: keep .git in the build context and install git in
    # the image so the version resolves.
    git_version_tools: tuple[str, ...] = (
        "setuptools-git-versioning",
        "setuptools_scm",
        "setuptools-scm",
        "hatch-vcs",
        "versioneer",
        "dunamai",
        "pdm-backend",
    )


@dataclass
class PinConfig:
    resolver: str = "uv"  # `uv pip compile`
    generate_hashes: bool = True
    emit_constraints_txt: bool = True
    lock_filename: str = "requirements.lock.txt"
    # Pipeline-owned name: must NOT collide with a repo's own requirements.in
    requirements_in_filename: str = "pipeline-requirements.in"
    constraints_filename: str = "constraints.txt"
    # Manifest extras to fold into the lock when present (test suites often live here)
    include_extras: tuple[str, ...] = ("test", "tests", "testing", "dev")
    # SMALL-model re-asks for a PyPI name when an inferred import fails to resolve.
    alias_reask_attempts: int = 1


@dataclass
class BaselineConfig:
    framework_priority: tuple[str, ...] = ("pytest", "unittest")
    quarantine_file: str = "tests/quarantine.txt"  # --deselect list
    report_filename: str = ".pytest-report.json"  # pytest-json-report output, read from workdir
    # Agent-fix may only edit these paths; edits outside are reverted and audited.
    agent_fix_allowed_globs: tuple[str, ...] = (
        "tests/**",
        "test/**",
        "conftest.py",
        "Dockerfile",
        ".dockerignore",
        "requirements.in",
        "requirements.lock.txt",
        "constraints.txt",
        "pipeline-requirements.in",
    )


@dataclass
class TestGenConfig:
    top_k_modules: int = 5
    top_n_functions_per_module: int = 6
    min_function_lines: int = 3
    complexity_weight: float = 5.0  # (1 + complexity/5)
    public_bonus: float = 1.5
    private_min_complexity: int = 5  # `_private` only if complexity >= this
    skip_dunder: bool = True
    skip_init_reexports: bool = True
    skip_cli_main: bool = True
    generated_tests_dir: str = "tests/generated"
    example_tests_in_prompt: int = 2  # existing tests shown for style
    mutants_per_function: int = 4
    min_mutants_killed: int = 1
    mutators: tuple[str, ...] = (
        "comparison_flip",
        "comparison_boundary",
        "arithmetic_swap",
        "and_or_swap",
        "return_none",
        "constant_tweak",
        "statement_delete",
    )
    enabled: bool = True  # --no-testgen turns the step into a no-op
    place_beside_existing_tests: bool = True  # else always generated_tests_dir
    generated_subdir: str = "generated"  # subdir name + marker excluded from input hashes
    max_agent_runs_per_repo: int = 10  # write + retry agent runs, all modules
    agent_max_turns: int = 12  # 30 tried on glom.core: agent explored, never wrote
    mutant_timeout_s: int = 120  # a mutant run past this is "invalid", not a kill
    run_output_chars: int = 2000  # agent-visible tail of a failed test run
    example_test_chars: int = 1500  # per existing test shown for style
    summary_chars: int = 500  # persisted agent summary
    targets_filename: str = "testgen_targets.json"
    results_filename: str = "testgen.json"
    decisions_filename: str = "testgen_decisions.json"
    lock_filename: str = ".testgen.lock"
    commit_label: str = "pipeline: generated tests"


@dataclass
class LintConfig:
    # ruff in-container on the hygiene clone only (historical trees are never linted);
    # unfixable findings get a per-file noqa, not an LLM fix.
    enabled: bool = True  # --no-lint turns the step into a no-op
    rules: tuple[str, ...] = ("E", "F", "W", "I", "B", "UP")
    autofix: bool = True
    format: bool = True
    allow_noqa_for_unfixable: bool = True


# --- Pipeline 2: knowledge layer ---


@dataclass
class GraphConfig:
    edge_types: tuple[str, ...] = ("imports", "contains", "calls", "inherits", "tested_by")
    resolve_calls_intra_repo_only: bool = True
    verification_sample_edges: int = 200  # graph self-check sample size
    diversity_unit: str = "file"  # "file" for glom-sized repos, "subpackage" for large
    large_repo_module_threshold: int = 200  # >= this many modules -> subpackage diversity unit
    # In-house branch counter (see ecosystems/symbols.py:_complexity), no radon dependency.
    complexity_metric: str = "branch_count"
    # Test files (indexed separately, never source nodes): under these dirs or matching globs.
    test_dir_names: tuple[str, ...] = ("test", "tests")
    test_file_globs: tuple[str, ...] = ("test_*.py", "*_test.py")
    # Packaging scripts excluded from graph nodes.
    nonsource_files: tuple[str, ...] = ("setup.py",)
    # Non-library dirs. Source = under a package root or source_roots entry, not a test,
    # not under one of these.
    nonsource_dirs: tuple[str, ...] = (
        "docs",
        "doc",
        "examples",
        "example",
        "scripts",
        "build",
        "dist",
    )


@dataclass
class KnowledgeConfig:
    """Pipeline-owned filenames + coverage settings for the P2 static layer."""

    # A small pytest plugin sets the coverage context to each test's nodeid
    # (Coverage.current().switch_context); no pytest-cov dependency.
    coveragerc_filename: str = ".coveragerc-knowledge"  # pipeline-owned; won't clobber repo's
    coverage_json_filename: str = ".knowledge-coverage.json"  # in-container --show-contexts json
    ctx_plugin_module: str = "_kn_ctx_plugin"  # written into the build context, loaded with -p
    # output/<repo>/knowledge/ artifact names
    graph_filename: str = "repo_graph.json"
    symbols_filename: str = "symbol_index.json"
    history_filename: str = "history_index.json"
    test_map_filename: str = "test_map.json"
    coverage_filename: str = "coverage.json"
    coverage_contexts_filename: str = "coverage_contexts.json"  # raw per-line test contexts
    hotspots_filename: str = "hotspots.json"
    verification_filename: str = "graph_verification.json"
    # history index parsing
    pr_number_regex: str = r"(?:GH-|#)(\d+)"  # first match in a commit subject
    manifest_name_prefixes: tuple[str, ...] = ("requirements",)  # + detect.manifest_markers
    # src-layout roots stripped from historical module names (src/pkg/mod.py -> pkg.mod).
    source_roots: tuple[str, ...] = ("src",)
    show_commit_max_chars: int = 4000  # git-fallback output cap in the show_commit tool
    # Pipeline sources fingerprinted into every knowledge step's input hash.
    code_fingerprint_files: tuple[str, ...] = (
        "pipeline/ecosystems/symbols.py",
        "pipeline/knowledge/graph.py",
        "pipeline/knowledge/indexes.py",
        "pipeline/knowledge/verify.py",
        "pipeline/knowledge/runner.py",
        "pipeline/knowledge/okf.py",
        "pipeline/knowledge/okf_verify.py",
    )


@dataclass
class OKFConfig:
    enabled: bool = True  # the shared task-fixture run turns this off (its own cassette stage)
    okf_version: str = "0.2"
    max_function_pages: int = 150
    function_page_selector: str = "public_or_top_complexity"
    min_private_page_complexity: int = 2  # private/dunder fns below this are summarized only
    generated_by_actor: str = "pipeline/{model}"
    verifier_actor: str = "process:okf-verifier"
    unverified_status: str = "draft"
    verified_status: str = "stable"  # a page whose claims all pass verification
    bundle_dirname: str = ".okf"
    verification_filename: str = "okf_verification.json"
    decisions_filename: str = "okf_decisions.json"
    manifest_filename: str = "okf.json"
    # names that count as an IO/mutation side effect when a contract claims "none"
    side_effect_call_names: tuple[str, ...] = (
        "open",
        "print",
        "write",
        "writelines",
        "remove",
        "unlink",
        "mkdir",
        "system",
        "popen",
        "run",
        "request",
        "urlopen",
        "connect",
        "send",
    )


# --- Pipeline 3: tasks ---


@dataclass
class HistoryFunnelConfig:
    min_source_lines_changed: int = 3
    max_source_lines_changed: int = 300
    max_source_files_changed: int = 6
    require_coverage_or_added_tests: bool = True
    reject_manifest_changes: bool = (
        True  # setup.py / requirements* / pyproject -> dependency-changing
    )
    ignore_paths: tuple[str, ...] = (
        "docs/",
        "*.md",
        "*.rst",
        ".github/",
        "CHANGELOG*",
        "*_version.py",
    )
    fix_keyword_regex: str = r"fix|bug|GH-\d+|#\d+|error|incorrect|regression|edge case"
    score_fix_keyword: float = 1.0
    score_adds_tests: float = 2.0
    score_public_fn: float = 1.0
    score_single_function: float = 1.0
    score_module_diversity: float = 0.5
    score_reverted_penalty: float = -3.0
    keep_kinds: tuple[str, ...] = ("bugfix", "feature")
    shortlist_size: int = 20
    build_target: int = 10  # built; headroom so select never lands on exactly 10
    pr_merge_input_is_first_parent: bool = True
    # Non-PR merges (back-merges) diff against an arbitrary first parent -> rejected.
    reject_non_pr_merges: bool = True
    reject_root_commits: bool = True  # no parent -> no input/ tree
    # Constituent commits of a surviving PR merge are superseded by the merge.
    prefer_pr_merge_over_constituents: bool = True
    # Reverted commits (revert message or reverse patch-id) are dropped; when False they
    # only take score_reverted_penalty.
    reject_reverted: bool = True
    revert_message_regex: str = r"^Revert\b|This reverts commit ([0-9a-f]{7,40})"
    # SMALL classifier walks scored survivors in classify_batch_size batches until
    # shortlist_size are kept, at most classify_max_commits. Decisions persist by content hash.
    classify_diff_max_chars: int = 3000
    classify_max_commits: int = 60
    reuse_classify_decisions: bool = True
    # Verifier = the commit's own changed tests, else a bounded BIG agent authors them.
    # Tests passing on input/ are dropped; harness.min_failing_tests must remain.
    neutrality_check: bool = True  # BIG check of the commit's tests (public interface?)
    neutrality_rewrite_max_attempts: int = 1  # bounded agent rewrite when flagged
    # Agent budgets per repo (cached/reused runs do not count).
    max_agent_runs_per_repo: int = 6
    max_neutrality_rewrites_per_repo: int = 2  # beyond -> reject on flag / missing symbol
    prompt_new_names_max: int = 20  # change-introduced identifiers listed in agent prompts
    neutrality_recheck_after_rewrite: bool = True  # one more complete_json on the rewrite
    # New public API may be verified via `getattr(mod, name, None)` (AssertionError on
    # input/ is a right reason); tests that top-level import it go to the rewrite agent.
    allow_new_symbol_features: bool = True
    verifier_agent_max_attempts: int = 1  # bounded agent when the commit has no tests
    verifier_agent_when_no_tests: bool = True
    agent_max_turns: int = 12  # P3 agents (verifier author, rewrite): BIG turns are costly
    agent_test_file_prefix: str = "test_hist_"
    agent_diff_max_chars: int = 6000  # source diff shown to the verifier agent
    # Collateral baseline = tests passing on input/ (HEAD baseline may list tests that
    # do not exist yet there).
    collateral_baseline_from_input: bool = True
    reuse_agent_outputs: bool = True  # verifier files from agents cached by content hash


@dataclass
class ExcisionFunnelConfig:
    min_covering_tests: int = 2  # distinct base test nodeids that PASSED at baseline
    # Excising central dispatch code fails most of the suite -> not a focused task.
    max_covering_tests: int = 40
    min_lines: int = 8  # span = end_line - def line + 1 (decorators excluded)
    max_lines: int = 80
    min_complexity: int = 3
    public_only: bool = True
    require_public_parent: bool = True  # method on a `_Private` class is not public API
    skip_init_modules: bool = True  # functions defined in __init__.py (re-export shims)
    min_assertions_touching_fn: int = 3  # below this, agent adds edge-case tests
    verifier_agent_max_attempts: int = 1  # bounded top-up agent runs per candidate
    excision_body: str = 'raise NotImplementedError("excised")'
    strip_docstring: bool = False  # flag: --excision-hard
    build_target: int = 5
    # Pre-gate: covering tests importing private repo symbols -> rejected before the screen.
    reject_private_verifier_imports: bool = True
    # SMALL screen walks the ranking in classify_batch_size chunks until build_target
    # survive; rest are `surplus`. Decisions persist in candidates.json by content hash.
    reuse_screen_decisions: bool = True
    # Score = covering_tests * complexity; ranked round-robin over modules for diversity.
    rank_module_round_robin: bool = True
    # Verifier test files are copied with their conftest.py ancestors so fixtures resolve.
    copy_conftests: bool = True


@dataclass
class NetNewConfig:
    max_tests: int = 5
    max_solution_lines: int = 60
    prefer_existing_module: bool = True
    proposals_per_module: int = 2
    build_target: int = 3
    validated_target: int = 2


@dataclass
class HarnessConfig:
    determinism_runs: int = 3
    strict_fail_reason: bool = True
    # The classifier may ONLY emit reasons from these two lists (enforced).
    valid_fail_reasons: tuple[str, ...] = (
        "AssertionError",
        "pytest.raises",
        "NotImplementedError",
        "exception_in_repo_code",  # any exception whose traceback passed through repo code
    )
    invalid_fail_reasons: tuple[str, ...] = (
        "ImportError",
        "ModuleNotFoundError",
        "SyntaxError",
        "AttributeError@import",
        "collection_error",
        "collected_0_items",
        "fixture_not_found",
        "error_before_repo_call",
        "no_failing_test",
        "no_report",
    )
    run_collateral_for_excision: bool = True
    recopy_canonical_verifier: bool = True
    verifier_may_only_import_public_symbols_in_input: bool = True
    verifier_visibility: str = "visible"  # flag: --verifier-visibility visible|hidden
    # Valid failure = exception through repo code, or assertion/pytest.raises in the test.
    report_filename: str = ".pytest-report.json"  # json-report written inside the workdir
    min_failing_tests: int = 1  # fail-before must have at least this many failing tests
    # Missing image tag -> build from <task>/input/Dockerfile.
    build_image_if_missing: bool = False
    # Rebuilt images get a new Id even from a pinned Dockerfile -> mismatch reported, not gated.
    gate_on_image_digest: bool = False
    evidence_dirname: str = "evidence"
    fail_before_log: str = "fail_before.log"
    pass_after_log: str = "pass_after.log"
    collateral_log: str = "collateral.log"
    raw_report_suffix: str = ".report.json"  # raw json-report kept next to each log
    determinism_filename: str = "determinism.json"
    collateral_filename: str = "collateral.json"
    verdict_filename: str = "verdict.json"


@dataclass
class TasksConfig:
    """Layout + bookkeeping for the P3 stage (funnels, builders, harness, manifest)."""

    tasks_root: str = "tasks"  # tasks/<repo>/<task_id>/ ; tasks/<repo>/tasks.json
    manifest_filename: str = "tasks.json"
    candidates_filename: str = "candidates.json"  # output/<repo>/tasks/candidates.json
    task_json: str = "task.json"
    golden_solution: str = "goldenSolution.md"
    verifier_run_script: str = "run.sh"
    excision_id_prefix: str = "exc"  # exc-<module>-<func>
    history_id_prefix: str = "hist"  # hist-<sha7>
    history_candidates_filename: str = "history_candidates.json"
    # Trees copied into input/ and solution/ skip these (never .git: tasks are self-contained)
    tree_ignore: tuple[str, ...] = (".git", "__pycache__", "*.egg-info", ".pytest_cache")
    # Builders' structural instruction status; LLM authoring replaces it with status_final.
    instruction_status_template: str = "template"
    history_instruction_status_template: str = "template"
    # Hygiene artifacts overlaid (never overwriting) onto historical trees.
    title_max_chars: int = 100  # task title = first subject line, truncated
    instruction_tests_listed: int = 12  # nodeids listed in the structural instruction
    audit_goal_chars: int = 500  # agent goal excerpt kept in agent_actions.jsonl
    audit_summary_chars: int = 300  # agent summary excerpt kept in agent_actions.jsonl
    content_key_chars: int = 16  # sha256 prefix used as content-hash key
    hygiene_overlay_files: tuple[str, ...] = (
        "Dockerfile",
        ".dockerignore",
        "requirements.lock.txt",
        "pipeline-requirements.in",
        "constraints.txt",
    )
    # Pipeline sources whose contents fingerprint every tasks step's input hash.
    code_fingerprint_files: tuple[str, ...] = (
        "pipeline/tasks/excision.py",
        "pipeline/tasks/build_excision.py",
        "pipeline/tasks/history.py",
        "pipeline/tasks/build_history.py",
        "pipeline/tasks/instruction.py",
        "pipeline/tasks/difficulty.py",
        "pipeline/tasks/harness.py",
        "pipeline/tasks/manifest.py",
        "pipeline/tasks/runner.py",
        "pipeline/tasks/classify.py",
        "pipeline/tasks/select.py",
        "pipeline/ecosystems/source_ops.py",
    )


@dataclass
class InstructionConfig:
    show_diff_to_author: bool = False  # structural leak prevention
    leak_min_tokens: int = 5  # any diff line with >= this many tokens must not appear
    forbid_new_identifiers_from_diff: bool = True
    examples_from_verifier: int = 2
    max_regenerations: int = 2
    files_in_scope_include_importers_and_tests: bool = True
    only_valid_tasks: bool = True  # INVALID tasks keep their template (never selected)
    tests_max_chars: int = 12_000  # verifier test sources shown to author/reviewer
    diff_max_chars: int = 8_000  # golden-rationale prompt (the only LLM call that sees it)
    title_max_chars: int = 80
    leak_min_identifier_chars: int = 3  # shorter new identifiers are too generic to gate
    # Gate (b): API-like names the diff introduces, not locals/params (false positives).
    leak_api_names_only: bool = True
    # Gate (a) exempts diff lines that also appear in the verifier tests (solver sees them).
    exempt_diff_lines_in_tests: bool = True
    status_final: str = "final"
    status_failed: str = "failed"
    decisions_filename: str = "instructions.json"  # output/<repo>/tasks/, keyed by content hash
    hidden_phrase: str = (
        "Hidden tests check the behavior described above; the instruction carries the "
        "full contract."
    )
    visible_phrase: str = "The verifier tests are in `verifier/` and are re-applied before judging."


@dataclass
class DifficultyConfig:
    features: tuple[str, ...] = (
        "files_touched",
        "functions_touched",
        "callers_count",
        "cross_module_edges",
        "diff_size",
        "similar_named_functions_nearby",
        "test_count",
    )
    justification_must_cite_feature: bool = True
    max_regenerations: int = 1  # rationale without a cited feature -> regenerate once, then fail
    batch_size: int = 10  # tasks labelled per BIG call
    similar_name_min_token_chars: int = 3  # name tokens shorter than this do not count as similar
    target_spread: dict[str, int] = field(
        default_factory=lambda: {"easy": 2, "medium": 5, "hard": 3}
    )


@dataclass
class SelectionConfig:
    total_tasks: int = 10
    min_history: int = 4
    max_excision: int = 4
    max_netnew: int = 2  # assignment allows up to 3
    min_distinct_modules: int = 4


@dataclass
class ReportConfig:
    # report_data.json (runner, per stage) is read only; the aggregate goes to report_summary.json.
    report_md_filename: str = "REPORT.md"  # under output/<repo>/; root REPORT.md is hand-maintained
    report_data_filename: str = "report_data.json"  # the runner's per-stage file (input only)
    summary_filename: str = "report_summary.json"  # the report's aggregate (output)
    decisions_filename: str = "report_decisions.json"  # output/<repo>/, drafts cached by hash
    draft_narrative: bool = True  # one BIG report.draft_sections call; --no-report-draft skips
    draft_max_chars: int = 6000  # compact data summary shown to the drafter


# --- Aggregate ---


@dataclass
class Config:
    llm: LLMConfig = field(default_factory=LLMConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    docker: DockerConfig = field(default_factory=DockerConfig)
    detect: DetectConfig = field(default_factory=DetectConfig)
    pin: PinConfig = field(default_factory=PinConfig)
    baseline: BaselineConfig = field(default_factory=BaselineConfig)
    testgen: TestGenConfig = field(default_factory=TestGenConfig)
    lint: LintConfig = field(default_factory=LintConfig)
    graph: GraphConfig = field(default_factory=GraphConfig)
    knowledge: KnowledgeConfig = field(default_factory=KnowledgeConfig)
    okf: OKFConfig = field(default_factory=OKFConfig)
    history: HistoryFunnelConfig = field(default_factory=HistoryFunnelConfig)
    excision: ExcisionFunnelConfig = field(default_factory=ExcisionFunnelConfig)
    netnew: NetNewConfig = field(default_factory=NetNewConfig)
    harness: HarnessConfig = field(default_factory=HarnessConfig)
    tasks: TasksConfig = field(default_factory=TasksConfig)
    instruction: InstructionConfig = field(default_factory=InstructionConfig)
    difficulty: DifficultyConfig = field(default_factory=DifficultyConfig)
    selection: SelectionConfig = field(default_factory=SelectionConfig)
    report: ReportConfig = field(default_factory=ReportConfig)
    step_model: dict[str, Tier] = field(default_factory=lambda: dict(STEP_MODEL))
    # Pipeline source files whose contents fingerprint every hygiene step's input hash.
    hygiene_code_files: tuple[str, ...] = (
        "pipeline/ecosystems/python.py",
        "pipeline/hygiene/detect.py",
        "pipeline/hygiene/pin.py",
        "pipeline/hygiene/dockerfile.py",
        "pipeline/hygiene/compose.py",
        "pipeline/hygiene/build.py",
        "pipeline/hygiene/baseline.py",
        "pipeline/hygiene/testgen.py",
        "pipeline/hygiene/mutate.py",
        "pipeline/hygiene/lint.py",
    )

    def model_for(self, step: str) -> str:
        tier = self.step_model[step]
        return LLM_MODEL_BIG if tier == "big" else LLM_MODEL_SMALL

    def reasoning_for(self, step: str) -> Reasoning:
        return TIER_REASONING[self.step_model[step]]


DEFAULT = Config()
