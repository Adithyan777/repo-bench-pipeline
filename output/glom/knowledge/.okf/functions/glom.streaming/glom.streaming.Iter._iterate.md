---
type: "python-function"
title: "_iterate"
description: "generator yielding processed items from target, or None if sentinel/STOP encountered"
resource: "/glom/streaming.py#L93-L113"
tags: ["glom", "streaming"]
sources: [{"resource": "/glom/streaming.py#L93-L113"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "callers", "link", "raises"]}]
status: "stable"
---
# `glom.streaming.Iter._iterate`

`_iterate(self, target, scope)`

## Contract

- **inputs**: self: Iter instance; target: iterable target; scope: glom scope dict containing TargetRegistry, Path, and glom
- **outputs**: generator yielding processed items from target, or None if sentinel/STOP encountered
- **raises**: TypeError
- **side_effects**: mutates scope[Path] during iteration

## Callers
[glom.streaming.Iter.glomit](glom.streaming.Iter.glomit.md)

## Callees
`glom.core.Path`

## Tested by
- `glom/test/generated/test_glom_streaming.py::test_chunked_basic_exact_division`
- `glom/test/generated/test_glom_streaming.py::test_chunked_empty_iterable`
- `glom/test/generated/test_glom_streaming.py::test_chunked_single_element`
- `glom/test/generated/test_glom_streaming.py::test_chunked_size_larger_than_iterable`
- `glom/test/generated/test_glom_streaming.py::test_chunked_size_larger_with_fill`
- `glom/test/generated/test_glom_streaming.py::test_chunked_size_one`
- `glom/test/generated/test_glom_streaming.py::test_chunked_with_fill`
- `glom/test/generated/test_glom_streaming.py::test_chunked_with_remainder_no_fill`
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
