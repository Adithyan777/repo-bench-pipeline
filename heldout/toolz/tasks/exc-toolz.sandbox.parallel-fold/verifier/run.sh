#!/bin/sh
set -e
cd "$(dirname "$0")"
python -m pytest -q toolz/sandbox/tests/test_parallel.py::test_fold toolz/tests/test_tlz.py::test_tlz
