---
type: "python-function"
title: "all"
description: "A convenience method which returns a new spec which turns an"
resource: "/glom/streaming.py#L325-L335"
tags: ["glom", "streaming"]
sources: [{"resource": "/glom/streaming.py#L325-L335"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "side_effects"]}]
status: "stable"
---
# `glom.streaming.Iter.all`

`all(self)`

> A convenience method which returns a new spec which turns an
> iterable into a list.
> 
> >>> glom(range(5), Iter(lambda t: t * 2).all())
> [0, 2, 4, 6, 8]
> 
> Note that this spec will always consume the whole iterable, and as
> such, the spec returned is *not* an :class:`Iter()` instance.

## Contract

- **inputs**: self: Iter instance
- **outputs**: Pipe spec combining self and list constructor
- **raises**: none
- **side_effects**: none

## Callees
`glom.core.Pipe`

## Tested by
- `glom/test/test_snippets.py::test_snippet`
- `glom/test/test_streaming.py::test_all`
- `glom/test/test_streaming.py::test_filter`
