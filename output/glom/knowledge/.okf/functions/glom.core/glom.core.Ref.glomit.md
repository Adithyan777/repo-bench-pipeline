---
type: "python-function"
title: "glomit"
description: "the result of evaluating the referenced subspec against target"
resource: "/glom/core.py#L1339-L1346"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L1339-L1346"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.core.Ref.glomit`

`glomit(self, target, scope)`

## Contract

- **inputs**: self: a Ref instance; target: the object being glommed; scope: the current evaluation scope (mapping)
- **outputs**: the result of evaluating the referenced subspec against target
- **raises**: none
- **side_effects**: may mutate scope by storing subspec under scope[(Ref, self.name)]

## Tested by
- `glom/test/test_basic.py::test_ref`
- `glom/test/test_match.py::test_json_ref`
- `glom/test/test_match.py::test_nested_struct`
- `glom/test/test_match.py::test_pattern_matching`
- `glom/test/test_snippets.py::test_snippet`
