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

## 2026-06-14 · d4216b0 · full repo (src/, pyproject, docs, CHANGELOG)

### TL;DR
Re-audit after the previous run's three fixes landed in `d4216b0` — all three
confirmed resolved (dynamic hatchling version; `run` re-exported in `__init__`
and pinned by `test_run_is_the_engine_entry`; README pin = `>=1.8,<2.0`). Code
is correct: mypy --strict + ruff clean, 13 integration tests pass, and every
diffctx call (`run`, `mcp.__main__.main`, `map_directory`, `build_diff_context`,
`to_*`) verified by signature inspection against installed diffctx 1.8.1. One
new defect: a **lying CHANGELOG**.

### Top Issues (fix immediately)
1. 🟡 `CHANGELOG.md:16-19` — Lying changelog. The `[Unreleased]` entry claims
   "Both paths fall back gracefully when an older diffctx (< 1.8.0 …) is
   installed — the CLI stays fully functional, only `--help`/MCP-hint naming
   reverts to `diffctx`." False twice over: (a) the fallback was deliberately
   removed in commit `2dd1a9b` ("drop pre-1.8 fallback") — `cli.py:9` and
   `mcp_main.py:7` call the engine directly with no try/except, so on a pre-1.8
   diffctx they raise, not "stay fully functional"; (b) it is impossible anyway —
   `pyproject.toml` pins `diffctx>=1.8,<2.0`. Rewrite to state the hard `>=1.8`
   requirement (matches CLAUDE.md "no fallback path") and record the 1.7→1.8 pin
   bump that this unreleased cycle actually made.

### False Positives
- `version.py` = `2.0.0` vs diffctx `1.8.1`: independent product versions, fine.

### Verdict
Code and delegation contract are correct; only fix needed is the false fallback
claim in `CHANGELOG.md [Unreleased]`.

### Resolution
Fixed in this run: `CHANGELOG.md [Unreleased]` rewritten to drop the false
graceful-fallback claim and record the `>=1.8` hard floor / removed fallback.

_Scouts/synthesis: folded (small scope, deterministic checks)_
