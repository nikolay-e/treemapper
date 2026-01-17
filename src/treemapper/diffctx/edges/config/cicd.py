from __future__ import annotations

import re
from pathlib import Path

from ...types import Fragment
from ..base import EdgeBuilder, EdgeDict, FragmentIndex, discover_files_by_refs

_GHA_RUN_RE = re.compile(r"^\s*-?\s*run:\s*[|>]?\s*(.+?)(?:\n\s{4,}|\n[^\s]|$)", re.MULTILINE | re.DOTALL)
_GHA_USES_RE = re.compile(r"^\s*uses:\s*([^\s@]+)", re.MULTILINE)
_GHA_WITH_RE = re.compile(r"^\s*with:\s*\n((?:\s+\w+:.+\n)+)", re.MULTILINE)

_GITLAB_SCRIPT_RE = re.compile(r"^\s*(?:script|before_script|after_script):\s*\n((?:\s+-\s*.+\n)+)", re.MULTILINE)
_GITLAB_INCLUDE_RE = re.compile(r"^\s*-?\s*(?:local|project|remote|template):\s*['\"]?([^'\"#\n]+)", re.MULTILINE)
_GITLAB_EXTENDS_RE = re.compile(r"^\s*extends:\s*['\"]?([^'\"#\n]+)", re.MULTILINE)

_JENKINS_STAGE_RE = re.compile(r"stage\s*\(\s*['\"]([^'\"]+)['\"]", re.MULTILINE)
_JENKINS_SH_RE = re.compile(r"sh\s*(?:\(['\"]|['\"])(.+?)(?:['\"](?:\))?)", re.MULTILINE | re.DOTALL)
_JENKINS_SCRIPT_RE = re.compile(r"script\s*\{([^}]+)\}", re.MULTILINE | re.DOTALL)

_SCRIPT_CALL_RE = re.compile(r"(?:bash|sh|python|python3|node|npm|yarn|pnpm|make|go|cargo|dotnet|mvn|gradle)\s+([^\s;&|]+)")
_FILE_REF_RE = re.compile(r"(?:\.\/|scripts\/|bin\/|tools\/)([a-zA-Z0-9_.-]+(?:\.(?:sh|py|js|ts|rb))?)")


def _is_github_actions(path: Path) -> bool:
    parts = path.parts
    return ".github" in parts and "workflows" in parts and path.suffix.lower() in {".yml", ".yaml"}


def _is_gitlab_ci(path: Path) -> bool:
    return path.name.lower() in {".gitlab-ci.yml", ".gitlab-ci.yaml"} or path.name.lower().startswith("gitlab-ci")


def _is_jenkinsfile(path: Path) -> bool:
    name = path.name.lower()
    return name == "jenkinsfile" or name.endswith(".jenkinsfile") or name.endswith(".jenkins")


def _is_circleci(path: Path) -> bool:
    return ".circleci" in path.parts and path.name.lower() in {"config.yml", "config.yaml"}


def _is_travis(path: Path) -> bool:
    return path.name.lower() in {".travis.yml", ".travis.yaml"}


def _is_azure_pipelines(path: Path) -> bool:
    name = path.name.lower()
    return name in {"azure-pipelines.yml", "azure-pipelines.yaml"} or name.startswith("azure-pipeline")


def _is_ci_file(path: Path) -> bool:
    return any(
        [
            _is_github_actions(path),
            _is_gitlab_ci(path),
            _is_jenkinsfile(path),
            _is_circleci(path),
            _is_travis(path),
            _is_azure_pipelines(path),
        ]
    )


def _extract_script_refs(content: str) -> set[str]:
    refs: set[str] = set()

    for match in _SCRIPT_CALL_RE.finditer(content):
        script = match.group(1).strip().strip("'\"")
        if script and not script.startswith("-"):
            refs.add(script)

    for match in _FILE_REF_RE.finditer(content):
        refs.add(match.group(1))

    return refs


