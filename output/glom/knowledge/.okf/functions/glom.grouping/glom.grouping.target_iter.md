---
type: "python-function"
title: "target_iter"
description: "an iterator over target produced by the registered iterate handler"
resource: "/glom/grouping.py#L32-L40"
tags: ["glom", "grouping"]
sources: [{"resource": "/glom/grouping.py#L32-L40"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "callers", "link", "raises", "side_effects"]}]
status: "stable"
---
# `glom.grouping.target_iter`

`target_iter(target, scope)`

## Contract

- **inputs**: target: the object to iterate over; scope: the glom execution scope containing TargetRegistry and Path
- **outputs**: an iterator over target produced by the registered iterate handler
- **raises**: TypeError
- **side_effects**: none
- **invariants**: the returned iterator yields the elements of target according to the registered iterate handler

## Callers
[glom.grouping.Group.glomit](glom.grouping.Group.glomit.md), [glom.reduction.Fold.glomit](../glom.reduction/glom.reduction.Fold.glomit.md)

## Callees
`glom.core.Path`

## Tested by
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_grouping.py::test_agg`
- `glom/test/test_grouping.py::test_bucketing`
- `glom/test/test_grouping.py::test_corner_cases`
- `glom/test/test_grouping.py::test_limit`
- `glom/test/test_grouping.py::test_reduce`
- `glom/test/test_grouping.py::test_sample`
- `glom/test/test_reduction.py::test_flatten`
- `glom/test/test_reduction.py::test_flatten_func`
- `glom/test/test_reduction.py::test_fold`
- `glom/test/test_reduction.py::test_fold_bad_iter`
- `glom/test/test_reduction.py::test_merge`
- `glom/test/test_reduction.py::test_merge_func`
- `glom/test/test_reduction.py::test_merge_omd`
- `glom/test/test_reduction.py::test_sum_integers`
- `glom/test/test_reduction.py::test_sum_seqs`
