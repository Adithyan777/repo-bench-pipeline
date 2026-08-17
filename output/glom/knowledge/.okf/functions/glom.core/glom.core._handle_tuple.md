---
type: "python-function"
title: "_handle_tuple"
description: "the result of sequentially evaluating each subspec against the intermediate result"
resource: "/glom/core.py#L1957-L1969"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L1957-L1969"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "callers", "link"]}]
status: "stable"
---
# `glom.core._handle_tuple`

`_handle_tuple(target, spec, scope)`

## Contract

- **inputs**: target: the object being glommed; spec: a tuple specification; scope: the current evaluation scope (mapping)
- **outputs**: the result of sequentially evaluating each subspec against the intermediate result
- **raises**: none
- **side_effects**: mutates scope by creating child scopes and updating scope[Path]

## Callers
[glom.core.AUTO](glom.core.AUTO.md), [glom.core.Pipe.glomit](glom.core.Pipe.glomit.md)

## Callees
[glom.core.chain_child](glom.core.chain_child.md)

## Tested by
- `glom/test/test_basic.py::test_beyond_access`
- `glom/test/test_basic.py::test_initial_integration`
- `glom/test/test_basic.py::test_list_item_lift_and_access`
- `glom/test/test_basic.py::test_pipe`
- `glom/test/test_basic.py::test_python_native`
- `glom/test/test_basic.py::test_ref`
- `glom/test/test_basic.py::test_scope`
- `glom/test/test_basic.py::test_skip`
- `glom/test/test_basic.py::test_spec_and_recursion`
- `glom/test/test_basic.py::test_stop`
- `glom/test/test_check.py::test_check_basic`
- `glom/test/test_cli.py::test_main_python_full_spec_python_target`
- `glom/test/test_error.py::test_error`
- `glom/test/test_error.py::test_line_trace`
- `glom/test/test_error.py::test_nesting_stack`
- `glom/test/test_error.py::test_pae_api`
- `glom/test/test_error.py::test_partially_failing_branch`
- `glom/test/test_grouping.py::test_corner_cases`
- `glom/test/test_match.py::test_check_ported_tests`
- `glom/test/test_match.py::test_cruddy_json`
- `glom/test/test_match.py::test_nested_struct`
- `glom/test/test_match.py::test_pattern_matching`
- `glom/test/test_match.py::test_regex`
- `glom/test/test_mutation.py::test_delete`
- `glom/test/test_mutation.py::test_s_assign`
- `glom/test/test_mutation.py::test_star_broadcast`
- `glom/test/test_path_and_t.py::test_empty_path_access`
- `glom/test/test_path_and_t.py::test_t_subspec`
- `glom/test/test_reduction.py::test_flatten_func`
- `glom/test/test_scope_vars.py::test_globals`
- `glom/test/test_scope_vars.py::test_let`
- `glom/test/test_scope_vars.py::test_max_skip`
- `glom/test/test_scope_vars.py::test_s_scope_assign`
- `glom/test/test_scope_vars.py::test_scoped_vars`
- `glom/test/test_scope_vars.py::test_vars`
- `glom/test/test_snippets.py::test_snippet`
- `glom/test/test_streaming.py::test_all`
- `glom/test/test_streaming.py::test_faulty_iterate`
- `glom/test/test_streaming.py::test_filter`
- `glom/test/test_streaming.py::test_first`
- `glom/test/test_streaming.py::test_iter`
- `glom/test/test_streaming.py::test_iter_composition`
- `glom/test/test_streaming.py::test_while`
- `glom/test/test_target_types.py::test_faulty_iterate`
- `glom/test/test_target_types.py::test_types_bare`
