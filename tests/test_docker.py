"""Docker runner + image build against real containers."""

from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.docker import (
    build_image,
    fresh_workdir,
    resolve_base_digest,
    run_in_container,
)
from pipeline.docker.runner import TIMEOUT_EXIT_CODE

BASE = "python:3.12-slim"
pytestmark = pytest.mark.docker


def test_run_in_container_executes(mini_pkg: Path, docker_available: None) -> None:
    result = run_in_container(mini_pkg, "ls setup.py && echo ok", BASE, timeout=60)
    assert result.exit_code == 0
    assert "ok" in result.stdout


def test_run_in_container_nonzero_exit(mini_pkg: Path, docker_available: None) -> None:
    result = run_in_container(mini_pkg, "exit 3", BASE, timeout=60)
    assert result.exit_code == 3


def test_run_in_container_enforces_timeout(mini_pkg: Path, docker_available: None) -> None:
    result = run_in_container(mini_pkg, "sleep 30", BASE, timeout=2)
    assert result.exit_code == TIMEOUT_EXIT_CODE
    assert "timeout" in result.stderr


def test_network_none_by_default(mini_pkg: Path, docker_available: None) -> None:
    # no network -> DNS/connect fails; python exits nonzero
    probe = "import urllib.request; urllib.request.urlopen('http://example.com', timeout=3)"
    result = run_in_container(mini_pkg, f'python -c "{probe}"', BASE, timeout=30)
    assert result.exit_code != 0


def test_fresh_workdir_is_isolated(mini_pkg: Path, docker_available: None) -> None:
    with fresh_workdir(mini_pkg) as work:
        run_in_container(work, "touch scratch.txt", BASE, timeout=30)
        assert (work / "scratch.txt").exists()
    assert not (mini_pkg / "scratch.txt").exists()  # original untouched


def test_resolve_base_digest(docker_available: None) -> None:
    pinned = resolve_base_digest(BASE)
    assert pinned.startswith("python@sha256:")


def test_build_tiny_image(tmp_path: Path, docker_available: None) -> None:
    digest = resolve_base_digest(BASE)
    (tmp_path / "Dockerfile").write_text(f"FROM {digest}\nRUN echo built > /marker\n")
    image_id = build_image(tmp_path, "bench-test-tiny:latest")
    assert image_id.startswith("sha256:")
    result = run_in_container(tmp_path, "cat /marker", "bench-test-tiny:latest", timeout=30)
    assert "built" in result.stdout
