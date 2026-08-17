---
type: "python-function"
title: "__init__"
description: "none (initializes Switch with cases list and default)"
resource: "/glom/matching.py#L831-L845"
tags: ["glom", "matching"]
sources: [{"resource": "/glom/matching.py#L831-L845"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.matching.Switch.__init__`

`__init__(self, cases, default=_MISSING)`

## Contract

- **inputs**: self; cases (dict or list of (keyspec, valspec) pairs); default=_MISSING
- **outputs**: none (initializes Switch with cases list and default)
- **raises**: TypeError, ValueError
- **side_effects**: none
- **invariants**: cases must be non-empty; if a dict is passed it is converted to a list of items; cases must be a list after conversion

## Tested by
- `glom/test/test_error.py::test_branching_stack`
- `glom/test/test_error.py::test_midway_branch`
- `glom/test/test_match.py::test_switch`
- `glom/test/test_snippets.py::test_snippet`
