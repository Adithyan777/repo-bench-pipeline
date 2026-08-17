"""Step 3.6: generate tests, gated by mutation kill.

Rank functions from an in-container coverage run + AST index (no knowledge artifacts);
a BIG agent writes only the generated test file per module; each target must pass on
real code AND kill >= testgen.min_mutants_killed mutants, else bounded retry / drop.
Agent outcomes are cached by content hash; generated tests get their own pipeline commit.
"""

from __future__ import annotations

import ast
import hashlib
import json
import math
import os
import shutil
import subprocess
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from pipeline.agent.loop import Agent
from pipeline.agent.tools import ToolContext, concrete_tools
from pipeline.docker.runner import fresh_workdir, run_in_container
from pipeline.ecosystems.source_ops import read_source, write_source
from pipeline.hygiene.context import HygieneContext, append_agent_action
from pipeline.hygiene.mutate import function_mutants
from pipeline.knowledge.indexes import run_coverage
from pipeline.log import log
from pipeline.state import hash_inputs

WRITE_STEP = "p1.testgen.write_tests_agent"
RETRY_STEP = "p1.testgen.mutation_retry_agent"
PROMPT_VERSION = "testgen.3"  # bump when the prompts/gate change: keys of persisted decisions

_SYSTEM = (
    "You write pytest tests for a Python library. You may create or edit ONLY the single "
    "test file you are told to write; never touch the library source or any other file. "
    "Write focused, deterministic tests that assert concrete behavior (exact return values, "
    "raised exceptions, boundaries) of the target functions -- not smoke tests. The target "
    "functions' source is already in your instructions: do not spend turns exploring the "
    "module; write the file within your first few turns, then use the run tool to execute "
    "it and iterate. A run that ends without the file written is a failure."
)


# --- ranking (deterministic, no container beyond the one coverage run) ---------


def _span_lines(fn: dict) -> int:
    return fn["end_line"] - fn["line"] + 1


def _is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


def _uncovered(fn: dict, cov_files: dict) -> tuple[float | None, int]:
    """(uncovered_ratio, measurable_lines). ratio None means no executable lines."""
    span = set(range(fn["line"], fn["end_line"] + 1))
    fdata = cov_files.get(fn["file"])
    if not fdata:
        return 1.0, _span_lines(fn)  # file never imported by any test
    executed = set(fdata.get("executed_lines", [])) & span
    missing = set(fdata.get("missing_lines", [])) & span
    measurable = executed | missing
    if not measurable:
        return None, 0
    return len(missing) / len(measurable), len(measurable)


def _skip_reason(fn: dict, measurable: int, config) -> str | None:
    tg = config.testgen
    if fn.get("is_method") and _is_dunder(fn["name"]):
        return "dunder" if tg.skip_dunder else None if measurable else "no_executable_lines"
    if tg.skip_dunder and _is_dunder(fn["name"]):
        return "dunder"
    if tg.skip_init_reexports and fn["file"].endswith("__init__.py"):
        return "init_reexport"
    if tg.skip_cli_main and (fn["name"] == "main" or fn["module"].endswith(".__main__")):
        return "cli_main"
    if _span_lines(fn) < tg.min_function_lines:
        return "too_small"
    if not fn["is_public"] and fn["complexity"] < tg.private_min_complexity:
        return "private_low_complexity"
    if measurable == 0:
        return "no_executable_lines"
    return None


def _score(fn: dict, ratio: float, config) -> float:
    bonus = config.testgen.public_bonus if fn["is_public"] else 1.0
    complexity_factor = 1 + fn["complexity"] / config.testgen.complexity_weight
    return ratio * math.log(1 + _span_lines(fn)) * complexity_factor * bonus


