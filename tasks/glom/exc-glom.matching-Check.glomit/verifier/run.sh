#!/bin/sh
set -e
cd "$(dirname "$0")"
python -m pytest -q glom/test/test_check.py::test_check_basic glom/test/test_check.py::test_check_multi glom/test/test_error.py::test_all_public_errors glom/test/test_snippets.py::test_snippet glom/test/test_streaming.py::test_filter glom/test/test_streaming.py::test_windowed
