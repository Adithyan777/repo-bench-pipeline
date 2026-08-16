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
LLM_MODEL_SMALL = os.environ.get("LLM_MODEL_SMALL", "deepseek-ai/DeepSeek-V4-Flash-0731")  # Baseten slug

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


@dataclass
class AgentConfig:
    max_turns: int = 25
    max_tokens_per_tool_result: int = 8_000
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


@dataclass
class PinConfig:
    resolver: str = "uv"  # `uv pip compile`
    generate_hashes: bool = True
    emit_constraints_txt: bool = True
    lock_filename: str = "requirements.lock.txt"


@dataclass
class BaselineConfig:
    framework_priority: tuple[str, ...] = ("pytest", "unittest")
    env_fix_attempts: int = 1  # automatic: add missing extra, rerun
    quarantine_file: str = "tests/quarantine.txt"  # --deselect list
    treat_collection_broken_as_no_tests_after_repair: bool = True


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
    reject_manifest_changes: bool = True  # setup.py / requirements* / pyproject -> dependency-changing
    ignore_paths: tuple[str, ...] = ("docs/", "*.md", "*.rst", ".github/", "CHANGELOG*", "*_version.py")
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


@dataclass
class ExcisionFunnelConfig:
    min_covering_tests: int = 2
    min_lines: int = 8
    max_lines: int = 80
    min_complexity: int = 3
    public_only: bool = True
    min_assertions_touching_fn: int = 3  # below this, agent adds edge-case tests
    excision_body: str = 'raise NotImplementedError("excised")'
    strip_docstring: bool = False  # flag: --excision-hard
    build_target: int = 5


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
    valid_fail_reasons: tuple[str, ...] = (
        "AssertionError",
        "pytest.raises",
        "NotImplementedError",
        "exception_in_function_under_test",
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
    )
    run_collateral_for_excision: bool = True
    recopy_canonical_verifier: bool = True
    verifier_may_only_import_public_symbols_in_input: bool = True
    verifier_visibility: str = "visible"  # flag: --verifier-visibility visible|hidden


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
    target_spread: dict[str, int] = field(default_factory=lambda: {"easy": 2, "medium": 5, "hard": 3})


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
    okf: OKFConfig = field(default_factory=OKFConfig)
    history: HistoryFunnelConfig = field(default_factory=HistoryFunnelConfig)
    excision: ExcisionFunnelConfig = field(default_factory=ExcisionFunnelConfig)
    netnew: NetNewConfig = field(default_factory=NetNewConfig)
    harness: HarnessConfig = field(default_factory=HarnessConfig)
    instruction: InstructionConfig = field(default_factory=InstructionConfig)
    difficulty: DifficultyConfig = field(default_factory=DifficultyConfig)
    selection: SelectionConfig = field(default_factory=SelectionConfig)
    step_model: dict[str, Tier] = field(default_factory=lambda: dict(STEP_MODEL))

    def model_for(self, step: str) -> str:
        tier = self.step_model[step]
        return LLM_MODEL_BIG if tier == "big" else LLM_MODEL_SMALL

    def reasoning_for(self, step: str) -> Reasoning:
        return TIER_REASONING[self.step_model[step]]


DEFAULT = Config()