def rank_targets(functions: list[dict], cov_files: dict, config) -> dict:
    """Score every function; pick top_k_modules x top_n_functions. Returns the full ranking
    with scores and skip reasons."""
    tg = config.testgen
    rows: list[dict] = []
    for fn in functions:
        ratio, measurable = _uncovered(fn, cov_files)
        skip = _skip_reason(fn, measurable, config) if ratio is not None else "no_executable_lines"
        score = _score(fn, ratio, config) if ratio is not None and skip is None else 0.0
        rows.append(
            {
                "qualname": fn["qualname"],
                "module": fn["module"],
                "file": fn["file"],
                "line": fn["line"],
                "end_line": fn["end_line"],
                "lines": _span_lines(fn),
                "complexity": fn["complexity"],
                "is_public": fn["is_public"],
                "uncovered_ratio": None if ratio is None else round(ratio, 3),
                "score": round(score, 4),
                "skip_reason": skip,
                "selected": False,
            }
        )
    # score > 0 <=> some lines uncovered; fully-covered functions are skipped.
    candidates = [r for r in rows if r["skip_reason"] is None and r["score"] > 0]
    by_module: dict[str, list[dict]] = {}
    for r in candidates:
        by_module.setdefault(r["module"], []).append(r)
    module_rank = sorted(
        ((m, sum(r["score"] for r in rs)) for m, rs in by_module.items()),
        key=lambda kv: (-kv[1], kv[0]),
    )
    selected_modules = module_rank[: tg.top_k_modules]
    modules_out: list[dict] = []
    selected_ids: set[str] = set()
    for module, mscore in selected_modules:
        picks = sorted(by_module[module], key=lambda r: (-r["score"], r["qualname"]))
        picks = picks[: tg.top_n_functions_per_module]
        for r in picks:
            r["selected"] = True
            selected_ids.add(r["qualname"])
        modules_out.append(
            {
                "module": module,
                "score": round(mscore, 4),
                "targets": [r["qualname"] for r in picks],
            }
        )
    return {
        "functions": sorted(rows, key=lambda r: r["qualname"]),
        "modules": modules_out,
        "selected": sorted(selected_ids),
    }


# --- generated-test location --------------------------------------------------


def _primary_test_dir(repo: Path, config) -> Path | None:
    # Exclude generated tests so the location is stable across reruns.
    marker = config.testgen.generated_subdir
    dirs: Counter[Path] = Counter()
    for pattern in ("test_*.py", "*_test.py"):
        for p in repo.rglob(pattern):
            rel = p.relative_to(repo)
            if ".git" not in p.parts and marker not in rel.parts:
                dirs[p.parent] += 1
    if not dirs:
        return None
    return max(dirs, key=lambda d: (dirs[d], str(d)))


def generated_dir(repo: Path, config) -> Path:
    primary = _primary_test_dir(repo, config)
    if primary is not None and config.testgen.place_beside_existing_tests:
        return primary / config.testgen.generated_subdir
    return repo / config.testgen.generated_tests_dir


def _ensure_dir(repo: Path, gen_dir: Path) -> None:
    gen_dir.mkdir(parents=True, exist_ok=True)
    parent = gen_dir.parent
    if (parent / "__init__.py").exists() and not (gen_dir / "__init__.py").exists():
        (gen_dir / "__init__.py").write_text("")


def _module_test_file(module: str) -> str:
    return f"test_{module.replace('.', '_')}.py"


# --- prompt facts -------------------------------------------------------------


def _imports_block(source: str) -> str:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ""
    lines = source.splitlines()
    out = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            out.extend(lines[node.lineno - 1 : (node.end_lineno or node.lineno)])
    return "\n".join(out)


def _function_source(source: str, fn: dict) -> str:
    lines = source.splitlines()
    return "\n".join(lines[fn["line"] - 1 : fn["end_line"]])


def _example_tests(repo: Path, gen_dir: Path, config) -> str:
    n = config.testgen.example_tests_in_prompt
    examples: list[str] = []
    for p in sorted(repo.rglob("test_*.py")):
        if ".git" in p.parts or gen_dir in p.parents:
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        examples.append(f"# {p.relative_to(repo)}\n{text[: config.testgen.example_test_chars]}")
        if len(examples) >= n:
            break
    return "\n\n".join(examples)


def _write_goal(
    module: str, targets: list[dict], source: str, repo: Path, gen_dir: Path, rel: str, config
) -> str:
    fns = "\n\n".join(
        f"### {t['qualname']}  (signature: {t['signature']})\n{_function_source(source, t)}"
        for t in targets
    )
    examples = _example_tests(repo, gen_dir, config)
    cmd = f"python -m pytest -q {rel}"
    return (
        f"Write pytest tests to the file `{rel}` for these functions from module "
        f"`{module}`. Test real behavior so a wrong implementation would fail.\n\n"
        f"Module imports:\n{_imports_block(source)}\n\n"
        f"Target functions:\n{fns}\n\n"
        f"Existing test style for reference:\n{examples or '(none)'}\n\n"
        f"Write ONLY `{rel}`. Confirm with: {cmd}"
    )


# --- container runs -----------------------------------------------------------


