"""Hygiene (P1 core) tests: detection, pin/lock (real uv), docker, baseline.

Real uv/docker/git; LLM only via replayed cassettes. Multi-build tests are `slow`.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline.config import Config
from pipeline.ecosystems.python import PythonAdapter, _constraints_from_lock
from pipeline.hygiene import baseline, compose, detect
from pipeline.hygiene.context import HygieneContext
from pipeline.llm.client import LLMClient
from pipeline.state import State

FIXTURES = Path(__file__).resolve().parent / "fixtures"


# --- helpers ------------------------------------------------------------------


def make_repo(tmp_path: Path, files: dict[str, str]) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    for rel, content in files.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    return repo


def make_ctx(tmp_path: Path, files: dict[str, str], mode: str = "replay") -> HygieneContext:
    run_dir = tmp_path / "run"
    (run_dir / "repo").mkdir(parents=True)
    for rel, content in files.items():
        path = run_dir / "repo" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    config = Config()
    state = State.load(run_dir)
    llm = LLMClient(stage="test", mode=mode, transcripts_dir=tmp_path / "t")
    adapter = PythonAdapter(config=config, work_dir=run_dir / "repo", llm=llm)
    return HygieneContext("x", run_dir, config, state, llm, adapter, repo_identity="id")


def _cassettes(stage: str) -> bool:
    d = Path("tests/cassettes") / stage
    return d.is_dir() and any(d.glob("*.json"))


def git_ctx(tmp_path: Path, files: dict[str, str]) -> HygieneContext:
    """A HygieneContext whose repo is a real git repo with `files` committed."""
    import subprocess

    ctx = make_ctx(tmp_path, files)
    repo = ctx.repo
    env = {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }
    import os

    full = {**os.environ, **env}
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "init"], check=True, env=full)
    return ctx


PYPROJECT = """\
[project]
name = "demo"
version = "0.1.0"
requires-python = ">=3.9"
dependencies = ["wcwidth>=0.2.0"]
[project.optional-dependencies]
test = ["pytest"]
"""

POETRY = """\
[tool.poetry]
name = "demo"
version = "0.1.0"
[tool.poetry.dependencies]
python = "^3.9"
requests = "^2.28"
"""

SETUP_CFG = """\
[metadata]
name = demo
version = 0.1.0

[options]
python_requires = >=3.9
install_requires =
    wcwidth>=0.2.0

[options.extras_require]
test =
    pytest
