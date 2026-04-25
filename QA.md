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
