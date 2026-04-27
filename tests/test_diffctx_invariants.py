from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

from tests.framework.pygit2_backend import Pygit2Repo

PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"

TOKEN_RE = re.compile(r"^([\d,]+)\s+tokens\b", re.MULTILINE)


def _make_diff_repo(tmp_path: Path) -> tuple[Pygit2Repo, str]:
    repo = Pygit2Repo(tmp_path / "repo")
    repo.add_file(
        "src/calc.py",
        "def add(a, b):\n    return a + b\n\n" "def sub(a, b):\n    return a - b\n\n" "def mul(a, b):\n    return a * b\n",
    )
    repo.add_file(
        "src/main.py",
        "from calc import add, sub, mul\n\n" "def run():\n    return add(1, 2) + sub(3, 1) + mul(2, 4)\n",
    )
    repo.add_file("README.md", "# Demo\n\nUses `calc` helpers.\n")
    base = repo.commit("initial")

    repo.add_file(
        "src/calc.py",
        "def add(a, b):\n    return a + b\n\n"
        "def sub(a, b):\n    return a - b\n\n"
        "def mul(a, b):\n    return a * b\n\n"
        "def div(a, b):\n    if b == 0:\n        raise ZeroDivisionError\n    return a / b\n",
    )
    head = repo.commit("add div")
    return repo, f"{base}..{head}"


def _run(
    cwd: Path,
    args: list[str],
    extra_env: dict[str, str] | None = None,
) -> tuple[str, str]:
    cmd = [sys.executable, "-m", "treemapper", *args]
    env = {"PYTHONPATH": str(SRC_DIR)}
    if extra_env:
        env.update(extra_env)
    result = subprocess.run(
        cmd,
        cwd=cwd,
        env={**dict(__import__("os").environ), **env},
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout, result.stderr


def _extract_tokens(combined_output: str) -> int:
    m = TOKEN_RE.search(combined_output)
    assert m, f"Could not parse token count from output:\n{combined_output[:500]}"
    return int(m.group(1).replace(",", ""))


def test_diffctx_output_is_byte_identical_across_runs(tmp_path):
    repo, diff_range = _make_diff_repo(tmp_path)
    args = [".", "--diff", diff_range, "--budget", "1024", "-f", "txt"]
    runs = [_run(repo.path, args)[0] for _ in range(5)]
    distinct = set(runs)
    assert len(distinct) == 1, (
        f"Non-deterministic output: {len(distinct)} distinct outputs across 5 runs. " f"First diff: {next(iter(distinct))[:300]}"
    )


def test_extreme_core_budget_fraction_is_clamped(tmp_path):
    repo, diff_range = _make_diff_repo(tmp_path)
    budget = 1024
    args = [".", "--diff", diff_range, "--budget", str(budget), "-f", "txt"]

    out, err = _run(repo.path, args)
    baseline_tokens = _extract_tokens(out + err)
    out, err = _run(repo.path, args, {"DIFFCTX_OP_SELECTION_CORE_BUDGET_FRACTION": "42"})
    extreme_tokens = _extract_tokens(out + err)

    assert extreme_tokens < 4 * budget, (
        f"core_budget_fraction=42 should clamp to 1.0, but produced {extreme_tokens} tokens "
        f"(budget={budget}, baseline={baseline_tokens}). Underflow likely."
    )


@pytest.mark.parametrize(
    "env_var",
    [
        "DIFFCTX_OP_SELECTION_CORE_BUDGET_FRACTION",
        "DIFFCTX_OP_RESCUE_BUDGET_FRACTION",
        "DIFFCTX_OP_PPR_ALPHA",
        "DIFFCTX_OP_PPR_FORWARD_BLEND",
    ],
)
def test_fraction_param_rejects_negative_falls_back_to_default(tmp_path, env_var):
    repo, diff_range = _make_diff_repo(tmp_path)
    args = [".", "--diff", diff_range, "--budget", "1024", "-f", "txt"]

    baseline_out, _ = _run(repo.path, args)
    negative_out, _ = _run(repo.path, args, {env_var: "-1.0"})

    assert baseline_out == negative_out, (
        f"{env_var}=-1.0 should be rejected and fall back to default, " f"but stdout differs (clamp/reject path inconsistent)."
    )
