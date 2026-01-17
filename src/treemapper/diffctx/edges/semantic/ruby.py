from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from ...types import Fragment, FragmentId
from ..base import EdgeBuilder, EdgeDict

_RUBY_EXTS = {".rb", ".rake", ".gemspec"}
_RUBY_FILES = {"rakefile", "gemfile", "guardfile", "vagrantfile", "capfile", "podfile"}

_RUBY_REQUIRE_RE = re.compile(r"^\s*require(?:_relative)?\s+['\"]([^'\"]+)['\"]", re.MULTILINE)
_RUBY_REQUIRE_RELATIVE_RE = re.compile(r"^\s*require_relative\s+['\"]([^'\"]+)['\"]", re.MULTILINE)
_RUBY_LOAD_RE = re.compile(r"^\s*load\s+['\"]([^'\"]+)['\"]", re.MULTILINE)
_RUBY_AUTOLOAD_RE = re.compile(r"^\s*autoload\s+:(\w+),\s*['\"]([^'\"]+)['\"]", re.MULTILINE)

_RUBY_CLASS_RE = re.compile(r"^\s*class\s+([A-Z]\w*(?:::[A-Z]\w*)*)", re.MULTILINE)
_RUBY_MODULE_RE = re.compile(r"^\s*module\s+([A-Z]\w*(?:::[A-Z]\w*)*)", re.MULTILINE)
_RUBY_DEF_RE = re.compile(r"^\s*def\s+(?:self\.)?([a-z_]\w*)", re.MULTILINE)
_RUBY_INCLUDE_RE = re.compile(r"^\s*(?:include|extend|prepend)\s+([A-Z]\w*(?:::[A-Z]\w*)*)", re.MULTILINE)
_RUBY_INHERIT_RE = re.compile(r"class\s+\w+\s*<\s*([A-Z]\w*(?:::[A-Z]\w*)*)")

_RUBY_CONST_REF_RE = re.compile(r"(?<![a-z_])([A-Z][a-zA-Z0-9_]*(?:::[A-Z][a-zA-Z0-9_]*)*)")
_RUBY_METHOD_CALL_RE = re.compile(r"\.([a-z_]\w*)\s*(?:\(|$|[^a-z_])")


def _is_ruby_file(path: Path) -> bool:
    if path.suffix.lower() in _RUBY_EXTS:
        return True
    return path.name.lower() in _RUBY_FILES


def _extract_requires(content: str) -> tuple[set[str], set[str]]:
    requires: set[str] = set()
    relative_requires: set[str] = set()

    for m in _RUBY_REQUIRE_RE.finditer(content):
        req = m.group(1)
        if "require_relative" not in m.group(0):
            requires.add(req)

    for m in _RUBY_REQUIRE_RELATIVE_RE.finditer(content):
        relative_requires.add(m.group(1))

    for m in _RUBY_LOAD_RE.finditer(content):
        requires.add(m.group(1))

    return requires, relative_requires


def _extract_autoloads(content: str) -> dict[str, str]:
    return {m.group(1): m.group(2) for m in _RUBY_AUTOLOAD_RE.finditer(content)}


def _extract_definitions(content: str) -> tuple[set[str], set[str], set[str]]:
    classes = {m.group(1).split("::")[-1] for m in _RUBY_CLASS_RE.finditer(content)}
    modules = {m.group(1).split("::")[-1] for m in _RUBY_MODULE_RE.finditer(content)}
    methods = {m.group(1) for m in _RUBY_DEF_RE.finditer(content)}
    return classes, modules, methods


def _extract_includes(content: str) -> set[str]:
    includes: set[str] = set()
    for m in _RUBY_INCLUDE_RE.finditer(content):
        full = m.group(1)
        includes.add(full.split("::")[-1])
    for m in _RUBY_INHERIT_RE.finditer(content):
        full = m.group(1)
        includes.add(full.split("::")[-1])
    return includes


def _extract_const_refs(content: str) -> set[str]:
    refs: set[str] = set()
    for m in _RUBY_CONST_REF_RE.finditer(content):
        full = m.group(1)
        refs.add(full.split("::")[-1])
    return refs


