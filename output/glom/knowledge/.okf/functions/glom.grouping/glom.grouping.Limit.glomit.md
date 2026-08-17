---
type: "python-function"
title: "glomit"
description: "the result of evaluating self.subspec against target, or STOP once the count exceeds self.n"
resource: "/glom/grouping.py#L303-L313"
tags: ["glom", "grouping"]
sources: [{"resource": "/glom/grouping.py#L303-L313"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "raises"]}]
status: "stable"
---
# `glom.grouping.Limit.glomit`

`glomit(self, target, scope)`

## Contract

- **inputs**: self: the Limit specifier instance with attributes n and subspec; target: the current item being processed; scope: the glom execution scope
- **outputs**: the result of evaluating self.subspec against target, or STOP once the count exceeds self.n
- **raises**: BadSpec
- **side_effects**: mutates scope[ACC_TREE] by inserting a [count, {}] list under tree[self] and updating the count; temporarily redirects scope[ACC_TREE] to the nested dict
- **invariants**: the counter stored in tree[self][0] increments by exactly 1 per call; once the counter exceeds self.n, the method returns STOP and does not recurse further

## Callees
`glom.core.BadSpec`

## Tested by
- `glom/test/test_grouping.py::test_corner_cases`
- `glom/test/test_grouping.py::test_limit`
