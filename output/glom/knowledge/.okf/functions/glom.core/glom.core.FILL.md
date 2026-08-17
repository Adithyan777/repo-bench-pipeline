---
type: "python-function"
title: "FILL"
description: "a recursively filled structure matching spec's type with evaluated values, or the result of calling spec if callable, or spec itself if not a container/callable"
resource: "/glom/core.py#L2546-L2560"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L2546-L2560"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["side_effects"]}]
status: "stable"
---
# `glom.core.FILL`

`FILL(target, spec, scope)`

## Contract

- **inputs**: target: the object being glommed; spec: the specification to evaluate (dict, list, tuple, set, frozenset, callable, or literal); scope: the current evaluation scope (mapping)
- **outputs**: a recursively filled structure matching spec's type with evaluated values, or the result of calling spec if callable, or spec itself if not a container/callable
- **raises**: none
- **side_effects**: none

## Tested by
- `glom/test/test_basic.py::test_ref`
- `glom/test/test_fill.py::test`
- `glom/test/test_match.py::test_pattern_matching`
- `glom/test/test_match.py::test_shortcircuit`
