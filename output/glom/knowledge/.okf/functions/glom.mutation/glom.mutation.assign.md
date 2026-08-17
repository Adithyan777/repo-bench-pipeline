---
type: "python-function"
title: "assign"
description: "*New in glom 18.3.0*"
resource: "/glom/mutation.py#L198-L213"
tags: ["glom", "mutation"]
sources: [{"resource": "/glom/mutation.py#L198-L213"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "link"]}]
status: "stable"
---
# `glom.mutation.assign`

`assign(obj, path, val, missing=None)`

> *New in glom 18.3.0*
> 
> The ``assign()`` function provides convenient "deep set"
> functionality, modifying nested data structures in-place::
> 
>   >>> target = {'a': [{'b': 'c'}, {'d': None}]}
>   >>> _ = assign(target, 'a.1.d', 'e')  # let's give 'd' a value of 'e'
>   >>> pprint(target)
>   {'a': [{'b': 'c'}, {'d': 'e'}]}
> 
> Missing structures can also be automatically created with the
> *missing* parameter. For more information and examples, see the
> :class:`~glom.Assign` specifier type, which this function wraps.

## Contract

- **inputs**: obj: the target object to mutate; path: the path where val should be assigned; val: the value to assign; missing: optional callable that returns a default object for missing intermediate structures
- **outputs**: the result of glom(obj, Assign(path, val, missing=missing))
- **raises**: none
- **side_effects**: mutates obj by assigning val at the specified path
- **invariants**: this function wraps Assign in a glom call; returns the glom result

## Callees
[glom.core.glom](../glom.core/glom.core.glom.md), `glom.mutation.Assign`

## Tested by
- `glom/test/test_mutation.py::test_assign`
- `glom/test/test_mutation.py::test_assign_missing_dict`
- `glom/test/test_mutation.py::test_assign_missing_object`
- `glom/test/test_mutation.py::test_assign_missing_signature`
- `glom/test/test_mutation.py::test_assign_missing_unassignable`
- `glom/test/test_mutation.py::test_assign_missing_with_extant_keys`
- `glom/test/test_mutation.py::test_bad_assign_target`
- `glom/test/test_mutation.py::test_invalid_assign_op_target`
- `glom/test/test_mutation.py::test_sequence_assign`
