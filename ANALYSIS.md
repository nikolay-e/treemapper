# Tournament Analysis: Addressing 98 Failing Tests Systematically

## Context

TreeMapper `diffctx` pipeline selects code fragments to explain a git diff.
98 integration tests fail because the algorithm includes
**forbidden distractor/sibling files**.

**Failure pattern (78/98 tests):**

- All required fragments ARE found (recall = 100%)
- Forbidden fragments also present (precision = 0%)
- Score = required_recall × (1 - forbidden_rate) = 0%

**Root cause confirmed:** PPR propagation flows through hub files
(lib.rs, variables.tf, Chart.yaml, package declarations) to sibling
files that have no direct relationship to the diff.

**Key parameters:**

- `alpha = 0.60` (PPR teleportation)
- `tau = 0.08` (adaptive stopping)
- `_LOW_RELEVANCE_THRESHOLD = 0.005`
- `_SIZE_PENALTY_BASE_TOKENS = 100`, `_SIZE_PENALTY_EXPONENT = 0.5`
- `_HUB_REVERSE_THRESHOLD = 3`
- `_MAX_CONTEXT_FRAGMENTS_PER_FILE = 10`

**Codebase:**

- `src/treemapper/diffctx/filtering.py` — hub noise, config_generic, relevance filtering
- `src/treemapper/diffctx/ppr.py` — personalized pagerank
- `src/treemapper/diffctx/graph.py` — graph construction
- `src/treemapper/diffctx/edges/` — all edge builders
- `src/treemapper/diffctx/select.py` — lazy greedy selection
- `tests/cases/diff/` — 1403 YAML test cases
