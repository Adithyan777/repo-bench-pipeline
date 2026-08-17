---
type: "python-function"
title: "__init__"
description: "none (initializes wrapped, recursive, echo, breakpoint, post_mortem)"
resource: "/glom/core.py#L994-L1009"
tags: ["core", "glom"]
sources: [{"resource": "/glom/core.py#L994-L1009"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "raises"]}]
status: "stable"
---
# `glom.core.Inspect.__init__`

`__init__(self, *a, **kw)`

## Contract

- **inputs**: self: a new Inspect instance; *a: optional wrapped spec (defaults to Path()); **kw: recursive, echo, breakpoint, post_mortem
- **outputs**: none (initializes wrapped, recursive, echo, breakpoint, post_mortem)
- **raises**: TypeError
- **side_effects**: mutates self by setting attributes wrapped, recursive, echo, breakpoint, post_mortem

## Callees
`glom.core.Path`

## Tested by
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_debug_and_inspect_with_closed_stdin`
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_debug_wraps_spec`
- `glom/test/generated/test_glom_cli.py::TestGlomCli::test_inspect_wraps_spec`
- `glom/test/test_basic.py::test_initial_integration`
- `glom/test/test_basic.py::test_inspect`
