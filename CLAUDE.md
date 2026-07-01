# treemapper

## What this is

TreeMapper is the **product layer** — a thin command-line distribution built on
top of the [`diffctx`](../diffctx) engine. It exists so the established
`treemapper` PyPI name keeps shipping a user-facing CLI while all real logic
lives in one place.

**The guiding rule: never duplicate engine logic here.** Directory traversal,
ignore handling, serialization (YAML/JSON/text/Markdown), git-diff context
selection, the dependency graph, tokenization, and the clipboard are all owned
by `diffctx`. TreeMapper imports them. If you find yourself reimplementing any
of that in this repo, stop — extend or fix `diffctx` instead.

## Architecture

```
treemapper (this repo)              diffctx (engine, PyPI dependency)
  src/treemapper/
    cli.py        ──delegates──▶    diffctx.run(prog="treemapper", version=…)  (tree, --diff, graph)
    mcp_main.py   ──delegates──▶    diffctx.mcp.__main__:main(prog=…, extra=…)  (treemapper-mcp)
    __init__.py   ──re-exports──▶   diffctx.{map_directory, build_diff_context, run, to_*}
    version.py
```

- `cli.py` calls `diffctx.run(argv, prog="treemapper", version=__version__)`
  (added in diffctx 1.8.0), which runs the entire engine CLI surface (tree
  mapping, `--diff`, the `graph` subcommand) under TreeMapper's own program
  name and version — `--help`, `--version`, and error prefixes are all branded.
  No CLI is re-declared here.
- `mcp_main.py` calls the engine MCP entry with `prog="treemapper-mcp"` /
  `extra="treemapper[mcp]"`.
- `__init__.py` re-exports the public engine API so `import treemapper` mirrors
  `import diffctx` for library users.
- Entry points: `treemapper` → `treemapper.cli:main`,
  `treemapper-mcp` → `treemapper.mcp_main:main`.

## Dependency contract

- `diffctx>=1.10.1,<2.0`. The floor guarantees the `run(prog=…)` entry (so
  `--help`/`--version`/errors are always branded as `treemapper` — no fallback
  path) and the diff-context orientation header + changed/context role ordering
  shipped in diffctx 1.9.x. The `>=1.10.1` bump pulls in the diffctx 1.10 engine
  (calibrated default `--tau` 0.12, the 256 KB MCP file cap, the
  document/import edge correctness fixes) plus the 1.10.1 fix that stops the
  postpass fallback from hiding real diff content. Extras pass through:
  `treemapper[tree-sitter]`, `treemapper[mcp]`, `treemapper[full]` install the
  matching `diffctx` extras.
- Depend only on diffctx's **public** API (`run`, `map_directory`,
  `build_diff_context`, `to_*`, `mcp.__main__.main`). Never reach into
  `_`-prefixed helpers; if you need something they expose, add a public engine
  API in `diffctx` instead.

## Development

```bash
pip install -e ".[dev]"
pytest
pre-commit run --all-files
```

## Testing

Integration tests only — real filesystem, real git repos, no mocking. Tests
run the `treemapper` CLI end to end and assert on its output, which also acts
as a tripwire: if a `diffctx` upgrade breaks the delegation contract, these
tests fail loudly.

## License

Apache 2.0
