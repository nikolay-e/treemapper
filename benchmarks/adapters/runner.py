from __future__ import annotations

import json
import time
from collections.abc import Callable, Iterable, Iterator
from dataclasses import asdict, dataclass, field
from pathlib import Path

from benchmarks.adapters.base import BenchmarkAdapter, BenchmarkInstance, EvalResult

EvalFn = Callable[[BenchmarkInstance, "RunParams"], EvalResult]


def _run_with_kill_switch(
    eval_fn: EvalFn,
    instance: BenchmarkInstance,
    params: RunParams,
    timeout_s: float,
) -> EvalResult:
    """Worker-side hard timeout. A daemon thread arms `os._exit(137)` after
    `timeout_s`; if the Rust pipeline blocks past the deadline (releasing
    the GIL via `py.allow_threads`), this kills the worker process
    unconditionally. The pool detects `BrokenProcessPool` and spawns a
    replacement, so a single pathological instance no longer monopolizes
    a worker slot for hours.
    """
    import os
    import threading

    timer = threading.Timer(timeout_s, lambda: os._exit(137))
    timer.daemon = True
    timer.start()
    try:
        return eval_fn(instance, params)
    finally:
        timer.cancel()


@dataclass(frozen=True)
class RunParams:
    """Parameters for one diffctx evaluation pass.

    `tau` and `core_budget_fraction` are the two calibrated knobs (validated
    by the sensitivity sweep — every other operational parameter showed
    near-zero effect). Anything else can be threaded through `extra_env`.
    """

    tau: float = 0.08
    core_budget_fraction: float = 0.70
    budget: int = 8000
    scoring: str = "hybrid"
    extra_env: dict[str, str] = field(default_factory=dict)

    def to_env(self) -> dict[str, str]:
        env = dict(self.extra_env)
        env["DIFFCTX_OP_SELECTION_STOPPING_THRESHOLD"] = f"{self.tau}"
        env["DIFFCTX_OP_SELECTION_CORE_BUDGET_FRACTION"] = f"{self.core_budget_fraction}"
        return env

    def label(self) -> str:
        return f"tau={self.tau:.4f}_cbf={self.core_budget_fraction:.4f}_b={self.budget}_s={self.scoring}"


def read_manifest(path: Path) -> frozenset[str]:
    """Return the set of `instance_id`s listed in a v1 manifest file."""
    return frozenset(line.strip() for line in path.read_text().splitlines() if line.strip())


def filter_instances_by_manifest(
    adapters: Iterable[BenchmarkAdapter],
    manifest_ids: frozenset[str] | set[str],
) -> Iterator[BenchmarkInstance]:
    """Stream instances whose ID is in `manifest_ids`, across all adapters.

    Adapters are walked once each; missing IDs are silently skipped (the
    caller's report should compare counts and warn).
    """
    wanted = frozenset(manifest_ids)
    for adapter in adapters:
        for inst in adapter.load():
            if inst.instance_id in wanted:
                yield inst


def read_checkpoint(path: Path) -> set[str]:
    """Return instance_ids already recorded in a JSONL checkpoint file."""
    if not path.exists():
        return set()
    done: set[str] = set()
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            done.add(json.loads(line)["instance_id"])
        except (KeyError, ValueError):
            continue
    return done


def append_checkpoint(path: Path, result: EvalResult) -> None:
    """Append one result as a JSONL row. fsync after each write so a
    `os._exit(137)` kill in a sibling worker cannot leave a half-written
    last line that breaks `jq` / line iteration on resume.
    """
    import os as _os

    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(asdict(result), default=str) + "\n"
    with path.open("a") as f:
        f.write(line)
        f.flush()
        _os.fsync(f.fileno())


def _load_existing_results(path: Path, allowed_ids: set[str]) -> list[EvalResult]:
    """Replay a checkpoint into in-memory `EvalResult`s so a fully-resumed
    run still contributes to per-trial aggregation."""
    if not path.exists():
        return []
    out: list[EvalResult] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if row.get("instance_id") not in allowed_ids:
            continue
        out.append(
            EvalResult(
                instance_id=row["instance_id"],
                source_benchmark=row.get("source_benchmark", "unknown"),
                file_recall=float(row.get("file_recall", 0.0)),
                file_precision=float(row.get("file_precision", 0.0)),
                fragment_recall=row.get("fragment_recall"),
                fragment_precision=row.get("fragment_precision"),
                line_f1=row.get("line_f1"),
                used_tokens=int(row.get("used_tokens", 0)),
                budget=int(row.get("budget", 0)),
                elapsed_seconds=float(row.get("elapsed_seconds", 0.0)),
                extra=row.get("extra", {}) or {},
            )
        )
    return out


