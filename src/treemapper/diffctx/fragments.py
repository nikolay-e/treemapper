from __future__ import annotations

import ast
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from .stopwords import TokenProfile
from .types import Fragment, FragmentId, extract_identifiers

if TYPE_CHECKING:
    from tree_sitter import Node, Parser

_MIN_FRAGMENT_LINES = 2
_GENERIC_MAX_LINES = 200
_GENERIC_MAX_EXTENSION = 100
_MIN_FRAGMENT_WORDS = 10

_BRACKET_PAIRS = {"{": "}", "[": "]", "(": ")"}
_CLOSE_BRACKETS = set(_BRACKET_PAIRS.values())


def _compute_bracket_balance(text: str) -> int:
    stack: list[str] = []
    in_string = False
    string_char = ""
    escape_count = 0

    for char in text:
        if in_string:
            if char == "\\":
                escape_count += 1
            elif char == string_char and escape_count % 2 == 0:
                in_string = False
                escape_count = 0
            else:
                escape_count = 0
        else:
            if char in ('"', "'"):
                in_string = True
                string_char = char
                escape_count = 0
            elif char in _BRACKET_PAIRS:
                stack.append(_BRACKET_PAIRS[char])
            elif char in _CLOSE_BRACKETS:
                if stack and stack[-1] == char:
                    stack.pop()

    return len(stack)


def _find_balanced_end_line(
    lines: list[str], start_idx: int, target_end_idx: int, max_extension: int = _GENERIC_MAX_EXTENSION
) -> int:
    if target_end_idx >= len(lines):
        target_end_idx = len(lines) - 1

    text_to_target = "\n".join(lines[start_idx : target_end_idx + 1])
    if _compute_bracket_balance(text_to_target) == 0:
        return target_end_idx

    max_end = min(len(lines) - 1, target_end_idx + max_extension)

    for end_idx in range(target_end_idx + 1, max_end + 1):
        text = "\n".join(lines[start_idx : end_idx + 1])
        if _compute_bracket_balance(text) == 0:
            return end_idx

    for end_idx in range(target_end_idx - 1, start_idx - 1, -1):
        text = "\n".join(lines[start_idx : end_idx + 1])
        if _compute_bracket_balance(text) == 0:
            return end_idx

    return target_end_idx


_SENTENCE_ENDINGS = (".", "?", "!", '."', '?"', '!"', ".'", "?'", "!'")


def _find_sentence_boundary(lines: list[str], start_idx: int, target_end_idx: int) -> int:
    if target_end_idx >= len(lines):
        target_end_idx = len(lines) - 1

    for end_idx in range(target_end_idx, start_idx, -1):
        line = lines[end_idx].rstrip()
        if not line.endswith(_SENTENCE_ENDINGS):
            continue

        if end_idx + 1 >= len(lines):
            return end_idx

        next_line = lines[end_idx + 1].lstrip()
        if not next_line or next_line[0].isupper():
            return end_idx

    return target_end_idx


def _get_indent_level(line: str) -> int:
    stripped = line.lstrip()
    if not stripped:
        return -1
    return len(line) - len(stripped)


def _find_indent_safe_end_line(lines: list[str], start_idx: int, target_end_idx: int) -> int:
    if target_end_idx >= len(lines):
        target_end_idx = len(lines) - 1

    if target_end_idx + 1 >= len(lines):
        return target_end_idx

    next_indent = _get_indent_level(lines[target_end_idx + 1])
    if next_indent <= 0:
        return target_end_idx

    target_indent = _get_indent_level(lines[target_end_idx])
    if target_indent < 0:
        target_indent = 0

    if next_indent <= target_indent:
        return target_end_idx

    for end_idx in range(target_end_idx - 1, start_idx, -1):
        current_indent = _get_indent_level(lines[end_idx])
        if current_indent < 0:
            continue

        if end_idx + 1 < len(lines):
            following_indent = _get_indent_level(lines[end_idx + 1])
            if following_indent < 0 or following_indent <= current_indent:
                return end_idx

    return target_end_idx


