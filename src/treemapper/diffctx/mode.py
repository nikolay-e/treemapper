from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ScoringMode(Enum):
    AUTO = "auto"
    PRECISE = "precise"
    DISCOVER = "discover"


@dataclass(frozen=True)
class PipelineConfig:
    discovery: str
    scoring: str
    low_relevance: bool
    bm25_top_k: int
    ego_depth: int
    ppr_alpha: float

    @staticmethod
    def from_mode(mode: ScoringMode, n_fragments: int = 0) -> PipelineConfig:
        if mode == ScoringMode.PRECISE:
            return PipelineConfig(
                discovery="default",
                scoring="ppr",
                low_relevance=True,
                bm25_top_k=0,
                ego_depth=1,
                ppr_alpha=0.60,
            )
        if mode == ScoringMode.DISCOVER:
            return PipelineConfig(
                discovery="ensemble",
                scoring="ego",
                low_relevance=False,
                bm25_top_k=1,
                ego_depth=2,
                ppr_alpha=0.60,
            )
        is_large = n_fragments > 300
        return PipelineConfig(
            discovery="ensemble" if is_large else "default",
            scoring="ego" if is_large else "ppr",
            low_relevance=not is_large,
            bm25_top_k=1 if is_large else 0,
            ego_depth=2 if is_large else 1,
            ppr_alpha=0.60,
        )
