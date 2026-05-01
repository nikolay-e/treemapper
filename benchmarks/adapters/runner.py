from __future__ import annotations

import json
import time
from collections.abc import Callable, Iterable, Iterator
from dataclasses import asdict, dataclass, field
from pathlib import Path

from benchmarks.adapters.base import BenchmarkAdapter, BenchmarkInstance, EvalResult

EvalFn = Callable[[BenchmarkInstance, "RunParams"], EvalResult]


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
    """Append one result as a JSONL row. Atomic per-line on POSIX."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(asdict(result), default=str) + "\n")


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
    timeout_per_instance: float = 300.0,
    resume_from: Path | None = None,
    checkpoint_path: Path | None = None,
    pool: object | None = None,
) -> list[EvalResult]:
    """Run `eval_fn(instance, params)` for every instance.

    - `workers > 1` uses a process pool (spawn context) so workers do
      not share the GIL; otherwise sequential.
    - `timeout_per_instance` records a `status="timeout"` failure for any
      future that does not return within the deadline. The hung worker
      process is left to finish on its own; pool shutdown does not wait
      for it.
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
        err = str((r.extra or {}).get("error", ""))
        if "BrokenProcessPool" in err:
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

    def _drain(active_pool: ProcessPoolExecutor) -> None:
        from concurrent.futures.process import BrokenProcessPool

        futures: dict = {}
        submit_failed: list[BenchmarkInstance] = []
        for inst in pending:
            try:
                futures[active_pool.submit(eval_fn, inst, params)] = inst
            except BrokenProcessPool:
                submit_failed.extend([inst, *pending[pending.index(inst) + 1 :]])
                break
        outer_deadline = time.monotonic() + timeout_per_instance * max(1, (len(pending) + workers - 1) // workers)
        completed: set[str] = set()
        try:
            for future in as_completed(futures, timeout=max(0.0, outer_deadline - time.monotonic())):
                inst = futures[future]
                try:
                    r = future.result(timeout=0)
                except FuturesTimeoutError:
                    r = _failure_result(inst, params, "timeout", f"after {timeout_per_instance}s")
                except BrokenProcessPool:
                    r = _failure_result(inst, params, "error", "BrokenProcessPool: worker died")
                except Exception as e:
                    r = _failure_result(inst, params, "error", f"{type(e).__name__}: {e}")
                completed.add(inst.instance_id)
                record(r)
        except FuturesTimeoutError:
            for inst in futures.values():
                if inst.instance_id not in completed:
                    record(_failure_result(inst, params, "timeout", "exceeded global deadline"))
        except BrokenProcessPool:
            for inst in futures.values():
                if inst.instance_id not in completed:
                    record(_failure_result(inst, params, "error", "BrokenProcessPool: worker died"))
        for inst in submit_failed:
            record(_failure_result(inst, params, "error", "BrokenProcessPool: submit failed"))
        if submit_failed or any(inst.instance_id not in completed for inst in futures.values()):
            raise BrokenProcessPool("pool degraded mid-cell")

    if pool is not None:
        _drain(pool)  # type: ignore[arg-type]
        return

    ctx = mp.get_context("spawn")
    with ProcessPoolExecutor(max_workers=workers, mp_context=ctx) as owned:
        _drain(owned)
        owned.shutdown(wait=False, cancel_futures=True)
