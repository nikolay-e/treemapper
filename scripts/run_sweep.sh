#!/usr/bin/env bash
# Sweep orchestrator: runs one cell of the v1 evaluation matrix with
# caffeinate to prevent macOS sleep, checkpoint+resume, and a global hard
# timeout. Each invocation is a single (baseline, scoring, budget) cell.
#
# Usage:
#   ./scripts/run_sweep.sh <baseline> <scoring> <budget> <out_subdir>
#
# Examples:
#   ./scripts/run_sweep.sh diffctx hybrid 8000 hybrid_b8k
#   ./scripts/run_sweep.sh diffctx ppr 16000 ppr_b16k
#   ./scripts/run_sweep.sh aider_fair _ 8000 aider_fair_b8k
#   ./scripts/run_sweep.sh bm25 _ 8000 bm25_workers1_b8k
#
# Output: results/final/v1/sweep/<out_subdir>/

set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "usage: $0 <baseline> <scoring> <budget> <out_subdir>" >&2
  echo "  baseline: diffctx | bm25 | aider_fair | aider_oracle" >&2
  echo "  scoring:  hybrid | ppr | ego | bm25 | _ (use _ for non-diffctx baselines)" >&2
  echo "  budget:   integer token budget; use -1 for ceiling, 0 for floor" >&2
  echo "  out_subdir: short tag for results dir" >&2
  exit 2
fi

BASELINE="$1"
SCORING="$2"
BUDGET="$3"
OUT_SUBDIR="$4"

cd "$(dirname "$0")/.."

OUT_DIR="results/final/v1/sweep/${OUT_SUBDIR}"
mkdir -p "${OUT_DIR}"

# Build a per-cell winner.json so the eval CLI can consume it.
WINNER_JSON="$(mktemp -t diffctx_sweep_winner.XXXXXX.json)"
trap 'rm -f "${WINNER_JSON}"' EXIT
cat >"${WINNER_JSON}" <<JSON
{
  "winner": {
    "tau": 0.12,
    "core_budget_fraction": 0.5,
    "budget": ${BUDGET},
    "scoring": "${SCORING}",
    "extra_env": {}
  },
  "winner_score": null,
  "note": "sweep cell ${BASELINE} ${SCORING} B=${BUDGET}"
}
JSON

# caffeinate prevents macOS Sequoia idle sleep + display sleep + system idle
# sleep + user activity assertion for the lifetime of this process. -i is a
# minimum requirement to keep long compute alive; -d keeps the display awake
# (avoids GPU power-state thrashing); -s keeps system awake on AC; -u
# simulates user activity for short Sleep schedules; -m disables disk sleep.
exec caffeinate -dimsu \
  .venv/bin/python -m benchmarks.run_final_eval \
  --baseline "${BASELINE}" \
  --winner "${WINNER_JSON}" \
  --manifests-dir benchmarks/manifests/v1 \
  --workers 40 \
  --timeout-per-instance 600 \
  --min-memory-gb 8 \
  --min-disk-gb 30 \
  --out "${OUT_DIR}"
