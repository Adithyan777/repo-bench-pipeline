"""History task construction (DESIGN 5.2 build + 5.6 folder format).

tasks/<repo>/hist-<sha7>/{task.json, input/, solution/, verifier/, goldenSolution.md, evidence/}
- input/    = full tree at the parent (git archive, never the working tree)
- solution/ = full tree at the commit
- both get the hygiene overlay ADDITIVELY (Dockerfile, lock, ...): never overwrite a
  historical file, never lint, so input<->solution == the historical change exactly.
- verifier/ = the commit's added/changed test functions (AST diff) at repo-relative
  paths + conftest ancestors + run.sh; or, when the commit has no tests, ONE file
  authored by a bounded BIG agent. Every gate runs in the container at build time.
"""

from __future__ import annotations

import fnmatch
import hashlib
import io
import json
import shutil
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path

from pipeline.agent.loop import Agent
from pipeline.agent.tools import ToolContext, concrete_tools, graph_tools
from pipeline.config import DEFAULT, Config
from pipeline.docker.runner import fresh_workdir, run_in_container
from pipeline.ecosystems.python import PythonAdapter
from pipeline.ecosystems.source_ops import (
    changed_test_functions,
    function_contracts,
    new_identifiers,
    read_source,
    test_nodeid_suffixes,
)
from pipeline.ecosystems.symbols import is_test_path, path_to_module
from pipeline.tasks import history as H
from pipeline.tasks.build_excision import BuildInputs, _audit, files_in_scope
from pipeline.tasks.classify import classify_report
from pipeline.tasks.harness import static_gate_violations

VERIFIER_AGENT_STEP = "p3.build.verifier_agent"
NEUTRALITY_STEP = "p3.build.neutrality_check_rewrite"

NEUTRALITY_SCHEMA = {
    "type": "object",
    "properties": {
        "neutral": {"type": "boolean"},
        "issues": {"type": "array", "items": {"type": "string"}},
        "flagged_tests": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["neutral", "issues", "flagged_tests"],
}

# Verifier convention for API the change introduces (history.allow_new_symbol_features).
NEW_SYMBOL_RULE = (
    "Names introduced by the change do not exist in the pre-change tree, so a module-level "
    "import of one fails with ImportError (an invalid failure). Convention: import an "
    "EXISTING public module (e.g. `from pkg import mod`), then inside the test do "
    "`fn = getattr(mod, 'new_name', None)`, `assert fn is not None`, and assert its "
    "behavior; the pre-change tree then fails with AssertionError (a valid failure). "
    "Never reach for private helpers (`_name`)."
)

VERIFIER_AGENT_SYSTEM = (
    "You are a test author. Write focused pytest tests that pin down ONE behavior change "
    "of this repository, asserting only through its public interface (the same imports "
    "the existing tests use; never private helpers). "
    + NEW_SYMBOL_RULE
    + " Run the tests with the `run` tool until they pass. Only the single file you were "
    "told to create is kept. Reply with a one-line summary when done."
)

REWRITE_AGENT_SYSTEM = (
    "You are a test reviewer. Rewrite the named tests so they assert behavior through the "
    "public interface only (no private helpers, no implementation details), keeping the "
    "test names and their intent. "
    + NEW_SYMBOL_RULE
    + " Run the tests with the `run` tool until they pass. Only the test files you were "
    "told about are kept. Reply with a one-line summary when done."
)

_DRIFT_REASONS = {
    "ImportError",
    "ModuleNotFoundError",
    "SyntaxError",
    "AttributeError@import",
    "collection_error",
    "collected_0_items",
    "no_report",
}


@dataclass
class HistoryBuild:
    task_id: str
    task_dir: Path | None
    reject_reason: str | None
    notes: dict


def task_id_for(c: H.HistoryCandidate, config: Config = DEFAULT) -> str:
    return f"{config.tasks.history_id_prefix}-{c.short}"


# --- trees ----------------------------------------------------------------------------


def archive_tree(repo: Path, sha: str, dest: Path) -> None:
    """Extract the committed tree at ``sha`` (never the working tree) into ``dest``."""
    proc = subprocess.run(
        ["git", "-C", str(repo), "archive", "--format=tar", sha], capture_output=True, check=True
    )
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(proc.stdout)) as tar:
        tar.extractall(dest, filter="data")


def overlay_files(repo: Path, config: Config = DEFAULT) -> list[str]:
    """Hygiene artifacts to overlay: the pipeline commit's files when recorded, else the
    configured list; only those present in the current repo tree."""
    names = list(config.tasks.hygiene_overlay_files)
    pb = repo.parent / "hygiene" / "pipeline_base.json"
    if pb.is_file():
        for sha in json.loads(pb.read_text()).get("pipeline_commits", []):
            listed = H.git(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", sha).split()
            names.extend(n for n in listed if n not in names)
    ignore = config.tasks.tree_ignore
    return sorted(
        n
        for n in names
        if (repo / n).is_file()
        and not any(fnmatch.fnmatch(part, pat) for part in Path(n).parts for pat in ignore)
    )


def overlay(repo: Path, dest: Path, names: list[str]) -> list[str]:
    """Copy each overlay file into ``dest`` unless the historical tree already has it."""
    done: list[str] = []
    for rel in names:
        target = dest / rel
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repo / rel, target)
        done.append(rel)
    return done


