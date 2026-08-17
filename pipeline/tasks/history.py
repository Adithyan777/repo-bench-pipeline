"""History-derived funnel (DESIGN 5.2) over ``knowledge/history_index.json``.

Deterministic hard filters + signal score (code, git), then a SMALL-model classify
(batched, decisions persisted by content hash), then a diversity-aware shortlist.
Every commit considered lands in ``output/<repo>/tasks/history_candidates.json`` with
a status and, when dropped, a ``reject_reason``.
"""

from __future__ import annotations

import ast
import fnmatch
import hashlib
import re
import subprocess
import warnings
from dataclasses import asdict, dataclass, field
from pathlib import Path

from pipeline.config import DEFAULT, Config
from pipeline.ecosystems.symbols import path_to_module

CLASSIFY_STEP = "p3.history.classify_commit"

CLASSIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "classifications": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "sha": {"type": "string"},
                    "kind": {
                        "type": "string",
                        "enum": ["bugfix", "feature", "refactor", "chore", "test-only"],
                    },
                    "self_contained": {"type": "boolean"},
                    "verifiable_via_tests": {"type": "boolean"},
                    "behavior_change_summary": {"type": "string"},
                    "difficulty_guess": {"type": "string", "enum": ["easy", "medium", "hard"]},
                },
                "required": [
                    "sha",
                    "kind",
                    "self_contained",
                    "verifiable_via_tests",
                    "behavior_change_summary",
                    "difficulty_guess",
                ],
            },
        }
    },
    "required": ["classifications"],
}


@dataclass
class HistoryCandidate:
    sha: str
    parents: list[str]
    message: str
    is_merge: bool
    pr_number: int | None
    input_sha: str  # first parent (PR merge or plain commit)
    files_changed: list[str]
    source_files: list[str]  # non-test .py files outside ignore_paths
    test_files: list[str]
    touched_functions: list[str]
    covered_functions: list[str] = field(default_factory=list)  # baseline-passing coverage
    source_lines_changed: int = 0
    modules: list[str] = field(default_factory=list)
    status: str = "considered"  # rejected | classified_out | kept | shortlisted | surplus
    reject_reason: str | None = None
    score: float = 0.0
    score_breakdown: dict = field(default_factory=dict)
    reverted_by: str | None = None
    classify: dict | None = None
    classify_key: str | None = None
    kind: str | None = None

    @property
    def short(self) -> str:
        return self.sha[:7]


# --- git ---------------------------------------------------------------------------


def git(repo: Path, *args: str, check: bool = False) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=check
    )
    return proc.stdout


def show(repo: Path, ref: str, path: str) -> str | None:
    proc = subprocess.run(
        ["git", "-C", str(repo), "show", f"{ref}:{path}"], capture_output=True, text=True
    )
    return proc.stdout if proc.returncode == 0 else None


def diff(repo: Path, a: str, b: str, paths: list[str] | None = None) -> str:
    args = ["diff", "--no-renames", a, b]
    if paths:
        args += ["--", *paths]
    return git(repo, *args)


def _patch_id(repo: Path, patch: str) -> str | None:
    if not patch.strip():
        return None
    proc = subprocess.run(
        ["git", "-C", str(repo), "patch-id", "--stable"],
        input=patch,
        capture_output=True,
        text=True,
    )
    return proc.stdout.split()[0] if proc.stdout.strip() else None


def forward_patch_ids(repo: Path, base_sha: str) -> dict[str, str]:
    """sha -> patch-id for every commit at/under base_sha in one git pass (merges are
    diffed against their first parent)."""
    proc = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "log",
            "--format=%H",
            "-p",
            "--no-renames",
            "--diff-merges=first-parent",
            base_sha,
        ],
        capture_output=True,
        text=True,
        errors="replace",
    )
    ids = subprocess.run(
        ["git", "-C", str(repo), "patch-id", "--stable"],
        input=proc.stdout,
        capture_output=True,
        text=True,
    )
    out: dict[str, str] = {}
    for line in ids.stdout.splitlines():
        parts = line.split()
        if len(parts) == 2:
            out[parts[1]] = parts[0]
    return out


# --- hard filters --------------------------------------------------------------------


def _ignored(path: str, patterns: tuple[str, ...]) -> bool:
    for pat in patterns:
        if pat.endswith("/"):
            if path.startswith(pat) or f"/{pat}" in f"/{path}":
                return True
        elif fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(Path(path).name, pat):
            return True
    return False


