---
type: "python-function"
title: "_format_slice"
description: "a formatted string representation of the slice, or bbrepr(x) if not a slice"
resource: "/glom/core.py#L1718-L1724"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L1718-L1724"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callers", "link", "side_effects"]}]
status: "stable"
---
# `glom.core._format_slice`

`_format_slice(x)`

## Contract

- **inputs**: x: a slice or other value
- **outputs**: a formatted string representation of the slice, or bbrepr(x) if not a slice
- **raises**: none
- **side_effects**: none

## Callers
[glom.core._format_t](glom.core._format_t.md)

## Tested by
- `glom/test/test_basic.py::test_invoke`
- `glom/test/test_basic.py::test_python_native`
- `glom/test/test_basic.py::test_ref`
- `glom/test/test_error.py::test_pae_scope_printable`
- `glom/test/test_match.py::test_and_or_reduction`
- `glom/test/test_match.py::test_m_call_match`
- `glom/test/test_mutation.py::test_delete`
- `glom/test/test_path_and_t.py::test_path_t_roundtrip`
- `glom/test/test_path_and_t.py::test_t_picklability`
- `glom/test/test_scope_vars.py::test_vars`
- `glom/test/test_streaming.py::test_split_flatten`
