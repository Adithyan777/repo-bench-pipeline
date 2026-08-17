"""EcosystemAdapter: the only ecosystem-specific surface; everything else is agnostic.

Constructed per repo as ``Adapter(config, work_dir, llm)``: ``work_dir`` is the clean
clone that receives ecosystem files, ``llm`` an optional client for model fallbacks.
Reference implementation: ``ecosystems/python.py``.
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
        """Lint + format ``repo`` in place via ``run(cmd)`` (executes inside the pinned
        container); return a structured report. Caller syncs the tree back and rebuilds."""

    @abstractmethod
    def parse_test_report(self, path: Path) -> dict[str, dict[str, str]]:
        """Parse a structured test report into {test_id: {status, reason}}."""

    @abstractmethod
    def symbol_index(self, repo: Path) -> dict[str, Any]:
        """Static AST facts: functions, classes, imports, calls."""

    @abstractmethod
    def mutators(self) -> list[Callable[[str], list[str]]]:
        """AST mutation operators used by test-gen and the verifier discrimination check."""
