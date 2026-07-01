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
| CI status | yes | `.github/workflows/ci.yml` runs `pytest`. Installs the *published* diffctx, so it exercises the real dependency-resolution + delegation path |
| SonarCloud | no | `nikolay-e_treemapper` returns "Project not found" |
| autoqa / K8s / browser / ZAP / backend | no | Pure CLI library, no HTTP/UI/cluster |

## What treemapper is

Thin DRY wrapper over the `diffctx` engine (`diffctx>=1.10.1,<2.0`). `cli.py`
delegates to `diffctx.run(prog="treemapper", version=…)` — a hard requirement,
no fallback (the pre-1.8 fallback path was removed); `__init__.py` re-exports
the public API.
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
/tmp/tm-clean/bin/pip install dist/treemapper-*.whl     # pulls diffctx (>=1.10.1) from PyPI
/tmp/tm-clean/bin/treemapper --version                  # → treemapper 2.3.0
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
  skill: Packaging QA — the hook can only install the *published* dep): keep
  diffctx out of the hook and rely on `[[tool.mypy.overrides]]
  module=["diffctx.*"] ignore_missing_imports = true` (hook → `Any`); the
  authoritative check is the local/CI `mypy src` against the real installed
  diffctx, which is the published `>=1.10.1` engine that exposes every symbol
  the wrapper calls (`run`, branded mcp).
- **Branding is unconditional**: the `>=1.10.1` floor guarantees the
  `run(prog=…, version=…)` entry, so `--help` / `--version` / errors / the MCP
  hint are always branded as `treemapper`. There is no unbranded fallback path
  to verify — any diffctx satisfying the pin brands correctly.
- **Dev install pollutes the diffctx venv**: `pip install -e .` from inside the
  shared `diffctx/.venv` adds treemapper there. Harmless for diffctx tests
  (separate `testpaths`), but prefer a dedicated venv for treemapper dev.
- **`test_console_script_entry_point` fails locally without an editable
  install**: `pytest`'s `pythonpath = ["src"]` config makes in-process
  `import treemapper` work even with no install, but the test's own
  `subprocess.run([sys.executable, "-m", "treemapper", ...])` spawns a real
  Python process that does not inherit that pytest-only path — it needs
  treemapper actually installed. `pip install -e ".[dev]"` before running the
  suite locally; CI is unaffected (fresh venv always installs the package first).
- **`ci.yml` had drifted to tag-pinned actions (`@v7`, `@v6`, `@v8.2.0`) while
  `cd.yml`/`automerge.yml` were SHA-pinned** — inconsistent with this
  workspace's SHA-pinning convention. Fixed by pinning to the SHA each tag
  resolves to today, with the resolved version in the trailing comment (`actions
  setup-python@v6` → `v6.3.0`, since `v6` is a floating major tag that had moved
  past the `v6.2.0` pinned elsewhere in `cd.yml`). When auditing SHA pins,
  always resolve `# <tag>` comment against `gh api repos/<owner>/<repo>/git/refs/tags/<tag>`
  — dependabot bumps the SHA but does not always update a stale comment (caught
  `softprops/action-gh-release` pinned to the 3.0.1 SHA but still commented `# v2`).

---

Generic QA patterns live in the `/qa` skill — do not duplicate here.
