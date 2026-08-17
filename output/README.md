# output/

Per-target-repo pipeline outputs. Mostly regenerated on each run.

## Layout

```
output/
  <repo>/
    repo/                   # clean working clone with git history preserved; pipeline edits are labeled commits
    hygiene/                # step JSON records (detect.json, pin.json, build.json, baseline.json, etc.)
    knowledge/
      repo_graph.json       # static knowledge graph (nodes + edges with evidence)
      symbol_index.json     # raw AST symbol index
      .okf/                 # OKF v0.2 knowledge bundle (cross-linked Markdown pages)
      history_index.json    # every original commit with touched functions
      test_map.json         # test -> source function mapping from coverage
      coverage.json         # per-function coverage percentages
      hotspots.json         # change frequency per function
      graph_verification.json
      okf_verification.json
      okf.json, okf_decisions.json
    tasks/
      candidates.json       # excision funnel output
      history_candidates.json
      built.json            # all built excision tasks
      built_history.json    # all built history tasks
      instructions.json     # instruction authoring outcomes
      selection.json        # why each eligible task was picked or not
      agent_cache/          # content-addressed agent decision cache
    audit/
      llm_usage.json        # token usage by step (prompt, completion, reasoning, total)
      agent_actions.jsonl   # every agent action (build repair, baseline fix, etc.)
    report_data.json        # per-stage timing + LLM usage written by the runners
    report_summary.json     # aggregated data from all stages, used to render REPORT.md
    state.json              # resumability ledger (step status + input hashes)
```

## What is committed

See `.gitignore` for the definitive policy. Most of `output/` is regenerated and gitignored. The committed exception is the knowledge deliverables for the target repo (`repo_graph.json` and the `.okf/` bundle).
