---
type: "python-function"
title: "_handle_dict"
description: "Returns a dict result built by matching target keys against spec keys, with optional defaults and required key enforcement"
resource: "/glom/matching.py#L677-L711"
tags: ["glom", "matching"]
sources: [{"resource": "/glom/matching.py#L677-L711"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "callers", "link", "raises", "side_effects"]}]
status: "stable"
---
# `glom.matching._handle_dict`

`_handle_dict(target, spec, scope)`

## Contract

- **inputs**: target; spec; scope
- **outputs**: Returns a dict result built by matching target keys against spec keys, with optional defaults and required key enforcement
- **raises**: TypeMatchError, MatchError
- **side_effects**: none
- **invariants**: Target must be a dict; Required keys are unwrapped; Optional keys with defaults pre-populate result; missing required keys raise MatchError; unmatched target keys raise MatchError

## Callers
[glom.matching._glom_match](glom.matching._glom_match.md)

## Callees
[glom.core.arg_val](../glom.core/glom.core.arg_val.md), [glom.core.chain_child](../glom.core/glom.core.chain_child.md), `glom.matching.MatchError`, `glom.matching.TypeMatchError`, [glom.matching._precedence](glom.matching._precedence.md)

## Tested by
- `glom/test/test_match.py::test_basic`
- `glom/test/test_match.py::test_check_ported_tests`
- `glom/test/test_match.py::test_cruddy_json`
- `glom/test/test_match.py::test_json_ref`
- `glom/test/test_match.py::test_nested_dict`
- `glom/test/test_match.py::test_nested_struct`
- `glom/test/test_match.py::test_precedence`
- `glom/test/test_match.py::test_sample`
- `glom/test/test_match.py::test_sets`
- `glom/test/test_snippets.py::test_snippet`
