"""Lint step on mini_pkg (real Docker): repo ends ruff-clean, a labeled
`pipeline: lint and format` commit exists, image rebuilds, suite green. Plus prune helper.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from pipeline.config import Config
from pipeline.docker.image import BUILD_LABEL, build_image, prune_dangling_bench_images
from pipeline.docker.runner import fresh_workdir, run_in_container
from pipeline.ecosystems.python import PythonAdapter, _apply_noqa, _container_rel

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _lint_cfg() -> Config:
    cfg = Config()
    cfg.testgen.enabled = False  # not needed here; lint is the focus
    cfg.okf.enabled = False
    cfg.lint.enabled = True
    return cfg


def test_container_rel_maps_mount_and_relative_paths():
    assert _container_rel("/repo/pkg/mod.py") == "pkg/mod.py"
    assert _container_rel("/repo/mod.py") == "mod.py"
    assert _container_rel("./pkg/mod.py") == "pkg/mod.py"
    assert _container_rel("pkg/mod.py") == "pkg/mod.py"


def test_apply_noqa_on_ruff_shaped_absolute_filename(tmp_path):
    (tmp_path / "foo.py").write_text("l = 1\n")  # E741, unfixable
    findings = [{"filename": "/repo/foo.py", "location": {"row": 1}, "code": "E741"}]
    applied = _apply_noqa(tmp_path, findings)
    assert applied == {"foo.py": ["E741"]}
    assert (tmp_path / "foo.py").read_text() == "l = 1  # noqa: E741\n"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def test_lint_step_leaves_repo_ruff_clean_and_committed(tmp_path, docker_available):
    from pipeline.hygiene.context import build_context
    from pipeline.hygiene.runner import run_hygiene

    src = tmp_path / "mini_pkg"
    shutil.copytree(FIXTURES / "mini_pkg", src)
    ctx = build_context(
        str(src), config=_lint_cfg(), output_root=tmp_path / "out", llm_mode="replay"
    )
    run_hygiene(ctx)

    lint = ctx.load("lint")
    assert lint.get("regressed") is False
    assert lint.get("image_rebuilt") is True
    assert lint.get("clean") is True
    # a minimal pyproject was created and files were reformatted
    assert (ctx.repo / "pyproject.toml").is_file()
    assert "[tool.ruff" in (ctx.repo / "pyproject.toml").read_text()

    # the linted repo is ruff-clean INSIDE the pinned image (the documented command)
    select = ",".join(ctx.config.lint.rules)
    result = run_in_container(ctx.repo, f"ruff check --select {select} .", ctx.image_tag)
    assert result.exit_code == 0, result.stdout + result.stderr

    # the suite still passes after linting
    assert lint["suite_after"]["failed"] == 0
    assert lint["twice_identical"] is True

    # a labeled pipeline commit exists and mines-at/under base_sha is unaffected
    subjects = _git(ctx.repo, "log", "--format=%s").splitlines()
    assert "pipeline: lint and format" in subjects


def test_lint_applies_noqa_for_unfixable_and_ends_clean(tmp_path, mini_env):
    """A real in-container ruff run over a file with an unfixable E741 finding: the noqa
    is applied on the right line and a fresh ruff check comes back clean."""
    repo = tmp_path / "r"
    (repo / "pkg").mkdir(parents=True)
    (repo / "pkg" / "mod.py").write_text("def f():\n    l = 1\n    return l\n")  # E741
    adapter = PythonAdapter(config=Config(), work_dir=repo)
    image = mini_env.image_tag  # a built image that has the pinned ruff
    with fresh_workdir(repo) as work:
        from pipeline.hygiene.lint import _sync_back

        def run(cmd):
            return run_in_container(work, cmd, image, timeout=300)

        report = adapter.lint_and_format(work, run)
        _sync_back(work, repo)
    assert "E741" in (report["codes"] or {})
    assert report["noqa"].get("pkg/mod.py") == ["E741"]
    assert report["clean"] is True
    assert "# noqa: E741" in (repo / "pkg" / "mod.py").read_text()


def test_lint_reverts_on_suite_regression(tmp_path, docker_available, monkeypatch):
    """If a formatting change makes a baseline-passing test fail, the tree is reverted
    (created pyproject removed, source restored) and `regressed` is recorded."""
    from pipeline.hygiene import lint as lint_mod
    from pipeline.hygiene.context import build_context
    from pipeline.hygiene.runner import run_hygiene

    src = tmp_path / "mini_pkg"
    shutil.copytree(FIXTURES / "mini_pkg", src)
    cfg = _lint_cfg()
    cfg.lint.enabled = False  # first build the image + baseline with source committed, no lint
    ctx = build_context(str(src), config=cfg, output_root=tmp_path / "out", llm_mode="replay")
    run_hygiene(ctx)

    # force lint but stub the rebuild (fast) and make the suite report a regression
    ctx.config.lint.enabled = True
    monkeypatch.setattr(lint_mod, "_rebuild_image", lambda c: (True, ""))
    monkeypatch.setattr(
        lint_mod,
        "_verify_suite",
        lambda c: {
            "suite_after": {"failed": 1},
            "twice_identical": True,
            "newly_failing": ["tests/test_calc.py::test_clamp"],
        },
    )
    data = lint_mod.run(ctx)
    assert data["regressed"] is True and data["reverted"] == "suite-regression"
    assert not (ctx.repo / "pyproject.toml").exists()  # the created config was reverted
    status = subprocess.run(
        ["git", "-C", str(ctx.repo), "status", "--porcelain"], capture_output=True, text=True
    ).stdout
    assert status.strip() == ""  # working tree restored -> no lint commit will be made


def test_second_run_skips_lint(tmp_path, docker_available):
    from pipeline.hygiene.context import build_context
    from pipeline.hygiene.runner import run_hygiene

    src = tmp_path / "mini_pkg"
    shutil.copytree(FIXTURES / "mini_pkg", src)
    out = tmp_path / "out"
    run_hygiene(build_context(str(src), config=_lint_cfg(), output_root=out, llm_mode="replay"))
    ctx2 = build_context(str(src), config=_lint_cfg(), output_root=out, llm_mode="replay")
    run_hygiene(ctx2)
    assert ctx2.report["stages"]["lint"]["skipped"] is True


def test_disabled_lint_is_noop(tmp_path, docker_available):
    from pipeline.hygiene import lint
    from pipeline.hygiene.context import build_context

    src = tmp_path / "mini_pkg"
    shutil.copytree(FIXTURES / "mini_pkg", src)
    cfg = _lint_cfg()
    cfg.lint.enabled = False
    ctx = build_context(str(src), config=cfg, output_root=tmp_path / "out", llm_mode="replay")
    data = lint.run(ctx)
    assert data == {"enabled": False}


def test_build_labels_image_and_prune_targets_only_our_dangling(tmp_path, docker_available):
    """A rebuild of the same tag leaves the previous image dangling; prune removes ONLY
    dangling images carrying our label, never the tagged one or anything unlabeled."""
    ctx_dir = tmp_path / "ctx"
    ctx_dir.mkdir()
    base = "python:3.12-slim"
    (ctx_dir / "Dockerfile").write_text(f"FROM {base}\nRUN echo v1 > /marker\n")
    tag = "bench-linttest-prune"
    build_image(ctx_dir, tag)

    # the built image carries our label
    labels = subprocess.run(
        ["docker", "inspect", "--format", '{{index .Config.Labels "' + BUILD_LABEL + '"}}', tag],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert labels == "1"

    # rebuild the same tag -> the old image becomes dangling (untagged) with our label
    old_id = _image_id(tag)
    (ctx_dir / "Dockerfile").write_text(f"FROM {base}\nRUN echo v2 > /marker\n")
    build_image(ctx_dir, tag)

    assert old_id in _dangling_labeled()
    prune_dangling_bench_images()
    # assert on OUR image only: an unrelated dangling image may be pinned by a stale container
    assert old_id not in _dangling_labeled()
    # the tagged image is still here (prune only touched dangling ones)
    assert subprocess.run(["docker", "image", "inspect", tag], capture_output=True).returncode == 0

    subprocess.run(["docker", "rmi", "-f", tag], capture_output=True, check=False)


def _dangling_labeled() -> set[str]:
    out = subprocess.run(
        [
            "docker",
            "images",
            "-f",
            "dangling=true",
            "-f",
            f"label={BUILD_LABEL}=1",
            "-q",
            "--no-trunc",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return {line.strip() for line in out.splitlines() if line.strip()}


def _image_id(ref: str) -> str:
    return subprocess.run(
        ["docker", "image", "inspect", "--format", "{{.Id}}", ref],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
