---
type: "python-function"
title: "glomit"
description: "the result of glomming self.spec against target in AUTO mode"
resource: "/glom/core.py#L1884-L1886"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L1884-L1886"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.core.Auto.glomit`

`glomit(self, target, scope)`

## Contract

- **inputs**: self: an Auto instance; target: the object being glommed; scope: the current evaluation scope (mapping)
- **outputs**: the result of glomming self.spec against target in AUTO mode
- **raises**: none
- **side_effects**: mutates scope by setting scope[MODE] to AUTO

## Tested by
- `glom/test/test_basic.py::test_spec_and_recursion`
- `glom/test/test_fill.py::test`
- `glom/test/test_grouping.py::test_corner_cases`
- `glom/test/test_match.py::test_cruddy_json`
- `glom/test/test_match.py::test_nested_struct`
- `glom/test/test_match.py::test_sky`
- `glom/test/test_snippets.py::test_snippet`
