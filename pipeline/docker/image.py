"""Image build + base-image digest pinning.

Base images are pinned to a sha256 digest so builds are reproducible. The built
image's own id is returned so it can be recorded in a task's verdict.json.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


class DockerError(RuntimeError):
    pass


# Every image this pipeline builds carries this label, so a prune can target ONLY our
# own leftovers (never a user's other images/containers).
BUILD_LABEL = "bench-pipeline"


def _run(argv: list[str]) -> str:
    proc = subprocess.run(argv, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise DockerError(f"{' '.join(argv[:3])}... failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def resolve_base_digest(base_ref: str) -> str:
    """Pull ``base_ref`` and return it pinned as ``repo@sha256:...``.

    e.g. ``python:3.12-slim`` -> ``python@sha256:<digest>``. Deterministic builds
    reference the digest form, not the mutable tag.
    """
    _run(["docker", "pull", base_ref])
    digests = _run(["docker", "inspect", "--format", '{{join .RepoDigests "\\n"}}', base_ref])
    repo = base_ref.split(":", 1)[0]
    for line in digests.splitlines():
        if line.startswith(repo + "@"):
            return line.strip()
    raise DockerError(f"no repo digest found for {base_ref}")


def build_image(context_dir: Path, tag: str) -> str:
    """Build the image at ``context_dir`` (expects a Dockerfile) and return its id.

    Returns the built image's ``sha256:...`` id for recording alongside tasks.
    """
    context_dir = Path(context_dir)
    if not (context_dir / "Dockerfile").is_file():
        raise DockerError(f"no Dockerfile in {context_dir}")
    _run(["docker", "build", "--label", f"{BUILD_LABEL}=1", "-t", tag, str(context_dir)])
    return _run(["docker", "inspect", "--format", "{{.Id}}", tag])


def prune_dangling_bench_images() -> int:
    """Remove ONLY dangling (untagged) images that carry this pipeline's build label —
    e.g. the old layers left behind when bench-<repo> is rebuilt. Tagged bench-* images
    and any image the pipeline did not build are never touched. Returns images removed.

    (A rebuild retags bench-<repo> onto the new image, leaving the previous one
    untagged; ``label=`` scopes the prune so nothing else on the host is affected.)
    """
    out = _run(
        [
            "docker", "image", "prune", "-f",
            "--filter", "dangling=true",
            "--filter", f"label={BUILD_LABEL}=1",
        ]
    )
    return sum(1 for line in out.splitlines() if "sha256:" in line or line.startswith("deleted:"))


def image_id(ref: str) -> str | None:
    """Local ``sha256:...`` id of an image tag/id, or None when it is not present."""
    try:
        return _run(["docker", "inspect", "--format", "{{.Id}}", ref])
    except DockerError:
        return None
