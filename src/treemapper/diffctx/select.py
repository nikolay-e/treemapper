from __future__ import annotations

import logging
import statistics
from dataclasses import dataclass, field

from .types import Fragment, FragmentId
from .utility import UtilityState, apply_fragment, compute_density, marginal_gain, utility_value

_BASELINE_K = 5


@dataclass
class SelectionResult:
    selected: list[Fragment]
    reason: str
    used_tokens: int
    utility: float


@dataclass
class _SelectionState:
    selected: list[Fragment] = field(default_factory=list)
    selected_ids: set[FragmentId] = field(default_factory=set)
    remaining_budget: int = 0
    utility_state: UtilityState = field(default_factory=UtilityState)
    skipped_core: list[Fragment] = field(default_factory=list)


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


def _select_core_fragments(
    core_fragments: list[Fragment],
    rel: dict[FragmentId, float],
    concepts: frozenset[str],
    state: _SelectionState,
) -> None:
    for frag in core_fragments:
        if frag.token_count <= state.remaining_budget:
            if not _is_subset_of_selected(frag, state.selected_ids):
                state.selected.append(frag)
                state.selected_ids.add(frag.id)
                state.remaining_budget -= frag.token_count
                apply_fragment(frag, rel.get(frag.id, 0.0), concepts, state.utility_state)
        else:
            state.skipped_core.append(frag)


def _log_skipped_core(skipped: list[Fragment]) -> None:
    if skipped:
        skipped_tokens = sum(f.token_count for f in skipped)
        logging.warning(
            "Core fragments (%d tokens) exceed budget. %d core fragments skipped.",
            skipped_tokens,
            len(skipped),
        )


def _compute_upper_bounds(
    candidates: list[Fragment],
    rel: dict[FragmentId, float],
    concepts: frozenset[str],
    state: UtilityState,
) -> dict[FragmentId, float]:
    upper_bounds: dict[FragmentId, float] = {}
    for frag in candidates:
        if frag.token_count > 0:
            upper_bounds[frag.id] = compute_density(frag, rel.get(frag.id, 0.0), concepts, state)
        else:
            upper_bounds[frag.id] = 0.0
    return upper_bounds


def _find_best_candidate(
    candidates: list[Fragment],
    selected_ids: set[FragmentId],
    remaining_budget: int,
    rel: dict[FragmentId, float],
    concepts: frozenset[str],
    state: UtilityState,
    upper_bounds: dict[FragmentId, float],
) -> tuple[Fragment | None, float, list[Fragment]]:
    best_frag = None
    best_density = 0.0
    filtered: list[Fragment] = []

    for frag in candidates:
        if frag.token_count > remaining_budget:
            continue
        if _overlaps_with_selected(frag, selected_ids):
            continue
        filtered.append(frag)

    filtered.sort(key=lambda f: upper_bounds.get(f.id, 0.0), reverse=True)

    for i, frag in enumerate(filtered):
        actual_gain = marginal_gain(frag, rel.get(frag.id, 0.0), concepts, state)
        actual_density = actual_gain / frag.token_count if frag.token_count > 0 else 0.0
        upper_bounds[frag.id] = actual_density

        if actual_density > best_density:
            best_frag = frag
            best_density = actual_density

        if i + 1 < len(filtered) and actual_density >= upper_bounds.get(filtered[i + 1].id, 0.0):
            break

    return best_frag, best_density, filtered


