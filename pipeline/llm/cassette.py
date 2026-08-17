"""Record/replay store for LLM calls: one JSON fixture per request+response pair, keyed
by a stable hash of the canonical request. Tests replay and never touch the network.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def request_key(request: dict) -> str:
    """Stable short hash over the canonicalized request."""
    blob = json.dumps(request, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


class Cassette:
    def __init__(self, root: Path, stage: str) -> None:
        self.dir = Path(root) / stage

    def _path(self, key: str) -> Path:
        return self.dir / f"{key}.json"

    def load(self, key: str) -> dict | None:
        path = self._path(key)
        if not path.is_file():
            return None
        return json.loads(path.read_text())["response"]

    def save(self, key: str, request: dict, response: dict) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        self._path(key).write_text(
            json.dumps({"request": request, "response": response}, indent=2, sort_keys=True)
        )
