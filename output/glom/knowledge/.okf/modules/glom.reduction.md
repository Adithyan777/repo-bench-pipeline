---
type: "python-module"
title: "glom.reduction"
description: "The glom.reduction module provides specifier types and helper functions for reducing and aggregating iterables in data, including counting elements, flattening nested iterables, folding iterables with"
resource: "/glom/reduction.py#L1"
tags: ["glom", "reduction"]
sources: [{"resource": "/glom/reduction.py#L1"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# Module `glom.reduction`

## Purpose
The glom.reduction module provides specifier types and helper functions for reducing and aggregating iterables in data, including counting elements, flattening nested iterables, folding iterables with custom logic, summing numerical values, and merging mappings into a single dict.

## API

- [glom.reduction.Flatten.__repr__](../functions/glom.reduction/glom.reduction.Flatten.__repr__.md) — `__repr__(self)`
- [glom.reduction.Fold.glomit](../functions/glom.reduction/glom.reduction.Fold.glomit.md) — `glomit(self, target, scope)`
- [glom.reduction.Merge.__init__](../functions/glom.reduction/glom.reduction.Merge.__init__.md) — `__init__(self, subspec=T, init=dict, op=None)`
- [glom.reduction.flatten](../functions/glom.reduction/glom.reduction.flatten.md) — `flatten(target, **kwargs)`
- [glom.reduction.merge](../functions/glom.reduction/glom.reduction.merge.md) — `merge(target, **kwargs)`

## Internal helpers

- `__init__(self)`
- `__repr__(self)`
- `__init__(self, subspec=T, init=list)`
- `_fold(self, iterator)`
- `__init__(self, subspec, init, op=operator.iadd)`
- `__repr__(self)`
- `_agg(self, target, tree)`
- `_fold(self, iterator)`
- `_agg(self, target, tree)`
- `_fold(self, iterator)`
- `__init__(self, subspec=T, init=int)`
- `__repr__(self)`

## Calls
`glom.core.format_invocation`, `glom.core.glom`, `glom.grouping.target_iter`, `glom.reduction.Flatten`, `glom.reduction.Fold._agg`, `glom.reduction.Fold._fold`, `glom.reduction.FoldError`, `glom.reduction.Merge`

## Tested by
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_grouping.py::test_agg`
- `glom/test/test_grouping.py::test_reduce`
- `glom/test/test_reduction.py::test_flatten`
- `glom/test/test_reduction.py::test_flatten_func`
- `glom/test/test_reduction.py::test_fold`
- `glom/test/test_reduction.py::test_fold_bad_iter`
- `glom/test/test_reduction.py::test_merge`
- `glom/test/test_reduction.py::test_merge_func`
- `glom/test/test_reduction.py::test_merge_omd`
- `glom/test/test_reduction.py::test_sum_integers`
- `glom/test/test_reduction.py::test_sum_seqs`
- `glom/test/test_snippets.py::test_snippet`
