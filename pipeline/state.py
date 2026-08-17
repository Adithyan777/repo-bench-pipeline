"""Resumability: per-step status + input hashing in output/<repo>/state.json.

A step is skipped when its recorded status is ``done`` and its input hash is
unchanged. ``--force <step>`` reruns one step; ``--fresh`` reruns everything.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

STATE_FILENAME = "state.json"


def hash_inputs(*parts: str | bytes | Path) -> str:
    """Stable hash over ordered inputs. Paths hash by content; str/bytes literally."""
    h = hashlib.sha256()
    for part in parts:
        if isinstance(part, Path):
            h.update(b"\x00path\x00")
            h.update(part.read_bytes() if part.is_file() else str(part).encode())
        elif isinstance(part, bytes):
            h.update(b"\x00bytes\x00")
            h.update(part)
        else:
            h.update(b"\x00str\x00")
            h.update(str(part).encode())
    return h.hexdigest()


def code_fingerprint(paths: Iterable[str]) -> str:
    """Hash the contents of pipeline source files; mixed into a step's input hash so a
    change to the producing code invalidates its artifacts."""
    files = [Path(p) for p in paths]
    return hash_inputs(*[p for p in files if p.is_file()])


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


@dataclass
class State:
    """Step ledger for one repo run, persisted to ``run_dir/state.json``."""

    run_dir: Path
    force: frozenset[str] = field(default_factory=frozenset)
    fresh: bool = False
    _steps: dict[str, dict] = field(default_factory=dict)

    @classmethod
    def load(cls, run_dir: Path, force: Iterable[str] = (), fresh: bool = False) -> State:
        run_dir = Path(run_dir)
        state = cls(run_dir=run_dir, force=frozenset(force), fresh=fresh)
        path = run_dir / STATE_FILENAME
        if path.is_file() and not fresh:
            state._steps = json.loads(path.read_text())
        return state

    @property
    def path(self) -> Path:
        return self.run_dir / STATE_FILENAME

    def should_run(self, step: str, input_hash: str) -> bool:
        """True unless the step is already done with a matching input hash."""
        if self.fresh or step in self.force:
            return True
        record = self._steps.get(step)
        return not (
            record is not None
            and record.get("status") == "done"
            and record.get("input_hash") == input_hash
        )

    def mark_done(self, step: str, input_hash: str) -> None:
        self._steps[step] = {
            "status": "done",
            "input_hash": input_hash,
            "finished_at": _now(),
        }
        self._flush()

    def mark_failed(self, step: str, input_hash: str) -> None:
        self._steps[step] = {
            "status": "failed",
            "input_hash": input_hash,
            "finished_at": _now(),
        }
        self._flush()

    def get(self, step: str) -> dict | None:
        return self._steps.get(step)

    def _flush(self) -> None:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._steps, indent=2, sort_keys=True))
