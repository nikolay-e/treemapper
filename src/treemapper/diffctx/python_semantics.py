from __future__ import annotations

import ast
import textwrap
from dataclasses import dataclass


@dataclass(frozen=True)
class PyFragmentInfo:
    defines: frozenset[str]
    references: frozenset[str]
    calls: frozenset[str]
    type_refs: frozenset[str]


def _names_from_expr(expr: ast.AST | None) -> set[str]:
    if expr is None:
        return set()
    out: set[str] = set()
    for node in ast.walk(expr):
        if isinstance(node, ast.Name):
            out.add(node.id)
        elif isinstance(node, ast.Attribute):
            out.add(node.attr)
    return out


def analyze_python_fragment(code: str) -> PyFragmentInfo:
    if not code.strip():
        return PyFragmentInfo(frozenset(), frozenset(), frozenset(), frozenset())

    dedented = textwrap.dedent(code)
    try:
        tree = ast.parse(dedented)
    except SyntaxError:
        return PyFragmentInfo(frozenset(), frozenset(), frozenset(), frozenset())

    defines: set[str] = set()
    refs: set[str] = set()
    calls: set[str] = set()
    type_refs: set[str] = set()

    # Only collect top-level definitions (not nested functions/classes)
    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defines.add(stmt.name)

    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            refs.add(node.id)

        if isinstance(node, ast.Attribute):
            refs.add(node.attr)

        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                calls.add(func.id)
            elif isinstance(func, ast.Attribute):
                calls.add(func.attr)

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            type_refs |= _names_from_expr(node.returns)
            for a in node.args.args + node.args.kwonlyargs:
                type_refs |= _names_from_expr(a.annotation)
            if node.args.vararg is not None:
                type_refs |= _names_from_expr(node.args.vararg.annotation)
            if node.args.kwarg is not None:
                type_refs |= _names_from_expr(node.args.kwarg.annotation)

        if isinstance(node, ast.AnnAssign):
            type_refs |= _names_from_expr(node.annotation)

    return PyFragmentInfo(
        defines=frozenset(defines),
        references=frozenset(refs),
        calls=frozenset(calls),
        type_refs=frozenset(type_refs),
    )
