from __future__ import annotations

import re
from pathlib import Path

from ...types import Fragment, FragmentId
from ..base import EdgeBuilder, EdgeDict, FragmentIndex, discover_files_by_refs

_MAKEFILE_NAMES = {"makefile", "gnumakefile"}
_MAKEFILE_EXTS = {".mk", ".mak", ".make"}

_MAKE_TARGET_RE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_.-]*)(?:\s*:(?!=))", re.MULTILINE)
_MAKE_INCLUDE_RE = re.compile(r"^(?:-)?include\s+(.+)$", re.MULTILINE)
_MAKE_VAR_RE = re.compile(r"^\s*([A-Z_][A-Z0-9_]*)\s*[:?]?=", re.MULTILINE)
_MAKE_RECIPE_RE = re.compile(r"^\t(.+)$", re.MULTILINE)

_CMAKE_ADD_EXE_RE = re.compile(r"add_executable\s*\(\s*(\w+)", re.IGNORECASE)
_CMAKE_ADD_LIB_RE = re.compile(r"add_library\s*\(\s*(\w+)", re.IGNORECASE)
_CMAKE_TARGET_LINK_RE = re.compile(
    r"target_link_libraries\s*\(\s*(\w+)\s+(?:PUBLIC|PRIVATE|INTERFACE)?\s*([\w\s]+)\)", re.IGNORECASE
)
_CMAKE_INCLUDE_RE = re.compile(r"include\s*\(\s*([^\)]+)\s*\)", re.IGNORECASE)
_CMAKE_ADD_SUBDIR_RE = re.compile(r"add_subdirectory\s*\(\s*([^\)\s]+)", re.IGNORECASE)
_CMAKE_FIND_PKG_RE = re.compile(r"find_package\s*\(\s*(\w+)", re.IGNORECASE)
_CMAKE_SET_RE = re.compile(r"set\s*\(\s*([A-Z_][A-Z0-9_]*)", re.IGNORECASE)

_SCRIPT_CALL_RE = re.compile(r"(?:bash|sh|python|python3|\.\/scripts\/|\.\/bin\/)([a-zA-Z0-9_.-]+)")
_SOURCE_FILE_RE = re.compile(r"\b([a-zA-Z_][a-zA-Z0-9_]*\.(?:c|cpp|cc|cxx|h|hpp|hxx|py|sh|go|rs|java))\b")


def _is_makefile(path: Path) -> bool:
    name = path.name.lower()
    return name in _MAKEFILE_NAMES or path.suffix.lower() in _MAKEFILE_EXTS


def _is_cmake(path: Path) -> bool:
    name = path.name.lower()
    return name == "cmakelists.txt" or path.suffix.lower() == ".cmake"


def _extract_make_refs(content: str) -> tuple[set[str], set[str]]:
    targets: set[str] = set()
    file_refs: set[str] = set()

    for match in _MAKE_TARGET_RE.finditer(content):
        targets.add(match.group(1))

    for match in _MAKE_INCLUDE_RE.finditer(content):
        includes = match.group(1).split()
        for inc in includes:
            inc = inc.strip()
            if inc and not inc.startswith("$"):
                file_refs.add(inc)

    for match in _MAKE_RECIPE_RE.finditer(content):
        recipe = match.group(1)
        file_refs.update(_SCRIPT_CALL_RE.findall(recipe))
        file_refs.update(_SOURCE_FILE_RE.findall(recipe))

    file_refs.update(_SOURCE_FILE_RE.findall(content))

    return targets, file_refs


def _extract_cmake_refs(content: str) -> tuple[set[str], set[str]]:
    targets: set[str] = set()
    file_refs: set[str] = set()

    for pattern in [_CMAKE_ADD_EXE_RE, _CMAKE_ADD_LIB_RE]:
        for match in pattern.finditer(content):
            targets.add(match.group(1))

    for match in _CMAKE_TARGET_LINK_RE.finditer(content):
        targets.add(match.group(1))
        deps = match.group(2).split()
        targets.update(d for d in deps if d and not d.startswith("$"))

    for match in _CMAKE_INCLUDE_RE.finditer(content):
        file_refs.add(match.group(1).strip())

    for match in _CMAKE_ADD_SUBDIR_RE.finditer(content):
        subdir = match.group(1).strip()
        file_refs.add(subdir)
        file_refs.add(f"{subdir}/CMakeLists.txt")

    file_refs.update(_SOURCE_FILE_RE.findall(content))

    return targets, file_refs


class BuildSystemEdgeBuilder(EdgeBuilder):
    weight = 0.55
    target_weight = 0.50
    file_ref_weight = 0.60
    reverse_weight_factor = 0.35

    def discover_related_files(
        self,
        changed_files: list[Path],
        all_candidate_files: list[Path],
        repo_root: Path | None = None,
    ) -> list[Path]:
        make_files = [f for f in changed_files if _is_makefile(f)]
        cmake_files = [f for f in changed_files if _is_cmake(f)]

        if not make_files and not cmake_files:
            return []

        refs: set[str] = set()

        for mf in make_files:
            try:
                content = mf.read_text(encoding="utf-8")
                _, file_refs = _extract_make_refs(content)
                refs.update(file_refs)
            except (OSError, UnicodeDecodeError):
                continue

        for cf in cmake_files:
            try:
                content = cf.read_text(encoding="utf-8")
                _, file_refs = _extract_cmake_refs(content)
                refs.update(file_refs)
            except (OSError, UnicodeDecodeError):
                continue

        return discover_files_by_refs(refs, changed_files, all_candidate_files)

    def build(self, fragments: list[Fragment], repo_root: Path | None = None) -> EdgeDict:
        make_frags = [f for f in fragments if _is_makefile(f.path)]
        cmake_frags = [f for f in fragments if _is_cmake(f.path)]

        if not make_frags and not cmake_frags:
            return {}

        edges: EdgeDict = {}
        idx = FragmentIndex(fragments, repo_root)

        for mf in make_frags:
            _targets, file_refs = _extract_make_refs(mf.content)

            for ref in file_refs:
                self._link_ref(mf.id, ref, idx, edges)

            for cf in cmake_frags:
                if cf.path.parent == mf.path.parent:
                    self.add_edge(edges, mf.id, cf.id, self.weight * 0.7)

        for cf in cmake_frags:
            _targets, file_refs = _extract_cmake_refs(cf.content)

            for ref in file_refs:
                self._link_ref(cf.id, ref, idx, edges)

            parent_cmake = cf.path.parent.parent / "CMakeLists.txt"
            for f in fragments:
                if f.path == parent_cmake:
                    self.add_edge(edges, cf.id, f.id, self.weight * 0.6)

        return edges

    def _link_ref(
        self,
        src_id: FragmentId,
        ref: str,
        idx: FragmentIndex,
        edges: EdgeDict,
    ) -> None:
        ref_lower = ref.lower()
        ref_name = ref.split("/")[-1].lower()

        for name, frag_ids in idx.by_name.items():
            if name == ref_name:
                for fid in frag_ids:
                    if fid != src_id:
                        self.add_edge(edges, src_id, fid, self.file_ref_weight)

        for path_str, frag_ids in idx.by_path.items():
            if ref in path_str or ref_lower in path_str.lower():
                for fid in frag_ids:
                    if fid != src_id:
                        self.add_edge(edges, src_id, fid, self.file_ref_weight)
