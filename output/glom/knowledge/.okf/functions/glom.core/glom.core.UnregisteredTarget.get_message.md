---
type: "python-function"
title: "get_message"
description: "a formatted error message string describing the unregistered target type"
resource: "/glom/core.py#L489-L499"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L489-L499"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["side_effects"]}]
status: "stable"
---
# `glom.core.UnregisteredTarget.get_message`

`get_message(self)`

## Contract

- **inputs**: self: an UnregisteredTarget instance
- **outputs**: a formatted error message string describing the unregistered target type
- **raises**: none
- **side_effects**: none

## Tested by
- `glom/test/test_basic.py::test_ref`
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_mutation.py::test_unregistered_assign`
- `glom/test/test_mutation.py::test_unregistered_delete`
- `glom/test/test_reduction.py::test_flatten_func`
- `glom/test/test_target_types.py::test_duck_register`
- `glom/test/test_target_types.py::test_exact_register`
- `glom/test/test_target_types.py::test_iter_str`
- `glom/test/test_target_types.py::test_types_bare`
