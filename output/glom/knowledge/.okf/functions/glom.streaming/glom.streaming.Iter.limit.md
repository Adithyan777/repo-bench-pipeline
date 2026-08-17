---
type: "python-function"
title: "limit"
description: "A convenient alias for :meth:`~Iter.slice`, which takes a single"
resource: "/glom/streaming.py#L281-L285"
tags: ["glom", "streaming"]
sources: [{"resource": "/glom/streaming.py#L281-L285"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "side_effects"]}]
status: "stable"
---
# `glom.streaming.Iter.limit`

`limit(self, count)`

> A convenient alias for :meth:`~Iter.slice`, which takes a single
> argument, *count*, the max number of items to yield.

## Contract

- **inputs**: self: Iter instance; count: maximum number of items to yield
- **outputs**: new Iter spec with limit operation added
- **raises**: none
- **side_effects**: none

## Callees
`glom.streaming.Iter._add_op`

## Tested by
- `glom/test/test_streaming.py::test_slice`
- `glom/test/test_streaming.py::test_while`
