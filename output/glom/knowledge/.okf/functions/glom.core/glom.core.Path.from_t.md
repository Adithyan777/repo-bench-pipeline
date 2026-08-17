---
type: "python-function"
title: "from_t"
description: "return the same path but starting from T"
resource: "/glom/core.py#L722-L729"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L722-L729"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.core.Path.from_t`

`from_t(self)`

> return the same path but starting from T

## Contract

- **inputs**: self: a Path instance
- **outputs**: a new Path starting from T if the original started from S, otherwise self
- **raises**: none
- **side_effects**: none

## Callees
`glom.core.Path`, `glom.core.TType`

## Tested by
- `glom/test/test_mutation.py::test_delete`
- `glom/test/test_mutation.py::test_s_assign`
- `glom/test/test_path_and_t.py::test_from_t_identity`
