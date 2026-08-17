---
type: "python-function"
title: "__init__"
description: "None"
resource: "/glom/reduction.py#L291-L300"
tags: ["glom", "reduction"]
sources: [{"resource": "/glom/reduction.py#L291-L300"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["raises"]}]
status: "stable"
---
# `glom.reduction.Merge.__init__`

`__init__(self, subspec=T, init=dict, op=None)`

## Contract

- **inputs**: self: the Merge instance; subspec: glomspec to fetch values from target (default T); init: callable to create the initial accumulator value (default dict); op: callable or string naming a method to use for combining values (default None, treated as 'update')
- **outputs**: None
- **raises**: ValueError
- **side_effects**: Initializes the Merge instance by setting subspec, init, and op attributes, calling super().__init__ with resolved values
- **invariants**: After initialization, self.op is always callable

## Tested by
- `glom/test/test_grouping.py::test_reduce`
- `glom/test/test_reduction.py::test_merge`
- `glom/test/test_reduction.py::test_merge_func`
- `glom/test/test_reduction.py::test_merge_omd`
