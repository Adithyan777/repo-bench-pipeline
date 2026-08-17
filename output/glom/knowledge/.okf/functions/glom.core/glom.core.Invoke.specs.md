---
type: "python-function"
title: "specs"
description: "Returns a new :class:`Invoke` spec, with the provided positional"
resource: "/glom/core.py#L1211-L1243"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L1211-L1243"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.core.Invoke.specs`

`specs(self, *a, **kw)`

> Returns a new :class:`Invoke` spec, with the provided positional
> and keyword arguments stored to be interpreted as specs, with
> the results passed to the underlying function.
> 
> >>> spec = Invoke(range).specs('value')
> >>> glom({'value': 5}, (spec, list))
> [0, 1, 2, 3, 4]
> 
> Subsequent positional arguments are appended:
> 
> >>> spec = Invoke(range).specs('start').specs('end', 'step')
> >>> target = {'start': 2, 'end': 10, 'step': 2}
> >>> glom(target, (spec, list))
> [2, 4, 6, 8]
> 
> Keyword arguments also work as one might expect:
> 
> >>> multiply = lambda x, y: x * y
> >>> times_3 = Invoke(multiply).constants(y=3).specs(x='value')
> >>> glom({'value': 5}, times_3)
> 15
> 
> :meth:`~Invoke.specs()` and other :class:`Invoke`
> methods may be called multiple times, just remember that every
> call returns a new spec.

## Contract

- **inputs**: self: an Invoke instance; *a: positional specs; **kw: keyword specs
- **outputs**: a new Invoke instance with the provided specs appended to its argument plan
- **raises**: none
- **side_effects**: none

## Tested by
- `glom/test/test_basic.py::test_invoke`
