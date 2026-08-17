---
type: "python-function"
title: "convert_field"
description: "the converted string, with 'r' conversion using bbrepr and replacing escaped single quotes"
resource: "/glom/core.py#L539-L542"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L539-L542"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["side_effects"]}]
status: "stable"
---
# `glom.core._BBReprFormatter.convert_field`

`convert_field(self, value, conversion)`

## Contract

- **inputs**: self: a _BBReprFormatter instance; value: the value to convert; conversion: the conversion type character
- **outputs**: the converted string, with 'r' conversion using bbrepr and replacing escaped single quotes
- **raises**: none
- **side_effects**: none

## Tested by
- `glom/test/test_basic.py::test_bbformat`
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_error.py::test_branching_stack`
- `glom/test/test_error.py::test_midway_branch`
- `glom/test/test_match.py::test_basic`
- `glom/test/test_match.py::test_check_ported_tests`
- `glom/test/test_match.py::test_cruddy_json`
- `glom/test/test_match.py::test_m_call_match`
- `glom/test/test_match.py::test_match_expressions`
- `glom/test/test_match.py::test_regex`
- `glom/test/test_match.py::test_sample`
- `glom/test/test_match.py::test_sets`
- `glom/test/test_match.py::test_shortcircuit`
- `glom/test/test_match.py::test_sky`