def _source_lines(repo: Path, c: HistoryCandidate) -> int:
    numstat = git(
        repo, "diff", "--no-renames", "--numstat", c.input_sha, c.sha, "--", *c.source_files
    )
    total = 0
    for line in numstat.splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            total += sum(int(p) for p in parts[:2] if p.isdigit())
    return total


def _parses(repo: Path, c: HistoryCandidate) -> str | None:
    for f in c.source_files:
        for state, ref in (("input", c.input_sha), ("solution", c.sha)):
            src = show(repo, ref, f)
            if src is None:
                continue
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", SyntaxWarning)
                    ast.parse(src)
            except SyntaxError:
                return f"unparseable({f}@{state})"
    return None


def _hard_reject(
    c: HistoryCandidate, commit: dict, repo: Path, covered_all: set[str], config: Config
) -> str | None:
    hc = config.history
    if not c.parents:
        return "root-commit" if hc.reject_root_commits else None
    if c.is_merge and hc.reject_non_pr_merges and c.pr_number is None:
        return "non-pr-merge"
    if all(_ignored(f, hc.ignore_paths) for f in c.files_changed):
        return "docs-or-ci-only"
    if hc.reject_manifest_changes and commit.get("touches_manifest"):
        return "dependency-changing"
    if not c.source_files:
        return "no-source-change"
    if len(c.source_files) > hc.max_source_files_changed:
        return f"too-many-files({len(c.source_files)}>{hc.max_source_files_changed})"
    c.source_lines_changed = _source_lines(repo, c)
    if c.source_lines_changed < hc.min_source_lines_changed:
        return f"too-small({c.source_lines_changed}<{hc.min_source_lines_changed})"
    if c.source_lines_changed > hc.max_source_lines_changed:
        return f"too-large({c.source_lines_changed}>{hc.max_source_lines_changed})"
    c.covered_functions = sorted(set(c.touched_functions) & covered_all)
    if hc.require_coverage_or_added_tests and not c.covered_functions and not c.test_files:
        return "uncovered-and-no-tests"
    return _parses(repo, c)


def _revert_targets(message: str, regex: str) -> list[str]:
    return [m for m in re.findall(regex, message) if m]


def _mark_reverted(
    cands: list[HistoryCandidate], repo: Path, base_sha: str, config: Config
) -> None:
    """A commit is reverted when a LATER commit names it in a revert message or carries
    the exact reverse patch (patch-id of the reversed diff)."""
    hc = config.history
    forward = forward_patch_ids(repo, base_sha)
    order = {c.sha: i for i, c in enumerate(cands)}  # index 0 = newest
    by_forward: dict[str, list[str]] = {}
    for sha, pid in forward.items():
        by_forward.setdefault(pid, []).append(sha)
    revert_re = re.compile(hc.revert_message_regex, re.MULTILINE)
    named: dict[str, str] = {}
    for c in cands:
        if revert_re.search(c.message):  # subject only; the sha is in the body
            body = git(repo, "show", "-s", "--format=%B", c.sha)
            for target in _revert_targets(body, hc.revert_message_regex):
                for other in cands:
                    if other.sha.startswith(target):
                        named[other.sha] = c.sha
    for c in cands:
        if c.status != "considered":
            continue
        by = named.get(c.sha)
        if by is None:
            reverse = _patch_id(repo, diff(repo, c.sha, c.input_sha))
            later = [
                s for s in by_forward.get(reverse, []) if s in order and order[s] < order[c.sha]
            ]
            by = later[0] if later else None
        if by:
            c.reverted_by = by
            if hc.reject_reverted:
                c.status, c.reject_reason = "rejected", f"reverted-by({by[:7]})"


def supersede_constituents(
    cands: list[HistoryCandidate], kept: list[HistoryCandidate], repo: Path
) -> list[HistoryCandidate]:
    """Constituent commits of a KEPT PR merge are superseded by the merge (the merge is the
    complete unit); constituents of rejected/classified-out merges stand alone. Returns the
    kept list without the superseded ones."""
    by_sha = {c.sha: c for c in cands}
    superseded: set[str] = set()
    for m in kept:
        if not (m.is_merge and len(m.parents) > 1):
            continue
        for sha in git(repo, "rev-list", f"{m.parents[0]}..{m.parents[1]}").split():
            c = by_sha.get(sha)
            if c is not None and c.status in ("considered", "kept", "surplus"):
                c.status, c.reject_reason = "rejected", f"superseded-by-merge({m.short})"
                superseded.add(sha)
    return [c for c in kept if c.sha not in superseded]


