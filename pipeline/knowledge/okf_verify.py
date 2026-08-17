"""Step 4.2 verifier: re-check OKF claims against the AST + graph.

Page stamping: >= 1 checked claim, all supported -> ``verified: [...]`` + ``status:
stable``; anything unsupported or nothing checkable -> ``status: draft``. Prose-only
fields (inputs/outputs/invariants) are never checked; listed in okf_verification.json.
Semantic checks: raises (claimed exception raised in the function or a one-hop callee;
``none`` rejected only if the function's OWN body raises), side_effects ``none``
(no global/nonlocal writes, attribute stores, IO-like calls), callees (name appears as
``ast.Call``). callers/links are by-construction and reported separately.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from pipeline.ecosystems.source_ops import _find_def
from pipeline.knowledge.okf import Graph, _base_at, _module_of, bundle_dir, page, parse_frontmatter

_RESERVED = {"index.md", "log.md"}
_UNCHECKED_KINDS = ["inputs", "outputs", "invariants"]
_SEMANTIC_KINDS = ["raises", "side_effects", "callees"]
_BY_CONSTRUCTION_KINDS = ["callers", "link"]

_H1_RE = re.compile(r"^# `([^`]+)`", re.M)
_CONTRACT_RE = re.compile(r"^- \*\*(\w+)\*\*: (.*)$", re.M)
_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
_SECTION_LINK_RE = re.compile(r"^## (Callers|Callees)\n(.+)$", re.M)
_TITLE_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_CODE_RE = re.compile(r"`([^`]+)`")


# --- AST truth ----------------------------------------------------------------


def _qualpath(graph: Graph, qual: str) -> list[str]:
    node = graph.nodes.get(qual)
    if not node:
        return qual.split(".")
    module = _module_of(qual, node)
    return qual[len(module) + 1 :].split(".") if qual.startswith(module + ".") else [qual]


def _func_ast(repo: Path, graph: Graph, qual: str) -> ast.AST | None:
    node = graph.nodes.get(qual)
    if not node:
        return None
    try:
        tree = ast.parse((repo / node["file"]).read_text(errors="replace"))
    except (OSError, SyntaxError):
        return None
    fn = _find_def(tree, _qualpath(graph, qual))
    return fn if isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef) else None


def _name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call):
        node = node.func
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _raises_in(fn: ast.AST) -> set[str]:
    return {
        _name(s.exc)
        for s in ast.walk(fn)
        if isinstance(s, ast.Raise) and s.exc is not None and _name(s.exc)
    }


def own_raises(repo: Path, graph: Graph, qual: str) -> set[str]:
    fn = _func_ast(repo, graph, qual)
    return _raises_in(fn) if fn else set()


def raises_truth(repo: Path, graph: Graph, qual: str) -> set[str]:
    """Own explicit raises + those of one-hop intra-repo callees (for positive claims)."""
    out = set(own_raises(repo, graph, qual))
    for callee in graph.callees(qual):
        out |= own_raises(repo, graph, callee)
    return out


def called_names(repo: Path, graph: Graph, qual: str) -> set[str]:
    fn = _func_ast(repo, graph, qual)
    if fn is None:
        return set()
    return {_name(s) for s in ast.walk(fn) if isinstance(s, ast.Call) and _name(s)}


def has_side_effects(repo: Path, graph: Graph, qual: str, config) -> bool:
    fn = _func_ast(repo, graph, qual)
    if fn is None:
        return False
    io_names = set(config.okf.side_effect_call_names)
    for sub in ast.walk(fn):
        if isinstance(sub, ast.Global | ast.Nonlocal):
            return True
        if isinstance(sub, ast.Attribute) and isinstance(sub.ctx, ast.Store):
            return True
        if isinstance(sub, ast.Call) and _name(sub.func) in io_names:
            return True
    return False


# --- page claims --------------------------------------------------------------


def _page_qual(body: str) -> str | None:
    m = _H1_RE.search(body)
    return m.group(1) if m else None


def _contract(body: str) -> dict:
    fields = dict(_CONTRACT_RE.findall(body))
    raises = fields.get("raises", "none")
    raised = [] if raises.strip().lower() == "none" else [r.strip() for r in raises.split(",")]
    return {"raises": [r for r in raised if r], "side_effects": fields.get("side_effects", "")}


def _linked_quals(body: str, section: str, graph: Graph) -> list[str]:
    """Qualnames referenced in a Callers/Callees section (links or inline code)."""
    for label, rest in _SECTION_LINK_RE.findall(body):
        if label != section:
            continue
        quals = _TITLE_RE.findall(rest) + _CODE_RE.findall(rest)
        return [q for q in quals if q in graph.nodes]
    return []


# --- conformance --------------------------------------------------------------


def check_conformance(bundle: Path) -> dict:
    issues: list[dict] = []
    for md in sorted(bundle.rglob("*.md")):
        rel = str(md.relative_to(bundle))
        fm, _ = parse_frontmatter(md.read_text())
        if rel in _RESERVED:
            if rel == "index.md" and "okf_version" not in fm:
                issues.append({"page": rel, "issue": "index.md missing okf_version"})
            continue
        if not fm:
            issues.append({"page": rel, "issue": "no parseable frontmatter"})
        elif not fm.get("type"):
            issues.append({"page": rel, "issue": "empty or missing type"})
    return {"conformant": not issues, "issues": issues}


# --- verify -------------------------------------------------------------------


class _Tally:
    def __init__(self):
        self.total: dict[str, int] = {}
        self.ok: dict[str, int] = {}

    def add(self, kind: str, ok: bool) -> None:
        self.total[kind] = self.total.get(kind, 0) + 1
        self.ok[kind] = self.ok.get(kind, 0) + int(ok)

    def precision(self, kinds) -> dict:
        return {k: round(self.ok[k] / self.total[k], 3) for k in kinds if k in self.total}

    def counts(self, kinds) -> dict:
        return {k: self.total[k] for k in kinds if k in self.total}


def verify_okf(ctx, graph_json: dict) -> dict:
    graph = Graph(graph_json)
    bundle = bundle_dir(ctx)
    at, config = _base_at(ctx), ctx.config
    verifier = config.okf.verifier_actor
    tally = _Tally()
    unsupported: list[dict] = []
    verified_pages = draft_pages = 0

    for md in sorted(bundle.glob("functions/*/*.md")):
        fm, body = parse_frontmatter(md.read_text())
        qual = _page_qual(body)
        issues, checks = _verify_page(ctx, graph, qual, body, md, tally, config)

        if issues or not checks:
            draft_pages += 1
            fm["status"], fm["verified"] = config.okf.unverified_status, []
            if issues:
                unsupported.append({"page": str(md.relative_to(bundle)), "unsupported": issues})
        else:
            verified_pages += 1
            fm["verified"] = [{"by": verifier, "at": at, "checks": sorted(checks)}]
            fm["status"] = config.okf.verified_status
        md.write_text(page(fm, body))

    return {
        "verifier": verifier,
        "pages_verified": verified_pages,
        "pages_draft": draft_pages,
        "precision_by_claim": tally.precision(_SEMANTIC_KINDS),
        "claim_counts": tally.counts(_SEMANTIC_KINDS),
        "by_construction": {
            "precision": tally.precision(_BY_CONSTRUCTION_KINDS),
            "counts": tally.counts(_BY_CONSTRUCTION_KINDS),
            "note": "graph-derived / structural; true by construction, not independent evidence",
        },
        "unchecked_claim_kinds": _UNCHECKED_KINDS,
        "unsupported": unsupported,
        "conformance": check_conformance(bundle),
    }


def _verify_page(ctx, graph, qual, body, md, tally, config) -> tuple[list[str], set[str]]:
    """Return (unsupported issues, kinds actually checked) for one function page."""
    issues: list[str] = []
    checks: set[str] = set()
    if qual not in graph.nodes:
        return ["unknown-qualname"], checks
    contract = _contract(body)

    # raises: "none" is rejected only if the function's OWN body raises.
    truth = raises_truth(ctx.repo, graph, qual)
    if contract["raises"]:
        checks.add("raises")
        for exc in contract["raises"]:
            ok = exc in truth
            tally.add("raises", ok)
            if not ok:
                issues.append(f"raises:{exc}")
    else:
        missing = sorted(own_raises(ctx.repo, graph, qual))
        if missing:
            checks.add("raises")
            tally.add("raises", False)
            issues.append(f"raises:missing:{','.join(missing)}")

    # side_effects (semantic): only the "none" claim is machine-checkable
    se = contract["side_effects"].strip().lower()
    if se in ("none", ""):
        ok = not has_side_effects(ctx.repo, graph, qual, config)
        checks.add("side_effects")
        tally.add("side_effects", ok)
        if not ok:
            issues.append("side_effects:claims-none")

    # callees (semantic): each linked callee must appear as an ast.Call in the function
    calls = called_names(ctx.repo, graph, qual)
    for c in _linked_quals(body, "Callees", graph):
        ok = c.split(".")[-1] in calls
        checks.add("callees")
        tally.add("callees", ok)
        if not ok:
            issues.append(f"callees:{c}")

    # callers (by_construction): must be a real caller edge
    for c in _linked_quals(body, "Callers", graph):
        ok = c in set(graph.callers(qual))
        checks.add("callers")
        tally.add("callers", ok)
        if not ok:
            issues.append(f"callers:{c}")

    # links (by_construction): every bundle (*.md) link must resolve
    for target in _LINK_RE.findall(body):
        page_target = target.split("#", 1)[0]
        if not page_target.endswith(".md"):
            continue  # links inside model prose are not link claims
        ok = (md.parent / page_target).resolve().is_file()
        checks.add("link")
        tally.add("link", ok)
        if not ok:
            issues.append(f"link:{target}")

    return issues, checks
