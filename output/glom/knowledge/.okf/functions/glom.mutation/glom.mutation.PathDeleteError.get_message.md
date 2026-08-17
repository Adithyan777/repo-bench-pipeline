---
type: "python-function"
title: "get_message"
description: "a formatted string describing the delete failure, including dest_name, path, and the underlying exception"
resource: "/glom/mutation.py#L54-L56"
tags: ["glom", "mutation"]
sources: [{"resource": "/glom/mutation.py#L54-L56"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["side_effects"]}]
status: "stable"
---
# `glom.mutation.PathDeleteError.get_message`

`get_message(self)`

## Contract

- **inputs**: self: the PathDeleteError instance
- **outputs**: a formatted string describing the delete failure, including dest_name, path, and the underlying exception
- **raises**: none
- **side_effects**: none
- **invariants**: the returned string always contains self.dest_name, self.path, and self.exc

## Tested by
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_mutation.py::test_bad_delete_target`
- `glom/test/test_mutation.py::test_delete`
- `glom/test/test_mutation.py::test_sequence_delete`
