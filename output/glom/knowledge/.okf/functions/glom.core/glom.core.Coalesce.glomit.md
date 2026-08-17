---
type: "python-function"
title: "glomit"
description: "the first subspec result that is not skipped, or the default/default_factory value"
resource: "/glom/core.py#L922-L940"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L922-L940"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "link", "raises", "side_effects"]}]
status: "stable"
---
# `glom.core.Coalesce.glomit`

`glomit(self, target, scope)`

## Contract

- **inputs**: self: a Coalesce instance; target: the object being glommed; scope: the current evaluation scope (mapping)
- **outputs**: the first subspec result that is not skipped, or the default/default_factory value
- **raises**: CoalesceError
- **side_effects**: none

## Callees
`glom.core.CoalesceError`, [glom.core.arg_val](glom.core.arg_val.md)

## Tested by
- `glom/test/test_basic.py::test_coalesce`
- `glom/test/test_basic.py::test_initial_integration`
- `glom/test/test_basic.py::test_skip`
- `glom/test/test_check.py::test_check_basic`
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_error.py::test_coalesce_stack`
- `glom/test/test_match.py::test_check_ported_tests`
- `glom/test/test_reduction.py::test_sum_integers`
- `glom/test/test_snippets.py::test_snippet`