def _extract_gha_refs(content: str) -> set[str]:
    refs: set[str] = set()

    for match in _GHA_RUN_RE.finditer(content):
        run_content = match.group(1)
        refs.update(_extract_script_refs(run_content))

    return refs


def _extract_gitlab_refs(content: str) -> set[str]:
    refs: set[str] = set()

    for match in _GITLAB_SCRIPT_RE.finditer(content):
        script_block = match.group(1)
        refs.update(_extract_script_refs(script_block))

    for match in _GITLAB_INCLUDE_RE.finditer(content):
        refs.add(match.group(1).strip())

    return refs


def _extract_jenkins_refs(content: str) -> set[str]:
    refs: set[str] = set()

    for match in _JENKINS_SH_RE.finditer(content):
        sh_content = match.group(1)
        refs.update(_extract_script_refs(sh_content))

    for match in _JENKINS_SCRIPT_RE.finditer(content):
        refs.update(_extract_script_refs(match.group(1)))

    return refs


class CICDEdgeBuilder(EdgeBuilder):
    weight = 0.55
    script_weight = 0.60
    reverse_weight_factor = 0.35

    def discover_related_files(
        self,
        changed_files: list[Path],
        all_candidate_files: list[Path],
        repo_root: Path | None = None,
    ) -> list[Path]:
        ci_files = [f for f in changed_files if _is_ci_file(f)]
        if not ci_files:
            return []

        refs: set[str] = set()

        for ci in ci_files:
            try:
                content = ci.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            if _is_github_actions(ci):
                refs.update(_extract_gha_refs(content))
            elif _is_gitlab_ci(ci):
                refs.update(_extract_gitlab_refs(content))
            elif _is_jenkinsfile(ci):
                refs.update(_extract_jenkins_refs(content))
            else:
                refs.update(_extract_script_refs(content))

            if any(cmd in content.lower() for cmd in ["npm", "yarn", "pnpm"]):
                refs.add("package.json")

        return discover_files_by_refs(refs, changed_files, all_candidate_files)

    def build(self, fragments: list[Fragment], repo_root: Path | None = None) -> EdgeDict:
        ci_frags = [f for f in fragments if _is_ci_file(f.path)]
        if not ci_frags:
            return {}

        edges: EdgeDict = {}
        idx = FragmentIndex(fragments, repo_root)

        for ci in ci_frags:
            refs: set[str] = set()

            if _is_github_actions(ci.path):
                refs = _extract_gha_refs(ci.content)
            elif _is_gitlab_ci(ci.path):
                refs = _extract_gitlab_refs(ci.content)
            elif _is_jenkinsfile(ci.path):
                refs = _extract_jenkins_refs(ci.content)
            else:
                refs = _extract_script_refs(ci.content)

            for ref in refs:
                ref_lower = ref.lower()
                ref_name = ref.split("/")[-1].lower()

                for name, frag_ids in idx.by_name.items():
                    if name == ref_name or name.startswith(ref_name.split(".")[0]):
                        for fid in frag_ids:
                            if fid != ci.id:
                                self.add_edge(edges, ci.id, fid, self.script_weight)

                for path_str, frag_ids in idx.by_path.items():
                    if ref in path_str or ref_lower in path_str.lower():
                        for fid in frag_ids:
                            if fid != ci.id:
                                self.add_edge(edges, ci.id, fid, self.script_weight)

            self._link_to_package_json(ci, fragments, edges)

        return edges

    def _link_to_package_json(self, ci_frag: Fragment, all_frags: list[Fragment], edges: EdgeDict) -> None:
        npm_commands = {"npm", "yarn", "pnpm", "npx"}
        if not any(cmd in ci_frag.content.lower() for cmd in npm_commands):
            return

        for f in all_frags:
            if f.path.name.lower() == "package.json":
                self.add_edge(edges, ci_frag.id, f.id, self.weight * 0.8)