# --- container runs -------------------------------------------------------------------


def run_tree(task_dir: Path, tree: str, cmd: str, image: str, config: Config) -> dict:
    """One in-container run of ``cmd`` on ``<task>/<tree>`` with verifier/ overlaid;
    returns ``{exit_code, report, outcomes, n_failing, n_passing}``."""
    adapter = PythonAdapter(config=config)
    report_rel = config.harness.report_filename
    with fresh_workdir(task_dir / tree) as work:
        if (task_dir / "verifier").is_dir():
            shutil.copytree(task_dir / "verifier", work, dirs_exist_ok=True)
        result = run_in_container(work, adapter.with_report(cmd, report_rel), image)
        path = work / report_rel
        report = json.loads(path.read_text()) if path.is_file() else None
    summary = (report or {}).get("summary", {})
    return {
        "exit_code": result.exit_code,
        "report": report,
        "outcomes": {t["nodeid"]: t.get("outcome") for t in (report or {}).get("tests", [])},
        "n_failing": summary.get("failed", 0) + summary.get("error", 0),
        "n_passing": summary.get("passed", 0),
        "log": f"$ {cmd}\nexit_code={result.exit_code}\n{result.stdout}\n{result.stderr}",
    }


def _reasons(run: dict, verifier_files: list[str], config: Config) -> dict[str, dict]:
    """nodeid -> {reason, valid} for every failing test of a run (STRICT classifier)."""
    hc = config.harness

    def is_test(rel: str) -> bool:
        return rel in verifier_files or is_test_path(Path("/r"), Path("/r") / rel, config)

    verdict = classify_report(
        run["report"],
        run["exit_code"],
        is_test,
        min_failing=0,
        valid_reasons=hc.valid_fail_reasons,
        invalid_reasons=hc.invalid_fail_reasons,
    )
    out = {n: {"reason": r["reason"], "valid": r["valid"]} for n, r in verdict.reasons.items()}
    for r in verdict.invalid:
        out.setdefault(f"<{r}>", {"reason": r, "valid": False})
    return out


def _drift_reasons(run: dict, verifier_files: list[str], config: Config) -> list[str]:
    reasons = _reasons(run, verifier_files, config)
    return sorted({r["reason"] for r in reasons.values() if r["reason"] in _DRIFT_REASONS})


# --- verifier -------------------------------------------------------------------------


def _write_rel(dest_root: Path, rel: str, text: str) -> None:
    path = dest_root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def commit_test_nodeids(c: H.HistoryCandidate, repo: Path) -> dict[str, list[str]]:
    """test file -> nodeids of test functions added/changed by the commit (AST diff of the
    file between input and commit state; deleted files are skipped)."""
    out: dict[str, list[str]] = {}
    for rel in c.test_files:
        after = H.show(repo, c.sha, rel)
        if after is None or not rel.endswith(".py"):
            continue
        before = H.show(repo, c.input_sha, rel)
        changed = changed_test_functions(before, after)
        if changed:
            out[rel] = [f"{rel}::{name}" for name in changed]
    return out


def _copy_commit_tests(c: H.HistoryCandidate, repo: Path, verifier: Path, files: list[str]) -> None:
    for rel in files:
        src = H.show(repo, c.sha, rel)
        if src is None:  # deleted by the commit
            continue
        _write_rel(verifier, rel, src)
        for anc in Path(rel).parents:
            conftest = str(anc / "conftest.py")
            src = H.show(repo, c.sha, conftest)
            if src is not None:
                _write_rel(verifier, conftest, src)


def _test_dir_for(solution: Path, source_files: list[str], config: Config) -> Path:
    """Directory for an agent-authored test file: the existing test directory sharing the
    longest path prefix with the touched sources (fallback ``tests/``)."""
    dirs: dict[str, int] = {}
    for p in solution.rglob("*.py"):
        if is_test_path(solution, p, config) and p.name.startswith("test_"):
            rel = str(p.parent.relative_to(solution))
            dirs[rel] = dirs.get(rel, 0) + 1
    if not dirs:
        return Path("tests")
    src_parts = [Path(f).parts for f in source_files]

    def affinity(d: str) -> tuple[int, int, str]:
        parts = Path(d).parts
        common = max(
            (sum(1 for a, b in zip(parts, s, strict=False) if a == b) for s in src_parts),
            default=0,
        )
        return (common, dirs[d], d)

    return Path(max(dirs, key=affinity))


