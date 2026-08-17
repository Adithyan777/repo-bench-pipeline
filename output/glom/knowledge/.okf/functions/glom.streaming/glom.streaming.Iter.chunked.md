---
type: "python-function"
title: "chunked"
description: "Return a new :class:`Iter()` spec which groups elements in the iterable"
resource: "/glom/streaming.py#L167-L186"
tags: ["glom", "streaming"]
sources: [{"resource": "/glom/streaming.py#L167-L186"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "side_effects"]}]
status: "stable"
---
# `glom.streaming.Iter.chunked`

`chunked(self, size, fill=_MISSING)`

> Return a new :class:`Iter()` spec which groups elements in the iterable
> into lists of length *size*.
> 
> If the optional *fill* argument is provided, iterables not
> evenly divisible by *size* will be padded out by the *fill*
> constant. Otherwise, the final chunk will be shorter than *size*.
> 
> >>> list(glom(range(10), Iter().chunked(3)))
> [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]
> >>> list(glom(range(10), Iter().chunked(3, fill=None)))
> [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, None, None]]

## Contract

- **inputs**: self: Iter instance; size: chunk size int; fill: optional padding value (defaults to _MISSING)
- **outputs**: new Iter spec with chunked operation added
- **raises**: none
- **side_effects**: none

## Callees
`glom.streaming.Iter._add_op`

## Tested by
- `glom/test/generated/test_glom_streaming.py::test_chunked_basic_exact_division`
- `glom/test/generated/test_glom_streaming.py::test_chunked_empty_iterable`
- `glom/test/generated/test_glom_streaming.py::test_chunked_repr`
- `glom/test/generated/test_glom_streaming.py::test_chunked_repr_with_fill`
- `glom/test/generated/test_glom_streaming.py::test_chunked_returns_iter_spec`
- `glom/test/generated/test_glom_streaming.py::test_chunked_single_element`
- `glom/test/generated/test_glom_streaming.py::test_chunked_size_larger_than_iterable`
- `glom/test/generated/test_glom_streaming.py::test_chunked_size_larger_with_fill`
- `glom/test/generated/test_glom_streaming.py::test_chunked_size_one`
- `glom/test/generated/test_glom_streaming.py::test_chunked_with_fill`
- `glom/test/generated/test_glom_streaming.py::test_chunked_with_remainder_no_fill`
- `glom/test/test_streaming.py::test_chunked`
