---
type: "python-function"
title: "glomit"
description: "Returns target if the glom of target with self.spec evaluates to a truthy value"
resource: "/glom/matching.py#L417-L421"
tags: ["glom", "matching"]
sources: [{"resource": "/glom/matching.py#L417-L421"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "raises", "side_effects"]}]
status: "stable"
---
# `glom.matching._MSubspec.glomit`

`glomit(self, target, scope)`

## Contract

- **inputs**: self; target; scope
- **outputs**: Returns target if the glom of target with self.spec evaluates to a truthy value
- **raises**: MatchError
- **side_effects**: none
- **invariants**: Raises MatchError showing spec and falsy result if the subspec glom result is not truthy

## Callees
`glom.matching.MatchError`

## Tested by
- `glom/test/test_match.py::test_check_ported_tests`
- `glom/test/test_match.py::test_m_call_match`
