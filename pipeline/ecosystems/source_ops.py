"""Python source operations for P3 (ecosystem-specific, pure AST, no LLM).

- ``excise_function``: replace one function body by line-span splice; everything
  outside the body is preserved byte-for-byte (decorators, signature, docstring,
  comments, other definitions).
- ``module_bound_names``: names a module binds at top level (defs, classes,
  assignments, imports, star-import expansion) -- the harness static gate.
- ``verifier_imports`` / ``count_assertions``: facts about verifier test files.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


class ExciseError(ValueError):
    """The target cannot be spliced without touching other code."""


@dataclass(frozen=True)
class Excision:
    source: str  # rewritten file
    body_start: int  # first replaced line (1-based)
    body_end: int  # last replaced line (inclusive)
    kept_docstring: bool


def _find_def(tree: ast.Module, path: list[str]) -> ast.AST | None:
    node: ast.AST = tree
    for part in path:
        found = None
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                if child.name == part:
                    found = child  # last definition wins (rebinding), like the graph
        if found is None:
            return None
        node = found
    return node


def _has_docstring(node: ast.AST) -> bool:
    body = getattr(node, "body", [])
    return bool(
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    )


def excise_function(
    source: str,
    qualpath: list[str],
    replacement: str,
    keep_docstring: bool = True,
) -> Excision:
    """Replace the body of the def at ``qualpath`` (names below the module) with
    ``replacement`` (one statement). Raises ExciseError when the def is missing or
    its body shares a line with the signature (one-liners cannot be spliced)."""
    tree = ast.parse(source)
    node = _find_def(tree, qualpath)
    if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
        raise ExciseError(f"no function {'.'.join(qualpath)}")
    keep = keep_docstring and _has_docstring(node)
    stmts = node.body[1:] if keep else node.body
    if not stmts:  # docstring-only body: nothing to excise
        raise ExciseError(f"{'.'.join(qualpath)} has no body beyond its docstring")
    first, last = stmts[0], stmts[-1]
    header_end = node.lineno
    for sub in [*ast.walk(node.args), *([node.returns] if node.returns else [])]:
        header_end = max(header_end, getattr(sub, "end_lineno", 0) or 0)
    if keep:
        header_end = max(header_end, node.body[0].end_lineno or 0)
    if first.lineno <= header_end:
        raise ExciseError(f"{'.'.join(qualpath)} body shares a line with its header")
    lines = source.splitlines(keepends=True)
    start, end = first.lineno, last.end_lineno or last.lineno
    indent = lines[start - 1][: first.col_offset]
    newline = "\r\n" if lines[start - 1].endswith("\r\n") else "\n"
    new_body = "".join(f"{indent}{stmt}{newline}" for stmt in replacement.splitlines())
    rewritten = "".join(lines[: start - 1]) + new_body + "".join(lines[end:])
    return Excision(rewritten, start, end, keep)


def module_bound_names(source: str) -> tuple[set[str], list[str]]:
    """Top-level names a module binds, plus modules it star-imports (unexpanded)."""
    names: set[str] = set()
    stars: list[str] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return names, stars

    def visit(stmts: list[ast.stmt]) -> None:
        for stmt in stmts:
            if isinstance(stmt, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                names.add(stmt.name)
            elif isinstance(stmt, ast.Import):
                names.update((a.asname or a.name).split(".")[0] for a in stmt.names)
            elif isinstance(stmt, ast.ImportFrom):
                for alias in stmt.names:
                    if alias.name == "*":
                        stars.append(f"{'.' * stmt.level}{stmt.module or ''}")
                    else:
                        names.add(alias.asname or alias.name)
            elif isinstance(stmt, ast.Assign | ast.AnnAssign | ast.AugAssign):
                targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
                for target in targets:
                    for node in ast.walk(target):
                        if isinstance(node, ast.Name):
                            names.add(node.id)
            elif isinstance(stmt, ast.If | ast.Try | ast.With | ast.For | ast.While):
                for field in ("body", "orelse", "finalbody", "handlers"):
                    block = getattr(stmt, field, [])
                    visit([b for b in block if not isinstance(b, ast.ExceptHandler)])
                    for h in block:
                        if isinstance(h, ast.ExceptHandler):
                            visit(h.body)

    visit(tree.body)
    return names, stars


@dataclass(frozen=True)
class ImportUse:
    module: str  # absolute dotted module (relative imports resolved by the caller)
    name: str | None  # None for `import module`
    line: int


def verifier_imports(source: str, package: str) -> list[ImportUse]:
    """Import statements of a test file; relative imports resolved against ``package``
    (the dotted package the file lives in, '' for top-level)."""
    uses: list[ImportUse] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return uses
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            uses.extend(ImportUse(a.name, None, node.lineno) for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package.split(".")[: len(package.split(".")) - node.level + 1]
                module = ".".join(p for p in [*base, node.module or ""] if p)
            else:
                module = node.module or ""
            for alias in node.names:
                uses.append(ImportUse(module, alias.name, node.lineno))
    return uses


def private_getattr_names(source: str, module_names: set[str]) -> list[tuple[int, str]]:
    """``getattr(<module>, "_name")`` / ``hasattr`` on one of ``module_names`` (names bound
    to repo modules in this file) with a private, non-dunder literal: (line, name)."""
    out: list[tuple[int, str]] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in ("getattr", "hasattr")
            and len(node.args) >= 2
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id in module_names
            and isinstance(node.args[1], ast.Constant)
            and isinstance(node.args[1].value, str)
        ):
            continue
        name = node.args[1].value
        if name.startswith("_") and not (name.startswith("__") and name.endswith("__")):
            out.append((node.lineno, name))
    return out


def count_assertions(source: str, test_names: set[str] | None = None) -> int:
    """`assert` statements + `pytest.raises` blocks inside the named test functions
    (all functions when ``test_names`` is None)."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return 0
    total = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if test_names is not None and node.name not in test_names:
            continue
        for child in ast.walk(node):
            if isinstance(child, ast.Assert):
                total += 1
            elif isinstance(child, ast.Call) and "raises" in ast.unparse(child.func):
                total += 1
    return total


