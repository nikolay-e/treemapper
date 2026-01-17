from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from ...types import Fragment, FragmentId
from ..base import EdgeBuilder, EdgeDict

_C_EXTENSIONS = {".c", ".h"}
_CPP_EXTENSIONS = {".cpp", ".hpp", ".cc", ".cxx", ".hxx", ".c++", ".h++", ".hh", ".ipp", ".tpp"}
_OBJC_EXTENSIONS = {".m", ".mm"}
_ALL_C_FAMILY = _C_EXTENSIONS | _CPP_EXTENSIONS | _OBJC_EXTENSIONS

_INCLUDE_RE = re.compile(r'^\s*#\s*(?:include|import)\s*[<"]([^>"]+)[>"]', re.MULTILINE)

_FUNC_DEF_RE = re.compile(
    r"^\s*(?:static\s+|inline\s+|virtual\s+|explicit\s+|constexpr\s+)*"
    r"(?:[\w:]+\s+)+"
    r"(\w+)\s*\([^)]*\)\s*(?:const\s*)?(?:override\s*)?(?:final\s*)?"
    r"(?:noexcept(?:\([^)]*\))?\s*)?"
    r"\s*\{",
    re.MULTILINE,
)

_CLASS_RE = re.compile(r"^\s*(?:template\s*<[^>]*>\s*)?(?:class|struct)\s+(\w+)", re.MULTILINE)
_TYPEDEF_RE = re.compile(r"^\s*typedef\s+.*?\s+(\w+)\s*;", re.MULTILINE)
_USING_TYPE_RE = re.compile(r"^\s*using\s+(\w+)\s*=", re.MULTILINE)
_ENUM_RE = re.compile(r"^\s*enum\s+(?:class\s+)?(\w+)", re.MULTILINE)
_NAMESPACE_RE = re.compile(r"^\s*namespace\s+(\w+)", re.MULTILINE)

_FUNC_CALL_RE = re.compile(r"\b(\w+)\s*\(")
_TYPE_REF_RE = re.compile(r"\b([A-Z][A-Za-z0-9_]*)\b")

_METHOD_IMPL_RE = re.compile(r"^\s*(?:[\w:]+\s+)?(\w+)::(\w+)\s*\(", re.MULTILINE)


def _is_c_family(path: Path) -> bool:
    return path.suffix.lower() in _ALL_C_FAMILY


def _extract_includes(content: str) -> set[str]:
    includes: set[str] = set()
    for match in _INCLUDE_RE.finditer(content):
        header = match.group(1)
        includes.add(header)
        if "/" in header:
            includes.add(header.split("/")[-1])
    return includes


def _extract_definitions(content: str) -> tuple[set[str], set[str], set[str]]:
    functions: set[str] = set()
    types: set[str] = set()
    namespaces: set[str] = set()

    for match in _FUNC_DEF_RE.finditer(content):
        functions.add(match.group(1))

    for pattern in [_CLASS_RE, _TYPEDEF_RE, _USING_TYPE_RE, _ENUM_RE]:
        for match in pattern.finditer(content):
            types.add(match.group(1))

    for match in _NAMESPACE_RE.finditer(content):
        namespaces.add(match.group(1))

    for match in _METHOD_IMPL_RE.finditer(content):
        class_name, method_name = match.groups()
        types.add(class_name)
        functions.add(method_name)

    return functions, types, namespaces


def _extract_references(content: str, own_defs: set[str]) -> tuple[set[str], set[str]]:
    calls: set[str] = set()
    type_refs: set[str] = set()

    for match in _FUNC_CALL_RE.finditer(content):
        name = match.group(1)
        if name not in own_defs and not name.startswith("_") and len(name) > 2:
            calls.add(name)

    for match in _TYPE_REF_RE.finditer(content):
        name = match.group(1)
        if name not in own_defs and len(name) > 2:
            type_refs.add(name)

    return calls, type_refs


class CFamilyEdgeBuilder(EdgeBuilder):
    weight = 0.70
    include_weight = 0.65
    call_weight = 0.55
    type_weight = 0.50
    reverse_weight_factor = 0.40

    def build(self, fragments: list[Fragment], repo_root: Path | None = None) -> EdgeDict:
        c_frags = [f for f in fragments if _is_c_family(f.path)]
        if not c_frags:
            return {}

        edges: EdgeDict = {}

        header_to_frags: dict[str, list[FragmentId]] = defaultdict(list)
        func_defs: dict[str, list[FragmentId]] = defaultdict(list)
        type_defs: dict[str, list[FragmentId]] = defaultdict(list)
        frag_own_defs: dict[FragmentId, set[str]] = {}

        for f in c_frags:
            header_to_frags[f.path.name].append(f.id)
            if f.path.stem:
                header_to_frags[f.path.stem + ".h"].append(f.id)
                header_to_frags[f.path.stem + ".hpp"].append(f.id)

            functions, types, _namespaces = _extract_definitions(f.content)
            frag_own_defs[f.id] = functions | types

            for func in functions:
                func_defs[func].append(f.id)

            for t in types:
                type_defs[t].append(f.id)

        for f in c_frags:
            includes = _extract_includes(f.content)
            for inc in includes:
                inc_name = inc.split("/")[-1] if "/" in inc else inc
                for target_id in header_to_frags.get(inc_name, []):
                    if target_id != f.id:
                        self.add_edge(edges, f.id, target_id, self.include_weight)

            own_defs = frag_own_defs.get(f.id, set())
            calls, type_refs = _extract_references(f.content, own_defs)

            for call in calls:
                for def_id in func_defs.get(call, []):
                    if def_id != f.id:
                        self.add_edge(edges, f.id, def_id, self.call_weight)

            for t in type_refs:
                for def_id in type_defs.get(t, []):
                    if def_id != f.id:
                        self.add_edge(edges, f.id, def_id, self.type_weight)

        self._link_header_impl_pairs(c_frags, edges)

        return edges

    def _link_header_impl_pairs(self, frags: list[Fragment], edges: EdgeDict) -> None:
        by_stem: dict[str, list[Fragment]] = defaultdict(list)
        for f in frags:
            by_stem[f.path.stem.lower()].append(f)

        for _stem, group in by_stem.items():
            if len(group) < 2:
                continue

            headers = [f for f in group if f.path.suffix.lower() in {".h", ".hpp", ".hh", ".hxx"}]
            impls = [f for f in group if f.path.suffix.lower() in {".c", ".cpp", ".cc", ".cxx", ".m", ".mm"}]

            for h in headers:
                for impl in impls:
                    self.add_edge(edges, h.id, impl.id, self.weight)
