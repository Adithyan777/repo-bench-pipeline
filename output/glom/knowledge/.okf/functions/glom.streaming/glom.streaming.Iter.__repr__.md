---
type: "python-function"
title: "__repr__"
description: "string representation of the Iter spec, reconstructing chained method calls"
resource: "/glom/streaming.py#L67-L83"
tags: ["glom", "streaming"]
sources: [{"resource": "/glom/streaming.py#L67-L83"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.streaming.Iter.__repr__`

`__repr__(self)`

## Contract

- **inputs**: self: Iter instance
- **outputs**: string representation of the Iter spec, reconstructing chained method calls
- **raises**: none
- **side_effects**: none

## Callees
[glom.core.format_invocation](../glom.core/glom.core.format_invocation.md)

## Tested by
- `glom/test/generated/test_glom_streaming.py::test_chunked_repr`
- `glom/test/generated/test_glom_streaming.py::test_chunked_repr_with_fill`
- `glom/test/test_streaming.py::test_all`
- `glom/test/test_streaming.py::test_faulty_iterate`
- `glom/test/test_streaming.py::test_filter`
- `glom/test/test_streaming.py::test_first`
- `glom/test/test_streaming.py::test_map`
- `glom/test/test_streaming.py::test_slice`
- `glom/test/test_streaming.py::test_split_flatten`
- `glom/test/test_streaming.py::test_unique`
- `glom/test/test_streaming.py::test_windowed`
