---
type: "python-function"
title: "get_keys"
description: "the keys of obj.__dict__"
resource: "/glom/core.py#L1912-L1914"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L1912-L1914"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["side_effects"]}]
status: "stable"
---
# `glom.core._ObjStyleKeys.get_keys`

`get_keys(obj)`

## Contract

- **inputs**: obj: an object
- **outputs**: the keys of obj.__dict__
- **raises**: none
- **side_effects**: none

## Tested by
- `glom/test/test_path_and_t.py::test_path_star`
