"""Test generation + mutation gate.

Ranking/mutators offline; the generation loop runs the real agent against a scripted
endpoint with real Docker (multi-turn container agents are not cassette-replayable).
"""

from __future__ import annotations

import ast
import shutil
from pathlib import Path

import pytest

from pipeline.config import Config
from pipeline.ecosystems.python import PythonAdapter
from pipeline.ecosystems.source_ops import read_source, write_source
from pipeline.hygiene import testgen
from pipeline.hygiene.context import HygieneContext
from pipeline.hygiene.mutate import function_mutants
from pipeline.state import State

FIXTURES = Path(__file__).resolve().parent / "fixtures"


# --- mutators (offline) -------------------------------------------------------

_FN = '''def classify(x, y):
    """Doc."""
    total = 0
    if x < y and y > 0:
        total = x + y
    elif x == y:
        total = 10
    return total
'''

_MUT_NAMES = [
    "comparison_flip",
    "comparison_boundary",
    "arithmetic_swap",
    "and_or_swap",
    "return_none",
    "constant_tweak",
    "statement_delete",
]


@pytest.mark.parametrize("name", _MUT_NAMES)
def test_each_mutator_parses_and_differs(name):
    from pipeline.ecosystems.python import _MUTATORS

    mutants = _MUTATORS[name](_FN)
    assert mutants, f"{name} produced no mutants"
    for m in mutants:
        ast.parse(m)  # parses
        assert m != _FN  # differs
        assert "def classify" in m  # never deletes the function under test


def test_mutants_leave_rest_of_file_byte_identical():
    src = "import os\n\n\n" + _FN + "\n\nTAIL = 1\n"
    lines = src.splitlines(keepends=True)
    # classify spans lines 4..11 in this file
    start = next(i for i, ln in enumerate(lines, 1) if ln.startswith("def classify"))
    end = next(i for i, ln in enumerate(lines, 1) if ln.startswith("    return total"))
    adapter = PythonAdapter(Config(), None, None)
    muts = function_mutants(src, start, end, adapter.mutators(), 6)
    assert muts
    for m in muts:
        ast.parse(m.source)
        out = m.source.splitlines(keepends=True)
        assert "".join(out[: start - 1]) == "".join(lines[: start - 1])  # prefix
        assert out[-1] == lines[-1] and out[-2] == lines[-2]  # TAIL untouched


# --- ranking (offline) --------------------------------------------------------


def _fn(qual, file, line, end, cx, pub, method=False):
    return {
        "qualname": qual,
        "module": qual.rsplit(".", 1)[0],
        "name": qual.rsplit(".", 1)[-1],
        "file": file,
        "line": line,
        "end_line": end,
        "complexity": cx,
        "is_public": pub,
        "is_method": method,
    }


def test_rank_skips_and_selects():
    cfg = Config()
    functions = [
        _fn("pkg.a.big_public", "pkg/a.py", 1, 20, 5, True),  # strong target
        _fn("pkg.a.tiny", "pkg/a.py", 30, 31, 1, True),  # too_small
        _fn("pkg.a._helper", "pkg/a.py", 40, 60, 1, False),  # private_low_complexity
        _fn("pkg.a.__eq__", "pkg/a.py", 70, 74, 1, False, True),  # dunder
        _fn("pkg.b.covered", "pkg/b.py", 1, 10, 3, True),  # fully covered -> score 0
    ]
    cov = {
        "pkg/a.py": {"executed_lines": [], "missing_lines": list(range(1, 75))},
        "pkg/b.py": {"executed_lines": list(range(1, 11)), "missing_lines": []},
    }
    t = testgen.rank_targets(functions, cov, cfg)
    reasons = {r["qualname"]: r["skip_reason"] for r in t["functions"]}
    assert reasons["pkg.a.tiny"] == "too_small"
    assert reasons["pkg.a._helper"] == "private_low_complexity"
    assert reasons["pkg.a.__eq__"] == "dunder"
    assert reasons["pkg.a.big_public"] is None
    assert "pkg.a.big_public" in t["selected"]
    assert "pkg.b.covered" not in t["selected"]  # covered -> not worth generating


def test_disabled_is_noop(tmp_path):
    cfg = Config()
    cfg.testgen.enabled = False
    ctx = HygieneContext("x", tmp_path / "r", cfg, None, None, None)
    ctx.report.setdefault("stages", {})
    assert testgen.run(ctx) == {"enabled": False}


