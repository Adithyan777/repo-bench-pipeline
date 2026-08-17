"""S7 OKF bundle + claim verifier + okf(path) tool.

The skeleton, verifier, tool sandbox and determinism are tested offline against a
hand-built graph + tiny repo (no LLM, no Docker). One cassette-backed test replays the
real module-purpose / function-contract calls through the full knowledge stage.
"""

from __future__ import annotations

import types
from pathlib import Path

import pytest

from pipeline.config import Config
from pipeline.ecosystems.python import PythonAdapter
from pipeline.knowledge import okf, okf_verify

_SRC = '''\
def raiser(x):
    """Raise on negatives."""
    if x < 0:
        raise ValueError("neg")
    return x


def caller(y):
    return raiser(y)


def _helper(z):
    total = 0
    for i in range(z):
        total += i
    return total
'''


def _graph() -> dict:
    def fn(name, line, end, cx, pub, tested=()):
        return {
            "id": f"pkg.mod.{name}", "type": "function", "file": "pkg/mod.py",
            "line": line, "end_line": end, "signature": f"{name}(...)",
            "docstring": None, "complexity": cx, "is_public": pub,
            "decorators": [], "coverage": 100.0, "tested_by": list(tested),
        }
    nodes = [
        {"id": "pkg.mod", "type": "module", "file": "pkg/mod.py", "line": 1,
         "is_public": True, "docstring": "A module."},
        fn("raiser", 1, 5, 2, True, ["tests/test_mod.py::test_raiser"]),
        fn("caller", 8, 9, 1, True),
        fn("_helper", 12, 16, 2, False),
    ]
    edges = [
        {"type": "contains", "source": "pkg.mod", "target": "pkg.mod.raiser",
         "evidence": {"file": "pkg/mod.py", "line": 1}},
        {"type": "calls", "source": "pkg.mod.caller", "target": "pkg.mod.raiser",
         "evidence": {"file": "pkg/mod.py", "line": 9}},
    ]
    return {"metadata": {}, "nodes": nodes, "edges": edges}


def _ctx(tmp_path: Path, config: Config):
    run_dir = tmp_path / "repo_out"
    repo = run_dir / "repo"
    (repo / "pkg").mkdir(parents=True)
    (repo / "pkg" / "mod.py").write_text(_SRC)
    (run_dir / "knowledge").mkdir(parents=True)
    (run_dir / "hygiene").mkdir(parents=True)
    return types.SimpleNamespace(
        run_dir=run_dir, repo=repo, knowledge_dir=run_dir / "knowledge",
        hygiene_dir=run_dir / "hygiene", config=config,
        adapter=PythonAdapter(config, repo, None),
    )


# --- frontmatter --------------------------------------------------------------


_FM = {
    "type": "python-function", "title": "f", "tags": ["a", "b"],
    "sources": [{"resource": "/x.py#L1-L2"}],
    "generated": {"by": "pipeline/m", "at": "2026-01-01T00:00:00Z"},
    "verified": [], "status": "draft",
}


def test_frontmatter_roundtrip():
    text = okf.emit_frontmatter(_FM) + "body\n"
    parsed, body = okf.parse_frontmatter(text)
    assert parsed == _FM
    assert body == "body\n"


def test_frontmatter_is_real_yaml():
    yaml = pytest.importorskip("yaml")  # runs where pyyaml is available (e.g. in-container)
    block = okf.emit_frontmatter(_FM)
    loaded = yaml.safe_load(block.split("---\n")[1])
    assert loaded == _FM  # inline-JSON frontmatter is valid YAML any consumer parses


# --- skeleton -----------------------------------------------------------------


def test_skeleton_matches_graph(tmp_path):
    cfg = Config()
    ctx = _ctx(tmp_path, cfg)
    manifest = okf.build_okf(ctx, _graph(), llm=None, decisions={})
    bundle = okf.bundle_dir(ctx)
    assert (bundle / "index.md").is_file() and (bundle / "repo.md").is_file()
    assert (bundle / "modules" / "pkg.mod.md").is_file()
    # public functions get pages; the trivial private helper (cx 2 >= threshold) does too
    assert (bundle / "functions" / "pkg.mod" / "pkg.mod.raiser.md").is_file()
    assert (bundle / "functions" / "pkg.mod" / "pkg.mod.caller.md").is_file()
    assert manifest["counts"]["modules"] == 1
    # caller page links to its callee raiser (a real page)
    caller = (bundle / "functions" / "pkg.mod" / "pkg.mod.caller.md").read_text()
    assert "## Callees" in caller and "pkg.mod.raiser" in caller
    # index lists every module
    assert "modules/pkg.mod.md" in (bundle / "index.md").read_text()


