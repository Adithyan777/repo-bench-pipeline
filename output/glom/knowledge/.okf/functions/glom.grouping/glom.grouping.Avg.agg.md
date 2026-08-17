---
type: "python-function"
title: "agg"
description: "the current running average (sum / count) as a float after incorporating target"
resource: "/glom/grouping.py#L187-L195"
tags: ["glom", "grouping"]
sources: [{"resource": "/glom/grouping.py#L187-L195"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.grouping.Avg.agg`

`agg(self, target, tree)`

## Contract

- **inputs**: self: the aggregator instance; target: a numeric value to incorporate into the running average; tree: a mutable mapping (accumulator tree) keyed by aggregator instances
- **outputs**: the current running average (sum / count) as a float after incorporating target
- **raises**: KeyError (internally caught)
- **side_effects**: mutates tree by inserting or updating a [sum, count] list under tree[self]
- **invariants**: the returned value equals the arithmetic mean of all target values seen so far for this aggregator instance

## Tested by
- `glom/test/test_grouping.py::test_agg`
