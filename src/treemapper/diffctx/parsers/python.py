from __future__ import annotations

import ast
from pathlib import Path

from ..types import Fragment, FragmentId, extract_identifiers
from .base import MIN_FRAGMENT_LINES, create_code_gap_fragments


class PythonAstStrategy:
    priority = 95

    def can_handle(self, path: Path, _content: str) -> bool:
        return path.suffix.lower() in {".py", ".pyw", ".pyi"}

    def fragment(self, path: Path, content: str) -> list[Fragment]:
        lines = content.splitlines()
        if not lines:
            return []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return []

        fragments: list[Fragment] = []
        covered: list[tuple[int, int]] = []

        for node in ast.walk(tree):
            frag = None
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                frag = self._create_function_fragment(path, lines, node)
            elif isinstance(node, ast.ClassDef):
                frag = self._create_class_fragment(path, lines, node)

            if frag:
                fragments.append(frag)
                covered.append((frag.start_line, frag.end_line))

        fragments.extend(create_code_gap_fragments(path, lines, covered))
        return fragments

    def _create_function_fragment(
        self, path: Path, lines: list[str], node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> Fragment | None:
        if not hasattr(node, "lineno") or not hasattr(node, "end_lineno") or node.end_lineno is None:
            return None

        start = max(1, node.lineno)
        for dec in getattr(node, "decorator_list", []) or []:
            dec_line = getattr(dec, "lineno", None)
            if isinstance(dec_line, int):
                start = min(start, dec_line)

        end = max(start, node.end_lineno)

        if end - start + 1 < MIN_FRAGMENT_LINES:
            return None

        snippet = "\n".join(lines[start - 1 : end])
        if not snippet.endswith("\n"):
            snippet += "\n"

        return Fragment(
            id=FragmentId(path=path, start_line=start, end_line=end),
            kind="function",
            content=snippet,
            identifiers=extract_identifiers(snippet, profile="code"),
        )

    def _create_class_fragment(self, path: Path, lines: list[str], node: ast.ClassDef) -> Fragment | None:
        if not hasattr(node, "lineno") or not hasattr(node, "end_lineno") or node.end_lineno is None:
            return None

        start = max(1, node.lineno)
        for dec in getattr(node, "decorator_list", []) or []:
            dec_line = getattr(dec, "lineno", None)
            if isinstance(dec_line, int):
                start = min(start, dec_line)

        end = max(start, node.end_lineno)

        if end - start + 1 < MIN_FRAGMENT_LINES:
            return None

        snippet = "\n".join(lines[start - 1 : end])
        if not snippet.endswith("\n"):
            snippet += "\n"

        return Fragment(
            id=FragmentId(path=path, start_line=start, end_line=end),
            kind="class",
            content=snippet,
            identifiers=extract_identifiers(snippet, profile="code"),
        )
