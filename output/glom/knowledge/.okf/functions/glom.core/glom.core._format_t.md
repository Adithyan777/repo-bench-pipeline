---
type: "python-function"
title: "_format_t"
description: "a formatted string representation of the T expression"
resource: "/glom/core.py#L1727-L1762"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L1727-L1762"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "callers", "link", "side_effects"]}]
status: "stable"
---
# `glom.core._format_t`

`_format_t(path, root=T)`

## Contract

- **inputs**: path: a TType operations path tuple; root: the root TType (default T)
- **outputs**: a formatted string representation of the T expression
- **raises**: none
- **side_effects**: none

## Callers
`glom.core.TType.__repr__`, [glom.core._format_path](glom.core._format_path.md)

## Callees
[glom.core._format_path](glom.core._format_path.md), [glom.core._format_slice](glom.core._format_slice.md), [glom.core.format_invocation](glom.core.format_invocation.md)

## Tested by
- `glom/test/test_basic.py::test_call_and_target`
- `glom/test/test_basic.py::test_invoke`
- `glom/test/test_basic.py::test_python_native`
- `glom/test/test_basic.py::test_ref`
- `glom/test/test_check.py::test_check_basic`
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_error.py::test_branching_stack`
- `glom/test/test_error.py::test_error`
- `glom/test/test_error.py::test_line_trace`
- `glom/test/test_error.py::test_midway_branch`
- `glom/test/test_error.py::test_pae_scope_printable`
- `glom/test/test_error.py::test_partially_failing_branch`
- `glom/test/test_fill.py::test`
- `glom/test/test_grouping.py::test_corner_cases`
- `glom/test/test_match.py::test_and_or_reduction`
- `glom/test/test_match.py::test_m_call_match`
- `glom/test/test_mutation.py::test_assign`
- `glom/test/test_mutation.py::test_delete`
- `glom/test/test_path_and_t.py::test_path_access_error_message`
- `glom/test/test_path_and_t.py::test_path_t_roundtrip`
- `glom/test/test_path_and_t.py::test_s_magic`
- `glom/test/test_path_and_t.py::test_t_arithmetic_errors`
- `glom/test/test_path_and_t.py::test_t_arithmetic_reprs`
- `glom/test/test_path_and_t.py::test_t_picklability`
- `glom/test/test_reduction.py::test_flatten_func`
- `glom/test/test_reduction.py::test_fold`
- `glom/test/test_scope_vars.py::test_let`
- `glom/test/test_scope_vars.py::test_s_scope_assign`
- `glom/test/test_scope_vars.py::test_vars`
- `glom/test/test_spec.py::test_scope_spec`
- `glom/test/test_streaming.py::test_filter`
- `glom/test/test_streaming.py::test_first`
- `glom/test/test_streaming.py::test_map`
- `glom/test/test_streaming.py::test_split_flatten`
- `glom/test/test_streaming.py::test_unique`
