---
type: "python-function"
title: "GROUP"
description: "Group mode dispatcher; also sentinel for current mode = group"
resource: "/glom/grouping.py#L98-L155"
tags: ["glom", "grouping"]
sources: [{"resource": "/glom/grouping.py#L98-L155"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "raises"]}]
status: "stable"
---
# `glom.grouping.GROUP`

`GROUP(target, spec, scope)`

> Group mode dispatcher; also sentinel for current mode = group

## Contract

- **inputs**: target: the current item being processed; spec: a grouping specification (dict, list, callable, or object with agg method); scope: the glom execution scope containing glom, ACC_TREE, etc.
- **outputs**: the accumulated result for the spec, or STOP, or SKIP; for dict specs returns the accumulated dict or STOP; for list specs returns the accumulated list or STOP; for callables/aggregators returns their result
- **raises**: BadSpec, ValueError
- **side_effects**: mutates tree (scope[ACC_TREE]) by inserting new accumulators and updating nested accumulator trees; may mutate scope[ACC_TREE] to point at sub-trees during recursion
- **invariants**: if spec is dict or list, the returned accumulator has the same type as spec; dict specs never produce a done result on the first item because SKIP/values always set done=False

## Callees
`glom.core.BadSpec`

## Tested by
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_grouping.py::test_agg`
- `glom/test/test_grouping.py::test_bucketing`
- `glom/test/test_grouping.py::test_corner_cases`
- `glom/test/test_grouping.py::test_limit`
- `glom/test/test_grouping.py::test_sample`
