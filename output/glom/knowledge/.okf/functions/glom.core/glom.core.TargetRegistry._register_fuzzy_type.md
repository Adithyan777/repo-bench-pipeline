---
type: "python-function"
title: "_register_fuzzy_type"
description: "Build a \"type tree\", an OrderedDict mapping registered types to"
resource: "/glom/core.py#L2065-L2095"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L2065-L2095"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "callers", "link"]}]
status: "stable"
---
# `glom.core.TargetRegistry._register_fuzzy_type`

`_register_fuzzy_type(self, op, new_type, _type_tree=None)`

> Build a "type tree", an OrderedDict mapping registered types to
> their subtypes
> 
> The type tree's invariant is that a key in the mapping is a
> valid parent type of all its children.
> 
> Order is preserved such that non-overlapping parts of the
> subtree take precedence by which was most recently added.

## Contract

- **inputs**: self: a TargetRegistry instance; op: operation name; new_type: type to register; _type_tree: optional OrderedDict subtree
- **outputs**: the updated type tree OrderedDict
- **raises**: none
- **side_effects**: mutates _type_tree by inserting new_type and reordering existing types

## Callers
[glom.core.TargetRegistry._register_fuzzy_type](glom.core.TargetRegistry._register_fuzzy_type.md), [glom.core.TargetRegistry.register](glom.core.TargetRegistry.register.md), [glom.core.TargetRegistry.register_op](glom.core.TargetRegistry.register_op.md)

## Callees
[glom.core.TargetRegistry._register_fuzzy_type](glom.core.TargetRegistry._register_fuzzy_type.md)

## Tested by
- `glom/test/test_reduction.py::test_fold_bad_iter`
- `glom/test/test_streaming.py::test_faulty_iterate`
- `glom/test/test_target_types.py::test_default_scope_register`
- `glom/test/test_target_types.py::test_duck_register`
- `glom/test/test_target_types.py::test_faulty_iterate`
- `glom/test/test_target_types.py::test_faulty_op_registration`
- `glom/test/test_target_types.py::test_invalid_register`
- `glom/test/test_target_types.py::test_iter_set`
- `glom/test/test_target_types.py::test_iter_str`
- `glom/test/test_target_types.py::test_reregister_type`
- `glom/test/test_target_types.py::test_types_bare`
- `glom/test/test_target_types.py::test_types_leave_one_out`
