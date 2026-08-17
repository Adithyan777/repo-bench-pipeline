---
type: "python-function"
title: "register"
description: "Register *target_type* so :meth:`~Glommer.glom()` will"
resource: "/glom/core.py#L2391-L2431"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L2391-L2431"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.core.register`

`register(target_type, **kwargs)`

> Register *target_type* so :meth:`~Glommer.glom()` will
> know how to handle instances of that type as targets.
> 
> Here's an example of adding basic iterabile support for Django's ORM:
> 
> .. code-block:: python
> 
>     import glom
>     import django.db.models
> 
>     glom.register(django.db.models.Manager, iterate=lambda m: m.all())
>     glom.register(django.db.models.QuerySet, iterate=lambda qs: qs.all())
> 
> 
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

- **inputs**: target_type: a type expected to appear as a glom target; **kwargs: optional keyword arguments including get, iterate, and exact
- **outputs**: None
- **raises**: none
- **side_effects**: Registers target_type in the default scope's TargetRegistry, affecting subsequent module-level glom() behavior.
- **invariants**: The module-level default scope is mutated.

## Tested by
- `glom/test/test_target_types.py::test_default_scope_register`
