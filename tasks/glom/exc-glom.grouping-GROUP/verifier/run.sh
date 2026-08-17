#!/bin/sh
set -e
cd "$(dirname "$0")"
python -m pytest -q glom/test/test_error.py::test_all_public_errors glom/test/test_grouping.py::test_agg glom/test/test_grouping.py::test_bucketing glom/test/test_grouping.py::test_corner_cases glom/test/test_grouping.py::test_limit glom/test/test_grouping.py::test_sample
