---
type: "python-function"
title: "specfunc"
description: "Creates an :class:`Invoke` instance where the function is"
resource: "/glom/core.py#L1169-L1178"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L1169-L1178"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "side_effects"]}]
status: "stable"
---
# `glom.core.Invoke.specfunc`

`specfunc(cls, spec)`

> Creates an :class:`Invoke` instance where the function is
> indicated by a spec.
> 
> >>> spec = Invoke.specfunc('func').constants(5)
> >>> glom({'func': range}, (spec, list))
> [0, 1, 2, 3, 4]

## Contract

- **inputs**: cls: the Invoke class; spec: a spec indicating the function to call
- **outputs**: a new Invoke instance whose func is a Spec wrapping the given spec
- **raises**: none
- **side_effects**: none

## Callees
`glom.core.Spec`

## Tested by
- `glom/test/test_basic.py::test_invoke`
