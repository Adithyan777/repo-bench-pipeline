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
    # Per-tier output-token ceiling. BIG needs headroom: Kimi with thinking on can
    # spend hundreds of completion tokens before the visible answer.
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
    # Build-system markers meaning the version is derived from git metadata; when
    # present we keep .git in the build context and install git in the image so the
    # version resolves (env fix, not a source edit).
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
    # Times to re-ask the SMALL model for a corrected PyPI name when an inferred
    # import fails to resolve, before dropping it as unresolved.
    alias_reask_attempts: int = 1


@dataclass
class BaselineConfig:
    framework_priority: tuple[str, ...] = ("pytest", "unittest")
    env_fix_attempts: int = 1  # automatic: add missing extra, rerun
    quarantine_file: str = "tests/quarantine.txt"  # --deselect list
    treat_collection_broken_as_no_tests_after_repair: bool = True
    report_filename: str = ".pytest-report.json"  # pytest-json-report output, read from workdir
    # The agent-fix step may ONLY change these paths (tests/config/deps); any edit
    # outside them is reverted and audited. It must never patch the code under test.
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


@dataclass
class LintConfig:
    tool: str = "ruff"
    rules: tuple[str, ...] = ("E", "F", "W", "I", "B", "UP")
    autofix: bool = True
    format: bool = True
    allow_noqa_for_unfixable: bool = True
    llm_fix_unfixable: bool = False  # else noqa + report
    never_lint_historical_trees: bool = True


# --- Pipeline 2: knowledge layer ---


@dataclass
class GraphConfig:
    edge_types: tuple[str, ...] = ("imports", "contains", "calls", "inherits", "tested_by")
    resolve_calls_intra_repo_only: bool = True
    verification_sample_edges: int = 200  # graph self-check sample size
    diversity_unit: str = "file"  # "file" for glom-sized repos, "subpackage" for large
    large_repo_module_threshold: int = 200  # >= this many modules -> subpackage diversity unit
    # Our own McCabe branch counter (no radon dependency): deterministic, version-stable.
    # Counted constructs documented in HEURISTICS.md and ecosystems/symbols.py:_complexity.
    complexity_metric: str = "branch_count"
    # A .py file is a test (indexed separately, never a source node) if it lives under
    # one of these dirs or its name matches one of these globs.
    test_dir_names: tuple[str, ...] = ("test", "tests")
    test_file_globs: tuple[str, ...] = ("test_*.py", "*_test.py")
    # Packaging/build scripts that are .py but not library source -> excluded from graph
    # nodes (they run side effects on import and pollute diversity counts).
    nonsource_files: tuple[str, ...] = ("setup.py",)


@dataclass
class KnowledgeConfig:
    """Pipeline-owned filenames + coverage settings for the P2 static layer."""

    # A tiny pytest plugin switches coverage's context to the exact pytest nodeid per
    # test (via coverage.Coverage.current().switch_context), so parametrized/inherited
    # cases are captured distinctly. No pytest-cov dependency needed.
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
    # src-layout roots stripped when deriving a historical module's dotted name so it
    # matches the graph's package-aware naming (e.g. src/pkg/mod.py -> pkg.mod).
    source_roots: tuple[str, ...] = ("src",)
    show_commit_max_chars: int = 4000  # git-fallback output cap in the show_commit tool
    # Pipeline source files whose contents fingerprint every knowledge step's input
    # hash, so a code change to an analyzer invalidates its artifacts (not just inputs).
    code_fingerprint_files: tuple[str, ...] = (
        "pipeline/ecosystems/symbols.py",
        "pipeline/knowledge/graph.py",
        "pipeline/knowledge/indexes.py",
        "pipeline/knowledge/verify.py",
        "pipeline/knowledge/runner.py",
    )


