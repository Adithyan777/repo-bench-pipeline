"""Build the fixture repos with real, reproducible git history.

Run: ``python tests/fixtures/build_mini_pkg.py``. Rebuilds
``tests/fixtures/mini_pkg`` and ``tests/fixtures/mini_pkg_notests`` from scratch
each time. .git dirs are created here, never committed to the outer repo.

mini_pkg: 3 modules, a setup.py manifest with one small third-party dep, real
pytest tests covering some (not all) functions, and 6 commits including a genuine
bugfix (test added in the same commit), a dependency change, a docs-only commit,
and a refactor.

mini_pkg_notests: same shape, no tests and no manifest, and it imports
third-party modules (one alias-mapped) so the AST-inferred-deps path has work.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUTHOR = ("Fixture Bot", "fixture@example.com")

# --- mini_pkg file bodies ------------------------------------------------------

CALC_BUGGY = '''"""Small numeric helpers."""


def ceil_div(a, b):
    """Return ceil(a / b) for positive integers."""
    return (a + b) // b  # off-by-one: overshoots when b divides a exactly


def clamp(value, low, high):
    """Clamp value into the inclusive range [low, high]."""
    if value < low:
        return low
    if value > high:
        return high
    return value


class RunningStats:
    """Accumulate numbers and report their mean."""

    def __init__(self):
        self._values = []

    def add(self, x):
        self._values.append(x)
        return self

    def mean(self):
        if not self._values:
            raise ValueError("no values")
        return sum(self._values) / len(self._values)

    def count(self):
        return len(self._values)
'''

CALC_FIXED = CALC_BUGGY.replace(
    "    return (a + b) // b  # off-by-one: overshoots when b divides a exactly",
    "    return (a + b - 1) // b",
)

CORE = '''"""Ordering-preserving collection helpers."""


def dedupe(items):
    """Return items with duplicates removed, preserving first-seen order."""
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


class Registry:
    """A tiny name -> value registry."""

    def __init__(self):
        self._items = {}

    def register(self, name, value):
        if name in self._items:
            raise KeyError(f"already registered: {name}")
        self._items[name] = value

    def get(self, name):
        return self._items[name]

    def names(self):
        return sorted(self._items)
'''

TEXT_LEN = '''"""Text width and truncation helpers."""


def display_width(s):
    """Return the display width of a string in columns."""
    return len(s)


def truncate(s, width):
    """Truncate s to at most `width` display columns, adding an ellipsis."""
    if display_width(s) <= width:
        return s
    if width <= 1:
        return "."[:width]
    return s[: width - 1] + "\\u2026"
'''

TEXT_WCWIDTH = '''"""Text width and truncation helpers."""

from wcwidth import wcswidth


def display_width(s):
    """Return the display width of a string in terminal columns."""
    width = wcswidth(s)
    return len(s) if width < 0 else width


def truncate(s, width):
    """Truncate s to at most `width` display columns, adding an ellipsis."""
    if display_width(s) <= width:
        return s
    if width <= 1:
        return "."[:width]
    return s[: width - 1] + "\\u2026"
'''

TEXT_REFACTORED = '''"""Text width and truncation helpers."""

from wcwidth import wcswidth


def display_width(s):
    """Return the display width of a string in terminal columns."""
    width = wcswidth(s)
    return len(s) if width < 0 else width


def _needs_truncation(s, width):
    return display_width(s) > width


def truncate(s, width):
    """Truncate s to at most `width` display columns, adding an ellipsis."""
    if not _needs_truncation(s, width):
        return s
    if width <= 1:
        return "."[:width]
    return s[: width - 1] + "\\u2026"
'''


def _init(with_text: bool) -> str:
    lines = [
        '"""mini_pkg: a tiny library used as a pipeline test fixture."""',
        "",
        "from mini_pkg.calc import RunningStats, ceil_div, clamp",
        "from mini_pkg.core import Registry, dedupe",
    ]
    exports = ["RunningStats", "ceil_div", "clamp", "Registry", "dedupe"]
    if with_text:
        lines.append("from mini_pkg.text import display_width, truncate")
        exports += ["display_width", "truncate"]
    lines += ["", f"__all__ = {exports!r}", ""]
    return "\n".join(lines)


def _setup(dep: bool) -> str:
    install = '\n    install_requires=["wcwidth>=0.2.0"],' if dep else ""
    return (
        "from setuptools import find_packages, setup\n\n"
        "setup(\n"
        '    name="mini_pkg",\n'
        '    version="0.1.0",\n'
        '    packages=find_packages(exclude=["tests", "tests.*"]),\n'
        '    python_requires=">=3.9",'
        f"{install}\n"
        ")\n"
    )


TEST_CALC = """from mini_pkg.calc import RunningStats, ceil_div, clamp


