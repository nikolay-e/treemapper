"""Materialize the v1 calibration / validation / test manifests.

Default decisions (see `benchmarks/README.md` for rationale):
- 3-way split (calibration + validation + test).
- Test set: SWE-bench Verified, PolyBench Verified, Multi-SWE-bench mini,
  ContextBench verified — each kept whole, never seen during the τ sweep.
- Calibration pool: SWE-bench Lite + PolyBench500 + Multi-SWE-bench flash
  + ContextBench default. Anything sharing `(repo, base_commit)` with a
  test instance is dropped via `ContaminationDetector`.
- Stratified sampling within `(source_benchmark, language)` groups; 10% of
  each group goes to validation.
- Random seed 42 for reproducibility.

Usage::

    python -m benchmarks.build_splits --out benchmarks/manifests/v1
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

from benchmarks.adapters import (
    BenchmarkAdapter,
    ContextBenchAdapter,
    MultiSWEBenchFlashAdapter,
    MultiSWEBenchMiniAdapter,
    PolyBench500Adapter,
    PolyBenchVerifiedAdapter,
    SWEBenchLiteAdapter,
    SWEBenchVerifiedAdapter,
)
from benchmarks.adapters.splits import (
    SplitConfig,
    build_splits,
    render_split_report,
    write_manifests,
)


def default_test_adapters() -> tuple[BenchmarkAdapter, ...]:
    return (
        SWEBenchVerifiedAdapter(),
        PolyBenchVerifiedAdapter(),
        MultiSWEBenchMiniAdapter(),
        ContextBenchAdapter(config="contextbench_verified"),
    )


def default_calibration_pool_adapters() -> tuple[BenchmarkAdapter, ...]:
    return (
        SWEBenchLiteAdapter(),
        PolyBench500Adapter(),
        MultiSWEBenchFlashAdapter(),
        ContextBenchAdapter(config="default"),
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).parent / "manifests" / "v1",
        help="Manifest directory (default: benchmarks/manifests/v1)",
    )
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--validation-fraction", type=float, default=0.10)
    args = p.parse_args()

    config = SplitConfig(
        test_only_adapters=default_test_adapters(),
        calibration_pool_adapters=default_calibration_pool_adapters(),
        validation_fraction=args.validation_fraction,
        seed=args.seed,
    )
    print(f"Building splits with seed={config.seed}, validation={config.validation_fraction:.0%}...")
    print(f"Test adapters: {[a.name for a in config.test_only_adapters]}")
    print(f"Calibration pool adapters: {[a.name for a in config.calibration_pool_adapters]}")
    print()

    result = build_splits(config)
    written = write_manifests(result, args.out)
    today = dt.date.today().isoformat()
    report = render_split_report(config, result, today=today)
    report_path = args.out / "SPLIT_REPORT.md"
    report_path.write_text(report)

    print(f"Test     : {result.stats.test_total:>5d}")
    print(f"Validation: {result.stats.validation_total:>5d}")
    print(f"Calibration: {result.stats.calibration_total:>5d}")
    print(f"Dropped (contamination): {result.stats.pool_dropped_by_contamination:>5d}")
    print()
    print(f"Manifests: {args.out}")
    for name, path in sorted(written.items()):
        print(f"  {name}: {path}")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
