#!/bin/sh
set -e
cd "$(dirname "$0")"
python -m pytest -q glom/test/test_error.py::test_all_public_errors glom/test/test_grouping.py::test_agg glom/test/test_grouping.py::test_reduce glom/test/test_reduction.py::test_flatten glom/test/test_reduction.py::test_flatten_func glom/test/test_reduction.py::test_fold glom/test/test_reduction.py::test_fold_bad_iter glom/test/test_reduction.py::test_merge glom/test/test_reduction.py::test_merge_func glom/test/test_reduction.py::test_merge_omd glom/test/test_reduction.py::test_sum_integers glom/test/test_reduction.py::test_sum_seqs
