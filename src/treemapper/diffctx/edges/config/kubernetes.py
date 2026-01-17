from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from ...types import Fragment, FragmentId
from ..base import EdgeBuilder, EdgeDict

_K8S_API_VERSION_RE = re.compile(r"^apiVersion:\s*([^\s#]+)", re.MULTILINE)
_K8S_KIND_RE = re.compile(r"^kind:\s*(\w+)", re.MULTILINE)
_K8S_NAME_RE = re.compile(r"^\s+name:\s*['\"]?([^'\"#\n]+)", re.MULTILINE)
_K8S_NAMESPACE_RE = re.compile(r"^\s+namespace:\s*['\"]?([^'\"#\n]+)", re.MULTILINE)

_CONFIGMAP_REF_RE = re.compile(r"configMapKeyRef:\s*\n\s+name:\s*['\"]?([^'\"#\n]+)", re.MULTILINE)
_CONFIGMAP_NAME_RE = re.compile(r"configMapName:\s*['\"]?([^'\"#\n]+)", re.MULTILINE)
_SECRET_REF_RE = re.compile(r"secretKeyRef:\s*\n\s+name:\s*['\"]?([^'\"#\n]+)", re.MULTILINE)
_SECRET_NAME_RE = re.compile(r"secretName:\s*['\"]?([^'\"#\n]+)", re.MULTILINE)

_SERVICE_NAME_RE = re.compile(r"serviceName:\s*['\"]?([^'\"#\n]+)", re.MULTILINE)
_BACKEND_SERVICE_RE = re.compile(r"service:\s*\n\s+name:\s*['\"]?([^'\"#\n]+)", re.MULTILINE)

_IMAGE_RE = re.compile(r"^\s+image:\s*['\"]?([^'\"#\n]+)", re.MULTILINE)

_SELECTOR_MATCH_LABELS_RE = re.compile(r"selector:\s*\n\s+matchLabels:\s*\n((?:\s+[a-zA-Z0-9_./-]+:\s*[^\n:]+\n)+)", re.MULTILINE)
_LABELS_RE = re.compile(r"labels:\s*\n((?:\s+[a-zA-Z0-9_./-]+:\s*[^\n:]+\n)+)", re.MULTILINE)
_LABEL_PAIR_RE = re.compile(r"^\s*([a-zA-Z0-9_./-]+):\s*['\"]?([a-zA-Z0-9_./-]+)['\"]?\s*$", re.MULTILINE)
_SIMPLE_SELECTOR_RE = re.compile(r"selector:\s*\n((?:\s+[a-zA-Z0-9_./-]+:\s*[^\n:]+\n)+)", re.MULTILINE)

_VOLUME_CONFIGMAP_RE = re.compile(r"configMap:\s*\n\s+name:\s*['\"]?([^'\"#\n]+)", re.MULTILINE)
_VOLUME_SECRET_RE = re.compile(r"secret:\s*\n\s+secretName:\s*['\"]?([^'\"#\n]+)", re.MULTILINE)
_VOLUME_PVC_RE = re.compile(r"persistentVolumeClaim:\s*\n\s+claimName:\s*['\"]?([^'\"#\n]+)", re.MULTILINE)

_K8S_KINDS = {
    "Deployment",
    "Service",
    "ConfigMap",
    "Secret",
    "Ingress",
    "Pod",
    "ReplicaSet",
    "StatefulSet",
    "DaemonSet",
    "Job",
    "CronJob",
    "PersistentVolume",
    "PersistentVolumeClaim",
    "ServiceAccount",
    "Role",
    "RoleBinding",
    "ClusterRole",
    "ClusterRoleBinding",
    "NetworkPolicy",
    "HorizontalPodAutoscaler",
    "Namespace",
}


def _is_kubernetes_manifest(path: Path, content: str | None = None) -> bool:
    if path.suffix.lower() not in {".yaml", ".yml"}:
        return False

    if content is None:
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return False

    api_match = _K8S_API_VERSION_RE.search(content)
    kind_match = _K8S_KIND_RE.search(content)

    if api_match and kind_match:
        kind = kind_match.group(1).strip()
        return kind in _K8S_KINDS

    return False


def _extract_resource_info(content: str) -> tuple[str | None, str | None, str | None]:
    kind_match = _K8S_KIND_RE.search(content)
    name_match = _K8S_NAME_RE.search(content)
    namespace_match = _K8S_NAMESPACE_RE.search(content)

    kind = kind_match.group(1).strip() if kind_match else None
    name = name_match.group(1).strip() if name_match else None
    namespace = namespace_match.group(1).strip() if namespace_match else None

    return kind, name, namespace


