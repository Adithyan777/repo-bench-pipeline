---
type: "python-function"
title: "__init__"
description: "none (initializes self.func, self.args, self.kwargs)"
resource: "/glom/core.py#L1083-L1093"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L1083-L1093"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["raises"]}]
status: "stable"
---
# `glom.core.Call.__init__`

`__init__(self, func=None, args=None, kwargs=None)`

## Contract

- **inputs**: self: a new Call instance; func: callable or Spec/TType expression to call (defaults to T); args: positional arguments tuple (defaults to ()); kwargs: keyword arguments dict (defaults to {})
- **outputs**: none (initializes self.func, self.args, self.kwargs)
- **raises**: TypeError
- **side_effects**: mutates self by setting attributes func, args, kwargs

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
