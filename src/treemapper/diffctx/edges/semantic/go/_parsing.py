from __future__ import annotations

import re
from pathlib import Path

_GO_IMPORT_SINGLE_RE = re.compile(r'^\s*import\s+(?:[\w.]+\s+)?"([^"]+)"', re.MULTILINE)
_GO_IMPORT_BLOCK_RE = re.compile(r"import\s*\((.*?)\)", re.DOTALL)
_GO_IMPORT_LINE_RE = re.compile(r'^\s*(?:(?:\w+|\.)\s+)?"([^"]+)"', re.MULTILINE)

_GO_FUNC_RE = re.compile(r"^func\s+(?:\([^)]+\)\s+)?(\w+)\s*\(", re.MULTILINE)
_GO_TYPE_RE = re.compile(r"^type\s+(\w+)\s+", re.MULTILINE)

_GO_FUNC_CALL_RE = re.compile(r"\b([a-zA-Z_]\w*)\s*\(")
_GO_KEYWORDS = frozenset(
    {
        "if",
        "for",
        "range",
        "switch",
        "select",
        "return",
        "go",
        "defer",
        "func",
        "type",
        "var",
        "const",
        "map",
        "make",
        "new",
        "append",
        "len",
        "cap",
        "copy",
        "delete",
        "close",
        "panic",
        "recover",
        "print",
        "println",
    }
)
_GO_TYPE_REF_RE = re.compile(r"\*?([A-Z]\w*)\b")
_GO_COMMON_TYPES = frozenset(
    {
        "Bool",
        "String",
        "Error",
        "Reader",
        "Writer",
        "Handler",
        "Server",
        "Client",
        "Request",
        "Response",
        "Context",
        "Logger",
        "Config",
        "Options",
        "Result",
        "Status",
        "Mutex",
        "Group",
    }
)
_GO_PKG_CALL_RE = re.compile(r"\b(\w+)\.([A-Z]\w*)")
_GO_EMBED_RE = re.compile(r"//go:embed\s+(\S+)", re.MULTILINE)
_GO_PKG_DECL_RE = re.compile(r"^package\s+(\w+)", re.MULTILINE)
_GO_STRUCT_BODY_RE = re.compile(r"type\s+(\w+)\s+struct\s*\{([^}]*)\}", re.DOTALL)
_GO_EMBED_LINE_RE = re.compile(r"^\s*\*?([A-Z]\w*)\s*$", re.MULTILINE)
_GO_INIT_FUNC_RE = re.compile(r"^func\s+init\s*\(\s*\)", re.MULTILINE)


def _extract_imports(content: str) -> set[str]:
    imports: set[str] = set()

    for match in _GO_IMPORT_SINGLE_RE.finditer(content):
        imports.add(match.group(1))

    for block_match in _GO_IMPORT_BLOCK_RE.finditer(content):
        block = block_match.group(1)
        for line_match in _GO_IMPORT_LINE_RE.finditer(block):
            imports.add(line_match.group(1))

    return imports


def _extract_definitions(content: str) -> tuple[set[str], set[str]]:
    funcs = {m.group(1) for m in _GO_FUNC_RE.finditer(content)}
    types = {m.group(1) for m in _GO_TYPE_RE.finditer(content)}
    return funcs, types


def _extract_references(content: str) -> tuple[set[str], set[str], set[tuple[str, str]]]:
    func_calls = {m.group(1) for m in _GO_FUNC_CALL_RE.finditer(content) if m.group(1) not in _GO_KEYWORDS}
    type_refs = {
        m.group(1) for m in _GO_TYPE_REF_RE.finditer(content) if m.group(1)[0].isupper() and m.group(1) not in _GO_COMMON_TYPES
    }
    pkg_calls = {(m.group(1), m.group(2)) for m in _GO_PKG_CALL_RE.finditer(content)}
    return func_calls, type_refs, pkg_calls


def _extract_embedded_types(content: str) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for match in _GO_STRUCT_BODY_RE.finditer(content):
        struct_name = match.group(1)
        body = match.group(2)
        embeds = {m.group(1) for m in _GO_EMBED_LINE_RE.finditer(body)}
        if embeds:
            result[struct_name] = embeds
    return result


def _has_init_func(content: str) -> bool:
    return _GO_INIT_FUNC_RE.search(content) is not None


def _is_go_file(path: Path) -> bool:
    return path.suffix.lower() == ".go"


def _get_package_name_from_content(content: str, path: Path) -> str:
    match = _GO_PKG_DECL_RE.search(content)
    if match:
        return match.group(1)
    return path.parent.name


def _resolve_bases(pattern_str: str, parent: Path, repo_root: Path | None) -> list[Path]:
    base_pattern = pattern_str.split("*")[0].rstrip("/")
    candidate_bases = [parent / base_pattern]
    if repo_root:
        candidate_bases.append(repo_root / base_pattern)
    dirs: list[Path] = []
    for base in candidate_bases:
        try:
            dirs.append(base.resolve())
        except (OSError, ValueError):
            pass
    return dirs


def _any_dir_matches(dirs_to_check: set[Path], embed_dirs: list[Path]) -> bool:
    for d in dirs_to_check:
        try:
            resolved = d.resolve()
            if any(resolved == ed or resolved.is_relative_to(ed) for ed in embed_dirs):
                return True
        except (ValueError, OSError):
            continue
    return False
