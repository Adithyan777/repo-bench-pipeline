"""Shared hygiene run context + repo provisioning + pipeline commit helpers.

Output layout (DESIGN 3.8):
  output/<repo>/repo/       clean working clone (git preserved)
  output/<repo>/hygiene/    step JSON records + emitted test command
  output/<repo>/audit/      agent_actions.jsonl, llm_usage.json
  output/<repo>/report_data.json
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from pipeline.config import DEFAULT, Config
from pipeline.ecosystems.python import PythonAdapter
from pipeline.llm.client import LLMClient
from pipeline.state import State

_GIT_ID = ("-c", "user.email=pipeline@bench", "-c", "user.name=bench-pipeline")


def is_url(repo_arg: str) -> bool:
    return repo_arg.startswith(("http://", "https://", "git@", "ssh://"))


@dataclass
class HygieneContext:
    repo_arg: str
    run_dir: Path
    config: Config
    state: State
    llm: LLMClient
    adapter: PythonAdapter
    repo_identity: str = ""  # stable id of the ORIGINAL tree (base SHA or content hash)
    report: dict = field(default_factory=dict)

    @property
    def repo(self) -> Path:
        return self.run_dir / "repo"

    @property
    def hygiene_dir(self) -> Path:
        return self.run_dir / "hygiene"

    @property
    def knowledge_dir(self) -> Path:
        return self.run_dir / "knowledge"

    @property
    def tasks_dir(self) -> Path:  # output/<repo>/tasks (candidates + build bookkeeping)
        return self.run_dir / "tasks"

    @property
    def audit_dir(self) -> Path:
        return self.run_dir / "audit"

    @property
    def image_tag(self) -> str:
        return self.config.docker.image_name_prefix + self.run_dir.name

    def record(self, name: str, data: dict) -> Path:
        self.hygiene_dir.mkdir(parents=True, exist_ok=True)
        path = self.hygiene_dir / f"{name}.json"
        path.write_text(json.dumps(data, indent=2, sort_keys=True))
        return path

    def load(self, name: str) -> dict:
        return json.loads((self.hygiene_dir / f"{name}.json").read_text())


def append_agent_action(audit_dir: Path, record: dict) -> None:
    """Append one agent-action record to ``audit/agent_actions.jsonl`` (shared by every
    step that runs a bounded agent)."""
    audit_dir.mkdir(parents=True, exist_ok=True)
    with (audit_dir / "agent_actions.jsonl").open("a") as fh:
        fh.write(json.dumps(record) + "\n")


def provision_repo(repo_arg: str, run_dir: Path, fresh: bool) -> str:
    """Clone (URL) or copy (local path) the repo into run_dir/repo. Returns base SHA."""
    repo = run_dir / "repo"
    if fresh and repo.exists():
        shutil.rmtree(repo)
    if not repo.exists():
        run_dir.mkdir(parents=True, exist_ok=True)
        if is_url(repo_arg):
            subprocess.run(["git", "clone", "--quiet", repo_arg, str(repo)], check=True)
        else:
            src = Path(repo_arg).resolve()
            if not src.is_dir():
                raise SystemExit(f"not a directory or URL: {repo_arg}")
            shutil.copytree(src, repo)
    base = _git(repo, "rev-parse", "HEAD") if (repo / ".git").exists() else ""
    return base


def commit_pipeline_changes(ctx: HygieneContext, message: str) -> str | None:
    """Commit current working-tree changes in repo/ as one labeled pipeline commit."""
    repo = ctx.repo
    if not (repo / ".git").exists():
        return None
    if not _git(repo, "status", "--porcelain"):
        return None
    _git(repo, "add", "-A")
    _git(repo, *_GIT_ID, "commit", "--quiet", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def build_context(
    repo_arg: str,
    config: Config = DEFAULT,
    force: tuple[str, ...] = (),
    fresh: bool = False,
    output_root: Path = Path("output"),
    llm_mode: str | None = None,
    llm_stage: str = "hygiene",
) -> HygieneContext:
    from pipeline.cli import repo_name

    run_dir = output_root / repo_name(repo_arg)
    base_sha = provision_repo(repo_arg, run_dir, fresh)
    # After pipeline commits, HEAD advances; the persisted base_sha is the stable one.
    pipeline_base = run_dir / "hygiene" / "pipeline_base.json"
    if pipeline_base.is_file() and not fresh:
        base_sha = json.loads(pipeline_base.read_text()).get("base_sha", base_sha)
    state = State.load(run_dir, force=force, fresh=fresh)
    llm = LLMClient(
        config=config,
        stage=llm_stage,
        audit_dir=run_dir / "audit",
        transcripts_dir=Path("transcripts"),
        **({"mode": llm_mode} if llm_mode else {}),
    )
    adapter = PythonAdapter(config=config, work_dir=run_dir / "repo", llm=llm)
    identity = base_sha or _tree_hash(run_dir / "repo")
    ctx = HygieneContext(repo_arg, run_dir, config, state, llm, adapter, repo_identity=identity)
    ctx.report["repo"] = run_dir.name
    ctx.report["base_sha"] = base_sha
    ctx.report.setdefault("stages", {})
    return ctx


def _tree_hash(repo: Path) -> str:
    """Content hash of the original tree (used as repo identity when there's no git)."""
    import hashlib

    h = hashlib.sha256()
    for path in sorted(p for p in repo.rglob("*") if p.is_file() and ".git" not in p.parts):
        h.update(str(path.relative_to(repo)).encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    )
    return proc.stdout.strip()
