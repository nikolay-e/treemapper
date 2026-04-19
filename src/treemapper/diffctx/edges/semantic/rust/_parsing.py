from __future__ import annotations

import re
from pathlib import Path

_RUST_USE_STMT_RE = re.compile(r"^\s*use\s+(.+?)\s*;", re.DOTALL | re.MULTILINE)
_RUST_MOD_RE = re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?mod\s+([a-z_][a-z0-9_]*)\s*[;{]", re.MULTILINE)

_RUST_FN_RE = re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?fn\s+([a-z_][a-z0-9_]*)", re.MULTILINE)
_RUST_STRUCT_RE = re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?struct\s+([A-Z]\w*)", re.MULTILINE)
_RUST_ENUM_RE = re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?enum\s+([A-Z]\w*)", re.MULTILINE)
_RUST_TRAIT_RE = re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?trait\s+([A-Z]\w*)", re.MULTILINE)
_RUST_IMPL_RE = re.compile(r"^\s*impl(?:<[^>\n]*>)?\s+(?:\w+\s+for\s+)?([A-Z]\w*)", re.MULTILINE)
_RUST_TRAIT_IMPL_RE = re.compile(r"^\s*impl(?:<[^>\n]*>)?\s+(\w+)\s+for\s+(\w+)", re.MULTILINE)
_RUST_PUB_USE_RE = re.compile(r"^\s*pub\s+use\s+(?:crate::)?([a-z_]\w*(?:::\w+)*)", re.MULTILINE)
_RUST_TYPE_ALIAS_RE = re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?type\s+([A-Z]\w*)", re.MULTILINE)

_RUST_TYPE_REF_RE = re.compile(r"(?<![a-z_])([A-Z]\w*)\b")
_RUST_FN_CALL_RE = re.compile(r"(?<!\w)([a-z_][a-z0-9_]*)\s?!?\s?\(")
_RUST_PATH_CALL_RE = re.compile(r"([a-z_][a-z0-9_]*)::([a-z_][a-z0-9_]*|[A-Z]\w*)")

_RUST_COMMON_TYPES = frozenset(
    {
        "String",
        "Vec",
        "Option",
        "Result",
        "Box",
        "Arc",
        "Rc",
        "Some",
        "None",
        "Ok",
        "Err",
        "Self",
        "HashMap",
        "HashSet",
        "BTreeMap",
        "BTreeSet",
        "Cow",
        "Pin",
        "PhantomData",
    }
)

_RUST_BUILTIN_MACROS = frozenset(
    {
        "println",
        "print",
        "eprintln",
        "eprint",
        "format",
        "vec",
        "assert",
        "assert_eq",
        "assert_ne",
        "debug_assert",
        "debug_assert_eq",
        "debug_assert_ne",
        "panic",
        "todo",
        "unimplemented",
        "unreachable",
        "cfg",
        "env",
        "file",
        "line",
        "column",
        "stringify",
        "concat",
        "include",
        "include_str",
        "include_bytes",
        "write",
        "writeln",
    }
)

_RUST_KEYWORDS = frozenset(
    {
        "if",
        "for",
        "while",
        "match",
        "return",
        "unsafe",
        "loop",
        "break",
        "continue",
        "else",
        "where",
        "as",
        "in",
        "ref",
        "mut",
        "pub",
        "fn",
        "let",
        "const",
        "static",
        "move",
        "async",
        "await",
        "dyn",
        "impl",
        "trait",
        "struct",
        "enum",
        "type",
        "use",
        "mod",
        "crate",
        "self",
        "super",
    }
)


def is_rust_file(path: Path) -> bool:
    return path.suffix.lower() == ".rs"


_MAX_USE_TREE_DEPTH = 10


def _find_matching_brace(inner: str) -> int:
    depth = 1
    for i, ch in enumerate(inner):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
    return 0


def _split_brace_items(items_str: str) -> tuple[list[str], bool]:
    items: list[str] = []
    current: list[str] = []
    depth = 0
    has_self = False
    for ch in items_str:
        if ch == "{":
            depth += 1
            current.append(ch)
        elif ch == "}":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            item = "".join(current).strip()
            if item == "self":
                has_self = True
            elif item:
                items.append(item)
            current = []
        else:
            current.append(ch)
    item = "".join(current).strip()
    if item == "self":
        has_self = True
    elif item:
        items.append(item)
    return items, has_self


def _parse_use_tree(text: str, _depth: int = 0) -> list[str]:
    if _depth > _MAX_USE_TREE_DEPTH:
        return []
    text = re.sub(r"^(?:crate|self|super)::", "", text.strip())
    if "{" not in text:
        return [text] if text else []
    brace_pos = text.index("{")
    prefix = text[:brace_pos].rstrip(":")
    inner = text[brace_pos + 1 :]
    end = _find_matching_brace(inner)
    items, has_self = _split_brace_items(inner[:end])
    results: list[str] = []
    if has_self and prefix:
        results.append(prefix)
    for item in items:
        results.extend(_parse_use_tree(f"{prefix}::{item}" if prefix else item, _depth + 1))
    return results


def extract_uses(content: str) -> set[str]:
    uses: set[str] = set()
    for match in _RUST_USE_STMT_RE.finditer(content):
        for path in _parse_use_tree(match.group(1)):
            uses.add(path)
            parts = path.split("::")
            if len(parts) > 1:
                uses.add(parts[0])
    return uses


def extract_mods(content: str) -> set[str]:
    return {m.group(1) for m in _RUST_MOD_RE.finditer(content)}


def extract_trait_impls(content: str) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(2)) for m in _RUST_TRAIT_IMPL_RE.finditer(content)]


def extract_pub_uses(content: str) -> list[str]:
    return [m.group(1) for m in _RUST_PUB_USE_RE.finditer(content)]


def extract_definitions(content: str) -> tuple[set[str], set[str]]:
    funcs = {m.group(1) for m in _RUST_FN_RE.finditer(content)}
    types: set[str] = set()
    types.update(m.group(1) for m in _RUST_STRUCT_RE.finditer(content))
    types.update(m.group(1) for m in _RUST_ENUM_RE.finditer(content))
    types.update(m.group(1) for m in _RUST_TRAIT_RE.finditer(content))
    types.update(m.group(1) for m in _RUST_TYPE_ALIAS_RE.finditer(content))

    for m in _RUST_IMPL_RE.finditer(content):
        if m.group(1):
            types.add(m.group(1))

    return funcs, types


def extract_references(content: str) -> tuple[set[str], set[str], set[tuple[str, str]]]:
    type_refs = {m.group(1) for m in _RUST_TYPE_REF_RE.finditer(content) if m.group(1) not in _RUST_COMMON_TYPES}
    fn_calls = {
        m.group(1)
        for m in _RUST_FN_CALL_RE.finditer(content)
        if m.group(1) not in _RUST_KEYWORDS and m.group(1) not in _RUST_BUILTIN_MACROS
    }
    path_calls = {(m.group(1), m.group(2)) for m in _RUST_PATH_CALL_RE.finditer(content)}
    return type_refs, fn_calls, path_calls


DISCOVERY_MAX_DEPTH = 2


def stem_to_mod_name(path: Path) -> str:
    stem = path.stem.lower()
    if stem in {"mod", "lib"}:
        return path.parent.name.lower()
    return stem


def read_cached(path: Path, cache: dict[Path, str] | None) -> str | None:
    if cache is not None and path in cache:
        return cache[path]
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    if cache is not None:
        cache[path] = content
    return content
