---
type: "python-function"
title: "format_invocation"
description: "Given a name, positional arguments, and keyword arguments, format"
resource: "/glom/core.py#L549-L577"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L549-L577"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callers", "link", "raises", "side_effects"]}]
status: "stable"
---
# `glom.core.format_invocation`

`format_invocation(name='', args=(), kwargs=None, **kw)`

> Given a name, positional arguments, and keyword arguments, format
> a basic Python-style function call.
> 
> >>> print(format_invocation('func', args=(1, 2), kwargs={'c': 3}))
> func(1, 2, c=3)
> >>> print(format_invocation('a_func', args=(1,)))
> a_func(1)
> >>> print(format_invocation('kw_func', kwargs=[('a', 1), ('b', 2)]))
> kw_func(a=1, b=2)

## Contract

- **inputs**: name: function name string (default ''); args: positional args tuple (default ()); kwargs: keyword args dict or sequence of pairs (default None); **kw: only accepts 'repr'
- **outputs**: a formatted function call string like 'name(args, kwargs)'
- **raises**: TypeError
- **side_effects**: none

## Callers
`glom.core.Coalesce.__repr__`, [glom.core.Invoke.__repr__](glom.core.Invoke.__repr__.md), `glom.core.Let.__repr__`, `glom.core.Vars.__repr__`, [glom.core._format_t](glom.core._format_t.md), `glom.matching.Check.__repr__`, [glom.reduction.Flatten.__repr__](../glom.reduction/glom.reduction.Flatten.__repr__.md), `glom.reduction.Fold.__repr__`, `glom.reduction.Sum.__repr__`, [glom.streaming.Iter.__repr__](../glom.streaming/glom.streaming.Iter.__repr__.md)

## Tested by
- `glom/test/generated/test_glom_streaming.py::test_chunked_repr`
- `glom/test/generated/test_glom_streaming.py::test_chunked_repr_with_fill`
- `glom/test/test_basic.py::test_coalesce`
- `glom/test/test_basic.py::test_invoke`
- `glom/test/test_basic.py::test_python_native`
- `glom/test/test_check.py::test_check_basic`
- `glom/test/test_check.py::test_check_multi`
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_error.py::test_coalesce_stack`
- `glom/test/test_grouping.py::test_agg`
- `glom/test/test_path_and_t.py::test_path_access_error_message`
- `glom/test/test_path_and_t.py::test_path_t_roundtrip`
- `glom/test/test_path_and_t.py::test_t_picklability`
- `glom/test/test_reduction.py::test_flatten`
- `glom/test/test_reduction.py::test_fold`
- `glom/test/test_reduction.py::test_sum_integers`
- `glom/test/test_scope_vars.py::test_let`
- `glom/test/test_scope_vars.py::test_s_scope_assign`
- `glom/test/test_scope_vars.py::test_vars`
- `glom/test/test_streaming.py::test_all`
- `glom/test/test_streaming.py::test_faulty_iterate`
- `glom/test/test_streaming.py::test_filter`
- `glom/test/test_streaming.py::test_first`
- `glom/test/test_streaming.py::test_map`
- `glom/test/test_streaming.py::test_slice`
- `glom/test/test_streaming.py::test_split_flatten`
- `glom/test/test_streaming.py::test_unique`
- `glom/test/test_streaming.py::test_windowed`
