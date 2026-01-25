from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AlgorithmLimits:
    max_file_size: int = 100_000
    max_fragments: int = 200
    rare_identifier_threshold: int = 3
    max_expansion_files: int = 20
    overhead_per_fragment: int = 18
    default_budget_tokens: int = 50_000


@dataclass(frozen=True)
class PPRConfig:
    alpha: float = 0.60
    tolerance: float = 1e-4
    max_iterations: int = 50


@dataclass(frozen=True)
class LexicalConfig:
    min_similarity: float = 0.1
    hub_percentile: float = 0.95
    top_k_neighbors: int = 10
    max_df_ratio: float = 0.20
    min_idf: float = 1.6
    max_postings: int = 200
    weight_min: float = 0.1
    weight_max: float = 0.2
    backward_factor: float = 0.7


@dataclass(frozen=True)
class CochangeConfig:
    weight: float = 0.40
    min_count: int = 2
    max_files_per_commit: int = 30
    commits_limit: int = 500
    timeout_seconds: int = 10


@dataclass(frozen=True)
class SiblingConfig:
    max_files_per_dir: int = 20


LIMITS = AlgorithmLimits()
PPR = PPRConfig()
LEXICAL = LexicalConfig()
COCHANGE = CochangeConfig()
SIBLING = SiblingConfig()
