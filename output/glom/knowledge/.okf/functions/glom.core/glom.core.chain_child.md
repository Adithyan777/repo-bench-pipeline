---
type: "python-function"
title: "chain_child"
description: "used for specs like Auto(tuple), Switch(), etc"
resource: "/glom/core.py#L2302-L2322"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L2302-L2322"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callers", "link"]}]
status: "stable"
---
# `glom.core.chain_child`

`chain_child(scope)`

> used for specs like Auto(tuple), Switch(), etc
> that want to chain their child scopes together
> 
> returns a new scope that can be passed to
> the next recursive glom call, e.g.
> 
> scope[glom](target, spec, chain_child(scope))

## Contract

- **inputs**: scope: the current evaluation scope (ChainMap-like)
- **outputs**: a new child scope wired into the chain, or scope itself if no children yet
- **raises**: none
- **side_effects**: mutates nxt_in_chain.maps[0] by setting NO_PYFRAME and clearing CHILD_ERRORS

## Callers
[glom.core._handle_tuple](glom.core._handle_tuple.md), [glom.matching.Switch.glomit](../glom.matching/glom.matching.Switch.glomit.md), [glom.matching._handle_dict](../glom.matching/glom.matching._handle_dict.md)

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
- `glom/test/test_error.py::test_midway_branch`
- `glom/test/test_error.py::test_nesting_stack`
- `glom/test/test_error.py::test_pae_api`
- `glom/test/test_error.py::test_partially_failing_branch`
- `glom/test/test_grouping.py::test_corner_cases`
- `glom/test/test_match.py::test_basic`
- `glom/test/test_match.py::test_check_ported_tests`
- `glom/test/test_match.py::test_cruddy_json`
- `glom/test/test_match.py::test_json_ref`
- `glom/test/test_match.py::test_nested_dict`
- `glom/test/test_match.py::test_nested_struct`
- `glom/test/test_match.py::test_pattern_matching`
- `glom/test/test_match.py::test_precedence`
- `glom/test/test_match.py::test_regex`
- `glom/test/test_match.py::test_sample`
- `glom/test/test_match.py::test_switch`
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
