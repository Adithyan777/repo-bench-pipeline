---
type: "python-function"
title: "_del_one"
description: "none"
resource: "/glom/mutation.py#L291-L310"
tags: ["glom", "mutation"]
sources: [{"resource": "/glom/mutation.py#L291-L310"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "callers", "link", "raises"]}]
status: "stable"
---
# `glom.mutation.Delete._del_one`

`_del_one(self, dest, op, arg, scope)`

## Contract

- **inputs**: self: the Delete instance; dest: the object from which to delete; op: operation character ('[', '.', or 'P'); arg: the key/attribute/index to delete; scope: the current glom scope dictionary
- **outputs**: none
- **raises**: PathDeleteError
- **side_effects**: mutates dest by deleting arg according to op
- **invariants**: if ignore_missing is True, exceptions during deletion are suppressed and PathDeleteError is not raised

## Callers
[glom.mutation.Delete.glomit](glom.mutation.Delete.glomit.md)

## Callees
`glom.mutation.PathDeleteError`

## Tested by
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_mutation.py::test_bad_delete_target`
- `glom/test/test_mutation.py::test_delete`
- `glom/test/test_mutation.py::test_delete_ignore_missing`
- `glom/test/test_mutation.py::test_sequence_delete`
- `glom/test/test_mutation.py::test_star_broadcast`
- `glom/test/test_mutation.py::test_unregistered_delete`
