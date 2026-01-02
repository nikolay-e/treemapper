from __future__ import annotations

import math
import re
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from heapq import nlargest
from pathlib import Path

from .python_semantics import PyFragmentInfo, analyze_python_fragment
from .stopwords import TokenProfile, filter_idents
from .types import Fragment, FragmentId, extract_identifier_list

_TOP_K_NEIGHBORS = 10
_MIN_SIMILARITY = 0.1
_BACKWARD_WEIGHT_FACTOR = 0.7
_LEXICAL_WEIGHT_MIN = 0.1
_LEXICAL_WEIGHT_MAX = 0.2
_HUB_PERCENTILE = 0.95

_MAX_DF_RATIO = 0.20
_MIN_IDF = 1.6
_MAX_POSTINGS = 200

_CALL_WEIGHT = 0.85
_SYMBOL_REF_WEIGHT = 0.95
_TYPE_REF_WEIGHT = 0.60
_CONTAINMENT_WEIGHT = 0.50
_CONTAINMENT_REVERSE_WEIGHT = 0.35

_IMPORT_WEIGHT = 0.5
_IMPORT_REVERSE_WEIGHT = 0.35
_IMPORT_RE = re.compile(r"(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))")

_TEST_WEIGHT_DIRECT = 0.60
_TEST_WEIGHT_NAMING = 0.50
_TEST_REVERSE_WEIGHT = 0.30

_CONFIG_CODE_WEIGHT = 0.45
_CONFIG_KEY_RE = re.compile(r"^\s*([a-zA-Z_][a-zA-Z0-9_-]*)\s*:", re.MULTILINE)
_TOML_KEY_RE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_-]*)\s*=", re.MULTILINE)
_TOML_SECTION_RE = re.compile(r"^\[([a-zA-Z_][a-zA-Z0-9_.-]*)\]", re.MULTILINE)

_SIBLING_WEIGHT = 0.15

_JAVA_EXT = ".java"
_SCALA_EXT = ".scala"
_JVM_EXTENSIONS = {_JAVA_EXT, ".kt", ".kts", _SCALA_EXT}


@dataclass(frozen=True)
class LangWeights:
    call: float
    symbol_ref: float
    type_ref: float
    lexical_min: float
    lexical_max: float


_LANG_WEIGHTS: dict[str, LangWeights] = {
    "python": LangWeights(0.55, 0.60, 0.50, 0.20, 0.35),
    "javascript": LangWeights(0.50, 0.55, 0.45, 0.25, 0.35),
    "typescript": LangWeights(0.70, 0.75, 0.65, 0.15, 0.25),
    "rust": LangWeights(0.90, 0.95, 0.85, 0.10, 0.15),
    "java": LangWeights(0.85, 0.90, 0.80, 0.10, 0.15),
    "kotlin": LangWeights(0.80, 0.85, 0.75, 0.12, 0.18),
    "scala": LangWeights(0.80, 0.85, 0.75, 0.12, 0.18),
    "go": LangWeights(0.80, 0.85, 0.75, 0.12, 0.20),
}

_DEFAULT_LANG_WEIGHTS = LangWeights(0.55, 0.60, 0.50, 0.15, 0.25)


_SUFFIX_TO_LANG: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".rs": "rust",
    ".go": "go",
    _JAVA_EXT: "java",
    ".kt": "kotlin",
    ".kts": "kotlin",
    _SCALA_EXT: "scala",
}


def _get_lang_weights(path: Path) -> LangWeights:
    suffix = path.suffix.lower()
    lang = _SUFFIX_TO_LANG.get(suffix)
    return _LANG_WEIGHTS.get(lang, _DEFAULT_LANG_WEIGHTS) if lang else _DEFAULT_LANG_WEIGHTS


_DOC_STRUCTURE_WEIGHT = 0.30
_DOC_STRUCTURE_REVERSE_WEIGHT = 0.25
_ANCHOR_LINK_WEIGHT = 0.55
_ANCHOR_LINK_REVERSE_WEIGHT = 0.35
_CITATION_WEIGHT = 0.25

