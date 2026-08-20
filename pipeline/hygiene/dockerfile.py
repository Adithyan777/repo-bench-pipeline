"""Hygiene step 3 (dockerfile): render the digest-pinned Dockerfile + .dockerignore
into the repo."""

from __future__ import annotations

from pipeline.hygiene.context import HygieneContext
from pipeline.state import hash_inputs


def input_hash(ctx: HygieneContext) -> str:
    return hash_inputs(
        ctx.repo / ctx.config.pin.lock_filename,
        ctx.hygiene_dir / "detect.json",
    )


def run(ctx: HygieneContext) -> dict:
    adapter, repo = ctx.adapter, ctx.repo
    lock = repo / ctx.config.pin.lock_filename
    dockerfile = adapter.write_dockerfile(repo, lock)
    text = dockerfile.read_text()
    base = text.splitlines()[0].removeprefix("FROM ").strip()
    data = {
        "dockerfile": "Dockerfile",
        "base_image": base,
        "test_command": adapter.test_command(repo),
    }
    ctx.record("dockerfile", data)
    return data
