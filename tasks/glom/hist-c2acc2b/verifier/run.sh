#!/bin/sh
set -e
cd "$(dirname "$0")"
python -m pytest -q glom/test/test_path_and_t.py::test_path_t_roundtrip