def test_private_low_complexity_summarized_not_paged(tmp_path):
    cfg = Config()
    cfg.okf.min_private_page_complexity = 5  # _helper (cx 2) now below threshold
    ctx = _ctx(tmp_path, cfg)
    okf.build_okf(ctx, _graph(), llm=None, decisions={})
    bundle = okf.bundle_dir(ctx)
    assert not (bundle / "functions" / "pkg.mod" / "pkg.mod._helper.md").exists()
    assert "_helper" in (bundle / "modules" / "pkg.mod.md").read_text()  # summarized


def test_determinism_byte_identical(tmp_path):
    cfg = Config()
    ctx = _ctx(tmp_path, cfg)
    okf.build_okf(ctx, _graph(), llm=None, decisions={})
    bundle = okf.bundle_dir(ctx)
    first = {p.name: p.read_text() for p in sorted(bundle.rglob("*.md"))}
    okf.build_okf(ctx, _graph(), llm=None, decisions={})
    second = {p.name: p.read_text() for p in sorted(bundle.rglob("*.md"))}
    assert first == second


class _CountingLLM:
    """Returns schema-valid stubs and counts calls, to prove reruns reuse decisions."""

    def __init__(self):
        self.calls = 0

    def complete_json(self, step, messages, schema):
        self.calls += 1
        if "purpose" in schema["properties"]:
            return {"purpose": "does things"}
        return {"contracts": []}


def test_second_run_makes_zero_llm_calls(tmp_path):
    cfg = Config()
    ctx = _ctx(tmp_path, cfg)
    llm, decisions = _CountingLLM(), {}
    okf.build_okf(ctx, _graph(), llm=llm, decisions=decisions)
    first = llm.calls
    assert first > 0  # authored purposes/contracts on the first run
    okf.build_okf(ctx, _graph(), llm=llm, decisions=decisions)
    assert llm.calls == first  # every decision reused -> zero new calls


# --- verifier + conformance ---------------------------------------------------


def test_verifier_stamps_and_conformance(tmp_path):
    cfg = Config()
    ctx = _ctx(tmp_path, cfg)
    okf.build_okf(ctx, _graph(), llm=None, decisions={})
    report = okf_verify.verify_okf(ctx, _graph())
    assert report["conformance"]["conformant"]
    assert report["unchecked_claim_kinds"] == ["inputs", "outputs", "invariants"]

    def load(qual):
        return okf.parse_frontmatter(
            (okf.bundle_dir(ctx) / "functions" / "pkg.mod" / f"{qual}.md").read_text()
        )[0]

    # caller makes a real callee claim (it calls raiser) -> verified, with checks recorded
    caller = load("pkg.mod.caller")
    assert caller["status"] == cfg.okf.verified_status
    assert caller["verified"][0]["by"] == cfg.okf.verifier_actor
    assert "callees" in caller["verified"][0]["checks"]
    # raiser's skeleton claims raises=none but its body raises -> negative check -> draft
    assert load("pkg.mod.raiser")["status"] == cfg.okf.unverified_status
    # callees is a semantic check; callers/link are reported by_construction, separately
    assert "callees" in report["precision_by_claim"]
    assert set(report["by_construction"]["precision"]) <= {"callers", "link"}


def test_page_with_only_unverifiable_fields_not_stamped(tmp_path):
    cfg = Config()
    ctx = _ctx(tmp_path, cfg)
    okf.build_okf(ctx, _graph(), llm=None, decisions={})
    bundle = okf.bundle_dir(ctx)
    # _helper: no raises, no callers/callees/links, side_effects not "none" -> nothing checked
    fp = bundle / "functions" / "pkg.mod" / "pkg.mod._helper.md"
    text = fp.read_text().replace(
        "- **side_effects**: unspecified", "- **side_effects**: mutates an accumulator"
    )
    fp.write_text(text)
    okf_verify.verify_okf(ctx, _graph())
    fm, _ = okf.parse_frontmatter(fp.read_text())
    assert fm["status"] == cfg.okf.unverified_status and fm["verified"] == []


def test_verifier_catches_planted_false_claims(tmp_path):
    cfg = Config()
    ctx = _ctx(tmp_path, cfg)
    okf.build_okf(ctx, _graph(), llm=None, decisions={})
    bundle = okf.bundle_dir(ctx)
    # raiser genuinely raises ValueError and is called by caller; plant an unsupported
    # KeyError and rewrite the real caller (caller) to a false one (_helper).
    fp = bundle / "functions" / "pkg.mod" / "pkg.mod.raiser.md"
    text = fp.read_text().replace("- **raises**: none", "- **raises**: ValueError, KeyError")
    assert "pkg.mod.caller" in text  # the real Callers link
    text = text.replace("pkg.mod.caller", "pkg.mod._helper")  # _helper does not call raiser
    fp.write_text(text)

    report = okf_verify.verify_okf(ctx, _graph())
    flagged = [u for u in report["unsupported"] if "raiser" in u["page"]][0]["unsupported"]
    assert "raises:KeyError" in flagged  # unsupported exception caught
    assert any(f.startswith("callers:") for f in flagged)  # false caller caught
    assert "raises:ValueError" not in flagged  # the true claim is NOT flagged
    assert report["precision_by_claim"]["raises"] == 0.5  # 1 of 2 raises claims supported
    fm, _ = okf.parse_frontmatter(fp.read_text())
    assert fm["status"] == cfg.okf.unverified_status and fm["verified"] == []


