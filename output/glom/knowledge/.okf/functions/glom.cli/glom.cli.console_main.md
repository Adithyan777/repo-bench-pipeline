---
type: "python-function"
title: "console_main"
description: "none (calls sys.exit with main's return value or 0)"
resource: "/glom/cli.py#L106-L115"
tags: ["cli", "glom"]
sources: [{"resource": "/glom/cli.py#L106-L115"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.cli.console_main`

`console_main()`

## Contract

- **inputs**: none (reads sys.argv and GLOM_CLI_DEBUG environment variable implicitly)
- **outputs**: none (calls sys.exit with main's return value or 0)
- **raises**: SystemExit, Exception (re-raised after optional pdb.post_mortem)
- **side_effects**: reads GLOM_CLI_DEBUG env var; may print sys.argv; may call sys.exit; may invoke pdb.post_mortem on exception if debugging enabled

## Callees
[glom.cli.main](glom.cli.main.md)

## Tested by
- `glom/test/generated/test_glom_cli.py::TestConsoleMain::test_console_main_calls_sys_exit`
- `glom/test/generated/test_glom_cli.py::TestConsoleMain::test_console_main_debug_prints_argv`
- `glom/test/generated/test_glom_cli.py::TestConsoleMain::test_console_main_raises_without_debug`
- `glom/test/generated/test_glom_cli.py::TestConsoleMain::test_console_main_zero_on_none`
