from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

from benchmarks.adapters.base import BenchmarkInstance, EvalResult
from benchmarks.adapters.evaluator import UniversalEvaluator
from benchmarks.adapters.runner import EvalFn, RunParams, run_eval_set


@dataclass(frozen=True)
class GridSpec:
    """2D grid: cartesian product of `tau_values` by `core_budget_fraction_values`."""

    tau_values: tuple[float, ...]
    core_budget_fraction_values: tuple[float, ...]
    budget: int = 8000
    scoring: str = "hybrid"

    def __post_init__(self) -> None:
        if not self.tau_values:
            raise ValueError("tau_values must be non-empty")
        if not self.core_budget_fraction_values:
            raise ValueError("core_budget_fraction_values must be non-empty")

    def points(self) -> Iterator[RunParams]:
        for tau in self.tau_values:
            for cbf in self.core_budget_fraction_values:
                yield RunParams(
                    tau=tau,
                    core_budget_fraction=cbf,
                    budget=self.budget,
                    scoring=self.scoring,
                )

    def __len__(self) -> int:
        return len(self.tau_values) * len(self.core_budget_fraction_values)


@dataclass(frozen=True)
class TrialResult:
    params: RunParams
    per_benchmark: dict[str, dict[str, float]]
    """`benchmark_name -> {metric: value}` from `aggregate_per_benchmark`."""

    raw_results: tuple[EvalResult, ...] = field(default_factory=tuple)

    @property
    def score(self) -> float:
        """Generalization-friendly objective: minimum file_recall across
        benchmarks. Defending the worst-performing benchmark prevents one
        large source from dominating the global mean."""
        if not self.per_benchmark:
            return 0.0
        return min(agg.get("file_recall", 0.0) for agg in self.per_benchmark.values())


TrialCallback = Callable[[int, int, "TrialResult"], None]


def evaluate_grid(
    spec: GridSpec,
    instances: list[BenchmarkInstance],
    eval_fn: EvalFn,
    workers: int = 1,
    on_trial: TrialCallback | None = None,
    timeout_per_instance: float = 300.0,
    checkpoint_dir: Path | None = None,
) -> list[TrialResult]:
    """Run every grid point, return per-trial aggregates.

    A single `ProcessPoolExecutor` is held across all cells so workers do
    not pay re-spawn cost between trials — CPU stays saturated through the
    whole sweep instead of dipping for ~30s per cell while 40 workers boot.
    `max_tasks_per_child` recycles workers periodically so per-instance
    memory leaks do not accumulate across the full grid.

    `on_trial(idx, total, trial)` fires after each completed trial — the CLI
    uses it for progress logging without coupling the pure logic to stdout.

    `checkpoint_dir`, when set, gets one JSONL per trial named after
    `params.label()`; restarting the sweep skips instances already recorded
    inside each trial's checkpoint.
    """
    import multiprocessing as mp
    from concurrent.futures import ProcessPoolExecutor

    evaluator = UniversalEvaluator()
    points = list(spec.points())
    out: list[TrialResult] = []

    from concurrent.futures.process import BrokenProcessPool

    def _make_pool() -> ProcessPoolExecutor:
        ctx = mp.get_context("spawn")
        p = ProcessPoolExecutor(max_workers=workers, mp_context=ctx, max_tasks_per_child=50)
        list(p.map(int, range(workers)))  # eager-spawn all workers
        return p

    pool: ProcessPoolExecutor | None = _make_pool() if workers > 1 else None
    try:
        for i, params in enumerate(points):
            ckpt = (checkpoint_dir / f"{params.label()}.jsonl") if checkpoint_dir is not None else None
            while True:
                try:
                    results = run_eval_set(
                        instances,
                        eval_fn,
                        params,
                        workers=workers,
                        timeout_per_instance=timeout_per_instance,
                        resume_from=ckpt,
                        checkpoint_path=ckpt,
                        pool=pool,
                    )
                    break
                except BrokenProcessPool:
                    if pool is not None:
                        try:
                            pool.shutdown(wait=False, cancel_futures=True)
                        except Exception:
                            pass
                    pool = _make_pool() if workers > 1 else None
            agg = evaluator.aggregate_per_benchmark(results)
            trial = TrialResult(params=params, per_benchmark=agg, raw_results=tuple(results))
            out.append(trial)
            if on_trial is not None:
                on_trial(i, len(points), trial)
    finally:
        if pool is not None:
            pool.shutdown(wait=False, cancel_futures=True)
    return out


