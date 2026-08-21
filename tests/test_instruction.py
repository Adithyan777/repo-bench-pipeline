"""LLM-authored instruction, leak gates, golden rationale, difficulty.

Gates and features tested directly; author/reviewer/label loops via scripted endpoints;
real BIG calls replay from ``tasks_fixture`` in tests/test_tasks.py.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from pipeline.config import Config
from pipeline.ecosystems.symbols import build_symbol_index
from pipeline.knowledge import graph as graph_mod
from pipeline.tasks import difficulty as D
from pipeline.tasks import instruction as I
from tests import _smoke

FIXTURES = Path(__file__).resolve().parent / "fixtures"
MINI = FIXTURES / "mini_pkg"

CALC_INPUT = '''"""calc"""


def ceil_div(a, b):
    """Return ceil(a / b) for positive integers."""
    return (a + b) // b
'''
CALC_SOLUTION = '''"""calc"""


def ceil_div(a, b):
    """Return ceil(a / b) for positive integers."""
    quotient, remainder = _split_division(a, b)
    return quotient + bool(remainder)


def _split_division(a, b):
    return divmod(a, b)
'''
TEST_SRC = """from mini_pkg.calc import ceil_div


def test_ceil_div_exact_multiple():
    assert ceil_div(4, 2) == 2
