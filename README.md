# TreeMapper

[![PyPI](https://img.shields.io/pypi/v/treemapper)](https://pypi.org/project/treemapper/)
[![License](https://img.shields.io/pypi/l/treemapper)](https://github.com/nikolay-e/treemapper/blob/main/LICENSE)

**Map a codebase into LLM-ready context.** TreeMapper serializes an entire
directory tree — structure plus file contents — to YAML, JSON, Markdown, or
text, and selects the minimal smart git-diff context needed to understand a
change. Paste the output into Claude, ChatGPT, or any LLM.

TreeMapper is a thin command-line product built on the
[`diffctx`](https://pypi.org/project/diffctx/) engine. All traversal,
serialization, and diff-context selection live in `diffctx`; TreeMapper
re-exposes them under the `treemapper` name so there is a single source of
truth and no duplicated logic.

## Installation

```bash
pipx install treemapper                  # recommended: isolated, no venv needed
pip install treemapper                   # or with pip
pip install 'treemapper[tree-sitter]'    # + AST parsing for smarter diff context
pip install 'treemapper[mcp]'            # + MCP server for AI assistants
```

## Usage

```bash
treemapper .                     # map current directory to YAML (stdout)
treemapper /path/to/project      # map a specific directory
treemapper . -f json             # output as JSON
treemapper . -f md --save        # save as tree.md
treemapper . --no-content        # structure only, no file contents
treemapper . -c                  # copy output to clipboard
treemapper . --diff HEAD~1       # smart context for the last commit
treemapper . --diff main..HEAD   # smart context for a branch range
treemapper graph .               # project dependency graph (mermaid)
```

### Two modes

- **Tree mapping** (`treemapper .`) — walks the directory tree, respects
  hierarchical ignore patterns (`.gitignore`, `.diffctx/ignore`), reads file
  contents with binary/encoding detection, and serializes the result.
- **Diff context** (`treemapper . --diff`) — analyzes a git diff and selects
  the minimal set of code fragments needed to understand the change, instead
  of dumping whole files.

Run `treemapper --help` for the full flag reference.

## Python API

```python
import treemapper

tree = treemapper.map_directory(".", no_content=False)
print(treemapper.to_yaml(tree))

context = treemapper.build_diff_context(root_dir=".", diff_range="HEAD~1")
```

## Relationship to diffctx

TreeMapper is the user-facing distribution; `diffctx` is the reusable engine.
Pin compatibility is `diffctx>=1.7,<2.0`. If you are embedding the engine in
your own tool, depend on `diffctx` directly.

## License

Apache 2.0
