---
type: "python-function"
title: "__eq__"
description: "True if other is a Path or TType with equivalent operations, otherwise False"
resource: "/glom/core.py#L681-L686"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L681-L686"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["side_effects"]}]
status: "stable"
---
# `glom.core.Path.__eq__`

`__eq__(self, other)`

## Contract

- **inputs**: self: a Path instance; other: the object to compare
- **outputs**: True if other is a Path or TType with equivalent operations, otherwise False
- **raises**: none
- **side_effects**: none

## Tested by
- `glom/test/test_error.py::test_pae_api`
- `glom/test/test_path_and_t.py::test_from_t_identity`
- `glom/test/test_path_and_t.py::test_path_eq`
- `glom/test/test_path_and_t.py::test_path_eq_t`
- `glom/test/test_path_and_t.py::test_path_getitem`
- `glom/test/test_path_and_t.py::test_path_slices`
