---
type: "python-function"
title: "_precedence"
description: "in a dict spec, target-keys may match many"
resource: "/glom/matching.py#L657-L674"
tags: ["glom", "matching"]
sources: [{"resource": "/glom/matching.py#L657-L674"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "callers", "link", "side_effects"]}]
status: "stable"
---
# `glom.matching._precedence`

`_precedence(match)`

> in a dict spec, target-keys may match many
> spec-keys (e.g. 1 will match int, M > 0, and 1);
> therefore we need a precedence for which order to try
> keys in; higher = later

## Contract

- **inputs**: match (a spec key, possibly Required or Optional wrapper)
- **outputs**: Returns an integer precedence (0, 1, or 2) for dict key matching order
- **raises**: none
- **side_effects**: none
- **invariants**: Required/Optional wrappers are unwrapped to their key; empty tuple/frozenset returns 0; types return 2; objects with glomit return 1; everything else returns 0

## Callers
`glom.matching.Optional.__init__`, `glom.matching.Required.__init__`, [glom.matching._handle_dict](glom.matching._handle_dict.md), [glom.matching._precedence](glom.matching._precedence.md)

## Callees
[glom.matching._precedence](glom.matching._precedence.md)

## Tested by
- `glom/test/test_match.py::test_basic`
- `glom/test/test_match.py::test_check_ported_tests`
- `glom/test/test_match.py::test_cruddy_json`
- `glom/test/test_match.py::test_double_wrapping`
- `glom/test/test_match.py::test_json_ref`
- `glom/test/test_match.py::test_nested_dict`
- `glom/test/test_match.py::test_nested_struct`
- `glom/test/test_match.py::test_precedence`
- `glom/test/test_match.py::test_sample`
- `glom/test/test_snippets.py::test_snippet`