def test_uncovered_ratio_from_missed_lines():
    cfg = Config()
    fn = _fn("pkg.m.f", "pkg/m.py", 1, 5, 2, True)  # 5 lines
    cov = {"pkg/m.py": {"executed_lines": [1, 2, 3], "missing_lines": [4, 5]}}
    t = testgen.rank_targets([fn], cov, cfg)
    row = t["functions"][0]
    assert row["uncovered_ratio"] == round(2 / 5, 3)


# --- mutation gate: weak survives, strong kills (real container) ---------------


@pytest.mark.docker
def test_weak_test_survives_strong_test_kills(mini_env):
    repo = mini_env.repo
    adapter = PythonAdapter(Config(), repo, None)
    fn = next(
        f for f in adapter.symbol_index(repo)["functions"] if f["qualname"] == "mini_pkg.calc.clamp"
    )
    src = read_source(repo / fn["file"])
    mutants = function_mutants(src, fn["line"], fn["end_line"], adapter.mutators(), 4)
    assert mutants

    weak = (  # calls clamp but asserts nothing about its result -> catches no mutant
        "from mini_pkg.calc import clamp\n\ndef test_w():\n    clamp(5, 0, 10)\n    assert True\n"
    )
    strong = (
        "from mini_pkg.calc import clamp\n\n"
        "def test_s():\n"
        "    assert clamp(5, 0, 10) == 5\n"
        "    assert clamp(-3, 0, 10) == 0\n"
        "    assert clamp(99, 0, 10) == 10\n"
    )
    gen = repo / "tests" / "generated"
    gen.mkdir(parents=True, exist_ok=True)
    rel = "tests/generated/_probe.py"

    def killed(mutants):
        return sum(
            testgen._mutant_outcome(mini_env, fn["file"], m.source, rel) == "killed"
            for m in mutants
        )

    try:
        write_source(repo / rel, weak)
        weak_killed = killed(mutants)
        write_source(repo / rel, strong)
        strong_killed = killed(mutants)
    finally:
        (repo / rel).unlink(missing_ok=True)
    assert weak_killed == 0
    assert strong_killed >= 1
    assert strong_killed > weak_killed


# --- generation loop (scripted endpoint, real container) ----------------------


class _ScriptedAgent:
    """Each agent.run does two chats: a write_file tool call, then a final message.
    The same body is written every run (so retries re-emit it)."""

    def __init__(self, path: str, body: str):
        self.path, self.body, self.calls = path, body, 0

    def chat(self, step, messages, tools=None, tool_choice=None, max_tokens=None):
        from tests.test_llm import make_completion

        self.calls += 1
        if self.calls % 2 == 1:
            import json

            return make_completion(
                tool_calls=[("write_file", json.dumps({"path": self.path, "content": self.body}))]
            )
        return make_completion(content="done")


def _tg_ctx(mini_env, tmp_path, scripted, config) -> HygieneContext:
    run_dir = tmp_path / "mini_pkg"  # name -> image bench-mini_pkg (mounted workdir)
    shutil.copytree(mini_env.repo, run_dir / "repo")
    (run_dir / "hygiene").mkdir(parents=True)
    for f in ("baseline.json", "build.json"):
        src = mini_env.hygiene_dir / f
        if src.exists():
            shutil.copy(src, run_dir / "hygiene" / f)
    state = State.load(run_dir, force=(), fresh=False)
    adapter = PythonAdapter(config=config, work_dir=run_dir / "repo", llm=scripted)
    ctx = HygieneContext("mini_pkg", run_dir, config, state, scripted, adapter)
    ctx.report.setdefault("stages", {})
    return ctx


def _targets(ctx, module):
    fns = ctx.adapter.symbol_index(ctx.repo)["functions"]
    return [f for f in fns if f["module"] == module and f["is_public"]]