# --- score ----------------------------------------------------------------------------


def _score(c: HistoryCandidate, public: dict[str, bool], config: Config) -> None:
    hc = config.history
    parts: dict[str, float] = {}
    if re.search(hc.fix_keyword_regex, c.message, re.IGNORECASE):
        parts["fix_keyword"] = hc.score_fix_keyword
    if c.test_files:
        parts["adds_tests"] = hc.score_adds_tests
    if any(_is_public(q, public) for q in c.touched_functions):
        parts["public_fn"] = hc.score_public_fn
    if len(c.touched_functions) == 1:
        parts["single_function"] = hc.score_single_function
    if c.reverted_by and not hc.reject_reverted:
        parts["reverted"] = hc.score_reverted_penalty
    c.score_breakdown = parts
    c.score = round(sum(parts.values()), 3)


def _is_public(qualname: str, public: dict[str, bool]) -> bool:
    """The symbol index's ``is_public`` when the node still exists; otherwise every
    component below the module must be public (a method on ``_Private`` is not)."""
    if qualname in public:
        return public[qualname]
    return not any(p.startswith("_") for p in qualname.split(".")[1:])


# --- funnel ---------------------------------------------------------------------------


def funnel(
    history: list[dict],
    test_map: dict[str, list[str]],
    baseline_passing: set[str] | None,
    repo: Path,
    base_sha: str,
    config: Config = DEFAULT,
    symbols: dict | None = None,
) -> list[HistoryCandidate]:
    """Deterministic stage over the ORIGINAL history (newest first). Survivors keep
    status ``considered`` with a score; the rest carry ``reject_reason``. PR-merge
    constituents are superseded later, once the merge is KEPT (``supersede_constituents``)."""
    hc = config.history
    public = {f["qualname"]: f["is_public"] for f in (symbols or {}).get("functions", [])}
    covered_all: set[str] = set()
    for nodeid, funcs in test_map.items():
        if baseline_passing is None or nodeid in baseline_passing:
            covered_all.update(funcs)
    cands: list[HistoryCandidate] = []
    for commit in history:
        tests = list(commit.get("test_files_touched", []))
        source = sorted(
            f
            for f in commit["files_changed"]
            if f.endswith(".py") and f not in tests and not _ignored(f, hc.ignore_paths)
        )
        parents = list(commit.get("parents", []))
        c = HistoryCandidate(
            sha=commit["sha"],
            parents=parents,
            message=commit["message"],
            is_merge=bool(commit.get("is_merge")),
            pr_number=commit.get("pr_number"),
            input_sha=parents[0] if parents else "",
            files_changed=list(commit["files_changed"]),
            source_files=source,
            test_files=tests,
            touched_functions=list(commit.get("touched_functions", [])),
            modules=sorted({path_to_module(f, config.knowledge.source_roots) for f in source}),
        )
        reason = _hard_reject(c, commit, repo, covered_all, config)
        if reason:
            c.status, c.reject_reason = "rejected", reason
        cands.append(c)
    _mark_reverted(cands, repo, base_sha, config)
    for c in cands:
        if c.status == "considered":
            _score(c, public, config)
    return cands


def ranked(cands: list[HistoryCandidate]) -> list[HistoryCandidate]:
    """Survivors by score desc, then history order (newest first) for determinism."""
    order = {c.sha: i for i, c in enumerate(cands)}
    return sorted(
        (c for c in cands if c.status == "considered"), key=lambda c: (-c.score, order[c.sha])
    )


# --- classify (SMALL) -----------------------------------------------------------------


def _truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit] + f"\n... (truncated, {len(text)} chars)"


def commit_block(c: HistoryCandidate, repo: Path, config: Config) -> str:
    src_diff = _truncate(
        diff(repo, c.input_sha, c.sha, c.source_files), config.history.classify_diff_max_chars
    )
    tests = ", ".join(c.test_files) or "(none)"
    return (
        f"### {c.short}\nmessage: {c.message}\nsource files: {', '.join(c.source_files)}\n"
        f"test files touched: {tests}\ntouched functions: {', '.join(c.touched_functions) or '-'}\n"
        f"```diff\n{src_diff}\n```"
    )


def classify_key(c: HistoryCandidate, block: str) -> str:
    return hashlib.sha256(f"{c.sha}\n{block}".encode()).hexdigest()[
        : DEFAULT.tasks.content_key_chars
    ]


