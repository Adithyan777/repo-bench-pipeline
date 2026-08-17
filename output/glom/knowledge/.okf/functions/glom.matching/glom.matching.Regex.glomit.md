---
type: "python-function"
title: "glomit"
description: "Returns target if target type is in _RE_TYPES and matches the compiled regex pattern"
resource: "/glom/matching.py#L234-L242"
tags: ["glom", "matching"]
sources: [{"resource": "/glom/matching.py#L234-L242"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "raises"]}]
status: "stable"
---
# `glom.matching.Regex.glomit`

`glomit(self, target, scope)`

## Contract

- **inputs**: self; target; scope
- **outputs**: Returns target if target type is in _RE_TYPES and matches the compiled regex pattern
- **raises**: MatchError
- **side_effects**: Updates scope with match.groupdict() on successful match
- **invariants**: If target type is invalid or regex does not match, raises MatchError; on success, scope contains the named group dictionary from the match

## Callees
`glom.matching.MatchError`

## Tested by
- `glom/test/test_match.py::test_nested_struct`
- `glom/test/test_match.py::test_regex`
