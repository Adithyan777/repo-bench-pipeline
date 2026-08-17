"""The fixture repos build reproducibly and encode the intended history."""

from __future__ import annotations

import subprocess
from pathlib import Path

from tests.fixtures import build_mini_pkg

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _log(repo: Path) -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(repo), "log", "--reverse", "--format=%s"],
        check=True,
        capture_output=True,
        text=True,
    )
    return out.stdout.splitlines()


def _show(repo: Path, ref: str, path: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), "show", f"{ref}:{path}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def test_rebuild_is_deterministic(tmp_path: Path) -> None:
    a = build_mini_pkg.build_mini_pkg(tmp_path / "a")
    b = build_mini_pkg.build_mini_pkg(tmp_path / "b")
    head_a = subprocess.run(
        ["git", "-C", str(a), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout
    head_b = subprocess.run(
        ["git", "-C", str(b), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout
    assert head_a == head_b


def test_history_shape() -> None:
    messages = _log(FIXTURES / "mini_pkg")
    assert len(messages) == 8
    assert any("docs:" in m for m in messages)
    assert any("Fix" in m for m in messages)
    assert any("wcwidth" in m for m in messages)
    assert any("Refactor" in m for m in messages)
    assert any("Rename" in m for m in messages)


def test_bugfix_commit_adds_test_and_fixes_behavior() -> None:
    repo = FIXTURES / "mini_pkg"
    # locate the ceil_div bugfix commit
    sha = subprocess.run(
        ["git", "-C", str(repo), "log", "--format=%H", "--grep", "ceil_div"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()[0]
    parent_calc = _show(repo, f"{sha}~1", "mini_pkg/calc.py")
    fixed_calc = _show(repo, sha, "mini_pkg/calc.py")
    parent_test = _show(repo, f"{sha}~1", "tests/test_calc.py")
    fixed_test = _show(repo, sha, "tests/test_calc.py")

    assert "(a + b) // b" in parent_calc and "(a + b - 1) // b" in fixed_calc
    assert "exact_multiple" not in parent_test and "exact_multiple" in fixed_test

    ns_buggy: dict = {}
    exec(parent_calc, ns_buggy)  # noqa: S102 - fixture source, trusted
    ns_fixed: dict = {}
    exec(fixed_calc, ns_fixed)  # noqa: S102
    assert ns_buggy["ceil_div"](4, 2) == 3  # the bug
    assert ns_fixed["ceil_div"](4, 2) == 2  # fixed
    assert ns_buggy["ceil_div"](5, 2) == ns_fixed["ceil_div"](5, 2) == 3  # unchanged elsewhere


def test_notests_has_no_manifest_or_tests() -> None:
    repo = FIXTURES / "mini_pkg_notests"
    assert not (repo / "setup.py").exists()
    assert not (repo / "pyproject.toml").exists()
    assert not any(repo.glob("**/test_*.py"))
    # third-party imports present for AST-inferred deps (one alias-mapped: yaml -> PyYAML)
    assert "import yaml" in (repo / "mini_pkg_notests" / "util.py").read_text()
    assert "from wcwidth import" in (repo / "mini_pkg_notests" / "render.py").read_text()
