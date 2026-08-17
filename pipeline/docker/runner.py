"""Sandboxed command execution.

Every command runs in a throwaway container:

    docker run --rm --network none -v <workdir>:/repo -w /repo <image> bash -c "<cmd>"

with a per-command timeout. A fresh workdir is created per unit of work; nothing
is shared between runs. This is the single execution helper used by the ecosystem
adapter, the agent ``run`` tool, and the validation harness.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import NamedTuple

from pipeline.config import DEFAULT

TIMEOUT_EXIT_CODE = 124  # matches coreutils `timeout`


class CommandResult(NamedTuple):
    exit_code: int
    stdout: str
    stderr: str


@contextmanager
def fresh_workdir(src: Path) -> Iterator[Path]:
    """Copy a source tree into a fresh temp dir for one unit of work, then clean up."""
    tmp = Path(tempfile.mkdtemp(prefix="bench-work-"))
    dest = tmp / "repo"
    shutil.copytree(src, dest)
    try:
        yield dest
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_in_container(
    workdir: Path,
    cmd: str,
    image: str,
    timeout: int | None = None,
    network_none: bool | None = None,
) -> CommandResult:
    """Run ``cmd`` in ``image`` with ``workdir`` bind-mounted at /repo.

    Returns (exit_code, stdout, stderr). On timeout the container is killed and
    exit code ``124`` is returned. Defaults come from config.
    """
    timeout = DEFAULT.docker.default_cmd_timeout_s if timeout is None else timeout
    if network_none is None:
        network_none = DEFAULT.docker.network_none_for_runs

    name = f"bench-run-{uuid.uuid4().hex[:12]}"
    argv = ["docker", "run", "--rm", "--name", name]
    if network_none:
        argv += ["--network", "none"]
    argv += ["-v", f"{Path(workdir).resolve()}:/repo", "-w", "/repo", image, "bash", "-c", cmd]

    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
        return CommandResult(proc.returncode, proc.stdout, proc.stderr)
    except subprocess.TimeoutExpired as exc:
        subprocess.run(["docker", "kill", name], capture_output=True, check=False)
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        return CommandResult(TIMEOUT_EXIT_CODE, stdout, f"timeout: command exceeded {timeout}s")
