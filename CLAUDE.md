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
- **Forward-compatible fallback:** if the installed `diffctx` predates 1.8.0
  (no `run`), `cli.py` falls back to `diffctx.main.main()` plus a `--version`
  short-circuit. Tree/`--diff`/`graph` still work; only `--help` and the MCP
  hint show the `diffctx` name until the engine is upgraded. The fallback is
  what lets TreeMapper ship against the currently-published `diffctx` (1.7.1).
- `mcp_main.py` calls the engine MCP entry with `prog="treemapper-mcp"` /
  `extra="treemapper[mcp]"` (also falls back gracefully on diffctx < 1.8).
- `__init__.py` re-exports the public engine API so `import treemapper` mirrors
  `import diffctx` for library users.
- Entry points: `treemapper` → `treemapper.cli:main`,
  `treemapper-mcp` → `treemapper.mcp_main:main`.

## Dependency contract

- `diffctx>=1.7,<2.0`. Full branding needs `diffctx>=1.8.0` (the `run(prog=…)`
  entry); against 1.7.1 the fallback path keeps everything functional. Once
  diffctx 1.8.0 is published, the pin may be tightened to `>=1.8,<2.0` to drop
  the fallback. Extras pass through: `treemapper[tree-sitter]`,
  `treemapper[mcp]`, `treemapper[full]` install the matching `diffctx` extras.
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