def _run_file(ctx: HygieneContext, rel: str) -> tuple[bool, str]:
    cmd = f"python -m pytest -p no:cacheprovider -q {rel}"
    with fresh_workdir(ctx.repo) as work:
        result = run_in_container(work, cmd, ctx.image_tag)
    tail = (result.stdout + result.stderr)[-ctx.config.testgen.run_output_chars :]
    return result.exit_code == 0, tail


def _mutant_outcome(ctx: HygieneContext, file_rel: str, mutant_source: str, test_rel: str) -> str:
    """``killed`` (a generated test failed, collection intact) / ``survived`` / ``invalid``
    (timeout or broken collection; counts neither as kill nor in the denominator)."""
    report_rel = ctx.config.baseline.report_filename
    cmd = f"python -m pytest -p no:cacheprovider -q {test_rel}"
    with fresh_workdir(ctx.repo) as work:
        write_source(work / file_rel, mutant_source)
        result = run_in_container(
            work,
            ctx.adapter.with_report(cmd, report_rel),
            ctx.image_tag,
            timeout=ctx.config.testgen.mutant_timeout_s,
        )
        report = work / report_rel
        if result.exit_code == 124 or not report.is_file():
            return "invalid"
        data = json.loads(report.read_text())
    if any(c.get("outcome") == "failed" for c in data.get("collectors", [])):
        return "invalid"  # collection broke -> not a discrimination signal
    tests = data.get("tests", [])
    if not tests:
        return "invalid"
    return "killed" if any(t.get("outcome") in ("failed", "error") for t in tests) else "survived"


@dataclass
class Gate:
    killed: int
    valid: int  # mutants that ran cleanly (killed + survived)
    invalid: int

    @property
    def has_mutants(self) -> bool:
        return self.valid > 0

    def status(self, min_killed: int) -> str:
        if not self.has_mutants:
            return "no_mutants"
        return "kept" if self.killed >= min_killed else "weak"


def _gate_function(ctx: HygieneContext, fn: dict, test_rel: str) -> Gate:
    source = read_source(ctx.repo / fn["file"])
    mutants = function_mutants(
        source,
        fn["line"],
        fn["end_line"],
        ctx.adapter.mutators(),
        ctx.config.testgen.mutants_per_function,
    )
    killed = valid = invalid = 0
    for m in mutants:
        outcome = _mutant_outcome(ctx, fn["file"], m.source, test_rel)
        if outcome == "invalid":
            invalid += 1
        else:
            valid += 1
            killed += outcome == "killed"
    return Gate(killed=killed, valid=valid, invalid=invalid)


# --- agent orchestration ------------------------------------------------------


def _decisions_path(ctx: HygieneContext) -> Path:
    return ctx.hygiene_dir / ctx.config.testgen.decisions_filename


def _load_decisions(ctx: HygieneContext) -> dict:
    path = _decisions_path(ctx)
    return json.loads(path.read_text()) if path.is_file() else {}


def _save_decisions(ctx: HygieneContext, decisions: dict) -> None:
    _decisions_path(ctx).write_text(json.dumps(decisions, indent=2, sort_keys=True))


def _module_key(ctx: HygieneContext, module: str, source: str, targets: list[dict]) -> str:
    payload = "\n".join(
        [
            PROMPT_VERSION,
            module,
            source,
            ctx.config.model_for(WRITE_STEP),
            # a different budget is a different attempt: never replay a smaller-budget drop
            str(ctx.config.testgen.agent_max_turns),
            str(ctx.config.testgen.mutants_per_function),
            str(ctx.config.testgen.min_mutants_killed),
        ]
        + [t["qualname"] for t in targets]
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _run_agent(ctx: HygieneContext, step: str, goal: str, gen_dir: Path, allowed: set[str]) -> str:
    tool_ctx = ToolContext(workdir=ctx.repo, image=ctx.image_tag)
    agent = Agent(
        ctx.llm,
        step,
        _SYSTEM,
        concrete_tools(tool_ctx),
        tool_ctx.files_changed,
        max_turns=ctx.config.testgen.agent_max_turns,
    )
    result = agent.run(goal)
    reverted = _revert_disallowed(ctx.repo, gen_dir, allowed)
    if reverted:
        append_agent_action(
            ctx.audit_dir, {"stage": step, "outcome": "reverted_disallowed", "reverted": reverted}
        )
    return result.summary[: ctx.config.testgen.summary_chars]


def _prune_empty_parents(start: Path, stop: Path) -> None:
    d = start
    while d != stop and d.is_dir() and not any(d.iterdir()):
        d.rmdir()
        d = d.parent


def _revert_disallowed(repo: Path, gen_dir: Path, allowed: set[str]) -> list[str]:
    """Undo agent edits outside ``allowed``: checkout tracked, delete untracked (``-uall``
    so a fresh gen_dir is not rmtree'd wholesale), prune emptied dirs."""
    reverted: list[str] = []
    proc = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain", "-uall"],
        capture_output=True,
        text=True,
        check=False,
    )
    for line in proc.stdout.splitlines():
        if not line:
            continue
        code, rel = line[:2].strip(), line[3:].strip()
        if rel in allowed:
            continue
        target = repo / rel
        if code == "??":
            if target.is_dir():
                shutil.rmtree(target, ignore_errors=True)
            else:
                target.unlink(missing_ok=True)
            _prune_empty_parents(target.parent, repo)
        else:
            subprocess.run(["git", "-C", str(repo), "checkout", "--", rel], check=False)
        reverted.append(rel)
    return reverted