_CITATION_RE = re.compile(r"\[@([a-zA-Z0-9_:-]+)\]")
_MD_INTERNAL_LINK_RE = re.compile(r"\[([^\]]+)\]\(#([^)]+)\)")
_MD_HEADING_RE = re.compile(r"^#{1,6}\s+([^\n]+)$", re.MULTILINE)  # NOSONAR(S5852)


def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-")


@dataclass
class Graph:
    adjacency: dict[FragmentId, dict[FragmentId, float]] = field(default_factory=dict)
    nodes: set[FragmentId] = field(default_factory=set)

    def add_node(self, node: FragmentId) -> None:
        self.nodes.add(node)

    def add_edge(self, src: FragmentId, dst: FragmentId, weight: float) -> None:
        if src not in self.adjacency:
            self.adjacency[src] = {}
        existing = self.adjacency[src].get(dst, 0.0)
        self.adjacency[src][dst] = max(existing, weight)
        self.nodes.add(src)
        self.nodes.add(dst)

    def neighbors(self, node: FragmentId) -> dict[FragmentId, float]:
        return self.adjacency.get(node, {})


def build_graph(fragments: list[Fragment]) -> Graph:
    graph = Graph()

    for frag in fragments:
        graph.nodes.add(frag.id)

    # Collect all edges from various sources
    all_edges: dict[tuple[FragmentId, FragmentId], float] = {}

    for edge_dict in [
        _build_python_semantic_edges(fragments),
        _build_containment_edges(fragments),
        _build_import_edges(fragments),
        _build_test_edges(fragments),
        _build_document_structure_edges(fragments),
        _build_anchor_link_edges(fragments),
        _build_citation_edges_sparse(fragments),
        _build_config_code_edges(fragments),
        _build_package_sibling_edges(fragments),
        _build_lexical_edges_sparse(fragments),
    ]:
        for (src, dst), weight in edge_dict.items():
            all_edges[(src, dst)] = max(all_edges.get((src, dst), 0.0), weight)

    # Apply hub suppression to ALL edges
    all_edges = _apply_hub_suppression(all_edges)

    for (src, dst), weight in all_edges.items():
        graph.add_edge(src, dst, weight)

    return graph


def _add_ref_edges(
    edges: dict[tuple[FragmentId, FragmentId], float],
    src_id: FragmentId,
    names: set[str],
    name_to_defs: dict[str, list[FragmentId]],
    weight: float,
    skip_self_defs: set[str] | None = None,
) -> None:
    for name in names:
        if skip_self_defs and name in skip_self_defs:
            continue
        for dst in name_to_defs.get(name, []):
            if dst == src_id:
                continue
            edges[(src_id, dst)] = max(edges.get((src_id, dst), 0.0), weight)
            edges[(dst, src_id)] = max(edges.get((dst, src_id), 0.0), weight * _BACKWARD_WEIGHT_FACTOR)


def _build_python_semantic_edges(fragments: list[Fragment]) -> dict[tuple[FragmentId, FragmentId], float]:
    py_frags = [f for f in fragments if f.path.suffix.lower() == ".py"]
    if not py_frags:
        return {}

    info_cache: dict[FragmentId, PyFragmentInfo] = {}
    for f in py_frags:
        info_cache[f.id] = analyze_python_fragment(f.content)

    name_to_defs: dict[str, list[FragmentId]] = defaultdict(list)
    frag_defines: dict[FragmentId, frozenset[str]] = {}

    for f in py_frags:
        info = info_cache[f.id]
        frag_defines[f.id] = info.defines
        for name in info.defines:
            name_to_defs[name].append(f.id)

    edges: dict[tuple[FragmentId, FragmentId], float] = {}

    for f in py_frags:
        info = info_cache[f.id]
        self_defs = set(frag_defines.get(f.id, frozenset()))

        _add_ref_edges(edges, f.id, set(filter_idents(info.calls, min_len=3)), name_to_defs, _CALL_WEIGHT)
        _add_ref_edges(edges, f.id, set(filter_idents(info.references, min_len=3)), name_to_defs, _SYMBOL_REF_WEIGHT, self_defs)
        _add_ref_edges(edges, f.id, set(filter_idents(info.type_refs, min_len=3)), name_to_defs, _TYPE_REF_WEIGHT, self_defs)

    return edges


