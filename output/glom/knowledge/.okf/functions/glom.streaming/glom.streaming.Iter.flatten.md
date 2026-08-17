---
type: "python-function"
title: "flatten"
description: "Returns a new :class:`Iter()` instance which combines iterables into a"
resource: "/glom/streaming.py#L232-L243"
tags: ["glom", "streaming"]
sources: [{"resource": "/glom/streaming.py#L232-L243"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "side_effects"]}]
status: "stable"
---
# `glom.streaming.Iter.flatten`

`flatten(self)`

> Returns a new :class:`Iter()` instance which combines iterables into a
> single iterable.
> 
> >>> target = [[1, 2], [3, 4], [5]]
> >>> list(glom(target, Iter().flatten()))
> [1, 2, 3, 4, 5]

## Contract

- **inputs**: self: Iter instance
- **outputs**: new Iter spec with flatten operation added
- **raises**: none
- **side_effects**: none

## Callees
`glom.streaming.Iter._add_op`

## Tested by
- `glom/test/test_streaming.py::test_iter_composition`
- `glom/test/test_streaming.py::test_split_flatten`
