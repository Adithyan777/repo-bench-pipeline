---
type: "python-module"
title: "glom.matching"
description: "The `glom.matching` module provides inline data validation and pattern matching capabilities within glom specs, allowing engineers to confirm target data matches their assumptions without a separate v"
resource: "/glom/matching.py#L1"
tags: ["glom", "matching"]
sources: [{"resource": "/glom/matching.py#L1"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# Module `glom.matching`

## Purpose
The `glom.matching` module provides inline data validation and pattern matching capabilities within glom specs, allowing engineers to confirm target data matches their assumptions without a separate validation step. It exposes specifiers like `Match`, `Check`, `And`, `Or`, `Not`, `Switch`, and `Regex` for asserting conditions, matching structures, and routing processing based on data shape, with corresponding error types (`CheckError`, `MatchError`, `TypeMatchError`) raised when checks fail.

## API

- [glom.matching.Check.__init__](../functions/glom.matching/glom.matching.Check.__init__.md) — `__init__(self, spec=T, **kwargs)`
- [glom.matching.Check.glomit](../functions/glom.matching/glom.matching.Check.glomit.md) — `glomit(self, target, scope)`
- [glom.matching.CheckError.get_message](../functions/glom.matching/glom.matching.CheckError.get_message.md) — `get_message(self)`
- [glom.matching.Match.glomit](../functions/glom.matching/glom.matching.Match.glomit.md) — `glomit(self, target, scope)`
- [glom.matching.Match.matches](../functions/glom.matching/glom.matching.Match.matches.md) — `matches(self, target)`
- [glom.matching.Match.verify](../functions/glom.matching/glom.matching.Match.verify.md) — `verify(self, target)`
- [glom.matching.MatchError.get_message](../functions/glom.matching/glom.matching.MatchError.get_message.md) — `get_message(self)`
- [glom.matching.Not.glomit](../functions/glom.matching/glom.matching.Not.glomit.md) — `glomit(self, target, scope)`
- [glom.matching.Optional.glomit](../functions/glom.matching/glom.matching.Optional.glomit.md) — `glomit(self, target, scope)`
- [glom.matching.Regex.__init__](../functions/glom.matching/glom.matching.Regex.__init__.md) — `__init__(self, pattern, flags=0, func=None)`
- [glom.matching.Regex.glomit](../functions/glom.matching/glom.matching.Regex.glomit.md) — `glomit(self, target, scope)`
- [glom.matching.Switch.__init__](../functions/glom.matching/glom.matching.Switch.__init__.md) — `__init__(self, cases, default=_MISSING)`
- [glom.matching.Switch.glomit](../functions/glom.matching/glom.matching.Switch.glomit.md) — `glomit(self, target, scope)`
- [glom.matching._Bool.__repr__](../functions/glom.matching/glom.matching._Bool.__repr__.md) — `__repr__(self)`
- [glom.matching._Bool.glomit](../functions/glom.matching/glom.matching._Bool.glomit.md) — `glomit(self, target, scope)`
- [glom.matching._MExpr.glomit](../functions/glom.matching/glom.matching._MExpr.glomit.md) — `glomit(self, target, scope)`
- [glom.matching._MSubspec.glomit](../functions/glom.matching/glom.matching._MSubspec.glomit.md) — `glomit(self, target, scope)`
- [glom.matching._MType.glomit](../functions/glom.matching/glom.matching._MType.glomit.md) — `glomit(self, target, spec)`
- [glom.matching._glom_match](../functions/glom.matching/glom.matching._glom_match.md) — `_glom_match(target, spec, scope)`
- [glom.matching._handle_dict](../functions/glom.matching/glom.matching._handle_dict.md) — `_handle_dict(target, spec, scope)`
- [glom.matching._precedence](../functions/glom.matching/glom.matching._precedence.md) — `_precedence(match)`

## Internal helpers

- `__and__(self, other)`
- `_glomit(self, target, scope)`
- `__repr__(self)`
- `__init__(self, msgs, check, path)`
- `__repr__(self)`
- `__init__(self, spec, default=_MISSING)`
- `__repr__(self)`
- `__init__(self, fmt, *args)`
- `__init__(self, child)`
- `__repr__(self)`
- `_m_repr(self)`
- `__init__(self, key, default=_MISSING)`
- `__repr__(self)`
- `__or__(self, other)`
- `_glomit(self, target, scope)`
- `__repr__(self)`
- `__init__(self, key)`
- `__repr__(self)`
- `__repr__(self)`
- `__copy__(self)`
- `__init__(self, actual, expected)`
- `__and__(self, other)`
- `__init__(self, *children, **kw)`
- `__invert__(self)`
- `__or__(self, other)`
- `_m_repr(self)`
- `__and__(self, other)`
- `__init__(self, lhs, op, rhs)`
- `__invert__(self)`
- `__or__(self, other)`
- `__repr__(self)`
- `__eq__(self, other)`
- `__ge__(self, other)`
- `__gt__(self, other)`
- `__init__(self, spec)`
- `__le__(self, other)`
- `__lt__(self, other)`
- `__ne__(self, other)`
- `__repr__(self)`
- `__and__(self, other)`
- `__call__(self, spec)`
- `__eq__(self, other)`
- `__ge__(self, other)`
- `__gt__(self, other)`
- `__invert__(self)`
- `__le__(self, other)`
- `__lt__(self, other)`
- `__ne__(self, other)`
- `__or__(self, other)`
- `__repr__(self)`
- `_bool_child_repr(child)`

## Calls
`glom.core.GlomError`, `glom.core.arg_val`, `glom.core.chain_child`, `glom.core.format_invocation`, `glom.core.glom`, `glom.matching.And`, `glom.matching.CheckError`, `glom.matching.MatchError`, `glom.matching.Not`, `glom.matching.Not._m_repr`, `glom.matching.Or`, `glom.matching.TypeMatchError`, `glom.matching._Bool._m_repr`, `glom.matching._MExpr`, `glom.matching._MSubspec`, `glom.matching._bool_child_repr`, `glom.matching._handle_dict`, `glom.matching._precedence`

## Tested by
- `glom/test/test_check.py::test_check_basic`
- `glom/test/test_check.py::test_check_multi`
- `glom/test/test_check.py::test_check_signature`
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_error.py::test_branching_stack`
- `glom/test/test_error.py::test_midway_branch`
- `glom/test/test_error.py::test_partially_failing_branch`
- `glom/test/test_match.py::test_and_or_reduction`
- `glom/test/test_match.py::test_basic`
- `glom/test/test_match.py::test_check_ported_tests`
- `glom/test/test_match.py::test_clamp`
- `glom/test/test_match.py::test_cruddy_json`
- `glom/test/test_match.py::test_defaults`
- `glom/test/test_match.py::test_double_wrapping`
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
- `glom/test/test_match.py::test_reprs`
- `glom/test/test_match.py::test_sample`
- `glom/test/test_match.py::test_sets`
- `glom/test/test_match.py::test_shortcircuit`
- `glom/test/test_match.py::test_sky`
- `glom/test/test_match.py::test_switch`
- `glom/test/test_match.py::test_ternary`
- `glom/test/test_mutation.py::test_assign_spec_val`
- `glom/test/test_path_and_t.py::test_t_subspec`
- `glom/test/test_scope_vars.py::test_max_skip`
- `glom/test/test_snippets.py::test_snippet`
- `glom/test/test_streaming.py::test_filter`
- `glom/test/test_streaming.py::test_windowed`