def _build_containment_edges(fragments: list[Fragment]) -> dict[tuple[FragmentId, FragmentId], float]:
    by_path: dict[Path, list[Fragment]] = defaultdict(list)
    for f in fragments:
        by_path[f.path].append(f)

    edges: dict[tuple[FragmentId, FragmentId], float] = {}

    for _path, frags in by_path.items():
        if len(frags) < 2:
            continue

        frags_sorted = sorted(frags, key=lambda x: (x.start_line, -x.end_line))
        stack: list[Fragment] = []

        for f in frags_sorted:
            while stack and f.start_line > stack[-1].end_line:
                stack.pop()

            if stack:
                parent = stack[-1]
                if parent.start_line <= f.start_line and f.end_line <= parent.end_line and parent.id != f.id:
                    edges[(f.id, parent.id)] = max(edges.get((f.id, parent.id), 0.0), _CONTAINMENT_WEIGHT)
                    edges[(parent.id, f.id)] = max(edges.get((parent.id, f.id), 0.0), _CONTAINMENT_REVERSE_WEIGHT)

            stack.append(f)

    return edges


def _build_import_edges(fragments: list[Fragment]) -> dict[tuple[FragmentId, FragmentId], float]:
    if not fragments:
        return {}

    module_to_frags: dict[str, list[FragmentId]] = defaultdict(list)
    frag_to_path: dict[FragmentId, Path] = {}

    for frag in fragments:
        frag_to_path[frag.id] = frag.path
        module_name = _path_to_module_name(frag.path)
        if module_name:
            module_to_frags[module_name].append(frag.id)
            parts = module_name.split(".")
            for i in range(1, len(parts)):
                partial = ".".join(parts[:i])
                module_to_frags[partial].append(frag.id)

    edges: dict[tuple[FragmentId, FragmentId], float] = {}

    for frag in fragments:
        for match in _IMPORT_RE.finditer(frag.content):
            imported = match.group(1) or match.group(2)
            if not imported:
                continue

            target_frags = _resolve_import(imported, module_to_frags, frag.path)
            for target_id in target_frags:
                if target_id != frag.id:
                    edges[(frag.id, target_id)] = _IMPORT_WEIGHT
                    edges[(target_id, frag.id)] = _IMPORT_REVERSE_WEIGHT

    return edges


def _path_to_module_name(path: Path) -> str:
    parts = list(path.parts)

    for i, part in enumerate(parts):
        if part in ("src", "lib", "packages"):
            parts = parts[i + 1 :]
            break

    if parts and parts[-1].endswith(".py"):
        parts[-1] = parts[-1][:-3]
        if parts[-1] == "__init__":
            parts = parts[:-1]

    return ".".join(parts) if parts else ""


def _resolve_relative_import(imported: str, source_path: Path, module_to_frags: dict[str, list[FragmentId]]) -> list[FragmentId]:
    base_module = _path_to_module_name(source_path.parent)
    if not base_module:
        return []

    dots = len(imported) - len(imported.lstrip("."))
    relative_part = imported[dots:]
    parts = base_module.split(".")

    if dots > len(parts):
        return []

    resolved = ".".join(parts[:-dots]) if dots > 0 else base_module
    if relative_part:
        resolved = f"{resolved}.{relative_part}" if resolved else relative_part

    return module_to_frags.get(resolved, [])


def _resolve_partial_import(imported: str, module_to_frags: dict[str, list[FragmentId]]) -> list[FragmentId]:
    parts = imported.split(".")
    for i in range(len(parts), 0, -1):
        partial = ".".join(parts[:i])
        if partial in module_to_frags:
            return module_to_frags[partial]
    return []


def _fuzzy_match_module(imported: str, module_to_frags: dict[str, list[FragmentId]]) -> list[FragmentId]:
    base_name = imported.split(".")[-1]
    matches: list[FragmentId] = []
    for module_name, frags in module_to_frags.items():
        if module_name.endswith(base_name) or module_name.endswith(f".{base_name}"):
            matches.extend(frags)
    return matches


