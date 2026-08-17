---
type: "python-function"
title: "_finalize"
description: "none"
resource: "/glom/core.py#L150-L167"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L150-L167"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.core.GlomError._finalize`

`_finalize(self, scope)`

## Contract

- **inputs**: self: a GlomError instance; scope: the current evaluation scope (mapping)
- **outputs**: none
- **raises**: none
- **side_effects**: mutates self by setting self._tb_lines and self._scope

## Tested by
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_glom_error_returns_one`
- `glom/test/test_basic.py::test_python_native`
- `glom/test/test_basic.py::test_ref`
- `glom/test/test_basic.py::test_seq_getitem`
- `glom/test/test_basic.py::test_top_level_default`
- `glom/test/test_check.py::test_check_basic`
- `glom/test/test_check.py::test_check_multi`
- `glom/test/test_cli.py::test_main_basic`
- `glom/test/test_error.py::test_3_11_byte_code_caret`
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_error.py::test_branching_stack`
- `glom/test/test_error.py::test_coalesce_stack`
- `glom/test/test_error.py::test_error`
- `glom/test/test_error.py::test_error_types`
- `glom/test/test_error.py::test_glom_dev_debug`
- `glom/test/test_error.py::test_glom_error_double_stack`
- `glom/test/test_error.py::test_glom_error_stack`
- `glom/test/test_error.py::test_good_error`
- `glom/test/test_error.py::test_long_target_repr`
- `glom/test/test_error.py::test_midway_branch`
- `glom/test/test_error.py::test_nesting_stack`
- `glom/test/test_error.py::test_pae_api`
- `glom/test/test_error.py::test_pae_scope_printable`
- `glom/test/test_error.py::test_partially_failing_branch`
- `glom/test/test_error.py::test_regular_error_stack`
- `glom/test/test_error.py::test_unicode_stack`
- `glom/test/test_grouping.py::test_corner_cases`
- `glom/test/test_grouping.py::test_limit`
- `glom/test/test_match.py::test_basic`
- `glom/test/test_match.py::test_check_ported_tests`
- `glom/test/test_match.py::test_cruddy_json`
- `glom/test/test_match.py::test_m_call_match`
- `glom/test/test_match.py::test_match_expressions`
- `glom/test/test_match.py::test_regex`
- `glom/test/test_match.py::test_sample`
- `glom/test/test_match.py::test_sets`
- `glom/test/test_match.py::test_shortcircuit`
- `glom/test/test_match.py::test_sky`
- `glom/test/test_match.py::test_switch`
- `glom/test/test_mutation.py::test_assign_missing_unassignable`
- `glom/test/test_mutation.py::test_bad_assign_target`
- `glom/test/test_mutation.py::test_bad_delete_target`
- `glom/test/test_mutation.py::test_delete`
- `glom/test/test_mutation.py::test_sequence_assign`
- `glom/test/test_mutation.py::test_sequence_delete`
- `glom/test/test_mutation.py::test_unregistered_assign`
- `glom/test/test_mutation.py::test_unregistered_delete`
- `glom/test/test_path_and_t.py::test_a_forbidden`
- `glom/test/test_path_and_t.py::test_path_access_error_message`
- `glom/test/test_path_and_t.py::test_s_magic`
- `glom/test/test_path_and_t.py::test_t_arithmetic_errors`
- `glom/test/test_reduction.py::test_flatten_func`
- `glom/test/test_reduction.py::test_fold_bad_iter`
- `glom/test/test_scope_vars.py::test_let`
- `glom/test/test_scope_vars.py::test_s_scope_assign`
- `glom/test/test_scope_vars.py::test_vars`
- `glom/test/test_spec.py::test_spec`
- `glom/test/test_streaming.py::test_faulty_iterate`
- `glom/test/test_target_types.py::test_bypass_getitem`
- `glom/test/test_target_types.py::test_duck_register`
- `glom/test/test_target_types.py::test_exact_register`
- `glom/test/test_target_types.py::test_faulty_iterate`
- `glom/test/test_target_types.py::test_iter_str`
- `glom/test/test_target_types.py::test_types_bare`
