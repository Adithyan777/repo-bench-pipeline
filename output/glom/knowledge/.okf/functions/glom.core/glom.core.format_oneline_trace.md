---
type: "python-function"
title: "format_oneline_trace"
description: "unpack a scope into a single line summary"
resource: "/glom/core.py#L283-L307"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L283-L307"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "link", "side_effects"]}]
status: "stable"
---
# `glom.core.format_oneline_trace`

`format_oneline_trace(scope)`

> unpack a scope into a single line summary
> (shortest summary possible)

## Contract

- **inputs**: scope: the current evaluation scope
- **outputs**: a single-line string summarizing the evaluation stack
- **raises**: none
- **side_effects**: none

## Callees
[glom.core._unpack_stack](glom.core._unpack_stack.md)

## Tested by
- `glom/test/test_error.py::test_line_trace`
