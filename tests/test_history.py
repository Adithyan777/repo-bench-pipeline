"""History-derived funnel + task builder.

Real fixture git history, AST diffs and Docker gates; classify/neutrality replay from
``tasks_fixture`` cassettes; agent paths use a scripted endpoint.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from pipeline.config import Config
from pipeline.ecosystems import source_ops
from pipeline.knowledge import indexes
from pipeline.llm.client import LLMClient
from pipeline.tasks import build_history as B
from pipeline.tasks import history as H
from pipeline.tasks.build_excision import BuildInputs
from tests import _smoke

FIXTURES = Path(__file__).resolve().parent / "fixtures"
MINI = FIXTURES / "mini_pkg"


def _cassettes(stage: str) -> bool:
    d = Path("tests/cassettes") / stage
    return d.is_dir() and any(d.glob("*.json"))


def _git(repo: Path, *args: str, env: dict | None = None) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True, env=env
    ).stdout.strip()


def _head(repo: Path = MINI) -> str:
    return _git(repo, "rev-parse", "HEAD")


def _fixture_funnel(cfg: Config | None = None):
    cfg = cfg or Config()
    history = indexes.build_history_index(MINI, _head(), cfg)
    passing = set(_smoke.MINI_PKG_TEST_MAP)
    return H.funnel(history, _smoke.MINI_PKG_TEST_MAP, passing, MINI, _head(), cfg), cfg


# --- source ops ---------------------------------------------------------------------------


def test_changed_test_functions_and_new_identifiers() -> None:
    old = "def test_a():\n    assert 1\n\nclass TestK:\n    def test_m(self):\n        assert 2\n"
    new = (
        "def test_a():\n    assert 1  # comment only\n\n"
        "def test_b():\n    assert 3\n\n"
        "class TestK:\n    def test_m(self):\n        assert 22\n"
    )
    assert source_ops.changed_test_functions(old, new) == ["TestK::test_m", "test_b"]
    assert source_ops.changed_test_functions(None, old) == ["TestK::test_m", "test_a"]
    assert source_ops.new_identifiers(
        "def f(a):\n    return a\n",
        "def f(a):\n    x = _h(a)\n    return x\n\ndef _h(a):\n    return a\n",
    ) == {"_h", "x"}
    contracts = source_ops.function_contracts(
        "class C:\n    def m(self, x=1):\n        'doc'\n\ndef _p():\n    pass\n", "pkg.mod"
    )
    assert [(c["qualname"], c["signature"], c["docstring"], c["is_public"]) for c in contracts] == [
        ("pkg.mod.C.m", "m(self, x=1)", "doc", True),
        ("pkg.mod._p", "_p()", None, False),
    ]


# --- funnel -------------------------------------------------------------------------------


def test_funnel_hard_filters_and_scores_on_fixture_history() -> None:
    cands, cfg = _fixture_funnel()
    by = {c.message[:20]: c for c in cands}
    reasons = {k: c.reject_reason for k, c in by.items()}
    assert reasons["Initial package: cal"] == "root-commit"
    assert reasons["docs: add README wit"] == "docs-or-ci-only"
    assert reasons["Use wcwidth for accu"] == "dependency-changing"
    assert reasons["Add standalone geome"] == "uncovered-and-no-tests"
    assert reasons["Rename geometry modu"] == "uncovered-and-no-tests"
    assert reasons["Test clamp with inve"] == "no-source-change"
    merge = by["Merge pull request #"]
    assert (
        by["Accept inverted boun"].status == "considered"
    )  # superseded only once the merge is kept
    bugfix = by["Fix ceil_div off-by-"]
    assert bugfix.status == "considered" and bugfix.source_lines_changed == 3
    assert bugfix.score == 5.0 and bugfix.score_breakdown == {
        "fix_keyword": 1.0,
        "adds_tests": 2.0,
        "public_fn": 1.0,
        "single_function": 1.0,
    }
    assert bugfix.covered_functions == ["mini_pkg.calc.ceil_div"]
    assert merge.status == "considered" and merge.is_merge and merge.pr_number == 7
    assert merge.input_sha == _git(MINI, "rev-parse", f"{merge.sha}^1")
    assert by["Refactor: extract _n"].score == 1.0  # public fn only: no keyword/tests/single
    order = H.ranked(cands)
    assert [c.message[:12] for c in order] == [
        "Merge pull r",
        "Fix ceil_div",
        "Add core.fir",
        "Add text mod",
        "Accept inver",
        "Refactor: ex",
    ]
    assert by["Add core.first helpe"].score == 4.0  # adds_tests + public_fn + single_function
    assert all(c.reject_reason for c in cands if c.status == "rejected")


def test_funnel_size_and_merge_knobs() -> None:
    cfg = Config()
    cfg.history.min_source_lines_changed = 4
    cands, _ = _fixture_funnel(cfg)
    by = {c.message[:20]: c for c in cands}
    assert by["Fix ceil_div off-by-"].reject_reason == "too-small(3<4)"
    # supersede applies only to constituents of a KEPT merge
    merge, accept = by["Merge pull request #"], by["Accept inverted boun"]
    merge.status = accept.status = "kept"
    assert H.supersede_constituents(cands, [merge, accept], MINI) == [merge]
    assert accept.reject_reason == f"superseded-by-merge({merge.short})"
    cands2, _ = _fixture_funnel(cfg)
    by2 = {c.message[:20]: c for c in cands2}
    by2["Accept inverted boun"].status = "kept"  # merge classified out -> constituent stands
    assert H.supersede_constituents(cands2, [by2["Accept inverted boun"]], MINI) == [
        by2["Accept inverted boun"]
    ]
    cfg2 = Config()
    cfg2.history.max_source_files_changed = 1
    cands2, _ = _fixture_funnel(cfg2)
    by2 = {c.message[:20]: c for c in cands2}
    assert by2["Add text module with"].reject_reason == "too-many-files(2>1)"


def _mk_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "r"
    repo.mkdir()
    env = {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@x",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@x",
        "PATH": "/usr/bin:/bin:/usr/local/bin",
    }
    _git(repo, "init", "-q", "-b", "main", env=env)
    (repo / "m.py").write_text("def f():\n    return 1\n")
    (repo / "test_m.py").write_text("from m import f\n\ndef test_f():\n    assert f() == 1\n")
    _git(repo, "add", "-A", env=env)
    _git(repo, "commit", "-q", "-m", "base", env=env)
    return repo


def _commit(repo: Path, msg: str, files: dict[str, str]) -> str:
    env = {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@x",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@x",
        "PATH": "/usr/bin:/bin:/usr/local/bin",
    }
    for rel, text in files.items():
        (repo / rel).write_text(text)
    _git(repo, "add", "-A", env=env)
    _git(repo, "commit", "-q", "-m", msg, env=env)
    return _head(repo)


def test_reverted_commits_detected_by_message_and_reverse_patch(tmp_path: Path) -> None:
    repo = _mk_repo(tmp_path)
    change = _commit(
        repo, "fix f", {"m.py": "def f():\n    return 2\n\n\ndef g():\n    return 0\n"}
    )
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@x", "revert", "--no-edit", change)
    revert = _head(repo)
    assert "This reverts commit" in _git(repo, "show", "-s", "--format=%B", revert)
    change2 = _commit(
        repo, "fix f again", {"m.py": "def f():\n    return 3\n\n\ndef g():\n    return 0\n"}
    )
    # hand-made undo without a revert message: caught by the reverse patch-id
    undo = _commit(repo, "oops", {"m.py": "def f():\n    return 1\n"})
    cfg = Config()
    cfg.history.require_coverage_or_added_tests = False
    history = indexes.build_history_index(repo, _head(repo), cfg)
    cands = H.funnel(history, {}, None, repo, _head(repo), cfg)
    by = {c.sha: c for c in cands}
    assert by[change].reject_reason == f"reverted-by({revert[:7]})"
    assert by[change2].reject_reason == f"reverted-by({undo[:7]})"
    assert by[undo].status == "considered" and by[revert].status == "considered"
    cfg.history.reject_reverted = False
    cands = H.funnel(history, {}, None, repo, _head(repo), cfg)
    by = {c.sha: c for c in cands}
    assert by[change].status == "considered" and by[change].score_breakdown["reverted"] == -3.0


class _FakeClassify:
    def __init__(self, kinds: dict[str, str]):
        self.calls, self.kinds = 0, kinds

    def complete_json(self, step, messages, schema):
        self.calls += 1
        out = []
        for block in messages[0]["content"].split("### ")[1:]:
            sha = block.splitlines()[0].strip()
            out.append(
                {
                    "sha": sha,
                    "kind": {"unverifiable": "feature"}.get(
                        self.kinds.get(sha, "bugfix"), self.kinds.get(sha, "bugfix")
                    ),
                    "self_contained": True,
                    "verifiable_via_tests": self.kinds.get(sha) != "unverifiable",
                    "behavior_change_summary": "s",
                    "difficulty_guess": "easy",
                }
            )
        return {"classifications": out}


def test_classify_backfills_persists_and_shortlists() -> None:
    cands, cfg = _fixture_funnel()
    order = H.ranked(cands)
    refactor = next(c for c in order if c.message.startswith("Refactor")).short
    text = next(c for c in order if c.message.startswith("Add text")).short
    cfg.llm.classify_batch_size = 2
    cfg.history.shortlist_size = 2
    llm = _FakeClassify({refactor: "refactor", text: "unverifiable"})
    decisions: dict = {}
    kept = H.classify(order, MINI, llm, cfg, decisions)
    assert [c.message[:12] for c in kept] == ["Merge pull r", "Fix ceil_div"]
    assert llm.calls == 1 and len(decisions) == 2  # first batch already fills the shortlist
    statuses = {c.message[:12]: (c.status, c.reject_reason) for c in order}
    assert statuses["Add text mod"] == ("surplus", "not-classified")
    cfg.history.shortlist_size = 5
    kept = H.classify(H.ranked(_fixture_funnel(cfg)[0]), MINI, llm, cfg, decisions)
    assert llm.calls == 3 and len(decisions) == 6  # only the later batches were new
    assert [c.message[:12] for c in kept] == [
        "Merge pull r",
        "Fix ceil_div",
        "Add core.fir",
        "Accept inver",
    ]
    kept = H.supersede_constituents(_fixture_funnel(cfg)[0], kept, MINI)
    assert [c.message[:12] for c in kept] == ["Merge pull r", "Fix ceil_div", "Add core.fir"]
    by = {c.message[:12]: c for c in H.ranked(_fixture_funnel(cfg)[0])}
    H.classify(list(by.values()), MINI, _FakeClassify({}), cfg, dict(decisions))
    assert by["Refactor: ex"].reject_reason == "kind:refactor"
    assert by["Add text mod"].reject_reason == "not-verifiable-via-tests"
    cfg.history.shortlist_size = 2
    short = H.shortlist(kept, cfg)
    assert [c.message[:12] for c in short] == ["Merge pull r", "Fix ceil_div"]
    assert all(c.status == "shortlisted" for c in short)
    third = next(c for c in kept if c not in short)
    assert (third.status, third.reject_reason) == ("surplus", "kept-not-shortlisted")
    cfg.history.shortlist_size = 5
    # zero calls on a rerun with the persisted decisions
    again = _FakeClassify({})
    H.classify(H.ranked(_fixture_funnel(cfg)[0]), MINI, again, cfg, dict(decisions))
    assert again.calls == 0


@pytest.mark.skipif(not _cassettes(_smoke.TASKS_STAGE), reason="tasks_fixture cassette missing")
def test_classify_replay_rejects_refactor_keeps_bugfix(tmp_path: Path) -> None:
    client = LLMClient(stage=_smoke.TASKS_STAGE, mode="replay", transcripts_dir=tmp_path / "t")
    cands, cfg = _fixture_funnel(_smoke.mini_pkg_excision_config())
    kept = H.classify(H.ranked(cands), MINI, client, cfg, {})
    by = {c.message[:12]: c for c in cands}
    assert by["Refactor: ex"].reject_reason == "kind:refactor"
    assert by["Fix ceil_div"].kind == "bugfix" and by["Fix ceil_div"] in kept
    assert "ceil_div" in by["Fix ceil_div"].classify["behavior_change_summary"]
    assert by["Merge pull r"] in kept and by["Add text mod"] in kept
    assert by["Add core.fir"].kind == "feature" and by["Add core.fir"] in kept


def test_static_gate_getattr_convention(tmp_path: Path) -> None:
    from pipeline.tasks.harness import static_gate_violations

    inp = tmp_path / "input"
    (inp / "pkg").mkdir(parents=True)
    (inp / "pkg/__init__.py").write_text("")
    (inp / "pkg/core.py").write_text("def old():\n    return 1\n\n\ndef _h():\n    pass\n")
    ver = tmp_path / "verifier" / "tests"
    ver.mkdir(parents=True)
    (ver / "test_new.py").write_text(
        "from pkg import core\nimport pkg.core\n\n"
        "def test_new():\n    fn = getattr(core, 'new_api', None)\n    assert fn is not None\n"
        "    assert hasattr(obj := object(), '__class__') and getattr(pkg, '__doc__') is None\n"
        "    assert getattr(core, '_h', None) is None\n"
    )
    v = static_gate_violations(inp, tmp_path / "verifier")
    assert [(x["import"], x["reason"]) for x in v] == [("getattr:_h", "private-symbol")]


def test_shortlist_prefers_module_diversity_and_bugfix_ties() -> None:
    cfg = Config()
    cfg.history.shortlist_size = 2

    def mk(sha, score, modules, kind):
        c = H.HistoryCandidate(sha, ["p"], "m", False, None, "p", [], [], [], [])
        c.score, c.modules, c.kind, c.status = score, modules, kind, "kept"
        return c

    a = mk("a" * 40, 3.0, ["pkg.x"], "feature")
    b = mk("b" * 40, 3.0, ["pkg.x"], "bugfix")
    c = mk("c" * 40, 2.6, ["pkg.y"], "bugfix")
    short = H.shortlist([a, b, c], cfg)
    assert [s.sha[0] for s in short] == ["b", "c"]  # bugfix wins the tie; y gets +0.5
    assert a.status == "surplus"


# --- build (no docker) --------------------------------------------------------------------


def _bugfix_candidate(cfg: Config | None = None) -> tuple[H.HistoryCandidate, Config]:
    cands, cfg = _fixture_funnel(cfg)
    c = next(c for c in cands if c.message.startswith("Fix ceil_div"))
    c.classify = {"kind": "bugfix", "behavior_change_summary": "ceil_div rounds exact multiples"}
    return c, cfg


def test_commit_test_nodeids_by_ast_diff() -> None:
    c, _ = _bugfix_candidate()
    assert B.commit_test_nodeids(c, MINI) == {
        "tests/test_calc.py": ["tests/test_calc.py::test_ceil_div_exact_multiple"]
    }
    cands, _ = _fixture_funnel()
    merge = next(c for c in cands if c.is_merge)
    assert B.commit_test_nodeids(merge, MINI) == {
        "tests/test_calc.py": ["tests/test_calc.py::test_clamp_inverted_bounds"]
    }


def test_archive_and_additive_overlay_reproduce_the_historical_diff(tmp_path: Path) -> None:
    c, cfg = _bugfix_candidate()
    fake_repo = tmp_path / "repo"
    shutil.copytree(MINI, fake_repo)
    (fake_repo / "Dockerfile").write_text("FROM x\n")
    (fake_repo / "requirements.lock.txt").write_text("wcwidth==0.2.13\n")
    (fake_repo / "setup.py").write_text("# HEAD version, must not overwrite history\n")
    inp, sol = tmp_path / "input", tmp_path / "solution"
    B.archive_tree(fake_repo, c.input_sha, inp)
    B.archive_tree(fake_repo, c.sha, sol)
    names = B.overlay_files(fake_repo, cfg)
    assert names == ["Dockerfile", "requirements.lock.txt"]
    assert B.overlay(fake_repo, inp, names + ["setup.py"]) == [
        "Dockerfile",
        "requirements.lock.txt",
    ]
    assert B.overlay(fake_repo, sol, names + ["setup.py"]) == [
        "Dockerfile",
        "requirements.lock.txt",
    ]
    assert (inp / "setup.py").read_text() == H.show(MINI, c.input_sha, "setup.py")
    assert not (inp / ".git").exists() and (inp / "Dockerfile").read_text() == "FROM x\n"
    changed = H.git(MINI, "diff", "--name-only", c.input_sha, c.sha).split()
    assert changed == ["mini_pkg/calc.py", "tests/test_calc.py"]
    for rel in changed:
        assert (inp / rel).read_text() == H.show(MINI, c.input_sha, rel)
        assert (sol / rel).read_text() == H.show(MINI, c.sha, rel)
    differing = sorted(
        str(p.relative_to(inp))
        for p in inp.rglob("*")
        if p.is_file() and (sol / p.relative_to(inp)).read_bytes() != p.read_bytes()
    )
    only_in_sol = sorted(
        str(p.relative_to(sol))
        for p in sol.rglob("*")
        if p.is_file() and not (inp / p.relative_to(sol)).exists()
    )
    assert differing == changed and only_in_sol == []  # overlay files identical on both sides
    # no lint touched the historical tree: byte-identical to git
    assert (inp / "mini_pkg/calc.py").read_bytes() == H.show(
        MINI, c.input_sha, "mini_pkg/calc.py"
    ).encode()


def test_test_dir_affinity_and_contracts(tmp_path: Path) -> None:
    root = tmp_path / "s"
    for rel in ("pkg/tests/test_a.py", "pkg/sub/tests/test_b.py", "tests/test_top.py"):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text("def test_x():\n    pass\n")
    cfg = Config()
    assert B._test_dir_for(root, ["pkg/sub/mod.py"], cfg) == Path("pkg/sub/tests")
    assert B._test_dir_for(root, ["pkg/core.py"], cfg) == Path("pkg/tests")
    assert B._test_dir_for(tmp_path / "empty", ["x.py"], cfg) == Path("tests")
    (root / "pkg/core.py").write_text("def f(a):\n    'Doc.'\n    return a\n")
    text = B._contracts(root, ["pkg/core.py"], ["pkg.core.f"], cfg)
    assert text == "- pkg.core.f: `f(a)`\n  Doc."


# --- build (docker) -----------------------------------------------------------------------


def _inputs(ctx, llm=None, decisions=None, cache_dir: Path | None = None) -> BuildInputs:
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
        llm=llm,
        cache_dir=cache_dir,
        decisions=decisions,
    )


def _ctx_candidate(ctx, prefix: str) -> H.HistoryCandidate:
    from pipeline.knowledge.runner import knowledge_paths

    kp = knowledge_paths(ctx.run_dir, ctx.config)
    history = json.loads(Path(kp["history_index"]).read_text())
    test_map = json.loads(Path(kp["test_map"]).read_text())
    base = ctx.report["base_sha"]
    cands = H.funnel(history, test_map, None, ctx.repo, base, ctx.config)
    c = next(c for c in cands if c.message.startswith(prefix))
    c.classify = {"kind": "bugfix", "behavior_change_summary": "ceil_div rounds exact multiples"}
    return c


class _ScriptedAgent:
    """Scripted OpenAI-style endpoint: a write_file tool call, then a final message."""

    def __init__(self, completions):
        self._it = iter(completions)
        self.calls = 0

    def chat(self, step, messages, tools=None, tool_choice=None, max_tokens=None):
        self.calls += 1
        return next(self._it)

    def complete_json(self, step, messages, schema):
        return {"neutral": True, "issues": [], "flagged_tests": []}


@pytest.mark.docker
def test_build_agent_authored_verifier_drops_non_discriminating_tests_and_caches(
    mini_env, tmp_path
):
    from tests.test_llm import make_completion

    ctx = mini_env
    c = _ctx_candidate(ctx, "Fix ceil_div")
    c.test_files = []  # pretend the commit shipped no tests -> agent path
    rel = f"tests/test_hist_{c.short}.py"
    body = (
        "from mini_pkg.calc import ceil_div\n\n"
        "def test_exact():\n    assert ceil_div(4, 2) == 2\n\n"
        "def test_unchanged():\n    assert ceil_div(5, 2) == 3\n"
    )
    scripted = _ScriptedAgent(
        [
            make_completion(
                tool_calls=[("write_file", json.dumps({"path": rel, "content": body}))]
            ),
            make_completion(content="done"),
        ]
    )
    inp = _inputs(ctx, llm=scripted, cache_dir=tmp_path / "cache")
    result = B.build_history_task(c, inp, tmp_path / "tasks", ctx.config)
    assert result.task_dir and result.notes["verifier_source"] == "agent-authored"
    task = json.loads((result.task_dir / "task.json").read_text())
    assert task["verifier_tests"] == [f"{rel}::test_exact"]
    assert task["dropped_tests"]["passing_on_input"] == [f"{rel}::test_unchanged"]
    assert task["verifier_agent"]["outcome"] == "added" and scripted.calls == 2
    assert task["provenance"]["verifier_source"] == "agent-authored"
    assert (result.task_dir / "verifier" / rel).read_text() == body
    audit = [
        json.loads(x) for x in (ctx.audit_dir / "agent_actions.jsonl").read_text().splitlines()
    ]
    assert any(
        a["stage"] == "p3.build.verifier_agent" and a["task"] == result.task_id for a in audit
    )
    # rerun: the cached file is reused, the endpoint is never called
    inp2 = _inputs(ctx, llm=_ScriptedAgent([]), cache_dir=tmp_path / "cache")
    again = B.build_history_task(c, inp2, tmp_path / "tasks2", ctx.config)
    assert again.task_dir and again.notes["verifier_agent"]["outcome"] == "reused"
    assert json.loads((again.task_dir / "task.json").read_text())["verifier_tests"] == [
        f"{rel}::test_exact"
    ]


@pytest.mark.docker
def test_build_rejects_when_agent_tests_pass_on_input(mini_env, tmp_path) -> None:
    from tests.test_llm import make_completion

    ctx = mini_env
    c = _ctx_candidate(ctx, "Fix ceil_div")
    c.test_files = []
    rel = f"tests/test_hist_{c.short}.py"
    body = (
        "from mini_pkg.calc import ceil_div\n\ndef test_same():\n    assert ceil_div(5, 2) == 3\n"
    )
    scripted = _ScriptedAgent(
        [
            make_completion(
                tool_calls=[("write_file", json.dumps({"path": rel, "content": body}))]
            ),
            make_completion(content="done"),
        ]
    )
    result = B.build_history_task(c, _inputs(ctx, llm=scripted), tmp_path / "tasks", ctx.config)
    assert result.task_dir is None and result.reject_reason == "agent-authored-pass-on-input"
    assert not (tmp_path / "tasks" / "mini_pkg" / result.task_id).exists()


@pytest.mark.docker
def test_build_env_drift_when_solution_cannot_collect(mini_env, tmp_path) -> None:
    """A synthetic history whose test file needs a module the image lacks: the solution
    tree cannot collect in the current image -> env-drift (not a property of the change)."""
    ctx = mini_env
    repo = _mk_repo(tmp_path)
    (repo / "conftest.py").write_text("")
    _commit(
        repo,
        "base with drifting test",
        {
            "conftest.py": "",
            "test_m.py": "import yaml\nfrom m import f\n\ndef test_f():\n    assert f() == 1\n",
        },
    )
    sha = _commit(
        repo,
        "fix f",
        {
            "m.py": "def f():\n    x = 1\n    return x + 1\n",
            "test_m.py": "import yaml\nfrom m import f\n\ndef test_f():\n    assert f() == 2\n",
        },
    )
    cfg = Config()
    cfg.history.require_coverage_or_added_tests = False
    history = indexes.build_history_index(repo, sha, cfg)
    cands = H.funnel(history, {}, None, repo, sha, cfg)
    c = next(c for c in cands if c.sha == sha)
    assert c.status == "considered"
    inp = _inputs(ctx)
    inp.repo = repo
    inp.repo_name = "synthetic"
    result = B.build_history_task(c, inp, tmp_path / "tasks", cfg)
    assert result.task_dir is None
    assert (
        result.reject_reason.startswith("env-drift(")
        and "ModuleNotFoundError" in result.reject_reason
    )


@pytest.mark.docker
def test_build_rejects_non_neutral_verifier_when_rewrite_disabled(mini_env, tmp_path) -> None:
    class _Flagging:
        def complete_json(self, step, messages, schema):
            assert step == "p3.build.neutrality_check_rewrite"
            return {
                "neutral": False,
                "issues": ["mirrors the patch"],
                "flagged_tests": ["tests/test_calc.py::test_ceil_div_exact_multiple"],
            }

    ctx = mini_env
    cfg = ctx.config
    c = _ctx_candidate(ctx, "Fix ceil_div")
    saved = cfg.history.neutrality_rewrite_max_attempts
    cfg.history.neutrality_rewrite_max_attempts = 0
    try:
        decisions: dict = {}
        result = B.build_history_task(
            c, _inputs(ctx, llm=_Flagging(), decisions=decisions), tmp_path / "tasks", cfg
        )
    finally:
        cfg.history.neutrality_rewrite_max_attempts = saved
    assert result.task_dir is None
    assert result.reject_reason == "verifier-not-implementation-neutral(rewrite:disabled)"
    assert len(decisions) == 1 and next(iter(decisions.values()))["neutral"] is False
    assert result.notes["neutrality"]["decision"]["flagged_tests"]


CONVENTION_TEST_CORE = """import pytest

