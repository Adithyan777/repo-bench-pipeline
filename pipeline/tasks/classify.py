"""Right-reason classifier over a pytest-json-report (docs/pipeline-3-tasks.md), STRICT.

Report shape (pytest-json-report 1.5.0): failing call/setup carries ``crash{path,lineno,
message="Type: text"}`` + ``traceback[...]`` (only the last frame names the type);
fixture-not-found errors carry only ``longrepr``; collection failures live ONLY in
``collectors`` (exitcode 2); "nothing ran" is ``summary.total == 0`` (exitcode 5).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass, field

from pipeline.config import DEFAULT

_IMPORT_TYPES = ("ModuleNotFoundError", "ImportError", "SyntaxError")  # in a test body
_COLLECT_TYPES = (*_IMPORT_TYPES, "AttributeError")  # AttributeError at import time = collect


@dataclass
class TestReason:
    nodeid: str
    outcome: str
    reason: str  # one of config.harness.valid_fail_reasons / invalid_fail_reasons
    valid: bool
    detail: str = ""


@dataclass
class ReportVerdict:
    ok: bool  # every failing test failed for a valid reason (and something failed)
    exit_code: int
    n_failing: int
    n_passing: int
    reasons: dict[str, dict] = field(default_factory=dict)  # nodeid -> TestReason
    invalid: list[str] = field(default_factory=list)  # reasons that made it invalid

    def to_dict(self) -> dict:
        return asdict(self)


def _rel(path: str, root: str) -> str | None:
    """Repo-relative path, or None when the frame is outside the repo (site-packages)."""
    if not path:
        return None
    if path.startswith(root.rstrip("/") + "/"):
        return path[len(root.rstrip("/")) + 1 :]
    if path.startswith("/"):
        return None
    return path


def _phase_reason(
    nodeid: str, outcome: str, phase: dict, is_test_file: Callable[[str], bool], root: str
) -> TestReason:
    longrepr = phase.get("longrepr") or ""
    crash = phase.get("crash") or {}
    tb = phase.get("traceback") or []
    last_line = longrepr.strip().splitlines()[-1] if longrepr.strip() else ""
    msg = crash.get("message") or last_line
    exc_type = (tb[-1]["message"] if tb and tb[-1].get("message") else msg.split(":", 1)[0]).strip()
    if "fixture '" in longrepr and "not found" in longrepr:
        return TestReason(
            nodeid, outcome, "fixture_not_found", False, longrepr.splitlines()[-1][:200]
        )
    if exc_type == "AssertionError" or msg.startswith("assert "):
        return TestReason(nodeid, outcome, "AssertionError", True, msg[:200])
    if msg.startswith("Failed: DID NOT RAISE"):
        return TestReason(nodeid, outcome, "pytest.raises", True, msg[:200])
    frames = [_rel(f.get("path", ""), root) for f in tb] + [_rel(crash.get("path", ""), root)]
    repo_frames = [p for p in frames if p and not is_test_file(p)]
    if repo_frames:
        if exc_type == "NotImplementedError" or msg.startswith("NotImplementedError"):
            return TestReason(nodeid, outcome, "NotImplementedError", True, f"in {repo_frames[-1]}")
        return TestReason(
            nodeid, outcome, "exception_in_repo_code", True, f"{exc_type} in {repo_frames[-1]}"
        )
    reason = exc_type if exc_type in _IMPORT_TYPES else "error_before_repo_call"
    return TestReason(nodeid, outcome, reason, False, msg[:200])


def _collector_reason(collector: dict) -> TestReason:
    longrepr = collector.get("longrepr") or ""
    detail = next((ln for ln in longrepr.splitlines() if "Error" in ln), longrepr[:200])
    kind = next((t for t in _COLLECT_TYPES if t in longrepr), "collection_error")
    if kind == "AttributeError":
        kind = "AttributeError@import"
    return TestReason(collector.get("nodeid") or "<collect>", "collect", kind, False, detail[:200])


def classify_report(
    report: dict | None,
    exit_code: int,
    is_test_file: Callable[[str], bool],
    min_failing: int = 1,
    valid_reasons: tuple[str, ...] = DEFAULT.harness.valid_fail_reasons,
    invalid_reasons: tuple[str, ...] = DEFAULT.harness.invalid_fail_reasons,
) -> ReportVerdict:
    """Judge a fail-before run: >= ``min_failing`` failing tests, ONLY for reasons in the
    configured valid list."""
    verdict = _classify(report, exit_code, is_test_file, min_failing)
    known = {*valid_reasons, *invalid_reasons}
    for r in [*verdict.invalid, *(x["reason"] for x in verdict.reasons.values())]:
        if r not in known:
            raise ValueError(f"classifier emitted unknown reason {r!r}; add it to config.harness")
    for x in verdict.reasons.values():
        if x["valid"] != (x["reason"] in valid_reasons):
            raise ValueError(f"reason {x['reason']!r} validity disagrees with config.harness")
    return verdict


def _classify(
    report: dict | None, exit_code: int, is_test_file: Callable[[str], bool], min_failing: int
) -> ReportVerdict:
    if report is None:
        return ReportVerdict(False, exit_code, 0, 0, {}, ["no_report"])
    root = report.get("root", "/repo")
    summary = report.get("summary", {})
    reasons: dict[str, TestReason] = {}
    invalid: list[str] = []
    for coll in report.get("collectors", []):
        if coll.get("outcome") == "failed":
            r = _collector_reason(coll)
            reasons[r.nodeid] = r
            invalid.append(r.reason)
    if summary.get("total", 0) == 0 and not invalid:
        invalid.append("collected_0_items")
    n_pass = 0
    for test in report.get("tests", []):
        outcome = test.get("outcome")
        if outcome == "passed":
            n_pass += 1
            continue
        if outcome not in ("failed", "error"):
            continue
        phase = next(
            (
                test.get(p)
                for p in ("setup", "call", "teardown")
                if (test.get(p) or {}).get("outcome") == "failed"
            ),
            {},
        )
        r = _phase_reason(test["nodeid"], outcome, phase, is_test_file, root)
        reasons[r.nodeid] = r
        if not r.valid:
            invalid.append(r.reason)
    n_fail = sum(1 for r in reasons.values() if r.outcome != "collect")
    if n_fail < min_failing and not invalid:
        invalid.append("no_failing_test")
    invalid = sorted(set(invalid))
    return ReportVerdict(
        ok=not invalid,
        exit_code=exit_code,
        n_failing=n_fail,
        n_passing=n_pass,
        reasons={k: asdict(v) for k, v in sorted(reasons.items())},
        invalid=invalid,
    )


def outcomes(report: dict | None) -> dict[str, str]:
    """nodeid -> outcome, the comparable core of a run (for the determinism check)."""
    if report is None:
        return {}
    out = {t["nodeid"]: t.get("outcome", "?") for t in report.get("tests", [])}
    for coll in report.get("collectors", []):
        if coll.get("outcome") == "failed":
            out[coll.get("nodeid") or "<collect>"] = "collect-failed"
    return out
