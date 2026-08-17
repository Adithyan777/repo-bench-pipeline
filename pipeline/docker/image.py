"""Image build + base-image digest pinning. Built image ids are recorded in verdict.json."""

from __future__ import annotations

import subprocess
from pathlib import Path


class DockerError(RuntimeError):
    pass


# Label on every pipeline-built image; prunes are scoped to it.
BUILD_LABEL = "bench-pipeline"


def _run(argv: list[str]) -> str:
    proc = subprocess.run(argv, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise DockerError(f"{' '.join(argv[:3])}... failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def resolve_base_digest(base_ref: str) -> str:
    """Pull ``base_ref`` and return the digest form ``repo@sha256:...``."""
    _run(["docker", "pull", base_ref])
    digests = _run(["docker", "inspect", "--format", '{{join .RepoDigests "\\n"}}', base_ref])
    repo = base_ref.split(":", 1)[0]
    for line in digests.splitlines():
        if line.startswith(repo + "@"):
            return line.strip()
    raise DockerError(f"no repo digest found for {base_ref}")


def build_image(context_dir: Path, tag: str) -> str:
    """Build the image at ``context_dir`` (needs a Dockerfile); return its ``sha256:...`` id."""
    context_dir = Path(context_dir)
    if not (context_dir / "Dockerfile").is_file():
        raise DockerError(f"no Dockerfile in {context_dir}")
    _run(["docker", "build", "--label", f"{BUILD_LABEL}=1", "-t", tag, str(context_dir)])
    return _run(["docker", "inspect", "--format", "{{.Id}}", tag])


def prune_dangling_bench_images() -> int:
    """Remove dangling images carrying BUILD_LABEL (layers orphaned by a bench-<repo>
    rebuild). Tagged or foreign images are never touched. Returns the count removed."""
    out = _run(
        [
            "docker",
            "image",
            "prune",
            "-f",
            "--filter",
            "dangling=true",
            "--filter",
            f"label={BUILD_LABEL}=1",
        ]
    )
    return sum(1 for line in out.splitlines() if "sha256:" in line or line.startswith("deleted:"))


def image_id(ref: str) -> str | None:
    """Local ``sha256:...`` id of an image tag/id, or None when it is not present."""
    try:
        return _run(["docker", "inspect", "--format", "{{.Id}}", ref])
    except DockerError:
        return None
