"""Index data files (docs/pipeline-2-knowledge.md); deterministic, no LLM.

- history_index.json: commits at/under base_sha; touched functions = diff hunks
  intersected with AST spans of the file AT that commit (never HEAD spans).
- test_map.json / coverage.json: one container run of ``coverage run -m pytest`` with
  per-test dynamic contexts, joined to source AST spans.
- hotspots.json: change frequency per function.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from pipeline.config import DEFAULT, Config
from pipeline.docker.runner import fresh_workdir, run_in_container
from pipeline.ecosystems.symbols import (
    functions_in_source,
    is_test_path,
    path_to_module,
)

_HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
_EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"  # git's empty-tree object

# pytest plugin: tags covered lines with the exact nodeid via coverage.switch_context
# (parametrized/inherited cases stay distinct; no pytest-cov dependency).
_CTX_PLUGIN = """import coverage
import pytest


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    cov = coverage.Coverage.current()
    if cov is not None:
        cov.switch_context(item.nodeid)
    yield
"""


@dataclass
class CoverageRun:
    """Result of the single in-container coverage run."""

    contexts: dict  # parsed coverage json (files -> executed/missing/contexts)
    status: str  # ok | no_output | no_tests
    exit_code: int


# --- coverage / test_map (container) ------------------------------------------


def run_coverage(
    repo: Path,
    image: str,
    deselect: list[str],
    config: Config = DEFAULT,
    ignore: tuple[str, ...] = (),
) -> CoverageRun:
    """One coverage run keyed by pytest nodeid -> (contexts JSON, status). ``ignore``
    paths (e.g. generated tests) are excluded from collection."""
    kc = config.knowledge
    with fresh_workdir(repo) as work:
        (work / kc.coveragerc_filename).write_text(_coveragerc())
        (work / f"{kc.ctx_plugin_module}.py").write_text(_CTX_PLUGIN)
        deselect_args = " ".join(f"--deselect {q}" for q in deselect)
        deselect_args += "".join(f" --ignore={p}" for p in ignore)
        # `-i`: doctests of transient files would otherwise abort with "No source for code".
        cmd = (
            f"coverage run --rcfile={kc.coveragerc_filename} -m pytest "
            f"-p no:cacheprovider -p {kc.ctx_plugin_module} -q {deselect_args} ; "
            f"echo __pytest_exit=$? ; "
            f"coverage json --rcfile={kc.coveragerc_filename} -i "
            f"-o {kc.coverage_json_filename} >/dev/null 2>&1 ; true"
        )
        result = run_in_container(work, cmd, image)
        exit_code = _parse_pytest_exit(result.stdout)
        out = work / kc.coverage_json_filename
        if not out.is_file():
            return CoverageRun({}, "no_output", exit_code)
        contexts = json.loads(out.read_text())
        status = "no_tests" if exit_code == 5 else "ok"
        return CoverageRun(contexts, status, exit_code)


def _parse_pytest_exit(stdout: str) -> int:
    for line in stdout.splitlines():
        if line.startswith("__pytest_exit="):
            tail = line.split("=", 1)[1].strip()
            return int(tail) if tail.isdigit() else -1
    return -1


def _coveragerc() -> str:
    return "[run]\nrelative_files = True\n[json]\nshow_contexts = True\n"


def build_coverage(symbols: dict, cov_json: dict) -> dict[str, float]:
    """Per-function coverage %, computed over each function's measurable body lines."""
    files = cov_json.get("files", {})
    exec_by_file = {f: set(d.get("executed_lines", [])) for f, d in files.items()}
    miss_by_file = {f: set(d.get("missing_lines", [])) for f, d in files.items()}
    result: dict[str, float] = {}
    for fn in _source_functions(symbols):
        span = set(range(fn["line"], fn["end_line"] + 1))
        executed = exec_by_file.get(fn["file"], set()) & span
        missing = miss_by_file.get(fn["file"], set()) & span
        measurable = executed | missing
        if not measurable:
            continue
        result[fn["qualname"]] = round(100 * len(executed) / len(measurable), 1)
    return dict(sorted(result.items()))


def build_test_map(symbols: dict, cov_json: dict) -> dict[str, list[str]]:
    """pytest nodeid -> source functions it executed (contexts are exact nodeids)."""
    files = cov_json.get("files", {})
    # nodeid -> {file: set(lines it covered)}
    lines_by_test: dict[str, dict[str, set[int]]] = {}
    for file, data in files.items():
        for line_str, contexts in data.get("contexts", {}).items():
            line = int(line_str)
            for ctx in contexts:
                if not ctx:  # import-time code, no active test
                    continue
                lines_by_test.setdefault(ctx, {}).setdefault(file, set()).add(line)

    funcs_by_file: dict[str, list[dict]] = {}
    for fn in _source_functions(symbols):
        funcs_by_file.setdefault(fn["file"], []).append(fn)

    test_map: dict[str, set[str]] = {}
    for nodeid, filemap in lines_by_test.items():
        hit: set[str] = set()
        for file, lines in filemap.items():
            for fn in funcs_by_file.get(file, []):
                if lines & set(range(fn["line"], fn["end_line"] + 1)):
                    hit.add(fn["qualname"])
        if hit:
            test_map[nodeid] = hit
    return {k: sorted(v) for k, v in sorted(test_map.items())}


