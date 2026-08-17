---
type: "python-function"
title: "register"
description: "Register *target_type* so :meth:`~Glommer.glom()` will"
resource: "/glom/core.py#L2476-L2505"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L2476-L2505"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.core.Glommer.register`

`register(self, target_type, **kwargs)`

> Register *target_type* so :meth:`~Glommer.glom()` will
> know how to handle instances of that type as targets.
> 
> Args:
>    target_type (type): A type expected to appear in a glom()
>       call target
>    get (callable): A function which takes a target object and
>       a name, acting as a default accessor. Defaults to
>       :func:`getattr`.
>    iterate (callable): A function which takes a target object
>       and returns an iterator. Defaults to :func:`iter` if
>       *target_type* appears to be iterable.
>    exact (bool): Whether or not to match instances of subtypes
>       of *target_type*.
> 
> .. note::
> 
>    The module-level :func:`register()` function affects the
>    module-level :func:`glom()` function's behavior. If this
>    global effect is undesirable for your application, or
>    you're implementing a library, consider instantiating a
>    :class:`Glommer` instance, and using the
>    :meth:`~Glommer.register()` and :meth:`Glommer.glom()`
>    methods instead.

## Contract

- **inputs**: self: a Glommer instance; target_type: a type to register; **kwargs: get, iterate, exact, etc.
- **outputs**: none (implicitly returns None)
- **raises**: none
- **side_effects**: mutates self.scope[TargetRegistry] by registering target_type

## Tested by
- `glom/test/test_reduction.py::test_fold_bad_iter`
- `glom/test/test_streaming.py::test_faulty_iterate`
- `glom/test/test_target_types.py::test_duck_register`
- `glom/test/test_target_types.py::test_exact_register`
- `glom/test/test_target_types.py::test_faulty_iterate`
- `glom/test/test_target_types.py::test_invalid_register`
- `glom/test/test_target_types.py::test_iter_set`
- `glom/test/test_target_types.py::test_iter_str`
- `glom/test/test_target_types.py::test_types_bare`
