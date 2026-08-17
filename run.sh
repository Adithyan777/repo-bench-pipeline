#!/usr/bin/env bash
# Thin wrapper around the pipeline CLI. Uses the project venv if present.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-.venv/bin/python}"
[ -x "$PY" ] || PY="python3"
exec "$PY" -m pipeline.cli "$@"
