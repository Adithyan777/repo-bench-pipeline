# docs/

Pipeline documentation. The source of truth for all behavior is `pipeline/config.py` and the code; these docs explain the design and rationale.

| Document | Contents |
|---|---|
| [architecture.md](architecture.md) | Stage flow, resumability, Docker execution model, agent loop, LLM client, logging |
| [pipeline-1-hygiene.md](pipeline-1-hygiene.md) | Hygiene stage: detect, pin, build, baseline, test-gen, lint |
| [pipeline-2-knowledge.md](pipeline-2-knowledge.md) | Knowledge stage: repo graph, indexes, OKF bundle, verification |
| [pipeline-3-tasks.md](pipeline-3-tasks.md) | Tasks stage: funnels, harness, instructions, difficulty, selection |
| [configuration.md](configuration.md) | Every config key: default, meaning, rationale, `--set` examples |
| [decisions.md](decisions.md) | Design decisions with rejected alternatives |
| [gaps.md](gaps.md) | Known gaps with evidence and next steps |
