"""Record the S1 smoke cassettes against the real endpoint (minimal spend).

Usage (from repo root, with .env present and Docker running):
    LLM_MODE=record .venv/bin/python scripts/record_cassettes.py

Records:
  - tests/cassettes/s1_smoke/  : one SMALL-tier schema-forced JSON call
  - tests/cassettes/s1_agent/  : the toy agent task (create hello.py -> run -> report)

Prints token spend per stage. Commit the resulting cassettes; tests then replay
them offline. Secrets are read from .env / env and never printed.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def load_env(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main() -> int:
    load_env(ROOT / ".env")
    os.environ["LLM_MODE"] = "record"

    from pipeline.llm.client import LLMClient
    from tests import _smoke

    transcripts = ROOT / "transcripts"

    # 1) direct JSON smoke (SMALL)
    json_client = LLMClient(stage=_smoke.JSON_STAGE, mode="record", transcripts_dir=transcripts)
    answer = _smoke.run_smoke_json(json_client)
    print(f"[s1_smoke] answer={answer}")

    # 2) agent smoke (BIG), executes in a real container
    workdir = ROOT / "scripts" / "_record_workdir"
    workdir.mkdir(parents=True, exist_ok=True)
    for stale in workdir.iterdir():
        stale.unlink()
    agent_client = LLMClient(stage=_smoke.AGENT_STAGE, mode="record", transcripts_dir=transcripts)
    agent = _smoke.build_agent(agent_client, workdir, "python:3.12-slim", transcripts)
    result = agent.run(_smoke.AGENT_GOAL)
    print(f"[s1_agent] files_changed={result.files_changed} summary={result.summary!r}")

    total = 0
    for client in (json_client, agent_client):
        for step, usage in client.usage_by_stage.items():
            print(
                f"  {step}: prompt={usage.prompt_tokens} completion={usage.completion_tokens} "
                f"reasoning={usage.reasoning_tokens} total={usage.total_tokens}"
            )
            total += usage.total_tokens
    print(f"TOTAL tokens recorded: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
