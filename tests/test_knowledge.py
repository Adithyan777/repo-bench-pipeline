"""P2 knowledge-layer tests: symbol index, repo_graph, indexes, verification, tools.

Real AST/git/docker; no LLM at all in this layer. Structural graph facts are
hand-written by reading the mini_pkg fixture, not copied from output. The single
container round-trip (coverage -> test_map/coverage) is marked `docker`.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from pipeline.agent.tools import ToolContext, graph_tools
from pipeline.ecosystems.symbols import build_symbol_index
from pipeline.knowledge import graph as graph_mod
from pipeline.knowledge import indexes, verify

FIXTURES = Path(__file__).resolve().parent / "fixtures"


# --- helpers ------------------------------------------------------------------


def _write_repo(root: Path, files: dict[str, str]) -> Path:
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    return root


def _edges(graph: dict, edge_type: str) -> set[tuple[str, str]]:
    return {(e["source"], e["target"]) for e in graph["edges"] if e["type"] == edge_type}


def _node_ids(graph: dict) -> set[str]:
    return {n["id"] for n in graph["nodes"]}


def _git(repo: Path, *args: str) -> str:
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True, env=env
    ).stdout.strip()


def _commit(repo: Path, files: dict[str, str | None], msg: str) -> str:
    for rel, content in files.items():
        path = repo / rel
        if content is None:
            path.unlink(missing_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", msg)
    return _git(repo, "rev-parse", "HEAD")


# --- symbol index -------------------------------------------------------------


def test_symbol_index_mini_pkg() -> None:
    idx = build_symbol_index(FIXTURES / "mini_pkg")
    quals = {f["qualname"]: f for f in idx["functions"]}
    assert "mini_pkg.calc.ceil_div" in quals
    assert quals["mini_pkg.calc.clamp"]["complexity"] == 4
    assert quals["mini_pkg.calc.ceil_div"]["complexity"] == 1
    test_modules = {m["name"] for m in idx["modules"] if m["is_test"]}
    assert test_modules == {"test_calc", "test_core", "test_text"}


def test_intra_repo_calls_resolved_and_unresolved_not_guessed() -> None:
    idx = build_symbol_index(FIXTURES / "mini_pkg")
    quals = {f["qualname"]: f for f in idx["functions"]}
    truncate = quals["mini_pkg.text.truncate"]
    assert {c["target"] for c in truncate["calls"]} == {"mini_pkg.text._needs_truncation"}
    dedupe = quals["mini_pkg.core.dedupe"]
    assert dedupe["calls"] == []
    unresolved = {c["text"] for c in dedupe["unresolved_calls"]}
    assert "set" in unresolved and "seen.add" in unresolved


def test_relative_and_aliased_imports_resolve(tmp_path: Path) -> None:
    repo = _write_repo(
        tmp_path / "r",
        {
            "pkg/__init__.py": "def top():\n    return 1\n",
            "pkg/a.py": "def helper():\n    return 2\n",
            "pkg/b.py": (
                "from .a import helper\n"
                "from . import a\n"
                "import pkg\n"
                "import pkg.a\n\n\n"
                "def use():\n"
                "    helper()\n"  # relative from-import
                "    a.helper()\n"  # relative module alias
                "    pkg.top()\n"  # top package defines top
                "    pkg.a.helper()\n"  # dotted chain off `import pkg.a`
            ),
        },
    )
    idx = build_symbol_index(repo)
    use = next(f for f in idx["functions"] if f["qualname"] == "pkg.b.use")
    assert {c["target"] for c in use["calls"]} == {"pkg.a.helper", "pkg.top"}
    assert use["unresolved_calls"] == []


def test_relative_import_resolves_when_module_sorts_first(tmp_path: Path) -> None:
    # `aaa` sorts before `zzz`; with all modules registered before imports are parsed,
    # `from .zzz import helper` still resolves regardless of file order.
    repo = _write_repo(
        tmp_path / "r",
        {
            "pkg/__init__.py": "",
            "pkg/aaa.py": "from .zzz import helper\n\n\ndef use():\n    helper()\n",
            "pkg/zzz.py": "def helper():\n    return 1\n",
        },
    )
    idx = build_symbol_index(repo)
    aaa = next(m for m in idx["modules"] if m["name"] == "pkg.aaa")
    assert any(i["target_module"] == "pkg.zzz" for i in aaa["imports"])
    use = next(f for f in idx["functions"] if f["qualname"] == "pkg.aaa.use")
    assert {c["target"] for c in use["calls"]} == {"pkg.zzz.helper"}
    graph = graph_mod.build_graph(idx)
    assert ("pkg.aaa", "pkg.zzz") in _edges(graph, "imports")


def test_code_fingerprint_invalidates_on_change(tmp_path: Path) -> None:
    from pipeline.state import code_fingerprint

    f = tmp_path / "analyzer.py"
    f.write_text("x = 1\n")
    before = code_fingerprint([str(f)])
    f.write_text("x = 2\n")  # a code change must change the fingerprint
    assert code_fingerprint([str(f)]) != before
    assert code_fingerprint([str(tmp_path / "missing.py")]) != before  # absent != present


def test_import_dotted_binds_top_package_only(tmp_path: Path) -> None:
    # `import pkg.sub` binds `pkg`; `sub` alone is NOT a bound module reference.
    repo = _write_repo(
        tmp_path / "r",
        {
            "pkg/__init__.py": "",
            "pkg/sub.py": "def f():\n    return 1\n",
            "pkg/c.py": "import pkg.sub\n\n\ndef g():\n    sub.f()\n",  # `sub` unbound
        },
    )
    idx = build_symbol_index(repo)
    g = next(f for f in idx["functions"] if f["qualname"] == "pkg.c.g")
    assert g["calls"] == []  # sub.f() does not resolve (only `pkg` is bound)
    assert any(c["text"] == "sub.f" for c in g["unresolved_calls"])


def test_complexity_counts_comprehension_ifs() -> None:
    idx = build_symbol_index(
        _write_repo(
            Path(__import__("tempfile").mkdtemp()) / "r",
            {"m.py": "def f(xs):\n    return [x for x in xs if x > 0 if x < 10]\n"},
        )
    )
    f = next(fn for fn in idx["functions"] if fn["qualname"] == "m.f")
    assert f["complexity"] == 4  # base 1 + for-clause 1 + two ifs


def test_inheritance_resolved_intra_repo(tmp_path: Path) -> None:
    repo = _write_repo(
        tmp_path / "r",
        {
            "pkg/__init__.py": "",
            "pkg/base.py": "class Animal:\n    def speak(self):\n        return '?'\n",
            "pkg/dog.py": (
                "from pkg.base import Animal\n\n\n"
                "class Dog(Animal):\n    def speak(self):\n        return 'woof'\n"
            ),
        },
    )
    idx = build_symbol_index(repo)
    dog = next(c for c in idx["classes"] if c["qualname"] == "pkg.dog.Dog")
    assert dog["bases"][0]["target"] == "pkg.base.Animal"
    graph = graph_mod.build_graph(idx)
    assert ("pkg.dog.Dog", "pkg.base.Animal") in _edges(graph, "inherits")


# --- graph: hand-written expected structure -----------------------------------


def test_graph_expected_nodes_and_edges() -> None:
    idx = build_symbol_index(FIXTURES / "mini_pkg")
    graph = graph_mod.build_graph(idx)  # structural: no test_map/coverage

    expected_nodes = {
        "mini_pkg",
        "mini_pkg.calc",
        "mini_pkg.core",
        "mini_pkg.text",
        "mini_pkg.shapes",
        "mini_pkg.calc.RunningStats",
        "mini_pkg.core.Registry",
        "mini_pkg.calc.ceil_div",
        "mini_pkg.calc.clamp",
        "mini_pkg.calc.RunningStats.__init__",
        "mini_pkg.calc.RunningStats.add",
        "mini_pkg.calc.RunningStats.mean",
        "mini_pkg.calc.RunningStats.count",
        "mini_pkg.core.dedupe",
        "mini_pkg.core.first",
        "mini_pkg.core.Registry.__init__",
        "mini_pkg.core.Registry.register",
        "mini_pkg.core.Registry.get",
        "mini_pkg.core.Registry.names",
        "mini_pkg.text.display_width",
        "mini_pkg.text._needs_truncation",
        "mini_pkg.text.truncate",
        "mini_pkg.shapes.area",
    }
    assert _node_ids(graph) == expected_nodes  # setup.py excluded as non-source

    assert _edges(graph, "imports") == {
        ("mini_pkg", "mini_pkg.calc"),
        ("mini_pkg", "mini_pkg.core"),
        ("mini_pkg", "mini_pkg.text"),
    }
    assert _edges(graph, "calls") == {
        ("mini_pkg.text._needs_truncation", "mini_pkg.text.display_width"),
        ("mini_pkg.text.truncate", "mini_pkg.text._needs_truncation"),
    }
    assert _edges(graph, "inherits") == set()
    contains = _edges(graph, "contains")
    assert ("mini_pkg.calc", "mini_pkg.calc.ceil_div") in contains
    assert ("mini_pkg.calc.RunningStats", "mini_pkg.calc.RunningStats.mean") in contains
    assert len(contains) == 18  # 16 + shapes.area + core.first
    for edge in graph["edges"]:
        assert edge["evidence"]["file"] and edge["evidence"]["line"] >= 1


def test_graph_bytes_deterministic() -> None:
    idx = build_symbol_index(FIXTURES / "mini_pkg")
    a = json.dumps(graph_mod.build_graph(idx), indent=2, sort_keys=True)
    b = json.dumps(graph_mod.build_graph(idx), indent=2, sort_keys=True)
    assert a == b


def test_graph_metadata_diversity_unit() -> None:
    idx = build_symbol_index(FIXTURES / "mini_pkg")
    meta = graph_mod.build_graph(idx)["metadata"]
    assert meta["diversity_unit"] == "file"
    assert meta["complexity_metric"] == "branch_count"
    assert meta["source_module_count"] == 5


# --- test_map / coverage join (synthetic coverage contexts, no docker) --------


def test_test_map_and_coverage_join() -> None:
    idx = build_symbol_index(FIXTURES / "mini_pkg")
    fn = {f["qualname"]: f for f in idx["functions"]}
    ceil = fn["mini_pkg.calc.ceil_div"]
    clamp = fn["mini_pkg.calc.clamp"]
    cov_json = {
        "files": {
            "mini_pkg/calc.py": {
                "executed_lines": [ceil["line"], ceil["end_line"], clamp["line"]],
                "missing_lines": list(range(clamp["line"] + 1, clamp["end_line"] + 1)),
                "contexts": {
                    str(ceil["end_line"]): ["tests/test_calc.py::test_ceil_div_rounds_up"],
                },
            }
        }
    }
    tmap = indexes.build_test_map(idx, cov_json)
    assert tmap["tests/test_calc.py::test_ceil_div_rounds_up"] == ["mini_pkg.calc.ceil_div"]
    cov = indexes.build_coverage(idx, cov_json)
    assert cov["mini_pkg.calc.ceil_div"] == 100.0
    assert cov["mini_pkg.calc.clamp"] < 100.0


def test_tested_by_collapses_parametrized_cases() -> None:
    # two parametrizations of one test -> one tested_by edge (the base nodeid)
    test_map = {
        "tests/test_calc.py::test_ceil_div[a]": ["mini_pkg.calc.ceil_div"],
        "tests/test_calc.py::test_ceil_div[b]": ["mini_pkg.calc.ceil_div"],
    }
    idx = build_symbol_index(FIXTURES / "mini_pkg")
    graph = graph_mod.build_graph(idx, test_map)
    tb = [
        e["target"]
        for e in graph["edges"]
        if e["type"] == "tested_by" and e["source"] == "mini_pkg.calc.ceil_div"
    ]
    assert tb == ["tests/test_calc.py::test_ceil_div"]


# --- history index / hotspots (real git, no docker) ---------------------------


def test_history_index_bugfix_and_manifest() -> None:
    base = _head(FIXTURES / "mini_pkg")
    history = indexes.build_history_index(FIXTURES / "mini_pkg", base)
    by_msg = {c["message"]: c for c in history}
    bugfix = next(c for c in history if c["message"].startswith("Fix ceil_div"))
    assert "mini_pkg.calc.ceil_div" in bugfix["touched_functions"]
    assert "tests/test_calc.py" in bugfix["test_files_touched"]
    assert bugfix["touches_manifest"] is False
    dep = next(c for c in history if c["message"].startswith("Use wcwidth"))
    assert dep["touches_manifest"] is True
    docs = by_msg["docs: add README with usage examples"]
    assert docs["touched_functions"] == [] and docs["touches_manifest"] is False


def test_history_spans_are_at_that_commit() -> None:
    # The refactor commit moves/renames functions in text.py; touched functions come
    # from the file's AST AT that commit, not HEAD.
    base = _head(FIXTURES / "mini_pkg")
    history = indexes.build_history_index(FIXTURES / "mini_pkg", base)
    refactor = next(c for c in history if c["message"].startswith("Refactor"))
    assert "mini_pkg.text._needs_truncation" in refactor["touched_functions"]
    assert "mini_pkg.text.truncate" in refactor["touched_functions"]


def test_history_rename_reports_both_sides() -> None:
    base = _head(FIXTURES / "mini_pkg")
    history = indexes.build_history_index(FIXTURES / "mini_pkg", base)
    rename = next(c for c in history if c["message"].startswith("Rename geometry"))
    assert "mini_pkg/geometry.py" in rename["files_changed"]
    assert "mini_pkg/shapes.py" in rename["files_changed"]
    # with --no-renames both the removed and added spans are attributed
    assert "mini_pkg.geometry.area" in rename["touched_functions"]
    assert "mini_pkg.shapes.area" in rename["touched_functions"]


def test_history_deleted_and_merge_commits(tmp_path: Path) -> None:
    repo = tmp_path / "r"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _commit(repo, {"m.py": "def a():\n    return 1\n"}, "init")
    _commit(repo, {"m.py": None, "n.py": "def b():\n    return 2\n"}, "drop m add n")
    _git(repo, "checkout", "-q", "-b", "feature")
    _commit(repo, {"n.py": "def b():\n    return 3\n"}, "change b")
    _git(repo, "checkout", "-q", "main")
    _commit(repo, {"o.py": "def c():\n    return 4\n"}, "add o")
    _git(repo, "merge", "-q", "--no-ff", "feature", "-m", "merge feature")
    history = indexes.build_history_index(repo, _head(repo))
    deleted = next(c for c in history if c["message"] == "drop m add n")
    assert "m.a" in deleted["touched_functions"]  # old side of a deleted file
    assert "n.b" in deleted["touched_functions"]
    merge = next(c for c in history if c["message"] == "merge feature")
    assert merge["is_merge"] is True and len(merge["parents"]) == 2


def test_history_src_layout_module_names(tmp_path: Path) -> None:
    repo = tmp_path / "r"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _commit(repo, {"src/pkg/mod.py": "def go():\n    return 1\n"}, "add mod")
    _commit(repo, {"src/pkg/mod.py": "def go():\n    return 2\n"}, "change go")
    history = indexes.build_history_index(repo, _head(repo))
    change = next(c for c in history if c["message"] == "change go")
    assert change["touched_functions"] == ["pkg.mod.go"]  # src/ stripped


def test_hotspots_from_history() -> None:
    base = _head(FIXTURES / "mini_pkg")
    history = indexes.build_history_index(FIXTURES / "mini_pkg", base)
    hot = indexes.build_hotspots(history)
    assert hot["mini_pkg.calc.ceil_div"] == 2


# --- verification -------------------------------------------------------------


def test_verify_confirms_clean_graph() -> None:
    idx = build_symbol_index(FIXTURES / "mini_pkg")
    graph = graph_mod.build_graph(idx)
    report = verify.verify_graph(FIXTURES / "mini_pkg", graph, idx, image=None)
    for edge_type in ("imports", "contains", "calls"):
        assert report["by_edge_type"][edge_type]["precision"] == 1.0
    assert report["mismatches"] == []


def test_verify_catches_wrong_module_same_leaf() -> None:
    idx = build_symbol_index(FIXTURES / "mini_pkg")
    graph = graph_mod.build_graph(idx)
    for edge in graph["edges"]:
        if edge["type"] == "calls" and edge["target"] == "mini_pkg.text.display_width":
            edge["target"] = "mini_pkg.calc.display_width"  # same leaf, wrong module
            break
    report = verify.verify_graph(FIXTURES / "mini_pkg", graph, idx, image=None)
    assert report["by_edge_type"]["calls"]["mismatch"] == 1
    assert any(m["target"] == "mini_pkg.calc.display_width" for m in report["mismatches"])


def test_verify_tested_by_from_coverage_contexts() -> None:
    idx = build_symbol_index(FIXTURES / "mini_pkg")
    fn = next(f for f in idx["functions"] if f["qualname"] == "mini_pkg.calc.ceil_div")
    test_map = {"tests/test_calc.py::test_ceil_div_rounds_up": ["mini_pkg.calc.ceil_div"]}
    graph = graph_mod.build_graph(idx, test_map)
    contexts = {
        "files": {
            "mini_pkg/calc.py": {
                "contexts": {str(fn["end_line"]): ["tests/test_calc.py::test_ceil_div_rounds_up"]}
            }
        }
    }
    report = verify.verify_graph(
        FIXTURES / "mini_pkg", graph, idx, coverage_contexts=contexts, image=None
    )
    assert report["by_edge_type"]["tested_by"]["precision"] == 1.0
    # a fabricated tested_by edge fails against the raw contexts
    graph["edges"].append(
        {
            "type": "tested_by",
            "source": "mini_pkg.calc.clamp",
            "target": "tests/test_calc.py::test_ceil_div_rounds_up",
            "evidence": {"file": "tests/test_calc.py", "line": 1},
        }
    )
    report2 = verify.verify_graph(
        FIXTURES / "mini_pkg", graph, idx, coverage_contexts=contexts, image=None
    )
    assert report2["by_edge_type"]["tested_by"]["mismatch"] == 1


# --- agent tools --------------------------------------------------------------


def _tool_ctx(tmp_path: Path) -> ToolContext:
    idx = build_symbol_index(FIXTURES / "mini_pkg")
    tmap = {"tests/test_calc.py::test_ceil_div_rounds_up": ["mini_pkg.calc.ceil_div"]}
    cov = {"mini_pkg.calc.ceil_div": 100.0}
    graph = graph_mod.build_graph(idx, tmap, cov)
    kdir = tmp_path / "knowledge"
    kdir.mkdir()
    (kdir / "repo_graph.json").write_text(json.dumps(graph))
    return ToolContext(
        workdir=FIXTURES / "mini_pkg", knowledge_dir=kdir, repo_root=FIXTURES / "mini_pkg"
    )


def test_agent_graph_tools(tmp_path: Path) -> None:
    tools = {t.name: t for t in graph_tools(_tool_ctx(tmp_path))}
    assert "mini_pkg/calc.py:4-7" in tools["show_symbol"].func(qualname="mini_pkg.calc.ceil_div")
    assert "mini_pkg.text._needs_truncation" in tools["callers"].func(
        qualname="mini_pkg.text.display_width"
    )
    assert "mini_pkg.text._needs_truncation" in tools["callees"].func(
        qualname="mini_pkg.text.truncate"
    )
    assert "test_ceil_div_rounds_up" in tools["tests_for"].func(qualname="mini_pkg.calc.ceil_div")


def test_agent_show_commit_validates_sha(tmp_path: Path) -> None:
    tools = {t.name: t for t in graph_tools(_tool_ctx(tmp_path))}
    bugfix = _find_commit(FIXTURES / "mini_pkg", "Fix ceil_div")
    assert "Fix ceil_div" in tools["show_commit"].func(sha=bugfix)
    for bad in ("", "; rm -rf /", "zzzz"):
        with pytest.raises(ValueError):
            tools["show_commit"].func(sha=bad)


def test_agent_okf_still_stubbed(tmp_path: Path) -> None:
    tools = {t.name: t for t in graph_tools(_tool_ctx(tmp_path))}
    with pytest.raises(NotImplementedError):
        tools["okf"].func(path="x")


# --- container round-trip (real coverage run) ---------------------------------


@pytest.mark.docker
def test_knowledge_e2e_mini_pkg(tmp_path: Path, docker_available: None) -> None:
    from pipeline.hygiene.context import build_context
    from pipeline.hygiene.runner import run_hygiene
    from pipeline.knowledge.runner import run_knowledge

    src = tmp_path / "mini_pkg"
    shutil.copytree(FIXTURES / "mini_pkg", src)
    ctx = build_context(str(src), output_root=tmp_path / "out", llm_mode="replay")
    run_hygiene(ctx)
    run_knowledge(ctx)

    kdir = ctx.knowledge_dir
    tmap = json.loads((kdir / "test_map.json").read_text())
    assert tmap["tests/test_calc.py::test_ceil_div_rounds_up"] == ["mini_pkg.calc.ceil_div"]
    cov = json.loads((kdir / "coverage.json").read_text())
    assert cov["mini_pkg.calc.ceil_div"] == 100.0
    assert cov["mini_pkg.calc.RunningStats.count"] < 100.0

    graph = json.loads((kdir / "repo_graph.json").read_text())
    tested = {(e["source"], e["target"]) for e in graph["edges"] if e["type"] == "tested_by"}
    assert ("mini_pkg.calc.ceil_div", "tests/test_calc.py::test_ceil_div_rounds_up") in tested

    ver = json.loads((kdir / "graph_verification.json").read_text())
    assert ver["symbol_existence"]["precision"] == 1.0
    assert ver["mismatches"] == []
    assert ver["by_edge_type"]["tested_by"]["precision"] == 1.0

    first = (kdir / "repo_graph.json").read_bytes()
    forced = build_context(
        str(src),
        output_root=tmp_path / "out",
        llm_mode="replay",
        force=("symbol_index", "indexes", "graph", "verify"),
    )
    run_knowledge(forced)
    assert (kdir / "repo_graph.json").read_bytes() == first


# --- git helpers --------------------------------------------------------------


def _head(repo: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()


def _find_commit(repo: Path, message_prefix: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(repo), "log", "--format=%H %s"], capture_output=True, text=True
    ).stdout
    for line in out.splitlines():
        sha, _, msg = line.partition(" ")
        if msg.startswith(message_prefix):
            return sha
    raise AssertionError(f"commit not found: {message_prefix}")
