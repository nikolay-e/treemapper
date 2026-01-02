from __future__ import annotations

import ast
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from .stopwords import TokenProfile
from .types import Fragment, FragmentId, extract_identifiers

_MIN_FRAGMENT_LINES = 2
_GENERIC_MAX_LINES = 200
_MIN_FRAGMENT_WORDS = 10


@dataclass
class Fragmenter(ABC):
    priority: int = 0

    @abstractmethod
    def can_handle(self, path: Path) -> bool: ...

    @abstractmethod
    def fragment(self, path: Path, content: str) -> list[Fragment]: ...


class PythonFragmenter(Fragmenter):
    priority = 100

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() == ".py"

    def fragment(self, path: Path, content: str) -> list[Fragment]:
        lines = content.splitlines()
        if not lines:
            return []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return GenericFragmenter().fragment(path, content)

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

        fragments.extend(self._create_gap_fragments(path, lines, covered))

        return fragments if fragments else GenericFragmenter().fragment(path, content)

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

        if end - start + 1 < _MIN_FRAGMENT_LINES:
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

        if end - start + 1 < _MIN_FRAGMENT_LINES:
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

    def _create_gap_fragments(self, path: Path, lines: list[str], covered: list[tuple[int, int]]) -> list[Fragment]:
        if not lines:
            return []

        covered_set: set[int] = set()
        for start, end in covered:
            covered_set.update(range(start, end + 1))

        uncovered_lines: list[int] = []
        for ln in range(1, len(lines) + 1):
            if ln not in covered_set:
                uncovered_lines.append(ln)

        if not uncovered_lines:
            return []

        gaps: list[tuple[int, int]] = []
        gap_start = uncovered_lines[0]
        gap_end = uncovered_lines[0]

        for ln in uncovered_lines[1:]:
            if ln == gap_end + 1:
                gap_end = ln
            else:
                gaps.append((gap_start, gap_end))
                gap_start = ln
                gap_end = ln
        gaps.append((gap_start, gap_end))

        fragments: list[Fragment] = []
        for start, end in gaps:
            while start <= end and not lines[start - 1].strip():
                start += 1
            while end >= start and not lines[end - 1].strip():
                end -= 1

            if start > end:
                continue

            if end - start + 1 < _MIN_FRAGMENT_LINES:
                continue

            snippet = "\n".join(lines[start - 1 : end])
            if not snippet.strip():
                continue
            if not snippet.endswith("\n"):
                snippet += "\n"

            fragments.append(
                Fragment(
                    id=FragmentId(path=path, start_line=start, end_line=end),
                    kind="module",
                    content=snippet,
                    identifiers=extract_identifiers(snippet, profile="code"),
                )
            )

        return fragments


class MarkdownFragmenter(Fragmenter):
    priority = 90
    _HEADING_RE = re.compile(r"^(#{1,6})\s+([^\n]+)$", re.MULTILINE)  # NOSONAR(S5852)

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in (".md", ".markdown", ".mdx")

    def fragment(self, path: Path, content: str) -> list[Fragment]:
        lines = content.splitlines()
        if not lines:
            return []

        headings: list[tuple[int, int, str]] = []
        for i, line in enumerate(lines):
            match = self._HEADING_RE.match(line)
            if match:
                headings.append((i + 1, len(match.group(1)), match.group(2).strip()))

        if not headings:
            return ParagraphFragmenter().fragment(path, content)

        fragments: list[Fragment] = []

        for idx, (start_line, level, _title) in enumerate(headings):
            end_line = len(lines)
            for next_line, next_level, _ in headings[idx + 1 :]:
                if next_level <= level:
                    end_line = next_line - 1
                    break

            if end_line < start_line:
                continue

            snippet = "\n".join(lines[start_line - 1 : end_line])
            if not snippet.strip():
                continue
            if not snippet.endswith("\n"):
                snippet += "\n"

            fragments.append(
                Fragment(
                    id=FragmentId(path=path, start_line=start_line, end_line=end_line),
                    kind="section",
                    content=snippet,
                    identifiers=extract_identifiers(snippet, profile="docs"),
                )
            )

        return fragments if fragments else ParagraphFragmenter().fragment(path, content)


