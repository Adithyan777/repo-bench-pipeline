---
type: "python-function"
title: "takewhile"
description: "Returns a new :class:`Iter()` spec which stops the stream once"
resource: "/glom/streaming.py#L287-L300"
tags: ["glom", "streaming"]
sources: [{"resource": "/glom/streaming.py#L287-L300"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "side_effects"]}]
status: "stable"
---
# `glom.streaming.Iter.takewhile`

`takewhile(self, key=T)`

> Returns a new :class:`Iter()` spec which stops the stream once
> *key* becomes falsy.
> 
> >>> glom([3, 2, 0, 1], Iter().takewhile().all())
> [3, 2]
> 
> :func:`itertools.takewhile` for more details.

## Contract

- **inputs**: self: Iter instance; key: spec or callable to test items (defaults to T)
- **outputs**: new Iter spec with takewhile operation added
- **raises**: none
- **side_effects**: none

## Callees
`glom.streaming.Iter._add_op`

## Tested by
- `glom/test/test_streaming.py::test_while`
