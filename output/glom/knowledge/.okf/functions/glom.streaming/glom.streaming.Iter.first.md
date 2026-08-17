---
type: "python-function"
title: "first"
description: "A convenience method for lazily yielding a single truthy item from"
resource: "/glom/streaming.py#L337-L352"
tags: ["glom", "streaming"]
sources: [{"resource": "/glom/streaming.py#L337-L352"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "side_effects"]}]
status: "stable"
---
# `glom.streaming.Iter.first`

`first(self, key=T, default=None)`

> A convenience method for lazily yielding a single truthy item from
> an iterable.
> 
> >>> target = [False, 1, 2, 3]
> >>> glom(target, Iter().first())
> 1
> 
> This method takes a condition, *key*, which can also be a
> glomspec, as well as a *default*, in case nothing matches the
> condition.
> 
> As this spec yields at most one item, and not an iterable, the
> spec returned from this method is not an :class:`Iter()` instance.

## Contract

- **inputs**: self: Iter instance; key: spec or callable to test items (defaults to T); default: value returned if no match (defaults to None)
- **outputs**: tuple of (self, First(key=key, default=default))
- **raises**: none
- **side_effects**: none

## Callees
`glom.streaming.First`

## Tested by
- `glom/test/test_streaming.py::test_first`
