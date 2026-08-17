"""S4: excision funnel + task builder + validation harness + tasks.json.

Real fixtures (mini_pkg), real AST, real Docker for the harness; the SMALL-model
screen is replayed from a cassette. Docker tests share one hygiene+knowledge run
of mini_pkg (module fixture) and build task variants from it.
"""

from __future__ import annotations

import json
import shutil
import textwrap
from pathlib import Path

import pytest

from pipeline.config import Config
from pipeline.ecosystems import source_ops
from pipeline.ecosystems.symbols import build_symbol_index
from pipeline.llm.client import LLMClient
from pipeline.tasks import excision
from pipeline.tasks.build_excision import BuildInputs, build_task
from pipeline.tasks.classify import classify_report
from pipeline.tasks.harness import static_gate_violations, validate_task
from pipeline.tasks.manifest import write_manifest
from tests import _smoke

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _cassettes(stage: str) -> bool:
    d = Path("tests/cassettes") / stage
    return d.is_dir() and any(d.glob("*.json"))


# --- AST rewrite -----------------------------------------------------------------

SRC = textwrap.dedent(
    '''\
    import functools  # header comment stays

    @functools.lru_cache(maxsize=None)
    @staticmethod
    def target(
        a,
        b=2,
    ) -> int:
        """Docstring line one.

        More docstring.
        """
        def inner(x):  # nested def is part of the body
            return x * 2
        if a:
            return inner(b)
        return b  # trailing body comment


    def other():
        return 1
    '''
)


def test_excise_preserves_everything_outside_body() -> None:
    ex = source_ops.excise_function(SRC, ["target"], 'raise NotImplementedError("excised")')
    before, after = SRC.splitlines(keepends=True), ex.source.splitlines(keepends=True)
    assert ex.kept_docstring and (ex.body_start, ex.body_end) == (13, 17)
    assert after[: ex.body_start - 1] == before[: ex.body_start - 1]  # decorators+sig+doc
    assert after[ex.body_start - 1] == '    raise NotImplementedError("excised")\n'
    assert after[ex.body_start :] == before[ex.body_end :]  # `other` untouched
    assert "def other" in ex.source and "inner" not in ex.source


def test_excise_strip_docstring_and_errors() -> None:
    ex = source_ops.excise_function(SRC, ["target"], "raise NotImplementedError()", False)
    assert not ex.kept_docstring and ex.body_start == 9 and "Docstring" not in ex.source
    with pytest.raises(source_ops.ExciseError):
        source_ops.excise_function(SRC, ["missing"], "pass")
    with pytest.raises(source_ops.ExciseError):
        source_ops.excise_function("def one(): return 1\n", ["one"], "pass")
    nested = "class A:\n    class B:\n        def m(self):\n            return 1\n"
    ex = source_ops.excise_function(nested, ["A", "B", "m"], "pass")
    assert ex.source == "class A:\n    class B:\n        def m(self):\n            pass\n"


def test_source_ops_names_imports_assertions() -> None:
    names, stars = source_ops.module_bound_names(
        "from .core import *\nfrom x import y as z\nimport os.path\nA = B = 1\n"
        "try:\n    import ujson as json\nexcept ImportError:\n    import json\n"
        "def f(): pass\nclass C: pass\nif True:\n    T = 2\n"
    )
    assert names == {"z", "os", "A", "B", "json", "f", "C", "T"} and stars == [".core"]
    uses = source_ops.verifier_imports("from ..core import g\nimport pkg.mod\n", "pkg.sub.tests")
    assert [(u.module, u.name) for u in uses] == [("pkg.sub.core", "g"), ("pkg.mod", None)]
    src = (
        "def test_a():\n    assert 1\n    with pytest.raises(E):\n        f()\n"
        "def test_b():\n    assert 2\n"
    )
    assert source_ops.count_assertions(src, {"test_a"}) == 2
    assert source_ops.count_assertions(src) == 3
    assert source_ops.test_functions_in(src) == ["test_a", "test_b"]


def test_excise_preserves_crlf_and_tabs_byte_for_byte(tmp_path: Path) -> None:
    tail = "\r\n\r\n\r\ndef g():\r\n\treturn 3\r\n"
    src = 'def f(a):\r\n\t"""doc"""\r\n\tif a:\r\n\t\treturn 1\r\n\treturn 2' + tail
    path = tmp_path / "m.py"
    source_ops.write_source(path, src)
    assert path.read_bytes() == src.encode()  # newline="" round trip
    ex = source_ops.excise_function(
        source_ops.read_source(path), ["f"], "raise NotImplementedError()"
    )
    expected = 'def f(a):\r\n\t"""doc"""\r\n\traise NotImplementedError()' + tail
    assert ex.source == expected  # tab indent kept, CRLF kept, everything else identical
    source_ops.write_source(path, ex.source)
    assert path.read_bytes() == expected.encode()


def test_private_repo_imports() -> None:
    src = (
        "import os\nfrom pkg._sig import _a, b\nfrom pkg.core import _c, d\n"
        "import pkg._x\nfrom other import _e\n"
    )
    assert source_ops.private_repo_imports(src, "", {"pkg"}) == [
        "pkg._sig._a",
        "pkg._sig.b",
        "pkg._x",
        "pkg.core._c",
    ]
    assert source_ops.is_private_dotted("pkg.mod._f") and not source_ops.is_private_dotted(
        "pkg.mod.f"
    )


# --- right-reason classifier --------------------------------------------------------

_IS_TEST = lambda p: p.startswith("tests/")  # noqa: E731


