---
type: "python-function"
title: "merge"
description: "By default, ``merge()`` turns an iterable of mappings into a"
resource: "/glom/reduction.py#L322-L348"
tags: ["glom", "reduction"]
sources: [{"resource": "/glom/reduction.py#L322-L348"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "link", "raises", "side_effects"]}]
status: "stable"
---
# `glom.reduction.merge`

`merge(target, **kwargs)`

> By default, ``merge()`` turns an iterable of mappings into a
> single, merged :class:`dict`, leveraging the behavior of the
> :meth:`~dict.update` method. A new mapping is created and none of
> the passed mappings are modified.
> 
> >>> target = [{'a': 'alpha'}, {'b': 'B'}, {'a': 'A'}]
> >>> res = merge(target)
> >>> pprint(res)
> {'a': 'A', 'b': 'B'}
> 
> Args:
>    target: The list of dicts, or some other iterable of mappings.
> 
> The start state can be customized with the *init* keyword
> argument, as well as the update operation, with the *op* keyword
> argument. For more on those customizations, see the :class:`Merge`
> spec.

## Contract

- **inputs**: target: the value to merge (iterable of mappings); **kwargs: keyword arguments including spec (default T), init (default dict), and op (default None)
- **outputs**: The merged mapping result
- **raises**: TypeError
- **side_effects**: none
- **invariants**: The returned result is produced by glomming target with a Merge spec constructed from subspec, init, and op

## Callees
[glom.core.glom](../glom.core/glom.core.glom.md), `glom.reduction.Merge`

## Tested by
- `glom/test/test_reduction.py::test_merge_func`