def test_clamp_within():
    assert clamp(5, 0, 10) == 5


def test_clamp_bounds():
    assert clamp(-1, 0, 10) == 0
    assert clamp(11, 0, 10) == 10


def test_ceil_div_rounds_up():
    assert ceil_div(5, 2) == 3
    assert ceil_div(1, 3) == 1


def test_running_stats_mean():
    stats = RunningStats()
    stats.add(2).add(4)
    assert stats.mean() == 3
"""

TEST_CALC_WITH_BUGFIX = (
    TEST_CALC
    + """

def test_ceil_div_exact_multiple():
    assert ceil_div(4, 2) == 2
    assert ceil_div(6, 3) == 2
"""
)

TEST_CORE = """import pytest

from mini_pkg.core import Registry, dedupe


def test_dedupe_preserves_order():
    assert dedupe([3, 1, 3, 2, 1]) == [3, 1, 2]


def test_registry_register_and_get():
    reg = Registry()
    reg.register("a", 1)
    assert reg.get("a") == 1


def test_registry_duplicate_raises():
    reg = Registry()
    reg.register("a", 1)
    with pytest.raises(KeyError):
        reg.register("a", 2)
"""

TEST_TEXT = """from mini_pkg.text import display_width, truncate


def test_display_width_ascii():
    assert display_width("hello") == 5


def test_truncate_short_string_unchanged():
    assert truncate("hi", 10) == "hi"


def test_truncate_adds_ellipsis():
    assert truncate("hello world", 5) == "hell\\u2026"
"""

README = """# mini_pkg

A tiny library used as a pipeline test fixture.

