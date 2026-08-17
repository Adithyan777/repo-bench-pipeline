---
type: "python-function"
title: "glom"
description: "the result of glomming target with self.spec"
resource: "/glom/core.py#L811-L816"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L811-L816"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["side_effects"]}]
status: "stable"
---
# `glom.core.Spec.glom`

`glom(self, target, **kw)`

## Contract

- **inputs**: self: a Spec instance; target: the object to glom; **kw: keyword arguments including optional 'scope'
- **outputs**: the result of glomming target with self.spec
- **raises**: none
- **side_effects**: none

## Tested by
- `glom/test/test_spec.py::test_scope_spec`
- `glom/test/test_spec.py::test_spec`
- `glom/test/test_streaming.py::test_first`
