# HEURISTICS review sheet

Every value lives in `pipeline/config.py` and is documented in `HEURISTICS.md`. All are
still **PROPOSED** pending your approval. This sheet groups the keys so you can sign off
quickly: **(a) fired on glom** (used, with the observed effect), **(b) never fired** on the
in-scope repos, **(c) changed** from the original grill-session proposal. Numbers are from
the documented glom runs in `docs/PROGRESS.md`; the lint/select/report rows fire for the
first time on the finalization `--fresh` run.

## (a) Fired on glom — with observed effect

| Key(s) | Observed effect |
|---|---|
| `detect.python_version_cap=3.12` | glom classifiers list >3.12; capped to 3.12 |
| `detect.manifest_markers`, packaging=`setup.py` | detected setup.py; `pin.include_extras=("test",...)` folded glom's `test` extra into the lock |
| `pin.resolver=uv`, `generate_hashes`, `emit_constraints_txt` | single `uv pip compile` lock + constraints; 0 unresolved imports |
| `baseline.framework_priority=(pytest,...)` | pytest detected; **202 passed, 0 quarantined** |
| `testgen.*` (mutation gate, `min_mutants_killed=1`, `mutators` ×7) | 4 modules kept, **`glom.core` dropped** (0-kill, honest), 14/16 mutants |
| `graph.complexity_metric=branch_count`, `edge_types`, `nonsource_files/dirs` | 11 source modules, 4727 edges; `docs/conf.py` excluded; **precision 1.0, 0 mismatches** |
| `okf.min_private_page_complexity=2`, `max_function_pages=150`, `side_effect_call_names` | 165 pages, **105 verified / 45 draft**; callees precision 1.0, raises 0.79 |
| `excision.*` (`min_lines=8`, `min_complexity=3`, `max_covering_tests=40`, `public_only`, round-robin, private-verifier pre-gate) | funnel rejected 497→ built 5, **4 VALID**; `too-central` kept `get_handler` (112 tests) out |
| `history.*` (size/file caps, `reject_non_pr_merges`, `reject_reverted`, score weights, `classify_max_commits=60`, neutrality, `agent_max_turns=12`, getattr convention) | 1049 commits → 15 shortlisted → **8 VALID**; every reject reason exercised |
| `instruction.*` (leak gates a/b, `leak_api_names_only`, `exempt_diff_lines_in_tests`, `max_regenerations=2`) | 12 VALID → **12 final**, 1 regeneration, 0 leak rejections |
| `difficulty.target_spread={easy2,med5,hard3}`, `justification_must_cite_feature` | labels **easy 6 / medium 4 / hard 2**, 0 cite failures |
| `harness.*` (`determinism_runs=3`, strict fail reasons, `min_failing_tests=1`, `recopy_canonical_verifier`, static gate) | strict classifier caught the face-`CommandChecker` CLI case (INVALID) |
| all `*_filename`, `code_fingerprint_files`, decision-cache keys | structural — used every run; enable 0-token resumes |
| `lint.rules=(E,F,W,I,B,UP)`, `allow_noqa_for_unfixable`, `enabled` | **new** — fires on the finalization run; smoke-tested on mini_pkg (ruff-clean, pyproject created) |
| `selection.*` (`total_tasks=10`, `min_history=4`, `max_excision=4`, `max_netnew=2`, `min_distinct_modules=4`) | **new** — selects the final 10 on the finalization run |
| `report.draft_narrative` | **new** — one BIG draft call, cached by hash |

## (b) Never fired on the in-scope repos

| Key(s) | Why it stayed idle |
|---|---|
| `detect.import_alias_table`, `pin.alias_reask_attempts` | glom/toolz have manifests; only mini_pkg_notests/minidump exercise AST-inferred imports |
| `detect.service_import_signals`, `service_env_signals`, `docker.compose_*` | no repo in scope needs postgres/redis |
| `detect.git_version_tools` | fired on **toolz** (git-versioned), not glom |
| `baseline.agent_fix_allowed_globs`, `agent.baseline_fix_max_attempts` | glom baseline all-pass; no agent-fix needed |
| `excision.strip_docstring` (`--excision-hard`), `harness.verifier_visibility=hidden` | defaults kept (docstring stays, visible) |
| `harness.build_image_if_missing`, `gate_on_image_digest` | standalone-revalidation / digest-gating off by default |
| `netnew.*` | net-new tasks CUT by decision (S8 not built) |
| `lint.llm_fix_unfixable` | default off (noqa + report is safer) |

## (c) Changed from the original proposal

| Key | From → to | Why |
|---|---|---|
| `selection.max_netnew` | 3 (PDF) → **2** | user decision |
| `excision.max_covering_tests` | (none) → **40** | glom `get_handler` is covered by 112 tests; excising it fails the whole suite (`too-central`) (S4) |
| `history.agent_max_turns` | 25 → **12** | a 25-turn Kimi rewrite cost ~150k tokens (S5a) |
| `history.max_agent_runs_per_repo` / `max_neutrality_rewrites_per_repo` | (none) → **6 / 2** | bound BIG spend per build step (S5a) |
| `graph.nonsource_dirs` | (none) → **docs/examples/scripts/build/…** | `docs/conf.py` + example scripts were indexed as source (S7 fix) |
| `okf.verified_status` stamping | any-claim → **≥1 claim actually checked** | pages of pure prose are no longer auto-verified (S7) |
| `baseline.env_fix_attempts`, `baseline.treat_collection_broken_as_no_tests_after_repair` | inert → **deleted** | never read; the collection-broken branch is a documented gap, not a live flag (S9) |
| `harness.min_failing_tests` | `--set` only → **`--min-failing-tests` CLI flag** | surfaced (S9) |

## Note

`difficulty.target_spread` and `selection.*` are approximate/soft where the assignment
allows (spread is a soft objective; the quotas are hard). Everything above is one line so
you can approve, tweak, or veto per row; on approval, flip the `Status` column in
`HEURISTICS.md` from PROPOSED to confirmed.
