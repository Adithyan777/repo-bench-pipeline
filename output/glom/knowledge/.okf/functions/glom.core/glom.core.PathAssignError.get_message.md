---
type: "python-function"
title: "get_message"
description: "a formatted error message string describing the assignment failure"
resource: "/glom/core.py#L381-L383"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L381-L383"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["side_effects"]}]
status: "stable"
---
# `glom.core.PathAssignError.get_message`

`get_message(self)`

## Contract

- **inputs**: self: a PathAssignError instance
- **outputs**: a formatted error message string describing the assignment failure
- **raises**: none
- **side_effects**: none

## Tested by
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_mutation.py::test_assign_missing_unassignable`
- `glom/test/test_mutation.py::test_bad_assign_target`
- `glom/test/test_mutation.py::test_sequence_assign`
- `glom/test/test_scope_vars.py::test_let`
- `glom/test/test_scope_vars.py::test_s_scope_assign`
