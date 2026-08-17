---
type: "python-function"
title: "glomit"
description: "Returns target if target equals self.key"
resource: "/glom/matching.py#L599-L602"
tags: ["glom", "matching"]
sources: [{"resource": "/glom/matching.py#L599-L602"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "raises", "side_effects"]}]
status: "stable"
---
# `glom.matching.Optional.glomit`

`glomit(self, target, scope)`

## Contract

- **inputs**: self; target; scope
- **outputs**: Returns target if target equals self.key
- **raises**: MatchError
- **side_effects**: none
- **invariants**: Raises MatchError with a message comparing target and self.key when they are not equal

## Callees
`glom.matching.MatchError`

## Tested by
- `glom/test/test_match.py::test_nested_struct`
- `glom/test/test_match.py::test_sample`
