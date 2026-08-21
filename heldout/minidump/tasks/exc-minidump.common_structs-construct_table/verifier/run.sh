#!/bin/sh
set -e
cd "$(dirname "$0")"
python -m pytest -q tests/generated/test_minidump_common_structs.py::TestConstructTable::test_basic tests/generated/test_minidump_common_structs.py::TestConstructTable::test_column_padding tests/generated/test_minidump_common_structs.py::TestConstructTable::test_empty_lines tests/generated/test_minidump_common_structs.py::TestConstructTable::test_multiple_columns tests/generated/test_minidump_common_structs.py::TestConstructTable::test_no_separate_head tests/generated/test_minidump_common_structs.py::TestConstructTable::test_single_row tests/generated/test_minidump_common_structs.py::TestConstructTable::test_single_row_no_separator