def _report(tests=(), collectors=(), total=None):
    tests = list(tests)
    n_fail = sum(1 for t in tests if t["outcome"] != "passed")
    total = len(tests) if total is None else total
    return {
        "root": "/repo",
        "summary": {"total": total, "collected": total, "failed": n_fail},
        "collectors": list(collectors),
        "tests": tests,
    }


def _failing(nodeid, crash_path, message, tb_paths, exc_type, phase="call", longrepr=""):
    tb = [{"path": p, "lineno": 1, "message": ""} for p in tb_paths]
    if tb:
        tb[-1]["message"] = exc_type
    body = {
        "outcome": "failed",
        "crash": {"path": crash_path, "lineno": 1, "message": message},
        "traceback": tb,
        "longrepr": longrepr,
    }
    return {"nodeid": nodeid, "outcome": "failed" if phase == "call" else "error", phase: body}


def test_classifier_valid_reasons() -> None:
    rep = _report(
        [
            _failing(
                "tests/t.py::a",
                "/repo/tests/t.py",
                "assert 1 == 2",
                ["tests/t.py"],
                "AssertionError",
            ),
            _failing(
                "tests/t.py::b",
                "/repo/tests/t.py",
                "Failed: DID NOT RAISE ValueError",
                ["tests/t.py"],
                "Failed",
            ),
            _failing(
                "tests/t.py::c",
                "/repo/pkg/m.py",
                "NotImplementedError: excised",
                ["tests/t.py", "pkg/m.py"],
                "NotImplementedError",
            ),
            _failing(
                "tests/t.py::d",
                "/repo/pkg/m.py",
                "ZeroDivisionError: division by zero",
                ["tests/t.py", "pkg/m.py"],
                "ZeroDivisionError",
            ),
            # exception raised in stdlib but called from repo code: repo frame present -> valid
            _failing(
                "tests/t.py::e",
                "/usr/lib/python3.12/json/__init__.py",
                "ValueError: bad",
                ["tests/t.py", "pkg/m.py"],
                "ValueError",
            ),
        ]
    )
    v = classify_report(rep, 1, _IS_TEST)
    assert v.ok and v.n_failing == 5 and not v.invalid
    assert [r["reason"] for r in v.reasons.values()] == [
        "AssertionError",
        "pytest.raises",
        "NotImplementedError",
        "exception_in_repo_code",
        "exception_in_repo_code",
    ]


def test_classifier_invalid_reasons() -> None:
    v = classify_report(
        _report(
            [
                _failing(
                    "tests/t.py::a",
                    "/repo/tests/t.py",
                    "ZeroDivisionError: division by zero",
                    ["tests/t.py"],
                    "ZeroDivisionError",
                ),
                _failing(
                    "tests/t.py::b",
                    "/repo/tests/t.py",
                    "ImportError: cannot import name 'x'",
                    ["tests/t.py"],
                    "ImportError",
                ),
                {
                    "nodeid": "tests/t.py::c",
                    "outcome": "error",
                    "setup": {
                        "outcome": "failed",
                        "longrepr": "file t.py, line 3\n  def c(nofix):\n"
                        "E       fixture 'nofix' not found",
                    },
                },
                # exception in a third-party wrapper (no repo frame): strict -> invalid
                _failing(
                    "tests/t.py::d",
                    "/usr/lib/site-packages/face/testing.py",
                    "face.testing.CheckError: exit -1",
                    ["tests/t.py", "/usr/lib/site-packages/face/testing.py"],
                    "CheckError",
                ),
            ]
        ),
        1,
        _IS_TEST,
    )
    assert not v.ok
    assert v.invalid == ["ImportError", "error_before_repo_call", "fixture_not_found"]
    coll = classify_report(
        _report(
            [],
            [
                {
                    "nodeid": "tests/t.py",
                    "outcome": "failed",
                    "longrepr": "ImportError while importing test module\n"
                    "E   ImportError: cannot import name 'q'",
                }
            ],
            total=0,
        ),
        2,
        _IS_TEST,
    )
    assert coll.invalid == ["ImportError"] and not coll.ok
    syntax = classify_report(
        _report(
            [],
            [
                {
                    "nodeid": "tests/t.py",
                    "outcome": "failed",
                    "longrepr": "E   SyntaxError: invalid syntax",
                }
            ],
            total=0,
        ),
        2,
        _IS_TEST,
    )
    assert syntax.invalid == ["SyntaxError"]
    zero = classify_report(_report([], total=0), 5, _IS_TEST)
    assert zero.invalid == ["collected_0_items"]
    passing = classify_report(
        _report([{"nodeid": "tests/t.py::p", "outcome": "passed"}]), 0, _IS_TEST
    )
    assert passing.invalid == ["no_failing_test"] and passing.n_passing == 1
    assert classify_report(None, 1, _IS_TEST).invalid == ["no_report"]
    attr = classify_report(
        _report(
            [
                _failing(
                    "tests/t.py::a",
                    "/repo/tests/t.py",
                    "AttributeError: x",
                    ["tests/t.py"],
                    "AttributeError",
                )
            ]
        ),
        1,
        _IS_TEST,
    )
    assert attr.invalid == ["error_before_repo_call"]
    coll_attr = classify_report(
        _report(
            [],
            [
                {
                    "nodeid": "tests/t.py",
                    "outcome": "failed",
                    "longrepr": "E   AttributeError: module has no attribute",
                }
            ],
            total=0,
        ),
        2,
        _IS_TEST,
    )
    assert coll_attr.invalid == ["AttributeError@import"]
    with pytest.raises(ValueError):  # every emitted reason must be in config.harness lists
        classify_report(
            zero_report := _report([], total=0),
            5,
            _IS_TEST,
            valid_reasons=(),
            invalid_reasons=("no_report",),
        )
    assert zero_report["summary"]["total"] == 0
    two = classify_report(
        _report(
            [
                _failing(
                    "tests/t.py::a",
                    "/repo/pkg/m.py",
                    "NotImplementedError: excised",
                    ["tests/t.py", "pkg/m.py"],
                    "NotImplementedError",
                )
            ]
        ),
        1,
        _IS_TEST,
        min_failing=2,
    )
    assert two.invalid == ["no_failing_test"]


