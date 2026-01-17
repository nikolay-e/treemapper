from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from ...types import Fragment, FragmentId
from ..base import EdgeBuilder, EdgeDict

_JAVA_EXTS = {".java"}
_KOTLIN_EXTS = {".kt", ".kts"}
_SCALA_EXTS = {".scala", ".sc"}
_JVM_EXTS = _JAVA_EXTS | _KOTLIN_EXTS | _SCALA_EXTS

_JAVA_IMPORT_RE = re.compile(r"^\s*import\s+(?:static\s+)?([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*(?:\.[A-Z]\w*)?)", re.MULTILINE)
_JAVA_PACKAGE_RE = re.compile(r"^\s*package\s+([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*)", re.MULTILINE)
_JAVA_CLASS_RE = re.compile(
    r"^\s*(?:public|private|protected)?\s*(?:abstract|final)?\s*(?:class|interface|enum|record)\s+([A-Z]\w*)", re.MULTILINE
)
_JAVA_EXTENDS_RE = re.compile(r"\bextends\s+([A-Z]\w*)")
_JAVA_IMPLEMENTS_RE = re.compile(r"\bimplements\s+([A-Z]\w*(?:\s*,\s*[A-Z]\w*)*)")

_KOTLIN_IMPORT_RE = re.compile(r"^\s*import\s+([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*(?:\.[A-Z]\w*)?)", re.MULTILINE)
_KOTLIN_CLASS_RE = re.compile(
    r"^\s*(?:public|private|internal|protected)?\s*(?:abstract|open|sealed|data|inline|value)?\s*(?:class|interface|object|enum)\s+([A-Z]\w*)",
    re.MULTILINE,
)
_KOTLIN_FUN_RE = re.compile(
    r"^\s*(?:public|private|internal|protected)?\s*(?:suspend\s+)?fun\s+(?:<[^>]+>\s+)?([a-z][a-zA-Z0-9_]*)", re.MULTILINE
)

_SCALA_IMPORT_RE = re.compile(r"^\s*import\s+([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*(?:\.[A-Z_]\w*)?)", re.MULTILINE)
_SCALA_CLASS_RE = re.compile(r"^\s*(?:abstract\s+)?(?:sealed\s+)?(?:case\s+)?(?:class|trait|object)\s+([A-Z]\w*)", re.MULTILINE)
_SCALA_DEF_RE = re.compile(r"^\s*(?:private|protected)?\s*def\s+([a-z][a-zA-Z0-9_]*)", re.MULTILINE)

_TYPE_REF_RE = re.compile(r"(?<![a-z_])([A-Z][a-zA-Z0-9_]*)\b")
_ANNOTATION_RE = re.compile(r"@([A-Z][a-zA-Z0-9_]*)")


def _is_jvm_file(path: Path) -> bool:
    return path.suffix.lower() in _JVM_EXTS


def _is_java(path: Path) -> bool:
    return path.suffix.lower() in _JAVA_EXTS


def _is_kotlin(path: Path) -> bool:
    return path.suffix.lower() in _KOTLIN_EXTS


def _is_scala(path: Path) -> bool:
    return path.suffix.lower() in _SCALA_EXTS


def _extract_imports(content: str, path: Path) -> set[str]:
    if _is_java(path):
        return {m.group(1) for m in _JAVA_IMPORT_RE.finditer(content)}
    elif _is_kotlin(path):
        return {m.group(1) for m in _KOTLIN_IMPORT_RE.finditer(content)}
    elif _is_scala(path):
        return {m.group(1) for m in _SCALA_IMPORT_RE.finditer(content)}
    return set()


def _extract_package(content: str) -> str | None:
    match = _JAVA_PACKAGE_RE.search(content)
    return match.group(1) if match else None


