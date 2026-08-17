---
type: "python-function"
title: "_glom_match"
description: "Returns target or transformed target if spec matches target according to type/dict/list/set/frozenset/tuple/callable/equality rules"
resource: "/glom/matching.py#L714-L761"
tags: ["glom", "matching"]
sources: [{"resource": "/glom/matching.py#L714-L761"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "link", "raises", "side_effects"]}]
status: "stable"
---
# `glom.matching._glom_match`

`_glom_match(target, spec, scope)`

## Contract

- **inputs**: target; spec; scope
- **outputs**: Returns target or transformed target if spec matches target according to type/dict/list/set/frozenset/tuple/callable/equality rules
- **raises**: TypeMatchError, MatchError
- **side_effects**: none
- **invariants**: For dict specs delegates to _handle_dict; for list/set/frozenset returns same container type (or list); for tuple returns tuple; for callable returns target only if callable(target) is truthy; for type checks isinstance; otherwise uses ==

## Callees
`glom.matching.MatchError`, `glom.matching.TypeMatchError`, [glom.matching._handle_dict](glom.matching._handle_dict.md)

## Tested by
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_error.py::test_branching_stack`
- `glom/test/test_error.py::test_midway_branch`
- `glom/test/test_match.py::test_basic`
- `glom/test/test_match.py::test_check_ported_tests`
- `glom/test/test_match.py::test_cruddy_json`
- `glom/test/test_match.py::test_defaults`
- `glom/test/test_match.py::test_json_ref`
- `glom/test/test_match.py::test_match_default`
- `glom/test/test_match.py::test_nested_dict`
- `glom/test/test_match.py::test_nested_struct`
- `glom/test/test_match.py::test_pattern_matching`
- `glom/test/test_match.py::test_precedence`
- `glom/test/test_match.py::test_sample`
- `glom/test/test_match.py::test_sets`
- `glom/test/test_match.py::test_sky`
- `glom/test/test_match.py::test_ternary`
- `glom/test/test_snippets.py::test_snippet`