from mini_pkg import core
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


def test_first_match_and_default():
    first = getattr(core, "first", None)
    assert first is not None
    assert first([1, 4, 6], lambda x: x % 2 == 0) == 4
    assert first([1, 3], lambda x: x % 2 == 0, default=-1) == -1
"""


@pytest.mark.docker
def test_build_new_symbol_feature_via_getattr_convention(mini_env, tmp_path) -> None:
    """A feature commit whose test imports the new symbol at module level: the missing
    import is routed to the rewrite agent (scripted here), the rewritten test fails on
    input/ with AssertionError and the task validates."""
    from pipeline.tasks.harness import validate_task
    from tests.test_llm import make_completion

    ctx = mini_env
    c = _ctx_candidate(ctx, "Add core.first")
    c.classify = {
        "kind": "feature",
        "behavior_change_summary": "core.first returns the first match",
    }
    cfg = ctx.config
    saved = cfg.history.max_neutrality_rewrites_per_repo
    cfg.history.max_neutrality_rewrites_per_repo = 2
    try:
        scripted = _ScriptedAgent(
            [
                make_completion(
                    tool_calls=[
                        (
                            "write_file",
                            json.dumps(
                                {"path": "tests/test_core.py", "content": CONVENTION_TEST_CORE}
                            ),
                        )
                    ]
                ),
                make_completion(content="done"),
            ]
        )
        inp = _inputs(ctx, llm=scripted, decisions={}, cache_dir=tmp_path / "cache")
        result = B.build_history_task(c, inp, tmp_path / "tasks", cfg)
        assert result.task_dir, result.reject_reason
        task = json.loads((result.task_dir / "task.json").read_text())
        assert task["new_symbol_rewrite"]["outcome"] == "rewritten" and scripted.calls == 2
        assert task["verifier_tests"] == ["tests/test_core.py::test_first_match_and_default"]
        assert inp.counters["rewrites"] == 1
        verdict = validate_task(result.task_dir, cfg)
        assert verdict["valid"], verdict["reasons"]
        reasons = verdict["checks"]["right_reason"]["tests"]
        assert [r["reason"] for r in reasons.values()] == ["AssertionError"]
        # budget exhausted -> plain reject with the recorded outcome
        inp2 = _inputs(ctx, llm=_ScriptedAgent([]), decisions={}, cache_dir=tmp_path / "cache2")
        inp2.counters["rewrites"] = 2
        again = B.build_history_task(c, inp2, tmp_path / "tasks2", cfg)
        assert again.task_dir is None
        assert again.reject_reason == (
            "verifier-imports-symbol-missing-in-input(mini_pkg.core.first; "
            "rewrite:budget-exhausted)"
        )
    finally:
        cfg.history.max_neutrality_rewrites_per_repo = saved


@pytest.mark.docker
def test_build_commit_tests_task_and_static_gate_reject(mini_env, tmp_path) -> None:
    ctx = mini_env
    c = _ctx_candidate(ctx, "Fix ceil_div")
    result = B.build_history_task(c, _inputs(ctx), tmp_path / "tasks", ctx.config)
    assert result.task_dir and result.notes["verifier_source"] == "commit-tests"
    task = json.loads((result.task_dir / "task.json").read_text())
    assert task["neutrality"]["checked"] is False  # no LLM given: recorded, not faked
    assert task["verifier_on_input"] == {"exit_code": 1, "n_failing": 1, "n_passing": 0}
    assert task["verifier_on_solution"] == {"exit_code": 0, "n_failing": 0, "n_passing": 1}
    run_sh = (result.task_dir / "verifier/run.sh").read_text()
    assert run_sh.endswith(task["verifier_cmd"] + "\n") and 'cd "$(dirname "$0")"' in run_sh
    # a verifier importing a solution-only symbol is stopped by the static gate at build
    text = _ctx_candidate(ctx, "Add text module")
    result2 = B.build_history_task(text, _inputs(ctx), tmp_path / "tasks", ctx.config)
    assert result2.task_dir is None
    assert result2.reject_reason == "verifier-on-input:ModuleNotFoundError"
