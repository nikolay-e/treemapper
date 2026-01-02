from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .types import Fragment

_FUNC_NAME_RE = re.compile(r"^\s*(?:async\s+)?def\s+(\w+)\s*\(", re.MULTILINE)
_CLASS_NAME_RE = re.compile(r"^\s*class\s+(\w+)\s*[:\(]", re.MULTILINE)
_MD_HEADING_RE = re.compile(r"^#{1,6}\s+([^\n]+)$", re.MULTILINE)  # NOSONAR(S5852)


def _preview(content: str, max_chars: int = 150) -> str:
    text = " ".join(content.split())
    return text[:max_chars] + "..." if len(text) > max_chars else text


def _extract_symbol(frag: Fragment) -> str | None:
    if frag.kind == "function":
        match = _FUNC_NAME_RE.search(frag.content)
        if match:
            return match.group(1)
    elif frag.kind == "class":
        match = _CLASS_NAME_RE.search(frag.content)
        if match:
            return match.group(1)
    elif frag.kind == "section":
        match = _MD_HEADING_RE.search(frag.content)
        if match:
            return match.group(1).strip()[:50]
    return None


def build_partial_tree(repo_root: Path, selected: list[Fragment]) -> dict[str, Any]:
    fragments_out: list[dict[str, Any]] = []

    by_path: dict[Path, list[Fragment]] = {}
    for frag in selected:
        if frag.path.is_absolute():
            try:
                rel_path = frag.path.relative_to(repo_root)
            except ValueError:
                rel_path = frag.path
        else:
            rel_path = frag.path

        if rel_path not in by_path:
            by_path[rel_path] = []
        by_path[rel_path].append(frag)

    for rel_path in sorted(by_path.keys()):
        frags = sorted(by_path[rel_path], key=lambda f: f.start_line)
        path_str = rel_path.as_posix()

        for frag in frags:
            entry: dict[str, Any] = {
                "path": path_str,
                "lines": f"{frag.start_line}-{frag.end_line}",
                "kind": frag.kind,
            }
            symbol = _extract_symbol(frag)
            if symbol:
                entry["symbol"] = symbol
            if frag.content:
                entry["content"] = frag.content
                entry["preview"] = _preview(frag.content)
            fragments_out.append(entry)

    resolved_root = repo_root.resolve()
    return {
        "name": resolved_root.name,
        "type": "diff_context",
        "fragment_count": len(fragments_out),
        "fragments": fragments_out,
    }
