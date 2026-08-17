---
type: "python-function"
title: "get_handler"
description: "for an operation and object **instance**, obj, return the"
resource: "/glom/core.py#L2010-L2037"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L2010-L2037"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "link", "raises"]}]
status: "stable"
---
# `glom.core.TargetRegistry.get_handler`

`get_handler(self, op, obj, path=None, raise_exc=True)`

> for an operation and object **instance**, obj, return the
> closest-matching handler function, raising UnregisteredTarget
> if no handler can be found for *obj* (or False if
> raise_exc=False)

## Contract

- **inputs**: self: a TargetRegistry instance; op: operation name; obj: an object instance; path: optional path for error context; raise_exc: whether to raise if not found (default True)
- **outputs**: the handler function for op and obj, or False if not found and raise_exc is False
- **raises**: UnregisteredTarget
- **side_effects**: mutates self._type_cache by caching the resolved handler

## Callees
[glom.core.TargetRegistry._get_closest_type](glom.core.TargetRegistry._get_closest_type.md), [glom.core.TargetRegistry.get_type_map](glom.core.TargetRegistry.get_type_map.md), `glom.core.UnregisteredTarget`

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
- `glom/test/generated/test_glom_streaming.py::test_chunked_basic_exact_division`
- `glom/test/generated/test_glom_streaming.py::test_chunked_empty_iterable`
- `glom/test/generated/test_glom_streaming.py::test_chunked_single_element`
- `glom/test/generated/test_glom_streaming.py::test_chunked_size_larger_than_iterable`
- `glom/test/generated/test_glom_streaming.py::test_chunked_size_larger_with_fill`
- `glom/test/generated/test_glom_streaming.py::test_chunked_size_one`
- `glom/test/generated/test_glom_streaming.py::test_chunked_with_fill`
- `glom/test/generated/test_glom_streaming.py::test_chunked_with_remainder_no_fill`
- `glom/test/test_basic.py::test_beyond_access`
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
- `glom/test/test_cli.py::test_cli_scalar`
- `glom/test/test_cli.py::test_cli_spec_argv_target_stdin_basic`
- `glom/test/test_cli.py::test_cli_spec_target_argv_basic`
- `glom/test/test_cli.py::test_cli_spec_target_files_basic`
- `glom/test/test_cli.py::test_main_basic`
- `glom/test/test_cli.py::test_main_python_full_spec_python_target`
- `glom/test/test_cli.py::test_main_toml_target`
- `glom/test/test_cli.py::test_main_yaml_target`
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_error.py::test_coalesce_stack`
- `glom/test/test_error.py::test_error`
- `glom/test/test_error.py::test_glom_dev_debug`
- `glom/test/test_error.py::test_glom_error_double_stack`
- `glom/test/test_error.py::test_glom_error_stack`
- `glom/test/test_error.py::test_good_error`
- `glom/test/test_error.py::test_line_trace`
- `glom/test/test_error.py::test_long_target_repr`
- `glom/test/test_error.py::test_nesting_stack`
- `glom/test/test_error.py::test_pae_api`
- `glom/test/test_error.py::test_partially_failing_branch`
- `glom/test/test_error.py::test_regular_error_stack`
- `glom/test/test_error.py::test_unicode_stack`
- `glom/test/test_fill.py::test`
- `glom/test/test_grouping.py::test_agg`
- `glom/test/test_grouping.py::test_bucketing`
- `glom/test/test_grouping.py::test_corner_cases`
- `glom/test/test_grouping.py::test_limit`
- `glom/test/test_grouping.py::test_reduce`
- `glom/test/test_grouping.py::test_sample`
- `glom/test/test_match.py::test_check_ported_tests`
- `glom/test/test_match.py::test_clamp`
- `glom/test/test_match.py::test_examples`
- `glom/test/test_match.py::test_switch`
- `glom/test/test_mutation.py::test_assign`
- `glom/test/test_mutation.py::test_assign_missing_dict`
- `glom/test/test_mutation.py::test_assign_missing_object`
- `glom/test/test_mutation.py::test_assign_missing_unassignable`
- `glom/test/test_mutation.py::test_assign_missing_with_extant_keys`
- `glom/test/test_mutation.py::test_assign_spec_val`
- `glom/test/test_mutation.py::test_bad_assign_target`
- `glom/test/test_mutation.py::test_bad_delete_target`
- `glom/test/test_mutation.py::test_delete`
- `glom/test/test_mutation.py::test_delete_ignore_missing`
- `glom/test/test_mutation.py::test_sequence_assign`
- `glom/test/test_mutation.py::test_sequence_delete`
- `glom/test/test_mutation.py::test_star_broadcast`
- `glom/test/test_mutation.py::test_unregistered_assign`
- `glom/test/test_mutation.py::test_unregistered_delete`
- `glom/test/test_path_and_t.py::test_list_path_access`
- `glom/test/test_path_and_t.py::test_path`
- `glom/test/test_path_and_t.py::test_path_access_error_message`
- `glom/test/test_path_and_t.py::test_path_star`
- `glom/test/test_path_and_t.py::test_star_broadcast`
- `glom/test/test_path_and_t.py::test_star_warning`
- `glom/test/test_path_and_t.py::test_t_dict_key`
- `glom/test/test_path_and_t.py::test_t_subspec`
- `glom/test/test_reduction.py::test_flatten`
- `glom/test/test_reduction.py::test_flatten_func`
- `glom/test/test_reduction.py::test_fold`
- `glom/test/test_reduction.py::test_fold_bad_iter`
- `glom/test/test_reduction.py::test_merge`
- `glom/test/test_reduction.py::test_merge_func`
- `glom/test/test_reduction.py::test_merge_omd`
- `glom/test/test_reduction.py::test_sum_integers`
- `glom/test/test_reduction.py::test_sum_seqs`
- `glom/test/test_scope_vars.py::test_globals`
- `glom/test/test_scope_vars.py::test_let`
- `glom/test/test_scope_vars.py::test_max_skip`
- `glom/test/test_scope_vars.py::test_s_scope_assign`
- `glom/test/test_scope_vars.py::test_scoped_vars`
- `glom/test/test_scope_vars.py::test_vars`
- `glom/test/test_snippets.py::test_snippet`
- `glom/test/test_streaming.py::test_all`
- `glom/test/test_streaming.py::test_chunked`
- `glom/test/test_streaming.py::test_faulty_iterate`
- `glom/test/test_streaming.py::test_filter`
- `glom/test/test_streaming.py::test_first`
- `glom/test/test_streaming.py::test_iter`
- `glom/test/test_streaming.py::test_iter_composition`
- `glom/test/test_streaming.py::test_map`
- `glom/test/test_streaming.py::test_slice`
- `glom/test/test_streaming.py::test_split_flatten`
- `glom/test/test_streaming.py::test_unique`
- `glom/test/test_streaming.py::test_while`
- `glom/test/test_streaming.py::test_windowed`
- `glom/test/test_target_types.py::test_bypass_getitem`
- `glom/test/test_target_types.py::test_duck_register`
- `glom/test/test_target_types.py::test_exact_register`
- `glom/test/test_target_types.py::test_faulty_iterate`
- `glom/test/test_target_types.py::test_iter_set`
- `glom/test/test_target_types.py::test_iter_str`
- `glom/test/test_target_types.py::test_reregister_type`
- `glom/test/test_target_types.py::test_types_bare`
- `glom/test/test_target_types.py::test_types_leave_one_out`
- `glom/test/test_tutorial.py::test_tutorial`
