---
type: "python-function"
title: "agg"
description: "the current maximum value stored for this aggregator (either the previous max or target if larger)"
resource: "/glom/grouping.py#L211-L214"
tags: ["glom", "grouping"]
sources: [{"resource": "/glom/grouping.py#L211-L214"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.grouping.Max.agg`

`agg(self, target, tree)`

## Contract

- **inputs**: self: the aggregator instance; target: a value to compare; tree: a mutable mapping (accumulator tree) keyed by aggregator instances
- **outputs**: the current maximum value stored for this aggregator (either the previous max or target if larger)
- **raises**: none
- **side_effects**: mutates tree by inserting or updating tree[self] with the maximum value seen so far
- **invariants**: the returned value is the maximum of all target values seen so far for this self; tree[self] always holds the current maximum

## Tested by
- `glom/test/test_grouping.py::test_agg`
- `glom/test/test_grouping.py::test_limit`
