from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from ...types import Fragment, FragmentId
from ..base import EdgeBuilder, EdgeDict

_PHP_EXTS = {".php", ".phtml", ".php3", ".php4", ".php5", ".php7", ".phps"}

_PHP_USE_RE = re.compile(r"^\s*use\s+([A-Z][a-zA-Z0-9_\\]*(?:\s+as\s+\w+)?)\s*;", re.MULTILINE)
_PHP_NAMESPACE_RE = re.compile(r"^\s*namespace\s+([A-Z][a-zA-Z0-9_\\]*)\s*;", re.MULTILINE)
_PHP_REQUIRE_RE = re.compile(r"^\s*(?:require|require_once|include|include_once)\s*\(?['\"]([^'\"]+)['\"]", re.MULTILINE)

_PHP_CLASS_RE = re.compile(r"^\s*(?:abstract\s+)?(?:final\s+)?class\s+([A-Z]\w*)", re.MULTILINE)
_PHP_INTERFACE_RE = re.compile(r"^\s*interface\s+([A-Z]\w*)", re.MULTILINE)
_PHP_TRAIT_RE = re.compile(r"^\s*trait\s+([A-Z]\w*)", re.MULTILINE)
_PHP_ENUM_RE = re.compile(r"^\s*enum\s+([A-Z]\w*)", re.MULTILINE)
_PHP_FUNCTION_RE = re.compile(r"^\s*(?:public|private|protected)?\s*(?:static\s+)?function\s+([a-z_]\w*)", re.MULTILINE)

_PHP_EXTENDS_RE = re.compile(r"class\s+\w+\s+extends\s+([A-Z]\w*)")
_PHP_IMPLEMENTS_RE = re.compile(r"implements\s+([A-Z]\w*(?:\s*,\s*[A-Z]\w*)*)")
_PHP_USE_TRAIT_RE = re.compile(r"^\s*use\s+([A-Z]\w*(?:\s*,\s*[A-Z]\w*)*)\s*;", re.MULTILINE)

_PHP_TYPE_HINT_RE = re.compile(r"(?::|->)\s*([A-Z]\w*)\b")
_PHP_NEW_RE = re.compile(r"new\s+([A-Z]\w*)")
_PHP_STATIC_CALL_RE = re.compile(r"([A-Z]\w*)::(?!\$)")
_PHP_INSTANCEOF_RE = re.compile(r"instanceof\s+([A-Z]\w*)")


def _is_php_file(path: Path) -> bool:
    return path.suffix.lower() in _PHP_EXTS


def _extract_uses(content: str) -> set[str]:
    uses: set[str] = set()
    for m in _PHP_USE_RE.finditer(content):
        use = m.group(1).split(" as ")[0].strip()
        if "\\" in use:
            parts = use.split("\\")
            uses.add(parts[-1])
            uses.add(use)
        else:
            uses.add(use)
    return uses


def _extract_namespace(content: str) -> str | None:
    match = _PHP_NAMESPACE_RE.search(content)
    return match.group(1) if match else None


def _extract_requires(content: str) -> set[str]:
    return {m.group(1) for m in _PHP_REQUIRE_RE.finditer(content)}


def _extract_definitions(content: str) -> tuple[set[str], set[str], set[str], set[str]]:
    classes = {m.group(1) for m in _PHP_CLASS_RE.finditer(content)}
    interfaces = {m.group(1) for m in _PHP_INTERFACE_RE.finditer(content)}
    traits = {m.group(1) for m in _PHP_TRAIT_RE.finditer(content)}
    enums = {m.group(1) for m in _PHP_ENUM_RE.finditer(content)}
    return classes, interfaces, traits, enums


def _extract_inheritance(content: str) -> set[str]:
    refs: set[str] = set()
    for m in _PHP_EXTENDS_RE.finditer(content):
        refs.add(m.group(1))
    for m in _PHP_IMPLEMENTS_RE.finditer(content):
        for cls in m.group(1).split(","):
            refs.add(cls.strip())
    for m in _PHP_USE_TRAIT_RE.finditer(content):
        for trait in m.group(1).split(","):
            refs.add(trait.strip())
    return refs


