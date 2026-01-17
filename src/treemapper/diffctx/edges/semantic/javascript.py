from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from ...javascript_semantics import JsFragmentInfo, analyze_javascript_fragment
from ...types import Fragment, FragmentId
from ..base import EdgeBuilder, EdgeDict, add_ref_edges

_JS_EXTS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".mts", ".cts"}

_JS_CALL_WEIGHT = 0.70
_JS_SYMBOL_REF_WEIGHT = 0.75
_JS_TYPE_REF_WEIGHT = 0.65

_JS_IMPORT_RE = re.compile(r"""(?:import\s+(?:.*?\s+from\s+)?['"]([^'"]+)['"]|require\s*\(\s*['"]([^'"]+)['"]\s*\))""")
_JS_EXPORT_FROM_RE = re.compile(r"""export\s+.*?\s+from\s+['"]([^'"]+)['"]""")


def _is_js_file(path: Path) -> bool:
    return path.suffix.lower() in _JS_EXTS


def _normalize_import(imp: str, source_path: Path) -> set[str]:
    names: set[str] = set()

    if imp.startswith("."):
        base_dir = source_path.parent
        parts = imp.split("/")
        resolved_parts: list[str] = []

        for part in parts:
            if part == ".":
                continue
            elif part == "..":
                base_dir = base_dir.parent
            else:
                resolved_parts.append(part)

        if resolved_parts:
            names.add("/".join(resolved_parts))
            names.add(resolved_parts[-1])
    else:
        names.add(imp)
        parts = imp.split("/")
        if len(parts) > 1:
            names.add(parts[-1])

    return names


def _extract_imports_from_content(content: str, source_path: Path) -> set[str]:
    imports: set[str] = set()

    for match in _JS_IMPORT_RE.finditer(content):
        imp = match.group(1) or match.group(2)
        if imp:
            imports.update(_normalize_import(imp, source_path))

    for match in _JS_EXPORT_FROM_RE.finditer(content):
        imp = match.group(1)
        if imp:
            imports.update(_normalize_import(imp, source_path))

    return imports


class JavaScriptEdgeBuilder(EdgeBuilder):
    weight = 0.70
    reverse_weight_factor = 0.5

    def discover_related_files(
        self,
        changed_files: list[Path],
        all_candidate_files: list[Path],
        repo_root: Path | None = None,
    ) -> list[Path]:
        js_changed = [f for f in changed_files if _is_js_file(f)]
        if not js_changed:
            return []

        changed_names: set[str] = set()
        for f in js_changed:
            stem = f.stem.lower()
            changed_names.add(stem)
            if stem == "index":
                changed_names.add(f.parent.name.lower())

            if repo_root:
                try:
                    rel = f.relative_to(repo_root)
                    rel_str = str(rel.with_suffix("")).replace("\\", "/")
                    changed_names.add(rel_str)
                    parts = rel_str.split("/")
                    for i in range(len(parts)):
                        changed_names.add("/".join(parts[i:]))
                except ValueError:
                    pass

        if not changed_names:
            return []

        discovered: list[Path] = []
        changed_set = set(changed_files)

        for candidate in all_candidate_files:
            if candidate in changed_set:
                continue
            if not _is_js_file(candidate):
                continue

            try:
                content = candidate.read_text(encoding="utf-8")
                imports = _extract_imports_from_content(content, candidate)

                for imp in imports:
                    imp_lower = imp.lower()
                    for name in changed_names:
                        if name in imp_lower or imp_lower.endswith(name):
                            discovered.append(candidate)
                            break
                    else:
                        continue
                    break
            except (OSError, UnicodeDecodeError):
                continue

        return discovered

    def build(self, fragments: list[Fragment], repo_root: Path | None = None) -> EdgeDict:
        js_frags = [f for f in fragments if f.path.suffix.lower() in _JS_EXTS]
        if not js_frags:
            return {}

        info_cache: dict[FragmentId, JsFragmentInfo] = {}
        for f in js_frags:
            info_cache[f.id] = analyze_javascript_fragment(f.content)

        name_to_defs: dict[str, list[FragmentId]] = defaultdict(list)
        frag_defines: dict[FragmentId, frozenset[str]] = {}

        for f in js_frags:
            info = info_cache[f.id]
            frag_defines[f.id] = info.defines
            for name in info.defines:
                name_to_defs[name].append(f.id)

        edges: EdgeDict = {}

        for f in js_frags:
            info = info_cache[f.id]
            self_defs = set(frag_defines.get(f.id, frozenset()))

            add_ref_edges(edges, f.id, set(info.calls), name_to_defs, _JS_CALL_WEIGHT)
            add_ref_edges(edges, f.id, set(info.references), name_to_defs, _JS_SYMBOL_REF_WEIGHT, skip_self_defs=self_defs)
            add_ref_edges(edges, f.id, set(info.type_refs), name_to_defs, _JS_TYPE_REF_WEIGHT, skip_self_defs=self_defs)

        return edges