_CODE_EXTENSIONS = {
    ".py",
    ".pyw",
    ".pyi",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".ts",
    ".tsx",
    ".mts",
    ".cts",
    ".vue",
    ".svelte",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".kts",
    ".scala",
    ".c",
    ".h",
    ".cpp",
    ".hpp",
    ".cc",
    ".cxx",
    ".cs",
    ".swift",
    ".rb",
    ".rake",
    ".php",
    ".lua",
    ".sh",
    ".bash",
    ".zsh",
    ".pl",
    ".pm",
    ".r",
    ".R",
    ".dart",
    ".zig",
    ".nim",
    ".v",
    ".ex",
    ".exs",
    ".hs",
    ".ml",
    ".mli",
}

_INDENT_EXTENSIONS = {".py", ".pyw", ".pyi", ".yaml", ".yml"}


def _is_code_file(path: Path) -> bool:
    return path.suffix.lower() in _CODE_EXTENSIONS


def _is_indent_based_file(path: Path) -> bool:
    return path.suffix.lower() in _INDENT_EXTENSIONS


def _find_smart_split_point(lines: list[str], start_idx: int, target_end_idx: int, path: Path) -> int:
    if target_end_idx >= len(lines):
        target_end_idx = len(lines) - 1

    if _is_indent_based_file(path):
        indent_end = _find_indent_safe_end_line(lines, start_idx, target_end_idx)
        if indent_end != target_end_idx:
            return indent_end

    if _is_code_file(path):
        balanced_end = _find_balanced_end_line(lines, start_idx, target_end_idx)
        return balanced_end

    return target_end_idx


@runtime_checkable
class FragmentationStrategy(Protocol):
    priority: int

    def can_handle(self, path: Path, content: str) -> bool: ...
    def fragment(self, path: Path, content: str) -> list[Fragment]: ...


_TREE_SITTER_LANGS: dict[str, str] = {
    ".py": "python",
    ".pyw": "python",
    ".pyi": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".mts": "typescript",
    ".cts": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".rb": "ruby",
    ".rake": "ruby",
}

_DEFINITION_NODE_TYPES = {
    "python": {"function_definition", "class_definition", "decorated_definition"},
    "javascript": {"function_declaration", "class_declaration", "method_definition", "arrow_function"},
    "typescript": {"function_declaration", "class_declaration", "method_definition", "arrow_function"},
    "go": {"function_declaration", "method_declaration", "type_declaration"},
    "rust": {"function_item", "impl_item", "struct_item", "enum_item", "trait_item"},
    "java": {"method_declaration", "class_declaration", "interface_declaration"},
    "c": {"function_definition", "struct_specifier"},
    "cpp": {"function_definition", "class_specifier", "struct_specifier"},
    "ruby": {"method", "class", "module"},
}


