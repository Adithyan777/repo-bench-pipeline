#!/bin/sh
set -e
cd "$(dirname "$0")"
python -m pytest -q toolz/sandbox/tests/test_core.py::test_unzip
