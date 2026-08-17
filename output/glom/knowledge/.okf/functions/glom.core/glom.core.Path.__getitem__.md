---
type: "python-function"
title: "__getitem__"
description: "a new Path representing the sliced/selected portion of the path"
resource: "/glom/core.py#L731-L754"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L731-L754"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.core.Path.__getitem__`

`__getitem__(self, i)`

## Contract

- **inputs**: self: a Path instance; i: an int index or slice
- **outputs**: a new Path representing the sliced/selected portion of the path
- **raises**: IndexError
- **side_effects**: none

## Callees
`glom.core.Path`, `glom.core.TType`

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
- `glom/test/test_path_and_t.py::test_path_getitem`
- `glom/test/test_path_and_t.py::test_path_slices`
