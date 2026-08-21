#!/bin/sh
set -e
cd "$(dirname "$0")"
python -m pytest -q tests/generated/test_minidump_common_structs.py::TestMinidumpMemorySegmentAread::test_aread_cross_boundary_raises tests/generated/test_minidump_common_structs.py::TestMinidumpMemorySegmentAread::test_aread_offset tests/generated/test_minidump_common_structs.py::TestMinidumpMemorySegmentAread::test_aread_restores_position tests/generated/test_minidump_common_structs.py::TestMinidumpMemorySegmentAread::test_aread_success tests/generated/test_minidump_common_structs.py::TestMinidumpMemorySegmentAread::test_aread_wrong_segment_raises