def _contracts(tree: Path, files: list[str], qualnames: list[str], config: Config) -> str:
    wanted = set(qualnames)
    lines: list[str] = []
    for rel in files:
        path = tree / rel
        if not path.is_file():
            continue
        module = path_to_module(rel, config.knowledge.source_roots)
        for fn in function_contracts(read_source(path), module):
            if fn["qualname"] in wanted:
                doc = (fn["docstring"] or "").strip()
                lines.append(
                    f"- {fn['qualname']}: `{fn['signature']}`" + (f"\n  {doc}" if doc else "")
                )
    return "\n".join(lines) or "- (no touched function contracts found)"


def _new_names(c: H.HistoryCandidate, repo: Path) -> list[str]:
    names: set[str] = set()
    for rel in c.source_files:
        after = H.show(repo, c.sha, rel)
        if after is None:
            continue
        names |= new_identifiers(H.show(repo, c.input_sha, rel), after)
    return sorted(n for n in names if len(n) > 1)


def _cache_key(*parts: str) -> str:
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()[: DEFAULT.tasks.content_key_chars]


def _take_agent_run(inp: BuildInputs, max_runs: int, kind: str = "agent_runs") -> bool:
    """Consume one unit of a per-build-step agent budget (cached/reused runs never call)."""
    used = inp.counters.get(kind, 0)
    if used >= max_runs:
        return False
    inp.counters[kind] = used + 1
    return True


def _agent_cache(inp: BuildInputs, key: str) -> Path | None:
    if inp.cache_dir is None:
        return None
    return inp.cache_dir / key


def _run_agent(
    inp: BuildInputs,
    step: str,
    system: str,
    goal: str,
    base_tree: Path,
    verifier: Path,
    keep_files: list[str],
    config: Config,
) -> tuple[list[str], dict]:
    """Bounded agent on a throw-away copy of ``base_tree`` (+ verifier overlay); only
    ``keep_files`` it changed are copied back into verifier/. Returns (kept, note)."""
    with tempfile.TemporaryDirectory(prefix="bench-agent-") as tmp:
        work = Path(tmp) / "repo"
        shutil.copytree(base_tree, work)
        if verifier.is_dir():
            shutil.copytree(verifier, work, dirs_exist_ok=True)
        tctx = ToolContext(
            work,
            image=inp.image_tag,
            knowledge_dir=inp.knowledge_dir,
            repo_root=inp.repo,
            config=config,
        )
        agent = Agent(
            inp.llm,
            step,
            system,
            [*concrete_tools(tctx), *graph_tools(tctx)],
            tctx.files_changed,
            max_turns=config.history.agent_max_turns,
            transcripts_dir=inp.transcripts_dir,
        )
        result = agent.run(goal)
        kept: list[str] = []
        for rel in keep_files:
            if (work / rel).is_file() and rel in result.files_changed:
                _write_rel(verifier, rel, read_source(work / rel))
                kept.append(rel)
    return kept, {
        "files_changed": result.files_changed,
        "summary": result.summary[: config.tasks.audit_summary_chars],
        "clean_exit": result.summary != Agent.MAX_TURNS_SUMMARY,
        "trajectory": result.trajectory_path,
    }


