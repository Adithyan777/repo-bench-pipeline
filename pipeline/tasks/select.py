"""Final task selection (docs/pipeline-3-tasks.md).

Pick exactly ``selection.total_tasks`` VALID tasks with a final instruction, honoring the
hard quotas (``min_history`` / ``max_excision`` / ``max_netnew`` / ``min_distinct_modules``)
and, softly, the difficulty spread. Writes the repo-root ``tasks.json`` + ``selection.json``
(why each eligible task was or was not picked). Deterministic: ranked by a total
tie-broken key; unmeetable constraints raise ``SelectionInfeasible``, never fewer tasks.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from pipeline.config import DEFAULT, Config

_TYPES = ("history", "excision", "net-new")


class SelectionInfeasible(RuntimeError):
    """Raised when the hard quotas cannot be satisfied by the eligible tasks."""


@dataclass
class Decision:
    id: str
    source_type: str
    module: str | None
    difficulty: str | None
    n_failing: int
    eligible: bool
    selected: bool
    reason: str


@dataclass
class SelectionResult:
    selected: list[dict]  # manifest entries, in final order
    decisions: list[Decision] = field(default_factory=list)
    spread: dict[str, int] = field(default_factory=dict)
    modules: list[str] = field(default_factory=list)


def _n_failing(task: dict) -> int:
    voi = task.get("verifier_on_input") or {}
    return int(voi.get("n_failing") or 0)


def _pref_key(task: dict) -> tuple:
    """Preference (best first): more failing-on-input tests, then id."""
    return (-_n_failing(task), task["id"])


def _eligible(task: dict, cfg: Config) -> tuple[bool, str]:
    if task.get("validation_status") != "VALID":
        return False, f"not-valid({task.get('validation_status')})"
    if task.get("instruction_status") != cfg.instruction.status_final:
        return False, f"instruction-{task.get('instruction_status')}"
    return True, "eligible"


def _cap(source_type: str, cfg: Config) -> int | None:
    if source_type == "excision":
        return cfg.selection.max_excision
    if source_type == "net-new":
        return cfg.selection.max_netnew
    return None  # history has a floor, not a cap


def _distinct_modules(tasks: list[dict]) -> set[str]:
    return {t.get("module") for t in tasks if t.get("module")}


def select(tasks: list[dict], config: Config = DEFAULT) -> SelectionResult:
    ranked = sorted(tasks, key=_pref_key)
    eligible: list[dict] = []
    decisions: dict[str, Decision] = {}
    for t in ranked:
        ok, why = _eligible(t, config)
        decisions[t["id"]] = Decision(
            id=t["id"],
            source_type=t.get("source_type", ""),
            module=t.get("module"),
            difficulty=t.get("difficulty"),
            n_failing=_n_failing(t),
            eligible=ok,
            selected=False,
            reason=why,
        )
        if ok:
            eligible.append(t)

    _check_feasible(eligible, config)
    chosen = _greedy(eligible, config)
    chosen = _ensure_module_diversity(chosen, eligible, config)
    chosen = _improve_spread(chosen, eligible, config)

    chosen_ids = {t["id"] for t in chosen}
    for t in eligible:
        d = decisions[t["id"]]
        if t["id"] in chosen_ids:
            d.selected, d.reason = True, "selected"
        else:
            d.reason = "surplus-to-quota"
    ordered = sorted(chosen, key=_pref_key)
    spread: dict[str, int] = {}
    for t in ordered:
        spread[t.get("difficulty") or "unlabeled"] = (
            spread.get(t.get("difficulty") or "unlabeled", 0) + 1
        )
    return SelectionResult(
        selected=ordered,
        decisions=[decisions[i] for i in sorted(decisions)],
        spread=dict(sorted(spread.items())),
        modules=sorted(_distinct_modules(ordered)),
    )


def _check_feasible(eligible: list[dict], config: Config) -> None:
    sel = config.selection
    by_type: dict[str, list[dict]] = {ty: [] for ty in _TYPES}
    for t in eligible:
        by_type.setdefault(t.get("source_type", ""), []).append(t)
    n_hist = len(by_type.get("history", []))
    e_max = min(len(by_type.get("excision", [])), sel.max_excision)
    n_max = min(len(by_type.get("net-new", [])), sel.max_netnew)
    if len(eligible) < sel.total_tasks:
        raise SelectionInfeasible(
            f"only {len(eligible)} eligible VALID+final tasks, need {sel.total_tasks}"
        )
    if n_hist < sel.min_history:
        raise SelectionInfeasible(
            f"only {n_hist} eligible history tasks, need >= {sel.min_history}"
        )
    if n_hist + e_max + n_max < sel.total_tasks:
        raise SelectionInfeasible(
            f"quota caps leave at most {n_hist + e_max + n_max} selectable "
            f"(history {n_hist}, excision<= {e_max}, net-new<= {n_max}), "
            f"need {sel.total_tasks}"
        )
    reachable = len({t.get("module") for t in eligible if t.get("module")})
    if reachable < sel.min_distinct_modules:
        raise SelectionInfeasible(
            f"eligible tasks span only {reachable} modules, need >= {sel.min_distinct_modules}"
        )


def _counts(tasks: list[dict]) -> dict[str, int]:
    counts = {ty: 0 for ty in _TYPES}
    for t in tasks:
        counts[t.get("source_type", "")] = counts.get(t.get("source_type", ""), 0) + 1
    return counts


def _greedy(eligible: list[dict], config: Config) -> list[dict]:
    """Reserve the history floor first, then fill by preference across types within the
    excision/net-new caps."""
    sel = config.selection
    ranked = sorted(eligible, key=_pref_key)
    history = [t for t in ranked if t.get("source_type") == "history"]
    chosen = history[: sel.min_history]
    chosen_ids = {t["id"] for t in chosen}
    counts = _counts(chosen)
    for t in ranked:
        if len(chosen) >= sel.total_tasks:
            break
        if t["id"] in chosen_ids:
            continue
        cap = _cap(t.get("source_type", ""), config)
        if cap is not None and counts.get(t.get("source_type", ""), 0) >= cap:
            continue
        chosen.append(t)
        chosen_ids.add(t["id"])
        counts[t.get("source_type", "")] = counts.get(t.get("source_type", ""), 0) + 1
    return chosen


def _caps_ok(tasks: list[dict], config: Config) -> bool:
    sel = config.selection
    c = _counts(tasks)
    return (
        c.get("excision", 0) <= sel.max_excision
        and c.get("net-new", 0) <= sel.max_netnew
        and c.get("history", 0) >= sel.min_history
    )


def _ensure_module_diversity(
    chosen: list[dict], eligible: list[dict], config: Config
) -> list[dict]:
    """Swap same-module duplicates for unselected tasks in unseen modules until
    >= min_distinct_modules, minimising preference loss."""
    sel = config.selection
    need = sel.min_distinct_modules
    chosen = list(chosen)
    guard = 0
    while len(_distinct_modules(chosen)) < need and guard < len(eligible) + need:
        guard += 1
        chosen_ids = {t["id"] for t in chosen}
        seen_modules = _distinct_modules(chosen)
        # candidates that would ADD a new module, best preference first
        adders = sorted(
            (
                t
                for t in eligible
                if t["id"] not in chosen_ids and t.get("module") not in seen_modules
            ),
            key=_pref_key,
        )
        swapped = False
        for cand in adders:
            # Drop the worst-preference duplicated-module task; caps + history floor stay valid.
            for drop in sorted(chosen, key=_pref_key, reverse=True):
                dup = [t for t in chosen if t.get("module") == drop.get("module")]
                if len(dup) < 2:
                    continue  # dropping it would lose that module entirely
                trial = [t for t in chosen if t["id"] != drop["id"]] + [cand]
                if _caps_ok(trial, config):
                    chosen = trial
                    swapped = True
                    break
            if swapped:
                break
        if not swapped:
            raise SelectionInfeasible(
                f"cannot reach {need} distinct modules without violating quotas"
            )
    return chosen


def _spread_cost(tasks: list[dict], config: Config) -> int:
    target = config.difficulty.target_spread
    have: dict[str, int] = {}
    for t in tasks:
        key = t.get("difficulty") or "unlabeled"
        have[key] = have.get(key, 0) + 1
    return sum(abs(target.get(k, 0) - have.get(k, 0)) for k in set(target) | set(have))


def _improve_spread(chosen: list[dict], eligible: list[dict], config: Config) -> list[dict]:
    """Soft objective: swap toward the target difficulty spread while keeping every hard
    constraint; deterministic (preference tie-break), stops when no swap lowers the cost."""
    chosen = list(chosen)
    improved = True
    guard = 0
    while improved and guard < 100:
        guard += 1
        improved = False
        best_cost = _spread_cost(chosen, config)
        chosen_ids = {t["id"] for t in chosen}
        outsiders = sorted((t for t in eligible if t["id"] not in chosen_ids), key=_pref_key)
        for cand in outsiders:
            for drop in sorted(chosen, key=_pref_key, reverse=True):
                if drop.get("difficulty") == cand.get("difficulty"):
                    continue
                trial = [t for t in chosen if t["id"] != drop["id"]] + [cand]
                if not _caps_ok(trial, config):
                    continue
                if len(_distinct_modules(trial)) < config.selection.min_distinct_modules:
                    continue
                if _spread_cost(trial, config) < best_cost:
                    chosen, improved = trial, True
                    break
            if improved:
                break
    return chosen


# --- manifest I/O -------------------------------------------------------------


def _source_ref(task: dict) -> str:
    prov = task.get("provenance") or {}
    if prov.get("type") == "history":
        return prov.get("commit", "")
    if prov.get("type") == "excision":
        return prov.get("target", "")
    return task.get("module") or ""


def root_entry(task: dict, repo: str, config: Config) -> dict:
    """Repo-root tasks.json record: id, title, source type, module, difficulty, provenance,
    verifier command, validation status, path, source_ref."""
    return {
        "id": task["id"],
        "title": task["title"],
        "source_type": task["source_type"],
        "module": task.get("module"),
        "difficulty": task.get("difficulty"),
        "provenance": task["provenance"],
        "source_ref": _source_ref(task),
        "verifier_cmd": task["verifier_cmd"],
        "validation_status": task["validation_status"],
        "path": f"{config.tasks.tasks_root}/{repo}/{task['path']}",
    }


def run_selection(
    repo: str,
    repo_manifest: Path,
    config: Config = DEFAULT,
    root_dir: Path = Path("."),
    summary_dir: Path | None = None,
) -> tuple[Path, Path, SelectionResult]:
    """Read the manifest, select the final set, write root tasks.json (``root_dir``) +
    selection.json (``summary_dir``, feeds REPORT.md). Returns (root_tasks_json,
    selection_json, result)."""
    manifest = json.loads(Path(repo_manifest).read_text())
    tasks = manifest.get("tasks", [])
    result = select(tasks, config)
    root_tasks = Path(root_dir) / "tasks.json"
    root_tasks.write_text(
        json.dumps(
            {"repo": repo, "tasks": [root_entry(t, repo, config) for t in result.selected]},
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    summary_dir = Path(summary_dir) if summary_dir is not None else Path(repo_manifest).parent
    summary_dir.mkdir(parents=True, exist_ok=True)
    selection = summary_dir / "selection.json"
    selection.write_text(
        json.dumps(
            {
                "repo": repo,
                "total": config.selection.total_tasks,
                "quotas": {
                    "min_history": config.selection.min_history,
                    "max_excision": config.selection.max_excision,
                    "max_netnew": config.selection.max_netnew,
                    "min_distinct_modules": config.selection.min_distinct_modules,
                },
                "target_spread": config.difficulty.target_spread,
                "achieved_spread": result.spread,
                "distinct_modules": result.modules,
                "counts": _counts(result.selected),
                "selected": [t["id"] for t in result.selected],
                "decisions": [d.__dict__ for d in result.decisions],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return root_tasks, selection, result
