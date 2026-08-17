---
type: "python-function"
title: "mw_get_target"
description: "the result of calling next_ with parsed spec and target keyword arguments"
resource: "/glom/cli.py#L168-L212"
tags: ["cli", "glom"]
sources: [{"resource": "/glom/cli.py#L168-L212"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.cli.mw_get_target`

`mw_get_target(next_, posargs_, target_file, target_format, spec_file, spec_format)`

## Contract

- **inputs**: next_: the next middleware/callable to invoke; posargs_: list of positional string arguments (length 0-2); target_file: optional path string to target data source; target_format: string format of target data; spec_file: optional path string to spec definition; spec_format: string format of spec
- **outputs**: the result of calling next_ with parsed spec and target keyword arguments
- **raises**: UsageError, OSError (caught and re-raised as UsageError)
- **side_effects**: reads files specified by spec_file and target_file; reads sys.stdin if '-' or non-tty stdin

## Callees
`glom.cli._eval_python_full_spec`, [glom.cli.mw_handle_target](glom.cli.mw_handle_target.md)

## Tested by
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