def _verifier_from_agent(
    c: H.HistoryCandidate, inp: BuildInputs, task_dir: Path, config: Config
) -> tuple[list[str], dict]:
    """Bounded BIG agent authors ONE test file for a commit without tests. Cached by
    content hash so a rerun costs no tokens. Returns (nodeids, note)."""
    hc = config.history
    test_dir = _test_dir_for(task_dir / "solution", c.source_files, config)
    rel = str(test_dir / f"{hc.agent_test_file_prefix}{c.short}.py")
    summary = (c.classify or {}).get("behavior_change_summary", "")
    contracts = _contracts(task_dir / "solution", c.source_files, c.touched_functions, config)
    src_diff = H.diff(inp.repo, c.input_sha, c.sha, c.source_files)
    if len(src_diff) > hc.agent_diff_max_chars:
        src_diff = src_diff[: hc.agent_diff_max_chars] + "\n... (truncated)"
    goal = (
        f"Create `{rel}` with 3-6 pytest tests that FAIL before this change and PASS "
        f"after it (the tree you see is AFTER the change).\n\nBehavior change: {summary}\n\n"
        f"Touched functions (signature + docstring):\n{contracts}\n\n"
        f"Import only public names that existed BEFORE the change (look at how existing "
        f"tests import from this package). Names introduced by this change "
        f"({', '.join(_new_names(c, inp.repo)[: hc.prompt_new_names_max]) or '(none)'}) may "
        f"only be reached through "
        f"the getattr convention above, never imported.\n\n"
        f"The change (for your understanding only; do not copy it into the tests):\n"
        f"```diff\n{src_diff}\n```\n\nRun `python -m pytest -q {rel}` until every test passes."
    )
    key = _cache_key("verifier_agent", c.sha, goal)
    verifier = task_dir / "verifier"
    note: dict = {"step": VERIFIER_AGENT_STEP, "file": rel, "cache_key": key, "attempts": 0}
    cache = _agent_cache(inp, key)
    prior = (inp.decisions or {}).get(key)
    if cache and (cache / rel).is_file() and hc.reuse_agent_outputs:
        _write_rel(verifier, rel, read_source(cache / rel))
        note.update({"outcome": "reused", "reused": True})
    elif prior is not None and hc.reuse_agent_outputs:
        note.update({"outcome": prior["outcome"], "reused": True})  # a recorded no-output run
    elif inp.llm is None:
        note["outcome"] = "no_llm"
    elif not _take_agent_run(inp, hc.max_agent_runs_per_repo):
        note["outcome"] = "budget-exhausted"
    else:
        for attempt in range(1, hc.verifier_agent_max_attempts + 1):
            note["attempts"] = attempt
            kept, run_note = _run_agent(
                inp,
                VERIFIER_AGENT_STEP,
                VERIFIER_AGENT_SYSTEM,
                goal,
                task_dir / "solution",
                verifier,
                [rel],
                config,
            )
            note.update(run_note)
            if kept and not run_note["clean_exit"]:  # no reviewed end state: discard
                (verifier / rel).unlink(missing_ok=True)
                kept = []
                note["outcome"] = "max-turns"
            else:
                note["outcome"] = "added" if kept else "no_tests"
            _audit(
                inp.audit_dir,
                {
                    "stage": VERIFIER_AGENT_STEP,
                    "goal": goal[: config.tasks.audit_goal_chars],
                    "task": task_id_for(c, config),
                    **note,
                },
            )
            if kept:
                if cache:
                    _write_rel(cache, rel, read_source(verifier / rel))
                break
        if inp.decisions is not None:
            inp.decisions[key] = {"outcome": note["outcome"]}
    path = verifier / rel
    names = test_nodeid_suffixes(read_source(path)) if path.is_file() else []
    if not names:
        return [], note
    _copy_conftests(task_dir / "solution", verifier, rel)
    return sorted(f"{rel}::{n}" for n in names), note


def _existing_nodeids(verifier: Path, nodeids: list[str]) -> list[str]:
    """Nodeids whose test function still exists in the (possibly rewritten) file."""
    by_file: dict[str, set[str]] = {}
    for n in nodeids:
        rel = n.split("::", 1)[0]
        if rel not in by_file:
            by_file[rel] = set(test_nodeid_suffixes(read_source(verifier / rel)))
    return sorted(n for n in nodeids if n.split("::", 1)[1] in by_file[n.split("::", 1)[0]])


def _copy_conftests(tree: Path, verifier: Path, rel: str) -> None:
    for anc in Path(rel).parents:
        conftest = tree / anc / "conftest.py"
        if conftest.is_file():
            _write_rel(verifier, str(anc / "conftest.py"), read_source(conftest))


# --- neutrality (BIG) -----------------------------------------------------------------


def _test_sources(verifier: Path, nodeids: list[str]) -> str:
    blocks: list[str] = []
    for rel in sorted({n.split("::", 1)[0] for n in nodeids}):
        names = {n.rsplit("::", 1)[-1] for n in nodeids if n.startswith(rel + "::")}
        src = read_source(verifier / rel)
        blocks.append(f"### {rel} (tests: {', '.join(sorted(names))})\n```python\n{src}\n```")
    return "\n\n".join(blocks)


def neutrality_prompt(
    c: H.HistoryCandidate, tests: str, contracts: str, new_names: list[str]
) -> str:
    return (
        "You review verifier tests for a benchmark task: the solver gets the tree BEFORE a "
        "change and must reimplement the change so these tests pass. Tests are acceptable "
        "only if they assert BEHAVIOR through the public interface. Flag a test if it: "
        "imports or calls private helpers (`_name`), references identifiers newly "
        "introduced by the change (listed below) that a solver could name differently, "
        "asserts implementation details (internal call order, private state, exact repr of "
        "internals), or merely mirrors the patch. Testing public functions/classes that "
        "already exist before the change is fine, and so is reaching NEW public API through "
        "the convention `getattr(existing_public_module, 'name', None)` + a presence assert "
        "(new public API is part of the task's contract; only its private helpers are not). "
        "Which exception type is raised, and exception identity/chaining observable by a "
        "caller (`e is cause`, `__cause__`), IS behavior, not an implementation detail.\n\n"
        f"Commit: {c.message}\nTouched functions:\n{contracts}\n"
        f"Identifiers introduced by the change: {', '.join(new_names) or '(none)'}\n\n"
        f"{tests}\n\nReturn neutral=true when nothing is flagged; otherwise list issues and "
        "the flagged test nodeids (file::name)."
    )


