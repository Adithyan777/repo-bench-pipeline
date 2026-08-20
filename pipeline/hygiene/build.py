"""Hygiene step 5 (build): build the repo image; bounded LLM repair loop on failure.

Repair agent gets read_file/grep/write_file + the build log (no `run`: no image yet).
Every attempt is appended to output/<repo>/audit/agent_actions.jsonl.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from pipeline.agent.loop import Agent
from pipeline.agent.tools import ToolContext, concrete_tools
from pipeline.docker.image import DockerError, build_image
from pipeline.hygiene.context import HygieneContext
from pipeline.log import log as plog
from pipeline.state import hash_inputs

_REPAIR_SYSTEM = (
    "You are a build engineer. A Docker image build for a Python repo failed. Read the "
    "build log and the relevant files (Dockerfile, requirements.lock.txt, requirements.in), "
    "make the smallest change that fixes the build, and write the corrected files. Do not "
    "explain at length; just fix it."
)


def input_hash(ctx: HygieneContext) -> str:
    return hash_inputs(ctx.repo / "Dockerfile", ctx.repo / ctx.config.pin.lock_filename)


def run(ctx: HygieneContext) -> dict:
    tag = ctx.image_tag
    try:
        digest = build_image(ctx.repo, tag)
        data = {"image_tag": tag, "image_digest": digest, "attempts": 0, "outcome": "built"}
        plog("hygiene", "build", f"built {tag}")
    except DockerError as exc:
        tail = (str(exc).strip().splitlines() or ["?"])[-1][:160]
        plog("hygiene", "build", f"build failed: {tail}")
        digest, attempts, outcome = _repair_loop(ctx, tag, str(exc))
        data = {"image_tag": tag, "image_digest": digest, "attempts": attempts, "outcome": outcome}
    ctx.record("build", data)
    if data["outcome"] != "built":
        raise SystemExit(f"{ctx.repo.name}: image build failed after repair; see audit log")
    return data


def _repair_loop(ctx: HygieneContext, tag: str, first_error: str) -> tuple[str, int, str]:
    max_attempts = ctx.config.agent.docker_repair_max_attempts
    log = first_error
    for attempt in range(1, max_attempts + 1):
        before = _diff(ctx.repo)
        tool_ctx = ToolContext(workdir=ctx.repo)
        tools = [t for t in concrete_tools(tool_ctx) if t.name != "run"]
        agent = Agent(
            ctx.llm,
            "p1.docker.repair_agent",
            _REPAIR_SYSTEM,
            tools,
            tool_ctx.files_changed,
        )
        goal = f"Docker build failed. Build log:\n{log[-4000:]}\nFix the build."
        plog("hygiene", "build", f"repair attempt {attempt}/{max_attempts}")
        result = agent.run(goal)
        try:
            digest = build_image(ctx.repo, tag)
            _audit(ctx, goal, result, attempt, "built", before)
            plog("hygiene", "build", f"repair attempt {attempt}: built")
            return digest, attempt, "built"
        except DockerError as exc:
            log = str(exc)
            _audit(ctx, goal, result, attempt, "failed", before)
            plog("hygiene", "build", f"repair attempt {attempt}: still failing")
    return "", max_attempts, "failed"


def _audit(ctx: HygieneContext, goal: str, result, attempt: int, outcome: str, before: str) -> None:
    ctx.audit_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "stage": "p1.docker.repair_agent",
        "goal": goal[:500],
        "files_changed": result.files_changed,
        "diff": _diff(ctx.repo),
        "attempt": attempt,
        "outcome": outcome,
    }
    with (ctx.audit_dir / "agent_actions.jsonl").open("a") as fh:
        fh.write(json.dumps(record) + "\n")


def _diff(repo: Path) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), "diff", "--stat"], capture_output=True, text=True, check=False
    )
    return proc.stdout.strip()
