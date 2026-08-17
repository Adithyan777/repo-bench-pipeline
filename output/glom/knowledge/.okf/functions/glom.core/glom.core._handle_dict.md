---
type: "python-function"
title: "_handle_dict"
description: "a new dict (or spec type) with evaluated keys and values"
resource: "/glom/core.py#L1924-L1933"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L1924-L1933"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callers", "link", "side_effects"]}]
status: "stable"
---
# `glom.core._handle_dict`

`_handle_dict(target, spec, scope)`

## Contract

- **inputs**: target: the object being glommed; spec: a dict specification; scope: the current evaluation scope (mapping)
- **outputs**: a new dict (or spec type) with evaluated keys and values
- **raises**: none
- **side_effects**: none

## Callers
[glom.core.AUTO](glom.core.AUTO.md)

## Tested by
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_glom_dict_result`
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_sort_keys`
- `glom/test/test_basic.py::test_beyond_access`
- `glom/test/test_basic.py::test_initial_integration`
- `glom/test/test_basic.py::test_inspect`
- `glom/test/test_basic.py::test_invoke`
- `glom/test/test_basic.py::test_python_native`
- `glom/test/test_basic.py::test_ref`
- `glom/test/test_basic.py::test_skip`
- `glom/test/test_basic.py::test_spec_and_recursion`
- `glom/test/test_basic.py::test_val`
- `glom/test/test_check.py::test_check_basic`
- `glom/test/test_cli.py::test_cli_spec_argv_target_stdin_basic`
- `glom/test/test_cli.py::test_cli_spec_target_argv_basic`
- `glom/test/test_cli.py::test_cli_spec_target_files_basic`
- `glom/test/test_error.py::test_glom_error_double_stack`
- `glom/test/test_error.py::test_glom_error_stack`
- `glom/test/test_error.py::test_line_trace`
- `glom/test/test_error.py::test_regular_error_stack`
- `glom/test/test_match.py::test_check_ported_tests`
- `glom/test/test_path_and_t.py::test_empty_path_access`
- `glom/test/test_path_and_t.py::test_t_dict_key`
- `glom/test/test_scope_vars.py::test_let`
- `glom/test/test_scope_vars.py::test_s_scope_assign`
- `glom/test/test_snippets.py::test_snippet`
- `glom/test/test_target_types.py::test_faulty_iterate`
- `glom/test/test_target_types.py::test_iter_str`
- `glom/test/test_target_types.py::test_types_bare`
