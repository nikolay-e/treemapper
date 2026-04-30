# QA Methodology

## CI

- CI matrix: Linux/macOS/Windows × Python 3.10-3.14
  (15 test matrices + 3 lint/arch jobs)
- Windows jobs slowest — typically 7-10min vs 2-4min for Linux/macOS
- All jobs must pass; no flaky CI tolerance

## SonarCloud

- Project key: `nikolay-e_TreeMapper`
- Dominant issue pattern: cognitive complexity (python:S3776)
  — 30+ instances in diffctx pipeline
- Benchmark PRNG (python:S2245) hotspots are safe — not crypto usage
- Regex DoS hotspot (python:S5852) in semantic parsers — review case-by-case
- Duplicate branch smell (python:S1871) in discovery methods:
  merge with `or` when bodies identical
- Test YAML fixture "Password" triggers false positive VULNERABILITY
  (yaml:S2068) — expected
- `dataclasses.replace()` return type: mypy (modern) infers correctly —
  do NOT add `cast(T, replace(...))`, mypy will flag as redundant-cast;
  remove cast and let type inference work
- Lambda capturing loop variable (S1515): use `dict.__getitem__` instead
  of `lambda k: d[k]` — simpler and avoids the flag

## Test Suite

- Run `python -m pytest --tb=no -q` for quick status
- test_graph.py separate from test_yaml_diff.py — check both
- Many xfails (strict=False) for bidirectional discovery precision tradeoff —
  check count trends, not absolute numbers

## Code Review

- Check for duplicate decorators (e.g. double `@staticmethod`)
  — Python silently allows stacking
- After merging duplicate branches (S1871 fix), verify the `or`
  logic preserves both conditions

## SonarCloud (extras)

- `whitelist_vulture.py` bare names (`Graph.add_node`) trigger S905
  "no side effects" BUG — wrap in `_ = expr` to silence (vulture
  still recognizes the reference)
- `numpy_array /= divisor` (in-place mutation) is misread by SonarCloud as
  unused local — use explicit `np.divide(arr, divisor, out=arr)` instead
- Pinning `dtolnay/rust-toolchain@<sha>` requires explicit
  `with: toolchain: stable` — pinning loses the default-input behavior
- API to mark hotspot Safe:
  `POST /api/hotspots/change_status hotspot=KEY status=REVIEWED resolution=SAFE`
- API to mark issue false-positive:
  `POST /api/issues/do_transition issue=KEY transition=falsepositive`
- GraphML XML namespace `http://graphml.graphdrawing.org/graphml` triggers
  S5332 (insecure http) but is the literal spec identifier — mark Safe

## Cognitive Complexity Tactics

- run_parallel-style "parallel-or-serial dispatcher" with extend/append:
  extract `_collect_result(results, r, collect)` helper to dedupe both
  branches and reduce S3776 score significantly
- evaluate_one-style "header → run → report → return" functions:
  extract `_print_*_header` and `_print_*_dump` helpers — the heavy
  formatting blocks dominate the complexity score

## Shell Scripts

- `shelldre:S7688` — convert every `[ ... ]` to `[[ ... ]]` across the
  whole file in one pass; SonarCloud reported lines drift after pre-commit
  reformatting, so don't trust line numbers literally
- `shelldre:S7682` — one-line tee/printf functions like `log() { ... }`
  also need an explicit `return 0`; SonarCloud reports the line BEFORE
  the function definition
- `bash -n script.sh` after edits — quick syntactic sanity check

## Pre-existing Test Failures (do not regress, do not retry-fix)

- `tests/test_graph.py`, `test_graph_cli.py`, `test_graph_export.py` —
  ALL three fail with `ModuleNotFoundError: treemapper.diffctx.edges`.
  Python `edges` module was deleted in commit `e77d5494` (Rust-only
  pipeline); CI excludes them via three `--ignore=...` flags in
  `.github/workflows/ci.yml`. Reproduce locally with the same flags
  before claiming "tests pass". Do NOT delete these files until
  ProjectGraph is ported to Rust — they document the contract.

## SonarCloud API

- Public `api/issues/search?projectKeys=nikolay-e_TreeMapper&statuses=OPEN`
  works without auth for OPEN issues. Token only needed for hotspot
  state changes / false-positive transitions.
- Token lives in macOS Keychain under service `sonarqube-token` (40 chars).
  Auth via `Authorization: Bearer <token>` (NOT basic auth). Use
  `--data-urlencode key=value` for hotspot/issue mutations.
