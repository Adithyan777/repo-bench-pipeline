#!/bin/sh
set -e
cd "$(dirname "$0")"
python -m pytest -q tests/generated/test_minidump_common_structs.py::TestMinidumpMemorySegmentSearch::test_search_chunksize_boundary tests/generated/test_minidump_common_structs.py::TestMinidumpMemorySegmentSearch::test_search_find_all tests/generated/test_minidump_common_structs.py::TestMinidumpMemorySegmentSearch::test_search_find_first tests/generated/test_minidump_common_structs.py::TestMinidumpMemorySegmentSearch::test_search_not_found tests/generated/test_minidump_common_structs.py::TestMinidumpMemorySegmentSearch::test_search_pattern_too_long tests/generated/test_minidump_common_structs.py::TestMinidumpMemorySegmentSearch::test_search_restores_position
