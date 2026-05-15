# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.6.1] - 2026-05-15

### Fixed

- **`_diffctx` Rust extension was missing from PyPI wheels** — `pip install treemapper`
  previously shipped a pure-Python wheel that lacked the compiled Rust core, causing
  `treemapper . --diff HEAD~1..HEAD` (the headline diff-context mode) to crash with
  `ModuleNotFoundError: No module named '_diffctx'`. The build backend is now
  `maturin`, and CD builds and publishes ABI3 wheels for Linux (x86_64 + aarch64),
  macOS (x86_64 + arm64) and Windows (x86_64). Token counting (`tokens.py`) and
  language detection (`writer.py`) now use the Rust path on every install instead
  of silently degrading.
- CI no longer references three deleted test files (`tests/test_graph*.py`) via
  `--ignore` flags.

### Added

- Post-publish CD smoke job installs the freshly published wheel from PyPI on a
  clean runner and exercises `treemapper --version`, the tree-mapping mode, the
  Rust extension import (`from treemapper._diffctx import …`) and the diff-context
  mode end-to-end across {Linux, macOS, Windows} × Python {3.10, 3.13}. The
  release fails (and is not finalized as a GitHub Release) if the smoke test
  fails — preventing a recurrence of the silent-degradation defect above.
- Output-size warning: when an emitted tree-mapping output exceeds 10 MB, a
  stderr hint suggests using `--no-content` (structure only) or `--diff RANGE`
  (relevance-ranked context).
- `CHANGELOG.md` (Keep-a-Changelog 1.1.0 format).

### Changed

- `--max-file-bytes` default lowered from 10 MB to 256 KB to keep tree-mapping
  output bounded on large repos (cpython would previously produce ~133 MB of
  YAML with the old default). Use `--no-file-size-limit` to disable the
  per-file cap.
- `from _diffctx import …` paths refactored to `from treemapper._diffctx import …`
  (the Rust extension is now a submodule of the `treemapper` package). External
  consumers of the Python API are unaffected; this is purely an internal layout
  change required by the unified maturin wheel.

### Removed

- `Programming Language :: Python :: 3.14` classifier (CI runs 3.14 as
  best-effort only; classifier was premature).
- Unused optional-dependency groups `[embeddings]` (sentence-transformers) and
  `[nlp]` (spacy) — neither was imported anywhere in `src/`.
- Stale paper-track scaffolding: `PAPER_DEVIATIONS.md`, `QA.md`,
  `Dockerfile.bench`, `requirements-bench.{txt,lock}`, `sonar-project.properties`,
  `treemapper.spec` (PyInstaller spec), `whitelist_vulture.py`.
- PyInstaller binary build path in CD (was orphan after the Rust extension
  began shipping via wheels; binary distribution is deferred).

[1.6.1]: https://github.com/nikolay-e/treemapper/releases/tag/v1.6.1
