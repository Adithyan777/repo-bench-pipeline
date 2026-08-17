---
type: "python-function"
title: "glomit"
description: "target (the original target object, after deletion is performed)"
resource: "/glom/mutation.py#L312-L328"
tags: ["glom", "mutation"]
sources: [{"resource": "/glom/mutation.py#L312-L328"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.mutation.Delete.glomit`

`glomit(self, target, scope)`

## Contract

- **inputs**: self: the Delete instance; target: the object being glommed; scope: the current glom scope dictionary
- **outputs**: target (the original target object, after deletion is performed)
- **raises**: PathAccessError
- **side_effects**: mutates the destination object by deleting the specified path
- **invariants**: if self.path.startswith(S), the destination target is scope[UP] instead of target; if a PathAccessError occurs and ignore_missing is True, the error is suppressed

## Callees
[glom.mutation.Delete._del_one](glom.mutation.Delete._del_one.md), [glom.mutation._apply_for_each](glom.mutation._apply_for_each.md)

## Tested by
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_mutation.py::test_bad_delete_target`
- `glom/test/test_mutation.py::test_delete`
- `glom/test/test_mutation.py::test_delete_ignore_missing`
- `glom/test/test_mutation.py::test_sequence_delete`
- `glom/test/test_mutation.py::test_star_broadcast`
- `glom/test/test_mutation.py::test_unregistered_delete`
