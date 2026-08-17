---
type: "python-function"
title: "glom"
description: "Access or construct a value from a given *target* based on the"
resource: "/glom/core.py#L2189-L2299"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L2189-L2299"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.core.glom`

`glom(target, spec, **kwargs)`

> Access or construct a value from a given *target* based on the
> specification declared by *spec*.
> 
> Accessing nested data, aka deep-get:
> 
> >>> target = {'a': {'b': 'c'}}
> >>> glom(target, 'a.b')
> 'c'
> 
> Here the *spec* was just a string denoting a path,
> ``'a.b'``. As simple as it should be. You can also use 
> :mod:`glob`-like wildcard selectors:
> 
> >>> target = {'a': [{'k': 'v1'}, {'k': 'v2'}]}
> >>> glom(target, 'a.*.k')
> ['v1', 'v2']
> 
> In addition to ``*``, you can also use ``**`` for recursive access:
> 
> >>> target = {'a': [{'k': 'v3'}, {'k': 'v4'}], 'k': 'v0'}
> >>> glom(target, '**.k')
> ['v0', 'v3', 'v4']
> 
> The next example shows how to use nested data to 
> access many fields at once, and make a new nested structure.
> 
> Constructing, or restructuring more-complicated nested data:
> 
> >>> target = {'a': {'b': 'c', 'd': 'e'}, 'f': 'g', 'h': [0, 1, 2]}
> >>> spec = {'a': 'a.b', 'd': 'a.d', 'h': ('h', [lambda x: x * 2])}
> >>> output = glom(target, spec)
> >>> pprint(output)
> {'a': 'c', 'd': 'e', 'h': [0, 2, 4]}
> 
> ``glom`` also takes a keyword-argument, *default*. When set,
> if a ``glom`` operation fails with a :exc:`GlomError`, the
> *default* will be returned, very much like
> :meth:`dict.get()`:
> 
> >>> glom(target, 'a.xx', default='nada')
> 'nada'
> 
> The *skip_exc* keyword argument controls which errors should
> be ignored.
> 
> >>> glom({}, lambda x: 100.0 / len(x), default=0.0, skip_exc=ZeroDivisionError)
> 0.0
> 
> Args:
>    target (object): the object on which the glom will operate.
>    spec (object): Specification of the output object in the form
>      of a dict, list, tuple, string, other glom construct, or
>      any composition of these.
>    default (object): An optional default to return in the case
>      an exception, specified by *skip_exc*, is raised.
>    skip_exc (Exception): An optional exception or tuple of
>      exceptions to ignore and return *default* (None if
>      omitted). If *skip_exc* and *default* are both not set,
>      glom raises errors through.
>    scope (dict): Additional data that can be accessed
>      via S inside the glom-spec. Read more: :ref:`scope`.
> 
> It's a small API with big functionality, and glom's power is
> only surpassed by its intuitiveness. Give it a whirl!

## Contract

- **inputs**: target: the object on which the glom will operate; spec: specification of the output object; **kwargs: optional keyword arguments including default, skip_exc, glom_debug, path, inspector, and scope
- **outputs**: The result of evaluating the spec against the target, or default if an exception in skip_exc occurs.
- **raises**: TypeError, GlomError
- **side_effects**: Modifies internal scope state and may mutate scope via kwargs.
- **invariants**: If kwargs contains unexpected keys, a TypeError is raised.

## Callers
[glom.core.Fill.fill](glom.core.Fill.fill.md), [glom.core.Glommer.glom](glom.core.Glommer.glom.md), [glom.matching.Match.matches](../glom.matching/glom.matching.Match.matches.md), [glom.matching.Match.verify](../glom.matching/glom.matching.Match.verify.md), [glom.mutation.assign](../glom.mutation/glom.mutation.assign.md), [glom.mutation.delete](../glom.mutation/glom.mutation.delete.md), [glom.reduction.flatten](../glom.reduction/glom.reduction.flatten.md), [glom.reduction.merge](../glom.reduction/glom.reduction.merge.md)

## Callees
`glom.core.ScopeVars`, [glom.core._glom](glom.core._glom.md)

