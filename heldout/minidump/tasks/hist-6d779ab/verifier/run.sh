#!/bin/sh
set -e
cd "$(dirname "$0")"
python -m pytest -q tests/generated/test_hist_6d779ab.py::TestSearchOffsetAccumulation::test_asearch_adjacent_patterns tests/generated/test_hist_6d779ab.py::TestSearchOffsetAccumulation::test_asearch_five_matches_progressive_addresses tests/generated/test_hist_6d779ab.py::TestSearchOffsetAccumulation::test_asearch_three_matches_correct_addresses tests/generated/test_hist_6d779ab.py::TestSearchOffsetAccumulation::test_search_adjacent_patterns tests/generated/test_hist_6d779ab.py::TestSearchOffsetAccumulation::test_search_five_matches_progressive_addresses tests/generated/test_hist_6d779ab.py::TestSearchOffsetAccumulation::test_search_three_matches_correct_addresses
