---
type: "python-function"
title: "__init__"
description: "none (initializes self.path_t)"
resource: "/glom/core.py#L613-L637"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L613-L637"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "raises"]}]
status: "stable"
---
# `glom.core.Path.__init__`

`__init__(self, *path_parts)`

## Contract

- **inputs**: self: a new Path instance; *path_parts: strings, Path instances, or TType path segments
- **outputs**: none (initializes self.path_t)
- **raises**: ValueError
- **side_effects**: mutates self by setting self.path_t

## Callees
`glom.core._t_child`

## Tested by
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_basic_glom`
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_glom_error_returns_one`
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_scalar_output`
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_sort_keys`
- `glom/test/test_basic.py::test_beyond_access`
- `glom/test/test_basic.py::test_coalesce`
- `glom/test/test_basic.py::test_initial_integration`
- `glom/test/test_basic.py::test_inspect`
- `glom/test/test_basic.py::test_invoke`
- `glom/test/test_basic.py::test_list_item_lift_and_access`
- `glom/test/test_basic.py::test_pipe`
- `glom/test/test_basic.py::test_python_native`
- `glom/test/test_basic.py::test_ref`
- `glom/test/test_basic.py::test_seq_getitem`
- `glom/test/test_basic.py::test_skip`
- `glom/test/test_basic.py::test_top_level_default`
- `glom/test/test_check.py::test_check_basic`
- `glom/test/test_cli.py::test_cli_blank`
- `glom/test/test_cli.py::test_main_basic`
- `glom/test/test_cli.py::test_main_yaml_target`
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_error.py::test_branching_stack`
- `glom/test/test_error.py::test_coalesce_stack`
- `glom/test/test_error.py::test_error`
- `glom/test/test_error.py::test_glom_dev_debug`
- `glom/test/test_error.py::test_glom_error_double_stack`
- `glom/test/test_error.py::test_glom_error_stack`
- `glom/test/test_error.py::test_good_error`
- `glom/test/test_error.py::test_long_target_repr`
- `glom/test/test_error.py::test_midway_branch`
- `glom/test/test_error.py::test_nesting_stack`
- `glom/test/test_error.py::test_pae_api`
- `glom/test/test_error.py::test_pae_fallback_for_non_path`
- `glom/test/test_error.py::test_pae_scope_printable`
- `glom/test/test_error.py::test_partially_failing_branch`
- `glom/test/test_error.py::test_unicode_stack`
- `glom/test/test_fill.py::test`
- `glom/test/test_grouping.py::test_corner_cases`
- `glom/test/test_match.py::test_switch`
- `glom/test/test_mutation.py::test_assign`
- `glom/test/test_mutation.py::test_assign_missing_dict`
- `glom/test/test_mutation.py::test_assign_missing_object`
- `glom/test/test_mutation.py::test_assign_missing_signature`
- `glom/test/test_mutation.py::test_assign_missing_unassignable`
- `glom/test/test_mutation.py::test_assign_missing_with_extant_keys`
- `glom/test/test_mutation.py::test_assign_recursive`
- `glom/test/test_mutation.py::test_assign_spec_val`
- `glom/test/test_mutation.py::test_bad_assign_target`
- `glom/test/test_mutation.py::test_bad_delete_target`
- `glom/test/test_mutation.py::test_delete`
- `glom/test/test_mutation.py::test_delete_ignore_missing`
- `glom/test/test_mutation.py::test_invalid_assign_op_target`
- `glom/test/test_mutation.py::test_invalid_delete_op_target`
- `glom/test/test_mutation.py::test_s_assign`
- `glom/test/test_mutation.py::test_sequence_assign`
- `glom/test/test_mutation.py::test_sequence_delete`
- `glom/test/test_mutation.py::test_star_broadcast`
- `glom/test/test_mutation.py::test_unregistered_assign`
- `glom/test/test_mutation.py::test_unregistered_delete`
- `glom/test/test_path_and_t.py::test_empty_path_access`
- `glom/test/test_path_and_t.py::test_from_t_identity`
- `glom/test/test_path_and_t.py::test_list_path_access`
- `glom/test/test_path_and_t.py::test_path`
- `glom/test/test_path_and_t.py::test_path_access_error_message`
- `glom/test/test_path_and_t.py::test_path_cache`
- `glom/test/test_path_and_t.py::test_path_eq`
- `glom/test/test_path_and_t.py::test_path_eq_t`
- `glom/test/test_path_and_t.py::test_path_getitem`
- `glom/test/test_path_and_t.py::test_path_items`
- `glom/test/test_path_and_t.py::test_path_len`
- `glom/test/test_path_and_t.py::test_path_slices`
- `glom/test/test_path_and_t.py::test_path_star`
- `glom/test/test_path_and_t.py::test_path_t_roundtrip`
- `glom/test/test_path_and_t.py::test_path_values`
- `glom/test/test_path_and_t.py::test_s_magic`
- `glom/test/test_path_and_t.py::test_star_broadcast`
- `glom/test/test_path_and_t.py::test_star_warning`
- `glom/test/test_path_and_t.py::test_startswith`
- `glom/test/test_path_and_t.py::test_t_arithmetic_errors`
- `glom/test/test_path_and_t.py::test_t_subspec`
- `glom/test/test_reduction.py::test_flatten_func`
- `glom/test/test_reduction.py::test_fold_bad_iter`
- `glom/test/test_reduction.py::test_sum_integers`
- `glom/test/test_scope_vars.py::test_let`
- `glom/test/test_scope_vars.py::test_s_scope_assign`
- `glom/test/test_scope_vars.py::test_vars`
- `glom/test/test_snippets.py::test_snippet`
- `glom/test/test_streaming.py::test_faulty_iterate`
- `glom/test/test_target_types.py::test_bypass_getitem`
- `glom/test/test_target_types.py::test_faulty_iterate`
- `glom/test/test_target_types.py::test_types_bare`
