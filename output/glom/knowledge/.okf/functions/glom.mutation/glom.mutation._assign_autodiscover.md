---
type: "python-function"
title: "_assign_autodiscover"
description: "a callable for assigning to instances of type_obj, or False if type_obj is unassignable"
resource: "/glom/mutation.py#L228-L238"
tags: ["glom", "mutation"]
sources: [{"resource": "/glom/mutation.py#L228-L238"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["side_effects"]}]
status: "stable"
---
# `glom.mutation._assign_autodiscover`

`_assign_autodiscover(type_obj)`

## Contract

- **inputs**: type_obj: a type object to discover assignment handler for
- **outputs**: a callable for assigning to instances of type_obj, or False if type_obj is unassignable
- **raises**: none
- **side_effects**: none
- **invariants**: returns False for subclasses of _UNASSIGNABLE_BASE_TYPES; otherwise returns a callable based on presence of __setitem__ and index methods, or setattr as fallback

## Tested by
- `glom/test/test_target_types.py::test_default_scope_register`