def _neutrality_decision(
    c: H.HistoryCandidate, inp: BuildInputs, task_dir: Path, nodeids: list[str], config: Config
) -> tuple[dict | None, dict]:
    """One BIG neutrality judgement of the current verifier tests (persisted by content
    hash). Returns (decision or None when no LLM, note)."""
    verifier = task_dir / "verifier"
    contracts = _contracts(task_dir / "solution", c.source_files, c.touched_functions, config)
    prompt = neutrality_prompt(
        c, _test_sources(verifier, nodeids), contracts, _new_names(c, inp.repo)
    )
    key = _cache_key("neutrality", c.sha, prompt)
    note: dict = {"key": key}
    decision = (inp.decisions or {}).get(key)
    if decision is None:
        if inp.llm is None:
            return None, note
        decision = inp.llm.complete_json(
            NEUTRALITY_STEP, [{"role": "user", "content": prompt}], NEUTRALITY_SCHEMA
        )
    else:
        note["reused"] = True
    if inp.decisions is not None:
        inp.decisions[key] = decision
    note["decision"] = decision
    return decision, note


def _neutrality(
    c: H.HistoryCandidate, inp: BuildInputs, task_dir: Path, nodeids: list[str], config: Config
) -> tuple[list[str], dict]:
    """BIG neutrality check of the commit's own tests; when flagged, one bounded agent
    rewrite (audited) followed by ONE re-check of the rewritten tests. Returns (nodeids,
    note)."""
    hc = config.history
    verifier = task_dir / "verifier"
    new_names = _new_names(c, inp.repo)
    decision, note = _neutrality_decision(c, inp, task_dir, nodeids, config)
    note.update({"step": NEUTRALITY_STEP, "checked": decision is not None})
    if decision is None or decision["neutral"]:
        return nodeids, note
    files = sorted({n.split("::", 1)[0] for n in nodeids})
    goal = (
        f"The following verifier tests were flagged as not implementation-neutral:\n"
        f"issues: {'; '.join(decision['issues'])}\nflagged: "
        f"{', '.join(decision['flagged_tests'])}\n\nRewrite ONLY those tests in "
        f"{', '.join(files)} so they assert the same behavior via the public interface "
        f"(private helpers never; identifiers introduced by the change "
        f"({', '.join(new_names) or '(none)'}) only through the getattr convention). "
        f"Keep test names. Run `python -m pytest -q {' '.join(files)}` until the tests pass."
    )
    note["rewrite"] = _rewrite_verifier(c, inp, task_dir, files, goal, "neutrality_rewrite", config)
    nodeids = _existing_nodeids(verifier, nodeids)  # a rewrite may drop tests
    if (
        note["rewrite"]["outcome"] in ("rewritten", "reused")
        and hc.neutrality_recheck_after_rewrite
    ):
        recheck, note["recheck"] = _neutrality_decision(c, inp, task_dir, nodeids, config)
        if recheck is not None and not recheck["neutral"]:
            note["rewrite"]["outcome"] = "still-not-neutral"
    return nodeids, note


def _rewrite_verifier(
    c: H.HistoryCandidate,
    inp: BuildInputs,
    task_dir: Path,
    files: list[str],
    goal: str,
    kind: str,
    config: Config,
) -> dict:
    """ONE bounded agent rewrite of verifier ``files`` (audited, cached by content hash,
    outcome persisted, per-build-step budgets ``max_neutrality_rewrites_per_repo`` and
    ``max_agent_runs_per_repo``). Outcomes: rewritten | reused | unchanged | max-turns |
    disabled | budget-exhausted | no_llm."""
    hc = config.history
    verifier = task_dir / "verifier"
    key = _cache_key(kind, c.sha, goal)
    note: dict = {"kind": kind, "key": key, "attempts": 0}
    cache = _agent_cache(inp, key)
    prior = (inp.decisions or {}).get(key)
    if cache and cache.is_dir() and hc.reuse_agent_outputs and any(cache.rglob("*.py")):
        for rel in files:
            if (cache / rel).is_file():
                _write_rel(verifier, rel, read_source(cache / rel))
        note.update({"outcome": "reused", "reused": True})
        return note
    if prior is not None and hc.reuse_agent_outputs:
        note.update({"outcome": prior["outcome"], "reused": True})
        return note
    if hc.neutrality_rewrite_max_attempts < 1:
        note["outcome"] = "disabled"
        return note
    if inp.llm is None:
        note["outcome"] = "no_llm"
        return note
    if inp.counters.get("rewrites", 0) >= hc.max_neutrality_rewrites_per_repo:
        note["outcome"] = "budget-exhausted"
        return note
    inp.counters["rewrites"] = inp.counters.get("rewrites", 0) + 1
    for attempt in range(1, hc.neutrality_rewrite_max_attempts + 1):
        note["attempts"] = attempt
        kept, run_note = _run_agent(
            inp,
            NEUTRALITY_STEP,
            REWRITE_AGENT_SYSTEM,
            goal,
            task_dir / "solution",
            verifier,
            files,
            config,
        )
        note.update(run_note)
        note["outcome"] = "rewritten" if kept else "unchanged"
        _audit(
            inp.audit_dir,
            {
                "stage": NEUTRALITY_STEP,
                "goal": goal[: config.tasks.audit_goal_chars],
                "task": task_id_for(c, config),
                **note,
            },
        )
        if kept:
            if cache:
                for rel in kept:
                    _write_rel(cache, rel, read_source(verifier / rel))
            break
    if inp.decisions is not None:
        inp.decisions[key] = {"outcome": note["outcome"]}
    return note


