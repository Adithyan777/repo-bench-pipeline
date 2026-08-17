---
type: "python-function"
title: "get_type_map"
description: "an OrderedDict mapping types to handlers for op, or empty OrderedDict if none"
resource: "/glom/core.py#L2039-L2043"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L2039-L2043"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callers", "link", "side_effects"]}]
status: "stable"
---
# `glom.core.TargetRegistry.get_type_map`

`get_type_map(self, op)`

## Contract

- **inputs**: self: a TargetRegistry instance; op: operation name
- **outputs**: an OrderedDict mapping types to handlers for op, or empty OrderedDict if none
- **raises**: none
- **side_effects**: none

## Callers
[glom.core.TargetRegistry.get_handler](glom.core.TargetRegistry.get_handler.md)

## Tested by
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_basic_glom`
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_glom_error_returns_one`
- `glom/test/generated/test_glom_streaming.py::test_chunked_basic_exact_division`
- `glom/test/generated/test_glom_streaming.py::test_chunked_empty_iterable`
- `glom/test/test_basic.py::test_initial_integration`
- `glom/test/test_basic.py::test_pipe`
- `glom/test/test_basic.py::test_ref`
- `glom/test/test_basic.py::test_seq_getitem`
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
- `glom/test/test_mutation.py::test_sequence_assign`
- `glom/test/test_mutation.py::test_sequence_delete`
- `glom/test/test_mutation.py::test_star_broadcast`
- `glom/test/test_mutation.py::test_unregistered_assign`
- `glom/test/test_mutation.py::test_unregistered_delete`
- `glom/test/test_path_and_t.py::test_path_star`
- `glom/test/test_path_and_t.py::test_star_broadcast`
- `glom/test/test_reduction.py::test_flatten_func`
- `glom/test/test_reduction.py::test_fold_bad_iter`
- `glom/test/test_scope_vars.py::test_let`
- `glom/test/test_scope_vars.py::test_s_scope_assign`
- `glom/test/test_scope_vars.py::test_vars`
- `glom/test/test_snippets.py::test_snippet`
- `glom/test/test_streaming.py::test_faulty_iterate`
- `glom/test/test_streaming.py::test_iter`
- `glom/test/test_streaming.py::test_iter_composition`
- `glom/test/test_streaming.py::test_while`
- `glom/test/test_target_types.py::test_duck_register`
- `glom/test/test_target_types.py::test_exact_register`
- `glom/test/test_target_types.py::test_faulty_iterate`
- `glom/test/test_target_types.py::test_faulty_op_registration`
- `glom/test/test_target_types.py::test_iter_set`
- `glom/test/test_target_types.py::test_iter_str`
- `glom/test/test_target_types.py::test_reregister_type`
- `glom/test/test_target_types.py::test_types_bare`
- `glom/test/test_target_types.py::test_types_leave_one_out`
- `glom/test/test_tutorial.py::test_tutorial`
