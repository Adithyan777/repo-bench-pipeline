"""Agent toolset.

``concrete_tools``: read_file/grep/write_file on the workdir, ``run`` only inside Docker.
``graph_tools``: repo graph / history index / git navigation plus the sandboxed ``okf``
page reader. Missing artifacts raise; the loop returns the error to the model as text.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from pipeline.config import DEFAULT, Config
from pipeline.docker.runner import run_in_container

_SHA_RE = re.compile(r"[0-9a-fA-F]{4,40}")


@dataclass
class ToolContext:
    """Shared state for a single agent run."""

    workdir: Path
    image: str | None = None
    files_changed: set[str] = field(default_factory=set)
    knowledge_dir: Path | None = None  # output/<repo>/knowledge (graph, test_map)
    repo_root: Path | None = None  # for show_commit / git; defaults to workdir
    config: Config = field(default_factory=lambda: DEFAULT)


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
    """Filesystem/container tools: read_file, grep, write_file, run."""
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


def _graph_path(ctx: ToolContext) -> Path:
    if ctx.knowledge_dir is None:
        raise RuntimeError("show_symbol requires the repo graph; knowledge_dir not set")
    return ctx.knowledge_dir / ctx.config.knowledge.graph_filename


def _okf(ctx: ToolContext, path: str) -> str:
    """Read one OKF page by bundle-relative path, sandboxed to the .okf bundle."""
    if ctx.knowledge_dir is None:
        raise RuntimeError("okf requires the .okf bundle; knowledge_dir not set")
    bundle = (ctx.knowledge_dir / ctx.config.okf.bundle_dirname).resolve()
    target = (bundle / path.lstrip("/")).resolve()
    if not target.is_relative_to(bundle):
        raise ValueError(f"path escapes the okf bundle: {path}")
    if not target.is_file():
        raise FileNotFoundError(f"no such okf page: {path}")
    return target.read_text(errors="replace")


def _load_graph(ctx: ToolContext) -> dict:
    path = _graph_path(ctx)
    if not path.is_file():
        raise FileNotFoundError(f"repo graph not built yet: {path}")
    return json.loads(path.read_text())


def _node(graph: dict, qualname: str) -> dict | None:
    for node in graph["nodes"]:
        if node["id"] == qualname:
            return node
    return None


def _show_symbol(ctx: ToolContext, qualname: str) -> str:
    graph = _load_graph(ctx)
    node = _node(graph, qualname)
    if node is None:
        raise ValueError(f"no symbol '{qualname}' in the graph")
    lines = [
        f"{node['type']} {node['id']}",
        f"  file: {node['file']}:{node.get('line')}-{node.get('end_line', node.get('line'))}",
    ]
    if node.get("signature"):
        lines.append(f"  signature: {node['signature']}")
    if node.get("complexity") is not None:
        lines.append(f"  complexity: {node['complexity']}")
    if node.get("coverage") is not None:
        lines.append(f"  coverage: {node['coverage']}%")
    if node.get("tested_by"):
        lines.append(f"  tested_by: {', '.join(node['tested_by'])}")
    if node.get("docstring"):
        lines.append(f"  docstring: {node['docstring'].strip().splitlines()[0]}")
    return "\n".join(lines)


def _calls_edges(ctx: ToolContext, *, source: str | None = None, target: str | None = None) -> str:
    graph = _load_graph(ctx)
    hits = [
        e
        for e in graph["edges"]
        if e["type"] == "calls"
        and (source is None or e["source"] == source)
        and (target is None or e["target"] == target)
    ]
    if not hits:
        return "none"
    key = "source" if target else "target"
    return "\n".join(f"{e[key]}  ({e['evidence']['file']}:{e['evidence']['line']})" for e in hits)


def _tests_for(ctx: ToolContext, qualname: str) -> str:
    graph = _load_graph(ctx)
    node = _node(graph, qualname)
    tested = node.get("tested_by") if node else None
    if not tested:
        tested = sorted(
            e["target"]
            for e in graph["edges"]
            if e["type"] == "tested_by" and e["source"] == qualname
        )
    return "\n".join(tested) if tested else "no tests found"


def _show_commit(ctx: ToolContext, sha: str) -> str:
    if not _SHA_RE.fullmatch(sha or ""):
        raise ValueError(f"not a valid commit sha: {sha!r}")
    root = ctx.repo_root or ctx.workdir
    history = (
        ctx.knowledge_dir / ctx.config.knowledge.history_filename if ctx.knowledge_dir else None
    )
    if history and history.is_file():
        for commit in json.loads(history.read_text()):
            if commit["sha"].startswith(sha):  # sha is a validated non-empty prefix
                return _format_commit(commit)
    # --end-of-options: sha is parsed as a revision, never an option or pathspec.
    result = subprocess.run(
        ["git", "-C", str(root), "show", "--stat", "--format=%H%n%s%n%an", "--end-of-options", sha],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(f"no such commit: {sha}")
    return result.stdout[: ctx.config.knowledge.show_commit_max_chars]


def _format_commit(commit: dict) -> str:
    lines = [
        f"commit {commit['sha']}",
        f"  message: {commit['message']}",
        f"  merge: {commit['is_merge']}  pr: {commit.get('pr_number')}",
        f"  +{commit['insertions']} -{commit['deletions']}  manifest: {commit['touches_manifest']}",
        f"  files: {', '.join(commit['files_changed'])}",
    ]
    if commit["touched_functions"]:
        lines.append(f"  functions: {', '.join(commit['touched_functions'])}")
    if commit["test_files_touched"]:
        lines.append(f"  tests: {', '.join(commit['test_files_touched'])}")
    return "\n".join(lines)


def graph_tools(ctx: ToolContext) -> list[Tool]:
    """Graph/history-backed navigation tools plus the okf page reader."""
    one = {
        "type": "object",
        "properties": {"qualname": {"type": "string"}},
        "required": ["qualname"],
    }
    return [
        Tool(
            "show_symbol",
            "Look up a function/class from the repo graph by qualname.",
            one,
            lambda qualname: _show_symbol(ctx, qualname),
        ),
        Tool(
            "callers",
            "List call sites that call the given qualname.",
            one,
            lambda qualname: _calls_edges(ctx, target=qualname),
        ),
        Tool(
            "callees",
            "List intra-repo symbols the given qualname calls.",
            one,
            lambda qualname: _calls_edges(ctx, source=qualname),
        ),
        Tool(
            "tests_for",
            "List tests that execute the given qualname.",
            one,
            lambda qualname: _tests_for(ctx, qualname),
        ),
        Tool(
            "show_commit",
            "Inspect a commit from the history index (or git).",
            {"type": "object", "properties": {"sha": {"type": "string"}}, "required": ["sha"]},
            lambda sha: _show_commit(ctx, sha),
        ),
        Tool(
            "okf",
            "Read an OKF knowledge page by bundle-relative path (e.g. 'modules/pkg.mod.md').",
            {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
            lambda path: _okf(ctx, path),
        ),
    ]