def _generate_module(
    ctx: HygieneContext,
    module: str,
    targets: list[dict],
    gen_dir: Path,
    runs_left: list[int],
    kept_files: set[str],
) -> dict:
    """Write + gate one module's tests; ``kept_files`` = prior generated files to preserve."""
    file_rel = str((gen_dir / _module_test_file(module)).relative_to(ctx.repo))
    source = read_source(ctx.repo / targets[0]["file"])
    tg = ctx.config.testgen
    allowed = kept_files | {file_rel}

    def gate_all() -> dict[str, Gate]:
        return {t["qualname"]: _gate_function(ctx, t, file_rel) for t in targets}

    goal = _write_goal(module, targets, source, ctx.repo, gen_dir, file_rel, ctx.config)
    summary = ""
    gates: dict[str, Gate] = {}
    passed_real = False
    for attempt in range(1 + ctx.config.agent.testgen_max_retries):
        if runs_left[0] <= 0:
            break
        runs_left[0] -= 1
        step = WRITE_STEP if attempt == 0 else RETRY_STEP
        log(
            "hygiene",
            "testgen",
            f"module {module}: agent run {attempt + 1}/{1 + ctx.config.agent.testgen_max_retries}"
            f" ({runs_left[0]} runs left in repo budget)",
        )
        summary = _run_agent(ctx, step, goal, gen_dir, allowed)
        if not (ctx.repo / file_rel).is_file():
            log("hygiene", "testgen", f"module {module}: agent wrote no file")
            break
        passed_real, output = _run_file(ctx, file_rel)
        if not passed_real:
            log("hygiene", "testgen", f"module {module}: tests fail on real code, retrying")
            goal = _retry_goal(file_rel, module, f"the file fails on the real code:\n{output}")
            continue
        gates = gate_all()
        weak = {q for q, g in gates.items() if g.status(tg.min_mutants_killed) == "weak"}
        log("hygiene", "testgen", f"module {module}: mutation gate {_gate_line(gates)}")
        if not weak:
            break
        log("hygiene", "testgen", f"module {module}: weak {len(weak)}/{len(gates)}, retrying")
        survived = ", ".join(sorted(weak))
        goal = _retry_goal(
            file_rel,
            module,
            f"tests do not catch bugs in: {survived}. Add assertions that would fail if these "
            f"functions were subtly wrong (flipped comparisons, off-by-one, wrong constant).",
        )

    return _finalize_module(ctx, module, file_rel, gates, passed_real, summary)


def _gate_line(gates: dict[str, Gate]) -> str:
    killed = sum(g.killed for g in gates.values())
    valid = sum(g.valid for g in gates.values())
    return f"mutants {killed}/{valid} killed"


def _retry_goal(file_rel: str, module: str, problem: str) -> str:
    return (
        f"The generated tests in `{file_rel}` for module `{module}` are not good enough: "
        f"{problem}\nStrengthen ONLY `{file_rel}` and rerun `python -m pytest -q {file_rel}`."
    )


def _drop(ctx, module, file_rel, status, summary) -> dict:
    (ctx.repo / file_rel).unlink(missing_ok=True)
    append_agent_action(
        ctx.audit_dir, {"stage": WRITE_STEP, "module": module, "outcome": status, "file": file_rel}
    )
    return {"status": status, "functions": {}, "summary": summary}


