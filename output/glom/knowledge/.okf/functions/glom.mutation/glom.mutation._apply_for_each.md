---
type: "python-function"
title: "_apply_for_each"
description: "none"
resource: "/glom/mutation.py#L59-L67"
tags: ["glom", "mutation"]
sources: [{"resource": "/glom/mutation.py#L59-L67"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callers", "link"]}]
status: "stable"
---
# `glom.mutation._apply_for_each`

`_apply_for_each(func, path, val)`

## Contract

- **inputs**: func: a callable to apply; path: a Path object; val: the value to apply func to
- **outputs**: none
- **raises**: none
- **side_effects**: calls func on val, or on each inner element if path contains star layers
- **invariants**: if path has star layers, val is flattened layers-1 times before func is applied to each inner element

## Callers
[glom.mutation.Assign.glomit](glom.mutation.Assign.glomit.md), [glom.mutation.Delete.glomit](glom.mutation.Delete.glomit.md)

## Tested by
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_mutation.py::test_assign`
- `glom/test/test_mutation.py::test_assign_missing_dict`
- `glom/test/test_mutation.py::test_assign_missing_object`
- `glom/test/test_mutation.py::test_assign_missing_unassignable`
- `glom/test/test_mutation.py::test_assign_missing_with_extant_keys`
- `glom/test/test_mutation.py::test_assign_recursive`
- `glom/test/test_mutation.py::test_assign_spec_val`
- `glom/test/test_mutation.py::test_bad_assign_target`
- `glom/test/test_mutation.py::test_bad_delete_target`
- `glom/test/test_mutation.py::test_delete`
- `glom/test/test_mutation.py::test_delete_ignore_missing`
- `glom/test/test_mutation.py::test_s_assign`
- `glom/test/test_mutation.py::test_sequence_assign`
- `glom/test/test_mutation.py::test_sequence_delete`
- `glom/test/test_mutation.py::test_star_broadcast`
- `glom/test/test_mutation.py::test_unregistered_assign`
- `glom/test/test_mutation.py::test_unregistered_delete`
