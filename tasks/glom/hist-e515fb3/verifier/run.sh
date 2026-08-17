#!/bin/sh
set -e
cd "$(dirname "$0")"
python -m pytest -q glom/test/test_error.py::test_pae_fallback_for_non_path glom/test/test_error.py::test_pae_scope_printable