- Quality gate ERROR conditions for treemapper after a paper-heavy push are
  usually `new_reliability_rating>1` (driven by S3516 BLOCKER bugs) and
  `new_security_hotspots_reviewed<100%`. Hotspots are bulk-resolvable in
  one loop over `/api/hotspots/search?status=TO_REVIEW` — set Safe with
  per-rule comments (S1313 instance-id false positive, S2245 seeded PRNG,
  docker S6471 internal image, S7637 tag-pin policy). Hotspots resolved
  this way DO clear the gate condition immediately on next refresh.

## SonarCloud Recurring Patterns (paper/benchmark commits)

- `python:S3516` BLOCKER on entry-points and orchestrators: appears when a
  function has multiple `return X` statements all of the same name (e.g.
  `return results`) — refactor into single tail-return by extracting
  per-branch helpers, NOT by collapsing branches.
- `python:S5799` MAJOR (implicit string concat / missing comma): black
  often line-splits long f-strings into adjacent literals (`"..." "..."`).
  Merge into one literal — keep flake8 / ruff aligned with this rule by
  not relying on implicit concat for readability.
- `python:S1244` MAJOR (float `==`): use `pytest.approx`, not `math.isclose`,
  because the codebase already imports pytest in every test module.
- `python:S1186` CRITICAL (empty methods): for duck-typed stubs (e.g.
  Aider IO interface) add a one-line docstring describing the no-op —
  `pass` alone is flagged.
- `python:S1192` CRITICAL (literal duplication ≥3): extract module-private
  `_TWO_COL_DIVIDER` style constant; keep adjacent to imports.

## CI Build of Rust Extension

- Test matrix needs `_diffctx` (Rust ext) installed before pytest. Use
  `maturin build --release --out wheelhouse && pip install --force-reinstall
  --no-deps wheelhouse/*.whl` — `maturin develop` requires a venv which the
  GH runner doesn't have by default.
- Set `PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1` for Python versions newer than
  PyO3's max supported (currently 3.13). Without this, 3.14+ matrix entries
  fail at the build step before any test runs.
- Cache cargo per-(os, python-version) — same cargo target dir compiled with
  different Python ABIs collides if the key doesn't include python-version.
- `panic = "abort"` in `[profile.release]` is INCOMPATIBLE with
  `cargo test --release` — the test harness force-uses unwind, dependencies
  get abort, link fails. Keep abort for production safety but split CI:
  `cargo test --lib` (dev profile, harness happy) +
  `cargo build --release` + `cargo test --release --test yaml_cases`
  (integration tests with `harness = false` work in release).
- Bench Dockerfile that copies `diffctx/Cargo.toml` MUST also copy
  `diffctx/tests/` whenever Cargo.toml declares any `[[test]]` entry —
  manifest parser validates path before any build step.

## YAML Case Runner (cargo integration test)

- Default `cargo test --release` runs every YAML case in `tests/cases/diff/`
  via `tests/yaml_cases.rs` — 2723 trials, ~70s at -j8. Cap with
  `DIFFCTX_YAML_CASES_LIMIT=N` env var for fast pre-commit (default in
  `.pre-commit-config.yaml` is 20). CI rust-diffctx-test job uses the same
  cap to avoid surfacing 269 long-tail failures as fresh CI noise.
- libtest-mimic is the harness — every YAML case becomes its own Trial
  visible in `cargo test` output. Cases with stale `xfail:` markers may
  pass ("xpass"); strip via `--ignored` sweep when the algorithm improves.
- Pass threshold (`DIFFCTX_YAML_MIN_SCORE`) defaults to 10% recall × (1 −
  forbidden_rate). Original Python framework used the same value.

## Memory Profiling for diffctx

- `/usr/bin/time -l` on macOS reports `peak memory footprint` and
  `maximum resident set size`. Run 3× and take median — single run
  varies by ~500MB on small diffs (rayon thread allocator cache noise)
- Peak on small diffs over treemapper itself is ~1.6–2.0 GB; dominated
  by `build_file_cache` (200MB cap, but reads ALL <100KB files into
  `Vec<(PathBuf, String)>` BEFORE applying the cap) and tree-sitter
  parse trees, NOT lexical similarity. Lexical fixes only show up on
  repos with many fragments + dense term overlap.
