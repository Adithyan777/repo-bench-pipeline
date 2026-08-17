---
type: "python-function"
title: "__repr__"
description: "a string representation of the Invoke spec construction"
resource: "/glom/core.py#L1273-L1299"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L1273-L1299"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "link", "side_effects"]}]
status: "stable"
---
# `glom.core.Invoke.__repr__`

`__repr__(self)`

## Contract

- **inputs**: self: an Invoke instance
- **outputs**: a string representation of the Invoke spec construction
- **raises**: none
- **side_effects**: none

## Callees
[glom.core.format_invocation](glom.core.format_invocation.md)

## Tested by
- `glom/test/test_basic.py::test_invoke`
