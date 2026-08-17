---
type: "python-function"
title: "glomit"
description: "The folded or aggregated result value"
resource: "/glom/reduction.py#L68-L83"
tags: ["glom", "reduction"]
sources: [{"resource": "/glom/reduction.py#L68-L83"}]
generated: {"by": "pipeline/moonshotai/Kimi-K2.6", "at": "2026-08-18T03:15:17+05:30"}
verified: [{"by": "process:okf-verifier", "at": "2026-08-18T03:15:17+05:30", "checks": ["callees", "link", "raises"]}]
status: "stable"
---
# `glom.reduction.Fold.glomit`

`glomit(self, target, scope)`

## Contract

- **inputs**: self: the Fold instance; target: the value to fold/aggregate; scope: the current glom scope dict
- **outputs**: The folded or aggregated result value
- **raises**: FoldError
- **side_effects**: May mutate scope by setting scope[CUR_AGG] to self when in GROUP mode and CUR_AGG is None
- **invariants**: If scope[MODE] is GROUP and no CUR_AGG exists, self is stored as the current aggregator before proceeding

## Callees
[glom.grouping.target_iter](../glom.grouping/glom.grouping.target_iter.md), `glom.reduction.Fold._agg`, `glom.reduction.Fold._fold`, `glom.reduction.FoldError`

## Tested by
- `glom/test/test_error.py::test_all_public_errors`
- `glom/test/test_grouping.py::test_agg`
- `glom/test/test_grouping.py::test_reduce`
- `glom/test/test_reduction.py::test_flatten`
- `glom/test/test_reduction.py::test_flatten_func`
- `glom/test/test_reduction.py::test_fold`
- `glom/test/test_reduction.py::test_fold_bad_iter`
- `glom/test/test_reduction.py::test_merge`
- `glom/test/test_reduction.py::test_merge_func`
- `glom/test/test_reduction.py::test_merge_omd`
- `glom/test/test_reduction.py::test_sum_integers`
- `glom/test/test_reduction.py::test_sum_seqs`
