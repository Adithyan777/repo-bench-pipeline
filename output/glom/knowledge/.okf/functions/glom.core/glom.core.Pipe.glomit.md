---
type: "python-function"
title: "glomit"
description: "the result of evaluating self.steps as a tuple against target"
resource: "/glom/core.py#L1985-L1986"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L1985-L1986"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "link", "side_effects"]}]
status: "stable"
---
# `glom.core.Pipe.glomit`

`glomit(self, target, scope)`

## Contract

- **inputs**: self: a Pipe instance; target: the object being glommed; scope: the current evaluation scope (mapping)
- **outputs**: the result of evaluating self.steps as a tuple against target
- **raises**: none
- **side_effects**: none

## Callees
[glom.core._handle_tuple](glom.core._handle_tuple.md)

## Tested by
- `glom/test/test_basic.py::test_pipe`
- `glom/test/test_streaming.py::test_all`
- `glom/test/test_streaming.py::test_filter`
