"""Excision task construction (DESIGN 5.3 build + 5.6 folder format).

tasks/<repo>/<task_id>/{task.json, input/, solution/, verifier/, goldenSolution.md, evidence/}
- solution/ = the current transformed repo tree (no .git)
- input/    = same tree with the target's body spliced to ``excision_body``
- verifier/ = the covering test files (repo-relative paths, so the harness can copy the
  directory over any workdir) + conftest ancestors + run.sh
"""

from __future__ import annotations

import difflib
import json
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from pipeline.agent.loop import Agent
from pipeline.agent.tools import ToolContext, concrete_tools, graph_tools
from pipeline.config import DEFAULT, Config
from pipeline.docker.runner import fresh_workdir, run_in_container
from pipeline.ecosystems.python import PythonAdapter
from pipeline.ecosystems.source_ops import (
    count_assertions,
    excise_function,
    read_source,
    test_functions_in,
    write_source,
)
from pipeline.tasks.excision import Candidate

VERIFIER_AGENT_STEP = "p3.build.verifier_agent"

VERIFIER_AGENT_SYSTEM = (
    "You are a test author. Write focused pytest edge-case tests for ONE function of "
    "this repository. Use only the public API as the existing tests do. Run the tests "
    "with the `run` tool until they pass. Only the single file you were told to create "
    "is kept; every other change is discarded. Reply with a one-line summary when done."
)


@dataclass
class BuildInputs:
    repo: Path  # output/<repo>/repo
    repo_name: str
    base_sha: str
    image_tag: str
    image_digest: str
    graph: dict
    baseline: dict  # hygiene/baseline.json
    knowledge_dir: Path
    audit_dir: Path
    llm: object | None = None  # LLMClient; None disables the top-up agent
    cache_dir: Path | None = None  # agent-authored verifier files, keyed by content hash
    decisions: dict | None = None  # persisted LLM decisions (content hash -> decision)
    counters: dict = field(default_factory=dict)  # per-build-step budgets (agent runs)
    transcripts_dir: Path = Path("transcripts")  # from the LLM client (agent trajectories)


def task_id_for(c: Candidate, config: Config = DEFAULT) -> str:
    within = c.qualname[len(c.module) + 1 :]
    return f"{config.tasks.excision_id_prefix}-{c.module}-{within}"


def build_task(c: Candidate, inp: BuildInputs, tasks_root: Path, config: Config = DEFAULT) -> Path:
    """Build one excision task folder; returns its path. Raises ExciseError when the
    target cannot be spliced (caller records the reject reason)."""
    tc = config.tasks
    adapter = PythonAdapter(config=config)
    original = read_source(inp.repo / c.file)
    qualpath = c.qualname[len(c.module) + 1 :].split(".")
    excised = excise_function(
        original,
        qualpath,
        config.excision.excision_body,
        keep_docstring=not config.excision.strip_docstring,
    )
    task_dir = tasks_root / inp.repo_name / task_id_for(c, config)
    if task_dir.exists():
        shutil.rmtree(task_dir)
    task_dir.mkdir(parents=True)

    ignore = shutil.ignore_patterns(*tc.tree_ignore)
    shutil.copytree(inp.repo, task_dir / "solution", ignore=ignore)
    shutil.copytree(inp.repo, task_dir / "input", ignore=ignore)
    write_source(task_dir / "input" / c.file, excised.source)

    verifier = task_dir / "verifier"
    test_files = sorted({n.split("::", 1)[0] for n in c.covering_tests})
    for rel in test_files:
        _copy_rel(inp.repo, verifier, rel)
        if config.excision.copy_conftests:
            for anc in Path(rel).parents:
                conftest = anc / "conftest.py"
                if (inp.repo / conftest).is_file():
                    _copy_rel(inp.repo, verifier, str(conftest))
    nodeids = list(c.covering_tests)
    assertions = _assertions_touching(inp.repo, nodeids)
    agent_note = None
    if assertions < config.excision.min_assertions_touching_fn and inp.llm is not None:
        added, agent_note = _top_up_tests(c, inp, task_dir, test_files[0], config)
        nodeids = sorted({*nodeids, *added})
    # One container run of the verifier on input/ at build time: records the fail-before
    # shape and drops top-up tests that do not fail on input (they would not discriminate).
    on_input = _verifier_on_input(
        task_dir, adapter.verifier_command(nodeids), adapter, inp.image_tag, config
    )
    if agent_note and agent_note.get("outcome") == "added":
        keep = {
            n for n in nodeids if on_input["outcomes"].get(n) != "passed" or n in c.covering_tests
        }
        agent_note["dropped_passing_on_input"] = sorted(set(nodeids) - keep)
        nodeids = sorted(keep)
    verifier_cmd = adapter.verifier_command(nodeids)
    run_sh = verifier / tc.verifier_run_script
    # verifier/ is overlaid onto a workdir root, so run.sh runs from its own directory.
    run_sh.write_text(f'#!/bin/sh\nset -e\ncd "$(dirname "$0")"\n{verifier_cmd}\n')
    run_sh.chmod(0o755)

    (task_dir / tc.golden_solution).write_text(_golden(c, original, excised.source, config))
    files_in_scope = _files_in_scope(c, inp.graph, test_files)
    task = {
        "id": task_id_for(c, config),
        "title": f"Reimplement {c.qualname}",
        "repo": inp.repo_name,
        "base_sha": inp.base_sha,
        "provenance": {
            "type": "excision",
            "target": c.qualname,
            "file": c.file,
            "span": [c.line, c.end_line],
            "excised_lines": [excised.body_start, excised.body_end],
            "docstring_kept": excised.kept_docstring,
        },
        "difficulty": None,
        "difficulty_rationale": None,
        "files_in_scope": files_in_scope,
        "instruction": _instruction(c, verifier, nodeids, verifier_cmd, config),
        "instruction_status": tc.instruction_status_template,
        "verifier_cmd": verifier_cmd,
        "verifier_tests": nodeids,
        "verifier_files": sorted(
            str(p.relative_to(verifier)) for p in verifier.rglob("*") if p.is_file()
        ),
        "verifier_visibility": config.harness.verifier_visibility,
        "assertions_touching_fn": assertions,
        "verifier_on_input": {k: v for k, v in on_input.items() if k != "outcomes"},
        "verifier_agent": agent_note,
        "collateral": _collateral(inp.baseline, adapter, config),
        "image_tag": inp.image_tag,
        "image_digest": inp.image_digest,
    }
    (task_dir / tc.task_json).write_text(json.dumps(task, indent=2, sort_keys=True) + "\n")
    (task_dir / config.harness.evidence_dirname).mkdir(exist_ok=True)
    return task_dir


