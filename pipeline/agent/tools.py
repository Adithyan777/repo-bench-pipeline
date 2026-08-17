"""Progressive-disclosure agent toolset.

Concrete tools operate on a copied repo workdir; ``run`` executes ONLY inside the
Docker container. Graph/okf-backed tools (show_symbol, callers, callees,
tests_for, show_commit, okf) are registered as stubs that raise
``NotImplementedError`` until the graph (S3) and .okf (S7) exist -- never faked.
The loop turns a raised tool error into a text observation for the model.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from pipeline.config import DEFAULT
from pipeline.docker.runner import run_in_container


@dataclass
class ToolContext:
    """Shared state for a single agent run."""

    workdir: Path
    image: str | None = None
    files_changed: set[str] = field(default_factory=set)


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    func: Callable[..., str]

    def schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


def _safe_path(ctx: ToolContext, path: str) -> Path:
    resolved = (ctx.workdir / path).resolve()
    if not resolved.is_relative_to(ctx.workdir.resolve()):
        raise ValueError(f"path escapes workdir: {path}")
    return resolved


def _read_file(ctx: ToolContext, path: str, lines: str | None = None) -> str:
    target = _safe_path(ctx, path)
    if not target.is_file():
        raise FileNotFoundError(f"no such file: {path}")
    text = target.read_text(errors="replace")
    if lines:
        start, _, end = lines.partition(":")
        rows = text.splitlines()
        lo = max(int(start) - 1, 0) if start else 0
        hi = int(end) if end else len(rows)
        return "\n".join(rows[lo:hi])
    return text


def _grep(ctx: ToolContext, pattern: str) -> str:
    regex = re.compile(pattern)
    root = ctx.workdir.resolve()
    limit = DEFAULT.agent.grep_max_matches
    hits: list[str] = []
    for path in sorted(root.rglob("*")):
        # Never follow symlinks or read anything resolving outside the workdir.
        if path.is_symlink() or not path.is_file() or ".git" in path.parts:
            continue
        if not path.resolve().is_relative_to(root):
            continue
        try:
            for n, line in enumerate(path.read_text(errors="strict").splitlines(), 1):
                if regex.search(line):
                    hits.append(f"{path.relative_to(root)}:{n}:{line.strip()}")
                    if len(hits) >= limit:
                        hits.append(f"... (truncated at {limit} matches)")
                        return "\n".join(hits)
        except (UnicodeDecodeError, OSError):
            continue
    return "\n".join(hits) if hits else "no matches"


def _write_file(ctx: ToolContext, path: str, content: str) -> str:
    target = _safe_path(ctx, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    ctx.files_changed.add(path)
    return f"wrote {len(content)} bytes to {path}"


def _run(ctx: ToolContext, cmd: str) -> str:
    if ctx.image is None:
        raise RuntimeError("run tool has no container image configured")
    result = run_in_container(ctx.workdir, cmd, ctx.image, timeout=DEFAULT.agent.run_tool_timeout_s)
    return (
        f"exit_code={result.exit_code}\n"
        f"--- stdout ---\n{result.stdout}\n"
        f"--- stderr ---\n{result.stderr}"
    )


def _stub(name: str, needs: str) -> Callable[..., str]:
    def raise_not_implemented(**_: object) -> str:
        raise NotImplementedError(f"{name} requires {needs}; not available yet")

    return raise_not_implemented


def concrete_tools(ctx: ToolContext) -> list[Tool]:
    """The tools implemented in S1: read_file, grep, write_file, run."""
    return [
        Tool(
            "read_file",
            "Read a source file. Optional `lines` as 'start:end' (1-indexed).",
            {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "lines": {"type": "string"},
                },
                "required": ["path"],
            },
            lambda path, lines=None: _read_file(ctx, path, lines),
        ),
        Tool(
            "grep",
            "Search the repo for a regular expression. Returns file:line:match.",
            {
                "type": "object",
                "properties": {"pattern": {"type": "string"}},
                "required": ["pattern"],
            },
            lambda pattern: _grep(ctx, pattern),
        ),
        Tool(
            "write_file",
            "Write (create or overwrite) a file in the repo.",
            {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
            lambda path, content: _write_file(ctx, path, content),
        ),
        Tool(
            "run",
            "Run a shell command inside the repo's Docker container. Returns exit code and output.",
            {
                "type": "object",
                "properties": {"cmd": {"type": "string"}},
                "required": ["cmd"],
            },
            lambda cmd: _run(ctx, cmd),
        ),
    ]


def stub_tools() -> list[Tool]:
    """Graph/okf-backed tools, registered but not yet implemented (S3/S7)."""
    empty = {"type": "object", "properties": {}}
    return [
        Tool(
            "show_symbol",
            "Look up a function/class from the repo graph.",
            empty,
            _stub("show_symbol", "the repo graph (S3)"),
        ),
        Tool(
            "callers", "List callers of a symbol.", empty, _stub("callers", "the repo graph (S3)")
        ),
        Tool(
            "callees", "List callees of a symbol.", empty, _stub("callees", "the repo graph (S3)")
        ),
        Tool(
            "tests_for",
            "Find tests covering a symbol.",
            empty,
            _stub("tests_for", "the test map (S3)"),
        ),
        Tool(
            "show_commit",
            "Inspect a commit.",
            empty,
            _stub("show_commit", "the history index (S3)"),
        ),
        Tool(
            "okf",
            "Read an OKF knowledge page.",
            empty,
            _stub("okf", "the .okf knowledge layer (S7)"),
        ),
    ]
