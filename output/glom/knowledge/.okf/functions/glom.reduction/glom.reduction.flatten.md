---
type: "python-function"
title: "flatten"
description: "At its most basic, ``flatten()`` turns an iterable of iterables"
resource: "/glom/reduction.py#L189-L263"
tags: ["glom", "reduction"]
sources: [{"resource": "/glom/reduction.py#L189-L263"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "link", "raises", "side_effects"]}]
status: "stable"
---
# `glom.reduction.flatten`

`flatten(target, **kwargs)`

> At its most basic, ``flatten()`` turns an iterable of iterables
> into a single list. But it has a few arguments which give it more
> power:
> 
> Args:
> 
>    init (callable): A function or type which gives the initial
>       value of the return. The value must support addition. Common
>       values might be :class:`list` (the default), :class:`tuple`,
>       or even :class:`int`. You can also pass ``init="lazy"`` to
>       get a generator.
>    levels (int): A positive integer representing the number of
>       nested levels to flatten. Defaults to 1.
>    spec: The glomspec to fetch before flattening. This defaults to the
>       the root level of the object.
> 
> Usage is straightforward.
> 
>   >>> target = [[1, 2], [3], [4]]
>   >>> flatten(target)
>   [1, 2, 3, 4]
> 
> Because integers themselves support addition, we actually have two
> levels of flattening possible, to get back a single integer sum:
> 
>   >>> flatten(target, init=int, levels=2)
>   10
> 
> However, flattening a non-iterable like an integer will raise an
> exception:
> 
>   >>> target = 10
>   >>> flatten(target)
>   Traceback (most recent call last):
>   ...
>   FoldError: can only Flatten on iterable targets, not int type (...)
> 
> By default, ``flatten()`` will add a mix of iterables together,
> making it a more-robust alternative to the built-in
> ``sum(list_of_lists, list())`` trick most experienced Python
> programmers are familiar with using:
> 
>   >>> list_of_iterables = [range(2), [2, 3], (4, 5)]
>   >>> sum(list_of_iterables, [])
>   Traceback (most recent call last):
>   ...
>   TypeError: can only concatenate list (not "tuple") to list
> 
> Whereas flatten() handles this just fine:
> 
>   >>> flatten(list_of_iterables)
>   [0, 1, 2, 3, 4, 5]
> 
> The ``flatten()`` function is a convenient wrapper around the
> :class:`Flatten` specifier type. For embedding in larger specs,
> and more involved flattening, see :class:`Flatten` and its base,
> :class:`Fold`.

## Contract

- **inputs**: target: the value to flatten; **kwargs: keyword arguments including spec (default T), init (default list), and levels (default 1)
- **outputs**: The flattened result: a single list by default, or other type depending on init and levels
- **raises**: TypeError, ValueError
- **side_effects**: none
- **invariants**: If levels is 0, returns target unchanged; if levels is negative, raises ValueError

## Callees
[glom.core.glom](../glom.core/glom.core.glom.md), `glom.reduction.Flatten`

## Tested by
- `glom/test/test_reduction.py::test_flatten_func`