def _failure_result(
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


def run_eval_set(
    instances: list[BenchmarkInstance],
    eval_fn: EvalFn,
    params: RunParams,
    workers: int = 1,
    timeout_per_instance: float = 20.0,
    resume_from: Path | None = None,
    checkpoint_path: Path | None = None,
    pool: object | None = None,
) -> list[EvalResult]:
    """Run `eval_fn(instance, params)` for every instance.

    - `workers > 1` uses a process pool (spawn context) so workers do
      not share the GIL; otherwise sequential.
    - `timeout_per_instance` is enforced worker-side via a daemon timer
      that calls `os._exit(137)` if the deadline passes — the pool then
      respawns the killed worker. This bounds calibration wall-clock at
      `timeout_per_instance * ceil(n / workers)` even on pathological
      instances (e.g. PPR convergence blow-up on huge graphs).
    - `resume_from` (JSONL path): instance_ids already present in that file
      are skipped — re-running after a crash continues where it left off.
    - `checkpoint_path` (JSONL path): each completed result is appended
      immediately so a crash mid-sweep loses at most one in-flight result.
    """
    done_ids: set[str] = read_checkpoint(resume_from) if resume_from else set()
    pending = [i for i in instances if i.instance_id not in done_ids]
    results: list[EvalResult] = _load_existing_results(resume_from, done_ids) if resume_from else []

    def _record(r: EvalResult) -> None:
        results.append(r)
        if checkpoint_path is None:
            return
        # Pool-level transient failures (BrokenProcessPool) must NOT be
        # persisted: on retry the orchestrator rebuilds the pool and these
        # instances should be re-evaluated, not skipped via the resume set.
        # EXCEPTION: status=="timeout" results — even though the kill switch
        # surfaces them via BrokenProcessPool, they are deterministic per
        # instance (the same input would hit the same deadline again) and
        # MUST be checkpointed to prevent an infinite retry loop on a
        # pathological repository.
        status = (r.extra or {}).get("status", "")
        err = str((r.extra or {}).get("error", ""))
        if status != "timeout" and "BrokenProcessPool" in err:
            return
        append_checkpoint(checkpoint_path, r)

    if pending:
        if workers <= 1 or len(pending) <= 1:
            _run_serial(pending, eval_fn, params, _record)
        else:
            _run_parallel(pending, eval_fn, params, workers, timeout_per_instance, _record, pool=pool)

    return results


def _run_serial(
    pending: list[BenchmarkInstance],
    eval_fn: EvalFn,
    params: RunParams,
    record: Callable[[EvalResult], None],
) -> None:
    for inst in pending:
        try:
            record(eval_fn(inst, params))
        except Exception as e:
            record(_failure_result(inst, params, "error", f"{type(e).__name__}: {e}"))


def _run_parallel(  # noqa: C901 — pool-shape branching + multi-failure-mode drain do not factor cleanly
    pending: list[BenchmarkInstance],
    eval_fn: EvalFn,
    params: RunParams,
    workers: int,
    timeout_per_instance: float,
    record: Callable[[EvalResult], None],
    pool: object | None = None,
) -> None:
    import multiprocessing as mp
    from concurrent.futures import (
        ProcessPoolExecutor,
        as_completed,
    )
    from concurrent.futures import (
        TimeoutError as FuturesTimeoutError,
    )

    def _drain(active_pool: ProcessPoolExecutor) -> None:  # noqa: C901
        from concurrent.futures import CancelledError
        from concurrent.futures.process import BrokenProcessPool

        futures: dict = {}
        submit_times: dict[str, float] = {}
        submit_failed: list[BenchmarkInstance] = []
        pool_broken = False
        for inst in pending:
            try:
                submit_times[inst.instance_id] = time.monotonic()
                futures[active_pool.submit(_run_with_kill_switch, eval_fn, inst, params, timeout_per_instance)] = inst
            except BrokenProcessPool:
                submit_failed.extend([inst, *pending[pending.index(inst) + 1 :]])
                pool_broken = True
                break
        outer_deadline = time.monotonic() + timeout_per_instance * max(1, (len(pending) + workers - 1) // workers)
        completed: set[str] = set()
        try:
            for future in as_completed(futures, timeout=max(0.0, outer_deadline - time.monotonic())):
                inst = futures[future]
                try:
                    r = future.result(timeout=0)
                except (FuturesTimeoutError, CancelledError):
                    r = _failure_result(inst, params, "timeout", f"after {timeout_per_instance}s")
                except BrokenProcessPool:
                    # The kill switch arms `os._exit(137)` at the deadline,
                    # which surfaces here as BrokenProcessPool. Distinguish
                    # timeout-induced death from a genuine pool crash by
                    # elapsed wall-clock — within 90% of the deadline the
                    # likely cause is our timer. Persist as "timeout" (not
                    # "error") so the checkpoint records it and a retry
                    # loop does not re-evaluate the same pathological
                    # instance forever.
                    elapsed = time.monotonic() - submit_times.get(inst.instance_id, 0.0)
                    if elapsed >= timeout_per_instance * 0.9:
                        r = _failure_result(
                            inst,
                            params,
                            "timeout",
                            f"killed after {timeout_per_instance}s (elapsed {elapsed:.1f}s)",
                        )
                    else:
                        r = _failure_result(inst, params, "error", "BrokenProcessPool: worker died")
                        pool_broken = True
                except Exception as e:
                    r = _failure_result(inst, params, "error", f"{type(e).__name__}: {e}")
                completed.add(inst.instance_id)
                record(r)
        except FuturesTimeoutError:
            for inst in futures.values():
                if inst.instance_id not in completed:
                    record(_failure_result(inst, params, "timeout", "exceeded global deadline"))
        except BrokenProcessPool:
            pool_broken = True
            for inst in futures.values():
                if inst.instance_id not in completed:
                    record(_failure_result(inst, params, "error", "BrokenProcessPool: worker died"))
        for inst in submit_failed:
            record(_failure_result(inst, params, "error", "BrokenProcessPool: submit failed"))
        if pool_broken:
            raise BrokenProcessPool("pool degraded mid-cell")

    if pool is not None:
        _drain(pool)  # type: ignore[arg-type]
        return

    ctx = mp.get_context("spawn")
    with ProcessPoolExecutor(max_workers=workers, mp_context=ctx, max_tasks_per_child=50) as owned:
        _drain(owned)
        owned.shutdown(wait=False, cancel_futures=True)