def test_functions_in(source: str) -> list[str]:
    """Names of top-level / class-level test functions (pytest naming) in a file."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name.startswith(
            "test"
        ):
            out.append(node.name)
    return out


def _test_defs(source: str) -> dict[str, str]:
    """``Class::name`` / ``name`` -> normalized AST dump for every test function."""
    out: dict[str, str] = {}
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return out

    def visit(body: list[ast.stmt], prefix: str) -> None:
        for node in body:
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                if node.name.startswith("test"):
                    out[f"{prefix}{node.name}"] = ast.dump(node)
            elif isinstance(node, ast.ClassDef):
                visit(node.body, f"{prefix}{node.name}::")

    visit(tree.body, "")
    return out


def test_nodeid_suffixes(source: str) -> list[str]:
    """Every test function as a pytest nodeid suffix (``name`` or ``Class::name``)."""
    return sorted(_test_defs(source))


def changed_test_functions(old_source: str | None, new_source: str) -> list[str]:
    """Test functions added or changed between two versions of a test file, as nodeid
    suffixes (``name`` or ``Class::name``). Formatting-only edits do not count (AST
    dumps are compared)."""
    before = _test_defs(old_source) if old_source is not None else {}
    after = _test_defs(new_source)
    return sorted(k for k, dump in after.items() if before.get(k) != dump)


def function_contracts(source: str, module: str) -> list[dict]:
    """Signature + docstring of every function/method as written in ``source``:
    ``{qualname, signature, docstring, line, end_line, is_public}``."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    out: list[dict] = []

    def visit(body: list[ast.stmt], parent: str) -> None:
        for node in body:
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                qual = f"{parent}.{node.name}"
                out.append(
                    {
                        "qualname": qual,
                        "signature": f"{node.name}({ast.unparse(node.args)})",
                        "docstring": ast.get_docstring(node),
                        "line": node.lineno,
                        "end_line": node.end_lineno or node.lineno,
                        "is_public": not any(
                            p.startswith("_") for p in qual[len(module) + 1 :].split(".")
                        ),
                    }
                )
                visit(node.body, qual)
            elif isinstance(node, ast.ClassDef):
                visit(node.body, f"{parent}.{node.name}")

    visit(tree.body, module)
    return out


def defined_names(source: str) -> set[str]:
    """Every def/class/assigned/imported name in a module, at any nesting depth."""
    names: set[str] = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return names
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.alias):
            names.add((node.asname or node.name).split(".")[0])
    return names


def new_identifiers(old_source: str | None, new_source: str) -> set[str]:
    """Identifiers the new version introduces (defs, classes, bindings, imports)."""
    return defined_names(new_source) - (defined_names(old_source) if old_source else set())


def read_source(path: Path) -> str:
    """Strict UTF-8, newlines untouched (CRLF survives a round trip)."""
    with Path(path).open(encoding="utf-8", newline="") as fh:
        return fh.read()


def write_source(path: Path, text: str) -> None:
    with Path(path).open("w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def is_private_dotted(name: str) -> bool:
    """Any dotted component starting with '_' (``pkg._impl.f``, ``mod._helper``)."""
    return any(part.startswith("_") for part in name.split(".") if part)


def private_repo_imports(source: str, package: str, top_packages: set[str]) -> list[str]:
    """Imports of private repo modules/symbols in a test file: ``pkg._x``, ``from pkg.m
    import _y``. Shared by the funnel pre-gate and the harness static gate."""
    out: list[str] = []
    for use in verifier_imports(source, package):
        if use.module.split(".")[0] not in top_packages:
            continue
        target = use.module if use.name is None else f"{use.module}.{use.name}"
        if use.name != "*" and is_private_dotted(target):
            out.append(target)
    return sorted(set(out))
