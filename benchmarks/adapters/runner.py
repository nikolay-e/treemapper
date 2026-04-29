from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass, field
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


def run_eval_set(
    instances: list[BenchmarkInstance],
    eval_fn: EvalFn,
    params: RunParams,
    workers: int = 1,
) -> list[EvalResult]:
    """Run `eval_fn(instance, params)` for every instance, optionally in
    parallel via a thread pool. Order is preserved.

    `eval_fn` is expected to be already-wrapped: tests pass a stub, the CLI
    wraps `default_eval_fn` (which clones the repo, applies the patch, calls
    diffctx, computes metrics).
    """
    if workers <= 1 or len(instances) <= 1:
        return [eval_fn(inst, params) for inst in instances]
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(lambda inst: eval_fn(inst, params), instances))
