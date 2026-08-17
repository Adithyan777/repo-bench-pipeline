"""Deterministic Python AST indexing — the static facts behind repo_graph.json.

One `.py` file = one module; a directory with `__init__.py` is a package. For every
module we extract classes, functions and methods (file, qualname, line span,
signature, docstring, complexity, is_public, decorators), module- and function-level
imports, inheritance, and intra-repo call sites resolved BY NAME only. Calls that
cannot be resolved to a symbol defined in this repo are kept in a separate list and
never guessed.

Complexity is our own McCabe branch counter (config `graph.complexity_metric`), not
radon: no third-party dependency, version-stable, fully deterministic. Counted
constructs are listed in `_complexity` and documented in HEURISTICS.md.

Test files are indexed separately from the source set (they are needed for the
`tested_by` join) and never contribute source nodes to the graph.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path

from pipeline.config import DEFAULT, Config

# --- module identity ----------------------------------------------------------


def module_name(repo: Path, path: Path) -> str:
    """Importable dotted name of `path`, matching how Python/coverage name it.

    A directory contributes to the dotted name only while it is a package (has
    `__init__.py`). So `mini_pkg/calc.py` -> `mini_pkg.calc`, but `tests/test_x.py`
    (no `tests/__init__.py`) -> `test_x`, which is exactly the module name coverage's
    dynamic contexts report.
    """
    repo = repo.resolve()
    path = path.resolve()
    stem_parts: list[str] = [] if path.name == "__init__.py" else [path.stem]
    directory = path.parent
    while directory != repo and (directory / "__init__.py").exists():
        stem_parts.insert(0, directory.name)
        directory = directory.parent
    return ".".join(stem_parts)


def is_test_path(repo: Path, path: Path, config: Config = DEFAULT) -> bool:
    rel = path.resolve().relative_to(repo.resolve())
    if any(part in config.graph.test_dir_names for part in rel.parts[:-1]):
        return True
    return any(rel.match(glob) for glob in config.graph.test_file_globs)


# --- records ------------------------------------------------------------------


@dataclass
class ImportRef:
    kind: str  # "import" | "from"
    module: str  # dotted module the name comes from
    name: str | None  # imported name (from-imports); None for plain `import x`
    asname: str | None
    line: int
    target_module: str | None = None  # intra-repo module this resolves to, if any


@dataclass
class ModuleRec:
    name: str
    file: str
    is_package: bool
    is_test: bool
    docstring: str | None
    imports: list[ImportRef] = field(default_factory=list)


@dataclass
class ClassRec:
    qualname: str
    module: str
    name: str
    file: str
    line: int
    end_line: int
    docstring: str | None
    decorators: list[str]
    is_public: bool
    bases: list[dict] = field(default_factory=list)  # {"expr", "target"}


@dataclass
class FunctionRec:
    qualname: str
    module: str
    name: str
    file: str
    line: int
    end_line: int
    signature: str
    docstring: str | None
    complexity: int
    is_public: bool
    is_method: bool
    parent: str  # enclosing class qualname, else module name
    decorators: list[str]
    calls: list[dict] = field(default_factory=list)  # {"target", "line"}
    unresolved_calls: list[dict] = field(default_factory=list)  # {"text", "line"}


# --- complexity ---------------------------------------------------------------

_BRANCH_NODES = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.ExceptHandler,
    ast.IfExp,  # ternary
    ast.match_case,
)


def _complexity(node: ast.AST) -> int:
    """McCabe branch count: 1 + decision points.

    +1 for each: if/elif, for, while, except handler, ternary (IfExp), each match
    case, and each boolean operator beyond the first in a BoolOp chain. Each
    comprehension clause adds +1 for its `for` and +1 per `if` filter. Nested
    function/class bodies are counted within their own nodes, not here.
    """
    total = 1
    for child in _walk_own(node):
        if isinstance(child, _BRANCH_NODES):
            total += 1
        elif isinstance(child, ast.BoolOp):
            total += len(child.values) - 1
        elif isinstance(child, ast.comprehension):
            total += 1 + len(child.ifs)
    return total


def _walk_own(node: ast.AST):
    """Walk descendants of a function body but do NOT descend into nested
    function/class definitions (they own their own complexity/nodes)."""
    for _field, value in ast.iter_fields(node):
        items = value if isinstance(value, list) else [value]
        for item in items:
            if isinstance(item, ast.AST):
                yield item
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    continue
                yield from _walk_own(item)


# --- signatures / helpers -----------------------------------------------------


def _signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    args = ast.unparse(node.args)
    ret = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
    return f"{prefix}{node.name}({args}){ret}"


def _decorators(node) -> list[str]:
    return [ast.unparse(d) for d in node.decorator_list]


def _is_public(name: str) -> bool:
    return not name.startswith("_")


def _own_calls(node: ast.AST):
    """Call nodes made directly by this function (not inside nested defs)."""
    for child in _walk_own(node):
        if isinstance(child, ast.Call):
            yield child


# --- the indexer --------------------------------------------------------------


class _Indexer:
    def __init__(self, repo: Path, config: Config) -> None:
        self.repo = repo.resolve()
        self.config = config
        self.modules: dict[str, ModuleRec] = {}
        self.classes: list[ClassRec] = []
        self.functions: list[FunctionRec] = []
        # per-module import resolution tables, filled in pass 1
        self._from_imports: dict[str, dict[str, str]] = {}  # module -> {local: dotted}
        self._module_aliases: dict[str, dict[str, str]] = {}  # module -> {alias: dotted mod}
        self._top_defs: dict[str, dict[str, str]] = {}  # module -> {name: qualname}
        self._method_owner: dict[str, str] = {}  # method qual -> class qual
        self._pending: list[tuple] = []  # (FunctionRec, ast node, module)

    def build(self) -> dict:
        files = sorted(
            p for p in self.repo.rglob("*.py") if ".git" not in p.parts and p.is_file()
        )
        parsed = []
        for path in files:
            try:
                tree = ast.parse(path.read_text(errors="replace"))
            except SyntaxError:
                continue
            mod = module_name(self.repo, path)
            parsed.append((mod, path, tree))
            self._register_module(mod, path, tree)  # pass 1: every module known first
        for mod, path, tree in parsed:  # pass 2: imports + defs, order-independent
            self._collect_module(mod, path, tree)
        self._finalize_imports()  # resolve intra-repo targets now that all modules are known
        self._function_quals = {f.qualname for f in self.functions}
        self._class_quals = {c.qualname for c in self.classes}
        self._module_set = set(self.modules)
        for rec, node, mod in self._pending:
            self._resolve_calls(rec, node, mod)
        return self._emit()

    # pass 1: register every module (name + is_package) before any import is parsed
    # so relative-import resolution never depends on file order.
    def _register_module(self, mod: str, path: Path, tree: ast.Module) -> None:
        self.modules[mod] = ModuleRec(
            name=mod,
            file=str(path.resolve().relative_to(self.repo)),
            is_package=path.name == "__init__.py",
            is_test=is_test_path(self.repo, path, self.config),
            docstring=ast.get_docstring(tree),
        )
        self._from_imports.setdefault(mod, {})
        self._module_aliases.setdefault(mod, {})
        self._top_defs.setdefault(mod, {})

    # pass 2: collect imports and definitions
    def _collect_module(self, mod: str, path: Path, tree: ast.Module) -> None:
        rel = self.modules[mod].file
        for node in tree.body:
            self._collect_import(mod, node)
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._add_function(mod, rel, node, parent=mod, is_method=False)
                self._top_defs[mod][node.name] = f"{mod}.{node.name}"
            elif isinstance(node, ast.ClassDef):
                self._add_class(mod, rel, node)
                self._top_defs[mod][node.name] = f"{mod}.{node.name}"

    def _collect_import(self, mod: str, node: ast.AST) -> None:
        rec = self.modules[mod]
        if isinstance(node, ast.Import):
            for alias in node.names:
                rec.imports.append(
                    ImportRef("import", alias.name, None, alias.asname, node.lineno, None)
                )
                if alias.asname:
                    # `import a.b as c` binds `c` -> module a.b
                    self._module_aliases[mod][alias.asname] = alias.name
                else:
                    # `import a.b` binds only the TOP package `a`; a.b.f is an attr chain
                    top = alias.name.split(".")[0]
                    self._module_aliases[mod][top] = top
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                source = node.module
            else:
                base = self._relative_base(mod, node.level)
                if base is None:
                    return  # climbed past the top package; unresolvable
                source = f"{base}.{node.module}" if node.module else base
            if not source:
                return
            for alias in node.names:
                local = alias.asname or alias.name
                dotted = f"{source}.{alias.name}" if source else alias.name
                rec.imports.append(
                    ImportRef("from", source, alias.name, alias.asname, node.lineno, None)
                )
                self._from_imports[mod][local] = dotted

    def _relative_base(self, mod: str, level: int) -> str | None:
        """Absolute package a relative import (`from ..x import y`) resolves against."""
        rec = self.modules.get(mod)
        parts = mod.split(".")
        if rec is not None and not rec.is_package:
            parts = parts[:-1]  # a module's package is its parent
        drop = level - 1
        if drop > len(parts):
            return None
        base_parts = parts[: len(parts) - drop] if drop else parts
        return ".".join(base_parts)

    def _finalize_imports(self) -> None:
        """Set each import's intra-repo target module once all modules are known.

        A `from pkg.sub import name` resolves to module `pkg.sub`; if `pkg.sub.name`
        is itself a submodule (package re-export), that submodule is preferred.
        """
        universe = self._all_module_names()
        for rec in self.modules.values():
            for imp in rec.imports:
                if imp.kind == "import":
                    imp.target_module = imp.module if imp.module in universe else None
                else:
                    submodule = f"{imp.module}.{imp.name}"
                    if submodule in universe:
                        imp.target_module = submodule
                    elif imp.module in universe:
                        imp.target_module = imp.module

    def _all_module_names(self) -> set[str]:
        names: set[str] = set()
        for m in self.modules:
            parts = m.split(".")
            for i in range(1, len(parts) + 1):
                names.add(".".join(parts[:i]))
        return names

    def _add_class(self, mod: str, rel: str, node: ast.ClassDef) -> None:
        qual = f"{mod}.{node.name}"
        bases = [{"expr": ast.unparse(b), "target": None} for b in node.bases]
        self.classes.append(
            ClassRec(
                qualname=qual,
                module=mod,
                name=node.name,
                file=rel,
                line=node.lineno,
                end_line=node.end_lineno or node.lineno,
                docstring=ast.get_docstring(node),
                decorators=_decorators(node),
                is_public=_is_public(node.name),
                bases=bases,
            )
        )
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._add_function(mod, rel, child, parent=qual, is_method=True)
                self._method_owner[f"{qual}.{child.name}"] = qual

    def _add_function(
        self, mod: str, rel: str, node, parent: str, is_method: bool
    ) -> None:
        qual = f"{parent}.{node.name}"
        rec = FunctionRec(
            qualname=qual,
            module=mod,
            name=node.name,
            file=rel,
            line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            signature=_signature(node),
            docstring=ast.get_docstring(node),
            complexity=_complexity(node),
            is_public=_is_public(node.name),
            is_method=is_method,
            parent=parent,
            decorators=_decorators(node),
        )
        self.functions.append(rec)
        self._pending.append((rec, node, mod))

    # pass 2: resolve calls ----------------------------------------------------

    def _resolve_calls(self, rec: FunctionRec, node: ast.AST, mod: str) -> None:
        enclosing_class = rec.parent if rec.is_method else None
        for call in _own_calls(node):
            target = self._resolve_one(call.func, mod, enclosing_class)
            if target is not None:
                rec.calls.append({"target": target, "line": call.lineno})
            else:
                rec.unresolved_calls.append(
                    {"text": ast.unparse(call.func), "line": call.lineno}
                )
        rec.calls = _dedup_sorted(rec.calls, ("target", "line"))
        rec.unresolved_calls = _dedup_sorted(rec.unresolved_calls, ("text", "line"))

    def _resolve_one(self, func: ast.AST, mod: str, enclosing_class: str | None) -> str | None:
        if isinstance(func, ast.Name):
            return self._resolve_name(func.id, mod)
        if isinstance(func, ast.Attribute):
            if (
                isinstance(func.value, ast.Name)
                and func.value.id == "self"
                and enclosing_class
            ):
                cand = f"{enclosing_class}.{func.attr}"
                return cand if cand in self._function_quals else None
            return self._resolve_attr_chain(func, mod)
        return None

    def _resolve_attr_chain(self, func: ast.Attribute, mod: str) -> str | None:
        """Resolve a dotted call like `pkg.sub.func()` by mapping the base name to an
        intra-repo module and checking the full path names a repo symbol."""
        attrs: list[str] = []
        node: ast.AST = func
        while isinstance(node, ast.Attribute):
            attrs.append(node.attr)
            node = node.value
        if not isinstance(node, ast.Name):
            return None  # base is a call/subscript/... — not a module reference
        attrs.append(node.id)
        attrs.reverse()  # [base, attr, attr, ...]
        aliases = self._module_aliases.get(mod, {})
        froms = self._from_imports.get(mod, {})
        base = attrs[0]
        if base in aliases:
            head = aliases[base].split(".")
        elif base in froms and froms[base] in self._module_set:
            head = froms[base].split(".")
        else:
            return None  # base does not refer to an intra-repo module
        dotted = ".".join(head + attrs[1:])
        return dotted if self._exists(dotted) else None

    def _resolve_name(self, name: str, mod: str) -> str | None:
        local = self._top_defs.get(mod, {}).get(name)
        if local and self._exists(local):
            return local
        dotted = self._from_imports.get(mod, {}).get(name)
        if dotted and self._exists(dotted):
            return dotted
        return None

    def _exists(self, qual: str) -> bool:
        return qual in self._function_quals or qual in self._class_quals

    # emit ---------------------------------------------------------------------

    def _emit(self) -> dict:
        for cls in self.classes:
            for base in cls.bases:
                base["target"] = self._resolve_base(base["expr"], cls.module)
        modules = [
            {
                "name": m.name,
                "file": m.file,
                "is_package": m.is_package,
                "is_test": m.is_test,
                "docstring": m.docstring,
                "imports": [vars(i) for i in m.imports],
            }
            for m in sorted(self.modules.values(), key=lambda m: m.name)
        ]
        classes = [vars(c) for c in sorted(self.classes, key=lambda c: c.qualname)]
        functions = [vars(f) for f in sorted(self.functions, key=lambda f: (f.qualname, f.line))]
        return {"modules": modules, "classes": classes, "functions": functions}

    def _resolve_base(self, expr: str, mod: str) -> str | None:
        # bare Name base (e.g. `Registry`) or dotted (`mod.Base`)
        head = expr.split(".")[0]
        if "." not in expr:
            cand = self._top_defs.get(mod, {}).get(expr) or self._from_imports.get(mod, {}).get(
                expr
            )
            return cand if cand and cand in self._class_quals else None
        target_mod = self._module_aliases.get(mod, {}).get(head)
        if target_mod:
            cand = f"{target_mod}.{expr.split('.', 1)[1]}"
            return cand if cand in self._class_quals else None
        return None


def _dedup_sorted(items: list[dict], keys: tuple[str, ...]) -> list[dict]:
    seen: set[tuple] = set()
    out: list[dict] = []
    for item in sorted(items, key=lambda d: tuple(str(d[k]) for k in keys)):
        sig = tuple(item[k] for k in keys)
        if sig not in seen:
            seen.add(sig)
            out.append(item)
    return out


def build_symbol_index(repo: Path, config: Config = DEFAULT) -> dict:
    """Static AST facts for the whole repo. Deterministic; no LLM, no container."""
    return _Indexer(Path(repo), config).build()


# --- historical-commit helpers (used by history_index) ------------------------


def path_to_module(rel_path: str, source_roots: tuple[str, ...] = ()) -> str:
    """Best-effort dotted module name from a repo-relative path (no filesystem access,
    for historical blobs where package layout can't be probed cheaply). A leading
    src-layout root is stripped so the name matches the graph's package-aware naming
    (e.g. src/pkg/mod.py -> pkg.mod)."""
    stem = rel_path[:-3] if rel_path.endswith(".py") else rel_path
    if stem.endswith("/__init__"):
        stem = stem[: -len("/__init__")]
    parts = stem.split("/")
    if parts and parts[0] in source_roots:
        parts = parts[1:]
    return ".".join(parts)


def functions_in_source(source: str, module: str) -> list[dict]:
    """Function/method spans in one source string: {qualname, line, end_line}.

    Used to resolve diff hunks to functions at a historical commit — parse the file
    as it was, never reuse HEAD spans.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    out: list[dict] = []

    def visit(body, parent: str) -> None:
        for child in body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out.append(
                    {
                        "qualname": f"{parent}.{child.name}",
                        "line": child.lineno,
                        "end_line": child.end_lineno or child.lineno,
                    }
                )
            elif isinstance(child, ast.ClassDef):
                visit(child.body, f"{parent}.{child.name}")

    visit(tree.body, module)
    return out
