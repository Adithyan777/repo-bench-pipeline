#!/bin/sh
set -e
cd "$(dirname "$0")"
python -m pytest -q glom/test/test_basic.py::test_spec_and_recursion glom/test/test_match.py::test_match_default glom/test/test_match.py::test_switch glom/test/test_mutation.py::test_assign_spec_val glom/test/test_path_and_t.py::test_t_subspec glom/test/test_scope_vars.py::test_s_scope_assign
