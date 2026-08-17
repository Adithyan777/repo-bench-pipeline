---
type: "python-function"
title: "_compile_code"
description: "the value bound to name in the execution environment after running code_str"
resource: "/glom/cli.py#L233-L241"
tags: ["cli", "glom"]
sources: [{"resource": "/glom/cli.py#L233-L241"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.cli._compile_code`

`_compile_code(code_str, name, env=None, verbose=False)`

## Contract

- **inputs**: code_str: a string of Python code to compile and execute; name: the key to look up in the environment after execution; env: optional dict to use as execution namespace, defaults to empty dict if None; verbose: optional bool to print code_str before execution
- **outputs**: the value bound to name in the execution environment after running code_str
- **raises**: SyntaxError, KeyError, NameError
- **side_effects**: if verbose is True, prints code_str to stdout; mutates env by executing code in it

## Callers
`glom.cli._eval_python_full_spec`

## Tested by
- `glom/test/test_cli.py::test_main_python_full_spec_python_target`
