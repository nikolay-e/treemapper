from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from ...types import Fragment, FragmentId
from ..base import EdgeBuilder, EdgeDict

_RUST_USE_RE = re.compile(r"^\s*use\s+(?:crate::)?([a-z_][a-z0-9_]*(?:::[a-z_][a-z0-9_]*)*)", re.MULTILINE)
_RUST_MOD_RE = re.compile(r"^\s*(?:pub\s+)?mod\s+([a-z_][a-z0-9_]*)\s*[;{]", re.MULTILINE)
_RUST_EXTERN_CRATE_RE = re.compile(r"^\s*extern\s+crate\s+([a-z_][a-z0-9_]*)", re.MULTILINE)

_RUST_FN_RE = re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?fn\s+([a-z_][a-z0-9_]*)", re.MULTILINE)
_RUST_STRUCT_RE = re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?struct\s+([A-Z][a-zA-Z0-9_]*)", re.MULTILINE)
_RUST_ENUM_RE = re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?enum\s+([A-Z][a-zA-Z0-9_]*)", re.MULTILINE)
_RUST_TRAIT_RE = re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?trait\s+([A-Z][a-zA-Z0-9_]*)", re.MULTILINE)
_RUST_IMPL_RE = re.compile(r"^\s*impl(?:<[^>]+>)?\s+(?:([A-Z][a-zA-Z0-9_]*)|(?:\w+\s+for\s+)?([A-Z][a-zA-Z0-9_]*))", re.MULTILINE)
_RUST_TYPE_ALIAS_RE = re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?type\s+([A-Z][a-zA-Z0-9_]*)", re.MULTILINE)

_RUST_TYPE_REF_RE = re.compile(r"(?<![a-z_])([A-Z][a-zA-Z0-9_]*)\b")
_RUST_FN_CALL_RE = re.compile(r"(?<![A-Za-z_])([a-z_][a-z0-9_]*)\s*[!]?\s*\(")
_RUST_PATH_CALL_RE = re.compile(r"([a-z_][a-z0-9_]*)::([a-z_][a-z0-9_]*|[A-Z][a-zA-Z0-9_]*)")


def _is_rust_file(path: Path) -> bool:
    return path.suffix.lower() == ".rs"


def _extract_uses(content: str) -> set[str]:
    uses: set[str] = set()
    for match in _RUST_USE_RE.finditer(content):
        path = match.group(1)
        uses.add(path)
        parts = path.split("::")
        if len(parts) > 1:
            uses.add(parts[0])
    return uses


def _extract_mods(content: str) -> set[str]:
    return {m.group(1) for m in _RUST_MOD_RE.finditer(content)}


def _extract_definitions(content: str) -> tuple[set[str], set[str], set[str]]:
    funcs = {m.group(1) for m in _RUST_FN_RE.finditer(content)}
    types: set[str] = set()
    types.update(m.group(1) for m in _RUST_STRUCT_RE.finditer(content))
    types.update(m.group(1) for m in _RUST_ENUM_RE.finditer(content))
    types.update(m.group(1) for m in _RUST_TRAIT_RE.finditer(content))
    types.update(m.group(1) for m in _RUST_TYPE_ALIAS_RE.finditer(content))

    for m in _RUST_IMPL_RE.finditer(content):
        if m.group(1):
            types.add(m.group(1))
        if m.group(2):
            types.add(m.group(2))

    traits = {m.group(1) for m in _RUST_TRAIT_RE.finditer(content)}
    return funcs, types, traits


def _extract_references(content: str) -> tuple[set[str], set[str], set[tuple[str, str]]]:
    type_refs = {m.group(1) for m in _RUST_TYPE_REF_RE.finditer(content)}
    fn_calls = {m.group(1) for m in _RUST_FN_CALL_RE.finditer(content)}
    path_calls = {(m.group(1), m.group(2)) for m in _RUST_PATH_CALL_RE.finditer(content)}
    return type_refs, fn_calls, path_calls


class RustEdgeBuilder(EdgeBuilder):
    weight = 0.75
    mod_weight = 0.70
    use_weight = 0.65
    type_weight = 0.65
    fn_weight = 0.60
    same_crate_weight = 0.50
    reverse_weight_factor = 0.4

    def build(self, fragments: list[Fragment], repo_root: Path | None = None) -> EdgeDict:
        rust_frags = [f for f in fragments if _is_rust_file(f.path)]
        if not rust_frags:
            return {}

        edges: EdgeDict = {}

        name_to_frags: dict[str, list[FragmentId]] = defaultdict(list)
        mod_to_frags: dict[str, list[FragmentId]] = defaultdict(list)
        type_defs: dict[str, list[FragmentId]] = defaultdict(list)
        fn_defs: dict[str, list[FragmentId]] = defaultdict(list)

        for f in rust_frags:
            stem = f.path.stem.lower()
            name_to_frags[stem].append(f.id)

            if stem == "mod" or stem == "lib":
                parent = f.path.parent.name.lower()
                mod_to_frags[parent].append(f.id)
            else:
                mod_to_frags[stem].append(f.id)

            funcs, types, _ = _extract_definitions(f.content)
            for t in types:
                type_defs[t.lower()].append(f.id)
            for fn in funcs:
                fn_defs[fn.lower()].append(f.id)

            declared_mods = _extract_mods(f.content)
            for mod_name in declared_mods:
                mod_to_frags[mod_name.lower()].append(f.id)

        for rf in rust_frags:
            uses = _extract_uses(rf.content)
            type_refs, fn_calls, path_calls = _extract_references(rf.content)

            for use_path in uses:
                parts = use_path.split("::")
                for part in parts:
                    part_lower = part.lower()
                    if part_lower in mod_to_frags:
                        for fid in mod_to_frags[part_lower]:
                            if fid != rf.id:
                                self.add_edge(edges, rf.id, fid, self.use_weight)
                    if part_lower in name_to_frags:
                        for fid in name_to_frags[part_lower]:
                            if fid != rf.id:
                                self.add_edge(edges, rf.id, fid, self.use_weight)

            declared_mods = _extract_mods(rf.content)
            for mod_name in declared_mods:
                mod_lower = mod_name.lower()
                if mod_lower in name_to_frags:
                    for fid in name_to_frags[mod_lower]:
                        if fid != rf.id:
                            self.add_edge(edges, rf.id, fid, self.mod_weight)

            for type_ref in type_refs:
                ref_lower = type_ref.lower()
                if ref_lower in type_defs:
                    for fid in type_defs[ref_lower]:
                        if fid != rf.id:
                            self.add_edge(edges, rf.id, fid, self.type_weight)

            for fn_call in fn_calls:
                call_lower = fn_call.lower()
                if call_lower in fn_defs:
                    for fid in fn_defs[call_lower]:
                        if fid != rf.id:
                            self.add_edge(edges, rf.id, fid, self.fn_weight)

            for mod_name, symbol in path_calls:
                mod_lower = mod_name.lower()
                if mod_lower in mod_to_frags:
                    for fid in mod_to_frags[mod_lower]:
                        if fid != rf.id:
                            self.add_edge(edges, rf.id, fid, self.use_weight)

            if rf.path.stem.lower() in {"lib", "main", "mod"}:
                parent_dir = rf.path.parent
                for f in rust_frags:
                    if f.path.parent == parent_dir and f.id != rf.id:
                        self.add_edge(edges, rf.id, f.id, self.same_crate_weight)

        return edges