# --- build ----------------------------------------------------------------------------


def build_history_task(
    c: H.HistoryCandidate, inp: BuildInputs, tasks_root: Path, config: Config = DEFAULT
) -> HistoryBuild:
    """Build one history task folder. Build-time gates (in-container) reject with a
    reason instead of producing a task the harness would fail for a knowable cause."""
    tc, hc = config.tasks, config.history
    adapter = PythonAdapter(config=config)
    task_id = task_id_for(c, config)
    task_dir = tasks_root / inp.repo_name / task_id
    if task_dir.exists():
        shutil.rmtree(task_dir)
    task_dir.mkdir(parents=True)
    notes: dict = {"verifier_source": None}

    def reject(reason: str) -> HistoryBuild:
        shutil.rmtree(task_dir, ignore_errors=True)
        return HistoryBuild(task_id, None, reason, notes)

    archive_tree(inp.repo, c.input_sha, task_dir / "input")
    archive_tree(inp.repo, c.sha, task_dir / "solution")
    names = overlay_files(inp.repo, config)
    notes["overlay"] = {
        "input": overlay(inp.repo, task_dir / "input", names),
        "solution": overlay(inp.repo, task_dir / "solution", names),
    }
    verifier = task_dir / "verifier"
    verifier.mkdir()

    by_file = commit_test_nodeids(c, inp.repo)
    if by_file:
        notes["verifier_source"] = "commit-tests"
        # every touched test file at commit state (helpers/fixtures too), changed nodeids only
        _copy_commit_tests(c, inp.repo, verifier, [f for f in c.test_files if f.endswith(".py")])
        nodeids = sorted(n for ns in by_file.values() for n in ns)
    elif hc.verifier_agent_when_no_tests:
        notes["verifier_source"] = "agent-authored"
        nodeids, notes["verifier_agent"] = _verifier_from_agent(c, inp, task_dir, config)
        if not nodeids:
            return reject("no-verifier-tests(agent)")
    else:
        return reject("no-tests-in-commit")

    violations = static_gate_violations(task_dir / "input", verifier, config)
    if violations:
        detail = ", ".join(sorted({v["import"] for v in violations}))
        missing = sorted(
            {v["import"] for v in violations if v["reason"] == "symbol-missing-in-input"}
        )
        if (
            len(missing) < len({v["import"] for v in violations})
            or not hc.allow_new_symbol_features
        ):
            return reject(f"verifier-imports-non-public-or-missing({detail})")
        files = sorted({v["file"] for v in violations})
        # A tree that cannot collect in the current image is env-drift: check it BEFORE
        # spending an agent on the rewrite (toolz: two 2013-era rewrites were wasted).
        probe = run_tree(
            task_dir, "solution", adapter.verifier_command(nodeids), inp.image_tag, config
        )
        drift = _drift_reasons(
            probe, sorted(str(p.relative_to(verifier)) for p in verifier.rglob("*.py")), config
        )
        if drift or not probe["outcomes"]:
            return reject(f"env-drift({', '.join(drift) or 'no tests ran'})")
        goal = (
            f"These verifier tests import names that do not exist BEFORE the change: "
            f"{', '.join(missing)}. {NEW_SYMBOL_RULE} Rewrite ONLY the affected imports and "
            f"tests in {', '.join(files)} accordingly, keeping test names and intent. Run "
            f"`python -m pytest -q {' '.join(files)}` until the tests pass."
        )
        notes["new_symbol_rewrite"] = _rewrite_verifier(
            c, inp, task_dir, files, goal, "new_symbol_rewrite", config
        )
        outcome = notes["new_symbol_rewrite"]["outcome"]
        if outcome not in ("rewritten", "reused"):
            return reject(f"verifier-imports-symbol-missing-in-input({detail}; rewrite:{outcome})")
        if static_gate_violations(task_dir / "input", verifier, config):
            return reject(f"verifier-imports-symbol-missing-in-input({detail}; rewrite:unfixed)")
        nodeids = _existing_nodeids(verifier, nodeids)

    verifier_files = sorted(str(p.relative_to(verifier)) for p in verifier.rglob("*.py"))
    # Solution first: a tree that cannot collect in the current image is env-drift, not a
    # property of the change.
    on_solution = run_tree(
        task_dir, "solution", adapter.verifier_command(nodeids), inp.image_tag, config
    )
    drift = _drift_reasons(on_solution, verifier_files, config)
    if drift or not on_solution["outcomes"]:
        return reject(f"env-drift({', '.join(drift) or 'no tests ran'})")
    passing_on_solution = {n for n, o in on_solution["outcomes"].items() if o == "passed"}
    notes["dropped_failing_on_solution"] = sorted(set(nodeids) - passing_on_solution)
    nodeids = sorted(set(nodeids) & passing_on_solution)
    if not nodeids:
        return reject("verifier-fails-on-solution")

    on_input = run_tree(task_dir, "input", adapter.verifier_command(nodeids), inp.image_tag, config)
    in_reasons = _reasons(on_input, verifier_files, config)
    invalid = sorted({r["reason"] for r in in_reasons.values() if not r["valid"]})
    if invalid:
        return reject(f"verifier-on-input:{','.join(invalid)}")
    failing_on_input = {n for n, o in on_input["outcomes"].items() if o in ("failed", "error")}
    notes["dropped_passing_on_input"] = sorted(set(nodeids) - failing_on_input)
    nodeids = sorted(set(nodeids) & failing_on_input)
    if len(nodeids) < config.harness.min_failing_tests:
        return reject(f"{notes['verifier_source']}-pass-on-input")

    if notes["verifier_source"] == "commit-tests" and hc.neutrality_check:
        nodeids, notes["neutrality"] = _neutrality(c, inp, task_dir, nodeids, config)
        if notes["neutrality"].get("rewrite", {}).get("outcome") in ("rewritten", "reused"):
            on_solution = run_tree(
                task_dir, "solution", adapter.verifier_command(nodeids), inp.image_tag, config
            )
            on_input = run_tree(
                task_dir, "input", adapter.verifier_command(nodeids), inp.image_tag, config
            )
            ok_sol = {n for n, o in on_solution["outcomes"].items() if o == "passed"}
            bad_in = {n for n, o in on_input["outcomes"].items() if o in ("failed", "error")}
            invalid = sorted(
                {
                    r["reason"]
                    for r in _reasons(on_input, verifier_files, config).values()
                    if not r["valid"]
                }
            )
            nodeids = sorted(set(nodeids) & ok_sol & bad_in)
            if invalid or len(nodeids) < config.harness.min_failing_tests:
                return reject("neutrality-rewrite-failed")
        elif not notes["neutrality"].get("decision", {"neutral": True})["neutral"]:
            outcome = notes["neutrality"].get("rewrite", {}).get("outcome", "no-rewrite")
            return reject(f"verifier-not-implementation-neutral(rewrite:{outcome})")

    verifier_cmd = adapter.verifier_command(nodeids)
    run_sh = verifier / tc.verifier_run_script
    run_sh.write_text(f'#!/bin/sh\nset -e\ncd "$(dirname "$0")"\n{verifier_cmd}\n')
    run_sh.chmod(0o755)

    collateral = _collateral(c, inp, task_dir, adapter, config, notes)
    contracts = _contracts(task_dir / "input", c.source_files, c.touched_functions, config)
    files_scope = files_in_scope(
        {*c.source_files, *c.test_files, *(n.split("::", 1)[0] for n in nodeids)},
        set(c.modules),
        inp.graph,
    )
    (task_dir / tc.golden_solution).write_text(_golden(c, inp.repo))
    task = {
        "id": task_id,
        "title": c.message.splitlines()[0][: tc.title_max_chars],
        "repo": inp.repo_name,
        "base_sha": inp.base_sha,
        "provenance": {
            "type": "history",
            "commit": c.sha,
            "parent": c.input_sha,
            "pr_number": c.pr_number,
            "is_merge": c.is_merge,
            "message": c.message,
            "files": c.files_changed,
            "source_files": c.source_files,
            "touched_functions": c.touched_functions,
            "modules": c.modules,
            "verifier_source": notes["verifier_source"],
            "classification": c.classify,
        },
        "difficulty": None,
        "difficulty_rationale": None,
        "files_in_scope": files_scope,
        "instruction": _instruction(c, contracts, verifier_cmd, nodeids, config),
        "instruction_status": tc.history_instruction_status_template,
        "verifier_cmd": verifier_cmd,
        "verifier_tests": nodeids,
        "verifier_files": sorted(
            str(p.relative_to(verifier)) for p in verifier.rglob("*") if p.is_file()
        ),
        "verifier_visibility": config.harness.verifier_visibility,
        "verifier_on_input": {k: on_input[k] for k in ("exit_code", "n_failing", "n_passing")},
        "verifier_on_solution": {
            k: on_solution[k] for k in ("exit_code", "n_failing", "n_passing")
        },
        "verifier_agent": notes.get("verifier_agent"),
        "neutrality": notes.get("neutrality"),
        "new_symbol_rewrite": notes.get("new_symbol_rewrite"),
        "dropped_tests": {
            "failing_on_solution": notes.get("dropped_failing_on_solution", []),
            "passing_on_input": notes.get("dropped_passing_on_input", []),
        },
        "overlay_files": notes["overlay"],
        "collateral": collateral,
        "image_tag": inp.image_tag,
        "image_digest": inp.image_digest,
    }
    (task_dir / tc.task_json).write_text(json.dumps(task, indent=2, sort_keys=True) + "\n")
    (task_dir / config.harness.evidence_dirname).mkdir(exist_ok=True)
    return HistoryBuild(task_id, task_dir, None, notes)


