---
type: "python-function"
title: "main"
description: "int exit code (0 if cmd.run returns None or falsy)"
resource: "/glom/cli.py#L101-L103"
tags: ["cli", "glom"]
sources: [{"resource": "/glom/cli.py#L101-L103"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "callers", "link"]}]
status: "stable"
---
# `glom.cli.main`

`main(argv)`

## Contract

- **inputs**: argv: list of command-line argument strings
- **outputs**: int exit code (0 if cmd.run returns None or falsy)
- **raises**: none
- **side_effects**: none beyond delegating to cmd.run

## Callers
[glom.cli.console_main](glom.cli.console_main.md)

## Callees
[glom.cli.get_command](glom.cli.get_command.md)

## Tested by
- `glom/test/test_cli.py::test_main_basic`
- `glom/test/test_cli.py::test_main_python_full_spec_python_target`
- `glom/test/test_cli.py::test_main_toml_target`
- `glom/test/test_cli.py::test_main_yaml_target`
