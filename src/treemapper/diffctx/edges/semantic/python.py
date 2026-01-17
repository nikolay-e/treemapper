from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from ...python_semantics import PyFragmentInfo, analyze_python_fragment
from ...types import Fragment, FragmentId
from ..base import EdgeBuilder, EdgeDict, add_ref_edges, path_to_module

_PYTHON_EXTS = {".py", ".pyi", ".pyw"}

_CALL_WEIGHT = 0.85
_SYMBOL_REF_WEIGHT = 0.95
_TYPE_REF_WEIGHT = 0.60

_PY_IMPORT_RE = re.compile(r"(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))")


def _is_python_file(path: Path) -> bool:
    return path.suffix.lower() in _PYTHON_EXTS


def _extract_imports_from_content(content: str) -> set[str]:
    imports: set[str] = set()
    for match in _PY_IMPORT_RE.finditer(content):
        imported = match.group(1) or match.group(2)
        if imported:
            imports.add(imported)
            parts = imported.split(".")
            for i in range(1, len(parts) + 1):
                imports.add(".".join(parts[:i]))
    return imports


class PythonEdgeBuilder(EdgeBuilder):
    weight = 0.70
    reverse_weight_factor = 0.5

    def discover_related_files(
        self,
        changed_files: list[Path],
        all_candidate_files: list[Path],
        repo_root: Path | None = None,
    ) -> list[Path]:
        py_changed = [f for f in changed_files if _is_python_file(f)]
        if not py_changed:
            return []

        changed_modules: set[str] = set()
        for f in py_changed:
            module = path_to_module(f, repo_root)
            if module:
                changed_modules.add(module)
                parts = module.split(".")
                for i in range(1, len(parts) + 1):
                    changed_modules.add(".".join(parts[:i]))

        if not changed_modules:
            return []

        discovered: list[Path] = []
        changed_set = set(changed_files)

        for candidate in all_candidate_files:
            if candidate in changed_set:
                continue
            if not _is_python_file(candidate):
                continue

            try:
                content = candidate.read_text(encoding="utf-8")
                imports = _extract_imports_from_content(content)

                for imp in imports:
                    if imp in changed_modules:
                        discovered.append(candidate)
                        break
            except (OSError, UnicodeDecodeError):
                continue

        return discovered

    def build(self, fragments: list[Fragment], repo_root: Path | None = None) -> EdgeDict:
        py_frags = [f for f in fragments if f.path.suffix.lower() == ".py"]
        if not py_frags:
            return {}

        info_cache: dict[FragmentId, PyFragmentInfo] = {}
        for f in py_frags:
            info_cache[f.id] = analyze_python_fragment(f.content)

        name_to_defs: dict[str, list[FragmentId]] = defaultdict(list)
        frag_defines: dict[FragmentId, frozenset[str]] = {}

        for f in py_frags:
            info = info_cache[f.id]
            frag_defines[f.id] = info.defines
            for name in info.defines:
                name_to_defs[name].append(f.id)

        edges: EdgeDict = {}

        for f in py_frags:
            info = info_cache[f.id]
            self_defs = set(frag_defines.get(f.id, frozenset()))

            add_ref_edges(edges, f.id, set(info.calls), name_to_defs, _CALL_WEIGHT)
            add_ref_edges(edges, f.id, set(info.references), name_to_defs, _SYMBOL_REF_WEIGHT, skip_self_defs=self_defs)
            add_ref_edges(edges, f.id, set(info.type_refs), name_to_defs, _TYPE_REF_WEIGHT, skip_self_defs=self_defs)

        return edges
