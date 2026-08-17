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


@pytest.fixture
def mini_pkg(tmp_path: Path) -> Path:
    """A throwaway copy of the mini_pkg fixture (safe to mutate)."""
    import shutil

    dest = tmp_path / "mini_pkg"
    shutil.copytree(FIXTURES / "mini_pkg", dest)
    return dest
