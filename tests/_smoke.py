"""Shared smoke definitions used by BOTH the cassette recorder and the tests.

Keeping the request-building here guarantees the recorder and the replay tests
produce byte-identical requests, so cassette keys match.
"""

from __future__ import annotations

from pathlib import Path

from pipeline.agent.loop import Agent
from pipeline.agent.tools import ToolContext, concrete_tools
from pipeline.llm.client import LLMClient

# --- direct schema-forced JSON smoke (SMALL tier) ---

JSON_STAGE = "s1_smoke"
JSON_STEP = "p1.pin.import_to_pypi"  # small
JSON_SCHEMA = {
    "type": "object",
    "properties": {"answer": {"type": "integer"}},
    "required": ["answer"],
    "additionalProperties": False,
}
JSON_MESSAGES = [{"role": "user", "content": "Return the integer 42 as `answer`."}]


def run_smoke_json(client: LLMClient) -> dict:
    return client.complete_json(JSON_STEP, JSON_MESSAGES, JSON_SCHEMA)


# --- agent loop smoke (BIG tier), executes in a container ---

AGENT_STAGE = "s1_agent"
AGENT_STEP = "p1.docker.repair_agent"  # big
AGENT_SYSTEM = (
    "You are a coding agent. Use the tools to complete the task, then reply with a "
    "short summary. Do not ask questions."
)
AGENT_GOAL = (
    "Create a file hello.py that prints 42, run it with `python hello.py`, and report "
    "the output it produced."
)


# --- S2 hygiene LLM smokes (SMALL tier) ---

PIN_STAGE = "s2_pin"
BASELINE_STAGE = "s2_baseline"

# An import whose PyPI name differs and is NOT in the alias table -> needs the model.
ALIAS_UNKNOWN = ["serial"]  # -> pyserial

CLASSIFY_SAMPLE = [
    "tests/test_x.py::test_reads_yaml: ModuleNotFoundError: No module named 'yaml'",
    "tests/test_x.py::test_math: assert add(1, 1) == 3",
]


def run_alias_map(client: LLMClient) -> dict:
    from pipeline.ecosystems.python import PythonAdapter

    return PythonAdapter(llm=client)._llm_map_imports(ALIAS_UNKNOWN)


REASK_STAGE = "s2_reask"
REASK_IMPORT = "zzznonexistent9876"  # an invented import that cannot resolve on PyPI


def run_reask(client: LLMClient) -> dict:
    from pipeline.ecosystems.python import PythonAdapter, reask_note

    adapter = PythonAdapter(llm=client)
    return adapter._llm_map_imports([REASK_IMPORT], error=reask_note(REASK_IMPORT, REASK_IMPORT))


def run_classify(client: LLMClient) -> dict:
    from pipeline.hygiene.baseline import _CLASSIFY_SCHEMA, classify_prompt

    return client.complete_json(
        "p1.baseline.classify_failure",
        [{"role": "user", "content": classify_prompt(CLASSIFY_SAMPLE)}],
        _CLASSIFY_SCHEMA,
    )


def build_agent(client: LLMClient, workdir: Path, image: str, transcripts_dir: Path) -> Agent:
    ctx = ToolContext(workdir=workdir, image=image)
    return Agent(
        llm=client,
        step=AGENT_STEP,
        system_prompt=AGENT_SYSTEM,
        tools=concrete_tools(ctx),
        files_changed=ctx.files_changed,
        transcripts_dir=transcripts_dir,
    )


# --- S4 excision screen (SMALL tier), replayed by tests/test_tasks.py ---

SCREEN_STAGE = "s4_screen"
FIXTURE_MINI_PKG = Path(__file__).resolve().parent / "fixtures" / "mini_pkg"

# The real mini_pkg test_map (knowledge stage output); pinned here so the recorded
# prompt (pool + order) is byte-identical to what the replay tests build.
MINI_PKG_TEST_MAP = {
    "tests/test_calc.py::test_ceil_div_exact_multiple": ["mini_pkg.calc.ceil_div"],
    "tests/test_calc.py::test_ceil_div_rounds_up": ["mini_pkg.calc.ceil_div"],
    "tests/test_calc.py::test_clamp_bounds": ["mini_pkg.calc.clamp"],
    "tests/test_calc.py::test_clamp_within": ["mini_pkg.calc.clamp"],
    "tests/test_calc.py::test_running_stats_mean": [
        "mini_pkg.calc.RunningStats.__init__",
        "mini_pkg.calc.RunningStats.add",
        "mini_pkg.calc.RunningStats.mean",
    ],
    "tests/test_core.py::test_dedupe_preserves_order": ["mini_pkg.core.dedupe"],
    "tests/test_core.py::test_registry_duplicate_raises": [
        "mini_pkg.core.Registry.__init__",
        "mini_pkg.core.Registry.register",
    ],
    "tests/test_core.py::test_registry_register_and_get": [
        "mini_pkg.core.Registry.__init__",
        "mini_pkg.core.Registry.get",
        "mini_pkg.core.Registry.register",
    ],
    "tests/test_text.py::test_display_width_ascii": ["mini_pkg.text.display_width"],
    "tests/test_text.py::test_truncate_adds_ellipsis": [
        "mini_pkg.text._needs_truncation",
        "mini_pkg.text.display_width",
        "mini_pkg.text.truncate",
    ],
    "tests/test_text.py::test_truncate_short_string_unchanged": [
        "mini_pkg.text._needs_truncation",
        "mini_pkg.text.display_width",
        "mini_pkg.text.truncate",
    ],
}


def mini_pkg_excision_config():
    """mini_pkg functions are all < 8 lines; relax the size/complexity floors so the
    fixture exercises the funnel + screen (thresholds themselves are tested separately)."""
    from pipeline.config import Config

    cfg = Config()
    cfg.excision.min_lines = 3
    cfg.excision.min_complexity = 1
    cfg.excision.min_assertions_touching_fn = 0  # no BIG top-up agent in the fixture run
    return cfg


def mini_pkg_ranked(repo: Path | None = None):
    from pipeline.ecosystems.symbols import build_symbol_index
    from pipeline.tasks import excision

    cfg = mini_pkg_excision_config()
    repo = repo or FIXTURE_MINI_PKG
    symbols = build_symbol_index(repo, cfg)
    passing = set(MINI_PKG_TEST_MAP)
    cands = excision.funnel(symbols, MINI_PKG_TEST_MAP, passing, cfg, repo=repo)
    return excision.rank(cands, cfg), cfg


def run_excision_screen(client: LLMClient, repo: Path | None = None) -> list[str]:
    from pipeline.tasks import excision

    ranked, cfg = mini_pkg_ranked(repo)
    selected = excision.screen(ranked, repo or FIXTURE_MINI_PKG, client, cfg)
    return [c.qualname for c in selected]
