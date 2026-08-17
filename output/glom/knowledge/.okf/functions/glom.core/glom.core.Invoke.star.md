---
type: "python-function"
title: "star"
description: "Returns a new :class:`Invoke` spec, with *args* and/or *kwargs*"
resource: "/glom/core.py#L1245-L1271"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L1245-L1271"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.core.Invoke.star`

`star(self, args=None, kwargs=None)`

> Returns a new :class:`Invoke` spec, with *args* and/or *kwargs*
> specs set to be "starred" or "star-starred" (respectively)
> 
> >>> spec = Invoke(zip).star(args='lists')
> >>> target = {'lists': [[1, 2], [3, 4], [5, 6]]}
> >>> list(glom(target, spec))
> [(1, 3, 5), (2, 4, 6)]
> 
> Args:
>    args (spec): A spec to be evaluated and "starred" into the
>       underlying function.
>    kwargs (spec): A spec to be evaluated and "star-starred" into
>       the underlying function.
> 
> One or both of the above arguments should be set.
> 
> The :meth:`~Invoke.star()`, like other :class:`Invoke`
> methods, may be called multiple times. The *args* and *kwargs*
> will be stacked in the order in which they are provided.

## Contract

- **inputs**: self: an Invoke instance; args: a spec for *args (optional); kwargs: a spec for **kwargs (optional)
- **outputs**: a new Invoke instance with star args/kwargs appended to its argument plan
- **raises**: TypeError
- **side_effects**: none

## Tested by
- `glom/test/test_basic.py::test_invoke`
