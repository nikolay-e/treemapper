# PRODUCT.md — Product Audit (intended vs actual behavior)

Append-only cumulative log. Each run layers on top; do not rewrite prior entries.

---

## Run 2026-06-20 — commit 970006c (v2.1.0)

**Scope:** whole repo (treemapper product layer, 55 LOC of source over the `diffctx` engine).

**External contract:** present and human-written — `README.md` (usage + Python API),
`CLAUDE.md` (architecture + dependency contract), `CHANGELOG.md` (2.1.0/2.0.0 promises),
`--help`/`--version` text, `pyproject.toml` entry points. This is NOT the "no external
contract" case; findings below are graded against those written sources.

**Headline: the product conforms to its written contract.** Every behavior promised in
README/CHANGELOG/CLAUDE.md is present and correctly branded as `treemapper`. No 🔴 (no
missing-required-behavior, no broken contract), no 🟡. Two minor 🔵 observations and a set
of do-not-change invariants for the leverage pass. Findings are deliberately thin — that is
the correct result for a faithful thin-delegation wrapper, not an under-run.

### What was checked and verified PRESENT (intended ↔ actual)

- **Branding** — README/CHANGELOG promise `--help`/`--version`/errors say `treemapper`.
  Actual: `python -m treemapper --version` → `treemapper 2.1.0`; `--help` → `usage: treemapper`,
  no `diffctx` leakage (`cli.py:9` passes `prog="treemapper", version=__version__`). ✓
- **All documented flags/modes delivered** — `-f json/md/txt`, `--no-content`, `--save`
  (writes `tree.md`, verified), `-c` clipboard, `--diff <range>`, `graph` subcommand (mermaid,
  verified) all present in the branded surface (`README.md:28-38`). ✓
- **CHANGELOG 2.1.0 diff-context promises** — `role: "changed"` marker + `changed_files`
  orientation header verified in real output of `treemapper . --diff HEAD~1`. `commit_message`
  is conditional (present for commit-bearing ranges e.g. `HEAD~1..HEAD`, emitted by all three
  format writers `writer.py:118/205/338`) — "at the top of every format" means every *output
  format*, claim holds. ✓
- **Branded MCP install hint** — `CHANGELOG:24-25` promises `treemapper-mcp` hint branded via
  engine `prog`/`extra`. Actual with `[mcp]` absent: `treemapper-mcp: missing optional
  dependencies for MCP server mode. Install with: pip install 'treemapper[mcp]'`
  (`mcp_main.py:7`). ✓
- **Python API examples run** — `treemapper.map_directory(".", no_content=False)` and
  `treemapper.build_diff_context(root_dir=".", diff_range="HEAD~1")` (README:53-60) both execute
  against a real repo, including the README's `str` `root_dir` (engine annotates `Path`, accepts `str`). ✓
- **Dependency-contract conformance** — installed `diffctx==1.9.1` exposes `run(argv, *, prog,
  version)`, `mcp.__main__.main(prog, extra)`, and all re-exported symbols; the `>=1.9.1,<2.0`
  floor in `pyproject.toml` matches the live signatures the wrapper calls. ✓
- **Version consistency** — `version.py` `2.1.0` = CHANGELOG top entry = `--version` output;
  single-sourced via `[tool.hatch.version]`. ✓
- **Tests green** — 13 passed; integration-only, drive the real CLI end-to-end. ✓

### Findings

**🔵 README "Python API" section omits `run` from the documented surface.**
`run` is exported (`src/treemapper/__init__.py:6,19`, in `__all__`) and is a tested public API
(`tests/test_api.py:16` — `assert treemapper.run is diffctx.run`); `CLAUDE.md` architecture
section lists it among re-exports. But `README.md:51-60` "Python API" shows only
`map_directory`, `to_yaml`, `build_diff_context`. Intended-or-not: the export is deliberate
(git `d4216b0 "export run"`) and tested, so this is a doc-completeness gap, not a missing
behavior. *Acceptance:* README Python-API section mentions `treemapper.run` (or explicitly scopes
itself as illustrative). Decide keep-as-is vs document.

**🔵 `treemapper-mcp` exits 0 when MCP deps are missing.**
`mcp_main.py:7` delegates to the engine, which prints the branded hint and returns success
(observed exit `0`). No written intent says it must be nonzero, so this is an is-this-intended
question, not a contract break. Note: the behavior is **engine-owned** (`diffctx.mcp.__main__`);
per the repo's "never duplicate/override engine logic" rule any change belongs in `diffctx`, not
here. *Acceptance:* product decision — if a missing-dependency launch should signal failure to a
supervisor, fix the exit code in `diffctx` and bump the floor; otherwise leave as documented
graceful-hint behavior.

### Do-not-change invariants (name them so a later cleanup / `/review-leverage` cannot break them)

- **Entry-point script names** `treemapper` → `treemapper.cli:main`, `treemapper-mcp` →
  `treemapper.mcp_main:main` (`pyproject.toml scripts`). These ARE the public CLI contract.
- **`--version` exact format** `treemapper {__version__}` — encoded by `tests/test_cli.py:15-18`.
- **Public `__all__` set** including `run` (`__init__.py:15-24`) — encoded by `tests/test_api.py:10-17`;
  `import treemapper` is contracted to mirror the engine API.
- **diffctx pin `>=1.9.1,<2.0`** — the `>=1.9.1` floor is load-bearing: it guarantees the branded
  `run(prog=…)` entry (no unbranded fallback) and the 1.9 diff-context format
  (`role`/`changed_files`/orientation header) that CHANGELOG 2.1.0 promises. Do not relax the floor
  (`CLAUDE.md` "Dependency contract").
- **Single-source version** — `version.py` is the sole version source consumed by both hatchling
  (`[tool.hatch.version]`) and the CLI `--version`; keep them from forking.

### Opportunities

None promoted. The only candidates (MCP integration-test coverage; asserting the 1.9 diff format
in treemapper's own `--diff` test rather than just substring presence) are **test-coverage gaps,
not product gaps** — they belong to `/review-tests`, so they are not recorded here as opportunities.
