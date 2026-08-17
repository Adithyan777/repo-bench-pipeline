---
type: "python-function"
title: "glomit"
description: "result of self._first.glomit(target, scope)"
resource: "/glom/streaming.py#L378-L379"
tags: ["glom", "streaming"]
sources: [{"resource": "/glom/streaming.py#L378-L379"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["side_effects"]}]
status: "stable"
---
# `glom.streaming.First.glomit`

`glomit(self, target, scope)`

## Contract

- **inputs**: self: First instance; target: object to glom; scope: glom scope dict
- **outputs**: result of self._first.glomit(target, scope)
- **raises**: none
- **side_effects**: none

## Tested by
- `glom/test/test_streaming.py::test_first`