class ParagraphFragmenter(Fragmenter):
    priority = 20

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in (".txt", ".text", ".rst", ".adoc", "")

    def fragment(self, path: Path, content: str) -> list[Fragment]:
        lines = content.splitlines()
        if not lines:
            return []

        fragments: list[Fragment] = []
        para_start = 0
        in_para = False

        for i, line in enumerate(lines):
            is_blank = not line.strip()

            if not is_blank and not in_para:
                para_start = i
                in_para = True
            elif is_blank and in_para:
                if i > para_start:
                    fragments.extend(self._chunk_large_paragraph(path, lines, para_start, i - 1))
                in_para = False

        if in_para:
            fragments.extend(self._chunk_large_paragraph(path, lines, para_start, len(lines) - 1))

        return self._merge_small(fragments)

    def _make_fragment(self, path: Path, lines: list[str], start: int, end: int) -> Fragment | None:
        snippet = "\n".join(lines[start : end + 1])
        if not snippet.strip():
            return None

        word_count = len(snippet.split())
        if word_count < _MIN_FRAGMENT_WORDS:
            return None

        if not snippet.endswith("\n"):
            snippet += "\n"

        return Fragment(
            id=FragmentId(path=path, start_line=start + 1, end_line=end + 1),
            kind="paragraph",
            content=snippet,
            identifiers=extract_identifiers(snippet, profile="docs"),
        )

    def _chunk_large_paragraph(self, path: Path, lines: list[str], start: int, end: int) -> list[Fragment]:
        length = end - start + 1
        if length <= _GENERIC_MAX_LINES:
            frag = self._make_fragment(path, lines, start, end)
            return [frag] if frag else []

        fragments: list[Fragment] = []
        chunk_start = start
        while chunk_start <= end:
            chunk_end = min(end, chunk_start + _GENERIC_MAX_LINES - 1)
            frag = self._make_fragment(path, lines, chunk_start, chunk_end)
            if frag:
                fragments.append(frag)
            chunk_start = chunk_end + 1
        return fragments

    def _merge_small(self, fragments: list[Fragment], max_lines: int = 100) -> list[Fragment]:
        if len(fragments) <= 1:
            return fragments

        merged: list[Fragment] = []
        buffer: list[Fragment] = []
        buffer_lines = 0

        for frag in fragments:
            if buffer_lines + frag.line_count <= max_lines:
                buffer.append(frag)
                buffer_lines += frag.line_count
            else:
                if buffer:
                    merged.append(self._combine(buffer))
                buffer = [frag]
                buffer_lines = frag.line_count

        if buffer:
            merged.append(self._combine(buffer))

        return merged

    def _combine(self, frags: list[Fragment]) -> Fragment:
        if len(frags) == 1:
            return frags[0]

        combined = "\n".join(f.content.rstrip("\n") for f in frags) + "\n"
        combined_idents = frozenset().union(*(f.identifiers for f in frags))

        return Fragment(
            id=FragmentId(path=frags[0].path, start_line=frags[0].start_line, end_line=frags[-1].end_line),
            kind="section",
            content=combined,
            identifiers=combined_idents,
        )


class ConfigFragmenter(Fragmenter):
    priority = 50

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in (".yaml", ".yml", ".json", ".toml")

    def fragment(self, path: Path, content: str) -> list[Fragment]:
        lines = content.splitlines()
        if not lines:
            return []

        suffix = path.suffix.lower()

        if suffix in (".yaml", ".yml"):
            key_re = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_-]*):\s*")
        elif suffix == ".toml":
            key_re = re.compile(r"^\[([a-zA-Z_][a-zA-Z0-9_.-]*)\]")
        else:
            key_re = re.compile(r'^\s{0,2}"([^"]+)":\s*')

        boundaries: list[int] = []
        for i, line in enumerate(lines):
            if key_re.match(line):
                boundaries.append(i)

        if len(boundaries) < 2:
            return GenericFragmenter().fragment(path, content)

        fragments: list[Fragment] = []
        boundaries.append(len(lines))

        for idx in range(len(boundaries) - 1):
            start, end = boundaries[idx], boundaries[idx + 1] - 1

            snippet = "\n".join(lines[start : end + 1])
            if not snippet.strip():
                continue
            if not snippet.endswith("\n"):
                snippet += "\n"

            fragments.append(
                Fragment(
                    id=FragmentId(path=path, start_line=start + 1, end_line=end + 1),
                    kind="config",
                    content=snippet,
                    identifiers=extract_identifiers(snippet, profile="data"),
                )
            )

        return fragments if fragments else GenericFragmenter().fragment(path, content)


class GenericFragmenter(Fragmenter):
    priority = 0

    def can_handle(self, path: Path) -> bool:
        return True

    def fragment(self, path: Path, content: str) -> list[Fragment]:
        lines = content.splitlines()
        if not lines:
            return []

        fragments: list[Fragment] = []
        total = len(lines)
        start = 1

        while start <= total:
            end = min(total, start + _GENERIC_MAX_LINES - 1)

            snippet = "\n".join(lines[start - 1 : end])
            if not snippet.endswith("\n"):
                snippet += "\n"

            profile = TokenProfile.from_path(str(path))

            fragments.append(
                Fragment(
                    id=FragmentId(path=path, start_line=start, end_line=end),
                    kind="chunk",
                    content=snippet,
                    identifiers=extract_identifiers(snippet, profile=profile),
                )
            )
            start = end + 1

        return fragments


_FRAGMENTERS: list[Fragmenter] = sorted(
    [
        PythonFragmenter(),
        MarkdownFragmenter(),
        ParagraphFragmenter(),
        ConfigFragmenter(),
        GenericFragmenter(),
    ],
    key=lambda f: -f.priority,
)


def fragment_file(path: Path, content: str) -> list[Fragment]:
    for fragmenter in _FRAGMENTERS:
        if fragmenter.can_handle(path):
            result = fragmenter.fragment(path, content)
            if result:
                return result
    return GenericFragmenter().fragment(path, content)


def enclosing_fragment(fragments: list[Fragment], line_no: int) -> Fragment | None:
    candidates = [f for f in fragments if f.start_line <= line_no <= f.end_line]
    if not candidates:
        return None
    return min(candidates, key=lambda f: (f.line_count, f.start_line))
