---
type: "python-function"
title: "glomit"
description: "the result of evaluating the path against target"
resource: "/glom/core.py#L674-L676"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L674-L676"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "link", "side_effects"]}]
status: "stable"
---
# `glom.core.Path.glomit`

`glomit(self, target, scope)`

## Contract

- **inputs**: self: a Path instance; target: the object being glommed; scope: the current evaluation scope (mapping)
- **outputs**: the result of evaluating the path against target
- **raises**: none
- **side_effects**: none

## Callees
[glom.core._t_eval](glom.core._t_eval.md)

## Tested by
- `glom/test/test_basic.py::test_initial_integration`
- `glom/test/test_cli.py::test_cli_blank`
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
- `glom/test/test_path_and_t.py::test_empty_path_access`
- `glom/test/test_path_and_t.py::test_list_path_access`
- `glom/test/test_path_and_t.py::test_path`
- `glom/test/test_path_and_t.py::test_path_access_error_message`
- `glom/test/test_path_and_t.py::test_path_star`
- `glom/test/test_scope_vars.py::test_let`
- `glom/test/test_scope_vars.py::test_s_scope_assign`
- `glom/test/test_scope_vars.py::test_vars`
