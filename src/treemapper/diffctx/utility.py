from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

from .stopwords import filter_idents
from .types import Fragment

_CONCEPT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def concepts_from_diff_text(diff_text: str) -> frozenset[str]:
    diff_lines = []
    for line in diff_text.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            diff_lines.append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            diff_lines.append(line[1:])
    text = "\n".join(diff_lines)
    raw = _CONCEPT_RE.findall(text)
    filtered = filter_idents(raw, min_len=3)
    return frozenset(filtered)


@dataclass
class UtilityState:
    max_rel: dict[str, float] = field(default_factory=dict)

    def copy(self) -> UtilityState:
        return UtilityState(max_rel=dict(self.max_rel))


def _phi(x: float) -> float:
    return math.sqrt(x) if x > 0 else 0.0


_MIN_REL_FOR_BONUS = 0.15
_RELATEDNESS_BONUS = 0.08


def marginal_gain(
    frag: Fragment,
    rel_score: float,
    concepts: frozenset[str],
    state: UtilityState,
) -> float:
    # Fallback: if no concepts, use relevance score as proxy
    if not concepts:
        return rel_score * 0.1

    gain = 0.0
    covered = frag.identifiers & concepts

    for c in covered:
        old_max = state.max_rel.get(c, 0.0)
        new_max = max(old_max, rel_score)
        gain += _phi(new_max) - _phi(old_max)

    # Add minimum gain for high-relevance fragments with concept overlap
    # This ensures semantically related fragments are included even when
    # concepts are already covered by core fragments with higher scores
    if covered and rel_score >= _MIN_REL_FOR_BONUS:
        min_gain = rel_score * _RELATEDNESS_BONUS * min(len(covered), 5)
        gain = max(gain, min_gain)

    return gain


def apply_fragment(
    frag: Fragment,
    rel_score: float,
    concepts: frozenset[str],
    state: UtilityState,
) -> None:
    covered = frag.identifiers & concepts

    for c in covered:
        old_max = state.max_rel.get(c, 0.0)
        state.max_rel[c] = max(old_max, rel_score)


def compute_density(frag: Fragment, rel_score: float, concepts: frozenset[str], state: UtilityState) -> float:
    if frag.token_count <= 0:
        return 0.0
    gain = marginal_gain(frag, rel_score, concepts, state)
    return gain / frag.token_count


def utility_value(state: UtilityState) -> float:
    return sum(_phi(v) for v in state.max_rel.values())
