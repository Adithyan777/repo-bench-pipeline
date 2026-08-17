"""P3 stage runner: excision funnel -> build -> validate -> manifest (S4 scope).

Mirrors the hygiene/knowledge runners: resumable via state.py with a pipeline-code
fingerprint in every step's input hash; per-step timing + LLM usage into
report_data.json. History/net-new funnels, LLM instructions and selection land later.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path

from pipeline.ecosystems.source_ops import ExciseError
from pipeline.hygiene.context import HygieneContext
from pipeline.knowledge.runner import knowledge_paths
from pipeline.state import code_fingerprint, hash_inputs
from pipeline.tasks import excision
from pipeline.tasks.build_excision import BuildInputs, build_task
from pipeline.tasks.harness import validate_tasks
from pipeline.tasks.manifest import write_manifest

_STEPS = ("excision_funnel", "build_excision", "validate", "manifest")


def tasks_root(ctx: HygieneContext) -> Path:
    return Path(ctx.config.tasks.tasks_root)


def repo_tasks_dir(ctx: HygieneContext) -> Path:
    return tasks_root(ctx) / ctx.run_dir.name


def run_tasks(ctx: HygieneContext) -> HygieneContext:
    _load_existing_report(ctx)
    for name in _STEPS:
        _run_step(ctx, name)
    ctx.llm.write_usage()
    _write_report(ctx)
    return ctx


def _run_step(ctx: HygieneContext, name: str) -> None:
    input_hash = _input_hash(ctx, name)
    stage = ctx.report["stages"].setdefault(name, {})
    if not ctx.state.should_run(name, input_hash):
        stage["skipped"] = True
        return
    start = time.monotonic()
    _STEP_FUNCS[name](ctx)
    stage["skipped"] = False
    stage["duration_s"] = round(time.monotonic() - start, 2)
    ctx.state.mark_done(name, input_hash)


# --- steps ----------------------------------------------------------------------


def _candidates_path(ctx: HygieneContext) -> Path:
    return ctx.tasks_dir / ctx.config.tasks.candidates_filename


def _built_path(ctx: HygieneContext) -> Path:
    return ctx.tasks_dir / "built.json"


def step_excision_funnel(ctx: HygieneContext) -> None:
    kp = knowledge_paths(ctx.run_dir, ctx.config)
    symbols = json.loads(Path(kp["symbols"]).read_text())
    test_map = json.loads(Path(kp["test_map"]).read_text())
    baseline = _baseline(ctx)
    results = baseline.get("results") or {}
    passing = {t for t, r in results.items() if r.get("status") == "pass"}
    candidates = excision.funnel(symbols, test_map, passing, ctx.config, repo=ctx.repo)
    ranked = excision.rank(candidates, ctx.config)
    decisions = _prior_screen_decisions(ctx)
    prior_keys = set(decisions)
    selected = excision.screen(ranked, ctx.repo, ctx.llm, ctx.config, decisions)
    ctx.tasks_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "selected": [c.qualname for c in selected],
        "ranked": [c.qualname for c in ranked],
        "counts": _counts(candidates),
        "screen_reused": sum(1 for c in ranked if c.screen_key in prior_keys),
        "candidates": excision.candidates_json(candidates),
    }
    _candidates_path(ctx).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    ctx.report.setdefault("tasks", {})["excision_funnel"] = {
        "considered": len(candidates),
        "ranked": len(ranked),
        "selected": len(selected),
        "counts": data["counts"],
    }


def _counts(candidates: list) -> dict[str, int]:
    counts: dict[str, int] = {}
    for c in candidates:
        status = c["status"] if isinstance(c, dict) else c.status
        reason = c["reject_reason"] if isinstance(c, dict) else c.reject_reason
        key = status if status != "rejected" else f"rejected:{(reason or '').split('(')[0]}"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _prior_screen_decisions(ctx: HygieneContext) -> dict[str, dict]:
    """Screen decisions from the previous candidates.json, keyed by content hash, so a
    rerun spends no LLM tokens on unchanged candidates. Ignored on --force / --fresh."""
    path = _candidates_path(ctx)
    if not ctx.config.excision.reuse_screen_decisions or not path.is_file():
        return {}
    if ctx.state.fresh or "excision_funnel" in ctx.state.force:
        return {}
    prior = json.loads(path.read_text())
    return {
        c["screen_key"]: c["screen"]
        for c in prior.get("candidates", [])
        if c.get("screen_key") and c.get("screen")
    }


def step_build_excision(ctx: HygieneContext) -> None:
    data = json.loads(_candidates_path(ctx).read_text())
    by_name = {c["qualname"]: c for c in data["candidates"]}
    kp = knowledge_paths(ctx.run_dir, ctx.config)
    build = ctx.load("build")
    inp = BuildInputs(
        repo=ctx.repo,
        repo_name=ctx.run_dir.name,
        base_sha=ctx.report.get("base_sha", ""),
        image_tag=build.get("image_tag", ctx.image_tag),
        image_digest=build.get("image_digest", ""),
        graph=json.loads(Path(kp["graph"]).read_text()),
        baseline=_baseline(ctx),
        knowledge_dir=ctx.knowledge_dir,
        audit_dir=ctx.audit_dir,
        llm=ctx.llm,
    )
    built: dict[str, dict] = {}
    for qual in data["selected"]:
        c = excision.Candidate(**{k: v for k, v in by_name[qual].items()})
        try:
            path = build_task(c, inp, tasks_root(ctx), ctx.config)
            built[qual] = {"task_dir": str(path), "task_id": path.name}
        except ExciseError as exc:
            built[qual] = {"task_dir": None, "reject_reason": f"unsplittable: {exc}"}
            by_name[qual]["status"] = "rejected"
            by_name[qual]["reject_reason"] = f"unsplittable({exc})"
    data["counts"] = _counts(data["candidates"])
    data["selected"] = [q for q in data["selected"] if built[q]["task_dir"]]
    _prune_stale(ctx, {b["task_id"] for b in built.values() if b["task_dir"]})
    _candidates_path(ctx).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    _built_path(ctx).write_text(json.dumps(built, indent=2, sort_keys=True) + "\n")
    ctx.report.setdefault("tasks", {})["build_excision"] = {
        "built": sum(1 for b in built.values() if b["task_dir"]),
        "unsplittable": sum(1 for b in built.values() if not b["task_dir"]),
    }


def _prune_stale(ctx: HygieneContext, keep: set[str]) -> None:
    """Excision task folders from an earlier build that were not rebuilt are removed,
    so tasks/<repo>/ and tasks.json reflect exactly this run's selection."""
    prefix = ctx.config.tasks.excision_id_prefix + "-"
    root = repo_tasks_dir(ctx)
    if not root.is_dir():
        return
    for path in root.iterdir():
        if path.is_dir() and path.name.startswith(prefix) and path.name not in keep:
            shutil.rmtree(path)


