from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from ...types import Fragment, FragmentId
from ..base import EdgeBuilder, EdgeDict

_SWIFT_IMPORT_RE = re.compile(r"^\s*import\s+(\w+)", re.MULTILINE)

_SWIFT_CLASS_RE = re.compile(
    r"^\s*(?:public\s+|private\s+|internal\s+|fileprivate\s+|open\s+|final\s+)*class\s+(\w+)", re.MULTILINE
)
_SWIFT_STRUCT_RE = re.compile(r"^\s*(?:public\s+|private\s+|internal\s+|fileprivate\s+)*struct\s+(\w+)", re.MULTILINE)
_SWIFT_ENUM_RE = re.compile(r"^\s*(?:public\s+|private\s+|internal\s+|fileprivate\s+)*enum\s+(\w+)", re.MULTILINE)
_SWIFT_PROTOCOL_RE = re.compile(r"^\s*(?:public\s+|private\s+|internal\s+|fileprivate\s+)*protocol\s+(\w+)", re.MULTILINE)
_SWIFT_EXTENSION_RE = re.compile(r"^\s*(?:public\s+|private\s+|internal\s+|fileprivate\s+)*extension\s+(\w+)", re.MULTILINE)
_SWIFT_FUNC_RE = re.compile(
    r"^\s*(?:public\s+|private\s+|internal\s+|fileprivate\s+|open\s+|override\s+|static\s+|class\s+|@\w+\s+)*func\s+(\w+)\s*[\(<]",
    re.MULTILINE,
)
_SWIFT_TYPEALIAS_RE = re.compile(r"^\s*(?:public\s+|private\s+|internal\s+|fileprivate\s+)*typealias\s+(\w+)", re.MULTILINE)

_SWIFT_CONFORMANCE_RE = re.compile(r"(?:class|struct|enum)\s+\w+\s*(?:<[^>]+>)?\s*:\s*([^{]+)", re.MULTILINE)
_SWIFT_TYPE_REF_RE = re.compile(r"(?<![a-z_])([A-Z][a-zA-Z0-9]*)\b")
_SWIFT_FUNC_CALL_RE = re.compile(r"(?<![A-Za-z_])([a-z][a-zA-Z0-9]*)\s*\(")
_SWIFT_DOT_CALL_RE = re.compile(r"(\w+)\.([a-z][a-zA-Z0-9]*)\s*\(")


def _is_swift_file(path: Path) -> bool:
    return path.suffix.lower() == ".swift"


def _extract_imports(content: str) -> set[str]:
    return {m.group(1) for m in _SWIFT_IMPORT_RE.finditer(content)}


def _extract_definitions(content: str) -> tuple[set[str], set[str], set[str]]:
    types: set[str] = set()
    types.update(m.group(1) for m in _SWIFT_CLASS_RE.finditer(content))
    types.update(m.group(1) for m in _SWIFT_STRUCT_RE.finditer(content))
    types.update(m.group(1) for m in _SWIFT_ENUM_RE.finditer(content))
    types.update(m.group(1) for m in _SWIFT_TYPEALIAS_RE.finditer(content))

    protocols = {m.group(1) for m in _SWIFT_PROTOCOL_RE.finditer(content)}
    extensions = {m.group(1) for m in _SWIFT_EXTENSION_RE.finditer(content)}
    funcs = {m.group(1) for m in _SWIFT_FUNC_RE.finditer(content)}

    return funcs, types | protocols, extensions


def _extract_conformances(content: str) -> set[str]:
    conformances: set[str] = set()
    for match in _SWIFT_CONFORMANCE_RE.finditer(content):
        inheritance = match.group(1)
        for part in inheritance.split(","):
            part = part.strip()
            part = re.sub(r"<[^>]+>", "", part)
            part = re.sub(r"\s+where\s+.*", "", part)
            if part and part[0].isupper():
                conformances.add(part.strip())
    return conformances


def _extract_references(content: str) -> tuple[set[str], set[str], set[tuple[str, str]]]:
    type_refs = {m.group(1) for m in _SWIFT_TYPE_REF_RE.finditer(content) if m.group(1)[0].isupper()}
    func_calls = {m.group(1) for m in _SWIFT_FUNC_CALL_RE.finditer(content)}
    dot_calls = {(m.group(1), m.group(2)) for m in _SWIFT_DOT_CALL_RE.finditer(content)}
    return type_refs, func_calls, dot_calls


class SwiftEdgeBuilder(EdgeBuilder):
    weight = 0.75
    import_weight = 0.70
    conformance_weight = 0.70
    extension_weight = 0.70
    type_weight = 0.65
    func_weight = 0.60
    same_module_weight = 0.50
    reverse_weight_factor = 0.4

    def build(self, fragments: list[Fragment], repo_root: Path | None = None) -> EdgeDict:
        swift_frags = [f for f in fragments if _is_swift_file(f.path)]
        if not swift_frags:
            return {}

        edges: EdgeDict = {}

        module_to_frags: dict[str, list[FragmentId]] = defaultdict(list)
        type_defs: dict[str, list[FragmentId]] = defaultdict(list)
        func_defs: dict[str, list[FragmentId]] = defaultdict(list)
        extension_targets: dict[str, list[FragmentId]] = defaultdict(list)

        for f in swift_frags:
            parent = f.path.parent.name.lower()
            module_to_frags[parent].append(f.id)

            funcs, types, extensions = _extract_definitions(f.content)
            for t in types:
                type_defs[t.lower()].append(f.id)
            for fn in funcs:
                func_defs[fn.lower()].append(f.id)
            for ext in extensions:
                extension_targets[ext.lower()].append(f.id)

        for sf in swift_frags:
            imports = _extract_imports(sf.content)
            type_refs, func_calls, dot_calls = _extract_references(sf.content)
            conformances = _extract_conformances(sf.content)
            _, _, extensions = _extract_definitions(sf.content)

            for imp in imports:
                imp_lower = imp.lower()
                if imp_lower in module_to_frags:
                    for fid in module_to_frags[imp_lower]:
                        if fid != sf.id:
                            self.add_edge(edges, sf.id, fid, self.import_weight)

            for conf in conformances:
                conf_lower = conf.lower()
                if conf_lower in type_defs:
                    for fid in type_defs[conf_lower]:
                        if fid != sf.id:
                            self.add_edge(edges, sf.id, fid, self.conformance_weight)

            for ext in extensions:
                ext_lower = ext.lower()
                if ext_lower in type_defs:
                    for fid in type_defs[ext_lower]:
                        if fid != sf.id:
                            self.add_edge(edges, sf.id, fid, self.extension_weight)

            for type_ref in type_refs:
                ref_lower = type_ref.lower()
                if ref_lower in type_defs:
                    for fid in type_defs[ref_lower]:
                        if fid != sf.id:
                            self.add_edge(edges, sf.id, fid, self.type_weight)

            for func_call in func_calls:
                call_lower = func_call.lower()
                if call_lower in func_defs:
                    for fid in func_defs[call_lower]:
                        if fid != sf.id:
                            self.add_edge(edges, sf.id, fid, self.func_weight)

            for obj, method in dot_calls:
                obj_lower = obj.lower()
                if obj_lower in type_defs:
                    for fid in type_defs[obj_lower]:
                        if fid != sf.id:
                            self.add_edge(edges, sf.id, fid, self.func_weight)

            current_module = sf.path.parent.name.lower()
            for fid in module_to_frags[current_module]:
                if fid != sf.id:
                    self.add_edge(edges, sf.id, fid, self.same_module_weight)

        return edges
