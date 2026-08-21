#!/bin/sh
set -e
cd "$(dirname "$0")"
python -m pytest -q tests/generated/test_minidump_common_structs.py::TestMinidumpMemorySegmentAsearch::test_asearch_chunksize_boundary tests/generated/test_minidump_common_structs.py::TestMinidumpMemorySegmentAsearch::test_asearch_find_all tests/generated/test_minidump_common_structs.py::TestMinidumpMemorySegmentAsearch::test_asearch_find_first tests/generated/test_minidump_common_structs.py::TestMinidumpMemorySegmentAsearch::test_asearch_not_found tests/generated/test_minidump_common_structs.py::TestMinidumpMemorySegmentAsearch::test_asearch_pattern_too_long tests/generated/test_minidump_common_structs.py::TestMinidumpMemorySegmentAsearch::test_asearch_restores_position
