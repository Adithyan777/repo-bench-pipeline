---
type: "python-function"
title: "windowed"
description: "Return a new :class:`Iter()` spec which will yield a sliding window of"
resource: "/glom/streaming.py#L188-L199"
tags: ["glom", "streaming"]
sources: [{"resource": "/glom/streaming.py#L188-L199"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "side_effects"]}]
status: "stable"
---
# `glom.streaming.Iter.windowed`

`windowed(self, size)`

> Return a new :class:`Iter()` spec which will yield a sliding window of
> adjacent elements in the iterable. Each tuple yielded will be
> of length *size*.
> 
> Useful for getting adjacent pairs and triples.
> 
> >>> list(glom(range(4), Iter().windowed(2)))
> [(0, 1), (1, 2), (2, 3)]

## Contract

- **inputs**: self: Iter instance; size: window size int
- **outputs**: new Iter spec with windowed operation added
- **raises**: none
- **side_effects**: none

## Callees
`glom.streaming.Iter._add_op`

## Tested by
- `glom/test/test_streaming.py::test_windowed`
