from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from ...types import Fragment, FragmentId
from ..base import EdgeBuilder, EdgeDict

_HELM_VALUES_RE = re.compile(r"\{\{\s*\.Values\.([a-zA-Z0-9_.]+)\s*\}\}")
_HELM_INCLUDE_RE = re.compile(r'\{\{\s*(?:include|template)\s+"([^"]+)"')
_HELM_DEFINE_RE = re.compile(r'\{\{-?\s*define\s+"([^"]+)"')
_HELM_RELEASE_RE = re.compile(r"\{\{\s*\.Release\.(\w+)\s*\}\}")
_HELM_CHART_RE = re.compile(r"\{\{\s*\.Chart\.(\w+)\s*\}\}")
_HELM_FILES_RE = re.compile(r'\{\{\s*\.Files\.(?:Get|Glob)\s+"([^"]+)"')

_YAML_KEY_PATH_RE = re.compile(r"^(\s*)([a-zA-Z_][a-zA-Z0-9_-]*):", re.MULTILINE)


def _is_helm_template(path: Path) -> bool:
    parts = path.parts
    return "templates" in parts and path.suffix.lower() in {".yaml", ".yml", ".tpl"}


def _is_helm_values(path: Path) -> bool:
    name = path.name.lower()
    return name in {"values.yaml", "values.yml"} or name.startswith("values-") or name.startswith("values_")


def _is_chart_yaml(path: Path) -> bool:
    return path.name.lower() in {"chart.yaml", "chart.yml"}


def _extract_yaml_keys(content: str, max_depth: int = 4) -> set[str]:
    keys: set[str] = set()
    path_stack: list[tuple[int, str]] = []

    for match in _YAML_KEY_PATH_RE.finditer(content):
        indent = len(match.group(1))
        key = match.group(2)

        while path_stack and path_stack[-1][0] >= indent:
            path_stack.pop()

        path_stack.append((indent, key))

        if len(path_stack) <= max_depth:
            full_path = ".".join(k for _, k in path_stack)
            keys.add(full_path)
            keys.add(key)

    return keys


def _get_chart_root(path: Path) -> Path | None:
    current = path.parent
    for _ in range(5):
        if (current / "Chart.yaml").exists() or (current / "chart.yaml").exists():
            return current
        if current.parent == current:
            break
        current = current.parent
    return None


class HelmEdgeBuilder(EdgeBuilder):
    weight = 0.70
    reverse_weight_factor = 0.45

    def discover_related_files(
        self,
        changed_files: list[Path],
        all_candidate_files: list[Path],
        repo_root: Path | None = None,
    ) -> list[Path]:
        templates = [f for f in changed_files if _is_helm_template(f)]
        values = [f for f in changed_files if _is_helm_values(f)]

        if not templates and not values:
            return []

        chart_roots: set[Path] = set()
        for t in templates:
            root = _get_chart_root(t)
            if root:
                chart_roots.add(root)
        for v in values:
            root = _get_chart_root(v)
            if root:
                chart_roots.add(root)

        if not chart_roots:
            return []

        discovered: list[Path] = []
        changed_set = set(changed_files)

        for candidate in all_candidate_files:
            if candidate in changed_set:
                continue

            for chart_root in chart_roots:
                try:
                    if candidate.is_relative_to(chart_root):
                        if _is_helm_template(candidate) or _is_helm_values(candidate) or _is_chart_yaml(candidate):
                            discovered.append(candidate)
                            break
                except (ValueError, TypeError):
                    continue

        return discovered

    def build(self, fragments: list[Fragment], repo_root: Path | None = None) -> EdgeDict:
        templates = [f for f in fragments if _is_helm_template(f.path)]
        values_files = [f for f in fragments if _is_helm_values(f.path)]
        chart_files = [f for f in fragments if _is_chart_yaml(f.path)]

        if not templates and not values_files:
            return {}

        edges: EdgeDict = {}

        values_keys_by_chart: dict[Path, dict[str, list[FragmentId]]] = defaultdict(lambda: defaultdict(list))
        for vf in values_files:
            chart_root = _get_chart_root(vf.path) or vf.path.parent
            keys = _extract_yaml_keys(vf.content)
            for key in keys:
                values_keys_by_chart[chart_root][key].append(vf.id)

        define_defs: dict[str, list[FragmentId]] = defaultdict(list)
        for tmpl in templates:
            for match in _HELM_DEFINE_RE.finditer(tmpl.content):
                define_name = match.group(1)
                define_defs[define_name].append(tmpl.id)

        for tmpl in templates:
            chart_root = _get_chart_root(tmpl.path) or tmpl.path.parent.parent
            values_keys = values_keys_by_chart.get(chart_root, {})

            for match in _HELM_VALUES_RE.finditer(tmpl.content):
                value_path = match.group(1)
                parts = value_path.split(".")

                for i in range(len(parts), 0, -1):
                    partial = ".".join(parts[:i])
                    for values_id in values_keys.get(partial, []):
                        self.add_edge(edges, tmpl.id, values_id, self.weight)
                        break
                    else:
                        continue
                    break

                if parts[0] in values_keys:
                    for values_id in values_keys[parts[0]]:
                        self.add_edge(edges, tmpl.id, values_id, self.weight * 0.8)

            for match in _HELM_INCLUDE_RE.finditer(tmpl.content):
                include_name = match.group(1)
                for def_id in define_defs.get(include_name, []):
                    if def_id != tmpl.id:
                        self.add_edge(edges, tmpl.id, def_id, self.weight * 0.9)

            for cf in chart_files:
                cf_chart_root = _get_chart_root(cf.path) or cf.path.parent
                if cf_chart_root == chart_root:
                    self.add_edge(edges, tmpl.id, cf.id, self.weight * 0.5)

        return edges
