---
type: "python-function"
title: "glomit"
description: "Returns target if target is truthy"
resource: "/glom/matching.py#L561-L564"
tags: ["glom", "matching"]
sources: [{"resource": "/glom/matching.py#L561-L564"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "raises", "side_effects"]}]
status: "stable"
---
# `glom.matching._MType.glomit`

`glomit(self, target, spec)`

## Contract

- **inputs**: self; target; spec
- **outputs**: Returns target if target is truthy
- **raises**: MatchError
- **side_effects**: none
- **invariants**: Raises MatchError with target repr if target is falsy

## Callees
`glom.matching.MatchError`

## Tested by
- `glom/test/test_match.py::test_basic`
- `glom/test/test_match.py::test_shortcircuit`
