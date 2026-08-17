---
type: "python-function"
title: "glomit"
description: "Returns the glom result of self.spec against target, or the evaluated default if a GlomError occurs and default is set"
resource: "/glom/matching.py#L148-L156"
tags: ["glom", "matching"]
sources: [{"resource": "/glom/matching.py#L148-L156"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.matching.Match.glomit`

`glomit(self, target, scope)`

## Contract

- **inputs**: self; target; scope
- **outputs**: Returns the glom result of self.spec against target, or the evaluated default if a GlomError occurs and default is set
- **raises**: GlomError
- **side_effects**: Sets scope[MODE] to _glom_match for the duration of the inner glom call
- **invariants**: If self.default is _MISSING, any GlomError from the inner glom is re-raised; otherwise default is evaluated and returned on GlomError

## Callees
[glom.core.arg_val](../glom.core/glom.core.arg_val.md)

## Tested by
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_error.py::test_branching_stack`
- `glom/test/test_error.py::test_midway_branch`
- `glom/test/test_match.py::test_basic`
- `glom/test/test_match.py::test_check_ported_tests`
- `glom/test/test_match.py::test_cruddy_json`
- `glom/test/test_match.py::test_defaults`
- `glom/test/test_match.py::test_json_ref`
- `glom/test/test_match.py::test_match_default`
- `glom/test/test_match.py::test_nested_dict`
- `glom/test/test_match.py::test_nested_struct`
- `glom/test/test_match.py::test_pattern_matching`
- `glom/test/test_match.py::test_precedence`
- `glom/test/test_match.py::test_sample`
- `glom/test/test_match.py::test_sets`
- `glom/test/test_match.py::test_sky`
- `glom/test/test_match.py::test_ternary`
- `glom/test/test_snippets.py::test_snippet`
