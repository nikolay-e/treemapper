# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.1.0] - 2026-06-14

### Changed

- Bumped the dependency floor to `diffctx>=1.9.1,<2.0`. This pulls in the diffctx
  1.9 diff-context improvements for `treemapper . --diff`: an orientation header
  (`commit_message` + `changed_files`) at the top of every format, a `role:
  changed` marker on fragments overlapping the diff with changed code emitted
  first, context ordered by descending per-file relevance, and merging of
  line-contiguous same-role fragments. The `>=1.9.1` floor also remains a hard
  requirement for the branded `run(prog=…, version=…)` entry — the pre-1.8
  fallback path was removed, so there is no unbranded code path.
- `treemapper` drives the engine through the public
  `diffctx.run(prog="treemapper", version=…)` entry, so `--help`, `--version`,
  and error prefixes are branded as `treemapper`. The `treemapper-mcp` install
  hint is likewise branded via the engine's `prog`/`extra` parameters.

### Added

- GitHub Actions release workflow (`cd.yml`) that builds the pure wheel + sdist
  and publishes to PyPI via OIDC trusted publishing.

## [2.0.0]

### Changed

- **TreeMapper is now a thin wrapper over the [`diffctx`](https://pypi.org/project/diffctx/)
  engine.** All directory traversal, serialization, and git-diff context
  selection are delegated to `diffctx` (pinned `>=1.7,<2.0`). TreeMapper itself
  ships only the `treemapper` command, the `treemapper-mcp` server entry point,
  and a Python API that re-exports `map_directory`, `build_diff_context`, and
  the `to_yaml`/`to_json`/`to_text`/`to_markdown` serializers. No engine logic
  is duplicated.
- Pure-Python wheel (built with hatchling). The native engine arrives through
  the `diffctx` dependency.

### Note

Releases `1.0.0` through `1.6.1` shipped TreeMapper as a self-contained package;
that lineage was renamed to `diffctx` at `diffctx` `1.7.0`. TreeMapper `2.0.0`
re-establishes the `treemapper` name as the product layer on top of that engine.

[Unreleased]: https://github.com/nikolay-e/treemapper/compare/v2.1.0...HEAD
[2.1.0]: https://github.com/nikolay-e/treemapper/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/nikolay-e/treemapper/releases/tag/v2.0.0
