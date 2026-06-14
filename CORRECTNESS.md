# CORRECTNESS — /review-correctness findings log

## 2026-06-14 · 2dd1a9b · full repo (src/, pyproject, docs)

### TL;DR
Thin delegation layer is logically sound: every called/re-exported `diffctx`
symbol exists with a matching signature, mypy is clean, 12 integration tests
pass. The defects are all **claims that no longer match reality** — a duplicated
version literal that can silently lie, and two stale docs (one promising an
export that doesn't exist, one citing an out-of-date dependency floor).

### Top Issues (fix immediately)
1. 🟡 `src/treemapper/version.py:1` + `pyproject.toml:7` — version `2.0.0` is
   hardcoded in **two** places with no `dynamic`/single-source link. `--version`
   reads `version.py`; PyPI ships `pyproject` version. A one-sided bump makes
   `treemapper --version` report a version different from what was published.
   Fix: `dynamic = ["version"]` + `[tool.hatch.version] path =
   "src/treemapper/version.py"`.
2. 🔵 `CLAUDE.md:23` — architecture diagram claims `__init__.py` re-exports
   `diffctx.{… run …}`, but `treemapper.run` raises `AttributeError` (`run`
   absent from `__init__` `__all__`). A library user following the doc breaks.
   Fix: add `run` to the re-exports (mirrors `import diffctx`, the stated intent)
   or drop `run` from the diagram.
3. 🔵 `README.md:65` — "Pin compatibility is `diffctx>=1.7,<2.0`", but the real
   pin is `>=1.8,<2.0` (`pyproject.toml:47`). The `>=1.8` floor is load-bearing
   (the `run(prog=…)` branded entry landed in diffctx 1.8.0, per the last
   commit). README understates the floor → a user could pin 1.7 and lose the
   branded CLI / `run` entry.

### Systemic Patterns
Duplicated facts across code+docs with no single source of truth: the version
literal, the dependency floor, and the export list each exist in 2 places and
have already drifted in 2 of 3 cases. Root cause: hand-maintained mirrors of
values that tooling could derive (hatchling dynamic version) or that tests could
pin (an assertion that `treemapper.run is diffctx.run`).

### False Positives
- README Python-API examples (`map_directory(".", no_content=False)`,
  `build_diff_context(root_dir=".", diff_range="HEAD~1")`) — signatures verified
  against installed diffctx 1.8.1; both run. `root_dir` is hinted `Path` but a
  str works at runtime; not a correctness bug.
- `mcp_main.py` `main(prog=…, extra=…)` — matches engine signature exactly.

### Resolution
All three fixed in this run: hatchling dynamic version, `run` added to
`__init__` re-exports (+ test pinning `treemapper.run is diffctx.run`), README
pin corrected to `>=1.8,<2.0`.

_Scouts/synthesis: folded (small scope, deterministic checks)_
