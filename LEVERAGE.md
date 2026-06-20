# LEVERAGE — /review-leverage findings log

## 2026-06-14 · 04b... (fix/changelog-fallback-claim) · full repo (src/, pyproject, CI, pre-commit)

### TL;DR
This repo is already a clean leverage result — it exists precisely to *not*
duplicate engine logic, and the recent commits (`c0ff3ed` drop black+pygit2 →
ruff-format + uv CI; `2dd1a9b` drop pre-1.8 fallback) did most of the trimming.
The 5 source files are pure delegation to `diffctx` with nothing to cut or
reinvent. One measured over-tooling finding remains: pytest-xdist on a sub-1s
suite.

### Top Issues
1. 🟡 `pyproject.toml:100` (`addopts = "-n auto --dist worksteal"`) + dev dep
   `pytest-xdist>=3.8.0,<4.0` (`pyproject.toml`) — parallel test execution on a
   13-test suite that runs in **0.76s serially**. Measured: with xdist = 1.64s
   wall / 8.7s CPU (531%); without = 0.76s wall / 0.75s CPU. xdist's
   worker-spawn ("bringing up nodes…" ×N) makes the suite **~2× slower** and
   ~10× more CPU for zero benefit. Over-tooling = complexity the problem doesn't
   demand. Fix: drop `-n auto --dist worksteal` from `addopts`, remove
   `pytest-xdist` from dev deps. Same waste multiplies in CI across the 4-version
   matrix. **Effort: Easy.**

### Already-good (no action — calibration for future runs)
- **Code:** `cli.py`, `mcp_main.py`, `__init__.py`, `__main__.py`, `version.py`
  are all thin delegation/re-export. No abstraction to collapse, no stdlib/lib
  reinvention. The "thin wrapper" pattern is executed correctly.
- **Tooling already modern:** ruff + ruff-format (replaced black+isort), uv in
  CI, hatchling dynamic version, validate-pyproject, mypy --strict. No swap to
  recommend.
- **`ty` (astral type checker) correctly NOT adopted** — not at mypy parity /
  not GA as of this audit; per the governing filter, flagging the gap, not
  forcing the swap. Revisit when GA.
- **Single runtime dependency** (`diffctx`); extras pass through cleanly.

### Total Estimated Savings
- Lines/config: remove 1 `addopts` knob + 1 dev dependency.
- CI: faster + lower-CPU test job across 4 Python versions (no worker spawn).
- Dependencies to remove: `pytest-xdist`. To add: none. Tools to swap: none.
- Net: the repo is near-optimal for leverage; the xdist removal is the only win.

_Scouts/synthesis: folded (small scope, deterministic + measured checks)_

## 2026-06-14 · b5483ca · full repo (src/, tests/, pyproject, CI, pre-commit, dependabot)

### TL;DR
Repo remains a near-optimal leverage result. The one prior actionable finding —
pytest-xdist on a sub-1s suite — was **resolved** in `a64854a` (no `addopts`, no
`pytest-xdist` dep remain). vulture finds zero dead code; no TODO/FIXME/commented
blocks; 5 source files are still pure delegation with nothing to cut, dedupe, or
reinvent. Tooling is already modern (ruff + ruff-format, uv CI, hatchling dynamic
version, mypy --strict). Only two 🔵 nitpicks, neither worth the churn.

### Notes (🔵 only — no action taken)
1. 🔵 `tests/test_cli.py:78` `test_result_dataclass_shape` — tautological: asserts
   `run_cli` (a test helper) returns its own `CliResult` dataclass, which every
   other test already exercises via `.exit_code`/`.stdout`. Tests the harness, not
   the product. Pure-subtraction deletion (~3 lines, no coverage loss) — left in
   as it's harmless and arguably documents the harness contract.
2. 🔵 `.github/workflows/ci.yml:36` `pytest tests/ -v --timeout=120` — the `tests/`
   arg duplicates `[tool.pytest.ini_options] testpaths`; the `--timeout=120`
   override of the config's `timeout=30` is intentional (slower CI). Trivial.

### Already-good (calibration for future runs)
- xdist removal landed; CI test job is now serial and fast across the 3.10–3.13
  matrix. Single runtime dep (`diffctx`); extras pass through cleanly.
- `ty` (astral type checker) still correctly NOT adopted — not at mypy parity / GA.

### Total Estimated Savings
- Lines deletable: ~3 (one tautological test, optional). Config removable: none.
- Dependencies to add/remove: none. Tools to swap: none.
- Net: nothing actionable — the repo is at the leverage floor for a thin wrapper.

_Scouts/synthesis: folded (small unchanged scope, deterministic + vulture checks)_

- _Re-confirmed at `fd0bd3e` — leverage source byte-identical to `b5483ca` (only workflows gained `concurrency`). One new **VERIFY**: `pyproject.toml` `dev` extra self-references `treemapper[tree-sitter]` — gate: `pytest` passes with it dropped → if so remove the unused native dev dep. Scout "phantom-gate / CI runs on GitHub mirror not Forgejo" **ruled out** — Forgejo-source + GitHub-mirror-Actions is the deliberate workspace model, not a hole. No contradictions with prior runs (ty stance consistent). Collapsed to one line per the no-landfill rule._