def _extract_type_refs(content: str) -> set[str]:
    refs: set[str] = set()
    refs.update(m.group(1) for m in _PHP_TYPE_HINT_RE.finditer(content))
    refs.update(m.group(1) for m in _PHP_NEW_RE.finditer(content))
    refs.update(m.group(1) for m in _PHP_STATIC_CALL_RE.finditer(content))
    refs.update(m.group(1) for m in _PHP_INSTANCEOF_RE.finditer(content))
    return refs


class PHPEdgeBuilder(EdgeBuilder):
    weight = 0.70
    use_weight = 0.75
    require_weight = 0.70
    inheritance_weight = 0.80
    type_weight = 0.60
    same_namespace_weight = 0.55
    reverse_weight_factor = 0.4

    def build(self, fragments: list[Fragment], repo_root: Path | None = None) -> EdgeDict:
        php_frags = [f for f in fragments if _is_php_file(f.path)]
        if not php_frags:
            return {}

        edges: EdgeDict = {}

        name_to_frags: dict[str, list[FragmentId]] = defaultdict(list)
        path_to_frags: dict[str, list[FragmentId]] = defaultdict(list)
        namespace_to_frags: dict[str, list[FragmentId]] = defaultdict(list)
        class_to_frags: dict[str, list[FragmentId]] = defaultdict(list)
        fqn_to_frags: dict[str, list[FragmentId]] = defaultdict(list)

        for f in php_frags:
            stem = f.path.stem.lower()
            name_to_frags[stem].append(f.id)

            if repo_root:
                try:
                    rel = f.path.relative_to(repo_root)
                    path_to_frags[str(rel)].append(f.id)
                    path_to_frags[rel.as_posix()].append(f.id)
                except ValueError:
                    pass

            ns = _extract_namespace(f.content)
            if ns:
                namespace_to_frags[ns.lower()].append(f.id)
                ns_parts = ns.split("\\")
                for i in range(len(ns_parts)):
                    partial_ns = "\\".join(ns_parts[: i + 1])
                    namespace_to_frags[partial_ns.lower()].append(f.id)

            classes, interfaces, traits, enums = _extract_definitions(f.content)
            all_types = classes | interfaces | traits | enums
            for t in all_types:
                class_to_frags[t.lower()].append(f.id)
                if ns:
                    fqn = f"{ns}\\{t}"
                    fqn_to_frags[fqn.lower()].append(f.id)

        for pf in php_frags:
            uses = _extract_uses(pf.content)
            requires = _extract_requires(pf.content)
            inheritance = _extract_inheritance(pf.content)
            type_refs = _extract_type_refs(pf.content)
            current_ns = _extract_namespace(pf.content)

            for use in uses:
                use_lower = use.lower().replace("\\", "\\\\")
                if use_lower in fqn_to_frags:
                    for fid in fqn_to_frags[use_lower]:
                        if fid != pf.id:
                            self.add_edge(edges, pf.id, fid, self.use_weight)

                class_name = use.split("\\")[-1].lower()
                if class_name in class_to_frags:
                    for fid in class_to_frags[class_name]:
                        if fid != pf.id:
                            self.add_edge(edges, pf.id, fid, self.use_weight)

            for req in requires:
                req_name = req.split("/")[-1].replace(".php", "").lower()
                if req_name in name_to_frags:
                    for fid in name_to_frags[req_name]:
                        if fid != pf.id:
                            self.add_edge(edges, pf.id, fid, self.require_weight)

                for path_str, frag_ids in path_to_frags.items():
                    if req in path_str:
                        for fid in frag_ids:
                            if fid != pf.id:
                                self.add_edge(edges, pf.id, fid, self.require_weight)

            for parent in inheritance:
                parent_lower = parent.lower()
                if parent_lower in class_to_frags:
                    for fid in class_to_frags[parent_lower]:
                        if fid != pf.id:
                            self.add_edge(edges, pf.id, fid, self.inheritance_weight)

            for type_ref in type_refs:
                ref_lower = type_ref.lower()
                if ref_lower in class_to_frags:
                    for fid in class_to_frags[ref_lower]:
                        if fid != pf.id:
                            self.add_edge(edges, pf.id, fid, self.type_weight)

            if current_ns and current_ns.lower() in namespace_to_frags:
                for fid in namespace_to_frags[current_ns.lower()]:
                    if fid != pf.id:
                        self.add_edge(edges, pf.id, fid, self.same_namespace_weight)

        return edges
