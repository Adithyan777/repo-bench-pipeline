---
type: "python-function"
title: "slice"
description: "Returns a new :class:`Iter()` spec which trims iterables in the"
resource: "/glom/streaming.py#L261-L279"
tags: ["glom", "streaming"]
sources: [{"resource": "/glom/streaming.py#L261-L279"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "raises", "side_effects"]}]
status: "stable"
---
# `glom.streaming.Iter.slice`

`slice(self, *args)`

> Returns a new :class:`Iter()` spec which trims iterables in the
> same manner as :func:`itertools.islice`.
> 
> >>> target = [0, 1, 2, 3, 4, 5]
> >>> glom(target, Iter().slice(3).all())
> [0, 1, 2]
> >>> glom(target, Iter().slice(2, 4).all())
> [2, 3]
> 
> This method accepts only positional arguments.

## Contract

- **inputs**: self: Iter instance; *args: positional arguments for itertools.islice
- **outputs**: new Iter spec with slice operation added
- **raises**: TypeError
- **side_effects**: none

## Callees
`glom.streaming.Iter._add_op`

## Tested by
- `glom/test/test_streaming.py::test_slice`
