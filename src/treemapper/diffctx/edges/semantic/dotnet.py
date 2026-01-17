from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from ...types import Fragment, FragmentId
from ..base import EdgeBuilder, EdgeDict

_CSHARP_EXTS = {".cs"}
_FSHARP_EXTS = {".fs", ".fsi", ".fsx"}
_DOTNET_EXTS = _CSHARP_EXTS | _FSHARP_EXTS

_CS_USING_RE = re.compile(r"^\s*using\s+(?:static\s+)?([A-Z][a-zA-Z0-9_.]*);", re.MULTILINE)
_CS_NAMESPACE_RE = re.compile(r"^\s*namespace\s+([A-Z][a-zA-Z0-9_.]*)", re.MULTILINE)
_CS_CLASS_RE = re.compile(
    r"^\s*(?:public|private|protected|internal)?\s*(?:static|sealed|abstract|partial)?\s*(?:class|interface|struct|record|enum)\s+([A-Z]\w*)",
    re.MULTILINE,
)
_CS_INHERIT_RE = re.compile(r"(?:class|interface|struct|record)\s+\w+\s*(?:<[^>]+>)?\s*:\s*([A-Z]\w*(?:\s*,\s*[A-Z]\w*)*)")
_CS_GENERIC_RE = re.compile(r"<([A-Z]\w*(?:\s*,\s*[A-Z]\w*)*)>")
_CS_METHOD_RE = re.compile(
    r"^\s*(?:public|private|protected|internal)?\s*(?:static|virtual|override|abstract|async)?\s*(?:[A-Z]\w*(?:<[^>]+>)?)\s+([A-Z][a-zA-Z0-9_]*)\s*\(",
    re.MULTILINE,
)

_FS_OPEN_RE = re.compile(r"^\s*open\s+([A-Z][a-zA-Z0-9_.]*)", re.MULTILINE)
_FS_MODULE_RE = re.compile(r"^\s*module\s+(?:rec\s+)?([A-Z][a-zA-Z0-9_.]*)", re.MULTILINE)
_FS_NAMESPACE_RE = re.compile(r"^\s*namespace\s+(?:rec\s+)?([A-Z][a-zA-Z0-9_.]*)", re.MULTILINE)
_FS_TYPE_RE = re.compile(r"^\s*type\s+(?:private\s+)?([A-Z]\w*)", re.MULTILINE)
_FS_LET_RE = re.compile(r"^\s*let\s+(?:rec\s+)?(?:private\s+)?([a-z][a-zA-Z0-9_]*)", re.MULTILINE)

_TYPE_REF_RE = re.compile(r"(?<![a-z_])([A-Z][a-zA-Z0-9_]*)\b")
_ATTRIBUTE_RE = re.compile(r"\[([A-Z][a-zA-Z0-9_]*)\]")


def _is_dotnet_file(path: Path) -> bool:
    return path.suffix.lower() in _DOTNET_EXTS


def _is_csharp(path: Path) -> bool:
    return path.suffix.lower() in _CSHARP_EXTS


def _is_fsharp(path: Path) -> bool:
    return path.suffix.lower() in _FSHARP_EXTS


def _extract_usings(content: str, path: Path) -> set[str]:
    if _is_csharp(path):
        return {m.group(1) for m in _CS_USING_RE.finditer(content)}
    elif _is_fsharp(path):
        return {m.group(1) for m in _FS_OPEN_RE.finditer(content)}
    return set()


def _extract_namespace(content: str, path: Path) -> str | None:
    if _is_csharp(path):
        match = _CS_NAMESPACE_RE.search(content)
    else:
        match = _FS_NAMESPACE_RE.search(content) or _FS_MODULE_RE.search(content)
    return match.group(1) if match else None


def _extract_types(content: str, path: Path) -> set[str]:
    types: set[str] = set()
    if _is_csharp(path):
        types.update(m.group(1) for m in _CS_CLASS_RE.finditer(content))
    elif _is_fsharp(path):
        types.update(m.group(1) for m in _FS_TYPE_RE.finditer(content))
    return types


def _extract_inheritance(content: str) -> set[str]:
    refs: set[str] = set()
    for m in _CS_INHERIT_RE.finditer(content):
        for cls in m.group(1).split(","):
            refs.add(cls.strip())
    return refs


