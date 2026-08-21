#!/bin/sh
set -e
cd "$(dirname "$0")"
python -m pytest -q toolz/tests/test_itertoolz.py::test_groupby toolz/tests/test_itertoolz.py::test_groupby_non_callable toolz/tests/test_itertoolz.py::test_join toolz/tests/test_itertoolz.py::test_join_double_repeats toolz/tests/test_itertoolz.py::test_join_missing_element toolz/tests/test_itertoolz.py::test_key_as_getter toolz/tests/test_itertoolz.py::test_left_outer_join toolz/tests/test_itertoolz.py::test_outer_join toolz/tests/test_itertoolz.py::test_right_outer_join
