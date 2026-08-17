"""PythonAdapter: the Python implementation of EcosystemAdapter.

All Python/packaging-specific logic lives here. The hygiene modules orchestrate
(state, audit, container steps); this class turns a repo into a canonical
requirements.in, a fully pinned lock, a Dockerfile, and parses test reports.

The adapter writes ecosystem files (requirements.in, lock, constraints, Dockerfile,
.dockerignore) into ``work_dir`` — the clean repo clone that becomes the build
context — so each task is self-contained. Step JSON records are written by the
hygiene layer, not here.

lint_and_format / symbol_index / mutators land in later sessions (S6/S9).
"""

from __future__ import annotations

import ast
import json
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from packaging.requirements import InvalidRequirement, Requirement
from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import Version

from pipeline.config import DEFAULT, Config
from pipeline.docker.image import resolve_base_digest
from pipeline.ecosystems.base import EcosystemAdapter

_PY_REQUIRES_RE = re.compile(r"""python_requires\s*=\s*['"]([^'"]+)['"]""")
_EXTRAS_BLOCK_RE = re.compile(r"extras_require\s*=\s*\{(.*?)\}", re.DOTALL)
_EXTRAS_KEY_RE = re.compile(r"""['"]([\w][\w.-]*)['"]\s*:""")
_CLASSIFIER_RE = re.compile(r"Programming Language :: Python :: (3\.\d+)")

# import-to-PyPI mapping schema for the SMALL-model fallback
_ALIAS_SCHEMA = {
    "type": "object",
    "properties": {
        "mappings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "import_name": {"type": "string"},
                    "pypi_name": {"type": "string"},
                },
                "required": ["import_name", "pypi_name"],
            },
        }
    },
    "required": ["mappings"],
}


@dataclass
class PackagingInfo:
    style: str  # pyproject | setup.py | setup.cfg | requirements | poetry | none
    manifest: str | None  # repo-relative path fed to uv, if any
    uv_readable: bool  # uv pip compile can read the manifest directly
    installable: bool  # `pip install -e .` works (has package metadata)
    available_extras: list[str] = field(default_factory=list)
    requires_python: str | None = None
    classifiers: list[str] = field(default_factory=list)


