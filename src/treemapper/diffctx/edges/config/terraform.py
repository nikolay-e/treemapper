from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from ...types import Fragment, FragmentId
from ..base import EdgeBuilder, EdgeDict, build_path_to_frags

_TF_EXTENSIONS = {".tf", ".tfvars", ".hcl"}

_TF_VARIABLE_RE = re.compile(r'^variable\s+"([^"]+)"', re.MULTILINE)
_TF_RESOURCE_RE = re.compile(r'^resource\s+"([^"]+)"\s+"([^"]+)"', re.MULTILINE)
_TF_DATA_RE = re.compile(r'^data\s+"([^"]+)"\s+"([^"]+)"', re.MULTILINE)
_TF_OUTPUT_RE = re.compile(r'^output\s+"([^"]+)"', re.MULTILINE)
_TF_MODULE_RE = re.compile(r'^module\s+"([^"]+)"', re.MULTILINE)
_TF_LOCALS_RE = re.compile(r"^locals\s*\{", re.MULTILINE)
_TF_LOCAL_KEY_RE = re.compile(r"^\s+(\w+)\s*=", re.MULTILINE)

_TF_VAR_REF_RE = re.compile(r"var\.(\w+)")
_TF_LOCAL_REF_RE = re.compile(r"local\.(\w+)")
_TF_DATA_REF_RE = re.compile(r"data\.(\w+)\.(\w+)")
_TF_RESOURCE_REF_RE = re.compile(r"(?<![.\w])(\w+)\.(\w+)\.(\w+)")
_TF_MODULE_REF_RE = re.compile(r"module\.(\w+)")

_TF_SOURCE_RE = re.compile(r'^\s*source\s*=\s*"([^"]+)"', re.MULTILINE)


def _is_terraform_file(path: Path) -> bool:
    return path.suffix.lower() in _TF_EXTENSIONS


def _extract_locals(content: str) -> set[str]:
    locals_keys: set[str] = set()
    in_locals = False
    brace_count = 0

    for line in content.splitlines():
        if _TF_LOCALS_RE.match(line):
            in_locals = True
            brace_count = 1
            continue

        if in_locals:
            brace_count += line.count("{") - line.count("}")
            if brace_count <= 0:
                in_locals = False
                continue

            match = _TF_LOCAL_KEY_RE.match(line)
            if match:
                locals_keys.add(match.group(1))

    return locals_keys