class TreeSitterStrategy:
    priority = 100

    def __init__(self) -> None:
        self._available = self._check_availability()
        self._parsers: dict[str, Parser] = {}

    def _check_availability(self) -> bool:
        try:
            from tree_sitter import Language, Parser  # noqa: F401

            return True
        except ImportError:
            return False

    def _get_parser(self, lang: str) -> Parser | None:
        if lang in self._parsers:
            return self._parsers[lang]

        try:
            from tree_sitter import Language, Parser

            if lang == "python":
                import tree_sitter_python as ts_lang
            elif lang == "javascript":
                import tree_sitter_javascript as ts_lang
            elif lang == "typescript":
                import tree_sitter_typescript as ts_lang

                ts_lang = ts_lang.language_tsx()
            elif lang == "go":
                import tree_sitter_go as ts_lang
            elif lang == "rust":
                import tree_sitter_rust as ts_lang
            elif lang == "java":
                import tree_sitter_java as ts_lang
            elif lang == "c":
                import tree_sitter_c as ts_lang
            elif lang == "cpp":
                import tree_sitter_cpp as ts_lang
            elif lang == "ruby":
                import tree_sitter_ruby as ts_lang
            else:
                return None

            parser = Parser()
            if hasattr(ts_lang, "language"):
                parser.language = Language(ts_lang.language())
            else:
                parser.language = Language(ts_lang)
            self._parsers[lang] = parser
            return parser
        except ImportError:
            logging.debug("tree-sitter-%s not available", lang)
            return None

    def can_handle(self, path: Path, content: str) -> bool:
        if not self._available:
            return False
        suffix = path.suffix.lower()
        if suffix not in _TREE_SITTER_LANGS:
            return False
        lang = _TREE_SITTER_LANGS[suffix]
        return self._get_parser(lang) is not None

    def fragment(self, path: Path, content: str) -> list[Fragment]:
        suffix = path.suffix.lower()
        lang = _TREE_SITTER_LANGS.get(suffix)
        if not lang:
            return []

        parser = self._get_parser(lang)
        if not parser:
            return []

        code_bytes = content.encode("utf-8")
        tree = parser.parse(code_bytes)
        lines = content.splitlines()

        fragments: list[Fragment] = []
        covered: set[tuple[int, int]] = set()

        definition_types = _DEFINITION_NODE_TYPES.get(lang, set())
        self._extract_definitions(tree.root_node, code_bytes, path, lines, definition_types, fragments, covered)

        gap_frags = self._create_gap_fragments(path, lines, list(covered))
        fragments.extend(gap_frags)

        return fragments if fragments else []

    def _extract_definitions(
        self,
        node: Node,
        code_bytes: bytes,
        path: Path,
        lines: list[str],
        definition_types: set[str],
        fragments: list[Fragment],
        covered: set[tuple[int, int]],
    ) -> None:
        if node.type in definition_types:
            start = node.start_point[0] + 1
            end = node.end_point[0] + 1

            if end - start + 1 >= _MIN_FRAGMENT_LINES:
                snippet = code_bytes[node.start_byte : node.end_byte].decode("utf-8", errors="replace")
                if not snippet.endswith("\n"):
                    snippet += "\n"

                kind = self._node_type_to_kind(node.type)
                fragments.append(
                    Fragment(
                        id=FragmentId(path=path, start_line=start, end_line=end),
                        kind=kind,
                        content=snippet,
                        identifiers=extract_identifiers(snippet, profile="code"),
                    )
                )
                covered.add((start, end))

        for child in node.children:
            self._extract_definitions(child, code_bytes, path, lines, definition_types, fragments, covered)

    def _node_type_to_kind(self, node_type: str) -> str:
        if "function" in node_type or "method" in node_type:
            return "function"
        if "class" in node_type:
            return "class"
        if "struct" in node_type:
            return "struct"
        if "impl" in node_type:
            return "impl"
        if "trait" in node_type or "interface" in node_type:
            return "interface"
        if "enum" in node_type:
            return "enum"
        if "module" in node_type:
            return "module"
        return "definition"

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


class PythonAstStrategy:
    priority = 95

    def can_handle(self, path: Path, content: str) -> bool:
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

        fragments.extend(self._create_gap_fragments(path, lines, covered))
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


