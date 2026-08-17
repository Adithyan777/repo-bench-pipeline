---
type: "python-function"
title: "_trace"
description: "the result of evaluating spec against target"
resource: "/glom/core.py#L1021-L1043"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L1021-L1043"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.core.Inspect._trace`

`_trace(self, target, spec, scope)`

## Contract

- **inputs**: self: an Inspect instance; target: the object being glommed; spec: the current spec; scope: the current evaluation scope (mapping)
- **outputs**: the result of evaluating spec against target
- **raises**: none
- **side_effects**: may print trace info to stdout, may call breakpoint/post_mortem callables, may mutate scope[glom]

## Tested by
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_debug_and_inspect_with_closed_stdin`
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_debug_wraps_spec`
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_inspect_wraps_spec`
- `glom/test/test_basic.py::test_initial_integration`
- `glom/test/test_basic.py::test_inspect`
