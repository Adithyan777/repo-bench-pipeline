# tasks/

Generated benchmark tasks. Each subdirectory is a target repo; within it, each task has its own folder.

## Layout

```
tasks/
  <repo>/
    tasks.json              # manifest of all built tasks for this repo
    <task_id>/
      task.json             # task metadata (id, title, provenance, module, instruction, difficulty)
      input/                # the repo tree as the solver sees it (function body excised, or parent commit)
      solution/             # the repo tree with the correct code in place
      verifier/             # test files + conftest ancestors + run.sh (copied over the workdir by the harness)
      goldenSolution.md     # LLM-authored rationale explaining why the solution is correct
      evidence/             # machine-generated validation artifacts
        verdict.json        # the harness verdict (valid/invalid + reasons). Never hand-edited
        fail_before.log     # console output of the verifier against input/
        fail_before.report.json
        pass_after.log      # console output of the verifier against solution/
        pass_after.report.json
        collateral.log      # console output of the collateral run
        collateral.report.json
        collateral.json     # collateral-damage comparison
        determinism.json    # repeat-run comparison
```

Task IDs are prefixed `exc-` (excision: function body removed) or `hist-` (history: a real commit's change).

## What is committed

See `.gitignore` for the policy. The committed deliverable is the repo-root `tasks.json` (the final selected set) plus the selected task folders. Surplus task folders and other repos' trees are not part of the committed set.

## Not here

- Root `tasks.json` (the final 10 selected tasks): repo root
- Selection logic and `selection.json`: `output/<repo>/tasks/`
- Task generation code: `pipeline/tasks/`
- Standalone validator: `python -m pipeline.validate <task_dir>`
