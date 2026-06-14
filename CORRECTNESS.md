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

## 2026-06-14 · 970006c · release diff (cd.yml, version 2.1.0, diffctx pin >=1.9.1)

### TL;DR
Audit of the 2.1.0 release work (new `.github/workflows/cd.yml`, version bump,
pin `diffctx>=1.9.1`). Clean: mypy --strict + ruff + 13 tests pass, cd.yml is
valid YAML and **actionlint-clean**, and the delegation contract was re-verified
against the **actually-shipped diffctx 1.9.1** (not memory) —
`run(argv, *, prog, version)` and `mcp.__main__.main(prog, extra)` match the
calls in `cli.py:9` / `mcp_main.py:7` exactly, `treemapper.run is diffctx.run`,
all re-exports present. The workflow itself ran green end-to-end in production
(prepare→build→publish→6× smoke), so its happy path is empirically correct, not
just statically plausible. No 🔴/🟡 defects.

### Notes
1. 🔵 `cd.yml` `finalize-release.if` (mirrors diffctx): with
   `publish_to_pypi=false`, publish+smoke are *skipped* (not failed), so finalize
   still runs and would push the version commit + tag and create a GitHub
   release — i.e. `publish_to_pypi=false` is not a true dry-run. In practice the
   "Push commit and tag to main" step fails first under branch protection
   (GH006), so nothing is actually mutated; manual finalize is the established
   flow. Inherited from the proven diffctx workflow, not a regression. Left as-is.
2. 🔵 `CLAUDE.md:41` says the `>=1.9.1` floor "guarantees the `run(prog=…)` entry"
   — technically true (1.9.1 > the 1.8.0 that introduced it); the sentence also
   correctly attributes the diff-context header/role ordering to diffctx 1.9.x.
   Not misleading.

### False Positives
- `version.py` = `2.1.0` while local dev venv still has diffctx 1.8.1: the venv
  wasn't reinstalled against the new pin; the *shipped* artifact resolves
  `diffctx>=1.9.1` (verified: PyPI 2.1.0 `requires_dist` + fresh-install pulled
  1.9.1). Not a defect.

### Verdict
Release is correct: code, workflow, and delegation against diffctx 1.9.1 all hold;
no fixes needed.

_Scouts/synthesis: folded (small scope, deterministic + empirical CD evidence)_

## 2026-06-14 · 83b989d · full repo (src/, pyproject, docs, CHANGELOG)

### TL;DR
Re-audit at HEAD. Source is **byte-identical** to the last clean run (970006c);
only `CORRECTNESS.md` changed since. Stronger evidence this time: the dev venv
now actually carries the pinned **diffctx 1.9.1** (was 1.8.1 before), so the
delegation contract is verified against the exact shipped floor, not an older
local copy. mypy --strict + ruff clean, 13 tests pass. No 🔴/🟡/🔵 defects.

### Verification
- `diffctx.run(argv, *, prog, version)` and `mcp.__main__.main(prog, extra)`
  signatures match the calls in `cli.py:9` / `mcp_main.py:7` exactly.
- `treemapper.run is diffctx.run`; all 7 re-exports identity-match diffctx.
- `map_directory(".", no_content=False)` and
  `build_diff_context(root_dir=".", diff_range="HEAD~1")` (README:56/59) run
  against the real 1.9.1 signatures (`root_dir: Path` accepts str at runtime).
- Docs consistent: README pin (`>=1.9.1,<2.0`, README:65) = pyproject;
  CHANGELOG `[Unreleased]` empty, `[2.1.0]` accurate; no stale fallback claims.

### Verdict
Clean — code, delegation against diffctx 1.9.1, and docs all hold; no fixes.

_Scouts/synthesis: folded (small scope, unchanged source, deterministic checks)_
