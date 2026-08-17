---
type: "python-function"
title: "glomit"
description: "target (the original target object, after assignment is performed)"
resource: "/glom/mutation.py#L161-L189"
tags: ["glom", "mutation"]
sources: [{"resource": "/glom/mutation.py#L161-L189"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.mutation.Assign.glomit`

`glomit(self, target, scope)`

## Contract

- **inputs**: self: the Assign instance; target: the object being glommed; scope: the current glom scope dictionary
- **outputs**: target (the original target object, after assignment is performed)
- **raises**: PathAccessError
- **side_effects**: mutates the destination object by assigning val at the specified path
- **invariants**: if self.path.startswith(S), the destination target is scope[UP] instead of target; if a PathAccessError occurs and self.missing is set, missing() is called to create intermediate structures

## Callees
[glom.core._assign_op](../glom.core/glom.core._assign_op.md), [glom.core.arg_val](../glom.core/glom.core.arg_val.md), `glom.mutation.Assign`, [glom.mutation._apply_for_each](glom.mutation._apply_for_each.md)

## Tested by
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_mutation.py::test_assign`
- `glom/test/test_mutation.py::test_assign_missing_dict`
- `glom/test/test_mutation.py::test_assign_missing_object`
- `glom/test/test_mutation.py::test_assign_missing_unassignable`
- `glom/test/test_mutation.py::test_assign_missing_with_extant_keys`
- `glom/test/test_mutation.py::test_assign_recursive`
- `glom/test/test_mutation.py::test_assign_spec_val`
- `glom/test/test_mutation.py::test_bad_assign_target`
- `glom/test/test_mutation.py::test_s_assign`
- `glom/test/test_mutation.py::test_sequence_assign`
- `glom/test/test_mutation.py::test_star_broadcast`
- `glom/test/test_mutation.py::test_unregistered_assign`