class TerraformEdgeBuilder(EdgeBuilder):
    weight = 0.60
    reverse_weight_factor = 0.40

    def discover_related_files(
        self,
        changed_files: list[Path],
        all_candidate_files: list[Path],
        repo_root: Path | None = None,
    ) -> list[Path]:
        tf_files = [f for f in changed_files if _is_terraform_file(f)]
        if not tf_files:
            return []

        tf_dirs: set[Path] = set()
        module_sources: set[str] = set()

        for tf in tf_files:
            tf_dirs.add(tf.parent)

            try:
                content = tf.read_text(encoding="utf-8")
                for match in _TF_SOURCE_RE.finditer(content):
                    src = match.group(1)
                    if src.startswith("./") or src.startswith("../"):
                        module_sources.add(src)
            except (OSError, UnicodeDecodeError):
                continue

        discovered: list[Path] = []
        changed_set = set(changed_files)

        for candidate in all_candidate_files:
            if candidate in changed_set:
                continue

            if _is_terraform_file(candidate):
                if candidate.parent in tf_dirs:
                    discovered.append(candidate)
                    continue

                for src in module_sources:
                    try:
                        for tf_dir in tf_dirs:
                            module_path = (tf_dir / src).resolve()
                            if candidate.is_relative_to(module_path):
                                discovered.append(candidate)
                                break
                    except (ValueError, OSError):
                        continue

        return discovered

    def build(self, fragments: list[Fragment], repo_root: Path | None = None) -> EdgeDict:
        tf_frags = [f for f in fragments if _is_terraform_file(f.path)]
        if not tf_frags:
            return {}

        edges: EdgeDict = {}

        var_defs: dict[str, list[FragmentId]] = defaultdict(list)
        resource_defs: dict[str, list[FragmentId]] = defaultdict(list)
        data_defs: dict[str, list[FragmentId]] = defaultdict(list)
        local_defs: dict[str, list[FragmentId]] = defaultdict(list)
        module_defs: dict[str, list[FragmentId]] = defaultdict(list)
        output_defs: dict[str, list[FragmentId]] = defaultdict(list)

        for f in tf_frags:
            for match in _TF_VARIABLE_RE.finditer(f.content):
                var_defs[match.group(1)].append(f.id)

            for match in _TF_RESOURCE_RE.finditer(f.content):
                resource_type, resource_name = match.group(1), match.group(2)
                resource_defs[f"{resource_type}.{resource_name}"].append(f.id)
                resource_defs[resource_name].append(f.id)

            for match in _TF_DATA_RE.finditer(f.content):
                data_type, data_name = match.group(1), match.group(2)
                data_defs[f"{data_type}.{data_name}"].append(f.id)
                data_defs[data_name].append(f.id)

            for local_key in _extract_locals(f.content):
                local_defs[local_key].append(f.id)

            for match in _TF_MODULE_RE.finditer(f.content):
                module_defs[match.group(1)].append(f.id)

            for match in _TF_OUTPUT_RE.finditer(f.content):
                output_defs[match.group(1)].append(f.id)

        for f in tf_frags:
            for match in _TF_VAR_REF_RE.finditer(f.content):
                var_name = match.group(1)
                for def_id in var_defs.get(var_name, []):
                    if def_id != f.id:
                        self.add_edge(edges, f.id, def_id, self.weight)

            for match in _TF_LOCAL_REF_RE.finditer(f.content):
                local_name = match.group(1)
                for def_id in local_defs.get(local_name, []):
                    if def_id != f.id:
                        self.add_edge(edges, f.id, def_id, self.weight)

            for match in _TF_DATA_REF_RE.finditer(f.content):
                data_type, data_name = match.group(1), match.group(2)
                full_ref = f"{data_type}.{data_name}"
                for def_id in data_defs.get(full_ref, []) + data_defs.get(data_name, []):
                    if def_id != f.id:
                        self.add_edge(edges, f.id, def_id, self.weight)

            for match in _TF_MODULE_REF_RE.finditer(f.content):
                module_name = match.group(1)
                for def_id in module_defs.get(module_name, []):
                    if def_id != f.id:
                        self.add_edge(edges, f.id, def_id, self.weight)

            for match in _TF_RESOURCE_REF_RE.finditer(f.content):
                res_type, res_name, _attr = match.groups()
                if res_type in ("var", "local", "data", "module", "path", "terraform"):
                    continue
                full_ref = f"{res_type}.{res_name}"
                for def_id in resource_defs.get(full_ref, []) + resource_defs.get(res_name, []):
                    if def_id != f.id:
                        self.add_edge(edges, f.id, def_id, self.weight)

        self._build_module_source_edges(tf_frags, fragments, edges, repo_root)

        return edges

    def _build_module_source_edges(
        self,
        tf_frags: list[Fragment],
        all_frags: list[Fragment],
        edges: EdgeDict,
        repo_root: Path | None,
    ) -> None:
        path_to_frags = build_path_to_frags(all_frags, repo_root)

        for f in tf_frags:
            base_dir = f.path.parent

            for match in _TF_SOURCE_RE.finditer(f.content):
                source = match.group(1)

                if source.startswith("./") or source.startswith("../"):
                    module_dir = (base_dir / source).resolve()
                    for p, frag_ids in path_to_frags.items():
                        try:
                            resolved = p.resolve() if p.is_absolute() else (repo_root / p).resolve() if repo_root else p
                            if resolved.parent == module_dir or str(resolved).startswith(str(module_dir)):
                                for frag_id in frag_ids:
                                    if frag_id != f.id:
                                        self.add_edge(edges, f.id, frag_id, self.weight * 0.8)
                        except (ValueError, OSError):
                            continue
