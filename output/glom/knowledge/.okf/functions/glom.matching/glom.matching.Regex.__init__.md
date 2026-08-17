---
type: "python-function"
title: "__init__"
description: "none (initializes Regex with compiled regex and chosen match function)"
resource: "/glom/matching.py#L217-L232"
tags: ["glom", "matching"]
sources: [{"resource": "/glom/matching.py#L217-L232"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.matching.Regex.__init__`

`__init__(self, pattern, flags=0, func=None)`

## Contract

- **inputs**: self; pattern (regex string); flags=0; func=None (must be in _RE_VALID_FUNCS)
- **outputs**: none (initializes Regex with compiled regex and chosen match function)
- **raises**: ValueError, TypeError
- **side_effects**: none
- **invariants**: If func is re.match or re.search, uses that method; otherwise uses regex.fullmatch if available, else compiles pattern with \Z and uses match; func must be a valid re function or None

## Tested by
- `glom/test/test_match.py::test_nested_struct`
- `glom/test/test_match.py::test_regex`
- `glom/test/test_match.py::test_reprs`
