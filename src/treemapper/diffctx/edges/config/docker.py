from __future__ import annotations

import re
from pathlib import Path

from ...types import Fragment, FragmentId
from ..base import EdgeBuilder, EdgeDict, build_path_to_frags, discover_files_by_refs

_DOCKERFILE_NAMES = {"dockerfile"}
_COMPOSE_NAMES = {"docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"}

_DOCKERFILE_FROM_RE = re.compile(r"^FROM\s+(\S+)", re.MULTILINE | re.IGNORECASE)
_DOCKERFILE_COPY_RE = re.compile(r"^(?:COPY|ADD)\s+(?:--[^\s]+\s+)*([^\s]+)\s+", re.MULTILINE | re.IGNORECASE)
_DOCKERFILE_ENV_RE = re.compile(r"^ENV\s+(\w+)", re.MULTILINE | re.IGNORECASE)
_DOCKERFILE_ARG_RE = re.compile(r"^ARG\s+(\w+)", re.MULTILINE | re.IGNORECASE)

_COMPOSE_BUILD_RE = re.compile(r"^\s+build:\s*['\"]?([^'\"#\n]+)", re.MULTILINE)
_COMPOSE_CONTEXT_RE = re.compile(r"^\s+context:\s*['\"]?([^'\"#\n]+)", re.MULTILINE)
_COMPOSE_DOCKERFILE_RE = re.compile(r"^\s+dockerfile:\s*['\"]?([^'\"#\n]+)", re.MULTILINE)
_COMPOSE_DEPENDS_RE = re.compile(r"depends_on:\s*\n((?:\s+-\s*\w+\s*\n)+)", re.MULTILINE)
_COMPOSE_SERVICE_RE = re.compile(r"^(\w+):\s*$", re.MULTILINE)
_COMPOSE_VOLUME_RE = re.compile(r"^\s+-\s*['\"]?([./][^:'\"\n]+):", re.MULTILINE)


def _is_dockerfile(path: Path) -> bool:
    name = path.name.lower()
    return name in _DOCKERFILE_NAMES or name.startswith("dockerfile.") or name.endswith(".dockerfile")


def _is_compose_file(path: Path) -> bool:
    return path.name.lower() in _COMPOSE_NAMES


def _normalize_path(base_dir: Path, rel_path: str) -> Path:
    rel_path = rel_path.strip().strip("'\"")
    if rel_path.startswith("./"):
        rel_path = rel_path[2:]
    return base_dir / rel_path


class DockerEdgeBuilder(EdgeBuilder):
    weight = 0.55
    copy_weight = 0.65
    compose_weight = 0.50
    reverse_weight_factor = 0.40

    def discover_related_files(
        self,
        changed_files: list[Path],
        all_candidate_files: list[Path],
        repo_root: Path | None = None,
    ) -> list[Path]:
        docker_files = [f for f in changed_files if _is_dockerfile(f) or _is_compose_file(f)]
        if not docker_files:
            return []

        refs: set[str] = set()

        for df in docker_files:
            try:
                content = df.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            if _is_dockerfile(df):
                for match in _DOCKERFILE_COPY_RE.finditer(content):
                    src = match.group(1)
                    if not src.startswith("--") and not src.startswith("$"):
                        refs.add(src.strip().strip("'\"").lstrip("./"))

            if _is_compose_file(df):
                for match in _COMPOSE_BUILD_RE.finditer(content):
                    refs.add(match.group(1).strip().lstrip("./"))
                for match in _COMPOSE_VOLUME_RE.finditer(content):
                    refs.add(match.group(1).strip().lstrip("./"))

        return discover_files_by_refs(refs, changed_files, all_candidate_files)

    def build(self, fragments: list[Fragment], repo_root: Path | None = None) -> EdgeDict:
        edges: EdgeDict = {}

        dockerfiles = [f for f in fragments if _is_dockerfile(f.path)]
        compose_files = [f for f in fragments if _is_compose_file(f.path)]

        if not dockerfiles and not compose_files:
            return edges

        path_to_frags = build_path_to_frags(fragments, repo_root)

        self._build_dockerfile_edges(dockerfiles, path_to_frags, edges)
        self._build_compose_edges(compose_files, dockerfiles, path_to_frags, edges)

        return edges

    def _build_dockerfile_edges(
        self,
        dockerfiles: list[Fragment],
        path_to_frags: dict[Path, list[FragmentId]],
        edges: EdgeDict,
    ) -> None:
        for df in dockerfiles:
            base_dir = df.path.parent

            for match in _DOCKERFILE_COPY_RE.finditer(df.content):
                src_path = match.group(1)
                if src_path.startswith("--") or src_path.startswith("$"):
                    continue

                target = _normalize_path(base_dir, src_path)
                for frag_id in path_to_frags.get(target, []):
                    self.add_edge(edges, df.id, frag_id, self.copy_weight)

                if "*" not in src_path:
                    for p, frag_ids in path_to_frags.items():
                        if str(p).endswith(src_path.lstrip("./")):
                            for frag_id in frag_ids:
                                self.add_edge(edges, df.id, frag_id, self.copy_weight * 0.8)

            env_vars = set(_DOCKERFILE_ENV_RE.findall(df.content))
            arg_vars = set(_DOCKERFILE_ARG_RE.findall(df.content))
            all_vars = env_vars | arg_vars

            if all_vars:
                env_files = [p for p in path_to_frags.keys() if p.suffix.lower() == ".env" or p.name.lower().startswith(".env")]
                for env_file in env_files:
                    for frag_id in path_to_frags.get(env_file, []):
                        self.add_edge(edges, df.id, frag_id, self.weight)

    def _build_compose_edges(
        self,
        compose_files: list[Fragment],
        dockerfiles: list[Fragment],
        path_to_frags: dict[Path, list[FragmentId]],
        edges: EdgeDict,
    ) -> None:
        for cf in compose_files:
            base_dir = cf.path.parent

            for df in dockerfiles:
                if df.path.parent == base_dir or df.path.parent.parent == base_dir:
                    self.add_edge(edges, cf.id, df.id, self.compose_weight)

            for match in _COMPOSE_BUILD_RE.finditer(cf.content):
                build_path = match.group(1).strip()
                if build_path and not build_path.startswith("$"):
                    target_dir = _normalize_path(base_dir, build_path)
                    dockerfile_path = target_dir / "Dockerfile"
                    for frag_id in path_to_frags.get(dockerfile_path, []):
                        self.add_edge(edges, cf.id, frag_id, self.compose_weight)

            for match in _COMPOSE_CONTEXT_RE.finditer(cf.content):
                context_path = match.group(1).strip()
                if context_path and not context_path.startswith("$"):
                    target_dir = _normalize_path(base_dir, context_path)
                    for p, frag_ids in path_to_frags.items():
                        try:
                            if p.is_relative_to(target_dir) or target_dir.is_relative_to(p.parent):
                                for frag_id in frag_ids:
                                    self.add_edge(edges, cf.id, frag_id, self.compose_weight * 0.7)
                        except (ValueError, TypeError):
                            continue

            for match in _COMPOSE_VOLUME_RE.finditer(cf.content):
                vol_path = match.group(1).strip()
                if vol_path:
                    target = _normalize_path(base_dir, vol_path)
                    for frag_id in path_to_frags.get(target, []):
                        self.add_edge(edges, cf.id, frag_id, self.compose_weight * 0.6)
