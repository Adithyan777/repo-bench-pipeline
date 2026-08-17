"""Tasks stage runner: excision funnel -> build -> history funnel -> build -> validate ->
instruct -> select -> manifest.

Resumable via state.py with a pipeline-code fingerprint in every step's input hash;
per-step timing + LLM usage into report_data.json.
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
from pipeline.log import fmt_counts, log, step_skipped, step_start
from pipeline.state import code_fingerprint, hash_inputs
from pipeline.tasks import difficulty as D
from pipeline.tasks import excision
from pipeline.tasks import history as H
from pipeline.tasks import instruction as I
from pipeline.tasks.build_excision import BuildInputs, build_task
from pipeline.tasks.build_history import build_history_task
from pipeline.tasks.harness import validate_tasks
from pipeline.tasks.manifest import write_manifest
from pipeline.tasks.select import SelectionInfeasible, run_selection

STAGE = "tasks"
_STEPS = (
    "excision_funnel",
    "build_excision",
    "history_funnel",
    "build_history",
    "validate",
    "instruct",
    "manifest",
    "select",
)

# Written by the instruct step; excluded from validate/instruct input hashes so those
# steps do not invalidate themselves.
_INSTRUCT_FIELDS = (
    "title",
    "instruction",
    "instruction_status",
    "instruction_review",
    "instruction_attempts",
    "difficulty",
    "difficulty_rationale",
    "difficulty_features",
    "difficulty_status",
    "verifier_visibility",
)


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
        step_skipped(STAGE, name)
        return
    start = time.monotonic()
    step = step_start(STAGE, name, ctx.llm)
    _STEP_FUNCS[name](ctx)
    stage["skipped"] = False
    stage["duration_s"] = round(time.monotonic() - start, 2)
    ctx.state.mark_done(name, input_hash)
    step.done()


# --- steps ----------------------------------------------------------------------


def _candidates_path(ctx: HygieneContext) -> Path:
    return ctx.tasks_dir / ctx.config.tasks.candidates_filename


def _built_path(ctx: HygieneContext) -> Path:
    return ctx.tasks_dir / "built.json"


def _history_candidates_path(ctx: HygieneContext) -> Path:
    return ctx.tasks_dir / ctx.config.tasks.history_candidates_filename


def _built_history_path(ctx: HygieneContext) -> Path:
    return ctx.tasks_dir / "built_history.json"


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
    log(
        STAGE,
        "excision_funnel",
        f"considered {len(candidates)}, ranked {len(ranked)}, "
        f"selected {len(selected)} (screen reused {data['screen_reused']})",
    )
    log(STAGE, "excision_funnel", fmt_counts(data["counts"]))


def _counts(candidates: list) -> dict[str, int]:
    counts: dict[str, int] = {}
    for c in candidates:
        status = c["status"] if isinstance(c, dict) else c.status
        reason = c["reject_reason"] if isinstance(c, dict) else c.reject_reason
        key = status if status != "rejected" else f"rejected:{(reason or '').split('(')[0]}"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _prior_screen_decisions(ctx: HygieneContext) -> dict[str, dict]:
    """Screen decisions from the previous candidates.json (content-hash keyed) so reruns spend
    no tokens on unchanged candidates. Ignored on --force / --fresh."""
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


def _build_inputs(ctx: HygieneContext, decisions: dict | None = None) -> BuildInputs:
    kp = knowledge_paths(ctx.run_dir, ctx.config)
    build = ctx.load("build")
    return BuildInputs(
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
        cache_dir=ctx.tasks_dir / "agent_cache",
        decisions=decisions,
        transcripts_dir=getattr(ctx.llm, "transcripts_dir", None) or Path("transcripts"),
    )


def step_build_excision(ctx: HygieneContext) -> None:
    data = json.loads(_candidates_path(ctx).read_text())
    by_name = {c["qualname"]: c for c in data["candidates"]}
    inp = _build_inputs(ctx)
    built: dict[str, dict] = {}
    for qual in data["selected"]:
        c = excision.Candidate(**{k: v for k, v in by_name[qual].items()})
        try:
            path = build_task(c, inp, tasks_root(ctx), ctx.config)
            built[qual] = {"task_dir": str(path), "task_id": path.name}
            log(STAGE, "build_excision", f"{path.name} built")
        except ExciseError as exc:
            built[qual] = {"task_dir": None, "reject_reason": f"unsplittable: {exc}"}
            log(STAGE, "build_excision", f"{qual} rejected: unsplittable ({str(exc)[:120]})")
            by_name[qual]["status"] = "rejected"
            by_name[qual]["reject_reason"] = f"unsplittable({exc})"
    data["counts"] = _counts(data["candidates"])
    data["selected"] = [q for q in data["selected"] if built[q]["task_dir"]]
    _prune_stale(
        ctx,
        ctx.config.tasks.excision_id_prefix,
        {b["task_id"] for b in built.values() if b["task_dir"]},
    )
    _candidates_path(ctx).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    _built_path(ctx).write_text(json.dumps(built, indent=2, sort_keys=True) + "\n")
    ctx.report.setdefault("tasks", {})["build_excision"] = {
        "built": sum(1 for b in built.values() if b["task_dir"]),
        "unsplittable": sum(1 for b in built.values() if not b["task_dir"]),
    }
    log(STAGE, "build_excision", fmt_counts(ctx.report["tasks"]["build_excision"]))


def _prune_stale(ctx: HygieneContext, prefix: str, keep: set[str]) -> None:
    """Remove task folders (of one source type) from an earlier build that were not rebuilt."""
    root = repo_tasks_dir(ctx)
    if not root.is_dir():
        return
    for path in root.iterdir():
        if path.is_dir() and path.name.startswith(prefix + "-") and path.name not in keep:
            shutil.rmtree(path)


def step_history_funnel(ctx: HygieneContext) -> None:
    kp = knowledge_paths(ctx.run_dir, ctx.config)
    history = json.loads(Path(kp["history_index"]).read_text())
    test_map = json.loads(Path(kp["test_map"]).read_text())
    symbols = json.loads(Path(kp["symbols"]).read_text())
    results = _baseline(ctx).get("results") or {}
    passing = {t for t, r in results.items() if r.get("status") == "pass"}
    base_sha = ctx.report.get("base_sha", "")
    cands = H.funnel(history, test_map, passing, ctx.repo, base_sha, ctx.config, symbols)
    order = H.ranked(cands)
    decisions = _prior_classify_decisions(ctx)
    prior_keys = set(decisions)
    kept = H.classify(order, ctx.repo, ctx.llm, ctx.config, decisions)
    if ctx.config.history.prefer_pr_merge_over_constituents:
        kept = H.supersede_constituents(cands, kept, ctx.repo)
    short = H.shortlist(kept, ctx.config)
    ctx.tasks_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "shortlist": [c.sha for c in short],
        "kept": [c.sha for c in kept],
        "counts": _counts(cands),
        "classify_reused": sum(1 for c in order if c.classify_key in prior_keys),
        "candidates": H.candidates_json(cands),
    }
    _history_candidates_path(ctx).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    ctx.report.setdefault("tasks", {})["history_funnel"] = {
        "considered": len(cands),
        "survivors": len(order),
        "classified": sum(1 for c in order if c.classify is not None),
        "kept": len(kept),
        "shortlisted": len(short),
        "counts": data["counts"],
    }
    log(
        STAGE,
        "history_funnel",
        f"considered {len(cands)}, survivors {len(order)}, "
        f"kept {len(kept)}, shortlisted {len(short)} (classify reused {data['classify_reused']})",
    )
    log(STAGE, "history_funnel", fmt_counts(data["counts"]))


def _prior_classify_decisions(ctx: HygieneContext) -> dict[str, dict]:
    path = _history_candidates_path(ctx)
    if not ctx.config.history.reuse_classify_decisions or not path.is_file():
        return {}
    if ctx.state.fresh or "history_funnel" in ctx.state.force:
        return {}
    prior = json.loads(path.read_text())
    return {
        c["classify_key"]: c["classify"]
        for c in prior.get("candidates", [])
        if c.get("classify_key") and c.get("classify")
    }


def _prior_build_decisions(ctx: HygieneContext) -> dict[str, dict]:
    path = _built_history_path(ctx)
    if not path.is_file() or ctx.state.fresh or "build_history" in ctx.state.force:
        return {}
    return json.loads(path.read_text()).get("_decisions", {})


def step_build_history(ctx: HygieneContext) -> None:
    data = json.loads(_history_candidates_path(ctx).read_text())
    by_sha = {c["sha"]: c for c in data["candidates"]}
    decisions = _prior_build_decisions(ctx)
    inp = _build_inputs(ctx, decisions)
    built: dict[str, dict] = {}
    n_built = 0
    log(
        STAGE,
        "build_history",
        f"shortlist {len(data['shortlist'])}, target {ctx.config.history.build_target}",
    )
    for i, sha in enumerate(data["shortlist"], 1):
        if n_built >= ctx.config.history.build_target:
            break
        c = H.HistoryCandidate(**by_sha[sha])
        log(STAGE, "build_history", f"{i}/{len(data['shortlist'])} {sha[:7]}: building")
        result = build_history_task(c, inp, tasks_root(ctx), ctx.config)
        source = (result.notes or {}).get("verifier_source")
        if result.task_dir:
            n_built += 1
            by_sha[sha]["status"] = "built"
            built[sha] = {"task_dir": str(result.task_dir), "task_id": result.task_id}
            log(
                STAGE,
                "build_history",
                f"{result.task_id} built (verifier {source}), "
                f"{n_built}/{ctx.config.history.build_target}",
            )
        else:
            by_sha[sha]["status"] = "rejected"
            by_sha[sha]["reject_reason"] = result.reject_reason
            built[sha] = {"task_dir": None, "reject_reason": result.reject_reason}
            log(
                STAGE,
                "build_history",
                f"{result.task_id} rejected (verifier {source}): {str(result.reject_reason)[:160]}",
            )
        built[sha]["notes"] = {k: v for k, v in result.notes.items() if k != "overlay"}
    for sha in data["shortlist"]:
        if sha not in built:
            by_sha[sha]["status"] = "surplus"
    data["counts"] = _counts(data["candidates"])
    data["built"] = [s for s in data["shortlist"] if built.get(s, {}).get("task_dir")]
    _prune_stale(
        ctx,
        ctx.config.tasks.history_id_prefix,
        {b["task_id"] for b in built.values() if b.get("task_dir")},
    )
    _history_candidates_path(ctx).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    built["_decisions"] = decisions
    _built_history_path(ctx).write_text(json.dumps(built, indent=2, sort_keys=True) + "\n")
    rejected: dict[str, int] = {}
    for b in built.values():
        if isinstance(b, dict) and b.get("task_dir") is None and b.get("reject_reason"):
            key = b["reject_reason"].split("(")[0]
            rejected[key] = rejected.get(key, 0) + 1
    log(
        STAGE,
        "build_history",
        f"attempted {len(built) - 1}, built {n_built}, rejected {fmt_counts(rejected) or 0}",
    )
    ctx.report.setdefault("tasks", {})["build_history"] = {
        "attempted": len(built) - 1,
        "built": n_built,
        "rejected": dict(sorted(rejected.items())),
        "verifier_source": {
            b["task_id"]: b["notes"].get("verifier_source")
            for b in built.values()
            if isinstance(b, dict) and b.get("task_dir")
        },
    }


def step_validate(ctx: HygieneContext) -> None:
    dirs = _task_dirs(ctx)
    log(
        STAGE,
        "validate",
        f"{len(dirs)} tasks, {ctx.config.docker.harness_parallel_workers} workers",
    )
    verdicts = validate_tasks(dirs, ctx.config, on_verdict=_log_verdict)
    summary = {
        Path(d).name: {"valid": v["valid"], "reasons": v["reasons"]} for d, v in verdicts.items()
    }
    ctx.report.setdefault("tasks", {})["validate"] = {
        "tasks": len(summary),
        "valid": sum(1 for v in summary.values() if v["valid"]),
        "verdicts": dict(sorted(summary.items())),
    }
    log(STAGE, "validate", f"{ctx.report['tasks']['validate']['valid']}/{len(summary)} VALID")


def _log_verdict(task_dir: Path, verdict: dict) -> None:
    checks = verdict.get("checks") or {}
    fb, pa, det = (
        checks.get("fail_before") or {},
        checks.get("pass_after") or {},
        checks.get("determinism") or {},
    )
    if verdict.get("valid"):
        facts = (
            f"fail-before {fb.get('n_failing', '?')}, pass-after {pa.get('n_passing', '?')}, "
            f"det {det.get('runs', '?')}/{det.get('runs', '?')}"
        )
        log(STAGE, "validate", f"{Path(task_dir).name} VALID ({facts})")
    else:
        log(
            STAGE,
            "validate",
            f"{Path(task_dir).name} INVALID ({', '.join(verdict.get('reasons') or [])})",
        )


def _decisions_path(ctx: HygieneContext) -> Path:
    return ctx.tasks_dir / ctx.config.instruction.decisions_filename


def _verdict_valid(ctx: HygieneContext, task_dir: Path) -> bool:
    hc = ctx.config.harness
    path = task_dir / hc.evidence_dirname / hc.verdict_filename
    return path.is_file() and bool(json.loads(path.read_text()).get("valid"))


def step_instruct(ctx: HygieneContext) -> None:
    """Instruction + leak gates + golden rationale + difficulty for every VALID task; decisions
    persisted in instructions.json by content hash."""
    cfg = ctx.config
    dpath = _decisions_path(ctx)
    forced = ctx.state.fresh or "instruct" in ctx.state.force
    decisions = json.loads(dpath.read_text()) if dpath.is_file() and not forced else {}
    kp = knowledge_paths(ctx.run_dir, cfg)
    graph = json.loads(Path(kp["graph"]).read_text())
    dirs = [
        d for d in _task_dirs(ctx) if not cfg.instruction.only_valid_tasks or _verdict_valid(ctx, d)
    ]
    stats: dict = {"tasks": len(dirs), "final": 0, "failed": 0, "regenerations": 0, "reused": 0}
    stats["leak_rejections"] = 0
    stats["reviewer_rejections"] = 0
    items: list[tuple[I.TaskFacts, dict]] = []
    for d in dirs:
        facts = I.task_facts(d, cfg)
        rec = I.write_instruction(facts, ctx.llm, cfg, decisions)
        task = facts.task
        if rec["status"] == cfg.instruction.status_final:
            task["title"], task["instruction"] = rec["title"], rec["instruction"]
        task["instruction_status"] = rec["status"]  # failed: template text stays
        task["verifier_visibility"] = cfg.harness.verifier_visibility
        task["instruction_review"] = rec.get("review")
        task["instruction_attempts"] = rec.get("attempts")
        stats["final" if rec["status"] == cfg.instruction.status_final else "failed"] += 1
        stats["reused"] += int(bool(rec.get("reused")))
        stats["regenerations"] += max(0, len(rec.get("attempts") or []) - 1)
        log(
            STAGE,
            "instruct",
            f"{d.name}: {rec['status']} "
            f"(attempts {len(rec.get('attempts') or [])}"
            f"{', reused' if rec.get('reused') else ''})",
        )
        for a in rec.get("attempts") or []:
            if any(not i.startswith("reviewer:") for i in a["issues"]):
                stats["leak_rejections"] += 1
            elif a["issues"]:
                stats["reviewer_rejections"] += 1
        why = I.golden_rationale(facts, ctx.llm, cfg, decisions)
        I.apply_golden(d, why, cfg)
        items.append((facts, D.features(facts, graph, cfg)))
        _write_task(d, task, cfg)
        _flush(dpath, decisions)
    labels = D.label_tasks(items, ctx.llm, cfg, decisions)
    spread: dict[str, int] = {}
    for facts, _ in items:
        lab = labels[facts.task["id"]]
        task = json.loads((facts.task_dir / cfg.tasks.task_json).read_text())
        task["difficulty"] = lab["difficulty"]
        task["difficulty_rationale"] = lab["rationale"]
        task["difficulty_features"] = lab["features"]
        task["difficulty_status"] = lab["status"]
        _write_task(facts.task_dir, task, cfg)
        spread[lab["difficulty"] or "failed"] = spread.get(lab["difficulty"] or "failed", 0) + 1
    _flush(dpath, decisions)
    stats["difficulty_spread"] = dict(sorted(spread.items()))
    stats["difficulty_failed"] = spread.get("failed", 0)
    ctx.report.setdefault("tasks", {})["instruct"] = stats
    log(
        STAGE,
        "instruct",
        fmt_counts(
            stats,
            (
                "tasks",
                "final",
                "failed",
                "regenerations",
                "reused",
                "leak_rejections",
                "reviewer_rejections",
            ),
        ),
    )
    log(STAGE, "instruct", f"difficulty {fmt_counts(stats['difficulty_spread'])}")


def _write_task(task_dir: Path, task: dict, cfg) -> None:
    (task_dir / cfg.tasks.task_json).write_text(json.dumps(task, indent=2, sort_keys=True) + "\n")


def _flush(path: Path, decisions: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(decisions, indent=2, sort_keys=True) + "\n")


def _task_projection(task_json: Path) -> str:
    """task.json minus the instruct-step fields (validate/instruct input hashing)."""
    if not task_json.is_file():
        return ""
    task = json.loads(task_json.read_text())
    return json.dumps({k: v for k, v in task.items() if k not in _INSTRUCT_FIELDS}, sort_keys=True)


def step_manifest(ctx: HygieneContext) -> None:
    out = repo_tasks_dir(ctx)
    out.mkdir(parents=True, exist_ok=True)
    path = write_manifest(out, ctx.config)
    ctx.report.setdefault("tasks", {})["manifest"] = str(path)
    log(STAGE, "manifest", str(path))


def step_select(ctx: HygieneContext) -> None:
    """Pick the final ``selection.total_tasks`` (repo-root tasks.json + selection.json); an
    infeasible quota is a hard error."""
    manifest = repo_tasks_dir(ctx) / ctx.config.tasks.manifest_filename
    root_dir = tasks_root(ctx).parent  # repo root for a real run; the tmp base under tests
    try:
        root, sel_path, result = run_selection(
            ctx.run_dir.name, manifest, ctx.config, root_dir, summary_dir=ctx.tasks_dir
        )
    except SelectionInfeasible as exc:
        ctx.report.setdefault("tasks", {})["select"] = {"error": str(exc)}
        log(STAGE, "select", f"infeasible: {exc}")
        raise SystemExit(f"selection infeasible: {exc}") from exc
    type_counts: dict[str, int] = {}
    for t in result.selected:
        type_counts[t["source_type"]] = type_counts.get(t["source_type"], 0) + 1
    ctx.report.setdefault("tasks", {})["select"] = {
        "root_manifest": str(root),
        "selection": str(sel_path),
        "selected": [t["id"] for t in result.selected],
        "counts": dict(sorted(type_counts.items())),
        "difficulty_spread": result.spread,
        "distinct_modules": result.modules,
    }
    log(
        STAGE,
        "select",
        f"selected {len(result.selected)}: {', '.join(t['id'] for t in result.selected)}",
    )
    log(
        STAGE,
        "select",
        f"types {fmt_counts(type_counts)}; difficulty {fmt_counts(result.spread)}; "
        f"modules {len(result.modules)}; {sel_path}",
    )


_STEP_FUNCS = {
    "excision_funnel": step_excision_funnel,
    "build_excision": step_build_excision,
    "history_funnel": step_history_funnel,
    "build_history": step_build_history,
    "validate": step_validate,
    "instruct": step_instruct,
    "manifest": step_manifest,
    "select": step_select,
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
    if step == "history_funnel":
        return hash_inputs(
            Path(kp["history_index"]),
            Path(kp["test_map"]),
            Path(kp["symbols"]),
            hy / "baseline.json",
            repr(ctx.config.history),
            repr(ctx.config.llm.classify_batch_size),
            ctx.config.model_for(H.CLASSIFY_STEP),
        )
    if step == "build_history":
        return hash_inputs(
            _history_build_input(ctx),
            hy / "build.json",
            _head(ctx.repo),
            repr(ctx.config.history),
            repr(ctx.config.tasks),
            repr(ctx.config.harness),
        )
    if step == "validate":
        parts: list[Path | str] = [repr(ctx.config.harness), hy / "build.json"]
        for d in _task_dirs(ctx):
            parts.append(_task_projection(d / ctx.config.tasks.task_json))
            parts.extend(sorted(p for p in (d / "verifier").rglob("*") if p.is_file()))
            parts.extend(sorted(p for p in (d / "input").rglob("*.py") if p.is_file()))
        return hash_inputs(*parts)
    if step == "instruct":
        parts = [
            repr(ctx.config.instruction),
            repr(ctx.config.difficulty),
            ctx.config.harness.verifier_visibility,
            *(
                ctx.config.model_for(s)
                for s in (I.WRITE_STEP, I.REVIEW_STEP, I.GOLDEN_STEP, D.LABEL_STEP)
            ),
            Path(kp["graph"]),
        ]
        for d in _task_dirs(ctx):
            parts.append(_task_projection(d / ctx.config.tasks.task_json))
            parts.append(
                d / ctx.config.harness.evidence_dirname / ctx.config.harness.verdict_filename
            )
        return hash_inputs(*parts)
    if step == "manifest":
        parts = []
        for d in _task_dirs(ctx):
            parts.append(d / ctx.config.tasks.task_json)
            parts.append(
                d / ctx.config.harness.evidence_dirname / ctx.config.harness.verdict_filename
            )
        return hash_inputs(*parts, repr(ctx.config.tasks))
    if step == "select":
        return hash_inputs(
            repo_tasks_dir(ctx) / ctx.config.tasks.manifest_filename,
            repr(ctx.config.selection),
            repr(ctx.config.difficulty.target_spread),
        )
    raise KeyError(step)


def _history_build_input(ctx: HygieneContext) -> str:
    """The shortlist as the funnel produced it (the build step's own status updates in
    history_candidates.json must not invalidate the step)."""
    path = _history_candidates_path(ctx)
    if not path.is_file():
        return ""
    data = json.loads(path.read_text())
    short = set(data.get("shortlist", []))
    cands = [
        {k: v for k, v in c.items() if k not in ("status", "reject_reason")}
        for c in data.get("candidates", [])
        if c["sha"] in short
    ]
    return json.dumps({"shortlist": data.get("shortlist", []), "candidates": cands}, sort_keys=True)


def _task_dirs(ctx: HygieneContext) -> list[Path]:
    dirs: list[Path] = []
    for path in (_built_path(ctx), _built_history_path(ctx)):
        if path.is_file():
            built = json.loads(path.read_text())
            dirs.extend(
                Path(b["task_dir"])
                for b in built.values()
                if isinstance(b, dict) and b.get("task_dir")
            )
    return sorted(dirs)


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
