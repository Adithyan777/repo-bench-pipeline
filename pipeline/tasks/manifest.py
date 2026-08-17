"""tasks.json writer. ``validation_status`` is READ from each task's
evidence/verdict.json -- never hand-set."""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.config import DEFAULT, Config


def task_entry(task_dir: Path, config: Config = DEFAULT) -> dict:
    task = json.loads((task_dir / config.tasks.task_json).read_text())
    verdict_path = task_dir / config.harness.evidence_dirname / config.harness.verdict_filename
    if verdict_path.is_file():
        verdict = json.loads(verdict_path.read_text())
        status = "VALID" if verdict.get("valid") else "INVALID"
        reasons = verdict.get("reasons", [])
    else:
        status, reasons = "UNVALIDATED", []
    prov = task["provenance"]
    target = prov.get("target", "")
    module = task.get("module") or (
        ".".join(target.split(".")[:-1]) if target else (prov.get("modules") or [None])[0]
    )
    return {
        "id": task["id"],
        "title": task["title"],
        "source_type": prov["type"],
        "module": module,  # primary touched module, never null for a built task
        "modules": task.get("modules") or prov.get("modules") or ([module] if module else []),
        "difficulty": task.get("difficulty"),
        "difficulty_status": task.get("difficulty_status"),
        "instruction_status": task.get("instruction_status"),
        "provenance": task["provenance"],
        "verifier_cmd": task["verifier_cmd"],
        "verifier_on_input": task.get("verifier_on_input"),  # {exit_code, n_failing, n_passing}
        "validation_status": status,
        "validation_reasons": reasons,
        "path": task_dir.name,
    }


def write_manifest(repo_tasks_dir: Path, config: Config = DEFAULT) -> Path:
    """tasks/<repo>/tasks.json over every task folder present (sorted by id)."""
    task_dirs = sorted(
        p for p in repo_tasks_dir.iterdir() if p.is_dir() and (p / config.tasks.task_json).is_file()
    )
    entries = sorted((task_entry(d, config) for d in task_dirs), key=lambda e: e["id"])
    out = repo_tasks_dir / config.tasks.manifest_filename
    out.write_text(
        json.dumps({"repo": repo_tasks_dir.name, "tasks": entries}, indent=2, sort_keys=True) + "\n"
    )
    return out
