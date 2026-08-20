"""Hygiene step 2 (pin): canonical requirements.in, then a fully pinned lock (written
into the clone).
No-manifest repos: AST import scan + alias table + SMALL-model fallback; poetry is translated.
"""

from __future__ import annotations

from pipeline.hygiene.context import HygieneContext
from pipeline.state import hash_inputs


def input_hash(ctx: HygieneContext) -> str:
    adapter, repo, cfg = ctx.adapter, ctx.repo, ctx.config
    info = adapter.packaging(repo)
    parts: list = [
        "pin",
        *cfg.pin.include_extras,
        *cfg.detect.test_tools,
        *cfg.detect.dev_tools,
        str(cfg.pin.generate_hashes),
    ]
    if info.manifest:
        parts.append(repo / info.manifest)
    if info.style == "setup.cfg":
        parts.append(repo / "setup.cfg")
    if info.style == "none":  # deps come from the import set, so hash it
        parts.append("imports:" + ",".join(sorted(adapter.infer_third_party_imports(repo))))
    return hash_inputs(*[p for p in parts if isinstance(p, str) or p.is_file()])


def run(ctx: HygieneContext) -> dict:
    adapter, repo = ctx.adapter, ctx.repo
    req_in = adapter.synthesize_requirements(repo)
    lock = adapter.lock(repo)
    pins = [
        line.split(" ")[0]
        for line in lock.read_text().splitlines()
        if line and not line[0].isspace() and "==" in line
    ]
    dropped = adapter.dropped_extras
    unresolved = adapter.unresolved_imports
    data = {
        "requirements_in": req_in.name,
        "lock": lock.name,
        "python_version": adapter.python_version(repo),
        "pin_count": len(pins),
        "pins": pins,
        "dropped_extras": dropped,
        "unresolved_imports": unresolved,
    }
    ctx.record("pin", data)
    if dropped or unresolved:
        detect = ctx.load("detect")
        detect["dropped_extras"] = dropped
        detect["unresolved_imports"] = unresolved
        ctx.record("detect", detect)
        ctx.report["dropped_extras"] = dropped
        ctx.report["unresolved_imports"] = unresolved
    return data
