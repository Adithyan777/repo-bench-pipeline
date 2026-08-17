---
type: "python-function"
title: "_extend_children"
description: "none (implicitly returns None)"
resource: "/glom/core.py#L1678-L1700"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L1678-L1700"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callers", "link"]}]
status: "stable"
---
# `glom.core._extend_children`

`_extend_children(children, item, get_handler)`

## Contract

- **inputs**: children: a list to extend; item: an object to extract children from; get_handler: callable to retrieve operation handlers
- **outputs**: none (implicitly returns None)
- **raises**: none
- **side_effects**: mutates children by appending child items from item

## Callers
[glom.core._t_eval](glom.core._t_eval.md)

## Tested by
- `glom/test/test_mutation.py::test_star_broadcast`
- `glom/test/test_path_and_t.py::test_path_star`
- `glom/test/test_path_and_t.py::test_star_broadcast`
