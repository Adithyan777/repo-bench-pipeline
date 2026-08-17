---
type: "python-function"
title: "save"
description: "none"
resource: "/glom/tutorial.py#L461-L462"
tags: ["glom", "tutorial"]
sources: [{"resource": "/glom/tutorial.py#L461-L462"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: []
status: "draft"
---
# `glom.tutorial.ContactManager.save`

`save(self, contact)`

## Contract

- **inputs**: self: a ContactManager instance; contact: a contact object with an id attribute
- **outputs**: none
- **raises**: none
- **side_effects**: stores contact in CONTACTS under contact.id

## Tested by
- `glom/test/test_tutorial.py::test_tutorial`
