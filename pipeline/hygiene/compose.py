"""Step 3.3 (compose): deterministic service detection from imports/deps, .env.example
URLs and existing compose files. Writes docker-compose.yml only for supported services
(postgres/redis); others are reported as unsupported in compose.json.
"""

from __future__ import annotations

import re

from pipeline.hygiene.context import HygieneContext
from pipeline.state import hash_inputs

_ENV_URL_RE = {
    "DATABASE_URL": "postgres",
    "REDIS_URL": "redis",
}


def input_hash(ctx: HygieneContext) -> str:
    return hash_inputs(ctx.repo / ctx.config.pin.lock_filename, str(sorted(_source_names(ctx))))


def _source_names(ctx: HygieneContext) -> set[str]:
    """Top-level imported module names across the repo (best-effort, text scan)."""
    names: set[str] = set()
    for path in ctx.repo.rglob("*.py"):
        if ".git" in path.parts:
            continue
        for m in re.finditer(
            r"^\s*(?:import|from)\s+([a-zA-Z0-9_]+)", path.read_text(errors="replace"), re.M
        ):
            names.add(m.group(1))
    return names


def run(ctx: HygieneContext) -> dict:
    cfg = ctx.config
    signals = cfg.detect.service_import_signals
    services: set[str] = set()
    evidence: dict[str, list[str]] = {}

    for name in _source_names(ctx) | _lock_names(ctx):
        if name in signals:
            svc = signals[name]
            services.add(svc)
            evidence.setdefault(svc, []).append(f"import/dep: {name}")

    env_example = ctx.repo / ".env.example"
    if env_example.is_file():
        text = env_example.read_text(errors="replace")
        for var in cfg.detect.service_env_signals:
            if re.search(rf"^{re.escape(var)}\s*=", text, re.M):
                svc = _ENV_URL_RE.get(var, "unknown")
                services.add(svc)
                evidence.setdefault(svc, []).append(f"env: {var}")

    existing = sorted(p.name for p in ctx.repo.glob("docker-compose*.y*ml"))
    supported = set(cfg.docker.compose_supported_services)
    unsupported = sorted(services - supported)
    emit = sorted(services & supported)

    data = {
        "services_detected": sorted(services),
        "supported_emitted": emit,
        "unsupported": unsupported,
        "existing_compose_files": existing,
        "evidence": evidence,
    }
    if emit:
        _write_compose(ctx, emit)
        data["compose_file"] = "docker-compose.yml"
    ctx.record("compose", data)
    return data


def _lock_names(ctx: HygieneContext) -> set[str]:
    lock = ctx.repo / ctx.config.pin.lock_filename
    if not lock.is_file():
        return set()
    names = set()
    for line in lock.read_text().splitlines():
        if line and not line[0].isspace() and "==" in line:
            names.add(line.split("==")[0].strip().lower())
    return names


def _write_compose(ctx: HygieneContext, services: list[str]) -> None:
    images = ctx.config.docker.compose_service_images
    lines = ["services:", "  app:", "    build: .", "    depends_on:"]
    lines += [f"      - {svc}" for svc in services]
    for svc in services:
        lines += [f"  {svc}:", f"    image: {images[svc]}"]
    (ctx.repo / "docker-compose.yml").write_text("\n".join(lines) + "\n")
