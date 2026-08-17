---
type: "python-function"
title: "glom"
description: "the result of calling glom with target, spec, scope=self.scope, and **kwargs"
resource: "/glom/core.py#L2507-L2508"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L2507-L2508"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "link", "side_effects"]}]
status: "stable"
---
# `glom.core.Glommer.glom`

`glom(self, target, spec, **kwargs)`

## Contract

- **inputs**: self: a Glommer instance; target: the object to glom; spec: the specification; **kwargs: extra keyword arguments forwarded to glom
- **outputs**: the result of calling glom with target, spec, scope=self.scope, and **kwargs
- **raises**: none
- **side_effects**: none

## Callees
[glom.core.glom](glom.core.glom.md)

## Tested by
- `glom/test/test_mutation.py::test_unregistered_assign`
- `glom/test/test_mutation.py::test_unregistered_delete`
- `glom/test/test_reduction.py::test_fold_bad_iter`
- `glom/test/test_streaming.py::test_faulty_iterate`
- `glom/test/test_target_types.py::test_duck_register`
- `glom/test/test_target_types.py::test_exact_register`
- `glom/test/test_target_types.py::test_faulty_iterate`
- `glom/test/test_target_types.py::test_iter_str`
- `glom/test/test_target_types.py::test_types_bare`
