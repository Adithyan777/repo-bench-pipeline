---
type: "python-function"
title: "agg"
description: "target on the first call for this self; STOP on subsequent calls"
resource: "/glom/grouping.py#L167-L171"
tags: ["glom", "grouping"]
sources: [{"resource": "/glom/grouping.py#L167-L171"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.grouping.First.agg`

`agg(self, target, tree)`

## Contract

- **inputs**: self: the aggregator instance; target: the value to consider as the first element; tree: a mutable mapping (accumulator tree) keyed by aggregator instances
- **outputs**: target on the first call for this self; STOP on subsequent calls
- **raises**: none
- **side_effects**: mutates tree by inserting STOP under tree[self] on first call
- **invariants**: returns target at most once per self; after the first call, tree[self] is STOP and the method returns STOP

## Tested by
- `glom/test/test_grouping.py::test_agg`