class MistuneMarkdownStrategy:
    priority = 90

    def __init__(self) -> None:
        self._available = self._check_availability()

    def _check_availability(self) -> bool:
        try:
            import mistune  # noqa: F401

            return True
        except ImportError:
            return False

    def can_handle(self, path: Path, content: str) -> bool:
        if not self._available:
            return False
        return path.suffix.lower() in {".md", ".markdown", ".mdx"}

    def fragment(self, path: Path, content: str) -> list[Fragment]:
        import mistune

        lines = content.splitlines()
        if not lines:
            return []

        md = mistune.create_markdown(renderer=None)
        tokens = md(content)

        if not tokens:
            return []

        heading_lines = self._find_all_headings(lines)
        if not heading_lines:
            return []

        fragments: list[Fragment] = []
        heading_idx = 0

        for token in tokens:
            if not isinstance(token, dict):
                continue

            token_type = token.get("type")
            if token_type == "heading" and heading_idx < len(heading_lines):
                start_line, level = heading_lines[heading_idx]
                heading_idx += 1

                end_line = self._find_section_end(lines, start_line, level, heading_lines[heading_idx:])

                snippet = "\n".join(lines[start_line - 1 : end_line])
                if snippet.strip():
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

        return fragments if fragments else []

    def _find_all_headings(self, lines: list[str]) -> list[tuple[int, int]]:
        headings: list[tuple[int, int]] = []
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if stripped.startswith("#"):
                level = 0
                for ch in stripped:
                    if ch == "#":
                        level += 1
                    else:
                        break
                if level <= 6 and (len(stripped) == level or stripped[level] == " "):
                    headings.append((i + 1, level))
        return headings

    def _find_section_end(self, lines: list[str], start_line: int, level: int, remaining_headings: list[tuple[int, int]]) -> int:
        for next_line, next_level in remaining_headings:
            if next_level <= level:
                return next_line - 1
        return len(lines)


class RegexMarkdownStrategy:
    priority = 85
    _HEADING_RE = re.compile(r"^(#{1,6})\s+([^\n]+)$", re.MULTILINE)

    def can_handle(self, path: Path, content: str) -> bool:
        return path.suffix.lower() in {".md", ".markdown", ".mdx"}

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
            return []

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

        return fragments


class PySBDTextStrategy:
    priority = 25

    def __init__(self) -> None:
        self._available = self._check_availability()

    def _check_availability(self) -> bool:
        try:
            import pysbd  # noqa: F401

            return True
        except ImportError:
            return False

    def can_handle(self, path: Path, content: str) -> bool:
        if not self._available:
            return False
        return path.suffix.lower() in {".txt", ".text", ".rst", ".adoc", ""}

    def fragment(self, path: Path, content: str) -> list[Fragment]:
        import pysbd

        lines = content.splitlines()
        if not lines:
            return []

        seg = pysbd.Segmenter(language="en", clean=False)
        sentences = seg.segment(content)

        fragments: list[Fragment] = []
        current_line = 1
        para_sentences: list[str] = []
        para_start = 1

        for sentence in sentences:
            sentence_lines = sentence.count("\n")

            if "\n\n" in sentence:
                if para_sentences:
                    combined = " ".join(para_sentences)
                    if len(combined.split()) >= _MIN_FRAGMENT_WORDS:
                        end_line = current_line - 1
                        if end_line >= para_start:
                            snippet = "\n".join(lines[para_start - 1 : end_line])
                            if snippet.strip():
                                if not snippet.endswith("\n"):
                                    snippet += "\n"
                                fragments.append(
                                    Fragment(
                                        id=FragmentId(path=path, start_line=para_start, end_line=end_line),
                                        kind="paragraph",
                                        content=snippet,
                                        identifiers=extract_identifiers(snippet, profile="docs"),
                                    )
                                )
                    para_sentences = []
                para_start = current_line + sentence_lines
            else:
                para_sentences.append(sentence)

            current_line += sentence_lines

        if para_sentences:
            combined = " ".join(para_sentences)
            if len(combined.split()) >= _MIN_FRAGMENT_WORDS:
                end_line = len(lines)
                if end_line >= para_start:
                    snippet = "\n".join(lines[para_start - 1 : end_line])
                    if snippet.strip():
                        if not snippet.endswith("\n"):
                            snippet += "\n"
                        fragments.append(
                            Fragment(
                                id=FragmentId(path=path, start_line=para_start, end_line=end_line),
                                kind="paragraph",
                                content=snippet,
                                identifiers=extract_identifiers(snippet, profile="docs"),
                            )
                        )

        return self._merge_small(fragments)

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