def _source_functions(symbols: dict) -> list[dict]:
    source_modules = {m["name"] for m in symbols["modules"] if not m["is_test"]}
    return [f for f in symbols["functions"] if f["module"] in source_modules]


# --- history index (git + AST) ------------------------------------------------


def build_history_index(repo: Path, base_sha: str, config: Config = DEFAULT) -> list[dict]:
    if not base_sha or not (Path(repo) / ".git").exists():
        return []
    shas = _git(repo, "rev-list", base_sha).splitlines()
    return [_commit_record(repo, sha, config) for sha in shas]


def _commit_record(repo: Path, sha: str, config: Config) -> dict:
    parents = _git(repo, "show", "-s", "--format=%P", sha).split()
    subject = _git(repo, "show", "-s", "--format=%s", sha)
    base = parents[0] if parents else _EMPTY_TREE
    # --no-renames: delete+add attributes both old and new spans, no similarity guessing.
    numstat = _git(repo, "diff", "--no-renames", "--numstat", base, sha)
    files, insertions, deletions = _parse_numstat(numstat)
    tests_touched = [f for f in files if is_test_path(Path(repo), Path(repo) / f, config)]
    touched_functions = _touched_functions(repo, base, sha, files, tests_touched, config)
    pr = re.search(config.knowledge.pr_number_regex, subject)
    return {
        "sha": sha,
        "parents": parents,
        "message": subject,
        "is_merge": len(parents) > 1,
        "pr_number": int(pr.group(1)) if pr else None,
        "files_changed": files,
        "insertions": insertions,
        "deletions": deletions,
        "test_files_touched": tests_touched,
        "touches_manifest": _touches_manifest(files, config),
        "touched_functions": touched_functions,
    }


def _touched_functions(
    repo: Path, base: str, sha: str, files: list[str], tests_touched: list[str], config: Config
) -> list[str]:
    touched: set[str] = set()
    for file in files:
        if not file.endswith(".py") or file in tests_touched:
            continue
        diff = _git(repo, "diff", "--no-renames", "--unified=0", base, sha, "--", file)
        old_lines, new_lines = _changed_lines(diff)
        module = path_to_module(file, config.knowledge.source_roots)
        touched |= _intersect(_show(repo, sha, file), module, new_lines)
        touched |= _intersect(_show(repo, base, file), module, old_lines)
    return sorted(touched)


def _intersect(source: str, module: str, lines: set[int]) -> set[str]:
    if not source or not lines:
        return set()
    hit: set[str] = set()
    for fn in functions_in_source(source, module):
        if lines & set(range(fn["line"], fn["end_line"] + 1)):
            hit.add(fn["qualname"])
    return hit


def _changed_lines(diff: str) -> tuple[set[int], set[int]]:
    old: set[int] = set()
    new: set[int] = set()
    for line in diff.splitlines():
        m = _HUNK_RE.match(line)
        if not m:
            continue
        o_start, o_len, n_start, n_len = (
            int(m.group(1)),
            int(m.group(2) or 1),
            int(m.group(3)),
            int(m.group(4) or 1),
        )
        old |= set(range(o_start, o_start + o_len))
        new |= set(range(n_start, n_start + n_len))
    return old, new


def _touches_manifest(files: list[str], config: Config) -> bool:
    markers = set(config.detect.manifest_markers)
    prefixes = config.knowledge.manifest_name_prefixes
    for file in files:
        name = Path(file).name
        if name in markers or name.startswith(prefixes):
            return True
    return False


def _parse_numstat(numstat: str) -> tuple[list[str], int, int]:
    files: list[str] = []
    insertions = deletions = 0
    for line in numstat.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        add, rem, path = parts
        files.append(path)
        insertions += int(add) if add.isdigit() else 0
        deletions += int(rem) if rem.isdigit() else 0
    return sorted(files), insertions, deletions


def build_hotspots(history: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for commit in history:
        for qual in commit["touched_functions"]:
            counts[qual] = counts.get(qual, 0) + 1
    # sort by count desc, then name for a stable, byte-identical file
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


# --- git ----------------------------------------------------------------------


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
    )
    return proc.stdout.rstrip("\n")


def _show(repo: Path, ref: str, path: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), "show", f"{ref}:{path}"],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout if proc.returncode == 0 else ""
