"""Modular agent loop behind the AgentRunner interface.

OpenAI-compatible function calling. The goal is the user message. The loop ends
when the model replies with no tool calls; that final text is the summary (no
`done` tool). Tool errors are returned to the model as text. Hard stop on the
turn cap. Every turn is written to a trajectory file. pi (`pi --rpc`) could be
swapped in behind the same interface.
"""

from __future__ import annotations

import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from pipeline.agent.tools import Tool
from pipeline.config import DEFAULT
from pipeline.llm.client import LLMClient


@dataclass
class AgentResult:
    files_changed: list[str]
    summary: str
    trajectory_path: str | None


class AgentRunner(ABC):
    @abstractmethod
    def run(self, goal: str) -> AgentResult: ...


class Agent(AgentRunner):
    MAX_TURNS_SUMMARY = "stopped: reached max turns"

    def __init__(
        self,
        llm: LLMClient,
        step: str,
        system_prompt: str,
        tools: list[Tool],
        files_changed: set[str],
        max_turns: int = DEFAULT.agent.max_turns,
        max_tokens_per_tool_result: int = DEFAULT.agent.max_tokens_per_tool_result,
        transcripts_dir: Path | None = None,
    ) -> None:
        self.llm = llm
        self.step = step  # selects model + reasoning via config
        self.system_prompt = system_prompt
        self.tools = {t.name: t for t in tools}
        self.tool_schemas = [t.schema() for t in tools]
        self.files_changed = files_changed
        self.max_turns = max_turns
        self.max_chars = max_tokens_per_tool_result * DEFAULT.agent.chars_per_token
        self.transcripts_dir = transcripts_dir or Path("transcripts")

    def run(self, goal: str) -> AgentResult:
        messages: list[dict] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": goal},
        ]
        summary = ""
        for _ in range(self.max_turns):
            completion = self.llm.chat(
                self.step, messages, tools=self.tool_schemas, tool_choice="auto"
            )
            message = completion.choices[0].message
            messages.append(self._assistant_dict(message))
            if not message.tool_calls:
                summary = message.content or ""
                break
            for call in message.tool_calls:
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": self._invoke(call),
                    }
                )
        else:
            summary = self.MAX_TURNS_SUMMARY
        trajectory = self._write_trajectory(goal, messages)
        return AgentResult(sorted(self.files_changed), summary, trajectory)

    def _invoke(self, call) -> str:
        tool = self.tools.get(call.function.name)
        if tool is None:
            return f"ERROR: unknown tool {call.function.name}"
        try:
            kwargs = json.loads(call.function.arguments or "{}")
        except json.JSONDecodeError as exc:
            return f"ERROR: bad tool arguments: {exc}"
        try:
            result = tool.func(**kwargs)
        except Exception as exc:  # noqa: BLE001 - tool errors are observations
            return f"ERROR: {exc}"
        if len(result) > self.max_chars:
            return result[: self.max_chars] + "\n... (truncated)"
        return result

    @staticmethod
    def _assistant_dict(message) -> dict:
        out: dict = {"role": "assistant", "content": message.content or ""}
        if message.tool_calls:
            out["tool_calls"] = [
                {
                    "id": c.id,
                    "type": "function",
                    "function": {"name": c.function.name, "arguments": c.function.arguments},
                }
                for c in message.tool_calls
            ]
        return out

    def _write_trajectory(self, goal: str, messages: list[dict]) -> str:
        out = self.transcripts_dir / "agent" / self.step
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{uuid.uuid4().hex[:12]}.json"
        path.write_text(json.dumps({"goal": goal, "messages": messages}, indent=2, default=str))
        return str(path)
