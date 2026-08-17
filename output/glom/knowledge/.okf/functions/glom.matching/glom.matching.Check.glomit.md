---
type: "python-function"
title: "glomit"
description: "Returns ret (original target) if all checks pass; returns evaluated default if a check fails and default is not RAISE"
resource: "/glom/matching.py#L958-L1008"
tags: ["glom", "matching"]
sources: [{"resource": "/glom/matching.py#L958-L1008"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "link", "raises", "side_effects"]}]
status: "stable"
---
# `glom.matching.Check.glomit`

`glomit(self, target, scope)`

## Contract

- **inputs**: self; target (value to check); scope (glom scope mapping)
- **outputs**: Returns ret (original target) if all checks pass; returns evaluated default if a check fails and default is not RAISE
- **raises**: CheckError
- **side_effects**: none
- **invariants**: If default is RAISE and any check fails, a CheckError is raised with all accumulated error messages; validators that raise self._ValidationError are treated as validation failures

## Callees
[glom.core.arg_val](../glom.core/glom.core.arg_val.md), `glom.matching.CheckError`

## Tested by
- `glom/test/test_check.py::test_check_basic`
- `glom/test/test_check.py::test_check_multi`
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_snippets.py::test_snippet`
- `glom/test/test_streaming.py::test_filter`
- `glom/test/test_streaming.py::test_windowed`
