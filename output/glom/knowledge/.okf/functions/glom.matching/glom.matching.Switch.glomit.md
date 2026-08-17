---
type: "python-function"
title: "glomit"
description: "Returns the result of the first valspec whose keyspec matches target, or evaluated default if no case matches and default is provided"
resource: "/glom/matching.py#L848-L857"
tags: ["glom", "matching"]
sources: [{"resource": "/glom/matching.py#L848-L857"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "link", "raises", "side_effects"]}]
status: "stable"
---
# `glom.matching.Switch.glomit`

`glomit(self, target, scope)`

## Contract

- **inputs**: self; target; scope
- **outputs**: Returns the result of the first valspec whose keyspec matches target, or evaluated default if no case matches and default is provided
- **raises**: MatchError
- **side_effects**: none
- **invariants**: Iterates cases in order; stops at first successful keyspec match; if no match and no default, raises MatchError

## Callees
[glom.core.arg_val](../glom.core/glom.core.arg_val.md), [glom.core.chain_child](../glom.core/glom.core.chain_child.md), `glom.matching.MatchError`

## Tested by
- `glom/test/test_error.py::test_branching_stack`
- `glom/test/test_error.py::test_midway_branch`
- `glom/test/test_match.py::test_switch`
- `glom/test/test_snippets.py::test_snippet`
