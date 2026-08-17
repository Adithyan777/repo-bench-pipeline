---
type: "python-function"
title: "__call__"
description: "a new TType representing a call operation with the given args and kwargs"
resource: "/glom/core.py#L1442-L1449"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L1442-L1449"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "raises", "side_effects"]}]
status: "stable"
---
# `glom.core.TType.__call__`

`__call__(self, *args, **kwargs)`

## Contract

- **inputs**: self: a TType instance (T or S); *args: positional arguments; **kwargs: keyword arguments
- **outputs**: a new TType representing a call operation with the given args and kwargs
- **raises**: TypeError
- **side_effects**: none
- **invariants**: if self is S, no positional args are allowed and at least one kwarg is required

## Callees
`glom.core._t_child`

## Tested by
- `glom/test/test_basic.py::test_call_and_target`
- `glom/test/test_basic.py::test_python_native`
- `glom/test/test_check.py::test_check_basic`
- `glom/test/test_cli.py::test_main_python_full_spec_python_target`
- `glom/test/test_grouping.py::test_corner_cases`
- `glom/test/test_match.py::test_pattern_matching`
- `glom/test/test_match.py::test_switch`
- `glom/test/test_mutation.py::test_delete`
- `glom/test/test_mutation.py::test_invalid_assign_op_target`
- `glom/test/test_mutation.py::test_invalid_delete_op_target`
- `glom/test/test_path_and_t.py::test_a_forbidden`
- `glom/test/test_path_and_t.py::test_path_access_error_message`
- `glom/test/test_path_and_t.py::test_path_items`
- `glom/test/test_path_and_t.py::test_path_len`
- `glom/test/test_path_and_t.py::test_path_slices`
- `glom/test/test_path_and_t.py::test_path_t_roundtrip`
- `glom/test/test_path_and_t.py::test_path_values`
- `glom/test/test_path_and_t.py::test_t_picklability`
- `glom/test/test_path_and_t.py::test_t_subspec`
- `glom/test/test_scope_vars.py::test_max_skip`
- `glom/test/test_scope_vars.py::test_s_scope_assign`
- `glom/test/test_scope_vars.py::test_vars`
- `glom/test/test_snippets.py::test_snippet`
- `glom/test/test_streaming.py::test_while`
