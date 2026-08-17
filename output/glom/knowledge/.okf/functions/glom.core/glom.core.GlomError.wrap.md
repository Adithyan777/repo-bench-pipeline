---
type: "python-function"
title: "wrap"
description: "a wrapper exception instance that subclasses both the original exception type and GlomError, or exc itself if re-creation fails"
resource: "/glom/core.py#L133-L145"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L133-L145"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.core.GlomError.wrap`

`wrap(cls, exc)`

## Contract

- **inputs**: cls: the GlomError class; exc: the exception to wrap
- **outputs**: a wrapper exception instance that subclasses both the original exception type and GlomError, or exc itself if re-creation fails
- **raises**: none
- **side_effects**: none

## Tested by
- `glom/test/test_error.py::test_3_11_byte_code_caret`
- `glom/test/test_error.py::test_error_types`
- `glom/test/test_error.py::test_fallback`
- `glom/test/test_error.py::test_regular_error_stack`
- `glom/test/test_reduction.py::test_fold_bad_iter`
- `glom/test/test_scope_vars.py::test_let`
- `glom/test/test_scope_vars.py::test_s_scope_assign`
- `glom/test/test_spec.py::test_spec`
- `glom/test/test_streaming.py::test_faulty_iterate`
- `glom/test/test_target_types.py::test_faulty_iterate`
