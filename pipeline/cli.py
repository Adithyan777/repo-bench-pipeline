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

STAGES = ("hygiene", "knowledge", "tasks")
OUTPUT_ROOT = Path("output")


def repo_name(repo: str) -> str:
    return sanitize_name(Path(repo.rstrip("/")).name.removesuffix(".git"))


def sanitize_name(name: str) -> str:
    """Safe run-dir + docker-tag component: lowercase, [a-z0-9._-], non-empty."""
    import re

    slug = re.sub(r"[^a-z0-9._-]+", "-", name.lower()).strip("-.")
    slug = re.sub(r"-{2,}", "-", slug)
    if slug in ("", ".", ".."):
        raise SystemExit(f"cannot derive a safe repo name from {name!r}")
    return slug


def load_dotenv(path: Path = Path(".env")) -> None:
    """Load KEY=VALUE lines from .env into the environment (does not override)."""
    import os

    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


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
    p.add_argument(
        "--verify-twice", action="store_true", help="after hygiene, run the test command twice"
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    load_dotenv()
    config = DEFAULT
    apply_overrides(config, args.set)
    config.llm.disk_cache = config.llm.disk_cache or args.llm_cache
    config.excision.strip_docstring = config.excision.strip_docstring or args.excision_hard
    config.harness.verifier_visibility = args.verifier_visibility

    stages = STAGES if args.stage == "all" else (args.stage,)
    for stage in stages:
        if stage == "hygiene":
            _run_hygiene(args, config)
        elif stage == "knowledge":
            _run_knowledge(args, config)
        else:
            raise SystemExit(f"stage '{stage}' is not implemented yet (lands in S4+)")
    return 0


def _run_hygiene(args: argparse.Namespace, config: Config) -> None:
    from pipeline.hygiene.context import build_context
    from pipeline.hygiene.runner import run_hygiene, verify_twice

    ctx = build_context(
        args.repo, config=config, force=tuple(args.force), fresh=args.fresh, output_root=OUTPUT_ROOT
    )
    run_hygiene(ctx)
    print(f"hygiene done: {ctx.run_dir}")
    if args.verify_twice:
        ok = verify_twice(ctx)
        print(f"verify-twice identical: {ok}")
        if not ok:
            raise SystemExit("twice-run verdicts differ")


def _run_knowledge(args: argparse.Namespace, config: Config) -> None:
    from pipeline.hygiene.context import build_context
    from pipeline.knowledge.runner import run_knowledge

    ctx = build_context(
        args.repo, config=config, force=tuple(args.force), fresh=args.fresh, output_root=OUTPUT_ROOT
    )
    run_knowledge(ctx)
    print(f"knowledge done: {ctx.run_dir}")


if __name__ == "__main__":
    sys.exit(main())
