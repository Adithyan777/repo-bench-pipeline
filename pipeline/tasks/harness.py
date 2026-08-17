"""Validation harness (DESIGN 5.5): ``validate_task(task_dir) -> verdict``.

Pure code. Every command runs via ``run_in_container`` against the image recorded in
task.json, on a fresh workdir per run. The canonical ``verifier/`` is ALWAYS re-copied
over the workdir before judging. Evidence (real container stdout/stderr + structured
JSON) is written to ``<task>/evidence/``; ``verdict.json`` is the only place a task's
validation status comes from.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from pipeline.config import DEFAULT, Config
from pipeline.docker.image import build_image, image_id
from pipeline.docker.runner import CommandResult, fresh_workdir, run_in_container
from pipeline.ecosystems.python import PythonAdapter
from pipeline.ecosystems.source_ops import (
    is_private_dotted,
    module_bound_names,
    read_source,
    verifier_imports,
)
from pipeline.ecosystems.symbols import build_symbol_index, is_test_path
from pipeline.tasks.classify import ReportVerdict, classify_report, outcomes


@dataclass
class RunOutcome:
    cmd: str
    result: CommandResult
    report: dict | None
    outcomes: dict[str, str] = field(default_factory=dict)

    def log(self) -> str:
        return (
            f"$ {self.cmd}\nexit_code={self.result.exit_code}\n"
            f"--- stdout ---\n{self.result.stdout}\n--- stderr ---\n{self.result.stderr}\n"
        )

    def summary(self) -> dict:
        return {"exit_code": self.result.exit_code, "outcomes": self.outcomes}


class Harness:
    def __init__(self, task_dir: Path, config: Config = DEFAULT):
        self.task_dir = Path(task_dir)
        self.config = config
        self.task = json.loads((self.task_dir / config.tasks.task_json).read_text())
        self.adapter = PythonAdapter(config=config)
        self.evidence = self.task_dir / config.harness.evidence_dirname
        self.verifier_dir = self.task_dir / "verifier"
        self.verifier_files = sorted(
            str(p.relative_to(self.verifier_dir))
            for p in self.verifier_dir.rglob("*")
            if p.is_file()
        )
        self._image = self.task["image_tag"]

    # -- primitives ---------------------------------------------------------------

    def _is_test_file(self, rel: str) -> bool:
        return rel in self.verifier_files or is_test_path(Path("/r"), Path("/r") / rel, self.config)

    def _run(
        self, tree: str, cmd: str, report_rel: str, overlay_verifier: bool = True
    ) -> RunOutcome:
        with fresh_workdir(self.task_dir / tree) as work:
            if overlay_verifier and self.config.harness.recopy_canonical_verifier:
                shutil.copytree(self.verifier_dir, work, dirs_exist_ok=True)
            result = run_in_container(work, cmd, self._image)
            report_path = work / report_rel
            report = json.loads(report_path.read_text()) if report_path.is_file() else None
        return RunOutcome(cmd, result, report, outcomes(report))

    def _verifier_run(self, tree: str) -> RunOutcome:
        cmd = self.adapter.with_report(
            self.task["verifier_cmd"], self.config.harness.report_filename
        )
        return self._run(tree, cmd, self.config.harness.report_filename)

    # -- checks -------------------------------------------------------------------

    def check_fail_before(self, run: RunOutcome) -> tuple[dict, ReportVerdict]:
        hc = self.config.harness
        rv = classify_report(
            run.report,
            run.result.exit_code,
            self._is_test_file,
            min_failing=hc.min_failing_tests,
            valid_reasons=hc.valid_fail_reasons,
            invalid_reasons=hc.invalid_fail_reasons,
        )
        failed = run.result.exit_code != 0 and rv.n_failing >= hc.min_failing_tests
        check = {
            "ok": failed,
            "exit_code": run.result.exit_code,
            "n_failing": rv.n_failing,
            "n_passing": rv.n_passing,
        }
        return check, rv

    def check_pass_after(self, run: RunOutcome) -> dict:
        s = (run.report or {}).get("summary", {})
        bad = s.get("failed", 0) + s.get("error", 0)
        ok = (
            run.result.exit_code == 0
            and run.report is not None
            and s.get("passed", 0) > 0
            and bad == 0
        )
        return {
            "ok": ok,
            "exit_code": run.result.exit_code,
            "n_passing": s.get("passed", 0),
            "n_failing": bad,
        }

    def check_determinism(self, first_fail: RunOutcome, first_pass: RunOutcome) -> dict:
        n = self.config.harness.determinism_runs
        fails, passes = [first_fail.summary()], [first_pass.summary()]
        for _ in range(1, n):
            fails.append(self._verifier_run("input").summary())
            passes.append(self._verifier_run("solution").summary())
        identical = all(f == fails[0] for f in fails) and all(p == passes[0] for p in passes)
        data = {"runs": n, "identical": identical, "fail_before": fails, "pass_after": passes}
        _write_json(self.evidence / self.config.harness.determinism_filename, data)
        return {"ok": identical, "runs": n}

    def check_collateral(self) -> dict:
        col = self.task.get("collateral")
        if not col:
            _write_json(
                self.evidence / self.config.harness.collateral_filename,
                {"skipped": True, "reason": "no baseline test set recorded"},
            )
            return {"ok": True, "skipped": True}
        run = self._run("solution", col["cmd"], col["report"])
        (self.evidence / self.config.harness.collateral_log).write_text(run.log())
        results = self.adapter.parse_test_report_data(run.report) if run.report else {}
        status = {t: results.get(t, {}).get("status", "missing") for t in col["baseline_passing"]}
        newly_failing = sorted(t for t, st in status.items() if st in ("fail", "error"))
        # A baseline-passing test that is now skipped or not collected did not run on the
        # solution: treated as failure-to-run (strict), listed separately.
        not_run = sorted(t for t, st in status.items() if st not in ("pass", "fail", "error"))
        ok = run.report is not None and not newly_failing and not not_run
        data = {
            "cmd": col["cmd"],
            "exit_code": run.result.exit_code,
            "baseline_passing": len(col["baseline_passing"]),
            "still_passing": sum(1 for st in status.values() if st == "pass"),
            "newly_failing": newly_failing,
            "not_run": not_run,
            "report_present": run.report is not None,
        }
        _write_json(self.evidence / self.config.harness.collateral_filename, data)
        _write_json(
            self.evidence / self._raw_name(self.config.harness.collateral_log), run.report or {}
        )
        return {
            "ok": ok,
            "newly_failing": len(newly_failing),
            "not_run": len(not_run),
            "report_present": run.report is not None,
        }

    def check_static_gate(self) -> dict:
        if not self.config.harness.verifier_may_only_import_public_symbols_in_input:
            return {"ok": True, "skipped": True}
        violations = static_gate_violations(self.task_dir / "input", self.verifier_dir, self.config)
        return {"ok": not violations, "violations": violations}

    def check_image(self) -> dict:
        live = image_id(self._image)
        built = False
        if live is None and self.config.harness.build_image_if_missing:
            if (self.task_dir / "input" / "Dockerfile").is_file():
                live = build_image(self.task_dir / "input", self._image)
                built = True
        recorded = self.task.get("image_digest")
        present = live is not None
        matches = present and live == recorded
        ok = present and (matches or not self.config.harness.gate_on_image_digest)
        return {
            "ok": ok,
            "present": present,
            "built_from_input": built,
            "digest_matches_task": matches,
            "live_digest": live,
            "environment_hashes": self._environment_hashes(),
        }

    def _environment_hashes(self) -> dict:
        """sha256 of the environment definition shipped inside input/ (Dockerfile + lock),
        so a verdict pins WHAT was built even though image Ids change on rebuild."""
        out = {}
        for name in ("Dockerfile", self.config.pin.lock_filename):
            path = self.task_dir / "input" / name
            out[name] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        return out

    def _raw_name(self, log_name: str) -> str:
        return log_name.rsplit(".", 1)[0] + self.config.harness.raw_report_suffix

    # -- driver -------------------------------------------------------------------

    def run(self) -> dict:
        hc = self.config.harness
        started = _now()
        self.evidence.mkdir(parents=True, exist_ok=True)
        checks: dict[str, dict] = {"image": self.check_image()}
        reasons: list[str] = []
        if not checks["image"]["ok"]:
            reasons.append(
                "image-unavailable" if not checks["image"]["present"] else "image-digest-mismatch"
            )
            return self._verdict(False, checks, reasons, started)

        fail_run = self._verifier_run("input")
        (self.evidence / hc.fail_before_log).write_text(fail_run.log())
        _write_json(self.evidence / self._raw_name(hc.fail_before_log), fail_run.report or {})
        checks["fail_before"], rv = self.check_fail_before(fail_run)
        checks["right_reason"] = {
            "ok": rv.ok if hc.strict_fail_reason else True,
            "invalid": rv.invalid,
            "tests": rv.reasons,
        }
        if not checks["fail_before"]["ok"]:
            reasons.append("input-does-not-fail")
        if hc.strict_fail_reason and not rv.ok:
            reasons.extend(f"fail-reason:{r}" for r in rv.invalid)

        pass_run = self._verifier_run("solution")
        (self.evidence / hc.pass_after_log).write_text(pass_run.log())
        _write_json(self.evidence / self._raw_name(hc.pass_after_log), pass_run.report or {})
        checks["pass_after"] = self.check_pass_after(pass_run)
        if not checks["pass_after"]["ok"]:
            reasons.append("solution-does-not-pass")

        checks["determinism"] = self.check_determinism(fail_run, pass_run)
        if not checks["determinism"]["ok"]:
            reasons.append("nondeterministic")

        run_collateral = (
            self.task["provenance"]["type"] != "excision" or hc.run_collateral_for_excision
        )
        checks["collateral"] = (
            self.check_collateral() if run_collateral else {"ok": True, "skipped": True}
        )
        if not checks["collateral"]["ok"]:
            reasons.append("collateral-breakage")

        checks["static_gate"] = self.check_static_gate()
        if not checks["static_gate"]["ok"]:
            reasons.append("verifier-imports-non-public-or-missing")
        return self._verdict(not reasons, checks, reasons, started)

    def _verdict(self, valid: bool, checks: dict, reasons: list[str], started: str) -> dict:
        verdict = {
            "task_id": self.task["id"],
            "valid": valid,
            "checks": checks,
            "reasons": reasons,
            "repeat_count": self.config.harness.determinism_runs,
            "image_tag": self._image,
            "image_digest": checks["image"].get("live_digest"),
            "task_image_digest": self.task.get("image_digest"),
            "environment_hashes": checks["image"].get("environment_hashes"),
            "timestamps": {"started": started, "finished": _now()},
        }
        _write_json(self.evidence / self.config.harness.verdict_filename, verdict)
        return verdict


def static_gate_violations(
    input_dir: Path, verifier_dir: Path, config: Config = DEFAULT
) -> list[dict]:
    """Verifier tests may only import (a) repo modules that exist in input/ and (b) names
    those modules bind at top level, none starting with '_'."""
    symbols = build_symbol_index(input_dir, config)
    modules = {m["name"]: m for m in symbols["modules"]}
    top_pkgs = {m.split(".")[0] for m in modules}
    names_cache: dict[str, set[str]] = {}

    def bound(mod: str, depth: int = 0) -> set[str] | None:
        if mod not in modules:
            return None
        if mod not in names_cache:
            names, stars = module_bound_names(read_source(input_dir / modules[mod]["file"]))
            names_cache[mod] = names
            for star in stars:
                target = _resolve_relative(star, mod, modules[mod]["is_package"])
                if depth < 3 and (sub := bound(target, depth + 1)) is not None:
                    names |= {n for n in sub if not n.startswith("_")}
            names_cache[mod] = names
        return names_cache[mod]

    violations: list[dict] = []
    for test_file in sorted(verifier_dir.rglob("*.py")):
        rel = str(test_file.relative_to(verifier_dir))
        package = _package_of(rel, modules)
        for use in verifier_imports(read_source(test_file), package):
            top = use.module.split(".")[0]
            if top not in top_pkgs:
                continue  # third-party / stdlib: not our concern
            target = use.module if use.name is None else f"{use.module}.{use.name}"
            if use.name != "*" and is_private_dotted(target):
                reason = "private-module" if is_private_dotted(use.module) else "private-symbol"
                violations.append(
                    {"file": rel, "line": use.line, "import": target, "reason": reason}
                )
                continue
            if use.name is None or use.module not in modules:
                # `import pkg.sub` / a module we cannot see statically (toolz's `tlz` builds
                # its submodules at import time): existence is proven by the container
                # runs (fail-before / pass-after), not judged here.
                continue
            if use.name == "*":
                continue
            names = bound(use.module) or set()
            if use.name not in names and f"{use.module}.{use.name}" not in modules:
                violations.append(
                    {
                        "file": rel,
                        "line": use.line,
                        "import": f"{use.module}.{use.name}",
                        "reason": "symbol-missing-in-input",
                    }
                )
    return violations


def _resolve_relative(star: str, module: str, is_package: bool) -> str:
    if not star.startswith("."):
        return star
    level = len(star) - len(star.lstrip("."))
    base = module.split(".") if is_package else module.split(".")[:-1]
    base = base[: len(base) - level + 1]
    rest = star.lstrip(".")
    return ".".join(p for p in [*base, rest] if p)


def _package_of(rel: str, modules: dict[str, dict]) -> str:
    """Dotted package a verifier file lives in, from the input module table."""
    parent = str(Path(rel).parent)
    for name, m in modules.items():
        if m["is_package"] and str(Path(m["file"]).parent) == parent:
            return name
    return ""


def validate_task(task_dir: Path, config: Config = DEFAULT) -> dict:
    return Harness(task_dir, config).run()


def validate_tasks(task_dirs: list[Path], config: Config = DEFAULT) -> dict[str, dict]:
    workers = max(1, config.docker.harness_parallel_workers)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda d: validate_task(d, config), task_dirs))
    return {str(d): v for d, v in zip(task_dirs, results, strict=True)}


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")