EvalAllCellsFn = Callable[
    [BenchmarkInstance, list[RunParams]],
    list[tuple[RunParams, EvalResult]],
]


def evaluate_grid_cached(  # noqa: C901 — pool teardown + per-cell demux + retry-on-BPP do not factor cleanly
    spec: GridSpec,
    instances: list[BenchmarkInstance],
    eval_all_cells_fn: EvalAllCellsFn,
    workers: int = 1,
    on_trial: TrialCallback | None = None,
    timeout_per_instance: float = 300.0,
    checkpoint_dir: Path | None = None,
) -> list[TrialResult]:
    """Inverted-loop calibration: outer = instance, inner = grid cells.

    Each ProcessPool task computes the heavy `ScoredState` ONCE per
    instance, then runs all (`tau`, `core_budget_fraction`) cells against
    it cheaply. Cuts wall time by ~12x for a 12-cell grid because the
    expensive parse/fragment/discover/score work is no longer redone per
    cell. State never crosses the pickle boundary — only the resulting
    `EvalResult` list does — so ProcessPool is preserved and per-process
    memory pressure is bounded.

    Per-cell checkpoint files (`<params.label()>.jsonl`) match the
    layout produced by `evaluate_grid` so the existing aggregator,
    `top_k_trials`, and `render_grid_report` work unchanged.
    """
    import multiprocessing as mp
    from concurrent.futures import ProcessPoolExecutor, as_completed
    from concurrent.futures.process import BrokenProcessPool

    from benchmarks.adapters.runner import (
        _load_existing_results,
        append_checkpoint,
        read_checkpoint,
    )

    evaluator = UniversalEvaluator()
    points = list(spec.points())

    ckpts: dict[RunParams, Path | None] = {
        p: (checkpoint_dir / f"{p.label()}.jsonl") if checkpoint_dir is not None else None for p in points
    }
    done_ids: dict[RunParams, set[str]] = {p: read_checkpoint(c) if c is not None else set() for p, c in ckpts.items()}
    results_by_cell: dict[RunParams, list[EvalResult]] = {
        p: (_load_existing_results(c, done_ids[p]) if c is not None else []) for p, c in ckpts.items()
    }

    pending: list[tuple[BenchmarkInstance, list[RunParams]]] = []
    for inst in instances:
        needed = [p for p in points if inst.instance_id not in done_ids[p]]
        if needed:
            pending.append((inst, needed))

    def _make_pool() -> ProcessPoolExecutor:
        ctx = mp.get_context("spawn")
        p = ProcessPoolExecutor(max_workers=workers, mp_context=ctx, max_tasks_per_child=50)
        list(p.map(int, range(workers)))
        return p

    def _record_per_cell(per_cell_results: list[tuple[RunParams, EvalResult]]) -> None:
        for params, result in per_cell_results:
            ckpt = ckpts.get(params)
            if ckpt is not None:
                err = str((result.extra or {}).get("error", ""))
                if "BrokenProcessPool" not in err:
                    append_checkpoint(ckpt, result)
            results_by_cell[params].append(result)

    def _drain(pool: ProcessPoolExecutor) -> None:
        futures: dict = {}
        submit_failed: list[tuple[BenchmarkInstance, list[RunParams]]] = []
        pool_broken = False
        for inst, params_list in pending:
            try:
                futures[pool.submit(eval_all_cells_fn, inst, params_list)] = (inst, params_list)
            except BrokenProcessPool:
                idx = pending.index((inst, params_list))
                submit_failed.extend(pending[idx:])
                pool_broken = True
                break
        outer_deadline = __import__("time").monotonic() + timeout_per_instance * len(points) * max(
            1, (len(pending) + workers - 1) // workers
        )
        completed: set[str] = set()
        try:
            for future in as_completed(
                futures,
                timeout=max(0.0, outer_deadline - __import__("time").monotonic()),
            ):
                inst, params_list = futures[future]
                try:
                    per_cell = future.result(timeout=0)
                except BrokenProcessPool:
                    pool_broken = True
                    per_cell = [(p, _failure_eval(inst, p, "error", "BrokenProcessPool: worker died")) for p in params_list]
                except Exception as e:
                    per_cell = [(p, _failure_eval(inst, p, "error", f"{type(e).__name__}: {e}")) for p in params_list]
                completed.add(inst.instance_id)
                _record_per_cell(per_cell)
        except BrokenProcessPool:
            pool_broken = True
        for inst, params_list in submit_failed:
            _record_per_cell([(p, _failure_eval(inst, p, "error", "BrokenProcessPool: submit failed")) for p in params_list])
        if pool_broken:
            raise BrokenProcessPool("pool degraded mid-grid")

    pool: ProcessPoolExecutor | None = _make_pool() if workers > 1 else None
    try:
        if pending and pool is not None:
            while True:
                try:
                    _drain(pool)
                    break
                except BrokenProcessPool:
                    try:
                        pool.shutdown(wait=False, cancel_futures=True)
                    except Exception:
                        pass
                    pool = _make_pool()
                    # Recompute pending for the rebuild from current
                    # checkpoint state — instances completed since last
                    # rebuild should be skipped.
                    done_ids_now = {p: read_checkpoint(c) if c is not None else set() for p, c in ckpts.items()}
                    pending[:] = [
                        (inst, [p for p in points if inst.instance_id not in done_ids_now[p]])
                        for inst, _ in pending
                        if any(inst.instance_id not in done_ids_now[p] for p in points)
                    ]
        elif pending and pool is None:
            # workers == 1: serial fallback
            for inst, params_list in pending:
                try:
                    per_cell = eval_all_cells_fn(inst, params_list)
                except Exception as e:
                    per_cell = [(p, _failure_eval(inst, p, "error", f"{type(e).__name__}: {e}")) for p in params_list]
                _record_per_cell(per_cell)
    finally:
        if pool is not None:
            pool.shutdown(wait=False, cancel_futures=True)

    out: list[TrialResult] = []
    for i, params in enumerate(points):
        agg = evaluator.aggregate_per_benchmark(results_by_cell[params])
        trial = TrialResult(
            params=params,
            per_benchmark=agg,
            raw_results=tuple(results_by_cell[params]),
        )
        out.append(trial)
        if on_trial is not None:
            on_trial(i, len(points), trial)
    return out


