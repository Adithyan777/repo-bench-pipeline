"""Shared test fixtures: build the fixture repos once, gate docker-only tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests.fixtures import build_mini_pkg

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _docker_up() -> bool:
    try:
        return subprocess.run(["docker", "info"], capture_output=True, timeout=15).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


@pytest.fixture(scope="session", autouse=True)
def _ensure_fixtures() -> None:
    if not (FIXTURES / "mini_pkg" / ".git").is_dir():
        build_mini_pkg.build_mini_pkg(FIXTURES)
    if not (FIXTURES / "mini_pkg_notests" / ".git").is_dir():
        build_mini_pkg.build_mini_pkg_notests(FIXTURES)


@pytest.fixture(scope="session")
def docker_available() -> None:
    if not _docker_up():
        pytest.skip("docker daemon not available")


@pytest.fixture(scope="session")
def mini_env(tmp_path_factory, docker_available: None):
    """One hygiene+knowledge run of mini_pkg shared by the tasks/harness/history tests
    (same config as the recorded ``s5_tasks`` cassettes)."""
    import shutil

    from pipeline.hygiene.context import build_context
    from pipeline.hygiene.runner import run_hygiene
    from pipeline.knowledge.runner import run_knowledge
    from tests import _smoke

    root = tmp_path_factory.mktemp("tasks")
    src = root / "mini_pkg"
    shutil.copytree(FIXTURES / "mini_pkg", src)
    cfg = _smoke.mini_pkg_excision_config()
    cfg.tasks.tasks_root = str(root / "tasks")
    ctx = build_context(
        str(src),
        config=cfg,
        output_root=root / "out",
        llm_mode="replay",
        llm_stage=_smoke.TASKS_STAGE,
    )
    run_hygiene(ctx)
    run_knowledge(ctx)
    return ctx


@pytest.fixture
def mini_pkg(tmp_path: Path) -> Path:
    """A throwaway copy of the mini_pkg fixture (safe to mutate)."""
    import shutil

    dest = tmp_path / "mini_pkg"
    shutil.copytree(FIXTURES / "mini_pkg", dest)
    return dest
