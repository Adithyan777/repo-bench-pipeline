---
type: "python-function"
title: "delete"
description: "The ``delete()`` function provides \"deep del\" functionality,"
resource: "/glom/mutation.py#L335-L356"
tags: ["glom", "mutation"]
sources: [{"resource": "/glom/mutation.py#L335-L356"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "link"]}]
status: "stable"
---
# `glom.mutation.delete`

`delete(obj, path, ignore_missing=False)`

> The ``delete()`` function provides "deep del" functionality,
> modifying nested data structures in-place::
> 
>   >>> target = {'a': [{'b': 'c'}, {'d': None}]}
>   >>> delete(target, 'a.0.b')
>   {'a': [{}, {'d': None}]}
> 
> Attempting to delete missing keys, attributes, and indexes will
> raise a :exc:`PathDeleteError`. To ignore these errors, use the
> *ignore_missing* argument::
> 
>   >>> delete(target, 'does_not_exist', ignore_missing=True)
>   {'a': [{}, {'d': None}]}
> 
> For more information and examples, see the :class:`~glom.Delete`
> specifier type, which this convenience function wraps.
> 
> .. versionadded:: 20.5.0

## Contract

- **inputs**: obj: the target object to mutate; path: the path to delete; ignore_missing: boolean flag to suppress errors on missing targets
- **outputs**: the result of glom(obj, Delete(path, ignore_missing=ignore_missing))
- **raises**: none
- **side_effects**: mutates obj by deleting the item at the specified path
- **invariants**: this function wraps Delete in a glom call; returns the glom result

## Callees
[glom.core.glom](../glom.core/glom.core.glom.md), `glom.mutation.Delete`

## Tested by
- `glom/test/test_mutation.py::test_bad_delete_target`
- `glom/test/test_mutation.py::test_delete`
- `glom/test/test_mutation.py::test_delete_ignore_missing`
- `glom/test/test_mutation.py::test_invalid_delete_op_target`
- `glom/test/test_mutation.py::test_sequence_delete`