def _verifier_on_input(
    task_dir: Path, cmd: str, adapter: PythonAdapter, image: str, config: Config
) -> dict:
    report_rel = config.harness.report_filename
    with fresh_workdir(task_dir / "input") as work:
        shutil.copytree(task_dir / "verifier", work, dirs_exist_ok=True)
        result = run_in_container(work, adapter.with_report(cmd, report_rel), image)
        path = work / report_rel
        report = json.loads(path.read_text()) if path.is_file() else {}
    summary = report.get("summary", {})
    return {
        "exit_code": result.exit_code,
        "n_failing": summary.get("failed", 0) + summary.get("error", 0),
        "n_passing": summary.get("passed", 0),
        "outcomes": {t["nodeid"]: t.get("outcome") for t in report.get("tests", [])},
    }


def _copy_rel(repo: Path, dest_root: Path, rel: str) -> None:
    dest = dest_root / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(repo / rel, dest)


def _assertions_touching(repo: Path, nodeids: list[str]) -> int:
    by_file: dict[str, set[str]] = {}
    for n in nodeids:
        path, _, rest = n.partition("::")
        by_file.setdefault(path, set()).add(rest.rsplit("::", 1)[-1])
    return sum(count_assertions(read_source(repo / f), names) for f, names in by_file.items())


def _collateral(baseline: dict, adapter: PythonAdapter, config: Config) -> dict | None:
    results = baseline.get("results") or {}
    passing = sorted(t for t, r in results.items() if r.get("status") == "pass")
    if not passing:
        return None
    report = config.baseline.report_filename
    return {
        "cmd": adapter.reporting_command(Path("."), report, baseline.get("quarantined") or []),
        "report": report,
        "baseline_passing": passing,
    }


def _files_in_scope(c: Candidate, graph: dict, test_files: list[str]) -> list[str]:
    return files_in_scope({c.file, *test_files}, {c.module}, graph)


def files_in_scope(files: set[str], modules: set[str], graph: dict) -> list[str]:
    """Touched files + their direct importers (repo graph ``imports`` edges)."""
    out = set(files)
    node_file = {n["id"]: n["file"] for n in graph.get("nodes", [])}
    for e in graph.get("edges", []):
        if e["type"] == "imports" and e["target"] in modules and e["source"] in node_file:
            out.add(node_file[e["source"]])
    return sorted(out)


def _golden(c: Candidate, original: str, excised: str, config: Config) -> str:
    diff = "".join(
        difflib.unified_diff(
            excised.splitlines(keepends=True),
            original.splitlines(keepends=True),
            fromfile=f"input/{c.file}",
            tofile=f"solution/{c.file}",
            n=3,
        )
    )
    return (
        f"# Golden solution: {c.qualname}\n\n"
        f"Restores the original body of `{c.signature}` in `{c.file}` "
        f"(lines {c.line}-{c.end_line}); the excised input raises "
        f"`{config.excision.excision_body}` in its place.\n\n"
        "```diff\n" + diff + "```\n\n"
        "Why correct: the solution is the repository's own implementation, which passes "
        "the verifier tests and the full baseline suite (see evidence/).\n\n"
        "<!-- TODO-S5: LLM-authored 'why correct' rationale -->\n"
    )


