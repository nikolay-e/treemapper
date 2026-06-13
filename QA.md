# treemapper — QA Playbook

Project-specific QA notes. Generic QA patterns live in the `/qa` skill — do not
duplicate here. The mechanics of wheel + clean-venv E2E, mypy hook scope, and
mypy `additional_dependencies` (published-deps-only) live in the skill's
**Packaging QA** section; this file records only the treemapper-specific shape.

## Applicability Matrix

| Check | Applies | Notes |
|---|---|---|
| Test suite | yes | `pytest` — integration only, real fs + real git repos |
| Pre-commit | yes | black, ruff, mypy (mypy scoped to `src/` only) |
| CLI smoke | yes | See CLI Smoke + Wheel E2E below |
| Wheel build + clean-venv install | yes | The critical check — see below |
| Code review | yes | Tiny surface (cli.py, __init__.py) |
| CI status | yes | `.github/workflows/ci.yml` runs `pytest`. Installs the *published* diffctx, so it exercises the fallback path |
| SonarCloud | no | `nikolay-e_treemapper` returns "Project not found" |
| autoqa / K8s / browser / ZAP / backend | no | Pure CLI library, no HTTP/UI/cluster |

## What treemapper is

Thin DRY wrapper over the `diffctx` engine (`diffctx>=1.7,<2.0`). `cli.py`
delegates to `diffctx.run(prog="treemapper", version=…)` (diffctx >= 1.8.0),
falling back to `diffctx.main.main()` on older engines; `__init__.py`
re-exports the public API.
**Do not test engine algorithm quality here** (relevance filtering, garbage
exclusion) — that belongs to diffctx's own suite. treemapper tests verify the
wrapper contract: delegation works, `--version` is branded, formats render,
the Python API is re-exported, the console script and `-m` entry run.

## Wheel Build + Clean-Venv E2E — treemapper specifics

See `/qa` skill: Packaging QA for why an editable install can't prove the
published artifact works. treemapper's twist: it depends on the *published*
diffctx, so the real risk is the dependency-resolution + delegation path. The
clean venv must pull diffctx from the index, not the dev editable install:

```bash
cd ~/treemapper && rm -rf dist && python -m build --wheel
python3 -m venv /tmp/tm-clean
/tmp/tm-clean/bin/pip install dist/treemapper-*.whl     # pulls diffctx + pathspec from PyPI
/tmp/tm-clean/bin/treemapper --version                  # → treemapper 2.0.0
# in a real git repo:
/tmp/tm-clean/bin/treemapper . -f yaml
/tmp/tm-clean/bin/treemapper . --diff HEAD~1
/tmp/tm-clean/bin/treemapper graph .
/tmp/tm-clean/bin/treemapper-mcp                         # graceful hint, no traceback (exit 2 when the mcp extra is absent — engine's exit code, not overridden)
```

## Gotchas

- **mypy hook scope** (see `/qa` skill: Packaging QA): `[tool.mypy]` is
  `files=["src"]` but the `mirrors-mypy` hook defaults to all passed `.py`
  files — pin the hook with `files: ^src/` so it matches the pyproject scope;
  tests are integration tests, not strict-typed.
- **mypy hook must NOT pin diffctx in `additional_dependencies`** (see `/qa`
  skill: Packaging QA — the hook can only install the *published* dep):
  TreeMapper develops against the unreleased diffctx 1.8.0 (`run`/branded mcp),
  but the hook can only install published diffctx (1.7.1), which lacks those
  symbols → version skew (`has no attribute run`). Leave diffctx out of the hook
  and rely on `[[tool.mypy.overrides]] module=["diffctx.*"]
  ignore_missing_imports = true` (hook → `Any`); the authoritative check is the
  local/CI `mypy src` against the real installed diffctx. Re-add the pin only
  after diffctx 1.8.0 is on PyPI.
- **Branding is version-gated**: `--help` / `--version` / MCP-hint branding
  needs `diffctx>=1.8.0`. Against published 1.7.1 the fallback path keeps
  everything functional but `--help` and the mcp hint still show `diffctx`.
  Verify full branding with the local editable diffctx (1.8.0); verify the
  fallback with the clean-venv wheel install (pulls 1.7.1).
- **Dev install pollutes the diffctx venv**: `pip install -e .` from inside the
  shared `diffctx/.venv` adds treemapper there. Harmless for diffctx tests
  (separate `testpaths`), but prefer a dedicated venv for treemapper dev.

---

Generic QA patterns live in the `/qa` skill — do not duplicate here.
