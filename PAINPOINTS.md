# PAINPOINTS — /review-painpoints research log (append-only)

Sourced complaints about competitors in the **"codebase → LLM context /
repo-to-text/prompt"** category, mapped to treemapper's current status. Every
finding carries a quote + URL. Ranked by frequency × severity.

Severity: 🔴 dealbreaker (users abandon over it) · 🟡 recurring friction · 🔵 wish.

---

## 2026-06-14 · 376adb5 · category audit (Repomix, code2prompt, files-to-prompt, yek, gpt-repository-loader, gitingest, uithub, repo2txt)

### Category & competitors

treemapper = CLI that serializes a repo to YAML/JSON/MD/text for LLMs, plus a
**smart git-diff context** mode (selects minimal code fragments for a change, not
whole files). Real alternatives users compare against:
- **CLI-native:** Repomix (yamadashy, the market leader), code2prompt (Rust),
  files-to-prompt (simonw), yek (Rust), gpt-repository-loader (OpenAI, stale).
- **Web/URL:** gitingest, uithub, repo2txt, ai-digest, codefetch.

Our status assessed against the shipped `diffctx` 1.9.1 engine (exact tiktoken
token counts, opt-in clipboard, default ignores, `--diff` fragment selection,
Python API). Verified by reading `diffctx/ignore.py`, `tokens.py`, `main.py`.

### 🔴 Dealbreakers (highest-frequency, cross-source)

