from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from .graph import Graph
from .types import DiffHunk, Fragment, FragmentId


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
    def __init__(self, max_depth: int = 2, decay: float = 0.5) -> None:
        self.max_depth = max_depth
        self.decay = decay

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
        rel_scores = self._ego_graph_bfs(graph, core_ids)

        filtered = [f for f in all_fragments if f.id in core_ids or rel_scores.get(f.id, 0.0) > 0]
        filtered = _cap_context_fragments(filtered, core_ids, rel_scores)

        return ScoringResult(rel_scores=rel_scores, filtered_fragments=filtered, graph=graph)

    def _ego_graph_bfs(self, graph: Graph, core_ids: set[FragmentId]) -> dict[FragmentId, float]:
        scores: dict[FragmentId, float] = {}
        for cid in core_ids:
            scores[cid] = 1.0

        frontier = set(core_ids)
        visited = set(core_ids)

        for depth in range(1, self.max_depth + 1):
            hop_score = self.decay**depth
            next_frontier: set[FragmentId] = set()

            for node in frontier:
                for neighbor, weight in graph.adjacency.get(node, {}).items():
                    if neighbor not in visited:
                        scores[neighbor] = max(scores.get(neighbor, 0.0), hop_score * weight)
                        next_frontier.add(neighbor)
                for neighbor, weight in graph.reverse_adjacency.get(node, {}).items():
                    if neighbor not in visited:
                        scores[neighbor] = max(scores.get(neighbor, 0.0), hop_score * weight)
                        next_frontier.add(neighbor)

            visited |= next_frontier
            frontier = next_frontier
            if not frontier:
                break

        return scores
