"""Excision funnel (DESIGN 5.3): deterministic candidate selection from the knowledge
artifacts, then a SMALL-model screen. Every function considered gets a status and,
when dropped, a ``reject_reason`` (feeds REPORT "what you rejected and why").
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from pathlib import Path

from pipeline.config import DEFAULT, Config
from pipeline.ecosystems.source_ops import private_repo_imports, read_source

SCREEN_STEP = "p3.excision.screen_candidate"

SCREEN_SCHEMA = {
    "type": "object",
    "properties": {
        "screens": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "qualname": {"type": "string"},
                    "docstring_leaks_impl": {"type": "boolean"},
                    "trivially_inferable": {"type": "boolean"},
                    "reason": {"type": "string"},
                },
                "required": ["qualname", "docstring_leaks_impl", "trivially_inferable", "reason"],
            },
        }
    },
    "required": ["screens"],
}


@dataclass
class Candidate:
    qualname: str
    module: str
    file: str
    line: int
    end_line: int
    span: int
    complexity: int
    is_method: bool
    parent: str
    signature: str
    docstring: str | None
    covering_tests: list[str] = field(default_factory=list)  # base nodeids, baseline-passing
    score: int = 0
    status: str = "considered"  # rejected | screened_out | selected | surplus
    reject_reason: str | None = None
    screen: dict | None = None
    screen_key: str | None = None  # content hash the screen decision is keyed by


def base_nodeid(nodeid: str) -> str:
    return nodeid.split("[", 1)[0]


def covering_tests(test_map: dict[str, list[str]], passing: set[str] | None) -> dict[str, set[str]]:
    """qualname -> distinct base test nodeids that exercise it (and passed at baseline
    when a passing set is given)."""
    out: dict[str, set[str]] = {}
    for nodeid, funcs in test_map.items():
        if passing is not None and nodeid not in passing:
            continue
        for fn in funcs:
            out.setdefault(fn, set()).add(base_nodeid(nodeid))
    return out


def _class_is_private(symbols: dict, parent: str) -> bool:
    for cls in symbols.get("classes", []):
        if cls["qualname"] == parent:
            return not cls["is_public"]
    return False


def _reject_reason(c: Candidate, symbols: dict, is_test: bool, config: Config) -> str | None:
    ex = config.excision
    if is_test:
        return "test-code"
    if ex.skip_init_modules and Path(c.file).name == "__init__.py":
        return "init-module"
    if ex.public_only and c.qualname.rsplit(".", 1)[-1].startswith("_"):
        return "private"
    if ex.require_public_parent and c.is_method and _class_is_private(symbols, c.parent):
        return "private-parent"
    n = len(c.covering_tests)
    if n == 0:
        return "uncovered"
    if n < ex.min_covering_tests:
        return f"few-covering-tests({n}<{ex.min_covering_tests})"
    if n > ex.max_covering_tests:
        return f"too-central({n}>{ex.max_covering_tests})"
    if c.span < ex.min_lines:
        return f"too-short({c.span}<{ex.min_lines})"
    if c.span > ex.max_lines:
        return f"too-long({c.span}>{ex.max_lines})"
    if c.complexity < ex.min_complexity:
        return f"low-complexity({c.complexity}<{ex.min_complexity})"
    return None


class _PrivateImportGate:
    """Per test file: private repo imports (same AST rule as the harness static gate)."""

    def __init__(self, repo: Path, symbols: dict):
        self.repo = repo
        self.by_file = {m["file"]: m for m in symbols["modules"]}
        self.top = {m["name"].split(".")[0] for m in symbols["modules"] if not m["is_test"]}
        self.cache: dict[str, list[str]] = {}

    def offenders(self, test_file: str) -> list[str]:
        if test_file not in self.cache:
            mod = self.by_file.get(test_file)
            package = ""
            if mod:
                package = mod["name"] if mod["is_package"] else mod["name"].rpartition(".")[0]
            path = self.repo / test_file
            source = read_source(path) if path.is_file() else ""
            self.cache[test_file] = private_repo_imports(source, package, self.top)
        return self.cache[test_file]


def funnel(
    symbols: dict,
    test_map: dict[str, list[str]],
    baseline_passing: set[str] | None,
    config: Config = DEFAULT,
    repo: Path | None = None,
) -> list[Candidate]:
    """Deterministic stage: every function becomes a Candidate; survivors are ranked
    (status ``considered``, ``score`` set) and losers carry ``reject_reason``. With
    ``repo``, covering test files that import private repo symbols/modules reject the
    candidate (``verifier-imports-private``) before any LLM is spent."""
    tests_for = covering_tests(test_map, baseline_passing)
    test_modules = {m["name"] for m in symbols["modules"] if m["is_test"]}
    gate = (
        _PrivateImportGate(repo, symbols)
        if repo and config.excision.reject_private_verifier_imports
        else None
    )
    out: list[Candidate] = []
    for fn in symbols["functions"]:
        c = Candidate(
            qualname=fn["qualname"],
            module=fn["module"],
            file=fn["file"],
            line=fn["line"],
            end_line=fn["end_line"],
            span=fn["end_line"] - fn["line"] + 1,
            complexity=fn["complexity"],
            is_method=fn["is_method"],
            parent=fn["parent"],
            signature=fn["signature"],
            docstring=fn["docstring"],
            covering_tests=sorted(tests_for.get(fn["qualname"], ())),
        )
        reason = _reject_reason(c, symbols, fn["module"] in test_modules, config)
        if reason is None and gate is not None:
            for test_file in sorted({n.split("::", 1)[0] for n in c.covering_tests}):
                bad = gate.offenders(test_file)
                if bad:
                    reason = f"verifier-imports-private({test_file}: {', '.join(bad)})"
                    break
        if reason:
            c.status, c.reject_reason = "rejected", reason
        else:
            c.score = len(c.covering_tests) * c.complexity
        out.append(c)
    return sorted(out, key=lambda c: c.qualname)


def rank(candidates: list[Candidate], config: Config = DEFAULT) -> list[Candidate]:
    """Survivors by score desc; round-robin over modules so one file cannot take every
    slot. Fully deterministic (ties broken by qualname)."""
    live = [c for c in candidates if c.status == "considered"]
    if not config.excision.rank_module_round_robin:
        return sorted(live, key=lambda c: (-c.score, c.qualname))
    by_module: dict[str, list[Candidate]] = {}
    for c in sorted(live, key=lambda c: (-c.score, c.qualname)):
        by_module.setdefault(c.module, []).append(c)
    order = sorted(by_module, key=lambda m: (-by_module[m][0].score, m))
    ranked: list[Candidate] = []
    while any(by_module.values()):
        for module in order:
            if by_module[module]:
                ranked.append(by_module[module].pop(0))
    return ranked


def function_source(repo: Path, c: Candidate) -> str:
    lines = read_source(repo / c.file).splitlines()
    return "\n".join(lines[c.line - 1 : c.end_line])


def screen_key(c: Candidate, source: str) -> str:
    return hashlib.sha256(f"{c.qualname}\n{source}".encode()).hexdigest()[:16]


def screen_prompt(items: list[tuple[str, str]]) -> str:
    blocks = "\n\n".join(f"### {qual}\n```python\n{src}\n```" for qual, src in items)
    return (
        "You screen candidate functions for a 'reimplement this function' benchmark task. "
        "The task hides the body but keeps the signature and docstring, and the solver "
        "must reimplement it so the existing tests pass. For EACH function answer:\n"
        "- docstring_leaks_impl: does the docstring spell out the implementation step by "
        "step (so a solver could transcribe it without understanding)? Describing behavior "
        "or the contract is NOT a leak.\n"
        "- trivially_inferable: is it a trivial wrapper/one-liner whose body is obvious "
        "from the signature and name alone (delegation, attribute access, constant)?\n"
        "Return one entry per function, same qualname, with a one-sentence reason.\n\n" + blocks
    )


def _apply_screen(c: Candidate, decision: dict | None) -> None:
    c.screen = decision
    if decision is None:
        c.status, c.reject_reason = "screened_out", "screen-no-answer"
    elif decision["docstring_leaks_impl"]:
        c.status, c.reject_reason = "screened_out", "docstring-leaks-implementation"
    elif decision["trivially_inferable"]:
        c.status, c.reject_reason = "screened_out", "trivially-inferable"


def screen(
    ranked: list[Candidate],
    repo: Path,
    llm,
    config: Config = DEFAULT,
    decisions: dict[str, dict] | None = None,
) -> list[Candidate]:
    """SMALL-model screen, walking the ranking in batches until ``build_target``
    survivors are found (backfills past screened-out candidates). ``decisions`` maps
    ``screen_key`` -> prior decision; keys found there are reused without an LLM call.
    Marks ``screened_out`` / ``selected`` / ``surplus``; returns the selected candidates."""
    ex = config.excision
    if decisions is None:
        decisions = {}
    batch = config.llm.classify_batch_size
    selected: list[Candidate] = []
    i = 0
    while len(selected) < ex.build_target and i < len(ranked):
        chunk = ranked[i : i + batch]
        i += batch
        sources = {c.qualname: function_source(repo, c) for c in chunk}
        for c in chunk:
            c.screen_key = screen_key(c, sources[c.qualname])
        pending = [c for c in chunk if c.screen_key not in decisions]
        if pending:
            res = llm.complete_json(
                SCREEN_STEP,
                [
                    {
                        "role": "user",
                        "content": screen_prompt(
                            [(c.qualname, sources[c.qualname]) for c in pending]
                        ),
                    }
                ],
                SCREEN_SCHEMA,
            )
            by_name = {d["qualname"]: d for d in res.get("screens", [])}
            for c in pending:
                if c.qualname in by_name:
                    decisions[c.screen_key] = by_name[c.qualname]
        for c in chunk:
            _apply_screen(c, decisions.get(c.screen_key))
            if c.status == "considered":
                if len(selected) < ex.build_target:
                    c.status = "selected"
                    selected.append(c)
                else:
                    c.status = "surplus"
    for c in ranked[i:]:
        c.status = "surplus"
    return selected


def candidates_json(candidates: list[Candidate]) -> list[dict]:
    return [asdict(c) for c in sorted(candidates, key=lambda c: c.qualname)]