def step_validate(ctx: HygieneContext) -> None:
    dirs = _task_dirs(ctx)
    verdicts = validate_tasks(dirs, ctx.config)
    summary = {
        Path(d).name: {"valid": v["valid"], "reasons": v["reasons"]} for d, v in verdicts.items()
    }
    ctx.report.setdefault("tasks", {})["validate"] = {
        "tasks": len(summary),
        "valid": sum(1 for v in summary.values() if v["valid"]),
        "verdicts": dict(sorted(summary.items())),
    }


def step_manifest(ctx: HygieneContext) -> None:
    out = repo_tasks_dir(ctx)
    out.mkdir(parents=True, exist_ok=True)
    path = write_manifest(out, ctx.config)
    ctx.report.setdefault("tasks", {})["manifest"] = str(path)


_STEP_FUNCS = {
    "excision_funnel": step_excision_funnel,
    "build_excision": step_build_excision,
    "validate": step_validate,
    "manifest": step_manifest,
}


# --- input hashes ------------------------------------------------------------------


def _input_hash(ctx: HygieneContext, step: str) -> str:
    fingerprint = code_fingerprint(ctx.config.tasks.code_fingerprint_files)
    return hash_inputs("tk-code", fingerprint, _step_input_hash(ctx, step))


def _step_input_hash(ctx: HygieneContext, step: str) -> str:
    kp = knowledge_paths(ctx.run_dir, ctx.config)
    hy = ctx.hygiene_dir
    if step == "excision_funnel":
        return hash_inputs(
            Path(kp["symbols"]),
            Path(kp["test_map"]),
            hy / "baseline.json",
            repr(ctx.config.excision),
            repr(ctx.config.llm.classify_batch_size),
            ctx.config.model_for(excision.SCREEN_STEP),
        )
    if step == "build_excision":
        return hash_inputs(
            _candidates_path(ctx),
            hy / "build.json",
            _head(ctx.repo),
            repr(ctx.config.excision),
            repr(ctx.config.tasks),
            repr(ctx.config.harness),
        )
    if step == "validate":
        parts: list[Path | str] = [repr(ctx.config.harness), hy / "build.json"]
        for d in _task_dirs(ctx):
            parts.append(d / ctx.config.tasks.task_json)
            parts.extend(sorted(p for p in (d / "verifier").rglob("*") if p.is_file()))
            parts.extend(sorted(p for p in (d / "input").rglob("*.py") if p.is_file()))
        return hash_inputs(*parts)
    if step == "manifest":
        parts = []
        for d in _task_dirs(ctx):
            parts.append(
                d / ctx.config.harness.evidence_dirname / ctx.config.harness.verdict_filename
            )
        return hash_inputs(*parts, repr(ctx.config.tasks))
    raise KeyError(step)


def _task_dirs(ctx: HygieneContext) -> list[Path]:
    if not _built_path(ctx).is_file():
        return []
    built = json.loads(_built_path(ctx).read_text())
    return sorted(Path(b["task_dir"]) for b in built.values() if b.get("task_dir"))


def _baseline(ctx: HygieneContext) -> dict:
    path = ctx.hygiene_dir / "baseline.json"
    return json.loads(path.read_text()) if path.is_file() else {}


def _head(repo: Path) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    )
    return proc.stdout.strip() if proc.returncode == 0 else ""


def _load_existing_report(ctx: HygieneContext) -> None:
    path = ctx.run_dir / "report_data.json"
    if path.is_file():
        existing = json.loads(path.read_text())
        existing.update({k: v for k, v in ctx.report.items() if k != "stages"})
        existing.setdefault("stages", {}).update(ctx.report.get("stages", {}))
        ctx.report.clear()
        ctx.report.update(existing)
    ctx.report.setdefault("stages", {})


def _write_report(ctx: HygieneContext) -> None:
    usage_path = ctx.audit_dir / "llm_usage.json"
    if usage_path.is_file():
        ctx.report["llm_usage"] = json.loads(usage_path.read_text())
    (ctx.run_dir / "report_data.json").write_text(json.dumps(ctx.report, indent=2, sort_keys=True))
