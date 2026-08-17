"""Hygiene stage runner: detect -> pin -> dockerfile -> compose -> build -> baseline
-> testgen -> lint. Steps are resumable via state.py; pipeline edits become labeled
commits, original HEAD is recorded so history mining sees only original commits.
Timing + LLM usage go to output/<repo>/report_data.json.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from pipeline.hygiene import baseline, build, compose, detect, dockerfile, lint, pin, testgen
from pipeline.hygiene.context import (
    HygieneContext,
    commit_pipeline_changes,
)
from pipeline.log import fmt_counts, log, step_skipped, step_start
from pipeline.state import code_fingerprint, hash_inputs

STAGE = "hygiene"

# (name, module, commit_label): a label commits working-tree edits so far as one pipeline commit.
_STEPS = [
    ("detect", detect, None),
    ("pin", pin, None),
    ("dockerfile", dockerfile, None),
    ("compose", compose, "pipeline: pin dependencies and containerize"),
    ("build", build, None),
    ("baseline", baseline, "pipeline: baseline and quarantine"),
    ("testgen", testgen, "pipeline: generated tests"),
    ("lint", lint, "pipeline: lint and format"),
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
                log(STAGE, name, f"pipeline commit {sha[:7]}")

    ctx.record("pipeline_base", {"base_sha": base_sha, "pipeline_commits": pipeline_commits})
    ctx.llm.write_usage()
    _write_report(ctx)
    return ctx


def _run_step(ctx: HygieneContext, name: str, module) -> None:
    # Fingerprint the hygiene code so a fix invalidates its artifacts, not just inputs.
    fingerprint = code_fingerprint(ctx.config.hygiene_code_files)
    input_hash = hash_inputs("hy-code", fingerprint, module.input_hash(ctx))
    stage = ctx.report["stages"].setdefault(name, {})
    if not ctx.state.should_run(name, input_hash):
        stage["skipped"] = True
        step_skipped(STAGE, name)
        return
    start = time.monotonic()
    step = step_start(STAGE, name, ctx.llm)
    data = module.run(ctx)
    stage["skipped"] = False
    stage["duration_s"] = round(time.monotonic() - start, 2)
    ctx.state.mark_done(name, input_hash)
    step.done(_step_summary(name, data))


def _step_summary(name: str, data) -> str:
    """One-line facts from a step's result dict; '' when the shape is unexpected."""
    if not isinstance(data, dict):
        return ""
    if name == "detect":
        return fmt_counts(data, ("packaging_style", "python_version", "test_framework"))
    if name == "pin":
        return fmt_counts(data, ("pin_count", "python_version"))
    if name == "dockerfile":
        return fmt_counts(data, ("base_image",))
    if name == "build":
        return fmt_counts(data, ("outcome", "attempts"))
    if name == "baseline":
        return fmt_counts(data.get("counts"))
    if name == "testgen":
        if not data.get("enabled", True):
            return "disabled"
        return fmt_counts(data.get("counts")) or fmt_counts(data, ("skipped",))
    if name == "lint":
        if not data.get("enabled", True):
            return "disabled"
        noqa = sum(len(v) for v in (data.get("noqa") or {}).values())
        facts = f"files_changed={len(data.get('files_changed') or [])} noqa={noqa}"
        return f"{facts} {fmt_counts(data, ('clean', 'regressed', 'reverted'))}".rstrip()
    return ""


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
    """Paths to the hygiene artifacts the knowledge stage consumes."""
    return {
        "repo": str(run_dir / "repo"),
        "detect": str(run_dir / "hygiene" / "detect.json"),
        "baseline": str(run_dir / "hygiene" / "baseline.json"),
        "pipeline_base": str(run_dir / "hygiene" / "pipeline_base.json"),
        "build": str(run_dir / "hygiene" / "build.json"),
        "testgen": str(run_dir / "hygiene" / "testgen.json"),
        "testgen_targets": str(run_dir / "hygiene" / "testgen_targets.json"),
        "lint": str(run_dir / "hygiene" / "lint.json"),
    }
