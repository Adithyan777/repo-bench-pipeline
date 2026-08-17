---
type: "python-function"
title: "__init__"
description: "none (initializes Check instance attributes: spec, _orig_kwargs, default, validators, instance_of, types, vals)"
resource: "/glom/matching.py#L898-L952"
tags: ["glom", "matching"]
sources: [{"resource": "/glom/matching.py#L898-L952"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.matching.Check.__init__`

`__init__(self, spec=T, **kwargs)`

## Contract

- **inputs**: self; spec (default T); **kwargs including optional 'default' (default RAISE), 'validate' (default truthy if no kwargs else _MISSING), 'type', 'instance_of', 'equal_to', 'one_of'
- **outputs**: none (initializes Check instance attributes: spec, _orig_kwargs, default, validators, instance_of, types, vals)
- **raises**: TypeError, ValueError
- **side_effects**: none
- **invariants**: If equal_to is passed, one_of must not be passed; kwargs must not contain unexpected keys after popping known ones

## Tested by
- `glom/test/test_check.py::test_check_basic`
- `glom/test/test_check.py::test_check_multi`
- `glom/test/test_check.py::test_check_signature`
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_snippets.py::test_snippet`
- `glom/test/test_streaming.py::test_filter`
- `glom/test/test_streaming.py::test_windowed`
