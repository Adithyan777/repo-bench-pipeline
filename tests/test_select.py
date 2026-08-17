"""Final-selection tests: quotas, diversity, difficulty spread, determinism, infeasible
cases, and the repo-root tasks.json / selection.json writers. Pure, no docker/LLM."""

from __future__ import annotations

import json

import pytest

from pipeline.config import Config
from pipeline.tasks.select import (
    SelectionInfeasible,
    root_entry,
    run_selection,
    select,
)

MODS = ["a", "b", "c", "d", "e", "f", "g"]


def _task(tid, source_type, module, difficulty, n_failing, valid="VALID", instr="final"):
    return {
        "id": tid,
        "title": tid.replace("-", " "),
        "source_type": source_type,
        "module": module,
        "modules": [module],
        "difficulty": difficulty,
        "verifier_on_input": {"n_failing": n_failing, "n_passing": 0, "exit_code": 1},
        "validation_status": valid,
        "instruction_status": instr,
        "provenance": {
            "type": source_type,
            "commit": "abc123" if source_type == "history" else "",
            "target": module + ".fn" if source_type == "excision" else "",
        },
        "verifier_cmd": f"python -m pytest -q {tid}",
        "path": tid,
    }


def _healthy_pool():
    tasks = []
    for i in range(10):
        tasks.append(
            _task(
                f"hist-{i:02d}", "history", MODS[i % 7], ["easy", "medium", "hard"][i % 3], 10 - i
            )
        )
    for i in range(5):
        tasks.append(_task(f"exc-{i}", "excision", MODS[i % 7], ["medium", "hard"][i % 2], 8 - i))
    for i in range(2):
        tasks.append(_task(f"net-{i}", "net-new", MODS[i % 7], "medium", 3))
    return tasks


def test_selects_exactly_ten_respecting_quotas():
    r = select(_healthy_pool(), Config())
    assert len(r.selected) == 10
    counts = {
        ty: sum(1 for t in r.selected if t["source_type"] == ty)
        for ty in ("history", "excision", "net-new")
    }
    assert counts["history"] >= 4
    assert counts["excision"] <= 4
    assert counts["net-new"] <= 2
    assert len(r.modules) >= 4


def test_only_valid_final_tasks_are_eligible():
    pool = _healthy_pool()
    pool.append(_task("exc-invalid", "excision", "z", "hard", 99, valid="INVALID"))
    pool.append(_task("exc-draft", "excision", "y", "hard", 99, instr="failed"))
    r = select(pool, Config())
    ids = {t["id"] for t in r.selected}
    assert "exc-invalid" not in ids and "exc-draft" not in ids
    dec = {d.id: d for d in r.decisions}
    assert not dec["exc-invalid"].eligible and not dec["exc-draft"].eligible


def test_deterministic_regardless_of_input_order():
    pool = _healthy_pool()
    a = [t["id"] for t in select(pool, Config()).selected]
    b = [t["id"] for t in select(list(reversed(pool)), Config()).selected]
    assert a == b


def test_difficulty_spread_matches_target_when_possible():
    r = select(_healthy_pool(), Config())
    # target is {easy:2, medium:5, hard:3}; the pool can hit it exactly
    assert r.spread == {"easy": 2, "hard": 3, "medium": 5}


def test_infeasible_history_floor():
    pool = [_task(f"h{i}", "history", MODS[i], "medium", 5) for i in range(3)]
    pool += [_task(f"e{i}", "excision", MODS[i % 7], "medium", 5) for i in range(9)]
    with pytest.raises(SelectionInfeasible, match="history"):
        select(pool, Config())


def test_infeasible_module_diversity():
    pool = [_task(f"h{i}", "history", "a", "medium", 5) for i in range(6)]
    pool += [_task(f"e{i}", "excision", "a", "medium", 5) for i in range(4)]
    with pytest.raises(SelectionInfeasible, match="modules"):
        select(pool, Config())


def test_infeasible_too_few_eligible():
    pool = [_task(f"h{i}", "history", MODS[i], "medium", 5) for i in range(5)]
    with pytest.raises(SelectionInfeasible, match="eligible"):
        select(pool, Config())


def test_root_entry_has_pdf_fields():
    task = _task("hist-01", "history", "glom.core", "medium", 3)
    e = root_entry(task, "glom", Config())
    for field in (
        "id",
        "title",
        "source_type",
        "module",
        "difficulty",
        "provenance",
        "verifier_cmd",
        "validation_status",
        "path",
    ):
        assert field in e
    assert e["path"] == "tasks/glom/hist-01"
    assert e["source_ref"] == "abc123"  # commit SHA for history


def test_run_selection_writes_root_and_selection(tmp_path, monkeypatch):
    repo_tasks = tmp_path / "tasks" / "glom"
    repo_tasks.mkdir(parents=True)
    (repo_tasks / "tasks.json").write_text(json.dumps({"repo": "glom", "tasks": _healthy_pool()}))
    monkeypatch.chdir(tmp_path)
    root, sel_path, result = run_selection("glom", repo_tasks / "tasks.json", Config())
    assert root.name == "tasks.json"
    root_data = json.loads(root.read_text())
    assert len(root_data["tasks"]) == 10
    sel = json.loads(sel_path.read_text())
    assert sel["counts"]["history"] >= 4
    assert len(sel["decisions"]) == len(_healthy_pool())
    # every selected id is marked selected in decisions
    selected_ids = set(sel["selected"])
    for d in sel["decisions"]:
        assert d["selected"] == (d["id"] in selected_ids)
