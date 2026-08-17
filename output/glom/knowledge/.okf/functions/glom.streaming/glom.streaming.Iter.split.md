---
type: "python-function"
title: "split"
description: "Return a new :class:`Iter()` spec which will lazily split an iterable based"
resource: "/glom/streaming.py#L201-L230"
tags: ["glom", "streaming"]
sources: [{"resource": "/glom/streaming.py#L201-L230"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "side_effects"]}]
status: "stable"
---
# `glom.streaming.Iter.split`

`split(self, sep=None, maxsplit=None)`

> Return a new :class:`Iter()` spec which will lazily split an iterable based
> on a separator (or list of separators), *sep*. Like
> :meth:`str.split()`, but for all iterables.
> 
> ``split_iter()`` yields lists of non-separator values. A separator will
> never appear in the output.
> 
> >>> target = [1, 2, None, None, 3, None, 4, None]
> >>> list(glom(target, Iter().split()))
> [[1, 2], [3], [4]]
> 
> Note that ``split_iter`` is based on :func:`str.split`, so if
> *sep* is ``None``, ``split()`` **groups** separators. If empty lists
> are desired between two contiguous ``None`` values, simply use
> ``sep=[None]``:
> 
> >>> list(glom(target, Iter().split(sep=[None])))
> [[1, 2], [], [3], [4], []]
> 
> A max number of splits may also be set:
> 
> >>> list(glom(target, Iter().split(maxsplit=2)))
> [[1, 2], [3], [4, None]]

## Contract

- **inputs**: self: Iter instance; sep: separator value or list of values (defaults to None); maxsplit: maximum number of splits (defaults to None)
- **outputs**: new Iter spec with split operation added
- **raises**: none
- **side_effects**: none

## Callees
`glom.streaming.Iter._add_op`

## Tested by
- `glom/test/test_streaming.py::test_split_flatten`