def _collateral(
    c: H.HistoryCandidate,
    inp: BuildInputs,
    task_dir: Path,
    adapter: PythonAdapter,
    config: Config,
    notes: dict,
) -> dict | None:
    """Collateral baseline = tests passing on input/ (one full-suite container run), so
    the check compares the commit against ITS parent, not against HEAD's suite."""
    report = config.baseline.report_filename
    quarantined = inp.baseline.get("quarantined") or []
    cmd = adapter.reporting_command(Path("."), report, quarantined)
    if not config.history.collateral_baseline_from_input:
        results = inp.baseline.get("results") or {}
        passing = sorted(t for t, r in results.items() if r.get("status") == "pass")
        return {"cmd": cmd, "report": report, "baseline_passing": passing} if passing else None
    with fresh_workdir(task_dir / "input") as work:
        result = run_in_container(work, cmd, inp.image_tag)
        path = work / report
        data = json.loads(path.read_text()) if path.is_file() else None
    results = adapter.parse_test_report_data(data) if data else {}
    passing = sorted(t for t, r in results.items() if r["status"] == "pass")
    # Tests the commit itself removed/renamed in the test files it touched cannot run on
    # solution/; they are not collateral.
    removed = _tests_removed_by_commit(c, inp.repo, passing)
    passing = [t for t in passing if t not in removed]
    notes["collateral_baseline"] = {
        "exit_code": result.exit_code,
        "report_present": data is not None,
        "passing": len(passing),
        "removed_by_commit": removed,
        "total": len(results),
    }
    if not passing:
        return None
    return {"cmd": cmd, "report": report, "baseline_passing": passing, "source": "input-run"}


