"""Per-cell metric aggregation from a checkpoint.jsonl file.

Produces the `cell_summary.json` consumed by `aggregate_sweep.py` and by
the bench-sweep workflow. Centralizing here lets us add F-beta, latency
percentiles, per-language breakdowns, robustness bins, and conditional
line-F1 once and have every sweep run pick them up.

CLI:
    python -m benchmarks.cell_metrics --ckpt path/to/X.checkpoint.jsonl

Writes a single JSON object to stdout. Stable, additive schema.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

_F_BETAS: tuple[float, ...] = (0.5, 1.0, 2.0)


def _safe_div(num: float, denom: float) -> float:
    return num / denom if denom > 0 else 0.0


def _percentile(sorted_values: Sequence[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    if q <= 0:
        return float(sorted_values[0])
    if q >= 1:
        return float(sorted_values[-1])
    pos = q * (len(sorted_values) - 1)
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return float(sorted_values[lo])
    frac = pos - lo
    return float(sorted_values[lo] * (1 - frac) + sorted_values[hi] * frac)


def _percentile_block(values: Iterable[float]) -> dict[str, object]:
    vals = sorted(float(v) for v in values)
    if not vals:
        return {"mean": 0.0, "median": 0.0, "p25": 0.0, "p75": 0.0, "p95": 0.0, "p99": 0.0, "max": 0.0, "std": 0.0}
    mean = statistics.fmean(vals)
    return {
        "mean": mean,
        "median": _percentile(vals, 0.5),
        "p25": _percentile(vals, 0.25),
        "p75": _percentile(vals, 0.75),
        "p95": _percentile(vals, 0.95),
        "p99": _percentile(vals, 0.99),
        "max": vals[-1],
        "std": statistics.pstdev(vals) if len(vals) > 1 else 0.0,
    }


def _f_beta(p: float, r: float, beta: float) -> float:
    """Fβ = (1+β²) · P · R / (β² · P + R). Returns 0 when denom == 0."""
    if p <= 0 and r <= 0:
        return 0.0
    b2 = beta * beta
    denom = b2 * p + r
    return _safe_div((1 + b2) * p * r, denom)


def _f_beta_block(precisions: Sequence[float], recalls: Sequence[float]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for beta in _F_BETAS:
        scores = [_f_beta(p, r, beta) for p, r in zip(precisions, recalls)]
        if not scores:
            out[f"f{beta:g}"] = {"mean": 0.0}
            continue
        out[f"f{beta:g}"] = {"mean": statistics.fmean(scores), "median": _percentile(sorted(scores), 0.5)}
    return out


def _recall_histogram(values: Sequence[float]) -> dict[str, float]:
    if not values:
        return {"perfect_pct": 0.0, "zero_pct": 0.0, "partial_pct": 0.0}
    n = len(values)
    perfect = sum(1 for v in values if v >= 1.0 - 1e-9)
    zero = sum(1 for v in values if v <= 1e-9)
    return {
        "perfect_pct": 100.0 * perfect / n,
        "zero_pct": 100.0 * zero / n,
        "partial_pct": 100.0 * (n - perfect - zero) / n,
    }


def _by_language(rows: Sequence[dict]) -> dict[str, dict[str, float]]:
    groups: dict[str, list[dict]] = {}
    for r in rows:
        lang = str((r.get("extra") or {}).get("language", "unknown"))
        groups.setdefault(lang, []).append(r)
    out: dict[str, dict[str, float]] = {}
    for lang, rs in groups.items():
        recalls = [float(r.get("file_recall") or 0.0) for r in rs]
        precs = [float(r.get("file_precision") or 0.0) for r in rs]
        n = len(rs)
        if n == 0:
            continue
        mean_r = statistics.fmean(recalls)
        mean_p = statistics.fmean(precs)
        out[lang] = {
            "n": float(n),
            "file_recall": mean_r,
            "file_precision": mean_p,
            "f1": _f_beta(mean_p, mean_r, 1.0),
            "f2": _f_beta(mean_p, mean_r, 2.0),
        }
    return out


def _conditional_line_f1(rows: Sequence[dict]) -> dict[str, float] | None:
    """Mean line_f1 conditional on file_recall > 0 (the file was at least partly retrieved)."""
    cond = [float(r["line_f1"]) for r in rows if r.get("line_f1") is not None and float(r.get("file_recall") or 0.0) > 0.0]
    if not cond:
        return None
    return {"mean": statistics.fmean(cond), "n": float(len(cond))}


def compute_cell_summary(rows: Sequence[dict]) -> dict:
    n = len(rows)
    if n == 0:
        return {"n": 0}

    recall = [float(r.get("file_recall") or 0.0) for r in rows]
    precision = [float(r.get("file_precision") or 0.0) for r in rows]
    elapsed = [float(r.get("elapsed_seconds") or 0.0) for r in rows]
    tokens = [float(r.get("used_tokens") or 0.0) for r in rows]

    frag_recall = [float(r["fragment_recall"]) for r in rows if r.get("fragment_recall") is not None]
    frag_precision = [float(r["fragment_precision"]) for r in rows if r.get("fragment_precision") is not None]
    line_f1 = [float(r["line_f1"]) for r in rows if r.get("line_f1") is not None]

    # Cardinality proxies: prefer extra.n_selected / extra.n_gold (added in UniversalEvaluator),
    # fall back to extra.fragment_count (legacy, fragments not files) when n_selected absent.
    n_selected: list[float] = []
    n_gold: list[float] = []
    fragment_count: list[float] = []
    for r in rows:
        ex = r.get("extra") or {}
        if "n_selected" in ex:
            n_selected.append(float(ex["n_selected"]))
        if "n_gold" in ex:
            n_gold.append(float(ex["n_gold"]))
        if "fragment_count" in ex:
            fragment_count.append(float(ex["fragment_count"]))

    statuses: dict[str, int] = {}
    errors: dict[str, int] = {}
    for r in rows:
        s = str((r.get("extra") or {}).get("status", "missing"))
        statuses[s] = statuses.get(s, 0) + 1
        if s != "ok":
            err = str((r.get("extra") or {}).get("error", "")).strip()
            if err:
                errors[err] = errors.get(err, 0) + 1
    ok = statuses.get("ok", 0)

    rec_block = _percentile_block(recall)
    rec_block["hist"] = _recall_histogram(recall)
    prec_block = _percentile_block(precision)

    out: dict = {
        "n": n,
        "ok": ok,
        "ok_pct": 100.0 * ok / n,
        "statuses": statuses,
        "errors": dict(sorted(errors.items(), key=lambda x: -x[1])[:10]),
        "file_recall": rec_block,
        "file_precision": prec_block,
        "file_fbeta": _f_beta_block(precision, recall),
        "fragment_recall": ({"mean": statistics.fmean(frag_recall), "n_with_gold": len(frag_recall)} if frag_recall else None),
        "fragment_precision": (
            {"mean": statistics.fmean(frag_precision), "n_with_gold": len(frag_precision)} if frag_precision else None
        ),
        "fragment_fbeta": (_f_beta_block(frag_precision, frag_recall) if frag_recall and frag_precision else None),
        "line_f1": (
            {
                "mean": statistics.fmean(line_f1),
                "n_with_gold": len(line_f1),
                "conditional_on_file_hit": _conditional_line_f1(rows),
            }
            if line_f1
            else None
        ),
        "elapsed_seconds": _percentile_block(elapsed),
        "used_tokens": _percentile_block(tokens),
        "by_language": _by_language(rows),
    }
    if n_selected:
        out["n_selected"] = _percentile_block(n_selected)
    if n_gold:
        out["n_gold"] = _percentile_block(n_gold)
    if fragment_count:
        out["fragment_count"] = _percentile_block(fragment_count)
    return out


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue
    return rows


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ckpt", type=Path, required=True, help="path to <test_set>.checkpoint.jsonl")
    p.add_argument("--out", type=Path, default=None, help="output path (default: stdout)")
    args = p.parse_args()

    if not args.ckpt.exists():
        sys.stderr.write(f"checkpoint not found: {args.ckpt}\n")
        payload = {"error": "no checkpoint produced", "expected_path": str(args.ckpt)}
    else:
        rows = load_jsonl(args.ckpt)
        payload = compute_cell_summary(rows)
        if payload.get("errors"):
            sys.stderr.write("=== ERROR BREAKDOWN ===\n")
            for msg, cnt in sorted(payload["errors"].items(), key=lambda x: -x[1]):
                sys.stderr.write(f"  [{cnt}x] {msg[:200]}\n")

    text = json.dumps(payload, indent=2, default=str)
    if args.out:
        args.out.write_text(text)
    else:
        sys.stdout.write(text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
