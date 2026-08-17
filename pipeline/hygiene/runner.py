"""Hygiene stage runner: detect -> pin -> dockerfile -> compose -> build -> baseline.

Each step is resumable via state.py (skip-if-unchanged, --force, --fresh). Pipeline
edits to the repo clone are committed as labeled commits after they are produced, and
the original HEAD is recorded so P3 mines only original history. Per-stage timing and
LLM usage land in output/<repo>/report_data.json.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from pipeline.hygiene import baseline, build, compose, detect, dockerfile, pin
from pipeline.hygiene.context import (
    HygieneContext,
    commit_pipeline_changes,
)

# (name, module, commit_label_after) — commit_label groups working-tree edits into
# one labeled pipeline commit once that step (and its peers) have written their files.
_STEPS = [
    ("detect", detect, None),
    ("pin", pin, None),
    ("dockerfile", dockerfile, None),
    ("compose", compose, "pipeline: pin dependencies and containerize"),
    ("build", build, None),
    ("baseline", baseline, "pipeline: baseline and quarantine"),
]


def run_hygiene(ctx: HygieneContext) -> HygieneContext:
    base_sha = ctx.report.get("base_sha", "")
    pipeline_commits: list[str] = []

    for name, module, commit_label in _STEPS:
        _run_step(ctx, name, module)
        if commit_label:
            sha = commit_pipeline_changes(ctx, commit_label)
            if sha:
                pipeline_commits.append(sha)

    ctx.record("pipeline_base", {"base_sha": base_sha, "pipeline_commits": pipeline_commits})
    ctx.llm.write_usage()
    _write_report(ctx)
    return ctx


def _run_step(ctx: HygieneContext, name: str, module) -> None:
    input_hash = module.input_hash(ctx)
    stage = ctx.report["stages"].setdefault(name, {})
    if not ctx.state.should_run(name, input_hash):
        stage["skipped"] = True
        return
    start = time.monotonic()
    module.run(ctx)
    stage["skipped"] = False
    stage["duration_s"] = round(time.monotonic() - start, 2)
    ctx.state.mark_done(name, input_hash)


def _write_report(ctx: HygieneContext) -> None:
    usage_path = ctx.audit_dir / "llm_usage.json"
    ctx.report["llm_usage"] = json.loads(usage_path.read_text()) if usage_path.is_file() else {}
    (ctx.run_dir / "report_data.json").write_text(json.dumps(ctx.report, indent=2, sort_keys=True))


def verify_twice(ctx: HygieneContext) -> bool:
    """Run the documented command twice on the built image; True if identical."""
    quarantined = []
    baseline_path = ctx.hygiene_dir / "baseline.json"
    if baseline_path.is_file():
        quarantined = json.loads(baseline_path.read_text()).get("quarantined", [])
    if ctx.adapter.test_framework(ctx.repo) == "none":
        return True
    return baseline.run_twice_identical(ctx, quarantined or None)


def hygiene_paths(run_dir: Path) -> dict:
    """Where S3 finds what it needs."""
    return {
        "repo": str(run_dir / "repo"),
        "detect": str(run_dir / "hygiene" / "detect.json"),
        "baseline": str(run_dir / "hygiene" / "baseline.json"),
        "pipeline_base": str(run_dir / "hygiene" / "pipeline_base.json"),
        "build": str(run_dir / "hygiene" / "build.json"),
    }
