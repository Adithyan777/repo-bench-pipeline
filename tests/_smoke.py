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
