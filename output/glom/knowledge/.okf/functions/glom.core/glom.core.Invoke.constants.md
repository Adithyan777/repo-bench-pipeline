---
type: "python-function"
title: "constants"
description: "Returns a new :class:`Invoke` spec, with the provided positional"
resource: "/glom/core.py#L1180-L1209"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L1180-L1209"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.core.Invoke.constants`

`constants(self, *a, **kw)`

> Returns a new :class:`Invoke` spec, with the provided positional
> and keyword argument values stored for passing to the
> underlying function.
> 
> >>> spec = Invoke(T).constants(5)
> >>> glom(range, (spec, list))
> [0, 1, 2, 3, 4]
> 
> Subsequent positional arguments are appended:
> 
> >>> spec = Invoke(T).constants(2).constants(10, 2)
> >>> glom(range, (spec, list))
> [2, 4, 6, 8]
> 
> Keyword arguments also work as one might expect:
> 
> >>> round_2 = Invoke(round).constants(ndigits=2).specs(T)
> >>> glom(3.14159, round_2)
> 3.14
> 
> :meth:`~Invoke.constants()` and other :class:`Invoke`
> methods may be called multiple times, just remember that every
> call returns a new spec.

## Contract

- **inputs**: self: an Invoke instance; *a: positional constant values; **kw: keyword constant values
- **outputs**: a new Invoke instance with the provided constants appended to its argument plan
- **raises**: none
- **side_effects**: none

## Tested by
- `glom/test/test_basic.py::test_invoke`
