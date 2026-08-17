"""LLM-authored task instruction + leak gates + golden rationale (DESIGN 5.6).

The authoring model (``p3.build.write_instruction``) sees only input/'s public contract,
verifier tests, behavior summary / excised signature, files_in_scope and the verifier
command -- never the diff or solution/. Gates: pure-code leak check + BIG reviewer
(``p3.build.review_instruction``); regenerate <= ``instruction.max_regenerations`` times,
then ``instruction_status: failed``. Decisions persisted by content hash. The golden
rationale (``p3.build.golden_rationale``) MAY see the diff.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from pipeline.config import DEFAULT, Config
from pipeline.ecosystems.source_ops import (
    defined_names,
    function_contracts,
    module_bound_names,
    new_api_names,
    new_identifiers,
    read_source,
)
from pipeline.ecosystems.symbols import build_symbol_index, path_to_module

WRITE_STEP = "p3.build.write_instruction"
REVIEW_STEP = "p3.build.review_instruction"
GOLDEN_STEP = "p3.build.golden_rationale"

WRITE_SCHEMA = {
    "type": "object",
    "properties": {"title": {"type": "string"}, "instruction": {"type": "string"}},
    "required": ["title", "instruction"],
}
REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "solvable_by_transcription": {"type": "boolean"},
        "self_contained": {"type": "boolean"},
        "states_mechanical_edit": {"type": "boolean"},
        "implementation_neutral": {"type": "boolean"},
        "issues": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "solvable_by_transcription",
        "states_mechanical_edit",
        "self_contained",
        "implementation_neutral",
        "issues",
    ],
}
GOLDEN_SCHEMA = {
    "type": "object",
    "properties": {"why_correct": {"type": "string"}},
    "required": ["why_correct"],
}

_TOKEN_RE = re.compile(r"\w+|[^\w\s]")
_TODO_RE = re.compile(r"<!-- TODO-golden:[^>]*-->\n?")


@dataclass
class TaskFacts:
    """Everything the instruction machinery needs about one built task folder."""

    task_dir: Path
    task: dict
    source_files: list[str]  # repo-relative source files that differ input->solution
    touched_functions: list[str]
    contract: str  # signatures + docstrings AS IN input/
    tests_source: str
    summary: str  # behavior summary (history) / excised contract note (excision)
    diff: str  # unified diff input->solution over source_files (never shown to the authoring model)
    new_names: set[str] = field(default_factory=set)
    public_names: set[str] = field(default_factory=set)
    test_names: set[str] = field(default_factory=set)


# --- facts ----------------------------------------------------------------------------


def task_facts(task_dir: Path, config: Config = DEFAULT) -> TaskFacts:
    task = json.loads((task_dir / config.tasks.task_json).read_text())
    prov = task["provenance"]
    if prov["type"] == "excision":
        source_files = [prov["file"]]
        touched = [prov["target"]]
        summary = (
            f"The body of `{prov['target']}` was removed (it raises NotImplementedError); "
            "the original behavior must be restored."
        )
    else:
        source_files = list(prov.get("source_files") or [])
        touched = list(prov.get("touched_functions") or [])
        summary = (prov.get("classification") or {}).get("behavior_change_summary") or ""
    inp, sol = task_dir / "input", task_dir / "solution"
    contract = _contract(inp, source_files, touched, config)
    tests_source = _tests_source(task_dir / "verifier", task["verifier_tests"], config)
    diff = "".join(_diff(inp, sol, f) for f in source_files)
    facts = TaskFacts(task_dir, task, source_files, touched, contract, tests_source, summary, diff)
    for rel in source_files:
        before = read_source(inp / rel) if (inp / rel).is_file() else None
        after = read_source(sol / rel) if (sol / rel).is_file() else ""
        pick = new_api_names if config.instruction.leak_api_names_only else new_identifiers
        facts.new_names |= pick(before, after)
    facts.public_names = _public_names(inp, config)
    facts.test_names = defined_names(tests_source) | set(re.findall(r"\w+", tests_source))
    return facts


def _contract(inp: Path, files: list[str], touched: list[str], config: Config) -> str:
    wanted = set(touched)
    lines: list[str] = []
    for rel in files:
        path = inp / rel
        if not path.is_file():
            continue
        module = path_to_module(rel, config.knowledge.source_roots)
        for fn in function_contracts(read_source(path), module):
            if fn["qualname"] in wanted:
                doc = (fn["docstring"] or "").strip()
                tag = "" if fn["is_public"] else " (internal)"
                lines.append(
                    f"- `{fn['qualname']}`{tag}: `{fn['signature']}`"
                    + (f"\n  {doc}" if doc else "")
                )
    return "\n".join(lines) or "- (touched functions have no contract in the current tree)"


def _tests_source(verifier: Path, nodeids: list[str], config: Config) -> str:
    blocks = []
    for rel in sorted({n.split("::", 1)[0] for n in nodeids}):
        names = sorted({n.split("::", 1)[1] for n in nodeids if n.startswith(rel + "::")})
        source = read_source(verifier / rel)
        blocks.append(f"### {rel} (verifier tests: {', '.join(names)})\n```python\n{source}\n```")
    text = "\n\n".join(blocks)
    limit = config.instruction.tests_max_chars
    return text if len(text) <= limit else text[:limit] + "\n... (truncated)"


def _diff(inp: Path, sol: Path, rel: str) -> str:
    a = read_source(inp / rel).splitlines(keepends=True) if (inp / rel).is_file() else []
    b = read_source(sol / rel).splitlines(keepends=True) if (sol / rel).is_file() else []
    return "".join(
        difflib.unified_diff(a, b, fromfile=f"input/{rel}", tofile=f"solution/{rel}", n=3)
    )


def _public_names(inp: Path, config: Config) -> set[str]:
    """Names visible in input/: module names, top-level bindings, public function/class names."""
    symbols = build_symbol_index(inp, config)
    names: set[str] = set()
    for m in symbols["modules"]:
        names.update(m["name"].split("."))
        if not m["is_test"]:
            bound, _ = module_bound_names(read_source(inp / m["file"]))
            names |= bound
    for kind in ("functions", "classes"):
        for rec in symbols.get(kind, []):
            if rec.get("is_public", True):
                names.add(rec["qualname"].rsplit(".", 1)[-1])
    return names


# --- leak gate (pure code) --------------------------------------------------------------


def _norm(line: str) -> str:
    return " ".join(line.split())


def diff_leaks(instruction: str, diff: str, min_tokens: int, exempt: str = "") -> list[str]:
    """Added diff lines with >= ``min_tokens`` tokens found verbatim (whitespace-normalized)
    in the instruction; lines also in ``exempt`` (verifier tests) do not count."""
    text = _norm(instruction)
    allowed = _norm(exempt)
    hits: list[str] = []
    for raw in diff.splitlines():
        if not raw.startswith("+") or raw.startswith("+++"):
            continue
        line = _norm(raw[1:])
        if len(_TOKEN_RE.findall(line)) >= min_tokens and line and line in text:
            if allowed and line in allowed:
                continue
            hits.append(line)
    return sorted(set(hits))


def identifier_leaks(instruction: str, facts: TaskFacts, config: Config = DEFAULT) -> list[str]:
    """Diff-introduced identifiers named by the instruction that are in neither input/'s public
    API nor the verifier tests."""
    ic = config.instruction
    forbidden = {
        n
        for n in facts.new_names
        if len(n) >= ic.leak_min_identifier_chars
        and n not in facts.public_names
        and n not in facts.test_names
    }
    return sorted(n for n in forbidden if re.search(rf"\b{re.escape(n)}\b", instruction))


def leak_issues(
    text: str, facts: TaskFacts, config: Config = DEFAULT, what: str = "instruction"
) -> tuple[list[str], list[str]]:
    """(detailed issues for the record, sanitized feedback for the authoring model); feedback
    never echoes the leaked line/identifier."""
    ic = config.instruction
    exempt = facts.tests_source if ic.exempt_diff_lines_in_tests else ""
    lines = diff_leaks(text, facts.diff, ic.leak_min_tokens, exempt)
    names = identifier_leaks(text, facts, config) if ic.forbid_new_identifiers_from_diff else []
    issues = [f"{what} leaks a solution line: `{ln}`" for ln in lines]
    issues += [f"{what} names an identifier introduced by the change: `{n}`" for n in names]
    feedback: list[str] = []
    if lines:
        feedback.append(
            f"the {what} copies {len(lines)} line(s) of the solution: describe behavior, never "
            "code that is not in the verifier tests"
        )
    if names:
        feedback.append(
            f"the {what} names {len(names)} identifier(s) that do not exist in the current tree "
            "or the tests: refer only to names visible in the contract or the tests"
        )
    return issues, feedback


def mask_names(text: str, facts: TaskFacts, config: Config = DEFAULT) -> str:
    """Mask change-introduced names in free text before it reaches the authoring/labeling model."""
    ic = config.instruction
    for n in sorted(facts.new_names, key=len, reverse=True):
        if (
            len(n) >= ic.leak_min_identifier_chars
            and n not in facts.public_names
            and n not in facts.test_names
        ):
            text = re.sub(rf"\b{re.escape(n)}\b", "[...]", text)
    return text


# --- prompts ----------------------------------------------------------------------------

PROMPT_VERSION = "instruction.2"  # bump when the prompts below change: keys of persisted decisions

AUTHOR_SYSTEM = (
    "You write instructions for a coding benchmark task. You see the contract of the touched "
    "functions as it stands in the pre-change tree, the verifier tests, a behavior summary "
    "and the scope; you never see the solution. Write a Markdown instruction with exactly "
    "these sections: `## Goal`, `## Observable behavior` (with the requested number of "
    "concrete input -> output examples COPIED verbatim from the verifier tests, as code), "
    "`## Constraints` (about the task: API to keep, files in scope), `## How success is "
    "measured` (the verifier command). Describe WHAT must hold, never how to implement it or "
    "which edit to make; name only identifiers visible in the contract or the tests, never "
    "internal names (starting with `_`); do not restate test code beyond the examples; do "
    "not copy meta lines of this prompt (title limits, example counts, visibility notes) "
    "into the instruction. Also return a short title that names no internal identifier."
)

REVIEW_SYSTEM = (
    "You review a benchmark task instruction against the touched-function contract and the "
    "verifier tests (you never see the solution). Judge: solvable_by_transcription (does the "
    "text spell out the implementation so a solver could transcribe it without "
    "understanding? Copied test examples are REQUIRED by the format and are not "
    "transcription; a behavioral statement of a small change is not transcription either), "
    "states_mechanical_edit (does it name the concrete edit to make -- e.g. 'replace X with "
    "Y on line N', 'add a parameter Z' -- instead of the observable behavior?), "
    "self_contained (can a competent engineer solve it with this instruction, the repo and "
    "the tests alone?), implementation_neutral (does it avoid prescribing a specific "
    "implementation, private names or internal structure?). List concrete issues."
)


def author_prompt(facts: TaskFacts, config: Config, feedback: list[str]) -> str:
    ic, task = config.instruction, facts.task
    hidden = config.harness.verifier_visibility == "hidden"
    phrase = ic.hidden_phrase if hidden else ic.visible_phrase
    fb = (
        ("\n\nThe previous draft was rejected; fix these issues:\n- " + "\n- ".join(feedback))
        if feedback
        else ""
    )
    return (
        f"Task kind: {task['provenance']['type']}\n"
        f"Behavior summary: {mask_names(facts.summary, facts, config)}\n\n"
        f"Touched-function contract (as in the current tree; entries marked (internal) "
        f"must not be named in the instruction):\n{facts.contract}\n\n"
        f"Files in scope: {', '.join(task['files_in_scope'])}\n"
        f"Verifier command: `{task['verifier_cmd']}`\nVerifier visibility: {phrase}\n"
        f"Examples to copy from the tests: {ic.examples_from_verifier}\n"
        f"Title max chars: {ic.title_max_chars}\n\n{facts.tests_source}{fb}"
    )


def review_prompt(instruction: str, facts: TaskFacts) -> str:
    return (
        f"Touched-function contract:\n{facts.contract}\n\n{facts.tests_source}\n\n"
        f"Instruction under review:\n---\n{instruction}\n---"
    )


def golden_prompt(facts: TaskFacts, config: Config) -> str:
    diff = facts.diff
    limit = config.instruction.diff_max_chars
    if len(diff) > limit:
        diff = diff[:limit] + "\n... (truncated)"
    return (
        "Write 2-4 sentences explaining WHY this change is correct for the task below, "
        "grounded on the diff and the verifier tests (what behavior it establishes and why "
        "the tests pass). Plain prose, no bullet list.\n\n"
        f"Task: {facts.task['title']}\nBehavior summary: {facts.summary}\n"
        f"Contract:\n{facts.contract}\n\n```diff\n{diff}\n```\n\n{facts.tests_source}"
    )


# --- driver -----------------------------------------------------------------------------


def _key(config: Config, *parts: str) -> str:
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()[: config.tasks.content_key_chars]


def prompt_hash() -> str:
    return hashlib.sha256(
        "\n".join([PROMPT_VERSION, AUTHOR_SYSTEM, REVIEW_SYSTEM]).encode()
    ).hexdigest()[:12]


def content_key(facts: TaskFacts, config: Config) -> str:
    """Content hash of everything the authoring model sees + prompt constants. Excludes gate
    config: a tightened gate needs --force instruct."""
    return _key(
        config,
        "instruction",
        prompt_hash(),
        facts.task["id"],
        facts.contract,
        facts.tests_source,
        facts.summary,
        config.harness.verifier_visibility,
        config.model_for(WRITE_STEP),
        config.model_for(REVIEW_STEP),
    )


def write_instruction(
    facts: TaskFacts, llm, config: Config = DEFAULT, decisions: dict | None = None
) -> dict:
    """Author -> leak gate -> reviewer, regenerating with issues fed back. Returns the persisted
    ``{status, title, instruction, attempts, review, issues, key}``."""
    ic = config.instruction
    key = content_key(facts, config)
    if decisions is not None and key in decisions:
        return {**decisions[key], "reused": True}
    feedback: list[str] = []
    attempts: list[dict] = []
    record: dict = {"key": key, "status": ic.status_failed}
    for attempt in range(1, ic.max_regenerations + 2):
        out = llm.complete_json(
            WRITE_STEP,
            [
                {"role": "system", "content": AUTHOR_SYSTEM},
                {"role": "user", "content": author_prompt(facts, config, feedback)},
            ],
            WRITE_SCHEMA,
        )
        title = out["title"].strip()[: ic.title_max_chars]
        instruction = out["instruction"].strip()
        issues, fb = leak_issues(instruction, facts, config)
        t_issues, t_fb = leak_issues(title, facts, config, what="title")
        issues, fb = issues + t_issues, fb + t_fb
        review = None
        if not issues:
            review = llm.complete_json(
                REVIEW_STEP,
                [
                    {"role": "system", "content": REVIEW_SYSTEM},
                    {"role": "user", "content": review_prompt(instruction, facts)},
                ],
                REVIEW_SCHEMA,
            )
            flags = {
                "solvable by transcription": review["solvable_by_transcription"],
                "states the mechanical edit": review.get("states_mechanical_edit", False),
                "not self-contained": not review["self_contained"],
                "not implementation-neutral": not review["implementation_neutral"],
            }
            issues += [f"reviewer: {k}" for k, v in flags.items() if v]
            if issues:
                issues += [f"reviewer: {i}" for i in review.get("issues", [])]
            fb = list(issues)  # reviewer text never contains the solution
        attempts.append(
            {"attempt": attempt, "issues": issues, "review": review, "draft_title": title}
        )
        if not issues:
            record.update({"status": ic.status_final, "title": title, "instruction": instruction})
            break
        feedback = fb
    record["review"] = attempts[-1]["review"] if attempts else None
    record["attempts"] = attempts
    record["issues"] = attempts[-1]["issues"] if record["status"] != ic.status_final else []
    if record["status"] != ic.status_final:  # drafts stay out of task.json
        record["drafts"] = [a["draft_title"] for a in attempts]
    if decisions is not None:
        decisions[key] = record
    return record


def golden_rationale(
    facts: TaskFacts, llm, config: Config = DEFAULT, decisions: dict | None = None
) -> str:
    prompt = golden_prompt(facts, config)
    key = _key(config, "golden", facts.task["id"], prompt, config.model_for(GOLDEN_STEP))
    if decisions is not None and key in decisions:
        return decisions[key]["why_correct"]
    out = llm.complete_json(GOLDEN_STEP, [{"role": "user", "content": prompt}], GOLDEN_SCHEMA)
    if decisions is not None:
        decisions[key] = {"why_correct": out["why_correct"]}
    return out["why_correct"]


WHY_HEADING = "## Why correct"


def apply_golden(task_dir: Path, why: str, config: Config = DEFAULT) -> None:
    """Idempotent: drops the TODO markers and any previous ``## Why correct`` section."""
    path = task_dir / config.tasks.golden_solution
    text = _TODO_RE.sub("", path.read_text())
    if WHY_HEADING in text:
        text = text[: text.index(WHY_HEADING)]
    path.write_text(text.rstrip("\n") + f"\n\n{WHY_HEADING}\n\n{why.strip()}\n")
