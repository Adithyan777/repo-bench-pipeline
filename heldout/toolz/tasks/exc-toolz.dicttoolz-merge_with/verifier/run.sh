#!/bin/sh
set -e
cd "$(dirname "$0")"
python -m pytest -q toolz/tests/test_curried.py::test_merge_with toolz/tests/test_curried.py::test_merge_with_list toolz/tests/test_dicttoolz.py::TestCustomMapping::test_merge_with toolz/tests/test_dicttoolz.py::TestCustomMapping::test_merge_with_iterable_arg toolz/tests/test_dicttoolz.py::TestDefaultDict::test_merge_with toolz/tests/test_dicttoolz.py::TestDefaultDict::test_merge_with_iterable_arg toolz/tests/test_dicttoolz.py::TestDict::test_merge_with toolz/tests/test_dicttoolz.py::TestDict::test_merge_with_iterable_arg toolz/tests/test_dicttoolz.py::test_merge_with_non_dict_mappings
