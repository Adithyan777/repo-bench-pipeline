---
type: "python-function"
title: "glomit"
description: "a ScopeVars instance constructed from self.base and self.defaults"
resource: "/glom/core.py#L1837-L1838"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L1837-L1838"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "side_effects"]}]
status: "stable"
---
# `glom.core.Vars.glomit`

`glomit(self, target, spec)`

## Contract

- **inputs**: self: a Vars instance; target: the object being glommed; spec: the current spec (unused)
- **outputs**: a ScopeVars instance constructed from self.base and self.defaults
- **raises**: none
- **side_effects**: none

## Callees
`glom.core.ScopeVars`

## Tested by
- `glom/test/test_scope_vars.py::test_let`
- `glom/test/test_scope_vars.py::test_max_skip`
- `glom/test/test_scope_vars.py::test_s_scope_assign`
- `glom/test/test_scope_vars.py::test_vars`
