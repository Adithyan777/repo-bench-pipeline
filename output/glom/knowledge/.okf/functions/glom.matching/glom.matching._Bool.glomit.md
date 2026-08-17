---
type: "python-function"
title: "glomit"
description: "Returns the result of self._glomit(target, scope), or evaluated default if a GlomError occurs and default is not _MISSING"
resource: "/glom/matching.py#L282-L288"
tags: ["glom", "matching"]
sources: [{"resource": "/glom/matching.py#L282-L288"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.matching._Bool.glomit`

`glomit(self, target, scope)`

## Contract

- **inputs**: self; target; scope
- **outputs**: Returns the result of self._glomit(target, scope), or evaluated default if a GlomError occurs and default is not _MISSING
- **raises**: GlomError
- **side_effects**: none
- **invariants**: If default is _MISSING, any GlomError from _glomit is re-raised; otherwise default is returned on GlomError

## Callees
[glom.core.arg_val](../glom.core/glom.core.arg_val.md)

## Tested by
- `glom/test/test_error.py::test_partially_failing_branch`
- `glom/test/test_match.py::test_basic`
- `glom/test/test_match.py::test_check_ported_tests`
- `glom/test/test_match.py::test_clamp`
- `glom/test/test_match.py::test_defaults`
- `glom/test/test_match.py::test_examples`
- `glom/test/test_match.py::test_json_ref`
- `glom/test/test_match.py::test_nested_struct`
- `glom/test/test_match.py::test_pattern_matching`
- `glom/test/test_match.py::test_shortcircuit`
- `glom/test/test_match.py::test_sky`
- `glom/test/test_match.py::test_ternary`
- `glom/test/test_mutation.py::test_assign_spec_val`
- `glom/test/test_path_and_t.py::test_t_subspec`
- `glom/test/test_scope_vars.py::test_max_skip`
- `glom/test/test_snippets.py::test_snippet`