def _underscore_to_camel(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_"))


class RubyEdgeBuilder(EdgeBuilder):
    weight = 0.70
    require_weight = 0.75
    include_weight = 0.70
    const_weight = 0.60
    same_dir_weight = 0.50
    reverse_weight_factor = 0.4

    def build(self, fragments: list[Fragment], repo_root: Path | None = None) -> EdgeDict:
        ruby_frags = [f for f in fragments if _is_ruby_file(f.path)]
        if not ruby_frags:
            return {}

        edges: EdgeDict = {}

        name_to_frags: dict[str, list[FragmentId]] = defaultdict(list)
        path_to_frags: dict[str, list[FragmentId]] = defaultdict(list)
        class_to_frags: dict[str, list[FragmentId]] = defaultdict(list)
        module_to_frags: dict[str, list[FragmentId]] = defaultdict(list)

        for f in ruby_frags:
            stem = f.path.stem.lower()
            name_to_frags[stem].append(f.id)

            camel = _underscore_to_camel(stem).lower()
            name_to_frags[camel].append(f.id)

            if repo_root:
                try:
                    rel = f.path.relative_to(repo_root)
                    path_to_frags[str(rel)].append(f.id)
                    path_to_frags[rel.as_posix()].append(f.id)
                    no_ext = str(rel.with_suffix(""))
                    path_to_frags[no_ext].append(f.id)
                except ValueError:
                    pass

            classes, modules, _ = _extract_definitions(f.content)
            for cls in classes:
                class_to_frags[cls.lower()].append(f.id)
            for mod in modules:
                module_to_frags[mod.lower()].append(f.id)

        for rf in ruby_frags:
            requires, relative_requires = _extract_requires(rf.content)
            includes = _extract_includes(rf.content)
            const_refs = _extract_const_refs(rf.content)

            for req in requires:
                req_name = req.split("/")[-1].lower()
                if req_name in name_to_frags:
                    for fid in name_to_frags[req_name]:
                        if fid != rf.id:
                            self.add_edge(edges, rf.id, fid, self.require_weight)

                for path_str, frag_ids in path_to_frags.items():
                    if req in path_str or req.replace("/", "\\") in path_str:
                        for fid in frag_ids:
                            if fid != rf.id:
                                self.add_edge(edges, rf.id, fid, self.require_weight)

            for rel_req in relative_requires:
                if repo_root:
                    try:
                        target = (rf.path.parent / rel_req).resolve()
                        if not target.suffix:
                            target = target.with_suffix(".rb")
                        target_rel = str(target.relative_to(repo_root))
                        if target_rel in path_to_frags:
                            for fid in path_to_frags[target_rel]:
                                if fid != rf.id:
                                    self.add_edge(edges, rf.id, fid, self.require_weight)
                    except (ValueError, OSError):
                        pass

                rel_name = rel_req.split("/")[-1].lower()
                if rel_name in name_to_frags:
                    for fid in name_to_frags[rel_name]:
                        if fid != rf.id:
                            self.add_edge(edges, rf.id, fid, self.require_weight)

            for inc in includes:
                inc_lower = inc.lower()
                if inc_lower in class_to_frags:
                    for fid in class_to_frags[inc_lower]:
                        if fid != rf.id:
                            self.add_edge(edges, rf.id, fid, self.include_weight)
                if inc_lower in module_to_frags:
                    for fid in module_to_frags[inc_lower]:
                        if fid != rf.id:
                            self.add_edge(edges, rf.id, fid, self.include_weight)

            for const in const_refs:
                const_lower = const.lower()
                if const_lower in class_to_frags:
                    for fid in class_to_frags[const_lower]:
                        if fid != rf.id:
                            self.add_edge(edges, rf.id, fid, self.const_weight)
                if const_lower in module_to_frags:
                    for fid in module_to_frags[const_lower]:
                        if fid != rf.id:
                            self.add_edge(edges, rf.id, fid, self.const_weight)

            for f in ruby_frags:
                if f.path.parent == rf.path.parent and f.id != rf.id:
                    self.add_edge(edges, rf.id, f.id, self.same_dir_weight)

        return edges
