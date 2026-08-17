---
type: "python-function"
title: "verify"
description: "A convenience function a :class:`Match` instance which returns the"
resource: "/glom/matching.py#L158-L170"
tags: ["glom", "matching"]
sources: [{"resource": "/glom/matching.py#L158-L170"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.matching.Match.verify`

`verify(self, target)`

> A convenience function a :class:`Match` instance which returns the
> matched value when *target* matches, or raises a
> :exc:`MatchError` when it does not.
> 
> Args:
>   target: Target value or data structure to match against.
> 
> Raises:
>   glom.MatchError

## Contract

- **inputs**: self; target
- **outputs**: Returns the result of glom(target, self) if matching succeeds
- **raises**: MatchError
- **side_effects**: none
- **invariants**: Raises MatchError (via glom) when target does not match self

## Callees
[glom.core.glom](../glom.core/glom.core.glom.md)

## Tested by
- `glom/test/test_match.py::test_basic`
