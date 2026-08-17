"""EcosystemAdapter: the only ecosystem-specific surface in the pipeline.

Everything else (agent loop, harness, funnels, okf writer, docker runner) is
ecosystem-agnostic. Adding a JS adapter means implementing these methods.

Construction contract: adapters are constructed per-repo with run context —
``Adapter(config, work_dir, llm)`` — where ``work_dir`` is the clean repo clone the
adapter writes ecosystem files into (requirements.in, lock, Dockerfile, …) and
``llm`` is an optional ``LLMClient`` for ecosystem-specific model calls (e.g. the
import→PyPI fallback). The abstract methods below therefore keep a ``(repo)``
signature and read their run context from the instance, not from arguments.
See ``ecosystems/python.py`` for the reference implementation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path
from typing import Any


class EcosystemAdapter(ABC):
    """~11 methods isolating one language ecosystem. See DESIGN.md 'EcosystemAdapter'."""

    name: str

    @abstractmethod
    def detect(self, repo: Path) -> bool:
        """True if this adapter handles the repo's ecosystem."""

    @abstractmethod
    def python_version(self, repo: Path) -> str:
        """Interpreter version to target, from repo metadata (capped by config)."""

    @abstractmethod
    def synthesize_requirements(self, repo: Path) -> Path:
        """Normalize any manifest style into one canonical requirements.in-like input."""

    @abstractmethod
    def lock(self, repo: Path) -> Path:
        """Resolve requirements into a fully pinned lockfile."""

    @abstractmethod
    def dockerfile(self, repo: Path, lock: Path) -> str:
        """Render the templated, digest-pinned Dockerfile for the repo."""

    @abstractmethod
    def test_command(self, repo: Path) -> str:
        """Command that runs the repo's test suite inside the container."""

    @abstractmethod
    def test_framework_bootstrap(self, repo: Path) -> None:
        """Create a minimal test layout (tests/, conftest) when the repo has none."""

    @abstractmethod
    def lint_and_format(self, repo: Path, run: Any) -> dict[str, Any]:
        """Lint + format ``repo`` in place; return a structured report.

        ``run(cmd) -> CommandResult`` executes a shell command inside the pinned
        container (so the exact, pinned linter version is used and no target code
        runs on the host). The adapter writes its lint config into the tree, runs
        the fix/format commands via ``run``, and adds suppressions for unfixable
        findings; the caller syncs the mutated tree back and verifies the build.
        """

    @abstractmethod
    def parse_test_report(self, path: Path) -> dict[str, dict[str, str]]:
        """Parse a structured test report into {test_id: {status, reason}}."""

    @abstractmethod
    def symbol_index(self, repo: Path) -> dict[str, Any]:
        """Static AST facts: functions, classes, imports, calls."""

    @abstractmethod
    def mutators(self) -> list[Callable[[str], list[str]]]:
        """AST mutation operators used by test-gen and the verifier discrimination check."""
