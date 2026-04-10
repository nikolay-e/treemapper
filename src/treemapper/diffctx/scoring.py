from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from .graph import Graph
from .types import DiffHunk, Fragment, FragmentId


@dataclass(frozen=True)
class DiscoveryContext:
    root_dir: Path
    changed_files: list[Path]
    all_candidate_files: list[Path]
    diff_text: str
    expansion_concepts: frozenset[str]


class DiscoveryStrategy(ABC):
    @abstractmethod
    def discover(self, ctx: DiscoveryContext) -> list[Path]: ...


class DefaultDiscovery(DiscoveryStrategy):
    def discover(self, ctx: DiscoveryContext) -> list[Path]:
        from .edges import discover_all_related_files
        from .universe import _expand_universe_by_rare_identifiers

        edge_discovered = discover_all_related_files(ctx.changed_files, ctx.all_candidate_files, ctx.root_dir)

        from ..ignore import get_ignore_specs

        combined_spec = get_ignore_specs(ctx.root_dir, None, False, None)
        expanded = _expand_universe_by_rare_identifiers(
            ctx.root_dir,
            ctx.expansion_concepts,
            ctx.changed_files + edge_discovered,
            combined_spec,
            candidate_files=ctx.all_candidate_files,
        )

        return list(dict.fromkeys(edge_discovered + expanded))


@dataclass
class ScoringResult:
    rel_scores: dict[FragmentId, float]
    filtered_fragments: list[Fragment]
    graph: Graph


class ScoringStrategy(ABC):
    @abstractmethod
    def score_and_filter(
        self,
        all_fragments: list[Fragment],
        core_ids: set[FragmentId],
        hunks: list[DiffHunk],
        repo_root: Path | None = None,
        seed_weights: dict[FragmentId, float] | None = None,
        dump_scores_file: str | None = None,
    ) -> ScoringResult: ...


class PPRScoring(ScoringStrategy):
    def __init__(self, alpha: float = 0.60) -> None:
        self.alpha = alpha

    def score_and_filter(
        self,
        all_fragments: list[Fragment],
        core_ids: set[FragmentId],
        hunks: list[DiffHunk],
        repo_root: Path | None = None,
        seed_weights: dict[FragmentId, float] | None = None,
        dump_scores_file: str | None = None,
    ) -> ScoringResult:
        from .filtering import (
            _apply_hunk_proximity_bonus,
            _cap_context_fragments,
            _filter_low_relevance_fragments,
            _filter_unrelated_fragments,
        )
        from .graph import build_graph
        from .ppr import personalized_pagerank

        graph = build_graph(all_fragments, repo_root=repo_root)
        rel_scores = personalized_pagerank(graph, core_ids, alpha=self.alpha, seed_weights=seed_weights)
        _apply_hunk_proximity_bonus(rel_scores, core_ids, all_fragments, hunks)

        if dump_scores_file and repo_root:
            self._dump_scores(
                dump_scores_file,
                all_fragments,
                core_ids,
                rel_scores,
                graph,
                repo_root,
            )

        filtered = _filter_unrelated_fragments(all_fragments, core_ids, graph)
        filtered = _filter_low_relevance_fragments(filtered, core_ids, rel_scores)
        filtered = _cap_context_fragments(filtered, core_ids, rel_scores)

        return ScoringResult(rel_scores=rel_scores, filtered_fragments=filtered, graph=graph)

    def _dump_scores(
        self,
        scores_file: str,
        all_fragments: list[Fragment],
        core_ids: set[FragmentId],
        rel_scores: dict[FragmentId, float],
        graph: Graph,
        repo_root: Path,
    ) -> None:
        import json as _json

        from .filtering import (
            _cap_context_fragments,
            _filter_low_relevance_fragments,
            _filter_unrelated_fragments,
        )

        filtered_fragments = _filter_unrelated_fragments(all_fragments, core_ids, graph)
        post_unrelated_ids = {f.id for f in filtered_fragments}
        filtered_fragments = _filter_low_relevance_fragments(filtered_fragments, core_ids, rel_scores)
        post_lowrel_ids = {f.id for f in filtered_fragments}
        filtered_fragments = _cap_context_fragments(filtered_fragments, core_ids, rel_scores)
        post_cap_ids = {f.id for f in filtered_fragments}

        with open(scores_file, "w") as _sf:
            for f in all_fragments:
                if f.id in core_ids:
                    continue
                try:
                    rel_path = str(f.path.relative_to(repo_root))
                except ValueError:
                    rel_path = str(f.path)
                score = rel_scores.get(f.id, 0.0)
                if f.id not in post_unrelated_ids:
                    reason = "filtered_unrelated"
                elif f.id not in post_lowrel_ids:
                    reason = f"filtered_low_relevance (threshold={0.02 * max(1.0, f.token_count / 100) ** 0.5:.4f})"
                elif f.id not in post_cap_ids:
                    reason = "filtered_cap_per_file"
                else:
                    reason = "candidate_for_greedy"
                _sf.write(
                    _json.dumps(
                        {
                            "path": rel_path,
                            "lines": f"{f.start_line}-{f.end_line}",
                            "kind": f.kind,
                            "ppr_score": round(score, 6),
                            "token_count": f.token_count,
                            "status": reason,
                        }
                    )
                    + "\n"
                )


class EgoGraphScoring(ScoringStrategy):
    def __init__(self, max_depth: int = 2) -> None:
        self.max_depth = max_depth

    def score_and_filter(
        self,
        all_fragments: list[Fragment],
        core_ids: set[FragmentId],
        hunks: list[DiffHunk],
        repo_root: Path | None = None,
        seed_weights: dict[FragmentId, float] | None = None,
        dump_scores_file: str | None = None,
    ) -> ScoringResult:
        from .filtering import _cap_context_fragments
        from .graph import build_graph

        graph = build_graph(all_fragments, repo_root=repo_root)
        rel_scores = graph.ego_graph(core_ids, radius=self.max_depth)

        filtered = [f for f in all_fragments if f.id in core_ids or rel_scores.get(f.id, 0.0) > 0]
        filtered = _cap_context_fragments(filtered, core_ids, rel_scores)

        return ScoringResult(rel_scores=rel_scores, filtered_fragments=filtered, graph=graph)