def _resolve_import(
    imported: str,
    module_to_frags: dict[str, list[FragmentId]],
    source_path: Path | None = None,
) -> list[FragmentId]:
    if imported.startswith(".") and source_path:
        result = _resolve_relative_import(imported, source_path, module_to_frags)
        if result:
            return result

    if imported in module_to_frags:
        return module_to_frags[imported]

    result = _resolve_partial_import(imported, module_to_frags)
    if result:
        return result

    return _fuzzy_match_module(imported, module_to_frags)


def _is_python_test(name: str) -> bool:
    return name.startswith("test_") or name.endswith("_test.py")


def _is_js_test(name: str, path_str: str) -> bool:
    return ".test." in name or ".spec." in name or "__tests__" in path_str


def _is_rust_test(name: str, path_str: str) -> bool:
    return "/tests/" in path_str or name == "tests.rs"


def _is_jvm_test(name: str) -> bool:
    stem = name.rsplit(".", 1)[0] if "." in name else name
    return stem.endswith("test") or stem.startswith("test")


# Test detection by extension. Python/Java/Kotlin use filename patterns only,
# while JS/TS/Rust also check directory structure (__tests__, /tests/).
_TEST_DETECTORS: dict[str, Callable[[str, str], bool]] = {
    ".py": lambda name, _path_str: _is_python_test(name),
    ".js": _is_js_test,
    ".ts": _is_js_test,
    ".jsx": _is_js_test,
    ".tsx": _is_js_test,
    ".rs": _is_rust_test,
    _JAVA_EXT: lambda name, _path_str: _is_jvm_test(name),
    ".kt": lambda name, _path_str: _is_jvm_test(name),
    ".kts": lambda name, _path_str: _is_jvm_test(name),
    _SCALA_EXT: lambda name, _path_str: _is_jvm_test(name),
}


def _is_test_file(path: Path) -> bool:
    name = path.name.lower()
    path_str = str(path).lower()
    suffix = path.suffix.lower()

    detector = _TEST_DETECTORS.get(suffix)
    if detector is not None and detector(name, path_str):
        return True

    return "/tests/" in path_str or "/test/" in path_str


def _has_direct_import(test_frag: Fragment, src_frag: Fragment) -> bool:
    src_module = _path_to_module_name(src_frag.path)
    if not src_module:
        return False
    for match in _IMPORT_RE.finditer(test_frag.content):
        imported = match.group(1) or match.group(2)
        if imported and (imported == src_module or imported.endswith(f".{src_module}")):
            return True
    return False


def _build_test_edges(fragments: list[Fragment]) -> dict[tuple[FragmentId, FragmentId], float]:
    edges: dict[tuple[FragmentId, FragmentId], float] = {}

    by_base: dict[str, list[Fragment]] = defaultdict(list)
    test_frags: list[Fragment] = []

    for f in fragments:
        if _is_test_file(f.path):
            test_frags.append(f)
        else:
            by_base[f.path.stem.lower()].append(f)

    for test_frag in test_frags:
        test_name = test_frag.path.stem.lower()

        # Extract target name based on naming conventions
        target_name = None
        if test_name.startswith("test_"):
            target_name = test_name[5:]
        elif test_name.endswith("_test"):
            target_name = test_name[:-5]
        elif ".test" in test_name:
            target_name = test_name.split(".test")[0]
        elif ".spec" in test_name:
            target_name = test_name.split(".spec")[0]

        if not target_name:
            continue

        for src_frag in by_base.get(target_name, []):
            # Higher weight if test has direct import
            if _has_direct_import(test_frag, src_frag):
                weight = _TEST_WEIGHT_DIRECT
            else:
                weight = _TEST_WEIGHT_NAMING
            edges[(test_frag.id, src_frag.id)] = weight
            edges[(src_frag.id, test_frag.id)] = _TEST_REVERSE_WEIGHT

    return edges


