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
    cli.py        ──delegates──▶    diffctx.main:main    (full CLI: tree, --diff, graph)
    __init__.py   ──re-exports──▶   diffctx.{map_directory, build_diff_context, to_*}
    version.py                       diffctx.mcp.__main__:main  (treemapper-mcp script)
```

- `cli.py` delegates execution to `diffctx.main.main()` so TreeMapper inherits
  the entire engine CLI surface (tree mapping, `--diff`, the `graph`
  subcommand) without re-declaring it. The only TreeMapper-specific behavior is
  a `-v/--version` short-circuit that prints TreeMapper's own version.
- `__init__.py` re-exports the public engine API so `import treemapper` mirrors
  `import diffctx` for library users.
- Entry points: `treemapper` → `treemapper.cli:main`,
  `treemapper-mcp` → `diffctx.mcp.__main__:main`.

### Known cosmetic limitation

Because execution is delegated to `diffctx.main.main()`, `treemapper --help`
renders examples using the `diffctx` program name. `treemapper --version` is
correctly branded. A clean fix would be a public `diffctx.run(prog=...)` entry
in the engine; until then the delegation is intentional to keep this layer DRY.

## Dependency contract

- `diffctx>=1.7,<2.0`. Extras pass through: `treemapper[tree-sitter]`,
  `treemapper[mcp]`, `treemapper[full]` install the matching `diffctx` extras.
- `cli.py` depends on `diffctx.main.main` — the engine's stable console-script
  entry point. Avoid reaching into `diffctx`'s private (`_`-prefixed) helpers;
  if you need something they expose, ask for a public engine API instead.

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