1. **Whole-repo dump blows past the context window — manual chunking is the
   workaround.** THE #1 structural complaint, every competitor, every source.
   "the codebase exceeds the 128k token limit by a wide margin—sometimes up to
   ten times more … Manually chopping the output into smaller pieces is tedious"
   ([repomix#424](https://github.com/yamadashy/repomix/issues/424)). Quantified:
   one repo → ~56M (Repomix) / 69.2M (gitingest) tokens
   ([HN 42329071](https://news.ycombinator.com/item?id=42329071)). "Just throwing
   an entire codebase into an LLM … seems like a fools errand"
   ([HN 46354970](https://news.ycombinator.com/item?id=46354970)).
   **Our status: this is our core wedge** — `treemapper . --diff` selects minimal
   fragments + `--no-content` (structure only) + `graph`. Lead positioning with it.

2. **No smart relevance selection — tool dumps everything, user filters by hand.**
   Category-wide. "The selection of the files is key here … to let the LLM focus
   on what is important" ([HN 42753302](https://news.ycombinator.com/item?id=42753302)).
   Repomix users explicitly ask for import-aware bundling: "read current directory
   files and imported files also … you don't need the whole code base"
   ([repomix#478](https://github.com/yamadashy/repomix/issues/478), among the
   most-commented). **Our status: addressed** by `--diff` (ego/multi-hop scoring)
   + `graph`. Biggest differentiator — no CLI competitor in this set has it.

3. **Diff-aware / changed-files-only output is an explicit competitor WISH we
   already ship.** Repomix [#339](https://github.com/yamadashy/repomix/issues) asks
   for "a difference-based output format for comparing changes";
   [discussion #291](https://github.com/yamadashy/repomix/discussions/291) wants
   before/after of staged changes; pr-agent [#1445](https://github.com/qodo-ai/pr-agent/issues/1445)
   proposes configurable "context-by-diff, context-by-file, or both". Competitors
   that do have git support only *dump the raw diff* (Repomix `--include-diffs`);
   raw diff is a poor LLM input — "mixes line-number metadata with text"
   ([Medium](https://medium.com/@yehezkieldio/precision-dissection-of-git-diffs-for-llm-consumption-7ce5d2ca5d47)).
   **Our status: shipped & differentiated** — we select & expand fragments, not
   pass-through diff. Frame as "the diff context Repomix users keep asking for."

4. **code2prompt forces clipboard even with `-o` — breaks headless/SSH.** Loudest
   code2prompt gripe. "even if you specified an output file, it will always put the
   output to the paste buffer" ([HN 41488949](https://news.ycombinator.com/item?id=41488949));
   "Could a flag be added to skip copying … on a remote without a clipboard"
   ([code2prompt#15](https://github.com/mufeedvh/code2prompt/issues/15)).
   **Our status: avoided** — clipboard is opt-in (`-c`); default is stdout/`--save`.

5. **`.gitignore` handling broken both ways — silent wrong output / secret leaks.**
   files-to-prompt over-included 19,929 lines of ignored `staticfiles/`
   ([#46](https://github.com/simonw/files-to-prompt/issues/46)) and mishandles
   nested `.gitignore` ([#40](https://github.com/simonw/files-to-prompt/issues/40));
   Repomix silently ignores `.gitignore` when targeting a subdirectory
   ([#776](https://github.com/yamadashy/repomix/issues/776)) and doesn't merge
   ignore sources ([#959](https://github.com/yamadashy/repomix/issues/959));
   code2prompt's `--no-ignore`/`--exclude` silently no-op
   ([#8](https://github.com/mufeedvh/code2prompt/issues/8),
   [#34](https://github.com/mufeedvh/code2prompt/issues/34),
   [#111](https://github.com/mufeedvh/code2prompt/issues/111)).
   **Our status: structurally safer** (hierarchical ignore in diffctx, default
   patterns cover node_modules/locks/build/.git). **Cheap insurance:** add a
   regression test asserting nested-`.gitignore` correctness so we never inherit
   this bug class.

### 🟡 Recurring friction & real gaps

6. **No secret scanning / redaction — `.env`, keys, `*.pem` flow straight into LLM
   output.** Repomix is repeatedly singled out as the *only* one that scans:
   "built-in security check that flags hardcoded secrets" via Secretlint
   ([openreplay](https://blog.openreplay.com/git-repos-llm-ready-text/)); gitingest
   had a real exploited arbitrary-file-read CVE-2024-56074 that dumped SSL certs
   ([nollium](https://blog.nollium.com/finding-and-fixing-an-arbitrary-file-read-vulnerability-in-gitingest-cve-2024-56074-ce1cdcbc645c)).
   **Our status: GAP (verified).** `diffctx/ignore.py:236` `DEFAULT_IGNORE_PATTERNS`
   covers build/vcs/locks but **contains no `.env*`, `*.pem`, `*.key`, `id_rsa`,
   `credentials.*`** and there is no content redaction — `treemapper .` will
   serialize a committed `.env` into the paste. **Highest-ROI opportunity & a
   footgun for our own users.** Fix belongs in the **engine (diffctx)**: add secret
   filename patterns to default ignores (low effort, big win) and consider an
   opt-out redaction pass. Flag upstream; do not duplicate logic here.

7. **Char-based token estimates are inaccurate; users want real counts.**
   files-to-prompt has no token counting ([#65](https://github.com/simonw/files-to-prompt/issues/65));
   char/4 estimators "consistently underperform"
   ([HN 42753302](https://news.ycombinator.com/item?id=42753302)).
   **Our status: STRONG — beat them.** diffctx prints exact tiktoken counts
   (`o200k_base`, Rust backend) on every run (`tokens.py` → `main.py:319`). Make
   this a README selling point ("exact token counts, not estimates").

8. **No library/programmatic API — CLI-only.** Recurring Repomix ask:
   "I would be interested in using this tool as a library with an API"
   ([repomix#257](https://github.com/yamadashy/repomix/issues/257), high reactions).
   **Our status: solved by design** — the diffctx-engine / treemapper-product split
   gives `import treemapper; map_directory(...)`, `build_diff_context(...)`. Sell it.

9. **Slow on large repos.** Rust tools hit "5-second … compared to Repomix's 22
   minutes on large repositories like Next.js"; Repomix's v1.14.0 "cut pack time
   58% in response to speed criticism"
   ([rywalker](https://rywalker.com/research/code-intelligence-tools)). gitingest
   "failed to process the Linux kernel" / hits a 10k file cap
   ([HN 42329071](https://news.ycombinator.com/item?id=42329071),
   [gitingest#196](https://github.com/coderamp-labs/gitingest/issues/196)).
   **Our status: partial advantage** — diffctx has a Rust core; `--diff` avoids
   walking the whole repo. Worth a large-repo smoke benchmark.

10. **Install/runtime friction.** code2prompt Rust/Cargo build barrier
    ([HN 41023269](https://news.ycombinator.com/item?id=41023269)); Repomix macOS
    clipboard crash "spawnSync sysctl ENOENT"
    ([repomix#193](https://github.com/yamadashy/repomix/issues/193)); files-to-prompt
    Windows recursion broken ([#62](https://github.com/simonw/files-to-prompt/issues/62)),
    UTF-8 wrongly dropped ([#55](https://github.com/simonw/files-to-prompt/issues/55)).
    **Our status: good** — `pipx install treemapper`, pure wheel, opt-in clipboard
    with a clear error+hint. **Cheap insurance:** a Windows-path recursion test.

### 🔵 Wishes / notes

11. **XML output format.** Repomix defaults to XML citing Anthropic guidance
    ([repomix output guide](https://repomix.com/guide/output)). **But the evidence
    says this is NOT a real pain** — XML vs Markdown is "doesn't make much of a
    difference" ([OpenAI community](https://community.openai.com/t/xml-vs-markdown-for-high-performance-tasks/1260014));
    benchmarks: Markdown ≈ XML, "JSON consistently underperformed". We already have
    Markdown (the mild winner). Adding XML neutralizes a *marketing* claim only —
    low-priority parity item, not an adoption blocker.
12. **Don't market JSON as the AI-optimal format** — it benchmarks worst of the
    common formats; position YAML/Markdown as the LLM-facing defaults.
13. Multiple/named configs in one file (repomix#325); semantic/signature
    compression (code2prompt#315); reverse/scaffold mode (yek#64). Backlog only.

### False positives / negative results (don't chase)
- **XML gap** — looks like a Repomix advantage; the format-performance literature
  says it's negligible. Skip unless trivially cheap for parity.
- **uithub-specific complaints** — no quotable Reddit/HN gripe threads surfaced;
  not fabricated into findings.
- **"secrets leaking" as a literal competitor *complaint*** — the evidence is
  (a) the gitingest CVE and (b) Repomix marketing its scanner, not users raging in
  threads. The risk is real (and we have the gap), but it's inferred from product
  posture, not a frequency-of-complaint signal — rated 🟡, not 🔴.

### ROI ranking (impact / effort) — actionable for us
1. **Secret leakage (#6)** — **PARTLY DONE** in diffctx `a7bc751c` (Unreleased).
   Investigation found two things: (a) the `--diff` path applied **no** ignore
   filtering at all (Rust backend: "not yet implemented"), so a changed key/`.env`
   leaked verbatim — worse than tree mode; (b) the engine **deliberately** treats
   a changed `.env` as legitimate change context (cases
   `algorithm_003_fragment_env_file_change`, `fragments_021` *require* it).
   - **Fixed:** private-key/keystore files (`*.pem`/`*.key`/`*.pfx`/`*.p12`/
     `*.keystore`/`*.jks`, `id_rsa`/`id_dsa`/`id_ecdsa`/`id_ed25519`; public
     `.pub` kept) are now excluded in **both** tree and `--diff` output — never
     legitimate context. Provably zero regression (no test case contains such a
     file); full Rust suite baseline unchanged (467 pre-existing relevance-frontier
     fails, ±0), 413 Python tests pass, new `test_secret_ignores_diff` +
     `test_default_private_key_ignores` added.
   - **Open decision:** `.env` secret *values*. A blunt filename ignore would
     hide legitimately-changed config and contradicts the engine's design; the
     right fix is a content-based redaction pass (also catches secrets hardcoded
     in `.py`/`.yaml`). Deferred pending product call.
   - **Delivery to treemapper users** still needs a diffctx release + `diffctx>=`
     pin bump here (outward/PyPI action, awaiting go-ahead).
2. **README: lead with `--diff` smart context + exact token counts + Python API**
   (#1,#3,#7,#8) — *Easy*, all already shipped, just under-marketed.
3. **Regression tests: nested-`.gitignore`, Windows recursion** (#5,#10) — *Easy*,
   pure insurance against the competitors' loudest bug classes.
4. **Large-repo smoke benchmark** (#9) — *Medium*, validates the speed story.

### Verdict
treemapper already *avoids or beats* the four loudest category pains — whole-repo
token blowout, no smart selection, forced clipboard, and inaccurate token counts —
and ships the diff-aware mode competitors keep requesting. The single genuine gap
is **no secret-aware filtering** (engine-side, Easy fix). The rest is a marketing
problem: real strengths that the README doesn't yet sell.

_Scouts/synthesis: 4 web-research scouts (Repomix · CLI cluster · web/URL cluster
· diff+format axis; a 5th category-wide scout rate-limited, its themes covered by
the others) / synthesis folded into main agent with direct code verification of
"our status" against diffctx 1.9.1._
