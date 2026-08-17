---
type: "python-function"
title: "fill"
description: "the result of glomming target with self as the spec"
resource: "/glom/core.py#L2537-L2538"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L2537-L2538"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "link", "side_effects"]}]
status: "stable"
---
# `glom.core.Fill.fill`

`fill(self, target)`

## Contract

- **inputs**: self: a Fill instance; target: the object being glommed
- **outputs**: the result of glomming target with self as the spec
- **raises**: none
- **side_effects**: none

## Callees
[glom.core.glom](glom.core.glom.md)

## Tested by
- `glom/test/test_fill.py::test`
