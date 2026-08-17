---
type: "python-function"
title: "get_message"
description: "Returns a formatted string using bbformat(fmt, *args)"
resource: "/glom/matching.py#L40-L42"
tags: ["glom", "matching"]
sources: [{"resource": "/glom/matching.py#L40-L42"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["side_effects"]}]
status: "stable"
---
# `glom.matching.MatchError.get_message`

`get_message(self)`

## Contract

- **inputs**: self (with args tuple where args[0] is a format string and args[1:] are format arguments)
- **outputs**: Returns a formatted string using bbformat(fmt, *args)
- **raises**: none
- **side_effects**: none
- **invariants**: The returned string is produced by applying bbformat to self.args[0] and self.args[1:]

## Tested by
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
- `glom/test/test_match.py::test_switch`
