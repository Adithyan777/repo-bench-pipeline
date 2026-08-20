"""Hygiene step 6 (baseline): baseline suite in the container; classify failures (SMALL model).

env + missing dep -> one env-fix (add dep, re-lock, rebuild); genuine -> one bounded
agent-fix limited to tests/config/deps (edits elsewhere reverted + audited); anything
still failing -> quarantine. Never delete a test or fake a pass; skips are not failures.
"""

from __future__ import annotations

import fnmatch
import json
import subprocess

from pipeline.agent.loop import Agent
from pipeline.agent.tools import ToolContext, concrete_tools
from pipeline.docker.image import build_image
from pipeline.docker.runner import fresh_workdir, run_in_container
from pipeline.hygiene.context import HygieneContext, append_agent_action
from pipeline.log import log
from pipeline.state import hash_inputs

NO_TESTS_EXIT = 5  # pytest: no tests collected

_CLASSIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "classifications": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "test_id": {"type": "string"},
                    "category": {"enum": ["env", "genuine"]},
                    "missing_dep": {"type": "string"},
                },
                "required": ["test_id", "category"],
            },
        }
    },
    "required": ["classifications"],
}

_FIX_SYSTEM = (
    "You are fixing pre-existing failing tests in a Python repo. You may ONLY edit test "
    "files, conftest.py, the Dockerfile, or the requirements files — never the library "
    "source under test. Use the tools to find the cause and make the smallest correct "
    "change so the suite passes. Run the tests to confirm."
)


def _is_failure(result: dict[str, str]) -> bool:
    return result["status"] not in ("pass", "skip")


def input_hash(ctx: HygieneContext) -> str:
    parts = [ctx.hygiene_dir / "build.json"]
    for pattern in ("test_*.py", "test*.py", "conftest.py"):
        parts += ctx.repo.rglob(pattern)
    for tests_dir in ctx.repo.rglob("tests"):
        if tests_dir.is_dir():
            parts += tests_dir.rglob("*.py")
    # Generated tests (written after baseline) are excluded so baseline stays resumable.
    marker = ctx.config.testgen.generated_subdir

    def is_generated(p) -> bool:
        try:
            return marker in p.relative_to(ctx.repo).parts
        except ValueError:
            return False

    files = sorted({p.resolve() for p in parts if p.is_file() and not is_generated(p)})
    return hash_inputs(*files)


def run(ctx: HygieneContext) -> dict:
    adapter, repo = ctx.adapter, ctx.repo
    framework = adapter.test_framework(repo)
    if framework == "none":
        adapter.test_framework_bootstrap(repo)
        _write_test_command(ctx, [])
        data = {"framework": "none", "bootstrapped": True, "counts": {"tests": 0}}
        ctx.record("baseline", data)
        return data

    results, exit_code = _run_suite(ctx)
    if exit_code == NO_TESTS_EXIT and not results:
        _write_test_command(ctx, [])
        data = {"framework": framework, "counts": {"tests": 0}, "note": "no tests collected"}
        ctx.record("baseline", data)
        return data

    failures = {tid: r for tid, r in results.items() if _is_failure(r)}
    quarantined: list[str] = []
    categories: dict[str, str] = {}
    notes: dict[str, object] = {}
    log("hygiene", "baseline", f"suite: {len(results)} tests, {len(failures)} failing")

    if failures:
        categories, deps = _classify(ctx, failures)
        log("hygiene", "baseline", f"classified: {_category_counts(categories)}")
        if deps:
            notes["env_fix"] = _env_fix(ctx, deps)
            results, _ = _run_suite(ctx)
            failures = {tid: r for tid, r in results.items() if _is_failure(r)}
            log(
                "hygiene",
                "baseline",
                f"env-fix {notes['env_fix'].get('outcome')}: {len(failures)} still failing",
            )
        genuine = [tid for tid in failures if categories.get(tid) == "genuine"]
        if genuine and ctx.config.agent.baseline_fix_max_attempts >= 1:
            notes["agent_fix"] = _agent_fix(ctx)
            results, _ = _run_suite(ctx)
            failures = {tid: r for tid, r in results.items() if _is_failure(r)}
            log(
                "hygiene",
                "baseline",
                f"agent-fix {notes['agent_fix'].get('outcome')}: {len(failures)} still failing",
            )
        if failures:
            quarantined = sorted(failures)
            _write_quarantine(ctx, quarantined)
            results, _ = _run_suite(ctx, deselect=quarantined)
            log("hygiene", "baseline", f"quarantined {len(quarantined)}")

    still_failing = sorted(tid for tid, r in results.items() if _is_failure(r))
    _write_test_command(ctx, quarantined)
    data = {
        "framework": framework,
        "counts": {
            "tests": len(results),
            "passed": sum(1 for r in results.values() if r["status"] == "pass"),
            "skipped": sum(1 for r in results.values() if r["status"] == "skip"),
            "quarantined": len(quarantined),
        },
        "quarantined": quarantined,
        "classifications": categories,
        "notes": notes,
        "still_failing_after_quarantine": still_failing,
        "results": results,
    }
    ctx.record("baseline", data)
    if still_failing:
        raise SystemExit(f"{repo.name}: {len(still_failing)} tests still failing after quarantine")
    return data


