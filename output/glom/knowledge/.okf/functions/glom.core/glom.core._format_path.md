---
type: "python-function"
title: "_format_path"
description: "a formatted string representation of the path"
resource: "/glom/core.py#L760-L781"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L760-L781"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "callers", "link", "side_effects"]}]
status: "stable"
---
# `glom.core._format_path`

`_format_path(t_path)`

## Contract

- **inputs**: t_path: a TType operations path tuple
- **outputs**: a formatted string representation of the path
- **raises**: none
- **side_effects**: none

## Callers
`glom.core.Path.__repr__`, [glom.core._format_t](glom.core._format_t.md)

## Callees
[glom.core._format_t](glom.core._format_t.md)

## Tested by
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_glom_error_returns_one`
- `glom/test/test_basic.py::test_initial_integration`
- `glom/test/test_basic.py::test_python_native`
- `glom/test/test_basic.py::test_seq_getitem`
- `glom/test/test_basic.py::test_top_level_default`
- `glom/test/test_cli.py::test_main_basic`
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
- `glom/test/test_mutation.py::test_assign`
- `glom/test/test_mutation.py::test_assign_missing_unassignable`
- `glom/test/test_mutation.py::test_bad_assign_target`
- `glom/test/test_mutation.py::test_bad_delete_target`
- `glom/test/test_mutation.py::test_delete`
- `glom/test/test_mutation.py::test_sequence_assign`
- `glom/test/test_mutation.py::test_sequence_delete`
- `glom/test/test_mutation.py::test_unregistered_assign`
- `glom/test/test_mutation.py::test_unregistered_delete`
- `glom/test/test_path_and_t.py::test_path_access_error_message`
- `glom/test/test_path_and_t.py::test_path_t_roundtrip`
- `glom/test/test_path_and_t.py::test_s_magic`
- `glom/test/test_path_and_t.py::test_t_arithmetic_errors`
- `glom/test/test_reduction.py::test_fold_bad_iter`
- `glom/test/test_scope_vars.py::test_let`
- `glom/test/test_scope_vars.py::test_s_scope_assign`
- `glom/test/test_scope_vars.py::test_vars`
- `glom/test/test_streaming.py::test_faulty_iterate`
- `glom/test/test_target_types.py::test_bypass_getitem`
- `glom/test/test_target_types.py::test_faulty_iterate`
