---
type: "python-function"
title: "glomit"
description: "self.value (the literal value stored in Val)"
resource: "/glom/core.py#L1789-L1790"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L1789-L1790"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["side_effects"]}]
status: "stable"
---
# `glom.core.Val.glomit`

`glomit(self, target, scope)`

## Contract

- **inputs**: self: a Val instance; target: the object being glommed; scope: the current evaluation scope (mapping)
- **outputs**: self.value (the literal value stored in Val)
- **raises**: none
- **side_effects**: none

## Tested by
- `glom/test/test_basic.py::test_call_and_target`
- `glom/test/test_basic.py::test_val`
- `glom/test/test_grouping.py::test_corner_cases`
- `glom/test/test_match.py::test_check_ported_tests`
- `glom/test/test_match.py::test_clamp`
- `glom/test/test_match.py::test_examples`
- `glom/test/test_match.py::test_json_ref`
- `glom/test/test_match.py::test_match_default`
- `glom/test/test_match.py::test_pattern_matching`
- `glom/test/test_match.py::test_precedence`
- `glom/test/test_scope_vars.py::test_let`
- `glom/test/test_scope_vars.py::test_max_skip`
- `glom/test/test_scope_vars.py::test_s_scope_assign`
- `glom/test/test_scope_vars.py::test_vars`
- `glom/test/test_snippets.py::test_snippet`