def _failure_eval(
    instance: BenchmarkInstance,
    params: RunParams,
    status: str,
    error: str,
) -> EvalResult:
    r = EvalResult(
        instance_id=instance.instance_id,
        source_benchmark=instance.source_benchmark,
        file_recall=0.0,
        file_precision=0.0,
        budget=params.budget,
    )
    r.extra["status"] = status
    r.extra["error"] = error
    r.extra["language"] = instance.language
    return r


def top_k_trials(trials: Iterable[TrialResult], k: int = 3) -> list[TrialResult]:
    """Pick the k highest-score trials, breaking ties by lower mean tokens."""

    def _key(t: TrialResult) -> tuple[float, float]:
        if t.raw_results:
            avg_tokens = sum(r.used_tokens for r in t.raw_results) / len(t.raw_results)
        else:
            avg_tokens = 0.0
        return (-t.score, avg_tokens)

    return sorted(trials, key=_key)[:k]


def render_grid_report(trials: list[TrialResult]) -> str:
    """Markdown summary: per-trial score + best-cell highlight."""
    if not trials:
        return "# Grid Report\n\n(empty)\n"
    lines: list[str] = ["# Calibration grid report", ""]
    benchmarks = sorted({name for t in trials for name in t.per_benchmark})
    headers = ["tau", "core_budget_fraction", "min_recall", *benchmarks]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join(["---"] * len(headers)) + "|")
    sorted_trials = sorted(trials, key=lambda t: -t.score)
    for t in sorted_trials:
        row = [f"{t.params.tau:.4f}", f"{t.params.core_budget_fraction:.4f}", f"{t.score:.4f}"]
        for name in benchmarks:
            r = t.per_benchmark.get(name, {}).get("file_recall")
            row.append(f"{r:.4f}" if r is not None else "—")
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    best = sorted_trials[0]
    lines.append("## Best cell")
    lines.append("")
    lines.append(f"- τ = {best.params.tau}")
    lines.append(f"- core_budget_fraction = {best.params.core_budget_fraction}")
    lines.append(f"- min(per-benchmark file_recall) = {best.score:.4f}")
    lines.append("")
    return "\n".join(lines)