def _extract_classes(content: str, path: Path) -> set[str]:
    classes: set[str] = set()
    if _is_java(path):
        classes.update(m.group(1) for m in _JAVA_CLASS_RE.finditer(content))
    elif _is_kotlin(path):
        classes.update(m.group(1) for m in _KOTLIN_CLASS_RE.finditer(content))
    elif _is_scala(path):
        classes.update(m.group(1) for m in _SCALA_CLASS_RE.finditer(content))
    return classes


def _extract_inheritance(content: str) -> set[str]:
    refs: set[str] = set()
    for m in _JAVA_EXTENDS_RE.finditer(content):
        refs.add(m.group(1))
    for m in _JAVA_IMPLEMENTS_RE.finditer(content):
        for cls in m.group(1).split(","):
            refs.add(cls.strip())
    return refs


def _extract_type_refs(content: str) -> set[str]:
    return {m.group(1) for m in _TYPE_REF_RE.finditer(content)}


def _extract_annotations(content: str) -> set[str]:
    return {m.group(1) for m in _ANNOTATION_RE.finditer(content)}


class JVMEdgeBuilder(EdgeBuilder):
    weight = 0.70
    import_weight = 0.75
    inheritance_weight = 0.80
    type_weight = 0.60
    same_package_weight = 0.55
    annotation_weight = 0.50
    reverse_weight_factor = 0.4

    def build(self, fragments: list[Fragment], repo_root: Path | None = None) -> EdgeDict:
        jvm_frags = [f for f in fragments if _is_jvm_file(f.path)]
        if not jvm_frags:
            return {}

        edges: EdgeDict = {}

        package_to_frags: dict[str, list[FragmentId]] = defaultdict(list)
        class_to_frags: dict[str, list[FragmentId]] = defaultdict(list)
        fqn_to_frags: dict[str, list[FragmentId]] = defaultdict(list)

        for f in jvm_frags:
            pkg = _extract_package(f.content)
            if pkg:
                package_to_frags[pkg].append(f.id)

            classes = _extract_classes(f.content, f.path)
            for cls in classes:
                class_to_frags[cls.lower()].append(f.id)
                if pkg:
                    fqn = f"{pkg}.{cls}"
                    fqn_to_frags[fqn.lower()].append(f.id)

        for jf in jvm_frags:
            imports = _extract_imports(jf.content, jf.path)
            inheritance = _extract_inheritance(jf.content)
            type_refs = _extract_type_refs(jf.content)
            annotations = _extract_annotations(jf.content)
            current_pkg = _extract_package(jf.content)

            for imp in imports:
                imp_lower = imp.lower()
                if imp_lower in fqn_to_frags:
                    for fid in fqn_to_frags[imp_lower]:
                        if fid != jf.id:
                            self.add_edge(edges, jf.id, fid, self.import_weight)

                parts = imp.split(".")
                if parts:
                    class_name = parts[-1].lower()
                    if class_name in class_to_frags:
                        for fid in class_to_frags[class_name]:
                            if fid != jf.id:
                                self.add_edge(edges, jf.id, fid, self.import_weight)

            for parent in inheritance:
                parent_lower = parent.lower()
                if parent_lower in class_to_frags:
                    for fid in class_to_frags[parent_lower]:
                        if fid != jf.id:
                            self.add_edge(edges, jf.id, fid, self.inheritance_weight)

            for type_ref in type_refs:
                ref_lower = type_ref.lower()
                if ref_lower in class_to_frags:
                    for fid in class_to_frags[ref_lower]:
                        if fid != jf.id:
                            self.add_edge(edges, jf.id, fid, self.type_weight)

            for annot in annotations:
                annot_lower = annot.lower()
                if annot_lower in class_to_frags:
                    for fid in class_to_frags[annot_lower]:
                        if fid != jf.id:
                            self.add_edge(edges, jf.id, fid, self.annotation_weight)

            if current_pkg and current_pkg in package_to_frags:
                for fid in package_to_frags[current_pkg]:
                    if fid != jf.id:
                        self.add_edge(edges, jf.id, fid, self.same_package_weight)

        return edges
