---
type: "python-function"
title: "glomit"
description: "run against the current target"
resource: "/glom/core.py#L1095-L1098"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L1095-L1098"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "link", "side_effects"]}]
status: "stable"
---
# `glom.core.Call.glomit`

`glomit(self, target, scope)`

> run against the current target

## Contract

- **inputs**: self: a Call instance; target: the object being glommed; scope: the current evaluation scope (mapping)
- **outputs**: the result of calling the evaluated func with evaluated args and kwargs against the current target
- **raises**: none
- **side_effects**: none

## Callees
[glom.core.arg_val](glom.core.arg_val.md)

## Tested by
- `glom/test/test_basic.py::test_call_and_target`
- `glom/test/test_basic.py::test_python_native`
- `glom/test/test_basic.py::test_spec_and_recursion`
- `glom/test/test_cli.py::test_main_python_full_spec_python_target`
- `glom/test/test_grouping.py::test_corner_cases`
- `glom/test/test_path_and_t.py::test_path_access_error_message`
- `glom/test/test_path_and_t.py::test_t_picklability`
- `glom/test/test_path_and_t.py::test_t_subspec`
- `glom/test/test_snippets.py::test_snippet`
- `glom/test/test_streaming.py::test_first`
- `glom/test/test_streaming.py::test_while`
