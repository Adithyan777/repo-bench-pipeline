---
type: "python-function"
title: "_get_closest_type"
description: "the closest registered type for obj, or None if not found"
resource: "/glom/core.py#L2045-L2052"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L2045-L2052"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "callers", "link", "side_effects"]}]
status: "stable"
---
# `glom.core.TargetRegistry._get_closest_type`

`_get_closest_type(self, obj, type_tree)`

## Contract

- **inputs**: self: a TargetRegistry instance; obj: an object instance; type_tree: a tree of registered types
- **outputs**: the closest registered type for obj, or None if not found
- **raises**: none
- **side_effects**: none

## Callers
[glom.core.TargetRegistry._get_closest_type](glom.core.TargetRegistry._get_closest_type.md), [glom.core.TargetRegistry.get_handler](glom.core.TargetRegistry.get_handler.md)

## Callees
[glom.core.TargetRegistry._get_closest_type](glom.core.TargetRegistry._get_closest_type.md)

## Tested by
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_glom_error_returns_one`
- `glom/test/generated/test_glom_streaming.py::test_chunked_basic_exact_division`
- `glom/test/test_basic.py::test_initial_integration`
- `glom/test/test_basic.py::test_pipe`
- `glom/test/test_basic.py::test_ref`
- `glom/test/test_basic.py::test_stop`
- `glom/test/test_cli.py::test_main_basic`
- `glom/test/test_cli.py::test_main_python_full_spec_python_target`
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_error.py::test_glom_error_stack`
- `glom/test/test_error.py::test_long_target_repr`
- `glom/test/test_mutation.py::test_assign`
- `glom/test/test_mutation.py::test_assign_missing_object`
- `glom/test/test_mutation.py::test_assign_missing_unassignable`
- `glom/test/test_mutation.py::test_bad_assign_target`
- `glom/test/test_mutation.py::test_bad_delete_target`
- `glom/test/test_mutation.py::test_delete`
- `glom/test/test_mutation.py::test_star_broadcast`
- `glom/test/test_path_and_t.py::test_path_star`
- `glom/test/test_path_and_t.py::test_star_broadcast`
- `glom/test/test_reduction.py::test_flatten_func`
- `glom/test/test_scope_vars.py::test_let`
- `glom/test/test_scope_vars.py::test_s_scope_assign`
- `glom/test/test_scope_vars.py::test_vars`
- `glom/test/test_streaming.py::test_iter`
- `glom/test/test_streaming.py::test_iter_composition`
- `glom/test/test_streaming.py::test_while`
- `glom/test/test_target_types.py::test_duck_register`
- `glom/test/test_target_types.py::test_exact_register`
- `glom/test/test_target_types.py::test_iter_set`
- `glom/test/test_target_types.py::test_iter_str`
- `glom/test/test_target_types.py::test_types_bare`
- `glom/test/test_target_types.py::test_types_leave_one_out`
