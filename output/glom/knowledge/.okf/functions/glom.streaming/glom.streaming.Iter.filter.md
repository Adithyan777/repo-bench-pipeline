---
type: "python-function"
title: "filter"
description: "Return a new :class:`Iter()` spec which will include only elements matching the"
resource: "/glom/streaming.py#L140-L165"
tags: ["glom", "streaming"]
sources: [{"resource": "/glom/streaming.py#L140-L165"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "side_effects"]}]
status: "stable"
---
# `glom.streaming.Iter.filter`

`filter(self, key=T)`

> Return a new :class:`Iter()` spec which will include only elements matching the
> given *key*.
> 
> >>> glom(range(6), Iter().filter(lambda x: x % 2).all())
> [1, 3, 5]
> 
> Because a spec can be a callable, :meth:`Iter.filter()` does
> everything the built-in :func:`filter` does, but with the full
> power of glom specs. For even more power, combine,
> :meth:`Iter.filter()` with :class:`Check()`.
> 
> >>> # PROTIP: Python's ints know how many binary digits they require, using the bit_length method
> >>> glom(range(9), Iter().filter(Check(T.bit_length(), one_of=(2, 4), default=SKIP)).all())
> [2, 3, 8]

## Contract

- **inputs**: self: Iter instance; key: spec or callable to test items (defaults to T), or a Check instance
- **outputs**: new Iter spec with filter operation added
- **raises**: none
- **side_effects**: none

## Callees
`glom.matching.Check`, `glom.streaming.Iter._add_op`

## Tested by
- `glom/test/test_streaming.py::test_filter`
- `glom/test/test_streaming.py::test_windowed`