def _finalize_module(ctx, module, file_rel, gates, passed_real, summary) -> dict:
    tg = ctx.config.testgen
    path = ctx.repo / file_rel
    if not path.is_file():
        return _drop(ctx, module, file_rel, "dropped_no_file", summary)
    if not passed_real:
        return _drop(ctx, module, file_rel, "dropped_failed_on_real", summary)
    gateable = [g for g in gates.values() if g.has_mutants]
    total_killed = sum(g.killed for g in gateable)
    if gateable and total_killed == 0:  # tests exist but prove nothing -> theater
        return _drop(ctx, module, file_rel, "dropped_zero_kill", summary)

    functions = {
        q: {
            "mutants_killed": g.killed,
            "mutants_valid": g.valid,
            "mutants_invalid": g.invalid,
            "status": g.status(tg.min_mutants_killed),
        }
        for q, g in sorted(gates.items())
    }
    append_agent_action(
        ctx.audit_dir,
        {
            "stage": WRITE_STEP,
            "module": module,
            "file": file_rel,
            "outcome": "kept",
            "functions": {q: f["status"] for q, f in functions.items()},
            "summary": summary,
        },
    )
    return {"status": "kept", "file": file_rel, "functions": functions, "summary": summary}


# --- step ---------------------------------------------------------------------


def input_hash(ctx: HygieneContext) -> str:
    # baseline.json is excluded (this step rewrites it) and so are generated tests, so the
    # step does not invalidate itself; the quarantine file is the stable-test-set input.
    marker = ctx.config.testgen.generated_subdir
    parts = [ctx.hygiene_dir / "build.json", ctx.repo / ctx.config.baseline.quarantine_file]
    src_files = [
        p
        for p in ctx.repo.rglob("*.py")
        if ".git" not in p.parts and p.is_file() and marker not in p.relative_to(ctx.repo).parts
    ]
    files = sorted({p.resolve() for p in [*parts, *src_files] if p.is_file()})
    # knobs that change what the agent may do or how the gate judges must invalidate the step
    return hash_inputs(repr(ctx.config.testgen), *files)


def _source_functions(ctx: HygieneContext) -> list[dict]:
    symbols = ctx.adapter.symbol_index(ctx.repo)
    # Only functions in importable library source (excludes tests, docs/conf.py, scripts).
    source_modules = {
        m["name"] for m in symbols.get("modules", []) if m.get("is_source", not m.get("is_test"))
    }
    return [f for f in symbols.get("functions", []) if f["module"] in source_modules]


def _quarantined(ctx: HygieneContext) -> list[str]:
    qfile = ctx.repo / ctx.config.baseline.quarantine_file
    if qfile.is_file():
        return [ln.strip() for ln in qfile.read_text().splitlines() if ln.strip()]
    return []


@contextmanager
def _run_lock(ctx: HygieneContext):
    """Fail fast if another process is already generating tests for this run dir."""
    lock = ctx.run_dir / ctx.config.testgen.lock_filename
    if lock.exists():
        raise SystemExit(f"test-gen already running for {ctx.run_dir} (remove {lock} to force)")
    ctx.run_dir.mkdir(parents=True, exist_ok=True)
    lock.write_text(str(os.getpid()))
    try:
        yield
    finally:
        lock.unlink(missing_ok=True)


def run(ctx: HygieneContext) -> dict:
    tg = ctx.config.testgen
    if not tg.enabled:
        data = {"enabled": False}
        ctx.record("testgen", data)
        return data
    with _run_lock(ctx):
        return _run(ctx)