def _build_document_structure_edges(fragments: list[Fragment]) -> dict[tuple[FragmentId, FragmentId], float]:
    edges: dict[tuple[FragmentId, FragmentId], float] = {}

    by_path: dict[Path, list[Fragment]] = defaultdict(list)
    for f in fragments:
        if f.kind in ("section", "paragraph"):
            by_path[f.path].append(f)

    for _path, frags in by_path.items():
        frags_sorted = sorted(frags, key=lambda x: x.start_line)

        for i in range(len(frags_sorted) - 1):
            curr, next_f = frags_sorted[i], frags_sorted[i + 1]
            edges[(curr.id, next_f.id)] = _DOC_STRUCTURE_WEIGHT
            edges[(next_f.id, curr.id)] = _DOC_STRUCTURE_REVERSE_WEIGHT

    return edges


def _build_anchor_link_edges(fragments: list[Fragment]) -> dict[tuple[FragmentId, FragmentId], float]:
    edges: dict[tuple[FragmentId, FragmentId], float] = {}

    anchor_index: dict[str, FragmentId] = {}
    for f in fragments:
        if f.kind == "section":
            first_line = f.content.split("\n")[0]
            heading = re.sub(r"^#+\s*", "", first_line).strip()
            slug = _slugify(heading)
            if slug:
                anchor_index[slug] = f.id

    for f in fragments:
        for match in _MD_INTERNAL_LINK_RE.finditer(f.content):
            target_slug = _slugify(match.group(2))
            if target_slug in anchor_index:
                target_id = anchor_index[target_slug]
                if target_id != f.id:
                    edges[(f.id, target_id)] = _ANCHOR_LINK_WEIGHT
                    edges[(target_id, f.id)] = _ANCHOR_LINK_REVERSE_WEIGHT

    return edges


def _build_citation_edges_sparse(fragments: list[Fragment]) -> dict[tuple[FragmentId, FragmentId], float]:
    citation_to_frags: dict[str, list[FragmentId]] = defaultdict(list)

    for f in fragments:
        for cit in _CITATION_RE.findall(f.content):
            citation_to_frags[cit].append(f.id)

    edges: dict[tuple[FragmentId, FragmentId], float] = {}

    for _cit, frag_ids in citation_to_frags.items():
        if len(frag_ids) < 2:
            continue
        hub = frag_ids[0]
        for other in frag_ids[1:]:
            edges[(hub, other)] = _CITATION_WEIGHT
            edges[(other, hub)] = _CITATION_WEIGHT

    return edges


def _apply_hub_suppression(
    edges: dict[tuple[FragmentId, FragmentId], float],
) -> dict[tuple[FragmentId, FragmentId], float]:
    if not edges:
        return edges

    in_degree: dict[FragmentId, int] = defaultdict(int)
    for src, dst in edges.keys():
        in_degree[dst] += 1

    if not in_degree:
        return edges

    sorted_degrees = sorted(in_degree.values())
    threshold_idx = int(len(sorted_degrees) * _HUB_PERCENTILE)
    threshold = sorted_degrees[min(threshold_idx, len(sorted_degrees) - 1)]

    suppressed: dict[tuple[FragmentId, FragmentId], float] = {}
    for (src, dst), weight in edges.items():
        if in_degree[dst] > threshold:
            weight = weight / math.log(1 + in_degree[dst])
        suppressed[(src, dst)] = weight

    return suppressed


def _clamp_lexical_weight(raw_sim: float, src_path: Path | None = None, dst_path: Path | None = None) -> float:
    if src_path and dst_path:
        src_weights = _get_lang_weights(src_path)
        dst_weights = _get_lang_weights(dst_path)
        lex_max = max(src_weights.lexical_max, dst_weights.lexical_max)
        lex_min = max(src_weights.lexical_min, dst_weights.lexical_min)
    else:
        lex_max = _LEXICAL_WEIGHT_MAX
        lex_min = _LEXICAL_WEIGHT_MIN

    if raw_sim < _MIN_SIMILARITY:
        return 0.0
    normalized = (raw_sim - _MIN_SIMILARITY) / (1.0 - _MIN_SIMILARITY)
    return lex_min + normalized * (lex_max - lex_min)


