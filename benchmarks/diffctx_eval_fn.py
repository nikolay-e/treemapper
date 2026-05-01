"""Production `EvalFn` that wires diffctx into the unified runner.

This is the only file that bridges the adapter layer to the existing
benchmark machinery (repo cloning, patch application, diffctx invocation).
Tests use stub `EvalFn`s — they never reach this module.
"""

from __future__ import annotations

import functools
import os
import time
from pathlib import Path

import tiktoken

from benchmarks.adapters import BenchmarkInstance, GoldenFragment
from benchmarks.adapters.base import EvalResult
from benchmarks.adapters.evaluator import SelectionOutput, UniversalEvaluator
from benchmarks.adapters.runner import RunParams

_TOKEN_ENC = tiktoken.get_encoding("o200k_base")

_WORKER_STATE: dict = {}


def _compute_used_tokens(output: dict) -> int:
    aggregate = output.get("token_count")
    if isinstance(aggregate, int) and aggregate > 0:
        return aggregate
    total = 0
    for f in output.get("fragments", []) or []:
        per_frag = f.get("token_count")
        if isinstance(per_frag, int) and per_frag > 0:
            total += per_frag
            continue
        content = f.get("content")
        if isinstance(content, str) and content:
            total += len(_TOKEN_ENC.encode(content, disallowed_special=()))
    return total


def _output_fragments(output: dict) -> tuple[GoldenFragment, ...]:
    from benchmarks.common import parse_lines_field

    out: list[GoldenFragment] = []
    for f in output.get("fragments", []) or []:
        path = f.get("path") or f.get("file")
        lines = f.get("lines", "")
        rng = parse_lines_field(lines) if isinstance(lines, str) else None
        if path is None:
            continue
        if rng is None:
            out.append(GoldenFragment(path=str(path), kind="file"))
        else:
            out.append(GoldenFragment(path=str(path), start_line=rng[0], end_line=rng[1], kind="hunk"))
    return tuple(out)


def _selected_files(fragments: tuple[GoldenFragment, ...]) -> frozenset[str]:
    return frozenset(f.path for f in fragments)


def _ensure_worker_state(repos_dir_str: str) -> tuple[Path, UniversalEvaluator]:
    state = _WORKER_STATE.get(repos_dir_str)
    if state is None:
        worktree_dir = Path(repos_dir_str) / "worktrees" / f"w{os.getpid()}"
        worktree_dir.mkdir(parents=True, exist_ok=True)
        evaluator = UniversalEvaluator()
        state = (worktree_dir, evaluator)
        _WORKER_STATE[repos_dir_str] = state
    return state


def _pool_eval(repos_dir_str: str, instance: BenchmarkInstance, params: RunParams) -> EvalResult:
    from benchmarks.common import apply_as_commit, ensure_repo, reset_to_parent

    worktree_dir, evaluator = _ensure_worker_state(repos_dir_str)

    repo_url = str(instance.extra.get("repo_url") or f"https://github.com/{instance.repo}")
    repo_dir = ensure_repo(repo_url, instance.repo, instance.base_commit, worktree_dir)
    if repo_dir is None:
        result = EvalResult(
            instance_id=instance.instance_id,
            source_benchmark=instance.source_benchmark,
            file_recall=0.0,
            file_precision=0.0,
            budget=params.budget,
        )
        result.extra["status"] = "clone_fail"
        return result

    prior_env = {k: os.environ.get(k) for k in params.to_env()}
    try:
        for k, v in params.to_env().items():
            os.environ[k] = v
        apply_as_commit(repo_dir, instance.gold_patch, "diffctx-eval-gold")
        t0 = time.perf_counter()
        from treemapper.diffctx.pipeline import build_diff_context

        output = build_diff_context(
            repo_dir,
            "HEAD~1..HEAD",
            budget_tokens=params.budget,
            scoring_mode=params.scoring,
            tau=params.tau,
        )
        elapsed = time.perf_counter() - t0
        if output is None:
            result = EvalResult(
                instance_id=instance.instance_id,
                source_benchmark=instance.source_benchmark,
                file_recall=0.0,
                file_precision=0.0,
                budget=params.budget,
                elapsed_seconds=elapsed,
            )
            result.extra["status"] = "diffctx_fail"
            return result
        fragments = _output_fragments(output)
        used_tokens = _compute_used_tokens(output)
        selection = SelectionOutput(
            selected_files=_selected_files(fragments),
            selected_fragments=fragments,
            used_tokens=used_tokens,
            elapsed_seconds=elapsed,
        )
        result = evaluator.evaluate(instance, selection, budget=params.budget)
        result.used_tokens = used_tokens
        result.extra["status"] = "ok"
        result.extra["language"] = instance.language
        result.extra["fragment_count"] = len(fragments)
        latency = output.get("latency") or {}
        if latency:
            result.extra["latency_total_ms"] = latency.get("total_ms")
            result.extra["latency_breakdown"] = {k: v for k, v in latency.items() if k != "total_ms"}
        return result
    finally:
        for k, v in prior_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        try:
            reset_to_parent(repo_dir)
        except Exception:
            pass


def make_diffctx_eval_fn(repos_dir: Path):
    return functools.partial(_pool_eval, str(repos_dir))
