"""Record LLM cassettes against the real endpoint (minimal spend).

Usage (from repo root, with .env present and Docker running):
    LLM_MODE=record .venv/bin/python scripts/record_cassettes.py [--rerecord STAGE ...]

By default each stage is SKIPPED if it already has cassettes (so re-runs don't
re-spend tokens or churn multi-turn tapes). Pass --rerecord <stage> to force one,
or --rerecord all to force everything. Secrets are read from .env, never printed.

Stages: s1_smoke, s1_agent, s2_pin, s2_baseline, s2_reask.
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


def _has_cassettes(stage: str) -> bool:
    d = ROOT / "tests" / "cassettes" / stage
    return d.is_dir() and any(d.glob("*.json"))


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    rerecord = {argv[i + 1] for i, a in enumerate(argv) if a == "--rerecord" and i + 1 < len(argv)}
    load_env(ROOT / ".env")
    os.environ["LLM_MODE"] = "record"

    from pipeline.llm.client import LLMClient
    from tests import _smoke

    transcripts = ROOT / "transcripts"
    clients = []

    def stage(name: str, fn) -> None:
        if _has_cassettes(name) and name not in rerecord and "all" not in rerecord:
            print(f"[{name}] skip (cassette exists; --rerecord {name} to force)")
            return
        client = LLMClient(stage=name, mode="record", transcripts_dir=transcripts)
        print(f"[{name}] {fn(client)}")
        clients.append(client)

    def agent_smoke(client: LLMClient):
        workdir = ROOT / "scripts" / "_record_workdir"
        workdir.mkdir(parents=True, exist_ok=True)
        for stale in workdir.iterdir():
            stale.unlink()
        result = _smoke.build_agent(client, workdir, "python:3.12-slim", transcripts).run(
            _smoke.AGENT_GOAL
        )
        return f"files_changed={result.files_changed}"

    stage(_smoke.JSON_STAGE, _smoke.run_smoke_json)
    stage(_smoke.AGENT_STAGE, agent_smoke)
    stage(_smoke.PIN_STAGE, _smoke.run_alias_map)
    stage(_smoke.BASELINE_STAGE, _smoke.run_classify)
    stage(_smoke.REASK_STAGE, _smoke.run_reask)

    total = 0
    for client in clients:
        for step, usage in client.usage_by_stage.items():
            print(f"  {step}: total={usage.total_tokens} (reasoning={usage.reasoning_tokens})")
            total += usage.total_tokens
    print(f"TOTAL tokens recorded this run: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
