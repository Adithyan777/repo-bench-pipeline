#!/bin/sh
set -e
cd "$(dirname "$0")"
python -m pytest -q glom/test/test_check.py::test_check_basic
