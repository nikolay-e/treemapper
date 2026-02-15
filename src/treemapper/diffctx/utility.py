from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .stopwords import CODE_STOPWORDS
from .tokenizer import extract_tokens
from .types import Fragment, FragmentId

if TYPE_CHECKING:
    from .graph import Graph

_CONCEPT_RE = re.compile(r"[A-Za-z_]\w*")
_CALL_RE = re.compile(r"(\w+)\s*\(")
_TYPE_REF_RE = re.compile(r"(?::\s*|->)\s*([A-Z]\w+)")
_CLOSURE_MIN_EDGE_WEIGHT = 0.5

_MATCH_DEFINE = 1.0
_MATCH_USE = 0.5


def _match_strength(frag: Fragment, concept: str) -> float:
    if frag.symbol_name and frag.symbol_name.lower() == concept:
        return _MATCH_DEFINE
    if concept in frag.identifiers:
        return _MATCH_USE
    return 0.0


def _extract_changed_lines(diff_text: str) -> list[str]:
    result: list[str] = []
    for line in diff_text.splitlines():
        is_added = line.startswith("+") and not line.startswith("+++")
        is_removed = line.startswith("-") and not line.startswith("---")
        if is_added or is_removed:
            result.append(line[1:])
    return result


def concepts_from_diff_text(diff_text: str, profile: str = "code", *, use_nlp: bool = False) -> frozenset[str]:
    text = "\n".join(_extract_changed_lines(diff_text))

    if use_nlp and profile != "code":
        return extract_tokens(text, profile=profile, use_nlp=True)

    raw = _CONCEPT_RE.findall(text)
    return frozenset(ident.lower() for ident in raw if len(ident) >= 3 and ident.lower() not in CODE_STOPWORDS)


def _build_sigma(
    all_fragments: list[Fragment],
    core_ids: set[FragmentId],
    diff_text: str,
) -> set[str]:
    sigma: set[str] = set()

    for frag in all_fragments:
        if frag.id in core_ids and frag.symbol_name:
            sigma.add(frag.symbol_name.lower())

    for line in _extract_changed_lines(diff_text):
        for m in _CALL_RE.finditer(line):
            name = m.group(1)
            if len(name) >= 3 and name.lower() not in CODE_STOPWORDS:
                sigma.add(name.lower())
        for m in _TYPE_REF_RE.finditer(line):
            sigma.add(m.group(1).lower())

    for frag in all_fragments:
        if frag.symbol_name and frag.symbol_name.lower().startswith("test_"):
            tested = frag.symbol_name.lower().removeprefix("test_")
            if tested in sigma:
                sigma.add(frag.symbol_name.lower())

    return sigma


def _apply_closure(
    sigma: set[str],
    all_fragments: list[Fragment],
    graph: Graph,
    closure_depth: int,
) -> set[str]:
    frag_by_symbol: dict[str, list[Fragment]] = {}
    for f in all_fragments:
        if f.symbol_name:
            frag_by_symbol.setdefault(f.symbol_name.lower(), []).append(f)

    frag_by_id: dict[FragmentId, Fragment] = {f.id: f for f in all_fragments}

    closure: set[str] = set(sigma)
    for _ in range(closure_depth):
        new_symbols: set[str] = set()
        for sym in closure:
            for frag in frag_by_symbol.get(sym, []):
                for nbr_id, weight in graph.neighbors(frag.id).items():
                    if weight < _CLOSURE_MIN_EDGE_WEIGHT:
                        continue
                    nbr = frag_by_id.get(nbr_id)
                    if nbr and nbr.symbol_name and nbr.symbol_name.lower() not in closure:
                        new_symbols.add(nbr.symbol_name.lower())
        if not new_symbols:
            break
        closure |= new_symbols

    return closure


def concepts_from_diff(
    all_fragments: list[Fragment],
    core_ids: set[FragmentId],
    graph: Graph,
    diff_text: str,
    closure_depth: int = 1,
) -> frozenset[str]:
    sigma = _build_sigma(all_fragments, core_ids, diff_text)
    closure = _apply_closure(sigma, all_fragments, graph, closure_depth)

    if not closure:
        return concepts_from_diff_text(diff_text)

    return frozenset(closure)


@dataclass
class UtilityState:
    max_rel: dict[str, float] = field(default_factory=dict)

    def copy(self) -> UtilityState:
        return UtilityState(max_rel=dict(self.max_rel))


def _phi(x: float) -> float:
    return math.sqrt(x) if x > 0 else 0.0


def marginal_gain(
    frag: Fragment,
    rel_score: float,
    concepts: frozenset[str],
    state: UtilityState,
) -> float:
    if not concepts:
        emergency = frag.identifiers
        if not emergency:
            return 0.0
        gain = 0.0
        for c in emergency:
            m = _match_strength(frag, c)
            if m <= 0.0:
                continue
            a_fz = rel_score * m
            old_max = state.max_rel.get(c, 0.0)
            new_max = max(old_max, a_fz)
            gain += _phi(new_max) - _phi(old_max)
        return gain

    gain = 0.0
    for c in concepts:
        m = _match_strength(frag, c)
        if m <= 0.0:
            continue
        a_fz = rel_score * m
        old_max = state.max_rel.get(c, 0.0)
        new_max = max(old_max, a_fz)
        gain += _phi(new_max) - _phi(old_max)

    return gain


def apply_fragment(
    frag: Fragment,
    rel_score: float,
    concepts: frozenset[str],
    state: UtilityState,
) -> None:
    effective = concepts if concepts else frag.identifiers
    for c in effective:
        m = _match_strength(frag, c)
        if m <= 0.0:
            continue
        a_fz = rel_score * m
        old_max = state.max_rel.get(c, 0.0)
        state.max_rel[c] = max(old_max, a_fz)


def compute_density(frag: Fragment, rel_score: float, concepts: frozenset[str], state: UtilityState) -> float:
    if frag.token_count <= 0:
        return 0.0
    gain = marginal_gain(frag, rel_score, concepts, state)
    return gain / frag.token_count


def utility_value(state: UtilityState) -> float:
    return sum(_phi(v) for v in state.max_rel.values())
