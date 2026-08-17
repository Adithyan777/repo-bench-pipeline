"""REPORT.md production.

``collect()`` aggregates output/<repo>/ artifacts (incl. the runner's report_data.json)
into ``report_summary.json``; ``render()`` writes the six-section REPORT.md with tables
auto-filled and narrative drafted by one cached BIG call, marked ``AUTHOR`` for a human.
Missing artifacts omit their rows; nothing is invented.
"""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.config import DEFAULT, Config

DRAFT_STEP = "report.draft_sections"

_SECTIONS = (
    ("broken", "1. What was broken and how the pipeline fixes each class"),
    ("decisions", "2. Design decisions & trade-offs"),
    ("selection", "3. Task-candidate selection: mined, rejected, and why"),
    ("run", "4. How to run everything"),
    ("scale", "5. Scale: what breaks at 100 repos"),
    ("gaps", "6. Honest gaps"),
)

_DRAFT_SCHEMA = {
    "type": "object",
    "properties": {s[0]: {"type": "string"} for s in _SECTIONS},
    "required": [s[0] for s in _SECTIONS],
}


def _load(path: Path) -> dict:
    try:
        return json.loads(Path(path).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _jsonl(path: Path) -> list[dict]:
    if not Path(path).is_file():
        return []
    out = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


# --- collection ---------------------------------------------------------------


def collect(run_dir: Path, config: Config = DEFAULT) -> dict:
    run_dir = Path(run_dir)
    hy = run_dir / "hygiene"
    kn = run_dir / "knowledge"
    tk = run_dir / "tasks"
    audit = run_dir / "audit"
    existing = _load(run_dir / config.report.report_data_filename)

    detect = _load(hy / "detect.json")
    pin = _load(hy / "pin.json")
    build = _load(hy / "build.json")
    baseline = _load(hy / "baseline.json")
    testgen = _load(hy / "testgen.json")
    lint = _load(hy / "lint.json")

    graph = _load(kn / config.knowledge.graph_filename)
    gverify = _load(kn / config.knowledge.verification_filename)
    okf = _load(kn / config.okf.manifest_filename)
    okfv = _load(kn / config.okf.verification_filename)

    candidates = _load(tk / config.tasks.candidates_filename)
    hcandidates = _load(tk / config.tasks.history_candidates_filename)
    selection = _load(tk / "selection.json")

    expected = {
        "detect": hy / "detect.json",
        "build": hy / "build.json",
        "baseline": hy / "baseline.json",
        "testgen": hy / "testgen.json",
        "lint": hy / "lint.json",
        "repo_graph": kn / config.knowledge.graph_filename,
        "graph_verification": kn / config.knowledge.verification_filename,
        "okf": kn / config.okf.manifest_filename,
        "okf_verification": kn / config.okf.verification_filename,
        "excision_candidates": tk / config.tasks.candidates_filename,
        "history_candidates": tk / config.tasks.history_candidates_filename,
        "selection": tk / "selection.json",
    }
    missing = sorted(name for name, path in expected.items() if not path.is_file())

    data: dict = {
        "repo": run_dir.name,
        "base_sha": existing.get("base_sha", ""),
        "missing_artifacts": missing,
        "hygiene": {
            "packaging_style": detect.get("packaging_style"),
            "python_version": detect.get("python_version"),
            "test_framework": detect.get("test_framework"),
            "extras_used": detect.get("extras") or detect.get("extras_used"),
            "dropped_extras": pin.get("dropped_extras") or detect.get("dropped_extras") or [],
            "unresolved_imports": pin.get("unresolved_imports") or [],
            "image_tag": build.get("image_tag"),
            "image_digest": build.get("image_digest"),
            "baseline": {
                "counts": baseline.get("counts"),
                "quarantined": baseline.get("quarantined") or [],
                "classifications": baseline.get("classifications") or [],
                "testgen_refreshed": baseline.get("testgen_refreshed", False),
            },
            "testgen": _testgen_summary(testgen),
            "lint": _lint_summary(lint),
        },
        "knowledge": {
            "graph": (graph.get("metadata") or {}).get("counts"),
            "source_module_count": (graph.get("metadata") or {}).get("source_module_count"),
            "graph_verification": _graph_verify_summary(gverify),
            "okf": {
                "counts": okf.get("counts"),
                "pages_verified": okfv.get("pages_verified"),
                "pages_draft": okfv.get("pages_draft"),
                "semantic_precision": okfv.get("precision_by_claim"),
                "by_construction": okfv.get("by_construction"),
                "unchecked_claim_kinds": okfv.get("unchecked_claim_kinds"),
                "conformance": okfv.get("conformance"),
            },
        },
        "tasks": _tasks_summary(existing, candidates, hcandidates, selection),
        "stages": existing.get("stages", {}),
        "llm": _llm_summary(_load(audit / "llm_usage.json")),
        "agents": _agents_summary(_jsonl(audit / "agent_actions.jsonl")),
    }
    return data


def _testgen_summary(testgen: dict) -> dict:
    if testgen.get("enabled") is False:
        return {"enabled": False}
    counts = testgen.get("counts") or {}
    return {
        "modules_selected": testgen.get("modules_selected"),
        "targets": testgen.get("targets"),
        "modules_kept": counts.get("modules_kept"),
        "functions_kept": counts.get("functions_kept"),
        "functions_weak": counts.get("functions_weak"),
        "mutants_killed": counts.get("mutants_killed"),
        "mutants_valid": counts.get("mutants_valid"),
        "mutation_score": (
            round(counts["mutants_killed"] / counts["mutants_valid"], 3)
            if counts.get("mutants_valid")
            else None
        ),
        "suite_after": testgen.get("suite_after"),
    }


def _lint_summary(lint: dict) -> dict:
    if not lint or lint.get("enabled") is False:
        return {"enabled": lint.get("enabled", None)}
    return {
        "config_created": lint.get("config_created"),
        "files_changed": len(lint.get("files_changed") or []),
        "unfixable": len(lint.get("unfixable") or []),
        "noqa_files": len(lint.get("noqa") or {}),
        "codes": lint.get("codes") or {},
        "clean": lint.get("clean"),
        "regressed": lint.get("regressed", False),
        "image_rebuilt": lint.get("image_rebuilt"),
    }


def _graph_verify_summary(gv: dict) -> dict:
    by_type = gv.get("by_edge_type") or {}
    precision = {et: v.get("precision") for et, v in by_type.items() if isinstance(v, dict)}
    return {
        "sample_size": gv.get("sample_size"),
        "precision_by_edge_type": precision,
        "mismatches": len(gv.get("mismatches") or []),
        "symbol_existence": gv.get("symbol_existence"),
    }


def _tasks_summary(existing: dict, candidates: dict, hcandidates: dict, selection: dict) -> dict:
    t = dict(existing.get("tasks") or {})
    t["excision_funnel_counts"] = candidates.get("counts")
    t["history_funnel_counts"] = hcandidates.get("counts")
    t["selection"] = (
        {
            "selected": selection.get("selected"),
            "counts": selection.get("counts"),
            "achieved_spread": selection.get("achieved_spread"),
            "target_spread": selection.get("target_spread"),
            "distinct_modules": selection.get("distinct_modules"),
        }
        if selection
        else t.get("select")
    )
    return t


def _llm_summary(usage: dict) -> dict:
    by_step = {
        k: v.get("total_tokens", 0)
        for k, v in usage.items()
        if k != "_total" and isinstance(v, dict)
    }
    return {
        "total_tokens": (usage.get("_total") or {}).get("total_tokens"),
        "reasoning_tokens": (usage.get("_total") or {}).get("reasoning_tokens"),
        "by_step": dict(sorted(by_step.items(), key=lambda kv: -kv[1])),
    }


def _agents_summary(actions: list[dict]) -> dict:
    by_stage: dict[str, int] = {}
    outcomes: dict[str, int] = {}
    for a in actions:
        by_stage[a.get("stage", "?")] = by_stage.get(a.get("stage", "?"), 0) + 1
        outcomes[a.get("outcome", "?")] = outcomes.get(a.get("outcome", "?"), 0) + 1
    return {
        "runs": len(actions),
        "by_stage": dict(sorted(by_stage.items())),
        "outcomes": dict(sorted(outcomes.items())),
    }


# --- rendering ----------------------------------------------------------------


def _cell(value) -> str:
    """Render a table cell; None/empty never shows as a bare 'None'."""
    if value is None or value == "":
        return "-"
    return str(value)


def _table(headers: list[str], rows: list[list]) -> str:
    if not rows:
        return "_(no data)_\n"
    head = "| " + " | ".join(headers) + " |\n"
    sep = "| " + " | ".join("---" for _ in headers) + " |\n"
    body = "".join("| " + " | ".join(_cell(c) for c in r) + " |\n" for r in rows)
    return head + sep + body


def _author(note: str) -> str:
    return f"<!-- AUTHOR: {note} -->\n"


def render(data: dict, config: Config = DEFAULT, narrative: dict | None = None) -> str:
    narrative = narrative or {}
    hy, kn, tk = data["hygiene"], data["knowledge"], data["tasks"]
    lines: list[str] = []
    a = lines.append
    a(f"# REPORT — {data['repo']}\n")
    a(
        "Tables in this report are generated from `output/"
        f"{data['repo']}/{config.report.summary_filename}`. Narrative paragraphs are DRAFTED "
        "and marked with `AUTHOR` comments for a human to finish.\n"
    )
    a(f"Base commit (original HEAD, P3 mines at/under this): `{data['base_sha']}`\n")
    if data.get("missing_artifacts"):
        a(
            "\n> Note: the following expected artifacts were not present when this report was "
            f"built (their rows read `-`): {', '.join(data['missing_artifacts'])}.\n"
        )

    # 1
    a(f"\n## {_SECTIONS[0][1]}\n")
    a(
        _para(
            narrative,
            "broken",
            "Summarize each class of problem the pipeline detected and "
            "the automated fix, grounded in the tables below.",
        )
    )
    a("\n**Environment & hygiene**\n\n")
    a(
        _table(
            ["Aspect", "Value"],
            [
                ["Packaging style", hy["packaging_style"]],
                ["Python version", hy["python_version"]],
                ["Test framework", hy["test_framework"]],
                ["Extras folded into lock", hy["extras_used"]],
                ["Dropped (unresolvable) extras", hy["dropped_extras"]],
                ["Unresolved inferred imports", hy["unresolved_imports"]],
                ["Image tag", hy["image_tag"]],
                ["Image digest", hy["image_digest"]],
                ["Baseline", _fmt(hy["baseline"]["counts"])],
                ["Quarantined tests", len(hy["baseline"]["quarantined"])],
            ],
        )
    )
    a("\n**Generated tests (mutation gate)**\n\n")
    tg = hy["testgen"]
    if tg.get("enabled") is False:
        a("_test-gen disabled for this run_\n")
    else:
        a(
            _table(
                ["Metric", "Value"],
                [
                    ["Modules selected", tg.get("modules_selected")],
                    ["Functions targeted", tg.get("targets")],
                    ["Functions kept", tg.get("functions_kept")],
                    ["Functions weak/dropped", tg.get("functions_weak")],
                    [
                        "Mutants killed / valid",
                        f"{tg.get('mutants_killed')}/{tg.get('mutants_valid')}",
                    ],
                    ["Mutation score", tg.get("mutation_score")],
                    ["Suite after", _fmt(tg.get("suite_after"))],
                ],
            )
        )
    a("\n**Lint / format**\n\n")
    ln = hy["lint"]
    if ln.get("enabled") is False:
        a("_lint disabled for this run_\n")
    else:
        a(
            _table(
                ["Metric", "Value"],
                [
                    ["pyproject created", ln.get("config_created")],
                    ["Files changed", ln.get("files_changed")],
                    ["Unfixable findings", ln.get("unfixable")],
                    ["Files given noqa", ln.get("noqa_files")],
                    ["Codes", _fmt(ln.get("codes"))],
                    ["ruff clean in container", ln.get("clean")],
                    ["Reverted (regression)", ln.get("regressed")],
                ],
            )
        )

    a("\n**Knowledge layer (accuracy)**\n\n")
    gv = kn.get("graph_verification") or {}
    okf = kn.get("okf") or {}
    byc = (okf.get("by_construction") or {}).get("precision")
    conf = okf.get("conformance")
    conf = conf.get("conformant", conf) if isinstance(conf, dict) else conf
    a(
        _table(
            ["Metric", "Value"],
            [
                ["Source modules", kn.get("source_module_count")],
                ["Graph node/edge counts", _fmt(kn.get("graph"))],
                ["Graph edge precision", _fmt(gv.get("precision_by_edge_type"))],
                ["Graph mismatches", gv.get("mismatches")],
                [
                    "OKF pages verified / draft",
                    f"{okf.get('pages_verified')}/{okf.get('pages_draft')}",
                ],
                ["OKF semantic precision", _fmt(okf.get("semantic_precision"))],
                ["OKF by-construction (callers/link)", _fmt(byc)],
                ["OKF unchecked (prose)", _fmt(okf.get("unchecked_claim_kinds"))],
                ["OKF conformance", conf],
            ],
        )
    )
    a(
        "\n_by-construction (callers / internal links) are graph-derived and reported "
        "separately from independently re-derived semantic checks (callees / raises / "
        "side_effects)._\n"
    )

    # 2
    a(f"\n## {_SECTIONS[1][1]}\n")
    a(
        _para(
            narrative,
            "decisions",
            "Explain the key automated-vs-manual decisions and "
            "trade-offs (LLM proposes / code disposes; mutation gate; "
            "strict right-reason classifier; determinism from gates).",
        )
    )

    # 3
    a(f"\n## {_SECTIONS[2][1]}\n")
    a(
        _para(
            narrative,
            "selection",
            "Describe what was mined and rejected and on what grounds, "
            "citing the funnel counts and the final selection below.",
        )
    )
    a("\n**Excision funnel** (every function considered → status/reject reason)\n\n")
    a(_counts_table(tk.get("excision_funnel_counts")))
    a("\n**History funnel** (every commit considered → status/reject reason)\n\n")
    a(_counts_table(tk.get("history_funnel_counts")))
    a("\n**Validation**\n\n")
    val = tk.get("validate") or {}
    a(
        _table(
            ["Metric", "Value"],
            [
                ["Tasks validated", val.get("tasks")],
                ["VALID", val.get("valid")],
            ],
        )
    )
    a("\n**Instruction authoring**\n\n")
    ins = tk.get("instruct") or {}
    a(
        _table(
            ["Metric", "Value"],
            [
                ["Tasks", ins.get("tasks")],
                ["Final", ins.get("final")],
                ["Failed", ins.get("failed")],
                ["Regenerations", ins.get("regenerations")],
                ["Difficulty spread", _fmt(ins.get("difficulty_spread"))],
            ],
        )
    )
    a("\n**Final selection (the 10)**\n\n")
    sel = tk.get("selection") or {}
    spread = f"{_fmt(sel.get('achieved_spread'))} (target {_fmt(sel.get('target_spread'))})"
    a(
        _table(
            ["Metric", "Value"],
            [
                ["Selected", _fmt(sel.get("counts"))],
                ["Difficulty spread", spread],
                ["Distinct modules", _fmt(sel.get("distinct_modules"))],
            ],
        )
    )
    a("\nSelected task ids: " + ", ".join(f"`{i}`" for i in (sel.get("selected") or [])) + "\n")

    # 4
    a(f"\n## {_SECTIONS[3][1]}\n")
    a(_run_instructions(data["repo"]))

    # 5
    a(f"\n## {_SECTIONS[4][1]}\n")
    a("\n**Measured cost of this run**\n\n")
    llm = data["llm"]
    a(
        _table(
            ["Metric", "Value"],
            [
                ["Total LLM tokens", llm.get("total_tokens")],
                ["Reasoning tokens", llm.get("reasoning_tokens")],
                ["Agent runs", data["agents"]["runs"]],
            ],
        )
    )
    a("\n**LLM tokens by step**\n\n")
    a(_table(["Step", "Tokens"], [[k, v] for k, v in (llm.get("by_step") or {}).items()]))
    a("\n**Per-stage timing (s)**\n\n")
    timing = [
        [k, v.get("duration_s", "-"), v.get("skipped")] for k, v in sorted(data["stages"].items())
    ]
    a(_table(["Stage", "Duration", "Skipped"], timing))
    a(
        _para(
            narrative,
            "scale",
            "Given the timings/tokens above, describe what breaks at 100 "
            "repos and what you would build differently (job queue, image "
            "registry, triage, human-review sampling).",
        )
    )

    # 6
    a(f"\n## {_SECTIONS[5][1]}\n")
    a(_para(narrative, "gaps", "State the de-scoped/known-weak items with next steps."))
    a(_gaps_checklist())
    return "".join(lines)


def _para(narrative: dict, key: str, note: str) -> str:
    text = (narrative or {}).get(key)
    if text:
        return f"\n{text}\n\n{_author('review and edit the drafted paragraph above.')}"
    return "\n" + _author(f"WRITE: {note}")


def _fmt(value) -> str:
    if isinstance(value, dict):
        return ", ".join(f"{k}={v}" for k, v in value.items()) or "-"
    if isinstance(value, list):
        return ", ".join(str(v) for v in value) or "-"
    return "-" if value is None else str(value)


def _counts_table(counts: dict | None) -> str:
    if not counts:
        return "_(no data)_\n"
    return _table(["Status / reject reason", "Count"], [[k, v] for k, v in counts.items()])


def _run_instructions(repo: str) -> str:
    return (
        "\nExact commands (fresh clone). See README for full detail.\n\n"
        "```bash\n"
        "# 0. setup\n"
        "git clone https://github.com/Adithyan777/repo-bench-pipeline.git && cd repo-bench-pipeline\n"
        "uv venv --python 3.12 .venv\n"
        "uv pip install --python .venv/bin/python -r requirements-dev.txt\n"
        "cp .env.example .env    # add LLM_BASE_URL + LLM_API_KEY\n\n"
        "# 1. full pipeline (hygiene -> knowledge -> tasks -> select -> report)\n"
        "./run.sh https://github.com/mahmoud/glom --fresh\n\n"
        "# 2. per stage\n"
        "./run.sh <repo> --stage hygiene\n"
        "./run.sh <repo> --stage knowledge\n"
        "./run.sh <repo> --stage tasks\n\n"
        "# 3. run the documented container test twice (acceptance)\n"
        "./run.sh <repo> --stage hygiene --verify-twice\n\n"
        "# 4. validate a selected task standalone (paths from tasks.json)\n"
        "python -m pipeline.validate tasks/" + repo + "/<task_id>\n\n"
        "# 5. the pipeline's own tests\n"
        ".venv/bin/python -m pytest\n"
        ".venv/bin/python -m pytest -m slow\n"
        ".venv/bin/ruff check .\n"
        "```\n"
    )


def _gaps_checklist() -> str:
    items = [
        "Net-new tasks are not generated; history + excision fill the 10.",
        "`apt-get git` in git-versioned images makes those images not byte-reproducible "
        "(env fix so the version resolves; digests are recorded, not gated).",
        "OKF `raises`/`side_effects` precision is conservative (implicit/under-claimed "
        "exceptions stay `draft`); `callers`/internal links are true-by-construction, not "
        "independent evidence.",
        "`test_map` excludes doctests.",
        "Test-gen coverage-theater guard: whole-file zero-kill drop (no per-test trimming).",
        "The test-gen run on minidump was launched twice; only the real run's tokens count.",
        "Verifier visibility defaults to `visible` (hack-proof via harness re-copy).",
        "History new-symbol features rely on the getattr convention; pure new-symbol "
        "imports on `input/` remain INVALID by the strict classifier's design.",
        "Old-commit dependency drift is recorded as `env-drift`, never re-locked.",
        "The collection-broken baseline path (one repair → treat as no tests) is not "
        "implemented — no in-scope repo hit it; the inert flags for it were removed.",
        "The lint step rebuilds the image and runs the suite twice to prove the linted "
        "tree still builds green; a change that regresses a test reverts the whole step. "
        "On glom this fires: its `test_error.py::*_stack` tests assert exact rendered "
        "source lines, so any edit to `core.py` (fixes or formatting) breaks 7 tests; the "
        "repo therefore ships un-linted with all findings recorded in `lint.json`.",
        "Test-gen drops a module when the agent spends its turn budget reading a large "
        "module without writing tests (glom.core, glom.grouping); no retry with a larger "
        "budget is attempted automatically.",
    ]
    return (
        "\n"
        + "".join(f"- {i}\n" for i in items)
        + _author("expand each gap with a concrete next step.")
    )


# --- narrative drafting -------------------------------------------------------


def draft_narrative(
    data: dict, llm, config: Config = DEFAULT, decisions: dict | None = None
) -> dict:
    """One BIG call drafting the six section paragraphs; cached by data-summary hash."""
    import hashlib

    decisions = {} if decisions is None else decisions
    compact = json.dumps(_compact(data), sort_keys=True)[: config.report.draft_max_chars]
    key = hashlib.sha256((DRAFT_STEP + "\n" + compact).encode()).hexdigest()[
        : config.tasks.content_key_chars
    ]
    if key in decisions:
        return decisions[key]
    prompt = (
        "You are drafting SHORT narrative paragraphs (2-4 sentences each) for a technical "
        "REPORT.md about an automated benchmark-task pipeline. Ground every sentence in the "
        "JSON metrics below; do not invent numbers. These are DRAFTS a human will edit. "
        "Return one paragraph per section key.\n\n"
        f"Metrics:\n{compact}\n"
    )
    result = llm.complete_json(DRAFT_STEP, [{"role": "user", "content": prompt}], _DRAFT_SCHEMA)
    decisions[key] = result
    return result


def _compact(data: dict) -> dict:
    """A small, drafter-friendly slice of the full report_data."""
    return {
        "repo": data["repo"],
        "hygiene": {
            "packaging_style": data["hygiene"]["packaging_style"],
            "baseline_counts": data["hygiene"]["baseline"]["counts"],
            "quarantined": len(data["hygiene"]["baseline"]["quarantined"]),
            "testgen": data["hygiene"]["testgen"],
            "lint": data["hygiene"]["lint"],
        },
        "knowledge": data["knowledge"],
        "tasks": {
            "validate": data["tasks"].get("validate"),
            "instruct": data["tasks"].get("instruct"),
            "selection": data["tasks"].get("selection"),
            "excision_funnel_counts": data["tasks"].get("excision_funnel_counts"),
            "history_funnel_counts": data["tasks"].get("history_funnel_counts"),
        },
        "llm": data["llm"],
    }


# --- top-level ----------------------------------------------------------------


def build(
    run_dir: Path,
    config: Config = DEFAULT,
    llm=None,
    draft: bool | None = None,
) -> tuple[Path, Path]:
    """Write output/<repo>/report_summary.json + output/<repo>/REPORT.md; return their paths.

    The generated report lives in the run dir; the repo-root REPORT.md is hand-maintained
    (seeded from a generated one) so later runs on other repos never overwrite it."""
    run_dir = Path(run_dir)
    data = collect(run_dir, config)
    data_path = run_dir / config.report.summary_filename
    data_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")

    narrative = None
    do_draft = config.report.draft_narrative if draft is None else draft
    if do_draft and llm is not None:
        dpath = run_dir / config.report.decisions_filename
        decisions = _load(dpath)
        narrative = draft_narrative(data, llm, config, decisions)
        dpath.write_text(json.dumps(decisions, indent=2, sort_keys=True) + "\n")

    md = render(data, config, narrative)
    md_path = run_dir / config.report.report_md_filename
    md_path.write_text(md)
    return data_path, md_path
