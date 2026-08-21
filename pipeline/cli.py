"""Entry point: arg parsing, stages, per-repo run directory + state.

Dispatches the hygiene/knowledge/tasks/report stages over a resumable per-repo state
file, with config overrides from the command line. ``run.sh`` wraps this module.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import fields, is_dataclass
from pathlib import Path

from pipeline import log as plog
from pipeline.config import DEFAULT, Config
from pipeline.log import STAGE, log

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
    p.add_argument("--no-testgen", action="store_true", help="skip P1 test generation")
    p.add_argument("--no-lint", action="store_true", help="skip P1 lint/format")
    p.add_argument(
        "--no-report-draft", action="store_true", help="skip the BIG REPORT narrative draft"
    )
    p.add_argument(
        "--min-failing-tests",
        type=int,
        default=None,
        help="fail-before must have at least this many failing tests (harness.min_failing_tests)",
    )
    p.add_argument(
        "--prune-images",
        action="store_true",
        help="after the run, prune ONLY dangling images carrying this pipeline's build label",
    )
    p.add_argument("--quiet", action="store_true", help="stage-level progress lines only")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    load_dotenv()
    config = DEFAULT
    apply_overrides(config, args.set)
    config.llm.disk_cache = config.llm.disk_cache or args.llm_cache
    config.excision.strip_docstring = config.excision.strip_docstring or args.excision_hard
    config.harness.verifier_visibility = args.verifier_visibility
    if args.no_testgen:
        config.testgen.enabled = False
    if args.no_lint:
        config.lint.enabled = False
    if args.no_report_draft:
        config.report.draft_narrative = False
    if args.min_failing_tests is not None:
        config.harness.min_failing_tests = args.min_failing_tests
    if args.quiet:
        plog.threshold = STAGE

    stages = STAGES if args.stage == "all" else (args.stage,)
    run_dir = OUTPUT_ROOT / repo_name(args.repo)
    log("run", "", f"repo {args.repo} run_dir {run_dir} stages {','.join(stages)}", STAGE)
    t0 = time.monotonic()
    for stage in stages:
        ts = time.monotonic()
        log(stage, "", "start", STAGE)
        if stage == "hygiene":
            _run_hygiene(args, config)
        elif stage == "knowledge":
            _run_knowledge(args, config)
        else:
            _run_tasks(args, config)
        log(stage, "", f"done in {time.monotonic() - ts:.1f}s", STAGE)
    if args.prune_images:
        from pipeline.docker.image import prune_dangling_bench_images

        removed = prune_dangling_bench_images()
        print(f"pruned {removed} dangling bench-pipeline image(s)")
    _print_summary(run_dir, config, stages, time.monotonic() - t0)
    return 0


def _run_hygiene(args: argparse.Namespace, config: Config) -> None:
    from pipeline.hygiene.context import build_context
    from pipeline.hygiene.runner import run_hygiene, verify_twice

    ctx = build_context(
        args.repo, config=config, force=tuple(args.force), fresh=args.fresh, output_root=OUTPUT_ROOT
    )
    base = (ctx.report.get("base_sha") or "")[:7]
    log("hygiene", "", f"run_dir {ctx.run_dir} image {ctx.image_tag} base {base}", STAGE)
    run_hygiene(ctx)
    print(f"hygiene done: {ctx.run_dir}")
    if args.verify_twice:
        log("hygiene", "verify_twice", "start", STAGE)
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


def _run_tasks(args: argparse.Namespace, config: Config) -> None:
    from pipeline.hygiene.context import build_context
    from pipeline.tasks.runner import repo_tasks_dir, run_tasks

    ctx = build_context(
        args.repo,
        config=config,
        force=tuple(args.force),
        fresh=args.fresh,
        output_root=OUTPUT_ROOT,
        llm_stage="tasks",
    )
    try:
        run_tasks(ctx)
    except SystemExit:
        # Selection infeasibility is a hard error, but the report over what WAS
        # built is still worth having.
        _build_report(ctx)
        raise
    summary = ctx.report.get("tasks", {}).get("validate", {})
    valid, total = summary.get("valid", 0), summary.get("tasks", 0)
    print(f"tasks done: {repo_tasks_dir(ctx)} ({valid}/{total} VALID)")
    _build_report(ctx)


def _stage_steps() -> dict[str, tuple[str, ...]]:
    from pipeline.hygiene import runner as hy
    from pipeline.knowledge import runner as kn
    from pipeline.tasks import runner as tk

    return {
        "hygiene": tuple(name for name, _, _ in hy._STEPS),
        "knowledge": tuple(kn._STEPS),
        "tasks": tuple(tk._STEPS),
    }


def _print_summary(run_dir: Path, config: Config, stages: tuple[str, ...], elapsed: float) -> None:
    """Compact end-of-run summary from report_data.json + audit/llm_usage.json; never raises."""
    log("summary", "", f"total {elapsed:.0f}s", STAGE)
    try:
        _summary_lines(run_dir, config, stages)
    except Exception as exc:  # noqa: BLE001 - summary is best effort
        log("summary", "", f"unavailable ({type(exc).__name__})", STAGE)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text()) if path.is_file() else {}


def _summary_lines(run_dir: Path, config: Config, stages: tuple[str, ...]) -> None:
    data = _read_json(run_dir / "report_data.json")
    usage = _read_json(run_dir / "audit" / "llm_usage.json")
    steps = data.get("stages") or {}
    for stage in stages:
        parts = []
        for name in _stage_steps().get(stage, ()):
            rec = steps.get(name) or {}
            if rec.get("skipped"):
                parts.append(f"{name}=skipped")
            elif "duration_s" in rec:
                parts.append(f"{name}={rec['duration_s']:.0f}s")
        if parts:
            log("summary", stage, " ".join(parts), STAGE)
    by_tier: dict[str, int] = {}
    for step, u in usage.items():
        if step == "_total" or not isinstance(u, dict):
            continue
        tier = config.step_model.get(step, "other")
        by_tier[tier] = by_tier.get(tier, 0) + int(u.get("total_tokens") or 0)
    total = (usage.get("_total") or {}).get("total_tokens", sum(by_tier.values()))
    tiers = " ".join(f"{t}={n}" for t, n in sorted(by_tier.items()))
    log("summary", "llm", f"tokens total={total} {tiers}".rstrip(), STAGE)
    tasks = data.get("tasks") or {}
    val = tasks.get("validate") or {}
    if val:
        log("summary", "tasks", f"VALID {val.get('valid')}/{val.get('tasks')}", STAGE)
    sel = tasks.get("select") or {}
    if sel.get("selected"):
        log(
            "summary",
            "select",
            f"{len(sel['selected'])} selected: {', '.join(sel['selected'])}",
            STAGE,
        )


def _build_report(ctx) -> None:
    """Enrich report_data.json + render output/<repo>/REPORT.md. A drafting failure
    never breaks the run — the report is still written from the tables alone."""
    from pipeline.report import build as report_build

    llm = ctx.llm if ctx.config.report.draft_narrative else None
    try:
        _, md = report_build.build(ctx.run_dir, ctx.config, llm=llm)
    except Exception as exc:  # noqa: BLE001 - report must never fail the pipeline
        _, md = report_build.build(ctx.run_dir, ctx.config, llm=None)
        print(f"report narrative draft skipped: {str(exc)[:200]}")
    ctx.llm.write_usage()
    print(f"report: {md}")


if __name__ == "__main__":
    sys.exit(main())
