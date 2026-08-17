---
type: "python-function"
title: "get_message"
description: "Returns a formatted string describing the check failure path, optional subtarget spec, and error messages"
resource: "/glom/matching.py#L1042-L1050"
tags: ["glom", "matching"]
sources: [{"resource": "/glom/matching.py#L1042-L1050"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["side_effects"]}]
status: "stable"
---
# `glom.matching.CheckError.get_message`

`get_message(self)`

## Contract

- **inputs**: self (with attributes path, check_obj, msgs)
- **outputs**: Returns a formatted string describing the check failure path, optional subtarget spec, and error messages
- **raises**: none
- **side_effects**: none
- **invariants**: The returned message always references self.path and self.msgs, and includes the subtarget spec only if check_obj.spec is not T

## Tested by
- `glom/test/test_check.py::test_check_basic`
- `glom/test/test_check.py::test_check_multi`
- `glom/test/test_error.py::test_all_public_errors`
