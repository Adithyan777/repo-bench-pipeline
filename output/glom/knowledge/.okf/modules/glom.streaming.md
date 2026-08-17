---
type: "python-module"
title: "glom.streaming"
description: "The `glom.streaming` module provides specifier types for incrementally processing streaming targets (e.g., database rows, file lines) without excessive memory usage. Its public API centers on the `Ite"
resource: "/glom/streaming.py#L1"
tags: ["glom", "streaming"]
sources: [{"resource": "/glom/streaming.py#L1"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# Module `glom.streaming`

## Purpose
The `glom.streaming` module provides specifier types for incrementally processing streaming targets (e.g., database rows, file lines) without excessive memory usage. Its public API centers on the `Iter` specifier, which offers methods like `map`, `filter`, `slice`, and `chunked` to lazily transform iterable targets, along with convenience utilities such as `First` for extracting the first matching element.

## API

- [glom.streaming.First.glomit](../functions/glom.streaming/glom.streaming.First.glomit.md) — `glomit(self, target, scope)`
- [glom.streaming.Iter.__repr__](../functions/glom.streaming/glom.streaming.Iter.__repr__.md) — `__repr__(self)`
- [glom.streaming.Iter._iterate](../functions/glom.streaming/glom.streaming.Iter._iterate.md) — `_iterate(self, target, scope)`
- [glom.streaming.Iter.all](../functions/glom.streaming/glom.streaming.Iter.all.md) — `all(self)`
- [glom.streaming.Iter.chunked](../functions/glom.streaming/glom.streaming.Iter.chunked.md) — `chunked(self, size, fill=_MISSING)`
- [glom.streaming.Iter.dropwhile](../functions/glom.streaming/glom.streaming.Iter.dropwhile.md) — `dropwhile(self, key=T)`
- [glom.streaming.Iter.filter](../functions/glom.streaming/glom.streaming.Iter.filter.md) — `filter(self, key=T)`
- [glom.streaming.Iter.first](../functions/glom.streaming/glom.streaming.Iter.first.md) — `first(self, key=T, default=None)`
- [glom.streaming.Iter.flatten](../functions/glom.streaming/glom.streaming.Iter.flatten.md) — `flatten(self)`
- [glom.streaming.Iter.glomit](../functions/glom.streaming/glom.streaming.Iter.glomit.md) — `glomit(self, target, scope)`
- [glom.streaming.Iter.limit](../functions/glom.streaming/glom.streaming.Iter.limit.md) — `limit(self, count)`
- [glom.streaming.Iter.map](../functions/glom.streaming/glom.streaming.Iter.map.md) — `map(self, subspec)`
- [glom.streaming.Iter.slice](../functions/glom.streaming/glom.streaming.Iter.slice.md) — `slice(self, *args)`
- [glom.streaming.Iter.split](../functions/glom.streaming/glom.streaming.Iter.split.md) — `split(self, sep=None, maxsplit=None)`
- [glom.streaming.Iter.takewhile](../functions/glom.streaming/glom.streaming.Iter.takewhile.md) — `takewhile(self, key=T)`
- [glom.streaming.Iter.unique](../functions/glom.streaming/glom.streaming.Iter.unique.md) — `unique(self, key=T)`
- [glom.streaming.Iter.windowed](../functions/glom.streaming/glom.streaming.Iter.windowed.md) — `windowed(self, size)`

## Internal helpers

- `__init__(self, key=T, default=None)`
- `__repr__(self)`
- `__init__(self, subspec=T, **kwargs)`
- `_add_op(self, opname, args, callback)`

## Calls
`glom.core.Call`, `glom.core.Path`, `glom.core.Pipe`, `glom.core.Spec`, `glom.core.format_invocation`, `glom.matching.Check`, `glom.streaming.First`, `glom.streaming.Iter._add_op`, `glom.streaming.Iter._iterate`

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
- `glom/test/test_basic.py::test_ref`
- `glom/test/test_snippets.py::test_snippet`
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