def _run(ctx: HygieneContext) -> dict:
    tg = ctx.config.testgen
    functions = _source_functions(ctx)
    gen_dir = generated_dir(ctx.repo, ctx.config)
    # Rank on original coverage (ignore generated tests) so a resume ranks identically.
    ignore = (str(gen_dir.relative_to(ctx.repo)),) if gen_dir.exists() else ()
    cov = run_coverage(ctx.repo, ctx.image_tag, _quarantined(ctx), ctx.config, ignore=ignore)
    if cov.status not in ("ok", "no_tests"):  # no_tests = bootstrap; anything else is garbage
        log("hygiene", "testgen", f"coverage {cov.status}: skipped")
        data = {"coverage_status": cov.status, "skipped": "coverage_unavailable"}
        ctx.record(tg.results_filename.removesuffix(".json"), data)
        return data

    targets = rank_targets(functions, cov.contexts.get("files", {}), ctx.config)
    ctx.record(tg.targets_filename.removesuffix(".json"), targets)
    log(
        "hygiene",
        "testgen",
        f"coverage {cov.status}: {len(targets['modules'])} modules, "
        f"{len(targets['selected'])} target functions",
    )

    fn_by_id = {f["qualname"]: f for f in functions}
    _ensure_dir(ctx.repo, gen_dir)
    decisions = _load_decisions(ctx)
    runs_left = [tg.max_agent_runs_per_repo]
    modules_out: dict[str, dict] = {}
    kept_files: set[str] = set()

    for module_rec in targets["modules"]:
        module = module_rec["module"]
        target_fns = [fn_by_id[q] for q in module_rec["targets"] if q in fn_by_id]
        if not target_fns:
            continue
        source = read_source(ctx.repo / target_fns[0]["file"])
        key = _module_key(ctx, module, source, target_fns)
        cached = decisions.get(key)
        if cached is not None:
            if cached.get("status") == "kept" and cached.get("test_source"):
                write_source(gen_dir / _module_test_file(module), cached["test_source"])
                kept_files.add(cached["file"])
            modules_out[module] = {k: v for k, v in cached.items() if k != "test_source"}
            log("hygiene", "testgen", f"module {module}: reused decision ({cached.get('status')})")
            continue
        log("hygiene", "testgen", f"module {module}: {len(target_fns)} targets")
        result = _generate_module(ctx, module, target_fns, gen_dir, runs_left, kept_files)
        modules_out[module] = result
        log("hygiene", "testgen", f"module {module}: {_module_line(result)}")
        entry = dict(result)
        if result.get("status") == "kept":
            entry["test_source"] = read_source(gen_dir / _module_test_file(module))
            kept_files.add(result["file"])
        decisions[key] = entry
        _save_decisions(ctx, decisions)  # persist after every module

    data = _summary(cov, targets, modules_out)
    data.update(_record_suite_after(ctx))
    ctx.record(tg.results_filename.removesuffix(".json"), data)
    return data


def _module_line(result: dict) -> str:
    status = result.get("status")
    if status != "kept":
        return str(status)
    fns = result.get("functions") or {}
    kept = sum(1 for f in fns.values() if f.get("status") == "kept")
    killed = sum(f.get("mutants_killed", 0) for f in fns.values())
    valid = sum(f.get("mutants_valid", 0) for f in fns.values())
    return f"kept {kept}/{len(fns)} functions, mutants {killed}/{valid} killed"


def _record_suite_after(ctx: HygieneContext) -> dict:
    """Suite with generated tests present: refresh baseline.json, report twice-identical."""
    from pipeline.hygiene import baseline as baseline_step

    quarantined = ctx.load("baseline").get("quarantined") if _has_baseline(ctx) else None
    results, _ = baseline_step._run_suite(ctx, quarantined or None)
    counts = {
        "tests": len(results),
        "passed": sum(1 for r in results.values() if r["status"] == "pass"),
        "failed": sum(1 for r in results.values() if r["status"] not in ("pass", "skip")),
    }
    twice = baseline_step.run_twice_identical(ctx, quarantined or None)
    if _has_baseline(ctx):  # baseline.json documents the stable test set for P3/collateral
        base = ctx.load("baseline")
        base["results"] = results
        base["counts"] = {**base.get("counts", {}), **counts}
        base["testgen_refreshed"] = True
        ctx.record("baseline", base)
    return {"suite_after": counts, "twice_identical": twice}


def _has_baseline(ctx: HygieneContext) -> bool:
    return (ctx.hygiene_dir / "baseline.json").is_file()


def _summary(cov, targets, modules_out: dict) -> dict:
    kept = {m: r for m, r in modules_out.items() if r.get("status") == "kept"}
    all_fns = [f for r in kept.values() for f in r.get("functions", {}).values()]
    return {
        "coverage_status": cov.status,
        "modules_selected": len(targets["modules"]),
        "targets": len(targets["selected"]),
        "modules": dict(sorted(modules_out.items())),
        "counts": {
            "modules_kept": len(kept),
            "functions_kept": sum(1 for f in all_fns if f["status"] == "kept"),
            "functions_weak": sum(1 for f in all_fns if f["status"] == "weak"),
            "functions_no_mutants": sum(1 for f in all_fns if f["status"] == "no_mutants"),
            "mutants_killed": sum(f["mutants_killed"] for f in all_fns),
            "mutants_valid": sum(f["mutants_valid"] for f in all_fns),
        },
    }