def _category_counts(categories: dict[str, str]) -> str:
    counts: dict[str, int] = {}
    for cat in categories.values():
        counts[cat] = counts.get(cat, 0) + 1
    return " ".join(f"{k}={v}" for k, v in sorted(counts.items())) or "none"


def _run_suite(
    ctx: HygieneContext, deselect: list[str] | None = None
) -> tuple[dict[str, dict[str, str]], int]:
    report_rel = ctx.config.baseline.report_filename
    cmd = ctx.adapter.reporting_command(ctx.repo, report_rel, deselect)
    with fresh_workdir(ctx.repo) as work:
        result = run_in_container(work, cmd, ctx.image_tag)
        report = work / report_rel
        parsed = ctx.adapter.parse_test_report(report) if report.is_file() else {}
    return parsed, result.exit_code


def run_twice_identical(ctx: HygieneContext, deselect: list[str] | None = None) -> bool:
    """Run the documented command twice; return whether verdicts are identical."""
    first, _ = _run_suite(ctx, deselect)
    second, _ = _run_suite(ctx, deselect)
    verdict = {tid: r["status"] for tid, r in first.items()}
    return verdict == {tid: r["status"] for tid, r in second.items()}


def classify_prompt(chunk: list[str]) -> str:
    return (
        "Classify each failing test as 'env' (missing optional dependency, network, "
        "python-version) or 'genuine' (real behavioral failure). If env and a package "
        "is missing, give its PyPI name in missing_dep.\n\n" + "\n".join(chunk)
    )


def _classify(ctx: HygieneContext, failures: dict) -> tuple[dict[str, str], list[str]]:
    from pipeline.ecosystems.python import valid_requirement

    batch = ctx.config.llm.classify_batch_size
    items = [f"{tid}: {r['reason'][:300]}" for tid, r in failures.items()]
    categories: dict[str, str] = {}
    deps: set[str] = set()
    for i in range(0, len(items), batch):
        chunk = items[i : i + batch]
        res = ctx.llm.complete_json(
            "p1.baseline.classify_failure",
            [{"role": "user", "content": classify_prompt(chunk)}],
            _CLASSIFY_SCHEMA,
        )
        for c in res.get("classifications", []):
            categories[c["test_id"]] = c["category"]
            dep = c.get("missing_dep")
            if dep and valid_requirement(dep):  # never write a garbage name
                deps.add(dep)
    return categories, sorted(deps)