def _extract_type_refs(content: str) -> set[str]:
    return {m.group(1) for m in _TYPE_REF_RE.finditer(content)}


def _extract_attributes(content: str) -> set[str]:
    return {m.group(1) for m in _ATTRIBUTE_RE.finditer(content)}


class DotNetEdgeBuilder(EdgeBuilder):
    weight = 0.70
    using_weight = 0.75
    inheritance_weight = 0.80
    type_weight = 0.60
    same_namespace_weight = 0.55
    attribute_weight = 0.50
    partial_class_weight = 0.85
    reverse_weight_factor = 0.4

    def build(self, fragments: list[Fragment], repo_root: Path | None = None) -> EdgeDict:
        dotnet_frags = [f for f in fragments if _is_dotnet_file(f.path)]
        if not dotnet_frags:
            return {}

        edges: EdgeDict = {}

        namespace_to_frags: dict[str, list[FragmentId]] = defaultdict(list)
        type_to_frags: dict[str, list[FragmentId]] = defaultdict(list)
        fqn_to_frags: dict[str, list[FragmentId]] = defaultdict(list)

        for f in dotnet_frags:
            ns = _extract_namespace(f.content, f.path)
            if ns:
                namespace_to_frags[ns.lower()].append(f.id)
                for i in range(len(ns.split("."))):
                    partial_ns = ".".join(ns.split(".")[: i + 1])
                    namespace_to_frags[partial_ns.lower()].append(f.id)

            types = _extract_types(f.content, f.path)
            for t in types:
                type_to_frags[t.lower()].append(f.id)
                if ns:
                    fqn = f"{ns}.{t}"
                    fqn_to_frags[fqn.lower()].append(f.id)

        for df in dotnet_frags:
            usings = _extract_usings(df.content, df.path)
            inheritance = _extract_inheritance(df.content)
            type_refs = _extract_type_refs(df.content)
            attributes = _extract_attributes(df.content)
            current_ns = _extract_namespace(df.content, df.path)
            current_types = _extract_types(df.content, df.path)

            for using in usings:
                using_lower = using.lower()
                if using_lower in namespace_to_frags:
                    for fid in namespace_to_frags[using_lower]:
                        if fid != df.id:
                            self.add_edge(edges, df.id, fid, self.using_weight)

                if using_lower in fqn_to_frags:
                    for fid in fqn_to_frags[using_lower]:
                        if fid != df.id:
                            self.add_edge(edges, df.id, fid, self.using_weight)

                parts = using.split(".")
                if parts:
                    type_name = parts[-1].lower()
                    if type_name in type_to_frags:
                        for fid in type_to_frags[type_name]:
                            if fid != df.id:
                                self.add_edge(edges, df.id, fid, self.using_weight)

            for parent in inheritance:
                parent_lower = parent.lower()
                if parent_lower in type_to_frags:
                    for fid in type_to_frags[parent_lower]:
                        if fid != df.id:
                            self.add_edge(edges, df.id, fid, self.inheritance_weight)

            for type_ref in type_refs:
                ref_lower = type_ref.lower()
                if ref_lower in type_to_frags:
                    for fid in type_to_frags[ref_lower]:
                        if fid != df.id:
                            self.add_edge(edges, df.id, fid, self.type_weight)

            for attr in attributes:
                attr_lower = attr.lower()
                attr_full = (attr_lower + "attribute") if not attr_lower.endswith("attribute") else attr_lower
                for lookup in [attr_lower, attr_full]:
                    if lookup in type_to_frags:
                        for fid in type_to_frags[lookup]:
                            if fid != df.id:
                                self.add_edge(edges, df.id, fid, self.attribute_weight)

            if current_ns and current_ns.lower() in namespace_to_frags:
                for fid in namespace_to_frags[current_ns.lower()]:
                    if fid != df.id:
                        self.add_edge(edges, df.id, fid, self.same_namespace_weight)

            for current_type in current_types:
                ct_lower = current_type.lower()
                if ct_lower in type_to_frags:
                    for fid in type_to_frags[ct_lower]:
                        if fid != df.id:
                            self.add_edge(edges, df.id, fid, self.partial_class_weight)

        return edges
