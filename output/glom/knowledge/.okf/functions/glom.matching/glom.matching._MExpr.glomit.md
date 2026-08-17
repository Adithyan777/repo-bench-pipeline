---
type: "python-function"
title: "glomit"
description: "Returns target if the comparison (lhs op rhs) is true after resolving M and _MSubspec placeholders"
resource: "/glom/matching.py#L441-L461"
tags: ["glom", "matching"]
sources: [{"resource": "/glom/matching.py#L441-L461"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "raises", "side_effects"]}]
status: "stable"
---
# `glom.matching._MExpr.glomit`

`glomit(self, target, scope)`

## Contract

- **inputs**: self; target; scope
- **outputs**: Returns target if the comparison (lhs op rhs) is true after resolving M and _MSubspec placeholders
- **raises**: MatchError
- **side_effects**: none
- **invariants**: If lhs or rhs is M, it is replaced with target; if _MSubspec, it is evaluated via glom; raises MatchError with operand details if comparison fails

## Callees
`glom.matching.MatchError`

## Tested by
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_match.py::test_basic`
- `glom/test/test_match.py::test_check_ported_tests`
- `glom/test/test_match.py::test_clamp`
- `glom/test/test_match.py::test_cruddy_json`
- `glom/test/test_match.py::test_defaults`
- `glom/test/test_match.py::test_examples`
- `glom/test/test_match.py::test_m_call_match`
- `glom/test/test_match.py::test_match_expressions`
- `glom/test/test_match.py::test_pattern_matching`
- `glom/test/test_match.py::test_sky`
- `glom/test/test_scope_vars.py::test_max_skip`
- `glom/test/test_snippets.py::test_snippet`