"""


def _fake_task(root: Path, kind: str = "history") -> Path:
    """A minimal task folder: input/solution trees for one module + a verifier test."""
    task_dir = root / "hist-abc1234"
    for tree, src in (("input", CALC_INPUT), ("solution", CALC_SOLUTION)):
        (task_dir / tree / "mini_pkg").mkdir(parents=True)
        (task_dir / tree / "mini_pkg" / "__init__.py").write_text("")
        (task_dir / tree / "mini_pkg" / "calc.py").write_text(src)
    (task_dir / "verifier" / "tests").mkdir(parents=True)
    (task_dir / "verifier" / "tests" / "test_calc.py").write_text(TEST_SRC)
    prov = (
        {
            "type": "history",
            "source_files": ["mini_pkg/calc.py"],
            "touched_functions": ["mini_pkg.calc.ceil_div"],
            "classification": {"behavior_change_summary": "ceil_div rounds exact multiples"},
        }
        if kind == "history"
        else {"type": "excision", "file": "mini_pkg/calc.py", "target": "mini_pkg.calc.ceil_div"}
    )
    task = {
        "id": task_dir.name,
        "title": "t",
        "provenance": prov,
        "files_in_scope": ["mini_pkg/calc.py", "tests/test_calc.py"],
        "verifier_cmd": "python -m pytest -q tests/test_calc.py::test_ceil_div_exact_multiple",
        "verifier_tests": ["tests/test_calc.py::test_ceil_div_exact_multiple"],
        "instruction": "template",
        "instruction_status": "template",
        "verifier_visibility": "visible",
    }
    (task_dir / "task.json").write_text(json.dumps(task))
    (task_dir / "goldenSolution.md").write_text(
        "# Golden\n\n```diff\n+x\n```\n\n"
        "<!-- TODO-golden: LLM-authored 'why correct' rationale -->\n"
    )
    return task_dir


def test_task_facts_and_leak_gates(tmp_path: Path) -> None:
    facts = I.task_facts(_fake_task(tmp_path))
    assert "`mini_pkg.calc.ceil_div`: `ceil_div(a, b)`" in facts.contract
    assert "Return ceil(a / b)" in facts.contract
    assert "+    quotient, remainder = _split_division(a, b)" in facts.diff
    assert facts.new_names == {"_split_division"}  # API-like names only, not locals
    assert "ceil_div" in facts.public_names and "test_ceil_div_exact_multiple" in facts.test_names
    # (a) a diff line with >= 5 tokens copied into the instruction
    leaky = "## Goal\nImplement it as `quotient, remainder = _split_division(a, b)` then return."
    assert I.diff_leaks(leaky, facts.diff, 5) == ["quotient, remainder = _split_division(a, b)"]
    assert I.diff_leaks("Return the ceiling of a / b.", facts.diff, 5) == []
    # (b) a new private identifier named; public/test names are fine
    assert I.identifier_leaks("Use the helper _split_division to divide.", facts) == [
        "_split_division"
    ]
    assert (
        I.identifier_leaks(
            "Make ceil_div(4, 2) return 2 (see test_ceil_div_exact_multiple).", facts
        )
        == []
    )
    issues, feedback = I.leak_issues(leaky, facts)
    assert len(issues) == 2 and issues[0].startswith("instruction leaks a solution line")
    assert issues[1].endswith("`_split_division`")
    assert len(feedback) == 2 and "_split_division" not in " ".join(feedback)  # never echoed
    assert "quotient" not in " ".join(feedback)
    # a diff line that is also in the verifier tests (an example) is exempt, via leak_issues
    facts.diff += "+    assert ceil_div(4, 2) == 2\n"
    assert I.leak_issues("Example: `assert ceil_div(4, 2) == 2`", facts) == ([], [])
    cfg_strict = Config()
    cfg_strict.instruction.exempt_diff_lines_in_tests = False
    assert I.leak_issues("Example: `assert ceil_div(4, 2) == 2`", facts, cfg_strict)[0]
    cfg2 = Config()
    cfg2.instruction.leak_api_names_only = False
    assert {"quotient", "remainder"} <= I.task_facts(facts.task_dir, cfg2).new_names
    cfg = Config()
    cfg.instruction.forbid_new_identifiers_from_diff = False
    assert I.leak_issues("call _split_division", facts, cfg) == ([], [])


def test_leak_exemptions_survive_test_source_truncation(tmp_path: Path) -> None:
    """A new API name a solver must produce (named in the verifier tests) stays exempt even
    when the test file is longer than tests_max_chars (toolz `peek`: named only at the end)."""
    task_dir = _fake_task(tmp_path)
    test_file = task_dir / "verifier" / "tests" / "test_calc.py"
    padding = "\n".join(f"def test_pad_{i}():\n    assert True\n" for i in range(400))
    test_file.write_text(padding + "\n\ndef test_peek():\n    assert peek([1]) == 1\n")
    task = json.loads((task_dir / "task.json").read_text())
    task["verifier_tests"] = ["tests/test_calc.py::test_peek"]
    (task_dir / "task.json").write_text(json.dumps(task))
    cfg = Config()
    assert len((task_dir / "verifier" / "tests" / "test_calc.py").read_text()) > (
        cfg.instruction.tests_max_chars
    )
    facts = I.task_facts(task_dir, cfg)
    assert facts.tests_source.endswith("... (truncated)")  # prompt text is capped
    assert "peek" in facts.test_names  # exemption built from the full source
    assert I.identifier_leaks("Add a function `peek` returning the first element.", facts) == []
    # the classifier's summary is masked before it reaches a prompt
    facts.summary = "Uses _split_division to compute ceil_div."
    assert I.mask_names(facts.summary, facts) == "Uses [...] to compute ceil_div."
    assert "_split_division" not in I.author_prompt(facts, Config(), [])


def test_api_names_include_module_constants() -> None:
    from pipeline.ecosystems.source_ops import new_api_names

    old = "def f():\n    return 1\n"
    new = "MIN_MODE = 2\n\n\ndef f():\n    local_var = MIN_MODE\n    return local_var\n"
    assert new_api_names(old, new) == {"MIN_MODE"}


class _Scripted:
    """complete_json responses in order, keyed by step."""

    def __init__(self, by_step: dict[str, list[dict]]):
        self.by_step = {k: list(v) for k, v in by_step.items()}
        self.calls: list[str] = []
        self.prompts: list[str] = []

    def complete_json(self, step, messages, schema):
        self.calls.append(step)
        self.prompts.append(messages[-1]["content"])
        return self.by_step[step].pop(0)


GOOD = {
    "title": "Fix ceil_div for exact multiples",
    "instruction": "## Goal\nceil_div must round up.\n## Observable behavior\n"
    "`assert ceil_div(4, 2) == 2`\n## Constraints\nkeep the API\n"
    "## How success is measured\nrun the verifier",
}
LEAKY = {"title": "t", "instruction": "## Goal\nquotient, remainder = _split_division(a, b)"}
OK_REVIEW = {
    "solvable_by_transcription": False,
    "states_mechanical_edit": False,
    "self_contained": True,
    "implementation_neutral": True,
    "issues": [],
}
BAD_REVIEW = {
    "solvable_by_transcription": False,
    "states_mechanical_edit": True,
    "self_contained": True,
    "implementation_neutral": True,
    "issues": ["reads like a patch"],
}


def test_write_instruction_regenerates_with_feedback_and_persists(tmp_path: Path) -> None:
    facts = I.task_facts(_fake_task(tmp_path))
    llm = _Scripted({I.WRITE_STEP: [LEAKY, GOOD, GOOD], I.REVIEW_STEP: [BAD_REVIEW, OK_REVIEW]})
    decisions: dict = {}
    rec = I.write_instruction(facts, llm, decisions=decisions)
    assert rec["status"] == "final" and rec["title"] == GOOD["title"]
    assert [a["issues"][:1] for a in rec["attempts"]] == [
        ["instruction leaks a solution line: `quotient, remainder = _split_division(a, b)`"],
        ["reviewer: states the mechanical edit"],
        [],
    ]
    assert llm.calls == [I.WRITE_STEP, I.WRITE_STEP, I.REVIEW_STEP, I.WRITE_STEP, I.REVIEW_STEP]
    assert "fix these issues" in llm.prompts[1] and "reads like a patch" in llm.prompts[3]
    assert "_split_division" not in llm.prompts[1]  # feedback never echoes the leak
    assert (
        "solution/" not in llm.prompts[0] and "_split_division" not in llm.prompts[0]
    )  # never the diff
    # persisted: a rerun costs nothing
    again = I.write_instruction(facts, _Scripted({}), decisions=decisions)
    assert again["reused"] and again["instruction"] == GOOD["instruction"]


def test_write_instruction_fails_after_bounded_regenerations(tmp_path: Path) -> None:
    facts = I.task_facts(_fake_task(tmp_path))
    cfg = Config()
    cfg.instruction.max_regenerations = 1
    llm = _Scripted({I.WRITE_STEP: [LEAKY, LEAKY, LEAKY], I.REVIEW_STEP: []})
    rec = I.write_instruction(facts, llm, cfg)
    assert (
        rec["status"] == "failed"
        and len(rec["attempts"]) == 2
        and llm.calls.count(I.WRITE_STEP) == 2
    )
    assert rec["issues"] and rec["review"] is None
    assert "instruction" not in rec and rec["drafts"] == ["t", "t"]  # drafts never reach task.json
    # a leaking TITLE is gated too
    llm2 = _Scripted(
        {I.WRITE_STEP: [{"title": "Use _split_division", "instruction": GOOD["instruction"]}] * 2}
    )
    rec2 = I.write_instruction(facts, llm2, cfg)
    assert rec2["status"] == "failed" and rec2["issues"][0].startswith("title names an identifier")


def test_hidden_visibility_phrase_and_golden(tmp_path: Path) -> None:
    facts = I.task_facts(_fake_task(tmp_path))
    cfg = Config()
    cfg.harness.verifier_visibility = "hidden"
    assert cfg.instruction.hidden_phrase in I.author_prompt(facts, cfg, [])
    cfg.harness.verifier_visibility = "visible"
    assert cfg.instruction.visible_phrase in I.author_prompt(facts, cfg, [])
    llm = _Scripted({I.GOLDEN_STEP: [{"why_correct": "It rounds up via divmod."}]})
    why = I.golden_rationale(facts, llm, decisions={})
    assert (
        "diff" in llm.prompts[0] and "_split_division" in llm.prompts[0]
    )  # golden MAY see the diff
    I.apply_golden(facts.task_dir, why)
    text = (facts.task_dir / "goldenSolution.md").read_text()
    assert "TODO-golden" not in text
    assert text.endswith("## Why correct\n\nIt rounds up via divmod.\n")
    I.apply_golden(facts.task_dir, "Second answer.")  # idempotent: one section, latest text
    text = (facts.task_dir / "goldenSolution.md").read_text()
    assert text.count("## Why correct") == 1 and text.endswith("## Why correct\n\nSecond answer.\n")
    assert "It rounds up" not in text


def _fixture_graph() -> dict:
    cfg = Config()
    symbols = build_symbol_index(MINI, cfg)
    return graph_mod.build_graph(symbols, _smoke.MINI_PKG_TEST_MAP, {}, cfg)


def test_features_on_mini_pkg(tmp_path: Path) -> None:
    graph = _fixture_graph()
    facts = I.task_facts(_fake_task(tmp_path))
    feats = D.features(facts, graph)
    assert feats == {
        "files_touched": 1,
        "functions_touched": 1,
        "callers_count": 0,
        "cross_module_edges": 0,  # only touched-function endpoints count
        "diff_size": 5,
        "similar_named_functions_nearby": 0,
        "test_count": 1,
    }
    # truncate: display_width shares no name token; _needs_truncation shares 'truncation'
    facts.touched_functions = ["mini_pkg.text.truncate"]
    facts.source_files = ["mini_pkg/text.py"]
    feats = D.features(facts, graph)
    assert feats["callers_count"] == 0 and feats["similar_named_functions_nearby"] == 0
    facts.touched_functions = ["mini_pkg.text._needs_truncation"]
    assert D.features(facts, graph)["callers_count"] == 1  # truncate calls it


def test_cites_feature() -> None:
    feats = {"callers_count": 12, "diff_size": 3, "files_touched": 1}
    assert D.cites_feature("callers_count=12 makes this medium", feats)
    assert D.cites_feature("only a diff size of 3", feats)
    assert D.cites_feature("12 callers count", feats)
    assert not D.cites_feature("The change is small.", feats)
    assert not D.cites_feature("callers_count is high", feats)  # name without its value
    assert not D.cites_feature("only 3 lines", feats)  # value without the name


def test_label_tasks_regenerates_once_then_fails(tmp_path: Path) -> None:
    graph = _fixture_graph()
    facts = I.task_facts(_fake_task(tmp_path))
    feats = D.features(facts, graph)
    tid = facts.task["id"]
    llm = _Scripted(
        {
            D.LABEL_STEP: [
                {"labels": [{"task_id": tid, "difficulty": "easy", "rationale": "trivial"}]},
                {
                    "labels": [
                        {
                            "task_id": tid,
                            "difficulty": "easy",
                            "rationale": "diff_size=5, one function",
                        }
                    ]
                },
            ]
        }
    )
    decisions: dict = {}
    out = D.label_tasks([(facts, feats)], llm, decisions=decisions)
    assert out[tid]["difficulty"] == "easy" and out[tid]["attempts"] == 2
    assert "does not cite" in llm.prompts[1]
    llm2 = _Scripted(
        {
            D.LABEL_STEP: [{"labels": [{"task_id": tid, "difficulty": "hard", "rationale": "meh"}]}]
            * 2
        }
    )
    out2 = D.label_tasks([(facts, feats)], llm2)
    assert out2[tid]["status"] == "failed" and out2[tid]["difficulty"] is None
    assert len(llm2.calls) == 2  # regenerate once, then fail
    # persisted decision: no call
    out3 = D.label_tasks([(facts, feats)], _Scripted({}), decisions=decisions)
    assert out3[tid]["reused"] and out3[tid]["difficulty"] == "easy"


def test_excision_facts_use_input_contract(tmp_path: Path) -> None:
    task_dir = _fake_task(tmp_path, kind="excision")
    shutil.copy(task_dir / "input/mini_pkg/calc.py", task_dir / "solution/mini_pkg/calc.py")
    (task_dir / "input/mini_pkg/calc.py").write_text(
        CALC_INPUT.replace("    return (a + b) // b", '    raise NotImplementedError("excised")')
    )
    facts = I.task_facts(task_dir)
    assert "was removed" in facts.summary and "ceil_div(a, b)" in facts.contract
    assert "+    return (a + b) // b" in facts.diff
    assert I.diff_leaks("Restore `return (a + b) // b` please", facts.diff, 5) == [
        "return (a + b) // b"
    ]