@dataclass
class OKFConfig:
    okf_version: str = "0.2"
    max_function_pages: int = 150
    function_page_selector: str = "public_or_top_complexity"
    generated_by_actor: str = "pipeline/{model}"
    verifier_actor: str = "process:okf-verifier"
    unverified_status: str = "draft"


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
    shortlist_size: int = 15
    build_target: int = 8  # built; expect ~5-6 to validate
    pr_merge_input_is_first_parent: bool = True
    # Only PR merges (a pr_number in the subject) are candidates; other merges
    # (back-merges of master into a branch) diff against an arbitrary first parent.
    reject_non_pr_merges: bool = True
    reject_root_commits: bool = True  # no parent -> no input/ tree
    # Commits that are part of a surviving PR merge's branch are superseded by the merge
    # (the merge is the complete unit); they stand alone only when the merge is rejected.
    prefer_pr_merge_over_constituents: bool = True
    # Reverted commits (a later "Revert ... This reverts commit <sha>" or an exact
    # reverse patch-id) are dropped; when False they only take score_reverted_penalty.
    reject_reverted: bool = True
    revert_message_regex: str = r"^Revert\b|This reverts commit ([0-9a-f]{7,40})"
    # SMALL classifier: source diff shown per commit is capped; the classifier walks the
    # scored survivors in classify_batch_size batches until shortlist_size are kept, never
    # past classify_max_commits (rest: not-classified). Decisions persist by content hash.
    classify_diff_max_chars: int = 3000
    classify_max_commits: int = 60
    reuse_classify_decisions: bool = True
    # Build-time verifier gates (all in-container): the commit's own changed test
    # functions are the verifier when present; else a bounded BIG agent authors tests.
    # Tests that pass on input/ are dropped; harness.min_failing_tests must remain.
    neutrality_check: bool = True  # BIG check of the commit's tests (public interface?)
    neutrality_rewrite_max_attempts: int = 1  # bounded agent rewrite when flagged
    # Agent budgets per build step (cached/reused runs do not count): total agent runs
    # (verifier author + rewrites) and, within it, rewrites.
    max_agent_runs_per_repo: int = 6
    max_neutrality_rewrites_per_repo: int = 2  # beyond -> reject on flag / missing symbol
    prompt_new_names_max: int = 20  # change-introduced identifiers listed in agent prompts
    neutrality_recheck_after_rewrite: bool = True  # one more complete_json on the rewrite
    # New public API introduced by the change may be verified through the getattr
    # convention (import an existing public module, `getattr(mod, name, None)`, assert
    # presence + behavior -> AssertionError on input/ is a right reason). Commit tests that
    # top-level import such a name are routed to the rewrite agent instead of rejected.
    allow_new_symbol_features: bool = True
    verifier_agent_max_attempts: int = 1  # bounded agent when the commit has no tests
    verifier_agent_when_no_tests: bool = True
    agent_max_turns: int = 12  # P3 agents (verifier author, rewrite): BIG turns are costly
    agent_test_file_prefix: str = "test_hist_"
    agent_diff_max_chars: int = 6000  # source diff shown to the verifier agent
    # Collateral baseline for a history task = tests that PASS on input/ (the parent
    # tree) in one build-time run; the HEAD baseline lists tests that may not exist yet.
    collateral_baseline_from_input: bool = True
    # A history task is built with build_target tasks by walking the shortlist in order;
    # build-time rejects (env-drift, tests pass on input, ...) are backfilled.
    reuse_agent_outputs: bool = True  # verifier files from agents cached by content hash


@dataclass
class ExcisionFunnelConfig:
    min_covering_tests: int = 2  # distinct base test nodeids that PASSED at baseline
    # Central dispatch/registry code is hit by most of the suite; excising it fails
    # nearly everything instead of a targeted set of tests -> not a focused task.
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
    # Pre-gate: a candidate whose covering test files import private repo symbols/modules
    # is rejected before the screen (same AST rule as the harness static gate).
    reject_private_verifier_imports: bool = True
    # The SMALL screen walks the ranking in classify_batch_size chunks until build_target
    # survivors are found (backfills past screened-out candidates); rest are `surplus`.
    # Screen decisions are persisted in candidates.json keyed by content hash and reused
    # on rerun (unless the step is --force'd), so reruns need no LLM call.
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
    # A failing test is "valid" only if the exception passed through repo (non-test)
    # code, or it is an assertion / pytest.raises mismatch raised in the test itself.
    report_filename: str = ".pytest-report.json"  # json-report written inside the workdir
    min_failing_tests: int = 1  # fail-before must have at least this many failing tests
    # If the task's image tag is missing locally, build it from <task>/input/Dockerfile.
    build_image_if_missing: bool = False
    # The verdict records the live image digest; a rebuilt image gets a new Id even
    # from the same pinned Dockerfile, so a digest mismatch is reported, not a gate.
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
    instruction_status_template: str = "template-S4"  # LLM-authored instruction lands in S5
    history_instruction_status_template: str = "template-S5a"
    # Hygiene artifacts overlaid (additively, never overwriting) onto historical trees so
    # every task ships its own environment; the pipeline commit's file list wins when known.
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
        "pipeline/tasks/harness.py",
        "pipeline/tasks/manifest.py",
        "pipeline/tasks/runner.py",
        "pipeline/tasks/classify.py",
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
    target_spread: dict[str, int] = field(
        default_factory=lambda: {"easy": 2, "medium": 5, "hard": 3}
    )


@dataclass
class SelectionConfig:
    total_tasks: int = 10
    min_history: int = 4
    max_excision: int = 4
    max_netnew: int = 2  # user decision (PDF allows 3)
    min_distinct_modules: int = 4


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
    )

    def model_for(self, step: str) -> str:
        tier = self.step_model[step]
        return LLM_MODEL_BIG if tier == "big" else LLM_MODEL_SMALL

    def reasoning_for(self, step: str) -> Reasoning:
        return TIER_REASONING[self.step_model[step]]


DEFAULT = Config()
