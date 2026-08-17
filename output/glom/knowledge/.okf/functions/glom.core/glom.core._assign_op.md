---
type: "python-function"
title: "_assign_op"
description: "helper method for doing the assignment on a T operation"
resource: "/glom/core.py#L1662-L1675"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L1662-L1675"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "callers", "link", "raises"]}]
status: "stable"
---
# `glom.core._assign_op`

`_assign_op(dest, op, arg, val, path, scope)`

> helper method for doing the assignment on a T operation

## Contract

- **inputs**: dest: destination object; op: operation string ('[', '.', 'P'); arg: argument for the operation; val: value to assign; path: path for error context; scope: current evaluation scope
- **outputs**: none (implicitly returns None)
- **raises**: PathAssignError
- **side_effects**: mutates dest by setting dest[arg] or setattr(dest, arg, val) or calling assign handler

## Callers
[glom.core._t_eval](glom.core._t_eval.md), [glom.mutation.Assign.glomit](../glom.mutation/glom.mutation.Assign.glomit.md)

## Callees
`glom.core.PathAssignError`

## Tested by
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_match.py::test_nested_dict`
- `glom/test/test_mutation.py::test_assign`
- `glom/test/test_mutation.py::test_assign_missing_dict`
- `glom/test/test_mutation.py::test_assign_missing_object`
- `glom/test/test_mutation.py::test_assign_missing_unassignable`
- `glom/test/test_mutation.py::test_assign_missing_with_extant_keys`
- `glom/test/test_mutation.py::test_assign_recursive`
- `glom/test/test_mutation.py::test_assign_spec_val`
- `glom/test/test_mutation.py::test_bad_assign_target`
- `glom/test/test_mutation.py::test_s_assign`
- `glom/test/test_mutation.py::test_sequence_assign`
- `glom/test/test_mutation.py::test_star_broadcast`
- `glom/test/test_mutation.py::test_unregistered_assign`
- `glom/test/test_scope_vars.py::test_globals`
- `glom/test/test_scope_vars.py::test_let`
- `glom/test/test_scope_vars.py::test_max_skip`
- `glom/test/test_scope_vars.py::test_s_scope_assign`
- `glom/test/test_scope_vars.py::test_scoped_vars`
- `glom/test/test_scope_vars.py::test_vars`
- `glom/test/test_snippets.py::test_snippet`