@pytest.mark.docker
def test_generation_keeps_strong_tests(mini_env, tmp_path):
    cfg = Config()
    gen_dir = testgen.generated_dir(mini_env.repo, cfg)  # tests/generated
    rel = str((gen_dir / "test_mini_pkg_calc.py").relative_to(mini_env.repo))
    body = (
        "from mini_pkg.calc import clamp, ceil_div\n\n"
        "def test_clamp():\n"
        "    assert clamp(5, 0, 10) == 5\n"
        "    assert clamp(-3, 0, 10) == 0\n"
        "    assert clamp(99, 0, 10) == 10\n\n"
        "def test_ceil_div():\n"
        "    assert ceil_div(7, 2) == 4\n"
        "    assert ceil_div(6, 2) == 3\n"
    )
    scripted = _ScriptedAgent(rel, body)
    ctx = _tg_ctx(mini_env, tmp_path, scripted, cfg)
    gd = testgen.generated_dir(ctx.repo, cfg)
    testgen._ensure_dir(ctx.repo, gd)
    targets = [
        f
        for f in _targets(ctx, "mini_pkg.calc")
        if f["qualname"] in ("mini_pkg.calc.clamp", "mini_pkg.calc.ceil_div")
    ]
    result = testgen._generate_module(
        ctx, "mini_pkg.calc", targets, gd, runs_left=[10], kept_files=set()
    )
    assert result["status"] == "kept"
    assert (ctx.repo / rel).is_file()
    assert result["functions"]["mini_pkg.calc.clamp"]["mutants_killed"] >= 1
    assert result["functions"]["mini_pkg.calc.clamp"]["status"] == "kept"
    assert scripted.calls == 2  # one successful run, no retries


@pytest.mark.docker
def test_generation_drops_zero_kill_tests(mini_env, tmp_path):
    cfg = Config()
    gen_dir = testgen.generated_dir(mini_env.repo, cfg)
    rel = str((gen_dir / "test_mini_pkg_calc.py").relative_to(mini_env.repo))
    weak = (  # proves nothing: exercises clamp but asserts no behavior
        "from mini_pkg.calc import clamp\n\n"
        "def test_weak():\n"
        "    clamp(5, 0, 10)\n"
        "    assert True\n"
    )
    scripted = _ScriptedAgent(rel, weak)
    ctx = _tg_ctx(mini_env, tmp_path, scripted, cfg)
    gd = testgen.generated_dir(ctx.repo, cfg)
    testgen._ensure_dir(ctx.repo, gd)
    targets = [f for f in _targets(ctx, "mini_pkg.calc") if f["qualname"] == "mini_pkg.calc.clamp"]
    result = testgen._generate_module(
        ctx, "mini_pkg.calc", targets, gd, runs_left=[10], kept_files=set()
    )
    assert result["status"] == "dropped_zero_kill"
    assert not (ctx.repo / rel).exists()  # theater removed
    # retried up to the cap: 1 write + testgen_max_retries, each run = 2 chats
    assert scripted.calls == 2 * (1 + cfg.agent.testgen_max_retries)


# --- revert of disallowed agent edits (offline, git only) ---------------------


def _git(repo, *args):
    import subprocess

    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def test_revert_disallowed_undoes_source_edits_and_new_dirs(tmp_path):
    repo = tmp_path / "repo"
    (repo / "pkg").mkdir(parents=True)
    (repo / "pkg" / "mod.py").write_text("x = 1\n")
    gen = repo / "tests" / "generated"
    gen.mkdir(parents=True)
    (gen / "test_mod.py").write_text("def test_x():\n    assert True\n")
    _git(repo, "init", "-q")
    _git(repo, "-c", "user.email=a@b", "-c", "user.name=a", "add", "-A")
    _git(repo, "-c", "user.email=a@b", "-c", "user.name=a", "commit", "-qm", "init")

    (repo / "pkg" / "mod.py").write_text("x = 999\n")  # illegit source edit (tracked)
    (repo / "newdir").mkdir()
    (repo / "newdir" / "junk.py").write_text("junk\n")  # illegit new dir
    (gen / "extra.py").write_text("scratch\n")  # stray file in gen dir

    reverted = testgen._revert_disallowed(repo, gen, {"tests/generated/test_mod.py"})

    assert (repo / "pkg" / "mod.py").read_text() == "x = 1\n"  # restored
    assert not (repo / "newdir").exists()  # emptied dir pruned
    assert not (gen / "extra.py").exists()  # stray gen file removed
    assert (gen / "test_mod.py").exists()  # allowed file preserved
    assert set(reverted) == {"pkg/mod.py", "newdir/junk.py", "tests/generated/extra.py"}