# --- source-module classification (docs/conf.py must not be a module) ---------


def test_docs_conf_is_not_a_source_module(tmp_path):
    from pipeline.ecosystems.symbols import build_symbol_index, is_source_path
    from pipeline.knowledge import graph as graph_mod

    repo = tmp_path / "repo"
    (repo / "pkg").mkdir(parents=True)
    (repo / "pkg" / "__init__.py").write_text("")
    (repo / "pkg" / "core.py").write_text("def f():\n    return 1\n")
    (repo / "docs").mkdir()
    (repo / "docs" / "conf.py").write_text("project = 'x'\n\n\ndef setup(app):\n    return {}\n")
    (repo / "setup.py").write_text("def main():\n    return 0\n")
    (repo / "noise.py").write_text("def g():\n    return 2\n")  # top-level script, no package
    cfg = Config()

    assert is_source_path(repo, repo / "pkg" / "core.py", cfg)
    for junk in ("docs/conf.py", "setup.py", "noise.py"):
        assert not is_source_path(repo, repo / junk, cfg), junk

    idx = build_symbol_index(repo, cfg)
    src = {m["name"] for m in idx["modules"] if m["is_source"]}
    assert "pkg.core" in src
    assert {"conf", "setup", "noise"}.isdisjoint(src)

    graph = graph_mod.build_graph(idx, {}, {}, cfg)
    module_nodes = {n["id"] for n in graph["nodes"] if n["type"] == "module"}
    assert "pkg.core" in module_nodes and "conf" not in module_nodes


class _HallucinatingLLM:
    """First purpose names an identifier not in the module; the regenerated one is clean."""

    def __init__(self):
        self.calls = 0

    def complete_json(self, step, messages, schema):
        self.calls += 1
        if "purpose" not in schema["properties"]:
            return {"contracts": []}
        if "not in this module" in messages[0]["content"]:  # regeneration prompt
            return {"purpose": "Internal helpers for the package."}
        return {"purpose": "Manages `DatabaseConnection` pooling and feature flags."}


def test_purpose_hallucination_guard(tmp_path):
    cfg = Config()
    ctx = _ctx(tmp_path, cfg)
    llm = _HallucinatingLLM()
    okf.build_okf(ctx, _graph(), llm=llm, decisions={})
    page = (okf.bundle_dir(ctx) / "modules" / "pkg.mod.md").read_text()
    assert "DatabaseConnection" not in page  # invented identifier rejected
    assert "Internal helpers" in page  # the regenerated, grounded purpose is used
    assert llm.calls >= 2  # regenerated once


# --- okf(path) tool -----------------------------------------------------------


def test_okf_tool_reads_and_sandboxes(tmp_path):
    from pipeline.agent.tools import ToolContext, _okf

    cfg = Config()
    ctx = _ctx(tmp_path, cfg)
    okf.build_okf(ctx, _graph(), llm=None, decisions={})
    tool_ctx = ToolContext(workdir=ctx.repo, knowledge_dir=ctx.knowledge_dir, config=cfg)
    assert _okf(tool_ctx, "index.md").startswith("---")
    assert "pkg.mod" in _okf(tool_ctx, "modules/pkg.mod.md")
    with pytest.raises(ValueError):
        _okf(tool_ctx, "../../../etc/passwd")
    with pytest.raises(FileNotFoundError):
        _okf(tool_ctx, "modules/nope.md")
    # a symlink inside the bundle pointing outside must not be followable out
    secret = tmp_path / "secret.txt"
    secret.write_text("top secret")
    (okf.bundle_dir(ctx) / "escape.md").symlink_to(secret)
    with pytest.raises(ValueError):
        _okf(tool_ctx, "escape.md")


# --- LLM contract via cassette ------------------------------------------------


def _cassettes(stage: str) -> bool:
    d = Path("tests/cassettes") / stage
    return d.is_dir() and any(d.glob("*.json"))


@pytest.mark.docker
@pytest.mark.skipif(not _cassettes("s7_okf"), reason="s7_okf cassettes not recorded")
def test_okf_llm_contract_replay(tmp_path):
    from tests import _smoke

    ctx = _smoke.run_okf_stage(tmp_path, "replay")
    bundle = Path(ctx.knowledge_dir) / ctx.config.okf.bundle_dirname
    clamp = (bundle / "functions" / "mini_pkg.calc" / "mini_pkg.calc.clamp.md").read_text()
    fm, body = okf.parse_frontmatter(clamp)
    # the model authored a real contract (not the skeleton placeholder)
    assert "_(unspecified)_" not in body
    assert "**inputs**:" in body and "**outputs**:" in body
    assert ctx.report["okf"]["pages_verified"] >= 1
