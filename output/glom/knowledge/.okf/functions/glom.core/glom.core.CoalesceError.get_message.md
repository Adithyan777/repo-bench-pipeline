---
type: "python-function"
title: "get_message"
description: "a formatted error message string describing the failed coalesce"
resource: "/glom/core.py#L430-L444"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L430-L444"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["side_effects"]}]
status: "stable"
---
# `glom.core.CoalesceError.get_message`

`get_message(self)`

## Contract

- **inputs**: self: a CoalesceError instance
- **outputs**: a formatted error message string describing the failed coalesce
- **raises**: none
- **side_effects**: none

## Tested by
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_error.py::test_coalesce_stack`
