"""Mutation driver (ecosystem-agnostic): whole-file mutants from a function's line span
and the adapter's AST mutators. Only the span is spliced, so mutants are byte-identical
elsewhere. Selection is deterministic: interleave across operators, take the first ``count``.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Mutant:
    operator: str
    index: int  # stable ordinal within a function's selected mutants
    source: str  # the whole file with one function mutated


def _splice(lines: list[str], start: int, end: int, replacement: str) -> str:
    """Replace 1-based lines ``[start, end]`` with ``replacement``; rest preserved byte-for-byte."""
    newline = "\r\n" if lines and lines[0].endswith("\r\n") else "\n"
    body = replacement if replacement.endswith(("\n", "\r\n")) else replacement + newline
    if newline == "\r\n":
        body = body.replace("\r\n", "\n").replace("\n", "\r\n")
    return "".join(lines[: start - 1]) + body + "".join(lines[end:])


def function_mutants(
    file_source: str,
    line: int,
    end_line: int,
    mutators: list[Callable[[str], list[str]]],
    count: int,
) -> list[Mutant]:
    """Up to ``count`` mutants of the function spanning ``[line, end_line]``."""
    lines = file_source.splitlines(keepends=True)
    if line < 1 or end_line > len(lines) or line > end_line:
        return []
    span = "".join(lines[line - 1 : end_line])
    per_operator: list[tuple[str, list[str]]] = []
    for fn in mutators:
        variants = fn(span)
        if variants:
            per_operator.append((getattr(fn, "__name__", "mutator"), variants))
    selected: list[tuple[str, str]] = []
    depth = 0
    while len(selected) < count and per_operator:
        progressed = False
        for name, variants in per_operator:
            if depth < len(variants):
                selected.append((name, variants[depth]))
                progressed = True
                if len(selected) >= count:
                    break
        if not progressed:
            break
        depth += 1
    return [
        Mutant(operator=name, index=i, source=_splice(lines, line, end_line, span_mut))
        for i, (name, span_mut) in enumerate(selected)
    ]
