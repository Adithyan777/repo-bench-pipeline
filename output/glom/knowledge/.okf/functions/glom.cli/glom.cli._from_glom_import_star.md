---
type: "python-function"
title: "_from_glom_import_star"
description: "a dict of glom module public attributes, excluding dunder attributes and submodules"
resource: "/glom/cli.py#L215-L222"
tags: ["cli", "glom"]
sources: [{"resource": "/glom/cli.py#L215-L222"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callers", "side_effects"]}]
status: "stable"
---
# `glom.cli._from_glom_import_star`

`_from_glom_import_star()`

## Contract

- **inputs**: none
- **outputs**: a dict of glom module public attributes, excluding dunder attributes and submodules
- **raises**: none
- **side_effects**: none

## Callers
`glom.cli._eval_python_full_spec`

## Tested by
- `glom/test/test_cli.py::test_main_python_full_spec_python_target`
