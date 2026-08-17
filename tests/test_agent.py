"""Agent loop solves a toy task end-to-end: replayed LLM + real container."""

from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.agent.loop import Agent
from pipeline.agent.tools import Tool, ToolContext, _grep
from pipeline.llm.client import LLMClient
from tests import _smoke
from tests.test_llm import make_completion

IMAGE = "python:3.12-slim"
STEP = "p1.docker.repair_agent"


def _has_cassettes() -> bool:
    d = Path("tests/cassettes") / _smoke.AGENT_STAGE
    return d.is_dir() and any(d.glob("*.json"))


def _noop_tool(name: str = "noop") -> Tool:
    return Tool(name, "noop", {"type": "object", "properties": {}}, lambda **_: "ok")


class _ScriptedLLM:
    """Stands in for the endpoint: returns scripted completions, counts calls."""

    def __init__(self, completions):
        self._it = iter(completions)
        self.calls = 0

    def chat(self, step, messages, tools=None, tool_choice=None, max_tokens=None):
        self.calls += 1
        return next(self._it)


def _agent(tmp_path: Path, tools, llm=None, **kw) -> Agent:
    llm = llm or LLMClient(stage="unit_test", mode="live", transcripts_dir=tmp_path / "t")
    return Agent(llm, STEP, "sys", tools, set(), transcripts_dir=tmp_path / "t", **kw)


def _call(name: str, arguments: str = "{}"):
    class _Call:
        id = "c0"

        class function:
            pass

    _Call.function.name = name
    _Call.function.arguments = arguments
    return _Call()


def test_agent_loop_stub_tool_errors_are_observations(tmp_path: Path) -> None:
    """A graph tool with no knowledge_dir raises; the loop must surface it as text."""
    from pipeline.agent.tools import ToolContext, graph_tools

    ctx = ToolContext(workdir=tmp_path)  # no knowledge_dir bound
    show_symbol = {t.name: t for t in graph_tools(ctx)}["show_symbol"]
    observation = _agent(tmp_path, [show_symbol])._invoke(_call("show_symbol", '{"qualname":"x"}'))
    assert observation.startswith("ERROR:")
    assert "repo graph" in observation


def test_agent_max_turns_hard_stop(tmp_path: Path) -> None:
    """Model never stops calling tools -> loop stops at max_turns."""
    forever = [make_completion(tool_calls=[("noop", "{}")]) for _ in range(10)]
    llm = _ScriptedLLM(forever)
    agent = _agent(tmp_path, [_noop_tool()], llm=llm, max_turns=3)
    result = agent.run("go")
    assert result.summary == "stopped: reached max turns"
    assert llm.calls == 3


def test_tool_result_truncation(tmp_path: Path) -> None:
    big = _noop_tool("big")
    big.func = lambda **_: "x" * 100_000
    agent = _agent(tmp_path, [big], max_tokens_per_tool_result=2)  # -> 8 chars budget
    observation = agent._invoke(_call("big"))
    assert observation.endswith("... (truncated)")
    assert observation.startswith("x" * 8)
    assert len(observation) < 100_000


def test_grep_does_not_follow_symlink_outside_workdir(tmp_path: Path) -> None:
    outside = tmp_path / "outside.txt"
    outside.write_text("TOPSECRET value\n")
    workdir = tmp_path / "repo"
    workdir.mkdir()
    (workdir / "safe.py").write_text("TOPSECRET marker here\n")  # a real in-repo hit
    (workdir / "link.txt").symlink_to(outside)  # escapes the workdir

    ctx = ToolContext(workdir=workdir)
    result = _grep(ctx, "TOPSECRET")
    assert "safe.py" in result  # in-repo match found
    assert "link.txt" not in result  # symlink skipped
    assert result.count("TOPSECRET") == 1  # outside file never read


@pytest.mark.docker
@pytest.mark.skipif(not _has_cassettes(), reason="agent_toy cassettes not recorded yet")
def test_agent_solves_toy_task(tmp_path: Path, docker_available: None) -> None:
    workdir = tmp_path / "repo"
    workdir.mkdir()
    client = LLMClient(stage=_smoke.AGENT_STAGE, mode="replay", transcripts_dir=tmp_path / "t")
    agent = _smoke.build_agent(client, workdir, IMAGE, tmp_path / "t")

    result = agent.run(_smoke.AGENT_GOAL)

    assert "hello.py" in result.files_changed
    assert (workdir / "hello.py").exists()
    assert "42" in result.summary
    assert Path(result.trajectory_path).is_file()
