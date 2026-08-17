---
type: "python-function"
title: "glomit"
description: "the final accumulated grouping result, or the last value before STOP if STOP is encountered"
resource: "/glom/grouping.py#L75-L91"
tags: ["glom", "grouping"]
sources: [{"resource": "/glom/grouping.py#L75-L91"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "link"]}]
status: "stable"
---
# `glom.grouping.Group.glomit`

`glomit(self, target, scope)`

## Contract

- **inputs**: self: the Group specifier instance with a spec attribute; target: an iterable target to group over; scope: the glom execution scope
- **outputs**: the final accumulated grouping result, or the last value before STOP if STOP is encountered
- **raises**: none
- **side_effects**: mutates scope by setting MODE=GROUP, CUR_AGG=None, and ACC_TREE={}; iterates over target; calls scope[glom] repeatedly
- **invariants**: scope[MODE] is set to GROUP before processing begins; if target iteration yields nothing and self.spec is dict/list, ret starts as an empty dict/list, otherwise None

## Callees
[glom.grouping.target_iter](glom.grouping.target_iter.md)

## Tested by
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_grouping.py::test_agg`
- `glom/test/test_grouping.py::test_bucketing`
- `glom/test/test_grouping.py::test_corner_cases`
- `glom/test/test_grouping.py::test_limit`
- `glom/test/test_grouping.py::test_reduce`
- `glom/test/test_grouping.py::test_sample`
