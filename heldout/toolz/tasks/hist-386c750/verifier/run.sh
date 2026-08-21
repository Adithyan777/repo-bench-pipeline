#!/bin/sh
set -e
cd "$(dirname "$0")"
python -m pytest -q toolz/tests/test_itertoolz.py::test_isiterable
