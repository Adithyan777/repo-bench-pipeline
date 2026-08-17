---
type: "python-function"
title: "glomit"
description: "iterator over processed target after applying all stacked operations"
resource: "/glom/streaming.py#L85-L91"
tags: ["glom", "streaming"]
sources: [{"resource": "/glom/streaming.py#L85-L91"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "link", "side_effects"]}]
status: "stable"
---
# `glom.streaming.Iter.glomit`

`glomit(self, target, scope)`

## Contract

- **inputs**: self: Iter instance; target: object to iterate over; scope: glom scope dict
- **outputs**: iterator over processed target after applying all stacked operations
- **raises**: none
- **side_effects**: none

## Callees
[glom.streaming.Iter._iterate](glom.streaming.Iter._iterate.md)

## Tested by
- `glom/test/generated/test_glom_streaming.py::test_chunked_basic_exact_division`
- `glom/test/generated/test_glom_streaming.py::test_chunked_empty_iterable`
- `glom/test/generated/test_glom_streaming.py::test_chunked_single_element`
- `glom/test/generated/test_glom_streaming.py::test_chunked_size_larger_than_iterable`
- `glom/test/generated/test_glom_streaming.py::test_chunked_size_larger_with_fill`
- `glom/test/generated/test_glom_streaming.py::test_chunked_size_one`
- `glom/test/generated/test_glom_streaming.py::test_chunked_with_fill`
- `glom/test/generated/test_glom_streaming.py::test_chunked_with_remainder_no_fill`
- `glom/test/test_basic.py::test_ref`
- `glom/test/test_streaming.py::test_all`
- `glom/test/test_streaming.py::test_chunked`
- `glom/test/test_streaming.py::test_faulty_iterate`
- `glom/test/test_streaming.py::test_filter`
- `glom/test/test_streaming.py::test_first`
- `glom/test/test_streaming.py::test_iter`
- `glom/test/test_streaming.py::test_iter_composition`
- `glom/test/test_streaming.py::test_map`
- `glom/test/test_streaming.py::test_slice`
- `glom/test/test_streaming.py::test_split_flatten`
- `glom/test/test_streaming.py::test_unique`
- `glom/test/test_streaming.py::test_while`
- `glom/test/test_streaming.py::test_windowed`
