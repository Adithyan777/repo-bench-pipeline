---
type: "python-function"
title: "map"
description: "Return a new :class:`Iter()` spec which will apply the provided"
resource: "/glom/streaming.py#L118-L138"
tags: ["glom", "streaming"]
sources: [{"resource": "/glom/streaming.py#L118-L138"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "side_effects"]}]
status: "stable"
---
# `glom.streaming.Iter.map`

`map(self, subspec)`

> Return a new :class:`Iter()` spec which will apply the provided
> *subspec* to each element of the iterable.
> 
> >>> glom(range(5), Iter().map(lambda x: x * 2).all())
> [0, 2, 4, 6, 8]
> 
> Because a spec can be a callable, :meth:`Iter.map()` does
> everything the built-in :func:`map` does, but with the full
> power of glom specs.
> 
> >>> glom(['a', 'B', 'C'], Iter().map(T.islower()).all())
> [True, False, False]

## Contract

- **inputs**: self: Iter instance; subspec: spec to apply to each element
- **outputs**: new Iter spec with map operation added
- **raises**: none
- **side_effects**: none

## Callees
`glom.streaming.Iter._add_op`

## Tested by
- `glom/test/test_streaming.py::test_chunked`
- `glom/test/test_streaming.py::test_map`
- `glom/test/test_streaming.py::test_windowed`
