"""Step 3.1: ecosystem + packaging-style + Python-version detection."""

from __future__ import annotations

from pipeline.hygiene.context import HygieneContext
from pipeline.state import hash_inputs


def input_hash(ctx: HygieneContext) -> str:
    # Key off the original tree identity, not current files: the pipeline writes
    # requirements.in (a manifest marker), which must not perturb detection.
    return hash_inputs(
        ctx.repo_identity,
        "detect",
        *ctx.config.detect.manifest_markers,
        ctx.config.detect.python_version_cap,
    )


def run(ctx: HygieneContext) -> dict:
    adapter, repo = ctx.adapter, ctx.repo
    if not adapter.detect(repo):
        raise SystemExit(
            f"{repo.name}: not a supported ecosystem "
            f"(supported: {ctx.config.detect.supported_ecosystems}); no Python found"
        )
    info = adapter.packaging(repo)
    data = {
        "ecosystem": "python",
        "packaging_style": info.style,
        "manifest": info.manifest,
        "installable": info.installable,
        "available_extras": info.available_extras,
        "requires_python": info.requires_python,
        "python_version": adapter.python_version(repo),
        "test_framework": adapter.test_framework(repo),
    }
    ctx.record("detect", data)
    return data