class ParagraphStrategy:
    priority = 20

    def can_handle(self, path: Path, content: str) -> bool:
        return path.suffix.lower() in {".txt", ".text", ".rst", ".adoc", ""}

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
            logging.debug("Skipping empty fragment at %s:%d-%d", path, start + 1, end + 1)
            return None

        word_count = len(snippet.split())
        if word_count < _MIN_FRAGMENT_WORDS:
            logging.debug(
                "Skipping fragment at %s:%d-%d (only %d words, need %d)",
                path,
                start + 1,
                end + 1,
                word_count,
                _MIN_FRAGMENT_WORDS,
            )
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
            target_end = min(end, chunk_start + _GENERIC_MAX_LINES - 1)
            chunk_end = _find_sentence_boundary(lines, chunk_start, target_end)
            if chunk_end < chunk_start:
                chunk_end = target_end
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


class HTMLStrategy:
    priority = 55

    def __init__(self) -> None:
        self._available = self._check_availability()

    def _check_availability(self) -> bool:
        try:
            from lxml import html  # noqa: F401

            return True
        except ImportError:
            return False

    def can_handle(self, path: Path, content: str) -> bool:
        if not self._available:
            return False
        return path.suffix.lower() in {".html", ".htm", ".xhtml", ".xml"}

    def fragment(self, path: Path, content: str) -> list[Fragment]:
        from lxml import html

        lines = content.splitlines()
        if not lines:
            return []

        try:
            tree = html.fromstring(content)
        except Exception:
            return []

        fragments: list[Fragment] = []
        semantic_tags = {
            "section",
            "article",
            "main",
            "header",
            "footer",
            "nav",
            "aside",
            "div",
            "p",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
        }

        for elem in tree.iter():
            if elem.tag not in semantic_tags:
                continue

            source_line = getattr(elem, "sourceline", None)
            if source_line is None:
                continue

            elem_html = html.tostring(elem, encoding="unicode")
            elem_lines = elem_html.count("\n") + 1
            end_line = min(source_line + elem_lines - 1, len(lines))

            if end_line - source_line + 1 < _MIN_FRAGMENT_LINES:
                continue

            snippet = "\n".join(lines[source_line - 1 : end_line])
            if not snippet.strip():
                continue
            if not snippet.endswith("\n"):
                snippet += "\n"

            kind = "section" if elem.tag in {"section", "article", "main"} else "block"
            fragments.append(
                Fragment(
                    id=FragmentId(path=path, start_line=source_line, end_line=end_line),
                    kind=kind,
                    content=snippet,
                    identifiers=extract_identifiers(snippet, profile="docs"),
                )
            )

        return self._deduplicate_nested(fragments)

    def _deduplicate_nested(self, fragments: list[Fragment]) -> list[Fragment]:
        if len(fragments) <= 1:
            return fragments

        fragments.sort(key=lambda f: (f.start_line, -f.end_line))
        result: list[Fragment] = []

        for frag in fragments:
            if result and result[-1].start_line <= frag.start_line <= result[-1].end_line:
                continue
            result.append(frag)

        return result


