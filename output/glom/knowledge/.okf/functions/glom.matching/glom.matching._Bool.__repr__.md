---
type: "python-function"
title: "__repr__"
description: "Returns a string representation combining child reprs with the operator string, or class-name call-style if default is present or _m_repr is truthy"
resource: "/glom/matching.py#L299-L305"
tags: ["glom", "matching"]
sources: [{"resource": "/glom/matching.py#L299-L305"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "side_effects"]}]
status: "stable"
---
# `glom.matching._Bool.__repr__`

`__repr__(self)`

## Contract

- **inputs**: self
- **outputs**: Returns a string representation combining child reprs with the operator string, or class-name call-style if default is present or _m_repr is truthy
- **raises**: none
- **side_effects**: none
- **invariants**: Always returns a non-empty string representation of the boolean expression node

## Callees
`glom.matching._Bool._m_repr`, `glom.matching._bool_child_repr`

## Tested by
- `glom/test/test_error.py::test_partially_failing_branch`
- `glom/test/test_match.py::test_and_or_reduction`
- `glom/test/test_match.py::test_reprs`
