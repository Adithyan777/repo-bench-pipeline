---
type: "python-function"
title: "repr1"
description: "a repr string, using builtin name map if x is a builtin"
resource: "/glom/core.py#L524-L528"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L524-L528"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["side_effects"]}]
status: "stable"
---
# `glom.core._BBRepr.repr1`

`repr1(self, x, level)`

## Contract

- **inputs**: self: a _BBRepr instance; x: the object to represent; level: the recursion level
- **outputs**: a repr string, using builtin name map if x is a builtin
- **raises**: none
- **side_effects**: none

## Tested by
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_glom_error_returns_one`
- `glom/test/generated/test_glom_streaming.py::test_chunked_repr`
- `glom/test/generated/test_glom_streaming.py::test_chunked_repr_with_fill`
- `glom/test/test_basic.py::test_bbrepr`
- `glom/test/test_basic.py::test_call_and_target`
- `glom/test/test_basic.py::test_coalesce`
- `glom/test/test_basic.py::test_invoke`
- `glom/test/test_basic.py::test_pipe`
- `glom/test/test_basic.py::test_python_native`
- `glom/test/test_basic.py::test_ref`
- `glom/test/test_basic.py::test_spec_and_recursion`
- `glom/test/test_basic.py::test_val`
- `glom/test/test_check.py::test_check_basic`
- `glom/test/test_check.py::test_check_multi`
- `glom/test/test_cli.py::test_main_basic`
- `glom/test/test_error.py::test_3_11_byte_code_caret`
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_error.py::test_branching_stack`
- `glom/test/test_error.py::test_coalesce_stack`
- `glom/test/test_error.py::test_glom_dev_debug`
- `glom/test/test_error.py::test_glom_error_double_stack`
- `glom/test/test_error.py::test_glom_error_stack`
- `glom/test/test_error.py::test_line_trace`
- `glom/test/test_error.py::test_long_target_repr`
- `glom/test/test_error.py::test_midway_branch`
- `glom/test/test_error.py::test_nesting_stack`
- `glom/test/test_error.py::test_pae_scope_printable`
- `glom/test/test_error.py::test_partially_failing_branch`
- `glom/test/test_error.py::test_regular_error_stack`
- `glom/test/test_error.py::test_unicode_stack`
- `glom/test/test_fill.py::test`
- `glom/test/test_match.py::test_and_or_reduction`
- `glom/test/test_match.py::test_basic`
- `glom/test/test_match.py::test_check_ported_tests`
- `glom/test/test_match.py::test_cruddy_json`
- `glom/test/test_match.py::test_double_wrapping`
- `glom/test/test_match.py::test_m_call_match`
- `glom/test/test_match.py::test_match_expressions`
- `glom/test/test_match.py::test_regex`
- `glom/test/test_match.py::test_reprs`
- `glom/test/test_match.py::test_sample`
- `glom/test/test_match.py::test_sets`
- `glom/test/test_match.py::test_shortcircuit`
- `glom/test/test_match.py::test_sky`
- `glom/test/test_match.py::test_switch`
- `glom/test/test_mutation.py::test_assign`
- `glom/test/test_mutation.py::test_bad_assign_target`
- `glom/test/test_mutation.py::test_bad_delete_target`
- `glom/test/test_mutation.py::test_delete`
- `glom/test/test_mutation.py::test_sequence_assign`
- `glom/test/test_mutation.py::test_sequence_delete`
- `glom/test/test_mutation.py::test_unregistered_assign`
- `glom/test/test_mutation.py::test_unregistered_delete`
- `glom/test/test_path_and_t.py::test_path_access_error_message`
- `glom/test/test_path_and_t.py::test_path_t_roundtrip`
- `glom/test/test_path_and_t.py::test_t_arithmetic_errors`
- `glom/test/test_path_and_t.py::test_t_arithmetic_reprs`
- `glom/test/test_path_and_t.py::test_t_picklability`
- `glom/test/test_reduction.py::test_flatten`
- `glom/test/test_reduction.py::test_fold`
- `glom/test/test_reduction.py::test_sum_integers`
- `glom/test/test_scope_vars.py::test_let`
- `glom/test/test_scope_vars.py::test_s_scope_assign`
- `glom/test/test_scope_vars.py::test_vars`
- `glom/test/test_spec.py::test_scope_spec`
- `glom/test/test_spec.py::test_spec`
- `glom/test/test_streaming.py::test_all`
- `glom/test/test_streaming.py::test_filter`
- `glom/test/test_streaming.py::test_first`
- `glom/test/test_streaming.py::test_map`
- `glom/test/test_streaming.py::test_slice`
- `glom/test/test_streaming.py::test_split_flatten`
- `glom/test/test_streaming.py::test_unique`
- `glom/test/test_streaming.py::test_windowed`
- `glom/test/test_target_types.py::test_types_bare`
