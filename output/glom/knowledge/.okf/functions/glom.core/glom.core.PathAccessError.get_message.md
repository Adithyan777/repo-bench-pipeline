---
type: "python-function"
title: "get_message"
description: "a formatted error message string describing the access failure"
resource: "/glom/core.py#L347-L353"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L347-L353"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["side_effects"]}]
status: "stable"
---
# `glom.core.PathAccessError.get_message`

`get_message(self)`

## Contract

- **inputs**: self: a PathAccessError instance
- **outputs**: a formatted error message string describing the access failure
- **raises**: none
- **side_effects**: none

## Tested by
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_glom_error_returns_one`
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
- `glom/test/test_mutation.py::test_assign_missing_unassignable`
- `glom/test/test_mutation.py::test_bad_assign_target`
- `glom/test/test_mutation.py::test_delete`
- `glom/test/test_path_and_t.py::test_path_access_error_message`
- `glom/test/test_path_and_t.py::test_s_magic`
- `glom/test/test_path_and_t.py::test_t_arithmetic_errors`
- `glom/test/test_scope_vars.py::test_vars`
- `glom/test/test_target_types.py::test_bypass_getitem`
