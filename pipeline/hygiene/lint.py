"""Step 3.7: lint + format the repo clone with ruff, in the pinned container.

Flow (DESIGN 3.7):
  - The adapter writes a ``[tool.ruff.lint]`` config into pyproject.toml (a minimal
    pyproject, no ``[build-system]``, is created when absent so a legacy setup.py
    install is unaffected), then runs ``ruff check --fix`` + ``ruff format`` and adds
    ``# noqa`` for anything still unfixable (``lint.allow_noqa_for_unfixable``).
  - ruff runs on a throwaway copy in-container (the exact pinned ruff, no host
    execution); changed ``.py`` + the config are synced back to output/<repo>/repo.
  - The image is REBUILT from the linted tree (proving a fresh `docker build` still
    works) and the documented suite is run twice; if a formatting change regresses a
    baseline-passing test the tree is reverted and the step records ``regressed`` —
    acceptance (suite stays green) is never sacrificed to a cosmetic change.

Scope: only output/<repo>/repo is linted. Historical task trees (tasks/) live
elsewhere and are built from `git archive` with an additive overlay and no lint, so
the input/->solution/ diff stays the real historical change. Generated tests ARE
linted: they are pipeline-authored, committed after base_sha, so P3 history mining
(at/under base_sha) is unaffected, and the repo ends ruff-clean as a whole.
"""

from __future__ import annotations

import shutil
import subprocess

from pipeline.docker.image import DockerError, build_image
from pipeline.docker.runner import fresh_workdir, run_in_container
from pipeline.hygiene.context import HygieneContext
from pipeline.state import hash_inputs


def input_hash(ctx: HygieneContext) -> str:
    """Keyed on the PRE-lint state (build inputs + the baseline/test-gen artifacts
    that fix the source content) and the lint config — never on the source ruff
    itself rewrites, so a clean resume does not re-lint an already-linted tree."""
    tg = ctx.config.testgen.results_filename
    return hash_inputs(
        ctx.repo / "Dockerfile",
        ctx.repo / ctx.config.pin.lock_filename,
        ctx.hygiene_dir / "baseline.json",
        ctx.hygiene_dir / tg,
        repr(ctx.config.lint),
    )


def run(ctx: HygieneContext) -> dict:
    if not ctx.config.lint.enabled:
        data = {"enabled": False}
        ctx.record("lint", data)
        return data
    data = _run(ctx)
    ctx.record("lint", data)
    return data


def _run(ctx: HygieneContext) -> dict:
    before = _snapshot(ctx)
    with fresh_workdir(ctx.repo) as work:
        def run_cmd(cmd: str):
            return run_in_container(
                work, cmd, ctx.image_tag, timeout=ctx.config.docker.default_cmd_timeout_s
            )

        report = ctx.adapter.lint_and_format(work, run_cmd)
        changed = _sync_back(work, ctx.repo)
    report["files_changed"] = changed
    # Prove the linted tree still builds, and record the linted image digest.
    build_ok, build_err = _rebuild_image(ctx)
    report["image_rebuilt"] = build_ok
    if not build_ok:
        report["build_error"] = build_err[-1000:]
        _revert(ctx, before)
        report["regressed"] = True
        report["reverted"] = "build-failed"
        return report
    suite = _verify_suite(ctx)
    report.update(suite)
    if suite["newly_failing"]:
        _revert(ctx, before)
        _rebuild_image(ctx)  # restore the pre-lint image
        report["regressed"] = True
        report["reverted"] = "suite-regression"
    else:
        report["regressed"] = False
    return report


def _snapshot(ctx: HygieneContext) -> dict:
    """What we need to revert cleanly: whether pyproject.toml already existed."""
    return {"pyproject_existed": (ctx.repo / "pyproject.toml").is_file()}


def _sync_back(work, repo) -> list[str]:
    """Copy every .py (and pyproject.toml) that ruff changed in the throwaway tree back
    onto the canonical repo, host-side (avoids container-root file ownership on the
    canonical tree). Returns the sorted list of repo-relative files changed."""
    changed: list[str] = []
    names = [p for p in work.rglob("*.py") if ".git" not in p.parts]
    names.append(work / "pyproject.toml")
    for src in names:
        if not src.is_file():
            continue
        rel = src.relative_to(work)
        dst = repo / rel
        new = src.read_bytes()
        if not dst.is_file() or dst.read_bytes() != new:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(new)
            changed.append(str(rel))
    return sorted(changed)


def _rebuild_image(ctx: HygieneContext) -> tuple[bool, str]:
    """Rebuild the canonical bench-<repo> image from the (linted) tree and update
    build.json's digest. Returns (ok, error_text)."""
    try:
        digest = build_image(ctx.repo, ctx.image_tag)
    except DockerError as exc:
        return False, str(exc)
    build = ctx.load("build") if (ctx.hygiene_dir / "build.json").is_file() else {}
    build["image_digest"] = digest
    build["image_tag"] = ctx.image_tag
    build["relinted"] = True
    ctx.record("build", build)
    return True, ""


def _verify_suite(ctx: HygieneContext) -> dict:
    """Run the documented suite twice (total) on the linted tree and compare; the first
    run also yields the newly-failing set vs the recorded baseline-passing tests."""
    from pipeline.hygiene import baseline as baseline_step

    if ctx.adapter.test_framework(ctx.repo) == "none":
        return {"suite_after": {}, "twice_identical": True, "newly_failing": []}
    base = ctx.load("baseline") if (ctx.hygiene_dir / "baseline.json").is_file() else {}
    quarantined = base.get("quarantined") or None
    baseline_passing = {
        t for t, r in (base.get("results") or {}).items() if r.get("status") == "pass"
    }
    results, _ = baseline_step._run_suite(ctx, quarantined)
    second, _ = baseline_step._run_suite(ctx, quarantined)
    twice = {t: r["status"] for t, r in results.items()} == {
        t: r["status"] for t, r in second.items()
    }
    now_failing = {t for t, r in results.items() if r["status"] not in ("pass", "skip")}
    newly_failing = sorted(baseline_passing & now_failing)
    return {
        "suite_after": {
            "tests": len(results),
            "passed": sum(1 for r in results.values() if r["status"] == "pass"),
            "failed": len(now_failing),
        },
        "twice_identical": twice,
        "newly_failing": newly_failing,
    }


def _revert(ctx: HygieneContext, before: dict) -> None:
    """Undo the lint edits so the committed repo keeps its green baseline: restore
    tracked files, and drop a pyproject.toml we created."""
    if (ctx.repo / ".git").is_dir():
        subprocess.run(
            ["git", "-C", str(ctx.repo), "checkout", "--", "."],
            capture_output=True,
            check=False,
        )
    if not before["pyproject_existed"]:
        (ctx.repo / "pyproject.toml").unlink(missing_ok=True)
    shutil.rmtree(ctx.repo / ".ruff_cache", ignore_errors=True)
