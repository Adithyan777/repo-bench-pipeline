---
type: "python-module"
title: "glom.cli"
description: "Provides a command-line interface to the glom library, enabling nested data access and restructuring using Python-powered specs directly from the shell. It supports reading targets and specs from file"
resource: "/glom/cli.py#L1"
tags: ["cli", "glom"]
sources: [{"resource": "/glom/cli.py#L1"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# Module `glom.cli`

## Purpose
Provides a command-line interface to the glom library, enabling nested data access and restructuring using Python-powered specs directly from the shell. It supports reading targets and specs from files or stdin in various formats (JSON, YAML, TOML, Python), with options for pretty-printing, interactive debugging, and data inspection.

## API

- [glom.cli._compile_code](../functions/glom.cli/glom.cli._compile_code.md) — `_compile_code(code_str, name, env=None, verbose=False)`
- [glom.cli._from_glom_import_star](../functions/glom.cli/glom.cli._from_glom_import_star.md) — `_from_glom_import_star()`
- [glom.cli.console_main](../functions/glom.cli/glom.cli.console_main.md) — `console_main()`
- [glom.cli.get_command](../functions/glom.cli/glom.cli.get_command.md) — `get_command()`
- [glom.cli.glom_cli](../functions/glom.cli/glom.cli.glom_cli.md) — `glom_cli(target, spec, indent, debug, inspect, scalar)`
- [glom.cli.main](../functions/glom.cli/glom.cli.main.md) — `main(argv)`
- [glom.cli.mw_get_target](../functions/glom.cli/glom.cli.mw_get_target.md) — `mw_get_target(next_, posargs_, target_file, target_format, spec_file, spec_format)`
- [glom.cli.mw_handle_target](../functions/glom.cli/glom.cli.mw_handle_target.md) — `mw_handle_target(target_text, target_format)`

## Internal helpers

- `_eval_python_full_spec(py_text)`

## Calls
`glom.cli._compile_code`, `glom.cli._eval_python_full_spec`, `glom.cli._from_glom_import_star`, `glom.cli.get_command`, `glom.cli.main`, `glom.cli.mw_handle_target`

## Tested by
- `glom/test/generated/test_glom_cli.py::TestConsoleMain::test_console_main_calls_sys_exit`
- `glom/test/generated/test_glom_cli.py::TestConsoleMain::test_console_main_debug_prints_argv`
- `glom/test/generated/test_glom_cli.py::TestConsoleMain::test_console_main_raises_without_debug`
- `glom/test/generated/test_glom_cli.py::TestConsoleMain::test_console_main_zero_on_none`
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
- `glom/test/generated/test_glom_cli.py::TestMwHandleTarget::test_empty_string_returns_empty_dict`
- `glom/test/generated/test_glom_cli.py::TestMwHandleTarget::test_invalid_format_raises`
- `glom/test/generated/test_glom_cli.py::TestMwHandleTarget::test_invalid_json_raises`
- `glom/test/generated/test_glom_cli.py::TestMwHandleTarget::test_invalid_python_raises`
- `glom/test/generated/test_glom_cli.py::TestMwHandleTarget::test_invalid_yaml_raises`
- `glom/test/generated/test_glom_cli.py::TestMwHandleTarget::test_json_format`
- `glom/test/generated/test_glom_cli.py::TestMwHandleTarget::test_none_returns_empty_dict`
- `glom/test/generated/test_glom_cli.py::TestMwHandleTarget::test_python_format`
- `glom/test/generated/test_glom_cli.py::TestMwHandleTarget::test_python_format_list`
- `glom/test/generated/test_glom_cli.py::TestMwHandleTarget::test_toml_format`
- `glom/test/generated/test_glom_cli.py::TestMwHandleTarget::test_yaml_format`
- `glom/test/generated/test_glom_cli.py::TestMwHandleTarget::test_yml_format`
- `glom/test/test_check.py::test_check_signature`
- `glom/test/test_cli.py::test_cli_blank`
- `glom/test/test_cli.py::test_cli_scalar`
- `glom/test/test_cli.py::test_cli_spec_argv_target_stdin_basic`
- `glom/test/test_cli.py::test_cli_spec_target_argv_basic`
- `glom/test/test_cli.py::test_cli_spec_target_files_basic`
- `glom/test/test_cli.py::test_main_basic`
- `glom/test/test_cli.py::test_main_python_full_spec_python_target`
- `glom/test/test_cli.py::test_main_toml_target`
- `glom/test/test_cli.py::test_main_yaml_target`
- `glom/test/test_cli.py::test_usage_errors`
