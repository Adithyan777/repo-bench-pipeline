"""Entry point: arg parsing, stages, per-repo run directory + state.

Stages (hygiene/knowledge/tasks) are implemented from S2 onward; S1 provides the
skeleton, resumable state, and config overrides. ``run.sh`` wraps this module.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import fields, is_dataclass
from pathlib import Path

from pipeline.config import DEFAULT, Config
from pipeline.state import State

STAGES = ("hygiene", "knowledge", "tasks")
OUTPUT_ROOT = Path("output")


def repo_name(repo: str) -> str:
    return Path(repo.rstrip("/")).name.removesuffix(".git")


def apply_overrides(config: Config, assignments: list[str]) -> None:
    """Apply ``--set section.key=value``, coercing to the existing value's type."""
    for item in assignments:
        dotted, _, value = item.partition("=")
        section, _, key = dotted.partition(".")
        target = getattr(config, section, None)
        if not is_dataclass(target) or key not in {f.name for f in fields(target)}:
            raise SystemExit(f"unknown config path: {dotted}")
        current = getattr(target, key)
        setattr(target, key, _coerce(value, current))


def _coerce(value: str, current: object) -> object:
    if isinstance(current, bool):
        return value.lower() in ("1", "true", "yes")
    if isinstance(current, int):
        return int(value)
    if isinstance(current, float):
        return float(value)
    return value


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="pipeline", description="AI task benchmark pipeline")
    p.add_argument("repo", help="repo URL or local path")
    p.add_argument("--stage", choices=(*STAGES, "all"), default="all")
    p.add_argument("--force", action="append", default=[], metavar="STEP", help="rerun a step")
    p.add_argument("--fresh", action="store_true", help="rerun everything")
    p.add_argument("--llm-cache", action="store_true", help="enable prompt->response disk cache")
    p.add_argument(
        "--excision-hard", action="store_true", help="strip docstrings from excised functions"
    )
    p.add_argument(
        "--verifier-visibility",
        choices=("visible", "hidden"),
        default=DEFAULT.harness.verifier_visibility,
    )
    p.add_argument("--set", action="append", default=[], metavar="section.key=value")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = DEFAULT
    apply_overrides(config, args.set)
    config.llm.disk_cache = config.llm.disk_cache or args.llm_cache
    config.excision.strip_docstring = config.excision.strip_docstring or args.excision_hard
    config.harness.verifier_visibility = args.verifier_visibility

    run_dir = OUTPUT_ROOT / repo_name(args.repo)
    State.load(run_dir, force=args.force, fresh=args.fresh)

    stages = STAGES if args.stage == "all" else (args.stage,)
    for stage in stages:
        raise SystemExit(f"stage '{stage}' is not implemented yet (lands in S2+)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
