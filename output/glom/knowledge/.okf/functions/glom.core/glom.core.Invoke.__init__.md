---
type: "python-function"
title: "__init__"
description: "none (initializes func, _args, _cur_kwargs)"
resource: "/glom/core.py#L1158-L1166"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L1158-L1166"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "raises"]}]
status: "stable"
---
# `glom.core.Invoke.__init__`

`__init__(self, func)`

## Contract

- **inputs**: self: a new Invoke instance; func: callable or Spec instance to invoke
- **outputs**: none (initializes func, _args, _cur_kwargs)
- **raises**: TypeError
- **side_effects**: mutates self by setting attributes func, _args, _cur_kwargs

## Callees
`glom.core._is_spec`

## Tested by
- `glom/test/test_basic.py::test_invoke`
