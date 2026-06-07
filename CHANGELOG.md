# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/nikolay-e/treemapper/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/nikolay-e/treemapper/releases/tag/v2.0.0
