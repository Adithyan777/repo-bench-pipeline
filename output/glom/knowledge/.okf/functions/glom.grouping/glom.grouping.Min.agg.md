---
type: "python-function"
title: "agg"
description: "the current minimum value stored for this aggregator (either the previous min or target if smaller)"
resource: "/glom/grouping.py#L230-L233"
tags: ["glom", "grouping"]
sources: [{"resource": "/glom/grouping.py#L230-L233"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.grouping.Min.agg`

`agg(self, target, tree)`

## Contract

- **inputs**: self: the aggregator instance; target: a value to compare; tree: a mutable mapping (accumulator tree) keyed by aggregator instances
- **outputs**: the current minimum value stored for this aggregator (either the previous min or target if smaller)
- **raises**: none
- **side_effects**: mutates tree by inserting or updating tree[self] with the minimum value seen so far
- **invariants**: the returned value is the minimum of all target values seen so far for this self; tree[self] always holds the current minimum

## Tested by
- `glom/test/test_grouping.py::test_agg`
