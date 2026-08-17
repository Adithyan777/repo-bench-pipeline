---
type: "python-module"
title: "glom.grouping"
description: "The `glom.grouping` module implements \"Group mode,\" a glom dispatch mode that aggregates collections of values through nested, combinable operations like Avg, First, Max, Min, Limit, and Sample. It pr"
resource: "/glom/grouping.py#L1"
tags: ["glom", "grouping"]
sources: [{"resource": "/glom/grouping.py#L1"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# Module `glom.grouping`

## Purpose
The `glom.grouping` module implements "Group mode," a glom dispatch mode that aggregates collections of values through nested, combinable operations like Avg, First, Max, Min, Limit, and Sample. It provides a recursive grouping framework—analogous to boltons.iterutils.bucketize but in glom style—allowing engineers to bucket and reduce data within a glom pipeline. The public API consists of accumulator classes and a Group dispatcher that enables these grouping operations to be nested and applied to targets.

## API

- [glom.grouping.Avg.agg](../functions/glom.grouping/glom.grouping.Avg.agg.md) — `agg(self, target, tree)`
- [glom.grouping.First.agg](../functions/glom.grouping/glom.grouping.First.agg.md) — `agg(self, target, tree)`
- [glom.grouping.GROUP](../functions/glom.grouping/glom.grouping.GROUP.md) — `GROUP(target, spec, scope)`
- [glom.grouping.Group.glomit](../functions/glom.grouping/glom.grouping.Group.glomit.md) — `glomit(self, target, scope)`
- [glom.grouping.Limit.glomit](../functions/glom.grouping/glom.grouping.Limit.glomit.md) — `glomit(self, target, scope)`
- [glom.grouping.Max.agg](../functions/glom.grouping/glom.grouping.Max.agg.md) — `agg(self, target, tree)`
- [glom.grouping.Min.agg](../functions/glom.grouping/glom.grouping.Min.agg.md) — `agg(self, target, tree)`
- [glom.grouping.Sample.agg](../functions/glom.grouping/glom.grouping.Sample.agg.md) — `agg(self, target, tree)`
- [glom.grouping.target_iter](../functions/glom.grouping/glom.grouping.target_iter.md) — `target_iter(target, scope)`

## Internal helpers

- `__repr__(self)`
- `__repr__(self)`
- `__init__(self, spec)`
- `__repr__(self)`
- `__init__(self, n, subspec=_MISSING)`
- `__repr__(self)`
- `__repr__(self)`
- `__repr__(self)`
- `__init__(self, size)`
- `__repr__(self)`

## Calls
`glom.core.BadSpec`, `glom.core.Path`, `glom.grouping.target_iter`

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
