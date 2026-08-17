---
type: "python-function"
title: "unique"
description: "Return a new :class:`Iter()` spec which lazily filters out duplicate"
resource: "/glom/streaming.py#L245-L258"
tags: ["glom", "streaming"]
sources: [{"resource": "/glom/streaming.py#L245-L258"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "side_effects"]}]
status: "stable"
---
# `glom.streaming.Iter.unique`

`unique(self, key=T)`

> Return a new :class:`Iter()` spec which lazily filters out duplicate
> values, i.e., only the first appearance of a value in a stream will
> be yielded.
> 
> >>> target = list('gloMolIcious')
> >>> out = list(glom(target, Iter().unique(T.lower())))
> >>> print(''.join(out))
> gloMIcus

## Contract

- **inputs**: self: Iter instance; key: spec or callable to determine uniqueness (defaults to T)
- **outputs**: new Iter spec with unique operation added
- **raises**: none
- **side_effects**: none

## Callees
`glom.streaming.Iter._add_op`

## Tested by
- `glom/test/test_streaming.py::test_iter_composition`
- `glom/test/test_streaming.py::test_unique`
