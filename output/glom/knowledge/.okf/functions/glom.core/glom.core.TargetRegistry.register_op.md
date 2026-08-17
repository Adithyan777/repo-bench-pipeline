---
type: "python-function"
title: "register_op"
description: "add operations beyond the builtins ('get' and 'iterate' at the time"
resource: "/glom/core.py#L2133-L2176"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L2133-L2176"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "callers", "link", "raises"]}]
status: "stable"
---
# `glom.core.TargetRegistry.register_op`

`register_op(self, op_name, auto_func=None, exact=False)`

> add operations beyond the builtins ('get' and 'iterate' at the time
> of writing).
> 
> auto_func is a function that when passed a type, returns a
> handler associated with op_name if it's supported, or False if
> it's not.
> 
> See glom.core.register_op() for the global version used by
> extensions.

## Contract

- **inputs**: self: a TargetRegistry instance; op_name: operation name string; auto_func: optional callable returning handler or False; exact: whether to skip fuzzy registration
- **outputs**: none (implicitly returns None)
- **raises**: TypeError
- **side_effects**: mutates self._op_type_map, self._op_type_tree, self._op_auto_map, and clears self._type_cache

## Callers
`glom.core.TargetRegistry._register_builtin_ops`

## Callees
[glom.core.TargetRegistry._register_fuzzy_type](glom.core.TargetRegistry._register_fuzzy_type.md)

## Tested by
- `glom/test/test_mutation.py::test_unregistered_assign`
- `glom/test/test_mutation.py::test_unregistered_delete`
- `glom/test/test_reduction.py::test_fold_bad_iter`
- `glom/test/test_streaming.py::test_faulty_iterate`
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
