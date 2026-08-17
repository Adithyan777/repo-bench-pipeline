---
type: "python-function"
title: "_handle_list"
description: "a list of evaluated subspec results for each iterated target item"
resource: "/glom/core.py#L1936-L1954"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L1936-L1954"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "callers", "link", "raises"]}]
status: "stable"
---
# `glom.core._handle_list`

`_handle_list(target, spec, scope)`

## Contract

- **inputs**: target: the object being glommed; spec: a list specification; scope: the current evaluation scope (mapping)
- **outputs**: a list of evaluated subspec results for each iterated target item
- **raises**: TypeError
- **side_effects**: mutates scope[Path] by appending indices during iteration

## Callers
[glom.core.AUTO](glom.core.AUTO.md)

## Callees
`glom.core.Path`

## Tested by
- `glom/test/test_basic.py::test_beyond_access`
- `glom/test/test_basic.py::test_initial_integration`
- `glom/test/test_basic.py::test_list_item_lift_and_access`
- `glom/test/test_basic.py::test_python_native`
- `glom/test/test_basic.py::test_ref`
- `glom/test/test_basic.py::test_scope`
- `glom/test/test_basic.py::test_skip`
- `glom/test/test_basic.py::test_spec_and_recursion`
- `glom/test/test_basic.py::test_stop`
- `glom/test/test_check.py::test_check_basic`
- `glom/test/test_cli.py::test_main_python_full_spec_python_target`
- `glom/test/test_error.py::test_3_11_byte_code_caret`
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_error.py::test_error`
- `glom/test/test_error.py::test_glom_error_double_stack`
- `glom/test/test_error.py::test_glom_error_stack`
- `glom/test/test_error.py::test_line_trace`
- `glom/test/test_error.py::test_regular_error_stack`
- `glom/test/test_match.py::test_check_ported_tests`
- `glom/test/test_match.py::test_clamp`
- `glom/test/test_match.py::test_examples`
- `glom/test/test_path_and_t.py::test_t_subspec`
- `glom/test/test_reduction.py::test_sum_integers`
- `glom/test/test_scope_vars.py::test_globals`
- `glom/test/test_scope_vars.py::test_let`
- `glom/test/test_scope_vars.py::test_max_skip`
- `glom/test/test_scope_vars.py::test_s_scope_assign`
- `glom/test/test_scope_vars.py::test_scoped_vars`
- `glom/test/test_snippets.py::test_snippet`
- `glom/test/test_target_types.py::test_duck_register`
- `glom/test/test_target_types.py::test_exact_register`
- `glom/test/test_target_types.py::test_faulty_iterate`
- `glom/test/test_target_types.py::test_iter_set`
- `glom/test/test_target_types.py::test_iter_str`
- `glom/test/test_target_types.py::test_types_bare`
