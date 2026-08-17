"""Plain progress log: ``HH:MM:SS [stage/step] msg`` on stdout, flushed, never raises.

Levels: STAGE (run/stage boundaries, summary), STEP (start/done/skipped with duration +
LLM tokens spent by the step), DETAIL (inner events). ``--quiet`` keeps STAGE lines only.
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from datetime import datetime

STAGE, STEP, DETAIL = 0, 1, 2
threshold = DETAIL  # cli sets STAGE for --quiet


def log(stage: str, step: str = "", msg: str = "", level: int = DETAIL) -> None:
    if level > threshold:
        return
    try:
        tag = f"{stage}/{step}" if step else stage
        sys.stdout.write(f"{datetime.now():%H:%M:%S} [{tag}] {msg}\n")
        sys.stdout.flush()
    except Exception:  # noqa: BLE001 - logging must never break the pipeline
        pass


def tokens(llm) -> int:
    """Total tokens accounted by this client so far; 0 when unavailable."""
    try:
        return int(llm._total_usage().total_tokens)
    except Exception:  # noqa: BLE001
        return 0


@dataclass
class Step:
    stage: str
    name: str
    llm: object = None
    t0: float = field(default_factory=time.monotonic)
    tok0: int = 0

    def done(self, extra: str = "") -> None:
        spent = tokens(self.llm) - self.tok0
        msg = f"done in {time.monotonic() - self.t0:.1f}s ({spent} LLM tokens)"
        log(self.stage, self.name, f"{msg} {extra}".rstrip(), STEP)


def step_start(stage: str, name: str, llm=None) -> Step:
    log(stage, name, "start", STEP)
    return Step(stage, name, llm, tok0=tokens(llm))


def step_skipped(stage: str, name: str, reason: str = "unchanged") -> None:
    log(stage, name, f"skipped ({reason})", STEP)


def fmt_counts(d: dict | None, keys: tuple[str, ...] = ()) -> str:
    """``k=v k=v`` for a dict (selected keys, or all); '' when missing."""
    try:
        items = [(k, d[k]) for k in keys if k in d] if keys else list(d.items())
        return " ".join(f"{k}={v}" for k, v in items)
    except Exception:  # noqa: BLE001
        return ""
