---
type: "python-function"
title: "glomit"
description: "Returns target if the child spec raises GlomError (i.e., does not match)"
resource: "/glom/matching.py#L363-L369"
tags: ["glom", "matching"]
sources: [{"resource": "/glom/matching.py#L363-L369"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "raises", "side_effects"]}]
status: "stable"
---
# `glom.matching.Not.glomit`

`glomit(self, target, scope)`

## Contract

- **inputs**: self; target; scope
- **outputs**: Returns target if the child spec raises GlomError (i.e., does not match)
- **raises**: GlomError
- **side_effects**: none
- **invariants**: If the child spec matches without exception, raises GlomError; if child raises GlomError, returns target unchanged

## Callees
`glom.core.GlomError`

## Tested by
- `glom/test/test_match.py::test_basic`
- `glom/test/test_match.py::test_shortcircuit`
