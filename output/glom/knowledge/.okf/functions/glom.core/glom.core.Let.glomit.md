---
type: "python-function"
title: "glomit"
description: "target (unchanged)"
resource: "/glom/core.py#L1863-L1866"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L1863-L1866"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.core.Let.glomit`

`glomit(self, target, scope)`

## Contract

- **inputs**: self: a Let instance; target: the object being glommed; scope: the current evaluation scope (mapping)
- **outputs**: target (unchanged)
- **raises**: none
- **side_effects**: mutates scope by updating it with evaluated bindings from self._binding

## Tested by
- `glom/test/test_scope_vars.py::test_let`
