"""Docker execution: sandboxed command runner + image build. See docs/architecture.md."""

from pipeline.docker.image import build_image, resolve_base_digest
from pipeline.docker.runner import CommandResult, fresh_workdir, run_in_container

__all__ = [
    "run_in_container",
    "CommandResult",
    "fresh_workdir",
    "build_image",
    "resolve_base_digest",
]