class PythonAdapter(EcosystemAdapter):
    name = "python"

    def __init__(
        self, config: Config = DEFAULT, work_dir: Path | None = None, llm: Any = None
    ) -> None:
        self.config = config
        self.work_dir = work_dir  # where ecosystem files are written (the repo clone)
        self.llm = llm
        self.dropped_extras: list[str] = []  # extras dropped by lock()'s bounded fallback
        self.unresolved_imports: list[str] = []  # inferred imports dropped after re-ask
        self._inferred_map: dict[str, str] = {}  # normalized pypi name -> import name
        self._packaging_cache: dict[Path, PackagingInfo] = {}

    # --- detection -------------------------------------------------------------

    def detect(self, repo: Path) -> bool:
        if any((repo / m).exists() for m in self.config.detect.manifest_markers):
            return True
        return any(repo.rglob("*.py"))

    def packaging(self, repo: Path) -> PackagingInfo:
        repo = Path(repo)
        if repo in self._packaging_cache:
            return self._packaging_cache[repo]
        info = self._detect_packaging(repo)
        self._packaging_cache[repo] = info
        return info

    def _detect_packaging(self, repo: Path) -> PackagingInfo:
        pyproject = repo / "pyproject.toml"
        if pyproject.is_file():
            data = _load_toml(pyproject)
            if "project" in data:
                proj = data["project"]
                return PackagingInfo(
                    style="pyproject",
                    manifest="pyproject.toml",
                    uv_readable=True,
                    installable=True,
                    available_extras=list(proj.get("optional-dependencies", {})),
                    requires_python=proj.get("requires-python"),
                    classifiers=list(proj.get("classifiers", [])),
                )
            if "tool" in data and "poetry" in data["tool"]:
                poetry = data["tool"]["poetry"]
                py = poetry.get("dependencies", {}).get("python")
                return PackagingInfo(
                    style="poetry",
                    manifest="pyproject.toml",
                    uv_readable=False,  # uv does not read [tool.poetry]
                    installable=True,
                    available_extras=list(poetry.get("extras", {})),
                    requires_python=py if isinstance(py, str) else None,
                )
        setup_py = repo / "setup.py"
        if setup_py.is_file():
            text = setup_py.read_text(errors="replace")
            return PackagingInfo(
                style="setup.py",
                manifest="setup.py",
                uv_readable=True,
                installable=True,
                available_extras=_setup_py_extras(text),
                requires_python=_search(_PY_REQUIRES_RE, text),
                classifiers=_CLASSIFIER_RE.findall(text),
            )
        if (repo / "setup.cfg").is_file():
            # uv cannot read setup.cfg alone; we parse its deps into requirements.in and
            # write a setup.py shim so `pip install -e .` still works.
            cfg = _read_setup_cfg(repo / "setup.cfg")
            return PackagingInfo(
                style="setup.cfg",
                manifest=None,
                uv_readable=False,
                installable=True,
                available_extras=cfg["extras"],
                requires_python=cfg["requires_python"],
            )
        for name in ("requirements.in", "requirements.txt"):
            if (repo / name).is_file():
                return PackagingInfo(
                    style="requirements", manifest=name, uv_readable=True, installable=False
                )
        return PackagingInfo(style="none", manifest=None, uv_readable=False, installable=False)

    def python_version(self, repo: Path) -> str:
        info = self.packaging(repo)
        cap = Version(self.config.detect.python_version_cap)
        candidates = [Version(f"3.{m}") for m in range(cap.minor, 7, -1)]  # cap..3.8
        spec = _safe_specifier(info.requires_python)
        if spec is not None:
            for v in candidates:
                if spec.contains(str(v), prereleases=False):
                    return str(v)
        classifier_versions = [
            Version(c) for c in _CLASSIFIER_RE.findall("\n".join(info.classifiers))
        ]
        capped = [v for v in classifier_versions if v <= cap]
        if capped:
            return str(max(capped))
        return self.config.detect.python_version_default

    # --- requirements synthesis + lock ----------------------------------------

    def synthesize_requirements(self, repo: Path) -> Path:
        info = self.packaging(repo)
        deps: list[str] = []
        if info.style == "none":
            deps = self._infer_no_manifest_deps(repo)
        elif info.style == "poetry":
            deps = self._translate_poetry(repo)
        elif info.style == "setup.cfg":
            deps = self._setup_cfg_deps(repo)
        tools = list(self.config.detect.test_tools) + list(self.config.detect.dev_tools)
        lines = _dedupe(deps + tools)
        dest = self._out(self.config.pin.requirements_in_filename)
        dest.write_text("\n".join(lines) + "\n")
        return dest

    def lock(self, repo: Path) -> Path:
        info = self.packaging(repo)
        pyver = self.python_version(repo)
        req_in = self._out(self.config.pin.requirements_in_filename)
        inputs: list[str] = []
        if info.uv_readable and info.manifest:
            inputs.append(str(Path(repo) / info.manifest))
        inputs.append(str(req_in))
        extras = (
            [e for e in info.available_extras if e in self.config.pin.include_extras]
            if info.uv_readable
            else []
        )
        lock_path = self._out(self.config.pin.lock_filename)
        self.dropped_extras = []
        self.unresolved_imports = []
        proc = self._compile(pyver, extras, lock_path, inputs)
        if proc.returncode != 0 and extras:
            # Bounded fallback: an extra may pull an unresolvable/heavy dep. Retry once
            # without extras and record what was dropped so it is visible downstream.
            self.dropped_extras = extras
            proc = self._compile(pyver, [], lock_path, inputs)
        proc = self._resolve_inferred_failures(proc, pyver, req_in, lock_path, inputs)
        if proc.returncode != 0:
            raise RuntimeError(f"uv pip compile failed:\n{proc.stderr.strip()}")
        if self.config.pin.emit_constraints_txt:
            self._out(self.config.pin.constraints_filename).write_text(
                _constraints_from_lock(lock_path.read_text())
            )
        return lock_path

    def _resolve_inferred_failures(self, proc, pyver, req_in, lock_path, inputs):
        """On lock failure from an INFERRED import, re-ask the model once for the right
        PyPI name; if it still won't resolve, drop the import and record it. Only
        touches names we inferred (never a manifest dependency)."""
        attempts = self.config.pin.alias_reask_attempts
        while proc.returncode != 0:
            pkg = _parse_unresolvable(proc.stderr)
            imp = self._inferred_map.get(pkg) if pkg else None
            if imp is None:
                break  # not an inferred import -> a real failure; caller raises
            fixed = False
            if attempts > 0 and self.llm is not None:
                attempts -= 1
                new = self._llm_map_imports([imp], error=reask_note(pkg, imp)).get(imp)
                if new and valid_requirement(new) and _norm_req(new) != pkg:
                    _rewrite_requirement(req_in, pkg, new)
                    self._inferred_map.pop(pkg, None)
                    self._inferred_map[_norm_req(new)] = imp
                    proc = self._compile(pyver, [], lock_path, inputs)
                    fixed = True
            if not fixed:
                _rewrite_requirement(req_in, pkg, None)  # drop it
                self._inferred_map.pop(pkg, None)
                self.unresolved_imports.append(imp)
                proc = self._compile(pyver, [], lock_path, inputs)
        return proc

    def _compile(self, pyver: str, extras: list[str], lock_path: Path, inputs: list[str]):
        cmd = ["uv", "pip", "compile", "--python-version", pyver, "--no-header"]
        if self.config.pin.generate_hashes:
            cmd.append("--generate-hashes")
        for extra in extras:
            cmd += ["--extra", extra]
        cmd += ["-o", str(lock_path), *inputs]
        return subprocess.run(cmd, capture_output=True, text=True, check=False)

    def _infer_no_manifest_deps(self, repo: Path) -> list[str]:
        imports = self.infer_third_party_imports(repo)
        alias = self.config.detect.import_alias_table
        unknown = [imp for imp in sorted(imports) if imp not in alias]
        mapped = self._llm_map_imports(unknown) if unknown else {}
        resolved: list[str] = []
        for imp in sorted(imports):
            pypi = alias.get(imp) or mapped.get(imp, imp)
            if not valid_requirement(pypi):  # never write a garbage name to requirements
                self.unresolved_imports.append(imp)
                continue
            resolved.append(pypi)
            self._inferred_map[_norm_req(pypi)] = imp
        return _dedupe(resolved)

    def _llm_map_imports(self, imports: list[str], error: str | None = None) -> dict[str, str]:
        if self.llm is None:
            return {}
        prompt = (
            "Map each Python import name to its PyPI distribution name. If the import "
            "name is already the PyPI name, repeat it.\nImports: " + ", ".join(imports)
        )
        if error:
            prompt += "\n\n" + error
        result = self.llm.complete_json(
            "p1.pin.import_to_pypi", [{"role": "user", "content": prompt}], _ALIAS_SCHEMA
        )
        return {m["import_name"]: m["pypi_name"] for m in result.get("mappings", [])}

    def infer_third_party_imports(self, repo: Path) -> set[str]:
        repo = Path(repo)
        local = _local_module_names(repo)
        stdlib = sys.stdlib_module_names
        found: set[str] = set()
        for path in repo.rglob("*.py"):
            if ".git" in path.parts:
                continue
            try:
                tree = ast.parse(path.read_text(errors="replace"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for a in node.names:
                        found.add(a.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    found.add(node.module.split(".")[0])
        return {n for n in found if n and n not in local and n not in stdlib}

    def _setup_cfg_deps(self, repo: Path) -> list[str]:
        cfg = _read_setup_cfg(repo / "setup.cfg")
        deps = list(cfg["install_requires"])
        for name, extra_deps in cfg["extras_require"].items():
            if name in self.config.pin.include_extras:
                deps += extra_deps
        # shim so `pip install -e .` works (setuptools reads setup.cfg through it)
        shim = repo / "setup.py"
        if not shim.exists():
            shim.write_text("from setuptools import setup\n\nsetup()\n")
        return _dedupe(deps)

    def _translate_poetry(self, repo: Path) -> list[str]:
        data = _load_toml(Path(repo) / "pyproject.toml")
        deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
        out: list[str] = []
        for name, spec in deps.items():
            if name == "python":
                continue
            if isinstance(spec, dict):  # git/path/table forms not translated
                if "version" in spec:
                    out.append(name + _poetry_caret(spec["version"]))
                continue
            out.append(name + _poetry_caret(spec))
        return out

    # --- docker ---------------------------------------------------------------

    def needs_git_metadata(self, repo: Path) -> bool:
        """True if the version is derived from git (needs .git + git in the image)."""
        text = ""
        for name in ("pyproject.toml", "setup.py", "setup.cfg"):
            path = Path(repo) / name
            if path.is_file():
                text += path.read_text(errors="replace")
        return any(tool in text for tool in self.config.detect.git_version_tools)

    def dockerfile(self, repo: Path, lock: Path) -> str:
        info = self.packaging(repo)
        pyver = self.python_version(repo)
        base = resolve_base_digest(self.config.docker.base_image.format(py=pyver))
        install_repo = (
            "RUN pip install --no-deps -e ." if info.installable else "ENV PYTHONPATH=/repo"
        )
        cmd = json.dumps(shlex.split(self.test_command(repo)))
        lines = [
            f"FROM {base}",
            "WORKDIR /repo",
            "ENV PYTHONDONTWRITEBYTECODE=1 PIP_DISABLE_PIP_VERSION_CHECK=1",
        ]
        if self.needs_git_metadata(repo):
            # git-derived version: install git so the build can read the tags in .git
            lines.append(
                "RUN apt-get update && apt-get install -y --no-install-recommends git "
                "&& rm -rf /var/lib/apt/lists/*"
            )
        lines += [
            f"COPY {lock.name} .",
            f"RUN pip install --no-deps --require-hashes -r {lock.name}",
            "COPY . .",
            install_repo,
            f"CMD {cmd}",
            "",
        ]
        return "\n".join(lines)

    def write_dockerfile(self, repo: Path, lock: Path) -> Path:
        content = self.dockerfile(repo, lock)
        (Path(repo) / "Dockerfile").write_text(content)
        # Keep .git in the build context only when the version is derived from it.
        ignore = (
            "__pycache__/\n*.pyc\n"
            if self.needs_git_metadata(repo)
            else ".git\n__pycache__/\n*.pyc\n"
        )
        (Path(repo) / ".dockerignore").write_text(ignore)
        return Path(repo) / "Dockerfile"

    # --- tests ----------------------------------------------------------------

    def test_framework(self, repo: Path) -> str:
        repo = Path(repo)
        pytest_markers = ("pytest.ini", "tox.ini", "conftest.py", "setup.cfg")
        if any((repo / m).is_file() for m in pytest_markers) or list(repo.rglob("test_*.py")):
            return "pytest"
        if list(repo.rglob("test*.py")):
            return "unittest"
        return "none"

    def test_command(self, repo: Path) -> str:
        return "python -m pytest -q"

    def reporting_command(
        self, repo: Path, report_rel: str, deselect: list[str] | None = None
    ) -> str:
        parts = [
            "python -m pytest -p no:cacheprovider -q",
            f"--json-report --json-report-file={report_rel}",
        ]
        for nodeid in deselect or []:
            parts.append(f"--deselect {shlex.quote(nodeid)}")
        return " ".join(parts)

    def verifier_command(self, nodeids: list[str]) -> str:
        """The documented command that runs exactly these tests (no report flags)."""
        return " ".join([self.test_command(Path(".")), *(shlex.quote(n) for n in nodeids)])

    def with_report(self, cmd: str, report_rel: str) -> str:
        """Same run, plus the structured report the harness parses (pytest accepts
        options after positional nodeids)."""
        return f"{cmd} -p no:cacheprovider --json-report --json-report-file={report_rel}"

    def test_framework_bootstrap(self, repo: Path) -> None:
        repo = Path(repo)
        tests = repo / "tests"
        tests.mkdir(exist_ok=True)
        conftest = tests / "conftest.py"
        if not conftest.exists():
            conftest.write_text("# bootstrapped by pipeline; generated tests land here (S6)\n")

    def parse_test_report(self, path: Path) -> dict[str, dict[str, str]]:
        return self.parse_test_report_data(json.loads(Path(path).read_text()))

    def parse_test_report_data(self, data: dict) -> dict[str, dict[str, str]]:
        results: dict[str, dict[str, str]] = {}
        status_map = {
            "passed": "pass",
            "failed": "fail",
            "skipped": "skip",
            "xfailed": "skip",
            "xpassed": "skip",
            "error": "error",
        }
        for test in data.get("tests", []):
            outcome = test.get("outcome", "error")
            status = status_map.get(outcome, "error")
            reason = ""
            if status not in ("pass", "skip"):
                for phase in ("call", "setup", "teardown"):
                    info = test.get(phase) or {}
                    if info.get("outcome") == "failed":
                        reason = (
                            info.get("longrepr") or info.get("crash", {}).get("message") or ""
                        )[:2000]
                        break
            results[test["nodeid"]] = {"status": status, "reason": reason}
        for collector in data.get("collectors", []):
            if collector.get("outcome") == "failed":
                results.setdefault(
                    collector.get("nodeid") or "<collect>",
                    {"status": "error", "reason": (collector.get("longrepr") or "")[:2000]},
                )
        return results

    # --- deferred to later sessions -------------------------------------------

    def lint_and_format(self, repo: Path, run) -> dict[str, Any]:
        """ruff check --fix + ruff format, driven by a ``[tool.ruff]`` config we write
        into the tree. Unfixable findings get a per-file ``# noqa`` (when configured);
        the exact ruff comes from the pinned image via ``run``. Historical task trees
        live outside this tree and are never touched here."""
        repo = Path(repo)
        lint = self.config.lint
        created = self._ensure_ruff_config(repo)
        report: dict[str, Any] = {
            "config_created": created,
            "select": list(lint.rules),
            "commands": [],
            "noqa": {},
            "unfixable": [],
            "remaining": [],
        }
        if lint.autofix:
            fix = f"ruff check --fix {_shq(lint.rules)} ."
            report["commands"].append(fix)
            run(fix)
        if lint.format:
            report["commands"].append("ruff format .")
            run("ruff format .")
        findings = self._ruff_findings(run)
        report["unfixable"] = _finding_summary(findings)
        if findings and lint.allow_noqa_for_unfixable:
            # Apply the noqa edits IN-CONTAINER: a host write to the bind-mounted tree can
            # be read mid-flush by the next container as a truncated file (spurious
            # F841/W292). Container-write → container-read is coherent.
            report["noqa"] = _apply_noqa_in_container(run, findings)
            findings = self._ruff_findings(run)
        report["remaining"] = _finding_summary(findings)
        report["clean"] = not findings
        report["codes"] = _code_counts(report["unfixable"])
        return report

    def _ruff_config_present(self, repo: Path) -> bool:
        if (repo / "ruff.toml").is_file() or (repo / ".ruff.toml").is_file():
            return True
        py = repo / "pyproject.toml"
        return py.is_file() and "[tool.ruff" in py.read_text(errors="replace")

    def _ensure_ruff_config(self, repo: Path) -> bool:
        """Write a ``[tool.ruff.lint]`` config into pyproject.toml (creating a minimal
        pyproject with NO ``[build-system]`` if absent, so a legacy setup.py install is
        unaffected). Returns True iff a pyproject.toml was created. An existing ruff
        config is respected (never clobbered)."""
        if self._ruff_config_present(repo):
            return False
        select = ", ".join(f'"{r}"' for r in self.config.lint.rules)
        block = (
            "# Added by the benchmark pipeline (P1 lint/format).\n"
            "[tool.ruff.lint]\n"
            f"select = [{select}]\n"
        )
        py = repo / "pyproject.toml"
        if py.is_file():
            py.write_text(py.read_text().rstrip() + "\n\n" + block)
            return False
        py.write_text(block)
        return True

    def _ruff_findings(self, run) -> list[dict]:
        """Current ruff findings as JSON (empty when clean). Uses the pinned image."""
        result = run(f"ruff check --output-format json {_shq(self.config.lint.rules)} .")
        text = (result.stdout or "").strip()
        if not text:
            return []
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return []

    def symbol_index(self, repo: Path) -> dict[str, Any]:
        from pipeline.ecosystems.symbols import build_symbol_index

        return build_symbol_index(Path(repo), self.config)

    def mutators(self) -> list:
        """AST mutation operators named in ``testgen.mutators``. Each is a callable
        ``(function_span_source) -> [mutant_span_source, ...]`` whose mutants parse and
        differ from the original; the driver in ``hygiene/mutate.py`` splices them back
        by line span so the rest of the file stays byte-identical."""
        return [_MUTATORS[name] for name in self.config.testgen.mutators if name in _MUTATORS]

    # --- helpers --------------------------------------------------------------

    def _out(self, name: str) -> Path:
        if self.work_dir is None:
            raise ValueError("PythonAdapter needs work_dir to write ecosystem files")
        self.work_dir.mkdir(parents=True, exist_ok=True)
        return self.work_dir / name


_UNRESOLVABLE_RE = re.compile(r"Because (\S+) was not found in the package registry")
_PKG_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def valid_requirement(spec: str) -> bool:
    """True if `spec` is a syntactically valid requirement with a sane distribution name."""
    spec = (spec or "").strip()
    if not spec:
        return False
    try:
        req = Requirement(spec)
    except InvalidRequirement:
        return False
    return bool(_PKG_NAME_RE.match(req.name))


# --- lint helpers -------------------------------------------------------------


def _shq(rules: tuple[str, ...]) -> str:
    """`--select E,F,W,...` so the CLI enforces our rule set regardless of any
    stray repo config, matching the ``[tool.ruff.lint] select`` we write."""
    return "--select " + shlex.quote(",".join(rules)) if rules else ""


# The synced tree is bind-mounted at this path inside the container (see docker/runner),
# so ruff's absolute `filename` (e.g. /repo/pkg/mod.py) maps back by stripping this prefix.
CONTAINER_MOUNT = "/repo"


def _container_rel(filename: str) -> str:
    """Map a ruff-reported path (absolute `/repo/...` or relative `./...`) to a
    tree-relative path, so a host-side edit lands on the right file."""
    name = filename.removeprefix(CONTAINER_MOUNT).lstrip("/")
    return name[2:] if name.startswith("./") else name


def _finding_summary(findings: list[dict]) -> list[dict]:
    """Compact, deterministic {file, code, line} list from ruff's JSON output."""
    out = [
        {
            "file": _container_rel(f.get("filename", "")),
            "code": f.get("code") or "",
            "line": (f.get("location") or {}).get("row", 0),
        }
        for f in findings
    ]
    return sorted(out, key=lambda x: (x["file"], x["line"], x["code"]))


def _code_counts(summary: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in summary:
        counts[item["code"]] = counts.get(item["code"], 0) + 1
    return dict(sorted(counts.items()))


def _noqa_plan(findings: list[dict]) -> dict[str, dict[int, list[str]]]:
    """{repo-relative file -> {row -> sorted codes}} from ruff's JSON. ruff reports paths
    inside the container mount (``/repo/...``); ``_container_rel`` maps them back."""
    by_line: dict[str, dict[int, set[str]]] = {}
    for f in findings:
        name = _container_rel(f.get("filename", ""))
        row = (f.get("location") or {}).get("row", 0)
        code = f.get("code") or ""
        if name and row and code:
            by_line.setdefault(name, {}).setdefault(row, set()).add(code)
    return {
        name: {row: sorted(codes) for row, codes in sorted(rows.items())}
        for name, rows in sorted(by_line.items())
    }


def _apply_plan_to_text(text: str, rows: dict[int, list[str]]) -> str:
    """Append ``# noqa: <codes>`` to the given 1-indexed rows of ``text``."""
    lines = text.splitlines(keepends=True)
    for row, codes in rows.items():
        if row < 1 or row > len(lines):
            continue
        raw = lines[row - 1]
        body, nl = (raw[:-1], raw[-1]) if raw.endswith("\n") else (raw, "")
        if "# noqa" in body:
            continue
        lines[row - 1] = f"{body}  # noqa: {', '.join(codes)}{nl}"
    return "".join(lines)


def _apply_noqa(repo: Path, findings: list[dict]) -> dict[str, list[str]]:
    """Host-side ``# noqa`` application (used off-container and unit-tested). Returns
    {repo-relative file: sorted codes applied}."""
    plan = _noqa_plan(findings)
    applied: dict[str, list[str]] = {}
    for name, rows in plan.items():
        path = repo / name
        if not path.is_file():
            continue
        path.write_text(_apply_plan_to_text(path.read_text(), rows))
        applied[name] = sorted({c for codes in rows.values() for c in codes})
    return applied


# In-container noqa applier: the same edit, but performed by the container so it never
# races a host write against the next container's read. The plan is embedded as base64
# (no shell-quoting hazards) and applied by a small python program run via ``run``.
_NOQA_APPLIER = r"""
import base64, json, sys
plan = json.loads(base64.b64decode(sys.argv[1]).decode())
for name, rows in plan.items():
    try:
        with open(name, encoding="utf-8") as fh:
            lines = fh.readlines()
    except OSError:
        continue
    for row, codes in rows.items():
        i = int(row) - 1
        if i < 0 or i >= len(lines):
            continue
        raw = lines[i]
        body, nl = (raw[:-1], raw[-1]) if raw.endswith("\n") else (raw, "")
        if "# noqa" in body:
            continue
        lines[i] = body + "  # noqa: " + ", ".join(codes) + nl
    with open(name, "w", encoding="utf-8") as fh:
        fh.writelines(lines)
"""


def _apply_noqa_in_container(run, findings: list[dict]) -> dict[str, list[str]]:
    import base64

    plan = _noqa_plan(findings)
    if not plan:
        return {}
    data = base64.b64encode(json.dumps(plan).encode()).decode()
    prog = base64.b64encode(_NOQA_APPLIER.encode()).decode()
    run(f"python3 -c \"import base64;exec(base64.b64decode('{prog}').decode())\" {data}")
    return {
        name: sorted({c for codes in rows.values() for c in codes})
        for name, rows in plan.items()
    }


def _norm_req(spec: str) -> str:
    """Normalized distribution name from a requirement string (name only, PEP 503-ish)."""
    name = re.split(r"[<>=!~;\s\[]", spec.strip(), maxsplit=1)[0]
    return name.lower().replace("_", "-")


def _parse_unresolvable(stderr: str) -> str | None:
    """The normalized package name uv reports as not found, if any."""
    m = _UNRESOLVABLE_RE.search(" ".join(stderr.split()))
    return _norm_req(m.group(1)) if m else None


def reask_note(pkg: str, imp: str) -> str:
    return (
        f"Package '{pkg}' was not found in the package registry (mapped from import "
        f"'{imp}'). Provide the correct PyPI name."
    )


def _rewrite_requirement(req_in: Path, norm_name: str, new: str | None) -> None:
    """Replace (new given) or drop (new None) the requirement line matching norm_name."""
    kept = []
    for line in req_in.read_text().splitlines():
        if line.strip() and _norm_req(line) == norm_name:
            if new is not None:
                kept.append(new)
        else:
            kept.append(line)
    req_in.write_text("\n".join(kept) + "\n")


def _load_toml(path: Path) -> dict:
    import tomllib

    return tomllib.loads(path.read_text())


def _read_setup_cfg(path: Path) -> dict:
    """Parse install_requires / extras_require / python_requires from a setup.cfg."""
    import configparser

    cp = configparser.ConfigParser()
    cp.read(path)

    def _lines(section: str, key: str) -> list[str]:
        raw = cp.get(section, key, fallback="")
        return [ln.strip() for ln in raw.splitlines() if ln.strip()]

    extras_require: dict[str, list[str]] = {}
    if cp.has_section("options.extras_require"):
        for name in cp.options("options.extras_require"):
            extras_require[name] = _lines("options.extras_require", name)
    return {
        "install_requires": _lines("options", "install_requires"),
        "extras_require": extras_require,
        "extras": list(extras_require),
        "requires_python": cp.get("options", "python_requires", fallback=None),
    }


def _search(regex: re.Pattern, text: str) -> str | None:
    m = regex.search(text)
    return m.group(1) if m else None


def _setup_py_extras(text: str) -> list[str]:
    block = _EXTRAS_BLOCK_RE.search(text)
    return _EXTRAS_KEY_RE.findall(block.group(1)) if block else []


def _safe_specifier(spec: str | None) -> SpecifierSet | None:
    if not spec:
        return None
    try:
        return SpecifierSet(spec)
    except InvalidSpecifier:
        return None


def _local_module_names(repo: Path) -> set[str]:
    names: set[str] = set()
    for child in repo.iterdir():
        if child.is_dir() and (child / "__init__.py").exists():
            names.add(child.name)
        elif child.suffix == ".py":
            names.add(child.stem)
    return names


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def _poetry_caret(spec: str) -> str:
    spec = spec.strip()
    if spec in ("*", ""):
        return ""
    if spec[0] in "^~":
        base = spec[1:]
        parts = base.split(".")
        upper = str(int(parts[0]) + 1) + ".0.0" if spec[0] == "^" else _tilde_upper(parts)
        return f">={base},<{upper}"
    return spec if spec[0] in "<>=!" else f"=={spec}"


def _tilde_upper(parts: list[str]) -> str:
    if len(parts) >= 2:
        return f"{parts[0]}.{int(parts[1]) + 1}.0"
    return f"{int(parts[0]) + 1}.0.0"


def _constraints_from_lock(lock_text: str) -> str:
    lines = []
    for raw in lock_text.splitlines():
        if raw and not raw[0].isspace() and not raw.startswith("#") and "==" in raw:
            lines.append(raw.split(" ")[0].split(";")[0].strip())
    return "\n".join(lines) + "\n"


# --- AST mutation operators (S6 test-gen + verifier discrimination) ------------
#
# Each operator takes a function's source span and returns mutants that parse and
# differ from it. Operators work on the dedented span (so method bodies parse),
# mutate one site per mutant, and re-emit via ``ast.unparse`` re-indented to the
# original column; the driver splices the whole span back by line range, so text
# outside the mutated function is untouched. Formatting inside the mutant is not
# preserved -- only behavior-changing edits matter for the mutation gate.

_CMP_FLIP = {
    ast.Lt: ast.Gt, ast.Gt: ast.Lt, ast.LtE: ast.GtE, ast.GtE: ast.LtE,
    ast.Eq: ast.NotEq, ast.NotEq: ast.Eq, ast.Is: ast.IsNot, ast.IsNot: ast.Is,
    ast.In: ast.NotIn, ast.NotIn: ast.In,
}  # fmt: skip
_CMP_BOUNDARY = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt}
_ARITH = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Div, ast.Div: ast.Mult}
_BOOL = {ast.And: ast.Or, ast.Or: ast.And}


def _dedent_span(span: str) -> tuple[str, str]:
    """Strip the common leading indentation (the def's column) so the span parses;
    return the dedented text and the stripped prefix."""
    lines = span.splitlines()
    indents = [len(ln) - len(ln.lstrip()) for ln in lines if ln.strip()]
    pad = min(indents) if indents else 0
    dedented = "\n".join(ln[pad:] if ln.strip() else "" for ln in lines)
    return dedented, " " * pad


def _reindent(text: str, prefix: str) -> str:
    body = "\n".join(prefix + ln if ln.strip() else "" for ln in text.splitlines())
    return body + "\n"


def _variants(span: str, collect, mutate) -> list[str]:
    """For each site ``collect`` finds, re-parse the span, mutate that one site and
    unparse; keep mutants that parse and differ from the original."""
    dedented, prefix = _dedent_span(span)
    try:
        base = ast.parse(dedented)
    except SyntaxError:
        return []
    original = ast.unparse(base)
    count = len(collect(base))
    out: list[str] = []
    for i in range(count):
        tree = ast.parse(dedented)
        mutate(collect(tree)[i])
        try:
            emitted = ast.unparse(ast.fix_missing_locations(tree))
        except (ValueError, TypeError):
            continue
        if emitted != original:
            out.append(_reindent(emitted, prefix))
    return out


def _compare_sites(tree: ast.AST, table: dict) -> list[tuple[ast.Compare, int]]:
    sites = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            sites.extend((node, i) for i, op in enumerate(node.ops) if type(op) in table)
    return sites


def _cmp_mutator(table: dict):
    def run(span: str) -> list[str]:
        def mutate(site):
            node, i = site
            node.ops[i] = table[type(node.ops[i])]()

        return _variants(span, lambda t: _compare_sites(t, table), mutate)

    return run


def _binop_mutator(table: dict):
    def collect(tree):
        return [
            n for n in ast.walk(tree) if isinstance(n, ast.BinOp) and type(n.op) in table
        ]

    def run(span: str) -> list[str]:
        def mutate(node):
            node.op = table[type(node.op)]()

        return _variants(span, collect, mutate)

    return run


def _boolop_mutator(span: str) -> list[str]:
    def collect(tree):
        return [n for n in ast.walk(tree) if isinstance(n, ast.BoolOp) and type(n.op) in _BOOL]

    def mutate(node):
        node.op = _BOOL[type(node.op)]()

    return _variants(span, collect, mutate)


def _return_none_mutator(span: str) -> list[str]:
    def collect(tree):
        return [
            n
            for n in ast.walk(tree)
            if isinstance(n, ast.Return)
            and n.value is not None
            and not (isinstance(n.value, ast.Constant) and n.value.value is None)
        ]

    def mutate(node):
        node.value = ast.Constant(value=None)

    return _variants(span, collect, mutate)


def _tweakable(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and (
        isinstance(node.value, bool) or isinstance(node.value, (int, float))
    )


def _constant_tweak_mutator(span: str) -> list[str]:
    def collect(tree):
        return [n for n in ast.walk(tree) if _tweakable(n)]

    def mutate(node):
        node.value = (not node.value) if isinstance(node.value, bool) else node.value + 1

    return _variants(span, collect, mutate)


_UNDELETABLE = (ast.Pass, ast.Return, ast.Raise, ast.Break, ast.Continue)
# def/class statements define the code under test; deleting them breaks imports.
_NOT_A_STATEMENT_MUTANT = (*_UNDELETABLE, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def _statement_delete_mutator(span: str) -> list[str]:
    """Delete one statement; ``pass``/control-flow statements and docstrings are left
    alone (deleting them rarely changes behavior). Emptied blocks get a ``pass``."""

    def bodies(tree):
        # Skip the module body: its statements are the def/class under test, and
        # deleting those breaks imports instead of testing behavior.
        for node in ast.walk(tree):
            if isinstance(node, ast.Module):
                continue
            for attr in ("body", "orelse", "finalbody"):
                block = getattr(node, attr, None)
                if isinstance(block, list) and all(isinstance(s, ast.stmt) for s in block):
                    yield node, attr, block

    def collect(tree):
        sites = []
        for node, attr, block in bodies(tree):
            for i, stmt in enumerate(block):
                if isinstance(stmt, _NOT_A_STATEMENT_MUTANT):
                    continue
                if i == 0 and isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                    continue  # docstring
                sites.append((node, attr, i))
        return sites

    def mutate(site):
        node, attr, i = site
        block = getattr(node, attr)
        del block[i]
        if not block:
            block.append(ast.Pass())

    return _variants(span, collect, mutate)


def _named(name: str, fn):
    fn.__name__ = name
    return fn


_MUTATORS = {
    "comparison_flip": _named("comparison_flip", _cmp_mutator(_CMP_FLIP)),
    "comparison_boundary": _named("comparison_boundary", _cmp_mutator(_CMP_BOUNDARY)),
    "arithmetic_swap": _named("arithmetic_swap", _binop_mutator(_ARITH)),
    "and_or_swap": _named("and_or_swap", _boolop_mutator),
    "return_none": _named("return_none", _return_none_mutator),
    "constant_tweak": _named("constant_tweak", _constant_tweak_mutator),
    "statement_delete": _named("statement_delete", _statement_delete_mutator),
}
