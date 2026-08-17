"""Knowledge stage runner: symbol_index -> indexes -> graph -> verify.

Indexes precede graph because node coverage/test refs and ``tested_by`` derive from
test_map/coverage. Steps are resumable via state.py; timing goes to report_data.json.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from pipeline.hygiene.context import HygieneContext
from pipeline.knowledge import graph as graph_mod
from pipeline.knowledge import indexes, okf, okf_verify, verify
from pipeline.log import fmt_counts, log, step_skipped, step_start
from pipeline.state import code_fingerprint, hash_inputs

STAGE = "knowledge"
_STEPS = ("symbol_index", "indexes", "graph", "verify", "okf")


def run_knowledge(ctx: HygieneContext) -> HygieneContext:
    _load_existing_report(ctx)
    for name in _STEPS:
        _run_step(ctx, name)
    ctx.llm.write_usage()
    _write_report(ctx)
    return ctx


def knowledge_paths(run_dir: Path, config=None) -> dict:
    from pipeline.config import DEFAULT

    kc = (config or DEFAULT).knowledge
    kdir = run_dir / "knowledge"
    return {
        "graph": str(kdir / kc.graph_filename),
        "symbols": str(kdir / kc.symbols_filename),
        "history_index": str(kdir / kc.history_filename),
        "test_map": str(kdir / kc.test_map_filename),
        "coverage": str(kdir / kc.coverage_filename),
        "hotspots": str(kdir / kc.hotspots_filename),
        "verification": str(kdir / kc.verification_filename),
        "okf": str(kdir / (config or DEFAULT).okf.bundle_dirname),
        "okf_manifest": str(kdir / (config or DEFAULT).okf.manifest_filename),
    }


# --- steps --------------------------------------------------------------------


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


def _step_symbol_index(ctx: HygieneContext) -> None:
    symbols = ctx.adapter.symbol_index(ctx.repo)
    _write(ctx, ctx.config.knowledge.symbols_filename, symbols)
    log(
        STAGE,
        "symbol_index",
        f"{len(symbols.get('modules') or [])} modules, "
        f"{len(symbols.get('functions') or [])} functions",
    )


def _step_indexes(ctx: HygieneContext) -> None:
    kc = ctx.config.knowledge
    symbols = _read(ctx, kc.symbols_filename)
    base_sha = _base_sha(ctx)

    history = indexes.build_history_index(ctx.repo, base_sha, ctx.config)
    _write(ctx, kc.history_filename, history)
    _write(ctx, kc.hotspots_filename, indexes.build_hotspots(history))
    log(STAGE, "indexes", f"history index: {len(history)} commits")

    cov = indexes.run_coverage(ctx.repo, ctx.image_tag, _quarantined(ctx), ctx.config)
    _write(ctx, kc.coverage_contexts_filename, cov.contexts)  # raw, for verify re-derivation
    test_map = indexes.build_test_map(symbols, cov.contexts)
    _write(ctx, kc.test_map_filename, test_map)
    _write(ctx, kc.coverage_filename, indexes.build_coverage(symbols, cov.contexts))
    ctx.report.setdefault("stages", {}).setdefault("indexes", {})["coverage_status"] = cov.status
    log(STAGE, "indexes", f"coverage {cov.status}: test_map {len(test_map)} functions")


def _step_graph(ctx: HygieneContext) -> None:
    kc = ctx.config.knowledge
    symbols = _read(ctx, kc.symbols_filename)
    test_map = _read(ctx, kc.test_map_filename)
    coverage = _read(ctx, kc.coverage_filename)
    graph = graph_mod.build_graph(symbols, test_map, coverage, ctx.config)
    _write(ctx, kc.graph_filename, graph)
    ctx.report["graph"] = graph["metadata"]
    counts = graph["metadata"].get("counts", {})
    log(
        STAGE,
        "graph",
        f"{counts.get('nodes')} nodes, {counts.get('total_edges')} edges "
        f"({fmt_counts(counts.get('edges'))})",
    )


def _step_verify(ctx: HygieneContext) -> None:
    kc = ctx.config.knowledge
    graph = _read(ctx, kc.graph_filename)
    symbols = _read(ctx, kc.symbols_filename)
    coverage_contexts = _read(ctx, kc.coverage_contexts_filename)
    report = verify.verify_graph(
        ctx.repo,
        graph,
        symbols,
        coverage_contexts=coverage_contexts,
        image=ctx.image_tag,
        config=ctx.config,
    )
    _write(ctx, kc.verification_filename, report)
    ctx.report["graph_verification"] = {
        "by_edge_type": report["by_edge_type"],
        "symbol_existence": report["symbol_existence"],
        "mismatch_count": len(report["mismatches"]),
    }
    log(
        STAGE,
        "verify",
        f"mismatches {len(report['mismatches'])}, "
        f"symbols {fmt_counts(report.get('symbol_existence'), ('checked', 'present'))}",
    )


def _step_okf(ctx: HygieneContext) -> None:
    kc, oc = ctx.config.knowledge, ctx.config.okf
    if not oc.enabled:
        ctx.report["okf"] = {"enabled": False}
        log(STAGE, "okf", "disabled")
        return
    graph = _read(ctx, kc.graph_filename)
    dpath = ctx.knowledge_dir / oc.decisions_filename
    decisions = json.loads(dpath.read_text()) if dpath.is_file() else {}
    try:
        manifest = okf.build_okf(ctx, graph, llm=ctx.llm, decisions=decisions)
    finally:  # keep any decisions authored before an error so a rerun reuses them
        dpath.write_text(json.dumps(decisions, indent=2, sort_keys=True))
    report = okf_verify.verify_okf(ctx, graph)
    _write(ctx, oc.manifest_filename, manifest)
    _write(ctx, oc.verification_filename, report)
    ctx.report["okf"] = {
        **manifest["counts"],
        "pages_verified": report["pages_verified"],
        "pages_draft": report["pages_draft"],
        "precision_by_claim": report["precision_by_claim"],
        "conformant": report["conformance"]["conformant"],
    }
    log(
        STAGE,
        "okf",
        f"{fmt_counts(manifest.get('counts'), ('modules', 'pages'))} "
        f"verified={report.get('pages_verified')} draft={report.get('pages_draft')} "
        f"conformant={report.get('conformance', {}).get('conformant')}",
    )


_STEP_FUNCS = {
    "symbol_index": _step_symbol_index,
    "indexes": _step_indexes,
    "graph": _step_graph,
    "verify": _step_verify,
    "okf": _step_okf,
}


# --- input hashing ------------------------------------------------------------


def _input_hash(ctx: HygieneContext, step: str) -> str:
    # Analyzer-code fingerprint: a code fix invalidates artifacts even with unchanged inputs.
    fingerprint = code_fingerprint(ctx.config.knowledge.code_fingerprint_files)
    return hash_inputs("kn-code", fingerprint, _step_input_hash(ctx, step))


def _step_input_hash(ctx: HygieneContext, step: str) -> str:
    kc = ctx.config.knowledge
    if step == "symbol_index":
        return hash_inputs("symbol_index", ctx.config.graph.complexity_metric, *_source_files(ctx))
    if step == "indexes":
        parts = ["indexes", _base_sha(ctx), kc.ctx_plugin_module]
        parts += [ctx.hygiene_dir / "baseline.json", ctx.hygiene_dir / "build.json"]
        parts += _source_files(ctx)
        return hash_inputs(*[p for p in parts if isinstance(p, str) or Path(p).is_file()])
    if step == "graph":
        files = _knowledge_files(
            ctx, kc.symbols_filename, kc.test_map_filename, kc.coverage_filename
        )
        return hash_inputs("graph", *files)
    if step == "verify":
        return hash_inputs(
            "verify",
            str(ctx.config.graph.verification_sample_edges),
            *_knowledge_files(
                ctx, kc.graph_filename, kc.symbols_filename, kc.coverage_contexts_filename
            ),
        )
    if step == "okf":
        return hash_inputs(
            "okf",
            okf.PROMPT_VERSION,
            ctx.config.model_for(okf.MODULE_PURPOSE_STEP),
            str(ctx.config.okf.max_function_pages),
            str(ctx.config.okf.min_private_page_complexity),
            *_knowledge_files(ctx, kc.graph_filename),
            *_source_files(ctx),
        )
    return hash_inputs(step)


def _source_files(ctx: HygieneContext) -> list[Path]:
    return sorted(p for p in ctx.repo.rglob("*.py") if ".git" not in p.parts and p.is_file())


def _knowledge_files(ctx: HygieneContext, *names: str) -> list[Path]:
    return [ctx.knowledge_dir / n for n in names if (ctx.knowledge_dir / n).is_file()]


# --- io helpers ---------------------------------------------------------------


def _write(ctx: HygieneContext, name: str, data) -> None:
    ctx.knowledge_dir.mkdir(parents=True, exist_ok=True)
    (ctx.knowledge_dir / name).write_text(json.dumps(data, indent=2, sort_keys=True))


def _read(ctx: HygieneContext, name: str):
    return json.loads((ctx.knowledge_dir / name).read_text())


def _base_sha(ctx: HygieneContext) -> str:
    pb = ctx.hygiene_dir / "pipeline_base.json"
    if pb.is_file():
        return json.loads(pb.read_text()).get("base_sha", "")
    return ctx.report.get("base_sha", "")


def _quarantined(ctx: HygieneContext) -> list[str]:
    baseline = ctx.hygiene_dir / "baseline.json"
    if baseline.is_file():
        return json.loads(baseline.read_text()).get("quarantined", [])
    return []


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
    (ctx.run_dir / "report_data.json").write_text(json.dumps(ctx.report, indent=2, sort_keys=True))
