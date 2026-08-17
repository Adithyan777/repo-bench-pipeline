---
type: "python-function"
title: "_unpack_stack"
description: "convert scope to [[scope, spec, target, error, [children]]]"
resource: "/glom/core.py#L189-L228"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L189-L228"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callers", "link", "side_effects"]}]
status: "stable"
---
# `glom.core._unpack_stack`

`_unpack_stack(scope, only_errors=True)`

> convert scope to [[scope, spec, target, error, [children]]]
> 
> this is a convenience method for printing stacks
> 
> only_errors=True means ignore branches which may still be hanging around
> which were not involved in the stack trace of the error
> 
> only_errors=False could be useful for debugger / introspection (similar
> to traceback.print_stack())

## Contract

- **inputs**: scope: the current evaluation scope; only_errors: whether to trim to error branch (default True)
- **outputs**: a list of [scope, spec, target, error, [children]] representing the evaluation stack
- **raises**: none
- **side_effects**: none

## Callers
[glom.core.format_oneline_trace](glom.core.format_oneline_trace.md), [glom.core.format_target_spec_trace](glom.core.format_target_spec_trace.md)

## Tested by
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_glom_error_returns_one`
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
- `glom/test/test_match.py::test_check_ported_tests`
- `glom/test/test_mutation.py::test_bad_assign_target`
- `glom/test/test_mutation.py::test_bad_delete_target`
- `glom/test/test_mutation.py::test_sequence_assign`
- `glom/test/test_mutation.py::test_sequence_delete`
- `glom/test/test_mutation.py::test_unregistered_assign`
- `glom/test/test_mutation.py::test_unregistered_delete`
- `glom/test/test_path_and_t.py::test_path_access_error_message`
- `glom/test/test_path_and_t.py::test_t_arithmetic_errors`
- `glom/test/test_spec.py::test_spec`
- `glom/test/test_target_types.py::test_types_bare`