## Tested by
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_basic_glom`
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_debug_and_inspect_with_closed_stdin`
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_debug_wraps_spec`
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_glom_dict_result`
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_glom_error_returns_one`
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_indent_zero_disables_pretty`
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_inspect_wraps_spec`
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_scalar_non_scalar`
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_scalar_output`
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_sort_keys`
- `glom/test/generated/test_glom_streaming.py::test_chunked_basic_exact_division`
- `glom/test/generated/test_glom_streaming.py::test_chunked_empty_iterable`
- `glom/test/generated/test_glom_streaming.py::test_chunked_single_element`
- `glom/test/generated/test_glom_streaming.py::test_chunked_size_larger_than_iterable`
- `glom/test/generated/test_glom_streaming.py::test_chunked_size_larger_with_fill`
- `glom/test/generated/test_glom_streaming.py::test_chunked_size_one`
- `glom/test/generated/test_glom_streaming.py::test_chunked_with_fill`
- `glom/test/generated/test_glom_streaming.py::test_chunked_with_remainder_no_fill`
- `glom/test/test_basic.py::test_beyond_access`
- `glom/test/test_basic.py::test_call_and_target`
- `glom/test/test_basic.py::test_coalesce`
- `glom/test/test_basic.py::test_glom_extra_kwargs`
- `glom/test/test_basic.py::test_initial_integration`
- `glom/test/test_basic.py::test_inspect`
- `glom/test/test_basic.py::test_invoke`
- `glom/test/test_basic.py::test_list_item_lift_and_access`
- `glom/test/test_basic.py::test_pipe`
- `glom/test/test_basic.py::test_python_native`
- `glom/test/test_basic.py::test_ref`
- `glom/test/test_basic.py::test_scope`
- `glom/test/test_basic.py::test_seq_getitem`
- `glom/test/test_basic.py::test_skip`
- `glom/test/test_basic.py::test_spec_and_recursion`
- `glom/test/test_basic.py::test_stop`
- `glom/test/test_basic.py::test_top_level_default`
- `glom/test/test_basic.py::test_val`
- `glom/test/test_check.py::test_check_basic`
- `glom/test/test_check.py::test_check_multi`
- `glom/test/test_cli.py::test_cli_blank`
- `glom/test/test_cli.py::test_cli_scalar`
- `glom/test/test_cli.py::test_cli_spec_argv_target_stdin_basic`
- `glom/test/test_cli.py::test_cli_spec_target_argv_basic`
- `glom/test/test_cli.py::test_cli_spec_target_files_basic`
- `glom/test/test_cli.py::test_main_basic`
- `glom/test/test_cli.py::test_main_python_full_spec_python_target`
- `glom/test/test_cli.py::test_main_toml_target`
- `glom/test/test_cli.py::test_main_yaml_target`
- `glom/test/test_error.py::test_3_11_byte_code_caret`
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_error.py::test_branching_stack`
- `glom/test/test_error.py::test_coalesce_stack`
- `glom/test/test_error.py::test_error`
- `glom/test/test_error.py::test_error_types`
- `glom/test/test_error.py::test_fallback`
- `glom/test/test_error.py::test_glom_dev_debug`
- `glom/test/test_error.py::test_glom_error_double_stack`
- `glom/test/test_error.py::test_glom_error_stack`
- `glom/test/test_error.py::test_good_error`
- `glom/test/test_error.py::test_line_trace`
- `glom/test/test_error.py::test_long_target_repr`
- `glom/test/test_error.py::test_midway_branch`
- `glom/test/test_error.py::test_nesting_stack`
- `glom/test/test_error.py::test_pae_api`
- `glom/test/test_error.py::test_pae_scope_printable`
- `glom/test/test_error.py::test_partially_failing_branch`
- `glom/test/test_error.py::test_regular_error_stack`
- `glom/test/test_error.py::test_unicode_stack`
- `glom/test/test_fill.py::test`
- `glom/test/test_grouping.py::test_agg`
- `glom/test/test_grouping.py::test_bucketing`
- `glom/test/test_grouping.py::test_corner_cases`
- `glom/test/test_grouping.py::test_limit`
- `glom/test/test_grouping.py::test_reduce`
- `glom/test/test_grouping.py::test_sample`
- `glom/test/test_match.py::test_basic`
- `glom/test/test_match.py::test_check_ported_tests`
- `glom/test/test_match.py::test_clamp`
- `glom/test/test_match.py::test_cruddy_json`
- `glom/test/test_match.py::test_defaults`
- `glom/test/test_match.py::test_examples`
- `glom/test/test_match.py::test_json_ref`
- `glom/test/test_match.py::test_m_call_match`
- `glom/test/test_match.py::test_match_default`
- `glom/test/test_match.py::test_match_expressions`
- `glom/test/test_match.py::test_nested_dict`
- `glom/test/test_match.py::test_nested_struct`
- `glom/test/test_match.py::test_pattern_matching`
- `glom/test/test_match.py::test_precedence`
- `glom/test/test_match.py::test_regex`
- `glom/test/test_match.py::test_sample`
- `glom/test/test_match.py::test_sets`
- `glom/test/test_match.py::test_shortcircuit`
- `glom/test/test_match.py::test_sky`
- `glom/test/test_match.py::test_switch`
- `glom/test/test_match.py::test_ternary`
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
- `glom/test/test_path_and_t.py::test_a_forbidden`
- `glom/test/test_path_and_t.py::test_empty_path_access`
- `glom/test/test_path_and_t.py::test_list_path_access`
- `glom/test/test_path_and_t.py::test_path`
- `glom/test/test_path_and_t.py::test_path_access_error_message`
- `glom/test/test_path_and_t.py::test_path_star`
- `glom/test/test_path_and_t.py::test_s_magic`
- `glom/test/test_path_and_t.py::test_star_broadcast`
- `glom/test/test_path_and_t.py::test_star_warning`
- `glom/test/test_path_and_t.py::test_t_arithmetic`
- `glom/test/test_path_and_t.py::test_t_arithmetic_errors`
- `glom/test/test_path_and_t.py::test_t_dict_key`
- `glom/test/test_path_and_t.py::test_t_dunders`
- `glom/test/test_path_and_t.py::test_t_picklability`
- `glom/test/test_path_and_t.py::test_t_subspec`
- `glom/test/test_reduction.py::test_flatten`
- `glom/test/test_reduction.py::test_flatten_func`
- `glom/test/test_reduction.py::test_fold`
- `glom/test/test_reduction.py::test_fold_bad_iter`
- `glom/test/test_reduction.py::test_merge`
- `glom/test/test_reduction.py::test_merge_func`
- `glom/test/test_reduction.py::test_merge_omd`
- `glom/test/test_reduction.py::test_sum_integers`
- `glom/test/test_reduction.py::test_sum_seqs`
- `glom/test/test_scope_vars.py::test_globals`
- `glom/test/test_scope_vars.py::test_let`
- `glom/test/test_scope_vars.py::test_max_skip`
- `glom/test/test_scope_vars.py::test_s_scope_assign`
- `glom/test/test_scope_vars.py::test_scoped_vars`
- `glom/test/test_scope_vars.py::test_vars`
- `glom/test/test_snippets.py::test_snippet`
- `glom/test/test_spec.py::test_scope_spec`
- `glom/test/test_spec.py::test_spec`
- `glom/test/test_streaming.py::test_all`
- `glom/test/test_streaming.py::test_chunked`
- `glom/test/test_streaming.py::test_faulty_iterate`
- `glom/test/test_streaming.py::test_filter`
- `glom/test/test_streaming.py::test_first`
- `glom/test/test_streaming.py::test_iter`
- `glom/test/test_streaming.py::test_iter_composition`
- `glom/test/test_streaming.py::test_map`
- `glom/test/test_streaming.py::test_slice`
- `glom/test/test_streaming.py::test_split_flatten`
- `glom/test/test_streaming.py::test_unique`
- `glom/test/test_streaming.py::test_while`
- `glom/test/test_streaming.py::test_windowed`
- `glom/test/test_target_types.py::test_bypass_getitem`
- `glom/test/test_target_types.py::test_duck_register`
- `glom/test/test_target_types.py::test_exact_register`
- `glom/test/test_target_types.py::test_faulty_iterate`
- `glom/test/test_target_types.py::test_iter_set`
- `glom/test/test_target_types.py::test_iter_str`
- `glom/test/test_target_types.py::test_types_bare`
- `glom/test/test_tutorial.py::test_tutorial`
