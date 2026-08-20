"""Difficulty labelling (docs/pipeline-3-tasks.md): code computes features from the graph + task
diff; a batched BIG call (``p3.build.difficulty_label``) assigns easy|medium|hard with a rationale
that must cite a computed feature (string match; <= ``difficulty.max_regenerations``
retries, then ``failed``).
"""

from __future__ import annotations

import hashlib
import re

from pipeline.config import DEFAULT, Config
from pipeline.tasks.instruction import TaskFacts, mask_names

LABEL_STEP = "p3.build.difficulty_label"

LABEL_SCHEMA = {
    "type": "object",
    "properties": {
        "labels": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]},
                    "rationale": {"type": "string"},
                },
                "required": ["task_id", "difficulty", "rationale"],
            },
        }
    },
    "required": ["labels"],
}


def _name_tokens(leaf: str, min_chars: int) -> set[str]:
    parts = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", leaf).lower().split("_")
    return {p for p in parts if len(p) >= min_chars}


def features(facts: TaskFacts, graph: dict, config: Config = DEFAULT) -> dict:
    """The configured features, from the task diff and ``repo_graph.json``."""
    dc = config.difficulty
    touched = set(facts.touched_functions)
    touched_modules = {q.rsplit(".", 1)[0] for q in touched} | {
        n["id"]
        for n in graph.get("nodes", [])
        if n.get("file") in set(facts.source_files) and n["type"] == "module"
    }
    node_module = {}
    for n in graph.get("nodes", []):
        node_module[n["id"]] = n["id"] if n["type"] == "module" else n["id"].rsplit(".", 1)[0]
        if n["type"] == "method":
            node_module[n["id"]] = n["id"].rsplit(".", 2)[0]
    edges = graph.get("edges", [])
    callers = sum(1 for e in edges if e["type"] == "calls" and e["target"] in touched)
    cross = 0
    for e in edges:
        if e["type"] not in ("calls", "imports"):
            continue
        sm, tm = (
            node_module.get(e["source"], e["source"]),
            node_module.get(e["target"], e["target"]),
        )
        if sm != tm and (e["source"] in touched or e["target"] in touched):
            cross += 1
    leaf_tokens: set[str] = set()
    for q in touched:
        leaf_tokens |= _name_tokens(q.rsplit(".", 1)[-1], dc.similar_name_min_token_chars)
    similar = 0
    for n in graph.get("nodes", []):
        if n["type"] not in ("function", "method") or n["id"] in touched:
            continue
        if node_module.get(n["id"]) in touched_modules and (
            _name_tokens(n["id"].rsplit(".", 1)[-1], dc.similar_name_min_token_chars) & leaf_tokens
        ):
            similar += 1
    diff_size = sum(
        1
        for ln in facts.diff.splitlines()
        if ln[:1] in "+-" and ln[1:].strip() and not ln.startswith(("+++", "---"))
    )
    all_features = {
        "files_touched": len(facts.source_files),
        "functions_touched": len(touched),
        "callers_count": callers,
        "cross_module_edges": cross,
        "diff_size": diff_size,
        "similar_named_functions_nearby": similar,
        "test_count": len(facts.task["verifier_tests"]),
    }
    return {k: all_features[k] for k in dc.features if k in all_features}


def cites_feature(rationale: str, feats: dict) -> bool:
    """A feature is cited when its name (``_`` or spaces) appears with its value:
    ``callers_count=12``, ``callers count of 12``, ``12 callers``."""
    text = rationale.lower()
    for name, value in feats.items():
        for form in (name, name.replace("_", " ")):
            if re.search(rf"{re.escape(form)}[^.;]{{0,20}}\b{value}\b", text) or re.search(
                rf"\b{value}\b[^.;]{{0,20}}{re.escape(form)}", text
            ):
                return True
    return False


def label_prompt(items: list[tuple[TaskFacts, dict]], feedback: dict[str, str]) -> str:
    blocks = []
    for facts, feats in items:
        fb = (
            f"\nPrevious rationale rejected: {feedback[facts.task['id']]}"
            if facts.task["id"] in feedback
            else ""
        )
        blocks.append(
            f"### {facts.task['id']}\ntitle: {facts.task.get('title', '')}\n"
            f"summary: {mask_names(facts.summary, facts)}\n"
            f"contract:\n{facts.contract}\nfeatures: {feats}{fb}"
        )
    return (
        "Assign a difficulty (easy | medium | hard) for a competent engineer to each benchmark "
        "task below, from its behavior summary, contract and the computed features. The "
        "rationale (1-2 sentences) MUST cite at least one feature by name with its value "
        "(e.g. `callers_count=12`). Return one entry per task_id.\n\n" + "\n\n".join(blocks)
    )


def _key(config: Config, *parts: str) -> str:
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()[: config.tasks.content_key_chars]


def label_tasks(
    items: list[tuple[TaskFacts, dict]],
    llm,
    config: Config = DEFAULT,
    decisions: dict | None = None,
) -> dict[str, dict]:
    """task_id -> {difficulty, rationale, features, status, attempts}; batched BIG calls
    persisted by content hash."""
    dc = config.difficulty
    out: dict[str, dict] = {}
    pending: list[tuple[TaskFacts, dict, str]] = []
    for facts, feats in items:
        key = _key(
            config,
            "difficulty",
            facts.task["id"],
            facts.contract,
            facts.summary,
            repr(feats),
            config.model_for(LABEL_STEP),
        )
        if decisions is not None and key in decisions:
            out[facts.task["id"]] = {**decisions[key], "reused": True}
        else:
            pending.append((facts, feats, key))
    for start in range(0, len(pending), dc.batch_size):
        batch = pending[start : start + dc.batch_size]
        feedback: dict[str, str] = {}
        results: dict[str, dict] = {}
        for attempt in range(1, dc.max_regenerations + 2):
            todo = [(f, feats) for f, feats, _ in batch if f.task["id"] not in results]
            if not todo:
                break
            res = llm.complete_json(
                LABEL_STEP,
                [{"role": "user", "content": label_prompt(todo, feedback)}],
                LABEL_SCHEMA,
            )
            by_id = {lab["task_id"]: lab for lab in res.get("labels", [])}
            for f, feats in todo:
                lab = by_id.get(f.task["id"])
                if lab is None:
                    feedback[f.task["id"]] = "no label returned"
                    continue
                if dc.justification_must_cite_feature and not cites_feature(
                    lab["rationale"], feats
                ):
                    feedback[f.task["id"]] = "the rationale does not cite any computed feature"
                    continue
                results[f.task["id"]] = {
                    "difficulty": lab["difficulty"],
                    "rationale": lab["rationale"],
                    "features": feats,
                    "status": "final",
                    "attempts": attempt,
                }
        for f, feats, key in batch:
            rec = results.get(
                f.task["id"],
                {
                    "difficulty": None,
                    "rationale": None,
                    "features": feats,
                    "status": "failed",
                    "attempts": dc.max_regenerations + 1,
                    "issue": feedback.get(f.task["id"]),
                },
            )
            rec["key"] = key
            out[f.task["id"]] = rec
            if decisions is not None:
                decisions[key] = rec
    return out
