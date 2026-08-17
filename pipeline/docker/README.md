# pipeline/docker/

Sandboxed container execution and image management. Every command the pipeline runs against a target repo goes through `run_in_container`.

## Files

| File | What it does |
|---|---|
| `runner.py` | `run_in_container`: runs a bash command inside a throwaway container (`docker run --rm --network none`) with the workdir bind-mounted at `/repo`. Per-command timeout; returns exit code, stdout, stderr. `fresh_workdir`: copies a source tree into a temp dir for one unit of work |
| `image.py` | `build_image`: builds a Dockerfile with the `bench-pipeline=1` label and returns its `sha256:...` id. `resolve_base_digest`: pulls a base image and returns its `repo@sha256:...` form for reproducible builds. `prune_dangling_bench_images`: removes only untagged images carrying this pipeline's label |

## How it's used

- The ecosystem adapter, agent `run` tool, and validation harness all call `run_in_container`.
- `build_image` is called during hygiene (initial build, post-repair rebuild, post-lint rebuild) and by the harness when a task needs a fresh image.
- `--prune-images` on the CLI calls `prune_dangling_bench_images` at the end of a run.
