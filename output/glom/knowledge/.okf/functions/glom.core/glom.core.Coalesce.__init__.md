---
type: "python-function"
title: "__init__"
description: "none (initializes subspecs, default, default_factory, skip, skip_exc)"
resource: "/glom/core.py#L902-L920"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L902-L920"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["raises"]}]
status: "stable"
---
# `glom.core.Coalesce.__init__`

`__init__(self, *subspecs, **kwargs)`

## Contract

- **inputs**: self: a new Coalesce instance; *subspecs: one or more specs to try in order; **kwargs: default, default_factory, skip, skip_exc
- **outputs**: none (initializes subspecs, default, default_factory, skip, skip_exc)
- **raises**: ValueError, TypeError
- **side_effects**: mutates self by setting attributes subspecs, default, default_factory, skip, skip_exc, skip_func
- **invariants**: default and default_factory cannot both be set

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
