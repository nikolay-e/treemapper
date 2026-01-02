from __future__ import annotations

import logging
import statistics
from dataclasses import dataclass

from .types import Fragment, FragmentId
from .utility import UtilityState, apply_fragment, compute_density, marginal_gain, utility_value

_BASELINE_K = 5


@dataclass
class SelectionResult:
    selected: list[Fragment]
    reason: str
    used_tokens: int
    utility: float


def _log_and_return(result: SelectionResult, core_ids: set[FragmentId]) -> SelectionResult:
    core_count = sum(1 for f in result.selected if f.id in core_ids)
    logging.debug(  # nosemgrep: python-logger-credential-disclosure
        "Selection: frags=%d core=%d tokens=%d reason=%s utility=%.4f",
        len(result.selected),
        core_count,
        result.used_tokens,
        result.reason,
        result.utility,
    )
    return result


def lazy_greedy_select(
    fragments: list[Fragment],
    core_ids: set[FragmentId],
    rel: dict[FragmentId, float],
    concepts: frozenset[str],
    budget_tokens: int,
    tau: float = 0.08,
) -> SelectionResult:
    if not fragments:
        return _log_and_return(
            SelectionResult(selected=[], reason="no_candidates", used_tokens=0, utility=0.0),
            core_ids,
        )

    state = UtilityState()
    selected: list[Fragment] = []
    remaining_budget = budget_tokens

    core_fragments = [f for f in fragments if f.id in core_ids]
    core_fragments.sort(key=lambda f: (f.token_count if f.token_count > 0 else 10**9, f.line_count, f.start_line))
    non_core_fragments = [f for f in fragments if f.id not in core_ids]

    selected_ids: set[FragmentId] = set()
    skipped_core_fragments: list[Fragment] = []

    for frag in core_fragments:
        if frag.token_count <= remaining_budget:
            if not _is_subset_of_selected(frag, selected_ids):
                selected.append(frag)
                selected_ids.add(frag.id)
                remaining_budget -= frag.token_count
                apply_fragment(frag, rel.get(frag.id, 0.0), concepts, state)
        else:
            skipped_core_fragments.append(frag)

    if skipped_core_fragments:
        skipped_tokens = sum(f.token_count for f in skipped_core_fragments)
        logging.warning(
            "Core fragments (%d tokens) exceed budget. %d core fragments skipped.",
            skipped_tokens,
            len(skipped_core_fragments),
        )

    if remaining_budget <= 0:
        used = budget_tokens - remaining_budget
        return _log_and_return(
            SelectionResult(selected=selected, reason="budget_exhausted", used_tokens=used, utility=utility_value(state)),
            core_ids,
        )

    base_state = state.copy()
    base_selected = list(selected)
    base_budget = remaining_budget

    candidates = [f for f in non_core_fragments if not _overlaps_with_selected(f, selected_ids)]

    upper_bounds: dict[FragmentId, float] = {}
    for frag in candidates:
        if frag.token_count > 0:
            upper_bounds[frag.id] = compute_density(frag, rel.get(frag.id, 0.0), concepts, state)
        else:
            upper_bounds[frag.id] = 0.0

    baseline_densities: list[float] = []
    threshold = 0.0
    selections_for_baseline = 0

    while candidates and remaining_budget > 0:
        candidates.sort(key=lambda f: upper_bounds.get(f.id, 0.0), reverse=True)

        best_frag = None
        best_density = 0.0

        i = 0
        while i < len(candidates):
            frag = candidates[i]

            if frag.token_count > remaining_budget:
                candidates.pop(i)
                continue

            if _overlaps_with_selected(frag, selected_ids):
                candidates.pop(i)
                continue

            actual_gain = marginal_gain(frag, rel.get(frag.id, 0.0), concepts, state)
            actual_density = actual_gain / frag.token_count if frag.token_count > 0 else 0.0

            upper_bounds[frag.id] = actual_density

            if actual_density > best_density:
                best_frag = frag
                best_density = actual_density

            if i + 1 < len(candidates) and actual_density >= upper_bounds.get(candidates[i + 1].id, 0.0):
                break

            i += 1

        if best_frag is None:
            break

        if best_density <= 0:
            break

        if selections_for_baseline < _BASELINE_K:
            baseline_densities.append(best_density)
            selections_for_baseline += 1
            if selections_for_baseline == _BASELINE_K and baseline_densities:
                median_density = statistics.median(baseline_densities)
                threshold = tau * median_density

        if selections_for_baseline >= _BASELINE_K and best_density < threshold:
            break

        selected.append(best_frag)
        selected_ids.add(best_frag.id)
        remaining_budget -= best_frag.token_count
        apply_fragment(best_frag, rel.get(best_frag.id, 0.0), concepts, state)

        candidates = [f for f in candidates if f.id != best_frag.id]
        candidates = [f for f in candidates if not _overlaps_with_selected(f, selected_ids)]

    greedy_utility = utility_value(state)

    best_singleton = None
    best_singleton_gain = 0.0
    base_selected_ids = {f.id for f in base_selected}

    for f in non_core_fragments:
        if f.token_count > base_budget:
            continue
        if _overlaps_with_selected(f, base_selected_ids):
            continue
        gain = marginal_gain(f, rel.get(f.id, 0.0), concepts, base_state)
        if gain > best_singleton_gain:
            best_singleton_gain = gain
            best_singleton = f

    if best_singleton is not None:
        singleton_utility = utility_value(base_state) + best_singleton_gain
        if singleton_utility > greedy_utility:
            used = budget_tokens - (base_budget - best_singleton.token_count)
            return _log_and_return(
                SelectionResult(
                    selected=[*base_selected, best_singleton],
                    reason="best_singleton",
                    used_tokens=used,
                    utility=singleton_utility,
                ),
                core_ids,
            )

    used = budget_tokens - remaining_budget

    if remaining_budget <= 0:
        return _log_and_return(
            SelectionResult(selected=selected, reason="budget_exhausted", used_tokens=used, utility=greedy_utility),
            core_ids,
        )

    if greedy_utility <= 0:
        return _log_and_return(
            SelectionResult(selected=selected, reason="no_utility", used_tokens=used, utility=greedy_utility),
            core_ids,
        )

    if not selected or len(selected) == len(base_selected):
        if skipped_core_fragments:
            return _log_and_return(
                SelectionResult(selected=selected, reason="budget_exhausted", used_tokens=used, utility=greedy_utility),
                core_ids,
            )
        return _log_and_return(
            SelectionResult(selected=selected, reason="no_candidates", used_tokens=used, utility=greedy_utility),
            core_ids,
        )

    if selections_for_baseline >= _BASELINE_K and threshold > 0 and candidates:
        return _log_and_return(
            SelectionResult(selected=selected, reason="stopped_by_tau", used_tokens=used, utility=greedy_utility),
            core_ids,
        )

    return _log_and_return(
        SelectionResult(selected=selected, reason="no_candidates", used_tokens=used, utility=greedy_utility),
        core_ids,
    )


def _overlaps_with_selected(frag: Fragment, selected_ids: set[FragmentId]) -> bool:
    for sel_id in selected_ids:
        if sel_id.path != frag.path:
            continue
        if sel_id == frag.id:
            continue
        if frag.start_line <= sel_id.start_line and sel_id.end_line <= frag.end_line:
            return True
        if sel_id.start_line <= frag.start_line and frag.end_line <= sel_id.end_line:
            return True
    return False


def _is_subset_of_selected(frag: Fragment, selected_ids: set[FragmentId]) -> bool:
    for sel_id in selected_ids:
        if sel_id.path != frag.path:
            continue
        if sel_id == frag.id:
            continue
        if sel_id.start_line <= frag.start_line and frag.end_line <= sel_id.end_line:
            return True
    return False
