---
type: "python-function"
title: "matches"
description: "A convenience method on a :class:`Match` instance, returns"
resource: "/glom/matching.py#L172-L186"
tags: ["glom", "matching"]
sources: [{"resource": "/glom/matching.py#L172-L186"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "link", "side_effects"]}]
status: "stable"
---
# `glom.matching.Match.matches`

`matches(self, target)`

> A convenience method on a :class:`Match` instance, returns
> ``True`` if the *target* matches, ``False`` if not.
> 
> >>> Match(int).matches(-1.0)
> False
> 
> Args:
>    target: Target value or data structure to match against.

## Contract

- **inputs**: self; target
- **outputs**: Returns True if glom(target, self) succeeds without GlomError, else False
- **raises**: none
- **side_effects**: none
- **invariants**: Always returns a boolean; never raises exceptions to the caller

## Callees
[glom.core.glom](../glom.core/glom.core.glom.md)

## Tested by
- `glom/test/test_match.py::test_basic`
