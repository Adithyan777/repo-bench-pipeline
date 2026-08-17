---
type: "python-function"
title: "register"
description: "none (implicitly returns None)"
resource: "/glom/core.py#L2097-L2131"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L2097-L2131"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "callers", "link", "raises"]}]
status: "stable"
---
# `glom.core.TargetRegistry.register`

`register(self, target_type, **kwargs)`

## Contract

- **inputs**: self: a TargetRegistry instance; target_type: a type to register; **kwargs: exact, get, iterate, etc.
- **outputs**: none (implicitly returns None)
- **raises**: TypeError
- **side_effects**: mutates self._op_type_map, self._op_type_tree, and clears self._type_cache

## Callers
`glom.core.TargetRegistry._register_default_types`

## Callees
[glom.core.TargetRegistry._register_fuzzy_type](glom.core.TargetRegistry._register_fuzzy_type.md)

## Tested by
- `glom/test/test_reduction.py::test_fold_bad_iter`
- `glom/test/test_streaming.py::test_faulty_iterate`
- `glom/test/test_target_types.py::test_default_scope_register`
- `glom/test/test_target_types.py::test_duck_register`
- `glom/test/test_target_types.py::test_exact_register`
- `glom/test/test_target_types.py::test_faulty_iterate`
- `glom/test/test_target_types.py::test_faulty_op_registration`
- `glom/test/test_target_types.py::test_invalid_register`
- `glom/test/test_target_types.py::test_iter_set`
- `glom/test/test_target_types.py::test_iter_str`
- `glom/test/test_target_types.py::test_reregister_type`
- `glom/test/test_target_types.py::test_types_bare`
- `glom/test/test_target_types.py::test_types_leave_one_out`