def _env_fix(ctx: HygieneContext, deps: list[str]) -> dict:
    """Add missing deps, re-lock, rebuild. On lock/build failure, record and fall through."""
    req_in = ctx.repo / ctx.config.pin.requirements_in_filename
    existing = req_in.read_text() if req_in.is_file() else ""
    req_in.write_text(existing + "\n".join(deps) + "\n")
    try:
        ctx.adapter.lock(ctx.repo)
        digest = build_image(ctx.repo, ctx.image_tag)
    except Exception as exc:  # noqa: BLE001 - lock/build may fail; fall through to quarantine
        return {"deps": deps, "outcome": "env_fix_failed", "error": str(exc)[:300]}
    _refresh_build_digest(ctx, digest)
    return {"deps": deps, "outcome": "rebuilt"}


def _agent_fix(ctx: HygieneContext) -> dict:
    """Bounded agent-fix restricted to tests/config/deps; audited with the real outcome."""
    tool_ctx = ToolContext(workdir=ctx.repo, image=ctx.image_tag)
    agent = Agent(
        ctx.llm,
        "p1.baseline.fix_agent",
        _FIX_SYSTEM,
        concrete_tools(tool_ctx),
        tool_ctx.files_changed,
    )
    goal = (
        "Some pre-existing tests fail for genuine reasons. Make the smallest change WITHIN "
        f"tests/config/deps so `{ctx.adapter.test_command(ctx.repo)}` passes. Confirm by running."
    )
    result = agent.run(goal)
    reverted = _revert_disallowed(ctx)
    passed, _ = _run_suite(ctx)
    outcome = "fixed" if not any(_is_failure(r) for r in passed.values()) else "not_fixed"
    record = {
        "stage": "p1.baseline.fix_agent",
        "goal": goal,
        "files_changed": result.files_changed,
        "reverted_disallowed": reverted,
        "diff": _diff(ctx.repo),
        "attempts": 1,
        "outcome": outcome,
        "summary": result.summary[:500],
    }
    append_agent_action(ctx.audit_dir, record)
    return {"outcome": outcome, "reverted_disallowed": reverted}


def _revert_disallowed(ctx: HygieneContext) -> list[str]:
    """Revert any working-tree change outside the agent-fix allowed globs."""
    allowed = ctx.config.baseline.agent_fix_allowed_globs
    reverted: list[str] = []
    for code, rel in _porcelain(ctx.repo):
        if any(fnmatch.fnmatch(rel, g) for g in allowed):
            continue
        if code == "??":
            (ctx.repo / rel).unlink(missing_ok=True)
        else:
            _git(ctx.repo, "checkout", "--", rel)
        reverted.append(rel)
    return reverted


def _porcelain(repo) -> list[tuple[str, str]]:
    # Raw stdout (not stripped): the leading status column can be a space.
    proc = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
    )
    entries = []
    for line in proc.stdout.splitlines():
        if line:
            entries.append((line[:2].strip(), line[3:].strip()))
    return entries


def _refresh_build_digest(ctx: HygieneContext, digest: str) -> None:
    build_path = ctx.hygiene_dir / "build.json"
    if build_path.is_file():
        data = json.loads(build_path.read_text())
        data["image_digest"] = digest
        ctx.record("build", data)


def _write_quarantine(ctx: HygieneContext, nodeids: list[str]) -> None:
    path = ctx.repo / ctx.config.baseline.quarantine_file
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(nodeids) + "\n")


def _write_test_command(ctx: HygieneContext, quarantined: list[str]) -> None:
    cmd = ctx.adapter.test_command(ctx.repo)
    if quarantined:
        cmd += " " + " ".join(f"--deselect {q}" for q in quarantined)
    ctx.hygiene_dir.mkdir(parents=True, exist_ok=True)
    (ctx.hygiene_dir / "test_command.txt").write_text(cmd + "\n")


def _diff(repo) -> str:
    return _git(repo, "diff")[:4000]


def _git(repo, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
    )
    return proc.stdout.strip()