# --- funnel + rank + screen ------------------------------------------------------------


def _fixture_symbols(cfg: Config) -> dict:
    return build_symbol_index(FIXTURES / "mini_pkg", cfg)


def test_funnel_defaults_reject_all_but_clamp_with_reasons() -> None:
    cfg = Config()
    cands = excision.funnel(
        _fixture_symbols(cfg), _smoke.MINI_PKG_TEST_MAP, set(_smoke.MINI_PKG_TEST_MAP), cfg
    )
    by = {c.qualname: c for c in cands}
    assert [c.qualname for c in cands if c.status != "rejected"] == ["mini_pkg.calc.clamp"]
    assert by["mini_pkg.calc.ceil_div"].reject_reason == "too-short(4<8)"
    assert by["mini_pkg.core.dedupe"].reject_reason == "few-covering-tests(1<2)"
    assert by["mini_pkg.text._needs_truncation"].reject_reason == "private"
    assert by["mini_pkg.shapes.area"].reject_reason == "uncovered"
    assert by["mini_pkg.calc.RunningStats.__init__"].reject_reason == "private"
    assert by["test_calc.test_clamp_bounds"].reject_reason == "test-code"
    assert [c.qualname for c in excision.rank(cands, cfg)] == ["mini_pkg.calc.clamp"]


def test_funnel_relaxed_selects_and_ranks_deterministically() -> None:
    ranked, cfg = _smoke.mini_pkg_ranked()
    names = [c.qualname for c in ranked]
    assert names[0] == "mini_pkg.calc.clamp"  # score 12, module round-robin from calc
    assert set(names) == {
        "mini_pkg.calc.clamp",
        "mini_pkg.text.display_width",
        "mini_pkg.core.Registry.register",
        "mini_pkg.calc.ceil_div",
        "mini_pkg.text.truncate",
    }
    assert names.index("mini_pkg.text.display_width") < names.index("mini_pkg.calc.ceil_div")
    again, _ = _smoke.mini_pkg_ranked()
    assert [c.qualname for c in again] == names
    # a passing set restricts covering tests: baseline failures do not count
    cands = excision.funnel(
        _fixture_symbols(cfg),
        _smoke.MINI_PKG_TEST_MAP,
        {"tests/test_calc.py::test_clamp_within"},
        cfg,
    )
    by = {c.qualname: c for c in cands}
    assert by["mini_pkg.calc.clamp"].reject_reason == "few-covering-tests(1<2)"
    assert by["mini_pkg.text.truncate"].reject_reason == "uncovered"


def test_funnel_central_and_private_parent_and_init() -> None:
    cfg = Config()
    cfg.excision.max_covering_tests = 1
    symbols = {
        "modules": [{"name": "p", "is_test": False}, {"name": "p.sub", "is_test": False}],
        "classes": [{"qualname": "p.sub._Hidden", "is_public": False}],
        "functions": [
            {
                "qualname": "p.sub.f",
                "module": "p.sub",
                "file": "p/sub.py",
                "line": 1,
                "end_line": 20,
                "complexity": 5,
                "is_method": False,
                "parent": "p.sub",
                "signature": "f()",
                "docstring": None,
            },
            {
                "qualname": "p.sub._Hidden.m",
                "module": "p.sub",
                "file": "p/sub.py",
                "line": 30,
                "end_line": 50,
                "complexity": 5,
                "is_method": True,
                "parent": "p.sub._Hidden",
                "signature": "m()",
                "docstring": None,
            },
            {
                "qualname": "p.g",
                "module": "p",
                "file": "p/__init__.py",
                "line": 1,
                "end_line": 20,
                "complexity": 5,
                "is_method": False,
                "parent": "p",
                "signature": "g()",
                "docstring": None,
            },
        ],
    }
    tmap = {
        "t.py::a": ["p.sub.f", "p.sub._Hidden.m", "p.g"],
        "t.py::b": ["p.sub.f", "p.sub._Hidden.m", "p.g"],
    }
    by = {c.qualname: c.reject_reason for c in excision.funnel(symbols, tmap, None, cfg)}
    assert by == {
        "p.sub.f": "too-central(2>1)",
        "p.sub._Hidden.m": "private-parent",
        "p.g": "init-module",
    }


