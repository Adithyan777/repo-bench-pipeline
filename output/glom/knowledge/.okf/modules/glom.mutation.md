---
type: "python-module"
title: "glom.mutation"
description: "The glom.mutation module provides in-place mutation capabilities for glom, complementing the library's default behavior of safely returning transformed copies of data. It exposes the Assign specifier "
resource: "/glom/mutation.py#L1"
tags: ["glom", "mutation"]
sources: [{"resource": "/glom/mutation.py#L1"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# Module `glom.mutation`

## Purpose
The glom.mutation module provides in-place mutation capabilities for glom, complementing the library's default behavior of safely returning transformed copies of data. It exposes the Assign specifier type and assign() function for "deep-set" operations, as well as the Delete specifier type and delete() function for "deep-del" operations, enabling modification of existing nested data structures. The module includes PathDeleteError for signaling failed deletions, with a documented warning about the risks of unintended assignments to global state when specs are data-driven or user-provided.

## API

- [glom.mutation.Assign.__init__](../functions/glom.mutation/glom.mutation.Assign.__init__.md) — `__init__(self, path, val, missing=None)`
- [glom.mutation.Assign.glomit](../functions/glom.mutation/glom.mutation.Assign.glomit.md) — `glomit(self, target, scope)`
- [glom.mutation.Delete.__init__](../functions/glom.mutation/glom.mutation.Delete.__init__.md) — `__init__(self, path, ignore_missing=False)`
- [glom.mutation.Delete._del_one](../functions/glom.mutation/glom.mutation.Delete._del_one.md) — `_del_one(self, dest, op, arg, scope)`
- [glom.mutation.Delete.glomit](../functions/glom.mutation/glom.mutation.Delete.glomit.md) — `glomit(self, target, scope)`
- [glom.mutation.PathDeleteError.get_message](../functions/glom.mutation/glom.mutation.PathDeleteError.get_message.md) — `get_message(self)`
- [glom.mutation._apply_for_each](../functions/glom.mutation/glom.mutation._apply_for_each.md) — `_apply_for_each(func, path, val)`
- [glom.mutation._assign_autodiscover](../functions/glom.mutation/glom.mutation._assign_autodiscover.md) — `_assign_autodiscover(type_obj)`
- [glom.mutation._delete_autodiscover](../functions/glom.mutation/glom.mutation._delete_autodiscover.md) — `_delete_autodiscover(type_obj)`
- [glom.mutation.assign](../functions/glom.mutation/glom.mutation.assign.md) — `assign(obj, path, val, missing=None)`
- [glom.mutation.delete](../functions/glom.mutation/glom.mutation.delete.md) — `delete(obj, path, ignore_missing=False)`

## Internal helpers

- `__repr__(self)`
- `__repr__(self)`
- `_del_sequence_item(target, idx)`
- `_set_sequence_item(target, idx, val)`

## Calls
`glom.core.Path`, `glom.core._assign_op`, `glom.core.arg_val`, `glom.core.glom`, `glom.mutation.Assign`, `glom.mutation.Delete`, `glom.mutation.Delete._del_one`, `glom.mutation.PathDeleteError`, `glom.mutation._apply_for_each`

## Tested by
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_mutation.py::test_assign`
- `glom/test/test_mutation.py::test_assign_missing_dict`
- `glom/test/test_mutation.py::test_assign_missing_object`
- `glom/test/test_mutation.py::test_assign_missing_signature`
- `glom/test/test_mutation.py::test_assign_missing_unassignable`
- `glom/test/test_mutation.py::test_assign_missing_with_extant_keys`
- `glom/test/test_mutation.py::test_assign_recursive`
- `glom/test/test_mutation.py::test_assign_spec_val`
- `glom/test/test_mutation.py::test_bad_assign_target`
- `glom/test/test_mutation.py::test_bad_delete_target`
- `glom/test/test_mutation.py::test_delete`
- `glom/test/test_mutation.py::test_delete_ignore_missing`
- `glom/test/test_mutation.py::test_invalid_assign_op_target`
- `glom/test/test_mutation.py::test_invalid_delete_op_target`
- `glom/test/test_mutation.py::test_s_assign`
- `glom/test/test_mutation.py::test_sequence_assign`
- `glom/test/test_mutation.py::test_sequence_delete`
- `glom/test/test_mutation.py::test_star_broadcast`
- `glom/test/test_mutation.py::test_unregistered_assign`
- `glom/test/test_mutation.py::test_unregistered_delete`
- `glom/test/test_target_types.py::test_default_scope_register`
