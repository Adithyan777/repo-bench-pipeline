---
type: "python-function"
title: "glomit"
description: "the result of evaluating self.spec against target with scope updated by self.scope"
resource: "/glom/core.py#L818-L820"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L818-L820"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.core.Spec.glomit`

`glomit(self, target, scope)`

## Contract

- **inputs**: self: a Spec instance; target: the object being glommed; scope: the current evaluation scope (mapping)
- **outputs**: the result of evaluating self.spec against target with scope updated by self.scope
- **raises**: none
- **side_effects**: mutates scope by updating it with self.scope

## Tested by
- `glom/test/test_basic.py::test_invoke`
- `glom/test/test_basic.py::test_spec_and_recursion`
- `glom/test/test_mutation.py::test_assign_spec_val`
- `glom/test/test_spec.py::test_scope_spec`
- `glom/test/test_spec.py::test_spec`
- `glom/test/test_streaming.py::test_first`
