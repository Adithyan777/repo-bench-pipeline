---
type: "python-function"
title: "format_target_spec_trace"
description: "unpack a scope into a multi-line but short summary"
resource: "/glom/core.py#L242-L279"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L242-L279"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "callers", "link", "side_effects"]}]
status: "stable"
---
# `glom.core.format_target_spec_trace`

`format_target_spec_trace(scope, root_error, width=TRACE_WIDTH, depth=0, prev_target=_MISSING, last_branch=True)`

> unpack a scope into a multi-line but short summary

## Contract

- **inputs**: scope: a scope object to unpack into a trace summary; root_error: the root error to distinguish from nested errors; width: maximum line width for trace formatting (defaults to TRACE_WIDTH); depth: current recursion depth for indentation (defaults to 0); prev_target: previous target for deduplication (defaults to _MISSING); last_branch: whether this is the last branch at the current depth (defaults to True)
- **outputs**: A multi-line string summarizing the scope stack with formatted targets, specs, branches, and errors.
- **raises**: none
- **side_effects**: none
- **invariants**: If depth > 0, the first segment line has a backslash at position depth+1, and if not last_branch or last_line_error is True, the last segment line has an X at position depth+1.

## Callers
[glom.core.GlomError.__str__](glom.core.GlomError.__str__.md), [glom.core.format_target_spec_trace](glom.core.format_target_spec_trace.md)

## Callees
[glom.core._unpack_stack](glom.core._unpack_stack.md), [glom.core.format_target_spec_trace](glom.core.format_target_spec_trace.md)

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