def _extract_labels(content: str) -> dict[str, str]:
    labels: dict[str, str] = {}
    for match in _LABELS_RE.finditer(content):
        label_block = match.group(1)
        for pair_match in _LABEL_PAIR_RE.finditer(label_block):
            key = pair_match.group(1).strip()
            value = pair_match.group(2).strip()
            labels[key] = value
    return labels


def _extract_selector_labels(content: str) -> dict[str, str]:
    labels: dict[str, str] = {}
    for match in _SELECTOR_MATCH_LABELS_RE.finditer(content):
        label_block = match.group(1)
        for pair_match in _LABEL_PAIR_RE.finditer(label_block):
            key = pair_match.group(1).strip()
            value = pair_match.group(2).strip()
            labels[key] = value
    return labels


def _labels_match(selector: dict[str, str], labels: dict[str, str]) -> bool:
    if not selector:
        return False
    return all(labels.get(k) == v for k, v in selector.items())


class KubernetesEdgeBuilder(EdgeBuilder):
    weight = 0.65
    configmap_secret_weight = 0.70
    service_weight = 0.60
    selector_weight = 0.55
    image_weight = 0.40
    reverse_weight_factor = 0.45

    def discover_related_files(
        self,
        changed_files: list[Path],
        all_candidate_files: list[Path],
        repo_root: Path | None = None,
    ) -> list[Path]:
        k8s_files: list[Path] = []
        for f in changed_files:
            if f.suffix.lower() in {".yaml", ".yml"}:
                try:
                    content = f.read_text(encoding="utf-8")
                    if _is_kubernetes_manifest(f, content):
                        k8s_files.append(f)
                except (OSError, UnicodeDecodeError):
                    continue

        if not k8s_files:
            return []

        k8s_dirs: set[Path] = set()
        for f in k8s_files:
            k8s_dirs.add(f.parent)
            if f.parent.name in {"base", "overlays", "templates", "manifests"}:
                k8s_dirs.add(f.parent.parent)

        discovered: list[Path] = []
        changed_set = set(changed_files)

        for candidate in all_candidate_files:
            if candidate in changed_set:
                continue

            if candidate.suffix.lower() not in {".yaml", ".yml"}:
                continue

            for k8s_dir in k8s_dirs:
                try:
                    if candidate.is_relative_to(k8s_dir):
                        try:
                            content = candidate.read_text(encoding="utf-8")
                            if _is_kubernetes_manifest(candidate, content):
                                discovered.append(candidate)
                                break
                        except (OSError, UnicodeDecodeError):
                            continue
                except (ValueError, TypeError):
                    continue

        return discovered

    def build(self, fragments: list[Fragment], repo_root: Path | None = None) -> EdgeDict:
        k8s_fragments = [f for f in fragments if _is_kubernetes_manifest(f.path, f.content)]

        if not k8s_fragments:
            return {}

        edges: EdgeDict = {}

        configmaps: dict[str, list[FragmentId]] = defaultdict(list)
        secrets: dict[str, list[FragmentId]] = defaultdict(list)
        services: dict[str, list[FragmentId]] = defaultdict(list)
        pvcs: dict[str, list[FragmentId]] = defaultdict(list)
        pods_with_labels: list[tuple[FragmentId, dict[str, str]]] = []
        images: dict[str, list[FragmentId]] = defaultdict(list)

        for frag in k8s_fragments:
            kind, name, _ = _extract_resource_info(frag.content)

            if kind == "ConfigMap" and name:
                configmaps[name].append(frag.id)
            elif kind == "Secret" and name:
                secrets[name].append(frag.id)
            elif kind == "Service" and name:
                services[name].append(frag.id)
            elif kind == "PersistentVolumeClaim" and name:
                pvcs[name].append(frag.id)

            if kind in {"Pod", "Deployment", "StatefulSet", "DaemonSet", "ReplicaSet", "Job", "CronJob"}:
                labels = _extract_labels(frag.content)
                if labels:
                    pods_with_labels.append((frag.id, labels))

            for match in _IMAGE_RE.finditer(frag.content):
                image = match.group(1).strip()
                if image and not image.startswith("$"):
                    images[image].append(frag.id)

        for frag in k8s_fragments:
            self._build_configmap_edges(frag, configmaps, edges)
            self._build_secret_edges(frag, secrets, edges)
            self._build_service_edges(frag, services, edges)
            self._build_volume_edges(frag, configmaps, secrets, pvcs, edges)
            self._build_selector_edges(frag, pods_with_labels, edges)
            self._build_image_edges(frag, images, edges)

        return edges

    def _build_configmap_edges(
        self,
        frag: Fragment,
        configmaps: dict[str, list[FragmentId]],
        edges: EdgeDict,
    ) -> None:
        for match in _CONFIGMAP_REF_RE.finditer(frag.content):
            cm_name = match.group(1).strip()
            for cm_id in configmaps.get(cm_name, []):
                if cm_id != frag.id:
                    self.add_edge(edges, frag.id, cm_id, self.configmap_secret_weight)

        for match in _CONFIGMAP_NAME_RE.finditer(frag.content):
            cm_name = match.group(1).strip()
            for cm_id in configmaps.get(cm_name, []):
                if cm_id != frag.id:
                    self.add_edge(edges, frag.id, cm_id, self.configmap_secret_weight)

        for match in _VOLUME_CONFIGMAP_RE.finditer(frag.content):
            cm_name = match.group(1).strip()
            for cm_id in configmaps.get(cm_name, []):
                if cm_id != frag.id:
                    self.add_edge(edges, frag.id, cm_id, self.configmap_secret_weight)

    def _build_secret_edges(
        self,
        frag: Fragment,
        secrets: dict[str, list[FragmentId]],
        edges: EdgeDict,
    ) -> None:
        for match in _SECRET_REF_RE.finditer(frag.content):
            secret_name = match.group(1).strip()
            for secret_id in secrets.get(secret_name, []):
                if secret_id != frag.id:
                    self.add_edge(edges, frag.id, secret_id, self.configmap_secret_weight)

        for match in _SECRET_NAME_RE.finditer(frag.content):
            secret_name = match.group(1).strip()
            for secret_id in secrets.get(secret_name, []):
                if secret_id != frag.id:
                    self.add_edge(edges, frag.id, secret_id, self.configmap_secret_weight)

        for match in _VOLUME_SECRET_RE.finditer(frag.content):
            secret_name = match.group(1).strip()
            for secret_id in secrets.get(secret_name, []):
                if secret_id != frag.id:
                    self.add_edge(edges, frag.id, secret_id, self.configmap_secret_weight)

    def _build_service_edges(
        self,
        frag: Fragment,
        services: dict[str, list[FragmentId]],
        edges: EdgeDict,
    ) -> None:
        for match in _SERVICE_NAME_RE.finditer(frag.content):
            svc_name = match.group(1).strip()
            for svc_id in services.get(svc_name, []):
                if svc_id != frag.id:
                    self.add_edge(edges, frag.id, svc_id, self.service_weight)

        for match in _BACKEND_SERVICE_RE.finditer(frag.content):
            svc_name = match.group(1).strip()
            for svc_id in services.get(svc_name, []):
                if svc_id != frag.id:
                    self.add_edge(edges, frag.id, svc_id, self.service_weight)

    def _build_volume_edges(
        self,
        frag: Fragment,
        configmaps: dict[str, list[FragmentId]],
        secrets: dict[str, list[FragmentId]],
        pvcs: dict[str, list[FragmentId]],
        edges: EdgeDict,
    ) -> None:
        for match in _VOLUME_PVC_RE.finditer(frag.content):
            pvc_name = match.group(1).strip()
            for pvc_id in pvcs.get(pvc_name, []):
                if pvc_id != frag.id:
                    self.add_edge(edges, frag.id, pvc_id, self.weight)

    def _build_selector_edges(
        self,
        frag: Fragment,
        pods_with_labels: list[tuple[FragmentId, dict[str, str]]],
        edges: EdgeDict,
    ) -> None:
        kind, _, _ = _extract_resource_info(frag.content)

        if kind == "Service":
            selector = _extract_selector_labels(frag.content)
            if not selector:
                selector_match = _SIMPLE_SELECTOR_RE.search(frag.content)
                if selector_match:
                    for pair_match in _LABEL_PAIR_RE.finditer(selector_match.group(1)):
                        key = pair_match.group(1).strip()
                        value = pair_match.group(2).strip()
                        selector[key] = value

            if selector:
                for pod_id, labels in pods_with_labels:
                    if pod_id != frag.id and _labels_match(selector, labels):
                        self.add_edge(edges, frag.id, pod_id, self.selector_weight)

    def _build_image_edges(
        self,
        frag: Fragment,
        images: dict[str, list[FragmentId]],
        edges: EdgeDict,
    ) -> None:
        for match in _IMAGE_RE.finditer(frag.content):
            image = match.group(1).strip()
            if image and not image.startswith("$"):
                for other_id in images.get(image, []):
                    if other_id != frag.id:
                        self.add_edge(edges, frag.id, other_id, self.image_weight)