"""


# --- detection ----------------------------------------------------------------


def test_detect_pyproject_project(tmp_path: Path) -> None:
    a = PythonAdapter(work_dir=tmp_path)
    repo = make_repo(tmp_path, {"pyproject.toml": PYPROJECT, "demo.py": "x = 1\n"})
    info = a.packaging(repo)
    assert info.style == "pyproject"
    assert info.installable and info.available_extras == ["test"]


def test_detect_requirements_only(tmp_path: Path) -> None:
    a = PythonAdapter(work_dir=tmp_path)
    repo = make_repo(tmp_path, {"requirements.txt": "requests\n", "app.py": "import requests\n"})
    info = a.packaging(repo)
    assert info.style == "requirements" and info.manifest == "requirements.txt"
    assert info.installable is False


def test_detect_poetry(tmp_path: Path) -> None:
    a = PythonAdapter(work_dir=tmp_path)
    repo = make_repo(tmp_path, {"pyproject.toml": POETRY, "demo.py": "x = 1\n"})
    info = a.packaging(repo)
    assert info.style == "poetry" and info.uv_readable is False


def test_detect_setup_py() -> None:
    a = PythonAdapter(work_dir=FIXTURES)
    info = a.packaging(FIXTURES / "mini_pkg")
    assert info.style == "setup.py" and info.installable


def test_detect_no_manifest() -> None:
    a = PythonAdapter(work_dir=FIXTURES)
    info = a.packaging(FIXTURES / "mini_pkg_notests")
    assert info.style == "none" and info.installable is False


def test_detect_setup_cfg_only(tmp_path: Path) -> None:
    a = PythonAdapter(work_dir=tmp_path)
    repo = make_repo(tmp_path, {"setup.cfg": SETUP_CFG, "demo.py": "x = 1\n"})
    info = a.packaging(repo)
    assert info.style == "setup.cfg"
    assert info.uv_readable is False  # uv can't read setup.cfg alone
    assert info.installable and info.available_extras == ["test"]
    assert info.requires_python == ">=3.9"


def test_pin_setup_cfg_only(tmp_path: Path) -> None:
    work = make_repo(tmp_path, {"setup.cfg": SETUP_CFG, "demo.py": "x = 1\n"})
    a = PythonAdapter(work_dir=work)
    a.synthesize_requirements(work)
    lock = a.lock(work)
    text = lock.read_text()
    pins = {ln.split("==")[0] for ln in text.splitlines() if "==" in ln and not ln[0].isspace()}
    assert {"wcwidth", "pytest"} <= pins  # install_requires + [test] extra
    assert "--hash=sha256" in text
    assert (work / "setup.py").is_file()  # shim written for editable install


def test_non_python_repo_exits(tmp_path: Path) -> None:
    ctx = make_ctx(tmp_path, {"README.md": "# not python\n", "main.go": "package main\n"})
    with pytest.raises(SystemExit):
        detect.run(ctx)


@pytest.mark.parametrize(
    ("requires", "expected"),
    [(">=3.9", "3.12"), ("<3.11", "3.10"), ("==3.9.*", "3.9"), (">=3.7,<3.10", "3.9")],
)
def test_python_version_from_requires(tmp_path: Path, requires: str, expected: str) -> None:
    a = PythonAdapter(work_dir=tmp_path)
    repo = make_repo(tmp_path, {"setup.py": f"setup(python_requires='{requires}')\n"})
    assert a.python_version(repo) == expected


def test_python_version_default(tmp_path: Path) -> None:
    a = PythonAdapter(work_dir=tmp_path)
    repo = make_repo(tmp_path, {"app.py": "x = 1\n"})
    assert a.python_version(repo) == "3.12"


# --- pin / lock (real uv) -----------------------------------------------------


def test_synthesize_and_lock_has_hashes(tmp_path: Path) -> None:
    src = FIXTURES / "mini_pkg"
    work = tmp_path / "w"
    import shutil

    shutil.copytree(src, work)
    a = PythonAdapter(work_dir=work)
    a.synthesize_requirements(work)
    lock = a.lock(work)
    text = lock.read_text()
    assert "--hash=sha256" in text
    pins = {ln.split("==")[0] for ln in text.splitlines() if "==" in ln and not ln[0].isspace()}
    assert {"wcwidth", "pytest", "coverage", "ruff"} <= pins  # runtime + tools


def test_lock_includes_test_extra(tmp_path: Path) -> None:
    work = make_repo(tmp_path, {"pyproject.toml": PYPROJECT})
    a = PythonAdapter(work_dir=work)
    a.synthesize_requirements(work)
    lock = a.lock(work)
    assert "pytest==" in lock.read_text()  # from the [test] extra


def test_lock_drops_unresolvable_extra(tmp_path: Path) -> None:
    pyproject = (
        '[project]\nname = "demo"\nversion = "0.1.0"\nrequires-python = ">=3.9"\n'
        'dependencies = ["wcwidth>=0.2.0"]\n'
        "[project.optional-dependencies]\n"
        'test = ["this-package-does-not-exist-xyz-9876>=999"]\n'
    )
    work = make_repo(tmp_path, {"pyproject.toml": pyproject})
    a = PythonAdapter(work_dir=work)
    a.synthesize_requirements(work)
    lock = a.lock(work)  # extra 'test' is unresolvable -> dropped, retried without it
    assert a.dropped_extras == ["test"]
    assert "wcwidth==" in lock.read_text()


def test_constraints_strips_hashes() -> None:
    lock = "wcwidth==0.2.0 \\\n    --hash=sha256:abc\n    # via foo\npytest==8.0.0\n"
    out = _constraints_from_lock(lock)
    assert "wcwidth==0.2.0" in out and "--hash" not in out


def test_poetry_translation(tmp_path: Path) -> None:
    work = make_repo(tmp_path, {"pyproject.toml": POETRY})
    a = PythonAdapter(work_dir=work)
    deps = a._translate_poetry(work)
    assert deps == ["requests>=2.28,<3.0.0"]


def test_infer_third_party_imports() -> None:
    a = PythonAdapter(work_dir=FIXTURES)
    imports = a.infer_third_party_imports(FIXTURES / "mini_pkg_notests")
    assert {"wcwidth", "yaml"} <= imports


# --- compose detection --------------------------------------------------------


def test_compose_detects_postgres(tmp_path: Path) -> None:
    ctx = make_ctx(
        tmp_path,
        {
            "app.py": "import psycopg2\n",
            ".env.example": "DATABASE_URL=postgres://localhost/db\n",
        },
    )
    result = compose.run(ctx)
    assert "postgres" in result["services_detected"]
    assert result["supported_emitted"] == ["postgres"]
    assert (ctx.repo / "docker-compose.yml").is_file()


def test_compose_no_services(tmp_path: Path) -> None:
    ctx = make_ctx(tmp_path, {"app.py": "import os\n"})
    result = compose.run(ctx)
    assert result["services_detected"] == []
    assert not (ctx.repo / "docker-compose.yml").exists()


# --- test report parsing ------------------------------------------------------


def test_parse_test_report(tmp_path: Path) -> None:
    report = {
        "tests": [
            {"nodeid": "t::a", "outcome": "passed"},
            {
                "nodeid": "t::b",
                "outcome": "failed",
                "call": {"outcome": "failed", "longrepr": "assert 1 == 2"},
            },
        ]
    }
    path = tmp_path / "r.json"
    path.write_text(json.dumps(report))
    parsed = PythonAdapter(work_dir=tmp_path).parse_test_report(path)
    assert parsed["t::a"]["status"] == "pass"
    assert parsed["t::b"]["status"] == "fail" and "assert" in parsed["t::b"]["reason"]


def test_no_tests_bootstrap(tmp_path: Path) -> None:
    a = PythonAdapter(work_dir=tmp_path)
    repo = make_repo(tmp_path, {"pkg.py": "x = 1\n"})
    assert a.test_framework(repo) == "none"
    a.test_framework_bootstrap(repo)
    assert (repo / "tests" / "conftest.py").is_file()


# --- LLM paths via cassette ---------------------------------------------------


@pytest.mark.skipif(not _cassettes("s2_pin"), reason="s2_pin cassette not recorded")
def test_alias_fallback_replay(tmp_path: Path) -> None:
    from tests import _smoke

    client = LLMClient(stage="s2_pin", mode="replay", transcripts_dir=tmp_path / "t")
    assert _smoke.run_alias_map(client) == {"serial": "pyserial"}


@pytest.mark.skipif(not _cassettes("s2_reask"), reason="s2_reask cassette not recorded")
def test_alias_reask_then_drop(tmp_path: Path) -> None:
    from tests import _smoke

    work = tmp_path / "repo"
    work.mkdir()
    client = LLMClient(stage=_smoke.REASK_STAGE, mode="replay", transcripts_dir=tmp_path / "t")
    a = PythonAdapter(work_dir=work, llm=client)
    # simulate the no-manifest infer step having mapped an invented import
    (work / a.config.pin.requirements_in_filename).write_text(f"{_smoke.REASK_IMPORT}\nwcwidth\n")
    a._inferred_map = {_smoke.REASK_IMPORT: _smoke.REASK_IMPORT}

    lock = a.lock(work)  # invented pkg fails -> re-ask (still bad) -> dropped
    text = lock.read_text()
    assert a.unresolved_imports == [_smoke.REASK_IMPORT]
    assert _smoke.REASK_IMPORT not in text
    assert "wcwidth==" in text  # the resolvable dep still locked


@pytest.mark.skipif(not _cassettes("s2_baseline"), reason="s2_baseline cassette not recorded")
def test_classify_replay(tmp_path: Path) -> None:
    from tests import _smoke

    client = LLMClient(stage="s2_baseline", mode="replay", transcripts_dir=tmp_path / "t")
    result = _smoke.run_classify(client)
    cats = {c["test_id"]: c["category"] for c in result["classifications"]}
    assert set(cats.values()) <= {"env", "genuine"}


# --- review-fix regressions (F1–F8) -------------------------------------------


def test_sanitize_name() -> None:
    from pipeline.cli import sanitize_name

    assert sanitize_name("Foo_Bar") == "foo_bar"  # underscore is a valid tag char
    assert sanitize_name("My.Repo") == "my.repo"
    assert sanitize_name("weird!!name??") == "weird-name"
    with pytest.raises(SystemExit):
        sanitize_name("!!!")


def test_valid_requirement() -> None:
    from pipeline.ecosystems.python import valid_requirement

    assert valid_requirement("pyserial")
    assert valid_requirement("requests>=2.0")
    assert not valid_requirement("not a package!")
    assert not valid_requirement("")
    assert not valid_requirement("-bad")


def test_infer_drops_invalid_mapping(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, {"app.py": "import weirdpkg\n"})
    a = PythonAdapter(work_dir=tmp_path / "out")
    (tmp_path / "out").mkdir()
    a._llm_map_imports = lambda imports, error=None: {"weirdpkg": "not valid!!"}  # endpoint stub
    deps = a._infer_no_manifest_deps(repo)
    assert "not valid!!" not in deps
    assert "weirdpkg" in a.unresolved_imports


def test_parse_report_maps_skips(tmp_path: Path) -> None:
    report = {
        "tests": [
            {"nodeid": "t::p", "outcome": "passed"},
            {"nodeid": "t::s", "outcome": "skipped"},
            {"nodeid": "t::xf", "outcome": "xfailed"},
            {"nodeid": "t::xp", "outcome": "xpassed"},
            {
                "nodeid": "t::f",
                "outcome": "failed",
                "call": {"outcome": "failed", "longrepr": "boom"},
            },
        ]
    }
    path = tmp_path / "r.json"
    path.write_text(json.dumps(report))
    parsed = PythonAdapter(work_dir=tmp_path).parse_test_report(path)
    assert parsed["t::s"]["status"] == "skip"
    assert parsed["t::xf"]["status"] == "skip"
    assert parsed["t::xp"]["status"] == "skip"
    failures = [t for t, r in parsed.items() if r["status"] not in ("pass", "skip")]
    assert failures == ["t::f"]  # skips excluded


def test_synthesize_does_not_overwrite_repo_requirements_in(tmp_path: Path) -> None:
    work = make_repo(tmp_path, {"requirements.txt": "requests\n", "requirements.in": "flask\n"})
    a = PythonAdapter(work_dir=work)
    req = a.synthesize_requirements(work)
    assert req.name == "pipeline-requirements.in"  # pipeline-owned name
    assert (work / "requirements.in").read_text() == "flask\n"  # repo's own file untouched


def test_needs_git_metadata(tmp_path: Path) -> None:
    a = PythonAdapter(work_dir=tmp_path)
    scm = make_repo(
        tmp_path / "a",
        {"pyproject.toml": '[build-system]\nrequires = ["setuptools-git-versioning"]\n'},
    )
    plain = make_repo(tmp_path / "b", {"setup.py": "setup(version='1.0')\n"})
    assert a.needs_git_metadata(scm) is True
    assert a.needs_git_metadata(plain) is False


def test_env_fix_failure_falls_through(tmp_path: Path) -> None:
    from pipeline.hygiene import baseline

    ctx = make_ctx(tmp_path, {"pipeline-requirements.in": "pytest\n"})
    ctx.adapter.lock = lambda repo: (_ for _ in ()).throw(RuntimeError("boom"))  # lock fails
    note = baseline._env_fix(ctx, ["somedep"])
    assert note["outcome"] == "env_fix_failed" and "boom" in note["error"]


def test_agent_fix_reverts_source_edits(tmp_path: Path) -> None:
    from pipeline.hygiene import baseline

    ctx = git_ctx(
        tmp_path, {"pkg.py": "x = 1\n", "tests/test_x.py": "def test_ok():\n    assert 1\n"}
    )
    (ctx.repo / "pkg.py").write_text("x = 999  # agent tampered with source\n")  # disallowed
    (ctx.repo / "tests" / "test_x.py").write_text("def test_ok():\n    assert True\n")  # allowed
    (ctx.repo / "evil.py").write_text("bad = 1\n")  # untracked disallowed

    reverted = baseline._revert_disallowed(ctx)

    assert "pkg.py" in reverted and "evil.py" in reverted
    assert "tests/test_x.py" not in reverted
    assert (ctx.repo / "pkg.py").read_text() == "x = 1\n"  # source restored
    assert not (ctx.repo / "evil.py").exists()  # untracked removed
    assert "assert True" in (ctx.repo / "tests" / "test_x.py").read_text()  # test edit kept


def test_env_no_dep_quarantines_without_agent(tmp_path: Path, monkeypatch) -> None:
    from pipeline.hygiene import baseline

    ctx = make_ctx(tmp_path, {"tests/test_x.py": "def test_v():\n    assert 1\n"})
    seq = iter(
        [
            ({"tests/test_x.py::test_v": {"status": "fail", "reason": "version 0.0.1"}}, 1),
            ({}, 0),  # after quarantine (deselected)
        ]
    )
    monkeypatch.setattr(baseline, "_run_suite", lambda ctx, deselect=None: next(seq))
    monkeypatch.setattr(
        baseline, "_classify", lambda ctx, failures: ({"tests/test_x.py::test_v": "env"}, [])
    )
    called = {"agent": False}
    monkeypatch.setattr(baseline, "_agent_fix", lambda ctx: called.__setitem__("agent", True) or {})

    data = baseline.run(ctx)
    assert called["agent"] is False  # env-with-no-dep must NOT invoke the agent
    assert data["quarantined"] == ["tests/test_x.py::test_v"]


def test_pin_hash_invalidates_on_import_change(tmp_path: Path) -> None:
    from pipeline.hygiene import pin

    ctx = make_ctx(tmp_path, {"app.py": "import requests\n"})
    h1 = pin.input_hash(ctx)
    (ctx.repo / "app.py").write_text("import flask\n")
    ctx.adapter._packaging_cache.clear()
    assert pin.input_hash(ctx) != h1


def test_baseline_hash_invalidates_on_test_change(tmp_path: Path) -> None:
    from pipeline.hygiene import baseline

    ctx = make_ctx(tmp_path, {"tests/test_x.py": "def test_a():\n    assert 1\n"})
    ctx.record("build", {"image_digest": "sha256:x"})
    h1 = baseline.input_hash(ctx)
    (ctx.repo / "tests" / "test_x.py").write_text("def test_a():\n    assert 2\n")
    assert baseline.input_hash(ctx) != h1


# --- real build + baseline (docker) -------------------------------------------


def _offline_cfg() -> Config:
    # Test-gen needs the BIG agent (no cassette); its own tests cover it (test_testgen.py).
    # Lint has its own test (test_lint.py); keep it off here so these hygiene assertions
    # (baseline counts, spans) run against unformatted source and skip the extra rebuild.
    cfg = Config()
    cfg.testgen.enabled = False
    cfg.lint.enabled = False
    return cfg


def _hygiene_on_fixture(tmp_path: Path, fixture: str) -> HygieneContext:
    import shutil

    from pipeline.hygiene.context import build_context
    from pipeline.hygiene.runner import run_hygiene

    src = tmp_path / fixture
    shutil.copytree(FIXTURES / fixture, src)
    ctx = build_context(
        str(src), config=_offline_cfg(), output_root=tmp_path / "out", llm_mode="replay"
    )
    run_hygiene(ctx)
    return ctx


@pytest.mark.docker
def test_dockerfile_renders_with_real_digest(tmp_path: Path, docker_available: None) -> None:
    import shutil

    work = tmp_path / "w"
    shutil.copytree(FIXTURES / "mini_pkg", work)
    a = PythonAdapter(work_dir=work)
    a.synthesize_requirements(work)
    lock = a.lock(work)
    a.write_dockerfile(work, lock)
    text = (work / "Dockerfile").read_text()
    assert text.startswith("FROM python@sha256:")
    assert "pip install --no-deps --require-hashes -r requirements.lock.txt" in text
    assert (work / ".dockerignore").is_file()


@pytest.mark.docker
def test_build_and_baseline_mini_pkg(tmp_path: Path, docker_available: None) -> None:
    ctx = _hygiene_on_fixture(tmp_path, "mini_pkg")
    data = ctx.load("baseline")
    assert data["counts"]["passed"] == 13
    assert data["counts"]["quarantined"] == 0
    assert (ctx.hygiene_dir / "pipeline_base.json").is_file()


@pytest.mark.docker
def test_no_tests_repo_bootstraps(tmp_path: Path, monkeypatch, docker_available: None) -> None:
    # wcwidth is an unknown import -> normally the SMALL model maps it (covered by
    # test_alias_fallback_replay). Stub that one endpoint call so this stays offline;
    # the identity default (wcwidth -> wcwidth) is correct here.
    monkeypatch.setattr(PythonAdapter, "_llm_map_imports", lambda self, imports: {})
    ctx = _hygiene_on_fixture(tmp_path, "mini_pkg_notests")
    data = ctx.load("baseline")
    assert data["framework"] == "none" and data["counts"]["tests"] == 0
    assert (ctx.repo / "tests" / "conftest.py").is_file()


@pytest.mark.slow
@pytest.mark.docker
def test_resumability_second_run_skips(tmp_path: Path, docker_available: None) -> None:
    import shutil

    from pipeline.hygiene.context import build_context
    from pipeline.hygiene.runner import run_hygiene

    src = tmp_path / "mini_pkg"
    shutil.copytree(FIXTURES / "mini_pkg", src)
    out = tmp_path / "out"
    run_hygiene(build_context(str(src), config=_offline_cfg(), output_root=out, llm_mode="replay"))
    ctx2 = build_context(str(src), config=_offline_cfg(), output_root=out, llm_mode="replay")
    run_hygiene(ctx2)
    assert all(s.get("skipped") for s in ctx2.report["stages"].values())


@pytest.mark.slow
@pytest.mark.docker
def test_run_twice_identical(tmp_path: Path, docker_available: None) -> None:
    from pipeline.hygiene.runner import verify_twice

    ctx = _hygiene_on_fixture(tmp_path, "mini_pkg")
    assert verify_twice(ctx) is True


@pytest.mark.slow
@pytest.mark.docker
def test_quarantine_failing_test(tmp_path: Path, monkeypatch, docker_available: None) -> None:
    """A genuinely failing test is quarantined and the suite goes green.

    The classify step (its own LLM call) is covered by test_classify_replay; here it
    is stubbed so the quarantine mechanics run against a real image without network.
    """
    import shutil

    from pipeline.hygiene.context import build_context
    from pipeline.hygiene.runner import run_hygiene

    src = tmp_path / "mini_pkg"
    shutil.copytree(FIXTURES / "mini_pkg", src)
    (src / "tests" / "test_broken.py").write_text("def test_broken():\n    assert 1 == 2\n")

    monkeypatch.setattr(
        baseline, "_classify", lambda ctx, failures: ({t: "genuine" for t in failures}, [])
    )
    ctx = build_context(
        str(src), config=_offline_cfg(), output_root=tmp_path / "out", llm_mode="replay"
    )
    ctx.config.agent.baseline_fix_max_attempts = 0  # skip agent-fix; test quarantine directly
    run_hygiene(ctx)

    data = ctx.load("baseline")
    assert data["quarantined"] == ["tests/test_broken.py::test_broken"]
    assert data["still_failing_after_quarantine"] == []
    assert "--deselect" in (ctx.hygiene_dir / "test_command.txt").read_text()
