---
type: "python-function"
title: "agg"
description: "the current reservoir sample list (length up to self.size) after possibly incorporating target"
resource: "/glom/grouping.py#L257-L270"
tags: ["glom", "grouping"]
sources: [{"resource": "/glom/grouping.py#L257-L270"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.grouping.Sample.agg`

`agg(self, target, tree)`

## Contract

- **inputs**: self: the aggregator instance with attribute size; target: the value to sample; tree: a mutable mapping (accumulator tree) keyed by aggregator instances
- **outputs**: the current reservoir sample list (length up to self.size) after possibly incorporating target
- **raises**: none
- **side_effects**: mutates tree by inserting or updating tree[self] with [num_seen, sample_list]; may append to or replace an element in the sample list
- **invariants**: len(returned list) <= self.size; the returned list represents a simple reservoir sample of all targets seen so far

## Tested by
- `glom/test/test_grouping.py::test_sample`