```python
from mini_pkg import ceil_div, clamp, dedupe, truncate

ceil_div(5, 2)          # 3
clamp(11, 0, 10)        # 10
dedupe([1, 1, 2])       # [1, 2]
truncate("hello", 4)    # "hel\\u2026"
```
"""

# --- mini_pkg_notests file bodies ---------------------------------------------

NT_CORE = '''"""Stdlib-only helpers (no manifest; deps inferred from imports)."""


def flatten(nested):
    """Concatenate an iterable of iterables into one list."""
    out = []
    for item in nested:
        out.extend(item)
    return out


def group_by(items, key):
    """Group items into a dict keyed by key(item)."""
    groups = {}
    for item in items:
        groups.setdefault(key(item), []).append(item)
    return groups
'''

NT_UTIL = '''"""Config loading. Imports PyYAML (import name `yaml` != PyPI name)."""

import yaml


def load_config(text):
    """Parse a YAML config string into a dict."""
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("expected a mapping")
    return data
'''

NT_RENDER = '''"""Column-aware rendering. Imports wcwidth (import name == PyPI name)."""

from wcwidth import wcswidth


def padded(s, width):
    """Right-pad s to the given display width."""
    gap = width - (wcswidth(s) or len(s))
    return s + " " * max(gap, 0)
'''

NT_INIT_NO_RENDER = '''"""mini_pkg_notests: fixture with no tests and no manifest."""

from mini_pkg_notests.core import flatten, group_by
from mini_pkg_notests.util import load_config

__all__ = ["flatten", "group_by", "load_config"]
'''

NT_INIT = '''"""mini_pkg_notests: fixture with no tests and no manifest."""

from mini_pkg_notests.core import flatten, group_by
from mini_pkg_notests.render import padded
from mini_pkg_notests.util import load_config

__all__ = ["flatten", "group_by", "padded", "load_config"]
'''

NT_README = "# mini_pkg_notests\n\nFixture with no tests and no manifest.\n"


# --- git plumbing --------------------------------------------------------------


def _git(repo: Path, *args: str, date: str | None = None) -> None:
    env = {"GIT_TERMINAL_PROMPT": "0"}
    if date:
        env |= {
            "GIT_AUTHOR_DATE": date,
            "GIT_COMMITTER_DATE": date,
            "GIT_AUTHOR_NAME": AUTHOR[0],
            "GIT_AUTHOR_EMAIL": AUTHOR[1],
            "GIT_COMMITTER_NAME": AUTHOR[0],
            "GIT_COMMITTER_EMAIL": AUTHOR[1],
        }
    subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, env=_full_env(env)
    )


def _full_env(extra: dict) -> dict:
    import os

    env = dict(os.environ)
    env.update(extra)
    return env


def _apply(repo: Path, files: dict[str, str | None]) -> None:
    for rel, content in files.items():
        path = repo / rel
        if content is None:
            path.unlink(missing_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)


def _build(repo: Path, commits: list[dict]) -> None:
    if repo.exists():
        shutil.rmtree(repo)
    repo.mkdir(parents=True)
    _git(repo, "init", "-q", "-b", "main")
    for i, commit in enumerate(commits):
        _apply(repo, commit["files"])
        date = f"2026-01-{i + 1:02d}T12:00:00 +0000"
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", commit["msg"], date=date)


def build_mini_pkg(root: Path) -> Path:
    repo = root / "mini_pkg"
    commits = [
        {
            "msg": "Initial package: calc and core modules with tests",
            "files": {
                "setup.py": _setup(dep=False),
                "mini_pkg/__init__.py": _init(with_text=False),
                "mini_pkg/calc.py": CALC_BUGGY,
                "mini_pkg/core.py": CORE,
                "tests/test_calc.py": TEST_CALC,
                "tests/test_core.py": TEST_CORE,
                "pytest.ini": "[pytest]\ntestpaths = tests\n",
            },
        },
        {
            "msg": "Add text module with width and truncation helpers",
            "files": {
                "mini_pkg/__init__.py": _init(with_text=True),
                "mini_pkg/text.py": TEXT_LEN,
                "tests/test_text.py": TEST_TEXT,
            },
        },
        {
            "msg": "docs: add README with usage examples",
            "files": {"README.md": README},
        },
        {
            "msg": "Use wcwidth for accurate display width",
            "files": {"setup.py": _setup(dep=True), "mini_pkg/text.py": TEXT_WCWIDTH},
        },
        {
            "msg": "Fix ceil_div off-by-one on exact multiples (add test)",
            "files": {"mini_pkg/calc.py": CALC_FIXED, "tests/test_calc.py": TEST_CALC_WITH_BUGFIX},
        },
        {
            "msg": "Refactor: extract _needs_truncation helper in text",
            "files": {"mini_pkg/text.py": TEXT_REFACTORED},
        },
    ]
    _build(repo, commits)
    return repo


def build_mini_pkg_notests(root: Path) -> Path:
    repo = root / "mini_pkg_notests"
    commits = [
        {
            "msg": "Initial package: core and yaml config loader",
            "files": {
                "mini_pkg_notests/__init__.py": NT_INIT_NO_RENDER,
                "mini_pkg_notests/core.py": NT_CORE,
                "mini_pkg_notests/util.py": NT_UTIL,
            },
        },
        {
            "msg": "Add wcwidth-based column rendering",
            "files": {
                "mini_pkg_notests/__init__.py": NT_INIT,
                "mini_pkg_notests/render.py": NT_RENDER,
            },
        },
        {
            "msg": "docs: add README",
            "files": {"README.md": NT_README},
        },
    ]
    _build(repo, commits)
    return repo


def main() -> None:
    mp = build_mini_pkg(HERE)
    nt = build_mini_pkg_notests(HERE)
    for repo in (mp, nt):
        count = subprocess.run(
            ["git", "-C", str(repo), "rev-list", "--count", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        print(f"built {repo.relative_to(HERE.parent.parent)}: {count} commits")


if __name__ == "__main__":
    main()
