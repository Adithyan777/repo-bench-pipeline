---
type: "python-function"
title: "__init__"
description: "none (initializes instance attributes: op, arg, _orig_path, path, val, missing)"
resource: "/glom/mutation.py#L133-L159"
tags: ["glom", "mutation"]
sources: [{"resource": "/glom/mutation.py#L133-L159"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.mutation.Assign.__init__`

`__init__(self, path, val, missing=None)`

## Contract

- **inputs**: self: the Assign instance; path: a string, Path, T, or S specifying the target location to assign to; val: the value to assign; missing: optional callable that returns a default object when intermediate path parts are missing
- **outputs**: none (initializes instance attributes: op, arg, _orig_path, path, val, missing)
- **raises**: TypeError, ValueError
- **side_effects**: none
- **invariants**: self.op is one of '[', '.', or 'P' after successful initialization; self.path is the original path with the last element removed

## Callees
`glom.core.Path`

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
- `glom/test/test_mutation.py::test_invalid_assign_op_target`
- `glom/test/test_mutation.py::test_s_assign`
- `glom/test/test_mutation.py::test_sequence_assign`
- `glom/test/test_mutation.py::test_star_broadcast`
- `glom/test/test_mutation.py::test_unregistered_assign`
