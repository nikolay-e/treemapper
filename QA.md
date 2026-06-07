# treemapper — QA Playbook

Project-specific QA notes. Generic patterns live in the global QA skill — do
not duplicate here.

## Applicability Matrix

| Check | Applies | Notes |
|---|---|---|
| Test suite | yes | `pytest` — integration only, real fs + real git repos |
| Pre-commit | yes | black, ruff, mypy (mypy scoped to `src/` only) |
| CLI smoke | yes | See CLI Smoke + Wheel E2E below |
| Wheel build + clean-venv install | yes | The critical check — see below |
| Code review | yes | Tiny surface (cli.py, __init__.py) |
| CI status | not yet | No git remote / CI wired as of 2026-06-07 |
| SonarCloud | no | `nikolay-e_treemapper` returns "Project not found" |
| autoqa / K8s / browser / ZAP / backend | no | Pure CLI library, no HTTP/UI/cluster |

## What treemapper is

Thin DRY wrapper over the `diffctx` engine (`diffctx>=1.7,<2.0`). `cli.py`
delegates to `diffctx.main.main()`; `__init__.py` re-exports the public API.
**Do not test engine algorithm quality here** (relevance filtering, garbage
exclusion) — that belongs to diffctx's own suite. treemapper tests verify the
wrapper contract: delegation works, `--version` is branded, formats render,
the Python API is re-exported, the console script and `-m` entry run.

## Wheel Build + Clean-Venv E2E (the important one)

Because treemapper depends on the *published* diffctx, the real risk is the
dependency-resolution + delegation path, not the source. Validate against a
clean venv that pulls diffctx from the index, not the dev editable install:

```bash
cd ~/treemapper && rm -rf dist && python -m build --wheel
python3 -m venv /tmp/tm-clean
/tmp/tm-clean/bin/pip install dist/treemapper-*.whl     # pulls diffctx + pathspec from PyPI
/tmp/tm-clean/bin/treemapper --version                  # → treemapper 2.0.0
# in a real git repo:
/tmp/tm-clean/bin/treemapper . -f yaml
/tmp/tm-clean/bin/treemapper . --diff HEAD~1
/tmp/tm-clean/bin/treemapper graph .
/tmp/tm-clean/bin/treemapper-mcp                         # graceful hint, exit 0, no traceback
```

## Gotchas

- **mypy hook scope**: `[tool.mypy]` is `files=["src"]`, but the
  `mirrors-mypy` pre-commit hook defaults to all passed `.py` files and its
  isolated env lacks pytest/types-pyyaml. Pin the hook with `files: ^src/` so
  it matches the pyproject scope; tests are integration tests, not strict-typed.
- **Dev install pollutes the diffctx venv**: `pip install -e .` from inside the
  shared `diffctx/.venv` adds treemapper there. Harmless for diffctx tests
  (separate `testpaths`), but prefer a dedicated venv for treemapper dev.
- **Known cosmetics** (display-only, see CLAUDE.md): `--help` shows the
  `diffctx` prog name; `treemapper-mcp` install hint says `diffctx[mcp]`.
