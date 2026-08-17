---
type: "python-function"
title: "_t_eval"
description: "the result of evaluating the TType path against target/scope"
resource: "/glom/core.py#L1541-L1659"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L1541-L1659"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.core._t_eval`

`_t_eval(target, _t, scope)`

## Contract

- **inputs**: target: the object being glommed; _t: a TType instance; scope: the current evaluation scope (mapping)
- **outputs**: the result of evaluating the TType path against target/scope
- **raises**: BadSpec, PathAccessError, ValueError
- **side_effects**: mutates scope[Path] and may mutate scope via S() assignment or A assignment

## Callers
[glom.core.AUTO](glom.core.AUTO.md), [glom.core.Path.glomit](glom.core.Path.glomit.md), [glom.core._glom](glom.core._glom.md), [glom.core._t_eval](glom.core._t_eval.md)

## Callees
`glom.core.BadSpec`, `glom.core.Call`, `glom.core.Path`, `glom.core.PathAccessError`, `glom.core.TType`, [glom.core._assign_op](glom.core._assign_op.md), [glom.core._extend_children](glom.core._extend_children.md), `glom.core._s_first_magic`, [glom.core._t_eval](glom.core._t_eval.md), [glom.core.arg_val](glom.core.arg_val.md)

## Tested by
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_basic_glom`
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_debug_and_inspect_with_closed_stdin`
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_debug_wraps_spec`
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_glom_dict_result`
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_glom_error_returns_one`
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_indent_zero_disables_pretty`
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_inspect_wraps_spec`
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_scalar_non_scalar`
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_scalar_output`
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_sort_keys`
- `glom/test/test_basic.py::test_beyond_access`
- `glom/test/test_basic.py::test_call_and_target`
- `glom/test/test_basic.py::test_coalesce`
- `glom/test/test_basic.py::test_initial_integration`
- `glom/test/test_basic.py::test_inspect`
- `glom/test/test_basic.py::test_invoke`
- `glom/test/test_basic.py::test_list_item_lift_and_access`
- `glom/test/test_basic.py::test_pipe`
- `glom/test/test_basic.py::test_python_native`
- `glom/test/test_basic.py::test_ref`
- `glom/test/test_basic.py::test_scope`
- `glom/test/test_basic.py::test_seq_getitem`
- `glom/test/test_basic.py::test_skip`
- `glom/test/test_basic.py::test_spec_and_recursion`
- `glom/test/test_basic.py::test_stop`
- `glom/test/test_basic.py::test_top_level_default`
- `glom/test/test_basic.py::test_val`
- `glom/test/test_check.py::test_check_basic`
- `glom/test/test_cli.py::test_cli_blank`
- `glom/test/test_cli.py::test_cli_scalar`
- `glom/test/test_cli.py::test_cli_spec_argv_target_stdin_basic`
- `glom/test/test_cli.py::test_cli_spec_target_argv_basic`
- `glom/test/test_cli.py::test_cli_spec_target_files_basic`
- `glom/test/test_cli.py::test_main_basic`
- `glom/test/test_cli.py::test_main_python_full_spec_python_target`
- `glom/test/test_cli.py::test_main_toml_target`
- `glom/test/test_cli.py::test_main_yaml_target`
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_error.py::test_branching_stack`
- `glom/test/test_error.py::test_coalesce_stack`
- `glom/test/test_error.py::test_error`
- `glom/test/test_error.py::test_glom_dev_debug`
- `glom/test/test_error.py::test_glom_error_double_stack`
- `glom/test/test_error.py::test_glom_error_stack`
- `glom/test/test_error.py::test_good_error`
- `glom/test/test_error.py::test_line_trace`
- `glom/test/test_error.py::test_long_target_repr`
- `glom/test/test_error.py::test_midway_branch`
- `glom/test/test_error.py::test_nesting_stack`
- `glom/test/test_error.py::test_pae_api`
- `glom/test/test_error.py::test_pae_scope_printable`
- `glom/test/test_error.py::test_partially_failing_branch`
- `glom/test/test_error.py::test_unicode_stack`
- `glom/test/test_fill.py::test`
- `glom/test/test_grouping.py::test_agg`
- `glom/test/test_grouping.py::test_bucketing`
- `glom/test/test_grouping.py::test_corner_cases`
- `glom/test/test_grouping.py::test_limit`
- `glom/test/test_match.py::test_check_ported_tests`
- `glom/test/test_match.py::test_examples`
- `glom/test/test_match.py::test_m_call_match`
- `glom/test/test_match.py::test_nested_dict`
- `glom/test/test_match.py::test_pattern_matching`
- `glom/test/test_match.py::test_regex`
- `glom/test/test_match.py::test_sky`
- `glom/test/test_match.py::test_switch`
- `glom/test/test_mutation.py::test_assign`
- `glom/test/test_mutation.py::test_assign_missing_dict`
- `glom/test/test_mutation.py::test_assign_missing_object`
- `glom/test/test_mutation.py::test_assign_missing_unassignable`
- `glom/test/test_mutation.py::test_assign_missing_with_extant_keys`
- `glom/test/test_mutation.py::test_assign_recursive`
- `glom/test/test_mutation.py::test_assign_spec_val`
- `glom/test/test_mutation.py::test_bad_assign_target`
- `glom/test/test_mutation.py::test_bad_delete_target`
- `glom/test/test_mutation.py::test_delete`
- `glom/test/test_mutation.py::test_delete_ignore_missing`
- `glom/test/test_mutation.py::test_s_assign`
- `glom/test/test_mutation.py::test_sequence_assign`
- `glom/test/test_mutation.py::test_sequence_delete`
- `glom/test/test_mutation.py::test_star_broadcast`
- `glom/test/test_mutation.py::test_unregistered_assign`
- `glom/test/test_mutation.py::test_unregistered_delete`
- `glom/test/test_path_and_t.py::test_a_forbidden`
- `glom/test/test_path_and_t.py::test_empty_path_access`
- `glom/test/test_path_and_t.py::test_list_path_access`
- `glom/test/test_path_and_t.py::test_path`
- `glom/test/test_path_and_t.py::test_path_access_error_message`
- `glom/test/test_path_and_t.py::test_path_star`
- `glom/test/test_path_and_t.py::test_s_magic`
- `glom/test/test_path_and_t.py::test_star_broadcast`
- `glom/test/test_path_and_t.py::test_star_warning`
- `glom/test/test_path_and_t.py::test_t_arithmetic`
- `glom/test/test_path_and_t.py::test_t_arithmetic_errors`
- `glom/test/test_path_and_t.py::test_t_dict_key`
- `glom/test/test_path_and_t.py::test_t_dunders`
- `glom/test/test_path_and_t.py::test_t_picklability`
- `glom/test/test_path_and_t.py::test_t_subspec`
- `glom/test/test_reduction.py::test_flatten_func`
- `glom/test/test_reduction.py::test_sum_integers`
- `glom/test/test_scope_vars.py::test_globals`
- `glom/test/test_scope_vars.py::test_let`
- `glom/test/test_scope_vars.py::test_max_skip`
- `glom/test/test_scope_vars.py::test_s_scope_assign`
- `glom/test/test_scope_vars.py::test_scoped_vars`
- `glom/test/test_scope_vars.py::test_vars`
- `glom/test/test_snippets.py::test_snippet`
- `glom/test/test_spec.py::test_scope_spec`
- `glom/test/test_spec.py::test_spec`
- `glom/test/test_streaming.py::test_filter`
- `glom/test/test_streaming.py::test_first`
- `glom/test/test_streaming.py::test_iter_composition`
- `glom/test/test_streaming.py::test_unique`
- `glom/test/test_streaming.py::test_while`
- `glom/test/test_target_types.py::test_bypass_getitem`
- `glom/test/test_target_types.py::test_faulty_iterate`
- `glom/test/test_target_types.py::test_types_bare`
- `glom/test/test_tutorial.py::test_tutorial`
