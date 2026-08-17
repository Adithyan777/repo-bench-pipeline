---
type: "python-function"
title: "register_op"
description: "For extension authors needing to add operations beyond the builtin"
resource: "/glom/core.py#L2434-L2440"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L2434-L2440"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.core.register_op`

`register_op(op_name, **kwargs)`

> For extension authors needing to add operations beyond the builtin
> 'get', 'iterate', 'keys', 'assign', and 'delete' to the default scope. 
> See TargetRegistry for more details.

## Contract

- **inputs**: op_name: the name of the operation to register; **kwargs: keyword arguments forwarded to TargetRegistry.register_op
- **outputs**: None
- **raises**: none
- **side_effects**: Registers a new operation in the default scope's TargetRegistry, affecting subsequent module-level glom() behavior.
- **invariants**: The module-level default scope is mutated.
