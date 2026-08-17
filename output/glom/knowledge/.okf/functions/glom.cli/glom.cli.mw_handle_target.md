---
type: "python-function"
title: "mw_handle_target"
description: "Handles reading in a file specified in cli command."
resource: "/glom/cli.py#L118-L164"
tags: ["cli", "glom"]
sources: [{"resource": "/glom/cli.py#L118-L164"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callers", "link", "raises", "side_effects"]}]
status: "stable"
---
# `glom.cli.mw_handle_target`

`mw_handle_target(target_text, target_format)`

> Handles reading in a file specified in cli command.
> 
> Args:
>     target_text (str): The target data to load, as text
>     target_format (str): Valid formats include `json`, `toml`, and `yml`/`yaml`
> Returns:
>     The content of the file that you specified
> Raises:
>     CommandLineError: Issue with file format or appropriate file reading package not installed.

## Contract

- **inputs**: target_text: string containing the raw target data; target_format: string indicating format (json, yaml, yml, toml, python)
- **outputs**: the parsed data structure loaded from target_text
- **raises**: UsageError
- **side_effects**: none

## Callers
[glom.cli.mw_get_target](glom.cli.mw_get_target.md)

## Tested by
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