def _compute_doc_frequencies(fragments: list[Fragment]) -> dict[str, int]:
    doc_freq: dict[str, int] = defaultdict(int)
    for frag in fragments:
        seen_in_doc: set[str] = set()
        profile = TokenProfile.from_path(str(frag.path))
        idents = filter_idents(extract_identifier_list(frag.content, profile=profile), min_len=3, profile=profile)
        for ident in idents:
            if ident not in seen_in_doc:
                doc_freq[ident] += 1
                seen_in_doc.add(ident)
    return doc_freq


def _compute_idf_scores(doc_freq: dict[str, int], n_docs: int) -> dict[str, float]:
    return {term: math.log((n_docs + 1) / (df + 1)) + 1 for term, df in doc_freq.items()}


def _build_tf_idf_vector(frag: Fragment, doc_freq: dict[str, int], idf: dict[str, float], max_df: int) -> dict[str, float]:
    tf: dict[str, int] = defaultdict(int)
    profile = TokenProfile.from_path(str(frag.path))
    idents = filter_idents(extract_identifier_list(frag.content, profile=profile), min_len=3, profile=profile)
    for ident in idents:
        tf[ident] += 1

    vec: dict[str, float] = {}
    for term, count in tf.items():
        df = doc_freq.get(term, 0)
        if df <= 0 or df > max_df:
            continue
        term_idf = idf.get(term, 1.0)
        if term_idf < _MIN_IDF:
            continue
        vec[term] = count * term_idf

    norm = math.sqrt(sum(v * v for v in vec.values())) if vec else 0.0
    if norm > 0:
        for term in vec:
            vec[term] /= norm

    return vec


def _build_postings_index(tf_idf_vectors: dict[FragmentId, dict[str, float]]) -> dict[str, list[tuple[FragmentId, float]]]:
    postings: dict[str, list[tuple[FragmentId, float]]] = defaultdict(list)
    for frag_id, vec in tf_idf_vectors.items():
        for term, weight in vec.items():
            postings[term].append((frag_id, weight))
    return postings


def _compute_dot_products(postings: dict[str, list[tuple[FragmentId, float]]]) -> dict[tuple[FragmentId, FragmentId], float]:
    dot_products: dict[tuple[FragmentId, FragmentId], float] = defaultdict(float)

    for term, posting_list in postings.items():
        if len(posting_list) > _MAX_POSTINGS:
            continue
        for i, (frag_i, weight_i) in enumerate(posting_list):
            for frag_j, weight_j in posting_list[i + 1 :]:
                pair = (frag_i, frag_j) if str(frag_i) < str(frag_j) else (frag_j, frag_i)
                dot_products[pair] += weight_i * weight_j

    return dot_products


def _collect_neighbors(
    dot_products: dict[tuple[FragmentId, FragmentId], float], id_to_path: dict[FragmentId, Path]
) -> dict[FragmentId, list[tuple[float, FragmentId]]]:
    neighbors_by_node: dict[FragmentId, list[tuple[float, FragmentId]]] = defaultdict(list)

    for (src, dst), sim in dot_products.items():
        if sim < _MIN_SIMILARITY:
            continue
        src_path = id_to_path.get(src)
        dst_path = id_to_path.get(dst)
        clamped_forward = _clamp_lexical_weight(sim, src_path, dst_path)
        clamped_backward = _clamp_lexical_weight(sim, dst_path, src_path) * _BACKWARD_WEIGHT_FACTOR
        neighbors_by_node[src].append((clamped_forward, dst))
        neighbors_by_node[dst].append((clamped_backward, src))

    return neighbors_by_node


def _build_lexical_edges_sparse(fragments: list[Fragment]) -> dict[tuple[FragmentId, FragmentId], float]:
    if not fragments:
        return {}

    doc_freq = _compute_doc_frequencies(fragments)
    n_docs = len(fragments)
    max_df = max(1, int(n_docs * _MAX_DF_RATIO))
    idf = _compute_idf_scores(doc_freq, n_docs)

    tf_idf_vectors = {frag.id: _build_tf_idf_vector(frag, doc_freq, idf, max_df) for frag in fragments}
    postings = _build_postings_index(tf_idf_vectors)
    dot_products = _compute_dot_products(postings)

    id_to_path = {frag.id: frag.path for frag in fragments}
    neighbors_by_node = _collect_neighbors(dot_products, id_to_path)

    edges: dict[tuple[FragmentId, FragmentId], float] = {}
    for node, candidates in neighbors_by_node.items():
        top_k = nlargest(_TOP_K_NEIGHBORS, candidates, key=lambda x: x[0])
        for weight, neighbor in top_k:
            edges[(node, neighbor)] = weight

    return edges


