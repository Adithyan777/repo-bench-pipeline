---
type: "python-function"
title: "glom_cli"
description: "Command-line interface to the glom library, providing nested data"
resource: "/glom/cli.py#L52-L77"
tags: ["cli", "glom"]
sources: [{"resource": "/glom/cli.py#L52-L77"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.cli.glom_cli`

`glom_cli(target, spec, indent, debug, inspect, scalar)`

> Command-line interface to the glom library, providing nested data
> access and data restructuring with the power of Python.

## Contract

- **inputs**: target: the data to run glom on; spec: the glom spec to evaluate; indent: int for JSON indentation spaces, 0 disables pretty-printing; debug: bool to enable post-mortem debugging; inspect: bool to enable interactive inspection; scalar: bool to output single values without JSON formatting
- **outputs**: returns 1 on GlomError, otherwise None (implicitly) after printing result
- **raises**: GlomError (caught and printed, returning 1)
- **side_effects**: prints error message to stdout on GlomError; prints formatted result or scalar value to stdout; may wrap spec in Inspect

## Tested by
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
- `glom/test/test_cli.py::test_cli_blank`
- `glom/test/test_cli.py::test_cli_scalar`
- `glom/test/test_cli.py::test_cli_spec_argv_target_stdin_basic`
- `glom/test/test_cli.py::test_cli_spec_target_argv_basic`
- `glom/test/test_cli.py::test_cli_spec_target_files_basic`
- `glom/test/test_cli.py::test_main_basic`
- `glom/test/test_cli.py::test_main_python_full_spec_python_target`
- `glom/test/test_cli.py::test_main_toml_target`
- `glom/test/test_cli.py::test_main_yaml_target`
