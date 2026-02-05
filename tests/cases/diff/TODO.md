# Diff Test Cases Enrichment

## Goal

Enrich all diff test cases with:

1. **Realistic code content** - larger, more representative code snippets
2. **Garbage files** - files with unique markers to test exclusion
3. **Proper diffctx format** - structured assertions

## File Structure

Each test case consists of 3 files:

- `{name}_before.yaml` - codebase state before the change
- `{name}_after.yaml` - codebase state after the change
- `{name}_diffctx.yaml` - assertions for diff context selection

## Garbage Marker Pattern

```
GARBAGE_{CATEGORY}_{NUM}_{DESCRIPTION}_{LETTER}
```

Examples:

- `GARBAGE_CICD_003_ROLLBACK_MARKER_A`
- `GARBAGE_ALGO_005_LOGGING_MARKER_B`

## diffctx Format

```yaml
must_include_files:
  - path/to/important/file.py
must_include_content:
  - |
    actual code block that must appear
must_not_include:
  - GARBAGE_MARKER_A
  - GarbageClassName
  - garbage_file.py
```

---

## Progress

### ✅ Completed

| Directory | Files | Test Cases | Status |
|-----------|-------|------------|--------|
| algorithm | 63 | 21 | ✅ Done |
| cicd | 45 | 15 | ✅ Done |

### 🔄 Remaining

| Directory | Files | Est. Cases | Priority |
|-----------|-------|------------|----------|
| cicd_and_docs | 234 | ~78 | High |
| comprehensive | 81 | ~27 | High |
| config | 15 | ~5 | Medium |
| cpp | 108 | ~36 | Medium |
| csharp | 78 | ~26 | Medium |
| dependencies | 123 | ~41 | High |
| docker | 135 | ~45 | High |
| fragments | 72 | ~24 | Medium |
| frontend | 90 | ~30 | High |
| go | 105 | ~35 | Medium |
| graph | 51 | ~17 | Medium |
| helm | 135 | ~45 | High |
| infrastructure_validation | 15 | ~5 | Low |
| internals | 195 | ~65 | Medium |
| java | 78 | ~26 | Medium |
| javascript | 255 | ~85 | High |
| javascript_extended | 147 | ~49 | Medium |
| json | 45 | ~15 | Low |
| jvm_and_compiled | 216 | ~72 | Medium |
| kubernetes | 120 | ~40 | High |
| merging | 36 | ~12 | Low |
| operations | 18 | ~6 | Low |
| output | 36 | ~12 | Low |
| patterns | 135 | ~45 | Medium |
| php | 60 | ~20 | Low |
| ppr | 105 | ~35 | Medium |
| python | 186 | ~62 | High |
| relations | 21 | ~7 | Low |
| ruby | 60 | ~20 | Low |
| rust | 120 | ~40 | Medium |
| scala | 78 | ~26 | Low |
| scripting | 90 | ~30 | Medium |
| selection | 24 | ~8 | Medium |
| shell | 75 | ~25 | Medium |
| swift | 60 | ~20 | Low |
| terraform | 240 | ~80 | High |
| typescript | 27 | ~9 | Medium |
| yaml | 60 | ~20 | Medium |

**Total remaining:** ~38 directories, ~1100+ test cases

---

## Process

For each test case:

1. **Read** all 3 files (before, after, diffctx)
2. **Check** if already enriched (look for garbage markers)
3. **Enrich** if minimal:
   - Add realistic code to before/after
   - Add 2 garbage files with unique markers
   - Update diffctx to proper format
4. **Write** updated files

## Notes

- Process one directory at a time
- Use consistent garbage marker naming per directory
- Keep code realistic for the test scenario
- Ensure diffctx assertions match actual diff content
