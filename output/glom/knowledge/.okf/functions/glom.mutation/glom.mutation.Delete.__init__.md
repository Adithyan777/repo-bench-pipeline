---
type: "python-function"
title: "__init__"
description: "none (initializes instance attributes: op, arg, _orig_path, path, ignore_missing)"
resource: "/glom/mutation.py#L271-L289"
tags: ["glom", "mutation"]
sources: [{"resource": "/glom/mutation.py#L271-L289"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.mutation.Delete.__init__`

`__init__(self, path, ignore_missing=False)`

## Contract

- **inputs**: self: the Delete instance; path: a string, Path, T, or S specifying the target location to delete; ignore_missing: boolean flag indicating whether to ignore missing targets
- **outputs**: none (initializes instance attributes: op, arg, _orig_path, path, ignore_missing)
- **raises**: TypeError, ValueError
- **side_effects**: none
- **invariants**: self.op is one of '[', '.', or 'P' after successful initialization; self.path is the original path with the last element removed

## Callees
`glom.core.Path`

## Tested by
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_mutation.py::test_bad_delete_target`
- `glom/test/test_mutation.py::test_delete`
- `glom/test/test_mutation.py::test_delete_ignore_missing`
- `glom/test/test_mutation.py::test_invalid_delete_op_target`
- `glom/test/test_mutation.py::test_sequence_delete`
- `glom/test/test_mutation.py::test_star_broadcast`
- `glom/test/test_mutation.py::test_unregistered_delete`
