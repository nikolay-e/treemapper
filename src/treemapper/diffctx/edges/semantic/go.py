from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from ...types import Fragment, FragmentId
from ..base import EdgeBuilder, EdgeDict

_GO_IMPORT_SINGLE_RE = re.compile(r'^\s*import\s+"([^"]+)"', re.MULTILINE)
_GO_IMPORT_BLOCK_RE = re.compile(r"import\s*\((.*?)\)", re.DOTALL)
_GO_IMPORT_LINE_RE = re.compile(r'^\s*(?:\w+\s+)?"([^"]+)"', re.MULTILINE)

_GO_FUNC_RE = re.compile(r"^func\s+(?:\([^)]+\)\s+)?(\w+)\s*\(", re.MULTILINE)
_GO_TYPE_RE = re.compile(r"^type\s+(\w+)\s+(?:struct|interface|func)", re.MULTILINE)
_GO_CONST_VAR_RE = re.compile(r"^(?:const|var)\s+(\w+)\s+", re.MULTILINE)

_GO_FUNC_CALL_RE = re.compile(r"\b([A-Z]\w+)\s*\(")
_GO_TYPE_REF_RE = re.compile(r"\*?([A-Z][a-zA-Z0-9]*)\b")
_GO_PKG_CALL_RE = re.compile(r"\b(\w+)\.([A-Z]\w*)")


def _extract_imports(content: str) -> set[str]:
    imports: set[str] = set()

    for match in _GO_IMPORT_SINGLE_RE.finditer(content):
        imports.add(match.group(1))

    for block_match in _GO_IMPORT_BLOCK_RE.finditer(content):
        block = block_match.group(1)
        for line_match in _GO_IMPORT_LINE_RE.finditer(block):
            imports.add(line_match.group(1))

    return imports


def _extract_definitions(content: str) -> tuple[set[str], set[str], set[str]]:
    funcs = {m.group(1) for m in _GO_FUNC_RE.finditer(content)}
    types = {m.group(1) for m in _GO_TYPE_RE.finditer(content)}
    consts_vars = {m.group(1) for m in _GO_CONST_VAR_RE.finditer(content)}
    return funcs, types, consts_vars


def _extract_references(content: str) -> tuple[set[str], set[str], set[tuple[str, str]]]:
    func_calls = {m.group(1) for m in _GO_FUNC_CALL_RE.finditer(content) if m.group(1)[0].isupper()}
    type_refs = {m.group(1) for m in _GO_TYPE_REF_RE.finditer(content) if m.group(1)[0].isupper()}
    pkg_calls = {(m.group(1), m.group(2)) for m in _GO_PKG_CALL_RE.finditer(content)}
    return func_calls, type_refs, pkg_calls


def _is_go_file(path: Path) -> bool:
    return path.suffix.lower() == ".go"


def _get_package_name(path: Path) -> str:
    return path.parent.name


class GoEdgeBuilder(EdgeBuilder):
    weight = 0.75
    import_weight = 0.70
    type_weight = 0.65
    func_weight = 0.60
    same_package_weight = 0.55
    reverse_weight_factor = 0.4

    def build(self, fragments: list[Fragment], repo_root: Path | None = None) -> EdgeDict:
        go_frags = [f for f in fragments if _is_go_file(f.path)]
        if not go_frags:
            return {}

        edges: EdgeDict = {}

        pkg_to_frags: dict[str, list[FragmentId]] = defaultdict(list)
        path_to_frags: dict[str, list[FragmentId]] = defaultdict(list)
        type_defs: dict[str, list[FragmentId]] = defaultdict(list)
        func_defs: dict[str, list[FragmentId]] = defaultdict(list)

        for f in go_frags:
            pkg = _get_package_name(f.path)
            pkg_to_frags[pkg].append(f.id)

            if repo_root:
                try:
                    rel = f.path.relative_to(repo_root)
                    pkg_path = str(rel.parent)
                    path_to_frags[pkg_path].append(f.id)
                except ValueError:
                    pass

            funcs, types, _ = _extract_definitions(f.content)
            for t in types:
                type_defs[t.lower()].append(f.id)
            for fn in funcs:
                func_defs[fn.lower()].append(f.id)

        for gf in go_frags:
            imports = _extract_imports(gf.content)
            func_calls, type_refs, pkg_calls = _extract_references(gf.content)

            for imp in imports:
                imp_pkg = imp.split("/")[-1]
                for pkg, frag_ids in pkg_to_frags.items():
                    if pkg == imp_pkg:
                        for fid in frag_ids:
                            if fid != gf.id:
                                self.add_edge(edges, gf.id, fid, self.import_weight)

                for path_str, frag_ids in path_to_frags.items():
                    if imp in path_str or imp.endswith(path_str):
                        for fid in frag_ids:
                            if fid != gf.id:
                                self.add_edge(edges, gf.id, fid, self.import_weight)

            for type_ref in type_refs:
                if type_ref.lower() in type_defs:
                    for fid in type_defs[type_ref.lower()]:
                        if fid != gf.id:
                            self.add_edge(edges, gf.id, fid, self.type_weight)

            for func_call in func_calls:
                if func_call.lower() in func_defs:
                    for fid in func_defs[func_call.lower()]:
                        if fid != gf.id:
                            self.add_edge(edges, gf.id, fid, self.func_weight)

            for pkg_name, symbol in pkg_calls:
                if pkg_name.lower() in pkg_to_frags:
                    for fid in pkg_to_frags[pkg_name.lower()]:
                        if fid != gf.id:
                            self.add_edge(edges, gf.id, fid, self.func_weight)

            current_pkg = _get_package_name(gf.path)
            for fid in pkg_to_frags[current_pkg]:
                if fid != gf.id:
                    self.add_edge(edges, gf.id, fid, self.same_package_weight)

        return edges