def classify_prompt(blocks: list[str]) -> str:
    return (
        "You classify commits of a Python repository as material for a 'reproduce this "
        "change' benchmark task: the solver gets the tree BEFORE the commit and must make "
        "hidden or visible tests pass. For EACH commit return:\n"
        "- kind: bugfix | feature | refactor | chore | test-only\n"
        "- self_contained: the change is understandable from the touched code alone "
        "(no dependency bump, no multi-PR migration, no generated code)\n"
        "- verifiable_via_tests: an observable behavior change that unit tests can pin down "
        "(refactors and pure renames are not)\n"
        "- behavior_change_summary: 1-2 sentences describing WHAT changes for a caller, in "
        "black-box terms (no line-level implementation details)\n"
        "- difficulty_guess: easy | medium | hard for a competent engineer\n"
        "Return one entry per commit with the same sha.\n\n" + "\n\n".join(blocks)
    )


def _apply_classification(c: HistoryCandidate, decision: dict | None, config: Config) -> None:
    c.classify = decision
    if decision is None:
        c.status, c.reject_reason = "classified_out", "classify-no-answer"
        return
    c.kind = decision["kind"]
    if c.kind not in config.history.keep_kinds:
        c.status, c.reject_reason = "classified_out", f"kind:{c.kind}"
    elif not decision["self_contained"]:
        c.status, c.reject_reason = "classified_out", "not-self-contained"
    elif not decision["verifiable_via_tests"]:
        c.status, c.reject_reason = "classified_out", "not-verifiable-via-tests"
    else:
        c.status = "kept"


def classify(
    order: list[HistoryCandidate],
    repo: Path,
    llm,
    config: Config = DEFAULT,
    decisions: dict[str, dict] | None = None,
) -> list[HistoryCandidate]:
    """SMALL classify, walking the scored survivors in ``classify_batch_size`` batches until
    ``shortlist_size`` are kept (never past ``classify_max_commits``). ``decisions`` maps
    ``classify_key`` -> prior decision (reused, no LLM call). Returns the kept ones."""
    hc = config.history
    if decisions is None:
        decisions = {}
    batch = config.llm.classify_batch_size
    kept: list[HistoryCandidate] = []
    i = 0
    while len(kept) < hc.shortlist_size and i < min(len(order), hc.classify_max_commits):
        chunk = order[i : i + batch]
        i += batch
        blocks = {c.sha: commit_block(c, repo, config) for c in chunk}
        for c in chunk:
            c.classify_key = classify_key(c, blocks[c.sha])
        pending = [c for c in chunk if c.classify_key not in decisions]
        if pending:
            res = llm.complete_json(
                CLASSIFY_STEP,
                [{"role": "user", "content": classify_prompt([blocks[c.sha] for c in pending])}],
                CLASSIFY_SCHEMA,
            )
            by_sha = {d["sha"]: d for d in res.get("classifications", [])}
            for c in pending:
                hit = by_sha.get(c.short) or by_sha.get(c.sha)
                if hit is None:
                    hit = next((d for s, d in by_sha.items() if c.sha.startswith(s)), None)
                if hit is not None:
                    decisions[c.classify_key] = hit
        for c in chunk:
            _apply_classification(c, decisions.get(c.classify_key), config)
            if c.status == "kept":
                kept.append(c)
    for c in order[i:]:
        c.status, c.reject_reason = "surplus", "not-classified"
    return kept


def shortlist(kept: list[HistoryCandidate], config: Config = DEFAULT) -> list[HistoryCandidate]:
    """Greedy top-``shortlist_size`` by score with a module-diversity bonus for commits
    whose modules are not yet represented; bugfixes win ties over features."""
    hc = config.history
    kind_rank = {k: i for i, k in enumerate(hc.keep_kinds)}
    pool = list(kept)
    picked: list[HistoryCandidate] = []
    seen_modules: set[str] = set()
    while pool and len(picked) < hc.shortlist_size:
        best = max(
            pool,
            key=lambda c: (
                c.score + (hc.score_module_diversity if not set(c.modules) & seen_modules else 0),
                -kind_rank.get(c.kind or "", 99),
                -pool.index(c),
            ),
        )
        pool.remove(best)
        picked.append(best)
        seen_modules.update(best.modules)
        best.status = "shortlisted"
    for c in pool:
        c.status, c.reject_reason = "surplus", "kept-not-shortlisted"
    return picked


def candidates_json(cands: list[HistoryCandidate]) -> list[dict]:
    return [asdict(c) for c in cands]
