---
type: "python-function"
title: "glomit"
description: "the result of glomming target with self.wrapped under tracing"
resource: "/glom/core.py#L1014-L1019"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L1014-L1019"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.core.Inspect.glomit`

`glomit(self, target, scope)`

## Contract

- **inputs**: self: an Inspect instance; target: the object being glommed; scope: the current evaluation scope (mapping)
- **outputs**: the result of glomming target with self.wrapped under tracing
- **raises**: none
- **side_effects**: mutates scope by stashing real handler under scope[Inspect] and replacing scope[glom] with self._trace

## Tested by
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_debug_and_inspect_with_closed_stdin`
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_debug_wraps_spec`
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_inspect_wraps_spec`
- `glom/test/test_basic.py::test_initial_integration`
- `glom/test/test_basic.py::test_inspect`