_JSON_KEY_RE = re.compile(r'"([a-zA-Z_][a-zA-Z0-9_-]*)"\s*:')
_INI_KEY_RE = re.compile(r"^\s*([a-zA-Z_][a-zA-Z0-9_-]*)\s*=", re.MULTILINE)
_ENV_KEY_RE = re.compile(r"^([A-Za-z_]\w*)\s*=", re.MULTILINE)

_CONFIG_EXTS = {".yaml", ".yml", ".json", ".toml", ".ini", ".env"}
_CODE_EXTS = {".py", ".js", ".ts", ".tsx", ".jsx", ".rs", ".go"} | _JVM_EXTENSIONS

_CONFIG_KEY_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    ".yaml": [_CONFIG_KEY_RE],
    ".yml": [_CONFIG_KEY_RE],
    ".json": [_JSON_KEY_RE],
    ".toml": [_TOML_KEY_RE, _TOML_SECTION_RE],
    ".ini": [_INI_KEY_RE],
    ".env": [_ENV_KEY_RE],
}


def _extract_config_keys(suffix: str, content: str) -> set[str]:
    patterns = _CONFIG_KEY_PATTERNS.get(suffix, [])
    keys: set[str] = set()
    for pattern in patterns:
        for match in pattern.finditer(content):
            keys.add(match.group(1).lower())
    return keys


def _build_config_code_edges(fragments: list[Fragment]) -> dict[tuple[FragmentId, FragmentId], float]:
    config_frags = [f for f in fragments if f.path.suffix.lower() in _CONFIG_EXTS]
    code_frags = [f for f in fragments if f.path.suffix.lower() in _CODE_EXTS]

    if not config_frags or not code_frags:
        return {}

    config_keys_by_frag = {cfg.id: _extract_config_keys(cfg.path.suffix.lower(), cfg.content) for cfg in config_frags}

    all_keys = {k for keys in config_keys_by_frag.values() for k in keys}
    key_patterns = {key: re.compile(rf"\b{re.escape(key)}\b", re.IGNORECASE) for key in all_keys}

    key_to_code_frags: dict[str, list[FragmentId]] = defaultdict(list)
    for code_frag in code_frags:
        for cfg_id, keys in config_keys_by_frag.items():
            for key in keys:
                if key_patterns[key].search(code_frag.content):
                    key_to_code_frags[key].append(code_frag.id)

    edges: dict[tuple[FragmentId, FragmentId], float] = {}
    for cfg in config_frags:
        for key in config_keys_by_frag.get(cfg.id, set()):
            matching = key_to_code_frags.get(key, [])
            if not matching:
                continue
            adjusted_weight = _CONFIG_CODE_WEIGHT * min(1.0, 3.0 / len(matching))
            for code_id in matching:
                edges[(cfg.id, code_id)] = max(edges.get((cfg.id, code_id), 0.0), adjusted_weight)
                edges[(code_id, cfg.id)] = max(edges.get((code_id, cfg.id), 0.0), adjusted_weight * _BACKWARD_WEIGHT_FACTOR)

    return edges


def _build_package_sibling_edges(fragments: list[Fragment]) -> dict[tuple[FragmentId, FragmentId], float]:
    edges: dict[tuple[FragmentId, FragmentId], float] = {}

    by_dir: dict[Path, list[Fragment]] = defaultdict(list)
    for f in fragments:
        by_dir[f.path.parent].append(f)

    for dir_path, frags in by_dir.items():
        if len(frags) < 2:
            continue
        for i, f1 in enumerate(frags):
            for f2 in frags[i + 1 :]:
                edges[(f1.id, f2.id)] = _SIBLING_WEIGHT
                edges[(f2.id, f1.id)] = _SIBLING_WEIGHT

    return edges
