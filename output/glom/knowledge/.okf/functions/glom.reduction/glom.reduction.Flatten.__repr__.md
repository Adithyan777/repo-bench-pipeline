---
type: "python-function"
title: "__repr__"
description: "A string representation formatted by format_invocation using the class name, positional args (subspec if not T), and keyword args (init if lazy or not list)"
resource: "/glom/reduction.py#L178-L186"
tags: ["glom", "reduction"]
sources: [{"resource": "/glom/reduction.py#L178-L186"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "link", "side_effects"]}]
status: "stable"
---
# `glom.reduction.Flatten.__repr__`

`__repr__(self)`

## Contract

- **inputs**: self: the Flatten instance
- **outputs**: A string representation formatted by format_invocation using the class name, positional args (subspec if not T), and keyword args (init if lazy or not list)
- **raises**: none
- **side_effects**: none
- **invariants**: The returned string always starts with the class name and reflects the current subspec, lazy, and init state

## Callees
[glom.core.format_invocation](../glom.core/glom.core.format_invocation.md)

## Tested by
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_reduction.py::test_flatten`
