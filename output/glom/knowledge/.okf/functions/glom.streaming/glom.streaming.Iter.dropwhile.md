---
type: "python-function"
title: "dropwhile"
description: "Returns a new :class:`Iter()` spec which drops stream items until"
resource: "/glom/streaming.py#L302-L321"
tags: ["glom", "streaming"]
sources: [{"resource": "/glom/streaming.py#L302-L321"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "side_effects"]}]
status: "stable"
---
# `glom.streaming.Iter.dropwhile`

`dropwhile(self, key=T)`

> Returns a new :class:`Iter()` spec which drops stream items until
> *key* becomes falsy.
> 
> >>> glom([0, 0, 3, 2, 0], Iter().dropwhile(lambda t: t < 1).all())
> [3, 2, 0]
> 
> Note that while similar to :meth:`Iter.filter()`, the filter
> only applies to the beginning of the stream. In a way,
> :meth:`Iter.dropwhile` can be thought of as
> :meth:`~str.lstrip()` for streams. See
> :func:`itertools.dropwhile` for more details.

## Contract

- **inputs**: self: Iter instance; key: spec or callable to test items (defaults to T)
- **outputs**: new Iter spec with dropwhile operation added
- **raises**: none
- **side_effects**: none

## Callees
`glom.streaming.Iter._add_op`

## Tested by
- `glom/test/test_streaming.py::test_while`
