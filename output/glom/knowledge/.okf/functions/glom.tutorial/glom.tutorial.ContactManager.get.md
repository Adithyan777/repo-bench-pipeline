---
type: "python-function"
title: "get"
description: "the value associated with contact_id in CONTACTS, or None if absent"
resource: "/glom/tutorial.py#L464-L465"
tags: ["glom", "tutorial"]
sources: [{"resource": "/glom/tutorial.py#L464-L465"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["side_effects"]}]
status: "stable"
---
# `glom.tutorial.ContactManager.get`

`get(self, contact_id)`

## Contract

- **inputs**: self: a ContactManager instance; contact_id: a key to look up in CONTACTS
- **outputs**: the value associated with contact_id in CONTACTS, or None if absent
- **raises**: none
- **side_effects**: none

## Tested by
- `glom/test/test_tutorial.py::test_tutorial`
