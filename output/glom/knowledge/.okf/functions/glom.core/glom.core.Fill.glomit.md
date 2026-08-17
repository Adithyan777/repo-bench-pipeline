---
type: "python-function"
title: "glomit"
description: "the result of glomming target with self.spec in FILL mode"
resource: "/glom/core.py#L2533-L2535"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L2533-L2535"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.core.Fill.glomit`

`glomit(self, target, scope)`

## Contract

- **inputs**: self: a Fill instance; target: the object being glommed; scope: the current evaluation scope (mapping)
- **outputs**: the result of glomming target with self.spec in FILL mode
- **raises**: none
- **side_effects**: mutates scope by setting scope[MODE] to FILL

## Tested by
- `glom/test/test_basic.py::test_ref`
- `glom/test/test_fill.py::test`
- `glom/test/test_match.py::test_pattern_matching`
- `glom/test/test_match.py::test_shortcircuit`
