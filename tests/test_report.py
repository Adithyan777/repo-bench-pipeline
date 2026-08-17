"""Report builder tests: report_data completeness (all required sections/keys), the
six-section REPORT.md, robustness to missing artifacts, and the cached-draft path. No
docker; the LLM is a tiny fake so no tokens are spent."""

from __future__ import annotations

import json

from pipeline.config import Config
from pipeline.report import build as R

REQUIRED_TOP = ("repo", "base_sha", "hygiene", "knowledge", "tasks", "stages", "llm", "agents")


def _populate(run_dir):
    (run_dir / "hygiene").mkdir(parents=True)
    (run_dir / "knowledge").mkdir(parents=True)
    (run_dir / "tasks").mkdir(parents=True)
    (run_dir / "audit").mkdir(parents=True)
    w = lambda p, d: (run_dir / p).write_text(json.dumps(d))  # noqa: E731
    w(
        "report_data.json",
        {
            "base_sha": "deadbeef",
            "stages": {"build": {"duration_s": 3.1}},
            "tasks": {
                "validate": {"tasks": 12, "valid": 12},
                "instruct": {
                    "tasks": 12,
                    "final": 10,
                    "failed": 2,
                    "regenerations": 3,
                    "difficulty_spread": {"easy": 5, "medium": 4, "hard": 1},
                },
            },
        },
    )
    w(
        "hygiene/detect.json",
        {"packaging_style": "setup.py", "python_version": "3.12", "test_framework": "pytest"},
    )
    w("hygiene/pin.json", {"unresolved_imports": [], "dropped_extras": []})
    w("hygiene/build.json", {"image_tag": "bench-x", "image_digest": "sha256:aa"})
    w("hygiene/baseline.json", {"counts": {"passed": 202}, "quarantined": []})
    w(
        "hygiene/testgen.json",
        {
            "modules_selected": 3,
            "targets": 8,
            "counts": {
                "modules_kept": 3,
                "functions_kept": 4,
                "functions_weak": 0,
                "mutants_killed": 14,
                "mutants_valid": 16,
            },
        },
    )
    w(
        "hygiene/lint.json",
        {
            "config_created": True,
            "files_changed": ["a.py"],
            "unfixable": [],
            "noqa": {},
            "codes": {},
            "clean": True,
            "regressed": False,
            "image_rebuilt": True,
        },
    )
    w(
        "knowledge/repo_graph.json",
        {
            "metadata": {"counts": {"nodes": 378, "total_edges": 4727}, "source_module_count": 11},
            "nodes": [],
            "edges": [],
        },
    )
    w(
        "knowledge/graph_verification.json",
        {"sample_size": 200, "by_edge_type": {"calls": {"precision": 1.0}}, "mismatches": []},
    )
    w("knowledge/okf.json", {"counts": {"modules": 11, "function_pages": 150}})
    w(
        "knowledge/okf_verification.json",
        {
            "pages_verified": 105,
            "pages_draft": 45,
            "precision_by_claim": {"callees": 1.0, "raises": 0.79},
            "by_construction": {"precision": {"callers": 1.0, "link": 1.0}},
            "unchecked_claim_kinds": ["inputs", "outputs"],
            "conformance": {"conformant": True},
        },
    )
    w("tasks/candidates.json", {"counts": {"rejected:private": 196, "selected": 5}})
    w(
        "tasks/history_candidates.json",
        {"counts": {"rejected:docs-or-ci-only": 136, "shortlisted": 15}},
    )
    w(
        "tasks/selection.json",
        {
            "selected": ["hist-1", "exc-1"],
            "counts": {"history": 6, "excision": 4},
            "achieved_spread": {"easy": 5, "medium": 4, "hard": 1},
            "target_spread": {"easy": 2, "medium": 5, "hard": 3},
            "distinct_modules": ["a", "b", "c", "d"],
        },
    )
    (run_dir / "audit" / "llm_usage.json").write_text(
        json.dumps(
            {
                "_total": {"total_tokens": 724747, "reasoning_tokens": 34131},
                "p2.okf.module_purpose": {"total_tokens": 14463},
            }
        )
    )
    (run_dir / "audit" / "agent_actions.jsonl").write_text(
        json.dumps({"stage": "p1.testgen.write_tests_agent", "outcome": "kept"})
        + "\n"
        + json.dumps({"stage": "p3.build.neutrality_check_rewrite", "outcome": "rewritten"})
        + "\n"
    )


def test_report_data_has_all_required_sections(tmp_path):
    run_dir = tmp_path / "glom"
    _populate(run_dir)
    data = R.collect(run_dir, Config())
    for key in REQUIRED_TOP:
        assert key in data, key
    assert set(data["hygiene"]) >= {"testgen", "lint", "baseline", "image_digest"}
    assert set(data["knowledge"]["okf"]) >= {
        "pages_verified",
        "semantic_precision",
        "by_construction",
    }
    assert data["llm"]["total_tokens"] == 724747
    assert data["agents"]["runs"] == 2
    assert data["tasks"]["excision_funnel_counts"]["selected"] == 5


def test_render_has_six_sections(tmp_path):
    run_dir = tmp_path / "glom"
    _populate(run_dir)
    md = R.render(R.collect(run_dir, Config()), Config())
    headers = [ln for ln in md.splitlines() if ln.startswith("## ")]
    assert len(headers) == 6
    # tables auto-filled from data
    assert "724747" in md and "105/45" in md and "sha256:aa" in md
    # narrative placeholders present for the author
    assert "AUTHOR:" in md


def test_collect_robust_to_missing_artifacts(tmp_path):
    run_dir = tmp_path / "empty"
    run_dir.mkdir()
    data = R.collect(run_dir, Config())  # nothing on disk
    for key in REQUIRED_TOP:
        assert key in data
    # render must not raise on the sparse data
    R.render(data, Config())


def test_draft_is_cached_zero_second_call(tmp_path):
    run_dir = tmp_path / "glom"
    _populate(run_dir)
    data = R.collect(run_dir, Config())

    class FakeLLM:
        calls = 0

        def complete_json(self, step, messages, schema):
            FakeLLM.calls += 1
            return {
                k: f"draft {k}"
                for k in ("broken", "decisions", "selection", "run", "scale", "gaps")
            }

    llm = FakeLLM()
    decisions = {}
    R.draft_narrative(data, llm, Config(), decisions)
    R.draft_narrative(data, llm, Config(), decisions)  # cached
    assert FakeLLM.calls == 1


def test_build_writes_summary_without_clobbering_report_data(tmp_path, monkeypatch):
    run_dir = tmp_path / "glom"
    _populate(run_dir)
    before = (run_dir / "report_data.json").read_text()  # the runner's per-stage file
    monkeypatch.chdir(tmp_path)
    data_path, md_path = R.build(run_dir, Config(), llm=None, draft=False)
    assert data_path.name == "report_summary.json" and md_path.name == "REPORT.md"
    assert md_path.read_text().startswith("# REPORT")
    assert "agents" in json.loads(data_path.read_text())
    # the runner's report_data.json is READ, never overwritten
    assert (run_dir / "report_data.json").read_text() == before