def _examples(c: Candidate, verifier: Path, nodeids: list[str], limit: int) -> list[str]:
    name = c.qualname.rsplit(".", 1)[-1]
    out: list[str] = []
    for rel in sorted({n.split("::", 1)[0] for n in nodeids}):
        for line in read_source(verifier / rel).splitlines():
            s = line.strip()
            if s.startswith("assert") and name in s and len(s) < 160:
                out.append(s)
            if len(out) >= limit:
                return out
    return out


def _instruction(c: Candidate, verifier: Path, nodeids: list[str], cmd: str, config: Config) -> str:
    kind = "method" if c.is_method else "function"
    contract = (
        c.docstring.strip()
        if c.docstring and not config.excision.strip_docstring
        else ("(no docstring; the contract is defined by the verifier tests)")
    )
    examples = _examples(c, verifier, nodeids, config.instruction.examples_from_verifier)
    ex_block = "\n".join(f"- `{e}`" for e in examples) or "- (see the verifier tests listed below)"
    k = config.tasks.instruction_tests_listed
    tests = "\n".join(f"- `{n}`" for n in nodeids[:k]) + ("\n- ..." if len(nodeids) > k else "")
    return (
        f"# Reimplement `{c.qualname}`\n\n"
        f"## Goal\n"
        f"The {kind} `{c.signature}` in `{c.file}` (module `{c.module}`) has had its body "
        f'removed; it currently raises `NotImplementedError("excised")`. Reimplement it so '
        f"the behavior below is restored.\n\n"
        f"## Contract\n{contract}\n\n"
        f"## Observable behavior (from the verifier tests)\n{ex_block}\n\n"
        f"Tests that exercise it:\n{tests}\n\n"
        f"## Constraints\n"
        f"- Edit `{c.file}`; keep the signature and the public API unchanged.\n"
        f"- Do not modify or delete tests; the canonical verifier is re-applied before judging.\n"
        f"- Any implementation that satisfies the tests is acceptable.\n\n"
        f"## How success is measured\n```\n{cmd}\n```\n"
    )


def _top_up_tests(
    c: Candidate, inp: BuildInputs, task_dir: Path, sibling_test: str, config: Config
) -> tuple[list[str], dict]:
    """Bounded BIG agent adds edge-case tests for the target into ONE new verifier file.
    Audited to agent_actions.jsonl. Returns (added nodeids, audit note)."""
    name = c.qualname.rsplit(".", 1)[-1]
    rel = str(Path(sibling_test).parent / f"test_excision_{name}.py")
    added: list[str] = []
    note = {"step": VERIFIER_AGENT_STEP, "file": rel, "attempts": 0, "outcome": "not_run"}
    for attempt in range(1, config.excision.verifier_agent_max_attempts + 1):
        note["attempts"] = attempt
        with tempfile.TemporaryDirectory(prefix="bench-agent-") as tmp:
            work = Path(tmp) / "repo"
            shutil.copytree(task_dir / "solution", work)
            tctx = ToolContext(
                work,
                image=inp.image_tag,
                knowledge_dir=inp.knowledge_dir,
                repo_root=inp.repo,
                config=config,
            )
            agent = Agent(
                inp.llm,
                VERIFIER_AGENT_STEP,
                VERIFIER_AGENT_SYSTEM,
                [*concrete_tools(tctx), *graph_tools(tctx)],
                tctx.files_changed,
                transcripts_dir=inp.transcripts_dir,
            )
            goal = (
                f"Create `{rel}` with 3-5 pytest edge-case tests for `{c.qualname}` "
                f"(`{c.signature}` in `{c.file}`). Import it exactly as `{sibling_test}` "
                f"does. Run `python -m pytest -q {rel}` and make sure every test passes."
            )
            result = agent.run(goal)
            new_file = work / rel
            names = test_functions_in(read_source(new_file)) if new_file.is_file() else []
            if names:
                _copy_rel(work, task_dir / "verifier", rel)
                added = sorted(f"{rel}::{n}" for n in names)
            note.update(
                {
                    "outcome": "added" if names else "no_tests",
                    "tests_added": len(names),
                    "files_changed": result.files_changed,
                    "summary": result.summary[: config.tasks.audit_summary_chars],
                }
            )
        _audit(
            inp.audit_dir,
            {
                "stage": VERIFIER_AGENT_STEP,
                "goal": goal[: config.tasks.audit_goal_chars],
                "task": task_id_for(c, config),
                **note,
            },
        )
        if names:
            break
    return added, note


def _audit(audit_dir: Path, record: dict) -> None:
    audit_dir.mkdir(parents=True, exist_ok=True)
    with (audit_dir / "agent_actions.jsonl").open("a") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")
