---
type: "python-function"
title: "glomit"
description: "the result of calling the resolved func with resolved positional and keyword arguments"
resource: "/glom/core.py#L1301-L1324"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L1301-L1324"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "side_effects"]}]
status: "stable"
---
# `glom.core.Invoke.glomit`

`glomit(self, target, scope)`

## Contract

- **inputs**: self: an Invoke instance; target: the object being glommed; scope: the current evaluation scope (mapping)
- **outputs**: the result of calling the resolved func with resolved positional and keyword arguments
- **raises**: none
- **side_effects**: none

## Callees
`glom.core._is_spec`

## Tested by
- `glom/test/test_basic.py::test_invoke`
