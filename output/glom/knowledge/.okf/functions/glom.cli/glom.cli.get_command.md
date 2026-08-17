---
type: "python-function"
title: "get_command"
description: "a configured Command object for the glom CLI with positional args and various flags added"
resource: "/glom/cli.py#L80-L98"
tags: ["cli", "glom"]
sources: [{"resource": "/glom/cli.py#L80-L98"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callers", "link", "side_effects"]}]
status: "stable"
---
# `glom.cli.get_command`

`get_command()`

## Contract

- **inputs**: none
- **outputs**: a configured Command object for the glom CLI with positional args and various flags added
- **raises**: none
- **side_effects**: none

## Callers
[glom.cli.main](glom.cli.main.md)

## Tested by
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