def _find_best_singleton(
    non_core: list[Fragment],
    base_selected_ids: set[FragmentId],
    base_budget: int,
    rel: dict[FragmentId, float],
    concepts: frozenset[str],
    base_state: UtilityState,
) -> tuple[Fragment | None, float]:
    best_singleton = None
    best_gain = 0.0
    for f in non_core:
        if f.token_count > base_budget:
            continue
        if _overlaps_with_selected(f, base_selected_ids):
            continue
        gain = marginal_gain(f, rel.get(f.id, 0.0), concepts, base_state)
        if gain > best_gain:
            best_gain = gain
            best_singleton = f
    return best_singleton, best_gain


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

    core_fragments = [f for f in fragments if f.id in core_ids]
    core_fragments.sort(key=lambda f: (f.token_count if f.token_count > 0 else 10**9, f.line_count, f.start_line))
    non_core_fragments = [f for f in fragments if f.id not in core_ids]

    state = _SelectionState(remaining_budget=budget_tokens)
    _select_core_fragments(core_fragments, rel, concepts, state)
    _log_skipped_core(state.skipped_core)

    if state.remaining_budget <= 0:
        used = budget_tokens - state.remaining_budget
        return _log_and_return(
            SelectionResult(
                selected=state.selected,
                reason="budget_exhausted",
                used_tokens=used,
                utility=utility_value(state.utility_state),
            ),
            core_ids,
        )

    base_state = state.utility_state.copy()
    base_selected = list(state.selected)
    base_budget = state.remaining_budget

    candidates = [f for f in non_core_fragments if not _overlaps_with_selected(f, state.selected_ids)]
    upper_bounds = _compute_upper_bounds(candidates, rel, concepts, state.utility_state)

    selections_for_baseline, threshold = _run_greedy_loop(candidates, state, rel, concepts, upper_bounds, tau)

    greedy_utility = utility_value(state.utility_state)
    base_selected_ids = {f.id for f in base_selected}

    singleton_result = _try_singleton_improvement(
        non_core_fragments,
        base_selected_ids,
        base_budget,
        base_selected,
        rel,
        concepts,
        base_state,
        greedy_utility,
        budget_tokens,
        core_ids,
    )
    if singleton_result is not None:
        return singleton_result

    return _determine_final_result(
        state, base_selected, budget_tokens, greedy_utility, selections_for_baseline, threshold, candidates, core_ids
    )


def _run_greedy_loop(
    candidates: list[Fragment],
    state: _SelectionState,
    rel: dict[FragmentId, float],
    concepts: frozenset[str],
    upper_bounds: dict[FragmentId, float],
    tau: float,
) -> tuple[int, float]:
    baseline_densities: list[float] = []
    threshold = 0.0
    selections_for_baseline = 0

    while candidates and state.remaining_budget > 0:
        best_frag, best_density, candidates = _find_best_candidate(
            candidates, state.selected_ids, state.remaining_budget, rel, concepts, state.utility_state, upper_bounds
        )

        if best_frag is None or best_density <= 0:
            break

        if selections_for_baseline < _BASELINE_K:
            baseline_densities.append(best_density)
            selections_for_baseline += 1
            if selections_for_baseline == _BASELINE_K and baseline_densities:
                threshold = tau * statistics.median(baseline_densities)

        if selections_for_baseline >= _BASELINE_K and best_density < threshold:
            break

        state.selected.append(best_frag)
        state.selected_ids.add(best_frag.id)
        state.remaining_budget -= best_frag.token_count
        apply_fragment(best_frag, rel.get(best_frag.id, 0.0), concepts, state.utility_state)

        candidates = [f for f in candidates if f.id != best_frag.id]

    return selections_for_baseline, threshold


def _try_singleton_improvement(
    non_core: list[Fragment],
    base_selected_ids: set[FragmentId],
    base_budget: int,
    base_selected: list[Fragment],
    rel: dict[FragmentId, float],
    concepts: frozenset[str],
    base_state: UtilityState,
    greedy_utility: float,
    budget_tokens: int,
    core_ids: set[FragmentId],
) -> SelectionResult | None:
    best_singleton, best_gain = _find_best_singleton(non_core, base_selected_ids, base_budget, rel, concepts, base_state)

    if best_singleton is None:
        return None

    singleton_utility = utility_value(base_state) + best_gain
    if singleton_utility <= greedy_utility:
        return None

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


def _determine_final_result(
    state: _SelectionState,
    base_selected: list[Fragment],
    budget_tokens: int,
    greedy_utility: float,
    selections_for_baseline: int,
    threshold: float,
    candidates: list[Fragment],
    core_ids: set[FragmentId],
) -> SelectionResult:
    used = budget_tokens - state.remaining_budget

    if state.remaining_budget <= 0:
        reason = "budget_exhausted"
    elif greedy_utility <= 0:
        reason = "no_utility"
    elif not state.selected or len(state.selected) == len(base_selected):
        reason = "budget_exhausted" if state.skipped_core else "no_candidates"
    elif selections_for_baseline >= _BASELINE_K and threshold > 0 and candidates:
        reason = "stopped_by_tau"
    else:
        reason = "no_candidates"

    return _log_and_return(
        SelectionResult(selected=state.selected, reason=reason, used_tokens=used, utility=greedy_utility),
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