class RuamelYamlStrategy:
    priority = 52

    def __init__(self) -> None:
        self._available = self._check_availability()

    def _check_availability(self) -> bool:
        try:
            from ruamel.yaml import YAML  # noqa: F401

            return True
        except ImportError:
            return False

    def can_handle(self, path: Path, content: str) -> bool:
        if not self._available:
            return False
        return path.suffix.lower() in {".yaml", ".yml"}

    def fragment(self, path: Path, content: str) -> list[Fragment]:
        from ruamel.yaml import YAML

        lines = content.splitlines()
        if not lines:
            return []

        yaml = YAML()
        yaml.preserve_quotes = True

        try:
            data = yaml.load(content)
        except Exception:
            return []

        if not hasattr(data, "lc") or not isinstance(data, dict):
            return []

        fragments: list[Fragment] = []
        keys = list(data.keys())

        for i, key in enumerate(keys):
            start_line = data.lc.key(key)[0] + 1  # type: ignore[attr-defined]

            if i + 1 < len(keys):
                end_line = data.lc.key(keys[i + 1])[0]  # type: ignore[attr-defined]
            else:
                end_line = len(lines)

            if end_line - start_line + 1 < _MIN_FRAGMENT_LINES:
                continue

            snippet = "\n".join(lines[start_line - 1 : end_line])
            if not snippet.strip():
                continue
            if not snippet.endswith("\n"):
                snippet += "\n"

            fragments.append(
                Fragment(
                    id=FragmentId(path=path, start_line=start_line, end_line=end_line),
                    kind="config",
                    content=snippet,
                    identifiers=extract_identifiers(snippet, profile="data"),
                )
            )

        return fragments


class ConfigStrategy:
    priority = 50

    def can_handle(self, path: Path, content: str) -> bool:
        return path.suffix.lower() in {".yaml", ".yml", ".json", ".toml"}

    def fragment(self, path: Path, content: str) -> list[Fragment]:
        lines = content.splitlines()
        if not lines:
            return []

        suffix = path.suffix.lower()

        if suffix in {".yaml", ".yml"}:
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
            return []

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

        return fragments


class GenericStrategy:
    priority = 0

    def can_handle(self, path: Path, content: str) -> bool:
        return True

    def fragment(self, path: Path, content: str) -> list[Fragment]:
        lines = content.splitlines()
        if not lines:
            return []

        fragments: list[Fragment] = []
        total = len(lines)
        start_idx = 0

        while start_idx < total:
            target_end_idx = min(total - 1, start_idx + _GENERIC_MAX_LINES - 1)
            end_idx = _find_smart_split_point(lines, start_idx, target_end_idx, path)

            snippet = "\n".join(lines[start_idx : end_idx + 1])
            if not snippet.endswith("\n"):
                snippet += "\n"

            profile = TokenProfile.from_path(str(path))

            fragments.append(
                Fragment(
                    id=FragmentId(path=path, start_line=start_idx + 1, end_line=end_idx + 1),
                    kind="chunk",
                    content=snippet,
                    identifiers=extract_identifiers(snippet, profile=profile),
                )
            )
            start_idx = end_idx + 1

        return fragments


class FragmentationEngine:
    def __init__(self) -> None:
        self._strategies: list[FragmentationStrategy] = []
        self._initialize_strategies()

    def _initialize_strategies(self) -> None:
        strategies: list[object] = [
            TreeSitterStrategy(),
            PythonAstStrategy(),
            MistuneMarkdownStrategy(),
            RegexMarkdownStrategy(),
            HTMLStrategy(),
            RuamelYamlStrategy(),
            ConfigStrategy(),
            PySBDTextStrategy(),
            ParagraphStrategy(),
            GenericStrategy(),
        ]

        for s in strategies:
            if isinstance(s, FragmentationStrategy):
                self._strategies.append(s)

        self._strategies.sort(key=lambda s: -s.priority)

    def fragment(self, path: Path, content: str) -> list[Fragment]:
        for strategy in self._strategies:
            if strategy.can_handle(path, content):
                try:
                    result = strategy.fragment(path, content)
                    if result:
                        return result
                except Exception as e:
                    logging.warning("Strategy %s failed for %s: %s", type(strategy).__name__, path, e)
                    continue

        return GenericStrategy().fragment(path, content)


_ENGINE = FragmentationEngine()


def fragment_file(path: Path, content: str) -> list[Fragment]:
    return _ENGINE.fragment(path, content)


def enclosing_fragment(fragments: list[Fragment], line_no: int) -> Fragment | None:
    candidates = [f for f in fragments if f.start_line <= line_no <= f.end_line]
    if not candidates:
        return None
    return min(candidates, key=lambda f: (f.line_count, f.start_line))