def _tests_removed_by_commit(c: H.HistoryCandidate, repo: Path, nodeids: list[str]) -> list[str]:
    out: list[str] = []
    for rel in c.test_files:
        after = H.show(repo, c.sha, rel)
        names = set(test_nodeid_suffixes(after)) if after is not None else set()
        for n in nodeids:
            if n.startswith(rel + "::") and n.split("::", 1)[1].split("[")[0] not in names:
                out.append(n)
    return sorted(out)


def _golden(c: H.HistoryCandidate, repo: Path) -> str:
    patch = H.diff(repo, c.input_sha, c.sha)
    return (
        f"# Golden solution: {c.short}\n\n"
        f"Commit `{c.sha}` (parent `{c.input_sha}`): {c.message}\n\n"
        "The historical change, applied to `input/` gives `solution/` exactly (hygiene "
        "overlay files aside).\n\n"
        "```diff\n" + patch + ("\n" if not patch.endswith("\n") else "") + "```\n\n"
        "<!-- TODO-S5b: LLM-authored 'why correct' rationale -->\n"
    )


def _instruction(
    c: H.HistoryCandidate, contracts: str, cmd: str, nodeids: list[str], config: Config
) -> str:
    summary = (c.classify or {}).get("behavior_change_summary") or "(see the verifier tests)"
    k = config.tasks.instruction_tests_listed
    tests = "\n".join(f"- `{n}`" for n in nodeids[:k]) + ("\n- ..." if len(nodeids) > k else "")
    hidden = config.harness.verifier_visibility == "hidden"
    where = (
        "Hidden tests check the behavior." if hidden else "The verifier tests are in `verifier/`."
    )
    return (
        f"# {c.message.splitlines()[0][: config.tasks.title_max_chars]}\n\n"
        f"## Goal\n{summary}\n\n"
        f"## Contract (as in the current tree)\n{contracts}\n\n"
        f"## Observable behavior\n{where}\nTests that exercise it:\n{tests}\n\n"
        f"## Constraints\n- Change only what the behavior requires within "
        f"{', '.join(f'`{f}`' for f in c.source_files)}; keep the public API otherwise unchanged.\n"
        f"- Do not modify or delete tests; the canonical verifier is re-applied before judging.\n\n"
        f"## How success is measured\n```\n{cmd}\n```\n"
    )