def test_funnel_pregate_rejects_private_verifier_imports(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    shutil.copytree(FIXTURES / "mini_pkg", repo)
    shutil.rmtree(repo / ".git")
    (repo / "tests" / "test_calc.py").write_text(
        (repo / "tests" / "test_calc.py").read_text()
        + "\nfrom mini_pkg.text import _needs_truncation\n"
    )
    ranked, cfg = _smoke.mini_pkg_ranked(repo)  # funnel WITH repo -> pre-gate active
    by = {c.qualname: c for c in ranked}
    assert "mini_pkg.calc.clamp" not in by and "mini_pkg.calc.ceil_div" not in by
    cands = excision.funnel(
        build_symbol_index(repo, cfg), _smoke.MINI_PKG_TEST_MAP, None, cfg, repo=repo
    )
    reason = {c.qualname: c.reject_reason for c in cands}["mini_pkg.calc.clamp"]
    assert reason == "verifier-imports-private(tests/test_calc.py: mini_pkg.text._needs_truncation)"
    assert "mini_pkg.text.truncate" in by  # its tests are clean


class _CountingScreen:
    def __init__(self, verdicts):
        self.calls = 0
        self.verdicts = verdicts  # qualname -> (leaks, trivial)

    def complete_json(self, step, messages, schema):
        self.calls += 1
        names = [ln[4:] for ln in messages[0]["content"].splitlines() if ln.startswith("### ")]
        return {
            "screens": [
                {
                    "qualname": n,
                    "docstring_leaks_impl": self.verdicts.get(n, (False, False))[0],
                    "trivially_inferable": self.verdicts.get(n, (False, False))[1],
                    "reason": "r",
                }
                for n in names
            ]
        }


def test_screen_backfills_and_reuses_persisted_decisions() -> None:
    ranked, cfg = _smoke.mini_pkg_ranked()
    cfg.excision.build_target = 2
    cfg.llm.classify_batch_size = 2  # forces several batches
    llm = _CountingScreen(
        {"mini_pkg.calc.clamp": (True, False), "mini_pkg.text.display_width": (False, True)}
    )
    decisions: dict = {}
    selected = excision.screen(ranked, _smoke.FIXTURE_MINI_PKG, llm, cfg, decisions)
    names = [c.qualname for c in selected]
    assert len(names) == 2 and "mini_pkg.calc.clamp" not in names  # backfilled past 2 screened-out
    assert llm.calls == 2 and len(decisions) == 4  # 2 batches of 2, the 5th stays surplus
    statuses = {c.qualname: c.status for c in ranked}
    assert (
        statuses["mini_pkg.calc.clamp"] == "screened_out"
        and list(statuses.values()).count("surplus") == 1
    )
    assert all(c.screen_key for c in ranked if c.status != "surplus")
    # rerun with the persisted decisions: identical selection, zero LLM calls
    ranked2, _ = _smoke.mini_pkg_ranked()
    llm2 = _CountingScreen({})
    again = excision.screen(ranked2, _smoke.FIXTURE_MINI_PKG, llm2, cfg, dict(decisions))
    assert [c.qualname for c in again] == names and llm2.calls == 0


@pytest.mark.skipif(not _cassettes(_smoke.SCREEN_STAGE), reason="s5_tasks cassette not recorded")
def test_screen_replay_records_a_decision_per_candidate(tmp_path: Path) -> None:
    client = LLMClient(stage=_smoke.SCREEN_STAGE, mode="replay", transcripts_dir=tmp_path / "t")
    selected = _smoke.run_excision_screen(client)
    assert selected[0] == "mini_pkg.calc.clamp" and len(selected) == 5  # this tape keeps all
    ranked, cfg = _smoke.mini_pkg_ranked()
    excision.screen(ranked, _smoke.FIXTURE_MINI_PKG, client, cfg)
    assert all(c.screen and c.screen["reason"] and c.screen_key for c in ranked)


# --- manifest + static gate (no docker) --------------------------------------------------


def _fake_task(root: Path, task_id: str, valid: bool | None) -> Path:
    d = root / task_id
    (d / "evidence").mkdir(parents=True)
    (d / "task.json").write_text(
        json.dumps(
            {
                "id": task_id,
                "title": "t",
                "provenance": {"type": "excision", "target": "pkg.mod.fn"},
                "verifier_cmd": "python -m pytest -q x",
                "difficulty": None,
            }
        )
    )
    if valid is not None:
        (d / "evidence" / "verdict.json").write_text(
            json.dumps({"valid": valid, "reasons": [] if valid else ["x"]})
        )
    return d


def test_manifest_status_comes_from_verdict(tmp_path: Path) -> None:
    _fake_task(tmp_path, "exc-b", True)
    _fake_task(tmp_path, "exc-a", False)
    _fake_task(tmp_path, "exc-c", None)
    data = json.loads(write_manifest(tmp_path).read_text())
    assert [(t["id"], t["validation_status"]) for t in data["tasks"]] == [
        ("exc-a", "INVALID"),
        ("exc-b", "VALID"),
        ("exc-c", "UNVALIDATED"),
    ]
    assert data["tasks"][0]["module"] == "pkg.mod" and data["tasks"][0]["validation_reasons"] == [
        "x"
    ]


def test_static_gate_violations(tmp_path: Path) -> None:
    inp = tmp_path / "input"
    (inp / "pkg").mkdir(parents=True)
    (inp / "pkg" / "__init__.py").write_text("from .core import *\nfrom .core import _hidden\n")
    (inp / "pkg" / "core.py").write_text("def pub(): pass\ndef _hidden(): pass\nCONST = 1\n")
    ver = tmp_path / "verifier" / "tests"
    ver.mkdir(parents=True)
    (ver / "test_x.py").write_text(
        "from pkg import pub, CONST\nfrom pkg.core import _hidden\nfrom pkg.core import gone\n"
        "import pkg.core\nimport pkg.nope\nimport os\nimport pkg._impl\nfrom pkg._impl import x\n"
    )
    v = static_gate_violations(inp, tmp_path / "verifier")
    assert [(x["import"], x["reason"]) for x in v] == [
        ("pkg.core._hidden", "private-symbol"),
        ("pkg.core.gone", "symbol-missing-in-input"),
        ("pkg._impl", "private-module"),
        ("pkg._impl.x", "private-module"),
    ]  # `import pkg.nope` is left to the container runs (may be a dynamic module)


# --- docker: runner e2e + harness variants ----------------------------------------------


def _inputs(ctx) -> BuildInputs:
    from pipeline.knowledge.runner import knowledge_paths

    kp = knowledge_paths(ctx.run_dir, ctx.config)
    build = ctx.load("build")
    return BuildInputs(
        repo=ctx.repo,
        repo_name=ctx.run_dir.name,
        base_sha=ctx.report.get("base_sha", ""),
        image_tag=build["image_tag"],
        image_digest=build["image_digest"],
        graph=json.loads(Path(kp["graph"]).read_text()),
        baseline=ctx.load("baseline"),
        knowledge_dir=ctx.knowledge_dir,
        audit_dir=ctx.audit_dir,
        llm=None,
    )


def _clamp_task(ctx, root: Path) -> Path:
    ranked, cfg = _smoke.mini_pkg_ranked(ctx.repo)
    target = next(c for c in ranked if c.qualname == "mini_pkg.calc.clamp")
    return build_task(target, _inputs(ctx), root, ctx.config)


def _set_verifier(task_dir: Path, extra_nodeids: list[str]) -> None:
    tj = task_dir / "task.json"
    task = json.loads(tj.read_text())
    task["verifier_cmd"] = task["verifier_cmd"] + " " + " ".join(extra_nodeids)
    tj.write_text(json.dumps(task))


def _strip_ts(v: dict) -> dict:
    return {k: val for k, val in v.items() if k != "timestamps"}


@pytest.mark.docker
def test_funnel_on_real_test_map(mini_env) -> None:
    ctx = mini_env
    from pipeline.knowledge.runner import knowledge_paths

    kp = knowledge_paths(ctx.run_dir, ctx.config)
    symbols = json.loads(Path(kp["symbols"]).read_text())
    tmap = json.loads(Path(kp["test_map"]).read_text())
    assert tmap == _smoke.MINI_PKG_TEST_MAP  # the cassette prompt is built from this
    defaults = excision.rank(excision.funnel(symbols, tmap, None, Config()), Config())
    assert [c.qualname for c in defaults] == ["mini_pkg.calc.clamp"]
    ranked = excision.rank(excision.funnel(symbols, tmap, None, ctx.config), ctx.config)
    assert ranked[0].qualname == "mini_pkg.calc.clamp"


@pytest.mark.docker
@pytest.mark.skipif(not _cassettes(_smoke.TASKS_STAGE), reason="s5_tasks cassette not recorded")
def test_tasks_stage_e2e_valid_and_resumable(mini_env) -> None:
    from pipeline.tasks.runner import repo_tasks_dir, run_tasks

    ctx = mini_env
    run_tasks(ctx)
    tasks_dir = repo_tasks_dir(ctx)
    manifest = json.loads((tasks_dir / "tasks.json").read_text())
    statuses = {t["id"]: t["validation_status"] for t in manifest["tasks"]}
    bugfix, merge = _smoke.fixture_sha("Fix ceil_div"), _smoke.fixture_sha("Merge pull request")
    assert statuses == {
        "exc-mini_pkg.calc-ceil_div": "VALID",
        "exc-mini_pkg.calc-clamp": "VALID",
        "exc-mini_pkg.core-Registry.register": "VALID",
        "exc-mini_pkg.text-display_width": "VALID",
        "exc-mini_pkg.text-truncate": "VALID",
        f"hist-{bugfix[:7]}": "VALID",
        f"hist-{merge[:7]}": "VALID",
    }
    assert {t["source_type"] for t in manifest["tasks"]} == {"excision", "history"}
    _check_history_e2e(ctx, tasks_dir, bugfix, merge)
    task_dir = tasks_dir / "exc-mini_pkg.calc-clamp"
    for name in (
        "task.json",
        "goldenSolution.md",
        "input",
        "solution",
        "verifier",
        "evidence/fail_before.log",
        "evidence/pass_after.log",
        "evidence/determinism.json",
        "evidence/collateral.json",
        "evidence/verdict.json",
    ):
        assert (task_dir / name).exists(), name
    task = json.loads((task_dir / "task.json").read_text())
    assert task["provenance"] == {
        "type": "excision",
        "target": "mini_pkg.calc.clamp",
        "file": "mini_pkg/calc.py",
        "span": [10, 20],
        "excised_lines": [14, 20],
        "docstring_kept": True,
    }
    assert task["instruction_status"] == "final" and task["difficulty"] in (
        "easy",
        "medium",
        "hard",
    )
    assert task["module"] == "mini_pkg.calc" and task["modules"] == ["mini_pkg.calc"]
    assert task["verifier_on_input"] == {"exit_code": 1, "n_failing": 3, "n_passing": 0}
    assert manifest["tasks"][1]["verifier_on_input"]["n_failing"] == 3
    assert "if value < low" not in task["instruction"]  # no body leak (LLM-authored now)
    assert "## Goal" in task["instruction"] and "## How success is measured" in task["instruction"]
    assert set(task["files_in_scope"]) >= {"mini_pkg/calc.py", "tests/test_calc.py"}
    assert (task_dir / "input/mini_pkg/calc.py").read_text().count("excised") == 1
    assert (task_dir / "solution/mini_pkg/calc.py").read_text() == (
        ctx.repo / "mini_pkg/calc.py"
    ).read_text()
    assert not (task_dir / "input" / ".git").exists()
    verdict = json.loads((task_dir / "evidence/verdict.json").read_text())
    assert verdict["valid"] and verdict["repeat_count"] == 3 and verdict["image_digest"]
    assert (
        verdict["environment_hashes"]["Dockerfile"]
        and verdict["environment_hashes"]["requirements.lock.txt"]
    )
    assert (task_dir / "evidence/fail_before.report.json").is_file()
    assert (
        json.loads((task_dir / "evidence/pass_after.report.json").read_text())["summary"]["passed"]
        == 3
    )
    assert all(
        r["reason"] == "NotImplementedError"
        for r in verdict["checks"]["right_reason"]["tests"].values()
    )
    golden = (task_dir / "goldenSolution.md").read_text()
    assert (
        "+    if value < low:" in golden and '-    raise NotImplementedError("excised")' in golden
    )
    cands = json.loads((ctx.tasks_dir / "candidates.json").read_text())
    assert cands["counts"]["selected"] == 5 and "screened_out" not in cands["counts"]
    assert all(c["reject_reason"] for c in cands["candidates"] if c["status"] == "rejected")
    # resumable: a second run skips every step
    ctx.report["stages"] = {}
    run_tasks(ctx)
    assert all(
        ctx.report["stages"][s]["skipped"]
        for s in (
            "excision_funnel",
            "build_excision",
            "history_funnel",
            "build_history",
            "validate",
            "instruct",
            "manifest",
        )
    )
    # harness idempotent: same folder, identical verdict (timestamps aside)
    again = validate_task(task_dir, ctx.config)
    assert _strip_ts(again) == _strip_ts(verdict)
    _check_classify_reuse(ctx)


def _check_history_e2e(ctx, tasks_dir: Path, bugfix: str, merge: str) -> None:
    from pipeline.tasks import history as H

    hist = json.loads((ctx.tasks_dir / "history_candidates.json").read_text())
    by = {c["sha"]: c for c in hist["candidates"]}
    reasons = {c["message"][:20]: c["reject_reason"] for c in hist["candidates"]}
    assert reasons["docs: add README wit"] == "docs-or-ci-only"
    assert reasons["Use wcwidth for accu"] == "dependency-changing"
    assert reasons["Refactor: extract _n"] == "kind:refactor"  # SMALL classify (cassette)
    assert reasons["Rename geometry modu"] == "uncovered-and-no-tests"
    assert reasons["Initial package: cal"] == "root-commit"
    assert reasons["Accept inverted boun"] == f"superseded-by-merge({merge[:7]})"
    assert reasons["Test clamp with inve"] == "no-source-change"
    assert reasons["Add text module with"] == "verifier-on-input:ModuleNotFoundError"
    assert reasons["Add core.first helpe"] == (
        "verifier-imports-symbol-missing-in-input(mini_pkg.core.first; rewrite:budget-exhausted)"
    )
    assert by[bugfix]["status"] == "built" and by[bugfix]["kind"] == "bugfix"
    assert by[bugfix]["score_breakdown"] == {
        "fix_keyword": 1.0,
        "adds_tests": 2.0,
        "public_fn": 1.0,
        "single_function": 1.0,
    }
    assert hist["shortlist"][:2] == [bugfix, merge]  # both score 5; bugfix beats feature
    built = json.loads((ctx.tasks_dir / "built_history.json").read_text())
    assert built["_decisions"] and all(len(k) == 16 for k in built["_decisions"])
    task_dir = tasks_dir / f"hist-{bugfix[:7]}"
    for name in (
        "goldenSolution.md",
        "verifier/run.sh",
        "verifier/tests/test_calc.py",
        "evidence/fail_before.log",
        "evidence/pass_after.log",
        "evidence/determinism.json",
        "evidence/collateral.json",
        "evidence/verdict.json",
    ):
        assert (task_dir / name).exists(), name
    task = json.loads((task_dir / "task.json").read_text())
    prov = task["provenance"]
    assert prov["type"] == "history" and prov["commit"] == bugfix
    assert prov["parent"] == H.git(ctx.repo, "rev-parse", f"{bugfix}^").strip()
    assert prov["verifier_source"] == "commit-tests" and prov["classification"]["kind"] == "bugfix"
    assert task["verifier_tests"] == ["tests/test_calc.py::test_ceil_div_exact_multiple"]
    assert task["instruction_status"] == "final" and task["difficulty_status"] == "final"
    assert task["difficulty"] in ("easy", "medium", "hard") and task["difficulty_rationale"]
    assert task["module"] == "mini_pkg.calc" and task["modules"] == ["mini_pkg.calc"]
    assert set(task["difficulty_features"]) == set(ctx.config.difficulty.features)
    assert (
        "quotient" not in task["instruction"] and "divmod" not in task["instruction"]
    )  # solution text
    assert task["title"] and task["title"] != task["provenance"]["message"]
    assert task["neutrality"]["decision"]["neutral"] is True and task["neutrality"]["checked"]
    assert (
        task["verifier_on_input"]["n_failing"] == 1
        and task["verifier_on_solution"]["n_passing"] == 1
    )
    assert (
        task["collateral"]["source"] == "input-run"
        and len(task["collateral"]["baseline_passing"]) == 10
    )
    assert set(task["files_in_scope"]) >= {"mini_pkg/calc.py", "tests/test_calc.py"}
    assert task["overlay_files"]["input"] == task["overlay_files"]["solution"]
    assert "Dockerfile" in task["overlay_files"]["input"]
    assert not any(".egg-info" in f for f in task["overlay_files"]["input"])
    # input/solution are the historical trees; the overlay never overwrites
    assert (task_dir / "input/mini_pkg/calc.py").read_text() == H.show(
        ctx.repo, f"{bugfix}^", "mini_pkg/calc.py"
    )
    assert (task_dir / "solution/mini_pkg/calc.py").read_text() == H.show(
        ctx.repo, bugfix, "mini_pkg/calc.py"
    )
    assert (task_dir / "input/setup.py").read_text() == H.show(ctx.repo, f"{bugfix}^", "setup.py")
    verdict = json.loads((task_dir / "evidence/verdict.json").read_text())
    assert verdict["valid"] and verdict["checks"]["collateral"]["ok"]
    assert (
        list(verdict["checks"]["right_reason"]["tests"].values())[0]["reason"] == "AssertionError"
    )
    golden = (task_dir / "goldenSolution.md").read_text()
    assert "+    quotient, remainder = divmod(a, b)" in golden and "TODO-S5" not in golden
    assert "## Why correct" in golden
    # every VALID task got a final instruction + difficulty; template markers are gone
    manifest = json.loads((tasks_dir / "tasks.json").read_text())
    for entry in manifest["tasks"]:
        if entry["validation_status"] == "VALID":
            assert entry["instruction_status"] == "final" and entry["module"], entry["id"]
            t = json.loads((tasks_dir / entry["path"] / "task.json").read_text())
            assert not t["instruction_status"].startswith("template"), entry["id"]
    inst = ctx.report["tasks"]["instruct"]
    assert inst["final"] == 7 and inst["failed"] == 0 and inst["difficulty_failed"] == 0
    assert (ctx.tasks_dir / "instructions.json").is_file()
    # PR merge: input = FIRST parent (mainline), solution = the merge
    mtask = json.loads((tasks_dir / f"hist-{merge[:7]}" / "task.json").read_text())
    first_parent = H.git(ctx.repo, "rev-parse", f"{merge}^1").strip()
    assert mtask["provenance"]["is_merge"] and mtask["provenance"]["parent"] == first_parent
    assert mtask["provenance"]["pr_number"] == 7
    assert (
        "low > high" not in (tasks_dir / f"hist-{merge[:7]}" / "input/mini_pkg/calc.py").read_text()
    )
    assert (
        "low > high" in (tasks_dir / f"hist-{merge[:7]}" / "solution/mini_pkg/calc.py").read_text()
    )
    assert mtask["verifier_tests"] == ["tests/test_calc.py::test_clamp_inverted_bounds"]


def _check_classify_reuse(ctx) -> None:
    """A forced funnel rerun reuses every persisted classify decision: zero LLM calls."""
    from pipeline.tasks.runner import step_history_funnel

    hist = json.loads((ctx.tasks_dir / "history_candidates.json").read_text())
    real_llm, ctx.llm = ctx.llm, _NoLLM()
    try:
        step_history_funnel(ctx)
    finally:
        ctx.llm = real_llm
    again = json.loads((ctx.tasks_dir / "history_candidates.json").read_text())
    assert again["classify_reused"] == 6 and again["shortlist"] == hist["shortlist"]


class _NoLLM:
    def complete_json(self, *a, **k):
        raise AssertionError("LLM must not be called: decisions are persisted")


@pytest.mark.docker
def test_verifier_run_sh_executes_in_container(mini_env, tmp_path: Path) -> None:
    from pipeline.docker.runner import fresh_workdir, run_in_container

    ctx = mini_env
    task_dir = _clamp_task(ctx, tmp_path)
    assert (task_dir / "verifier/run.sh").stat().st_mode & 0o111
    codes = {}
    for tree in ("solution", "input"):
        with fresh_workdir(task_dir / tree) as work:
            shutil.copytree(task_dir / "verifier", work, dirs_exist_ok=True)
            codes[tree] = run_in_container(work, "./run.sh", ctx.image_tag).exit_code
    assert codes == {"solution": 0, "input": 1}


@pytest.mark.docker
def test_harness_verifier_import_only_in_solution_is_invalid(mini_env, tmp_path: Path) -> None:
    ctx = mini_env
    task_dir = _clamp_task(ctx, tmp_path)
    with (task_dir / "solution/mini_pkg/calc.py").open("a") as fh:
        fh.write("\n\ndef clamp2(v, lo, hi):\n    return max(lo, min(v, hi))\n")
    (task_dir / "verifier/tests/test_extra.py").write_text(
        "from mini_pkg.calc import clamp2\n\ndef test_clamp2():\n    assert clamp2(5, 0, 3) == 3\n"
    )
    _set_verifier(task_dir, ["tests/test_extra.py::test_clamp2"])
    v = validate_task(task_dir, ctx.config)
    assert not v["valid"]
    assert "fail-reason:ImportError" in v["reasons"]
    assert "verifier-imports-non-public-or-missing" in v["reasons"]
    assert v["checks"]["static_gate"]["violations"][0]["import"] == "mini_pkg.calc.clamp2"


@pytest.mark.docker
def test_harness_flaky_verifier_fails_determinism(mini_env, tmp_path: Path) -> None:
    ctx = mini_env
    task_dir = _clamp_task(ctx, tmp_path)
    (task_dir / "verifier/tests/test_flaky.py").write_text(
        "import time\nimport pytest\n\n@pytest.mark.parametrize('bit', range(10, 22))\n"
        "def test_flaky(bit):\n    assert (time.time_ns() >> bit) & 1 == 0\n"
    )
    _set_verifier(task_dir, ["tests/test_flaky.py"])
    v = validate_task(task_dir, ctx.config)
    assert not v["valid"] and "nondeterministic" in v["reasons"]
    det = json.loads((task_dir / "evidence/determinism.json").read_text())
    assert det["runs"] == 3 and not det["identical"] and len(det["fail_before"]) == 3


@pytest.mark.docker
def test_harness_collateral_breakage(mini_env, tmp_path: Path) -> None:
    ctx = mini_env
    task_dir = _clamp_task(ctx, tmp_path)
    calc = task_dir / "solution/mini_pkg/calc.py"
    calc.write_text(calc.read_text().replace("quotient + bool(remainder)", "quotient"))
    v = validate_task(task_dir, ctx.config)
    assert v["reasons"] == ["collateral-breakage"]
    col = json.loads((task_dir / "evidence/collateral.json").read_text())
    assert col["newly_failing"] == ["tests/test_calc.py::test_ceil_div_rounds_up"]
    assert col["baseline_passing"] == 13


@pytest.mark.docker
def test_harness_recopies_canonical_verifier(mini_env, tmp_path: Path) -> None:
    ctx = mini_env
    task_dir = _clamp_task(ctx, tmp_path)
    tampered = (
        "def test_clamp_within():\n    assert True\n\ndef test_clamp_bounds():\n    assert True\n"
    )
    (task_dir / "input/tests/test_calc.py").write_text(tampered)
    assert validate_task(task_dir, ctx.config)["valid"]
    loose = Config()
    loose.harness.recopy_canonical_verifier = False
    v = validate_task(task_dir, loose)
    assert not v["valid"] and "input-does-not-fail" in v["reasons"]


@pytest.mark.docker
def test_harness_static_gate_private_import(mini_env, tmp_path: Path) -> None:
    ctx = mini_env
    task_dir = _clamp_task(ctx, tmp_path)
    (task_dir / "verifier/tests/test_priv.py").write_text(
        "from mini_pkg.text import _needs_truncation\n\n"
        "def test_priv():\n    assert _needs_truncation('ab', 1)\n"
    )
    _set_verifier(task_dir, ["tests/test_priv.py::test_priv"])
    v = validate_task(task_dir, ctx.config)
    assert v["reasons"] == ["verifier-imports-non-public-or-missing"]
    assert v["checks"]["static_gate"]["violations"] == [
        {
            "file": "tests/test_priv.py",
            "line": 1,
            "import": "mini_pkg.text._needs_truncation",
            "reason": "private-symbol",
        }
    ]


@pytest.mark.docker
def test_validate_cli(mini_env, tmp_path: Path, capsys) -> None:
    from pipeline.validate import main

    ctx = mini_env
    task_dir = _clamp_task(ctx, tmp_path)
    assert task_dir.name == "exc-mini_pkg.calc-clamp"
    rc = main([str(task_dir), "--set", "excision.min_lines=3"])
    assert rc == 0 and capsys.readouterr().out.startswith("VALID")


# --- bounded verifier top-up agent (scripted endpoint; no live BIG call) ------------------


class _ScriptedLLM:
    def __init__(self, completions):
        self._it = iter(completions)
        self.calls = 0

    def chat(self, step, messages, tools=None, tool_choice=None, max_tokens=None):
        self.calls += 1
        return next(self._it)


def test_top_up_agent_adds_one_verifier_file_and_audits(tmp_path: Path) -> None:
    from pipeline.tasks.build_excision import _top_up_tests
    from tests.test_llm import make_completion

    repo = tmp_path / "repo"
    shutil.copytree(FIXTURES / "mini_pkg", repo)
    shutil.rmtree(repo / ".git")
    ranked, cfg = _smoke.mini_pkg_ranked(repo)
    cfg.excision.min_assertions_touching_fn = 3
    target = next(c for c in ranked if c.qualname == "mini_pkg.text.truncate")
    task_dir = tmp_path / "task"
    shutil.copytree(repo, task_dir / "solution")
    (task_dir / "verifier").mkdir()
    new_test = (
        "from mini_pkg.text import truncate\n\ndef test_edge():\n    assert truncate('', 3) == ''\n"
    )
    scripted = _ScriptedLLM(
        [
            make_completion(
                tool_calls=[
                    (
                        "write_file",
                        json.dumps(
                            {"path": "tests/test_excision_truncate.py", "content": new_test}
                        ),
                    ),
                    (
                        "write_file",
                        json.dumps({"path": "mini_pkg/text.py", "content": "# tampered\n"}),
                    ),
                ]
            ),
            make_completion(content="done"),
        ]
    )
    inp = BuildInputs(
        repo=repo,
        repo_name="mini_pkg",
        base_sha="",
        image_tag="unused",
        image_digest="",
        graph={},
        baseline={},
        knowledge_dir=tmp_path / "k",
        audit_dir=tmp_path / "audit",
        llm=scripted,
    )
    added, note = _top_up_tests(target, inp, task_dir, "tests/test_text.py", cfg)
    assert added == ["tests/test_excision_truncate.py::test_edge"]
    assert (task_dir / "verifier/tests/test_excision_truncate.py").read_text() == new_test
    assert not (task_dir / "verifier/mini_pkg").exists()  # only the one file is kept
    assert (
        task_dir / "solution/mini_pkg/text.py"
    ).read_text() != "# tampered\n"  # agent worked on a copy
    assert note["outcome"] == "added" and note["attempts"] == 1 and scripted.calls == 2
    audit = [
        json.loads(line)
        for line in (tmp_path / "audit/agent_actions.jsonl").read_text().splitlines()
    ]
    assert audit[0]["stage"] == "p3.build.verifier_agent" and audit[0]["tests_added"] == 1


def test_build_step_prunes_stale_excision_folders(tmp_path: Path) -> None:
    from types import SimpleNamespace

    from pipeline.tasks.runner import _prune_stale

    cfg = Config()
    cfg.tasks.tasks_root = str(tmp_path / "tasks")
    root = tmp_path / "tasks" / "repo"
    for name in ("exc-a", "exc-stale", "hist-keep"):
        (root / name).mkdir(parents=True)
    ctx = SimpleNamespace(config=cfg, run_dir=tmp_path / "out" / "repo")
    _prune_stale(ctx, "exc", {"exc-a"})
    assert sorted(p.name for p in root.iterdir()) == ["exc-a", "hist-keep"]
