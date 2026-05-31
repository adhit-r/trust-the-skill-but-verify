#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-${PYTHON:-python3}}"
export PYTHONDONTWRITEBYTECODE=1

for repeat_id in 1 2 3; do
  "$PYTHON_BIN" tools/run_source_mix_rp6_report_card.py --repeat-id "$repeat_id"
done

"$PYTHON_BIN" tools/build_source_mix_rp6_repeat_stability.py
"$PYTHON_BIN" tools/scrub_local_paths.py \
  --target results/fixtures/strengthening/source-mix-rp6-report-card \
  --target results/fixtures/strengthening/source-mix-rp6-repeat-stability
"$PYTHON_BIN" tools/validate_source_mix_rp6_report_card.py
"$PYTHON_BIN" tools/build_source_mix_rp6_repeat_stability.py --check
"$PYTHON_BIN" tools/validate_repeat_coverage.py
"$PYTHON_BIN" tools/validate_traces.py results/fixtures/strengthening/source-mix-rp6-report-card/_runs/rp6-*/trace.jsonl

echo "source-mix RP6 repeat stability reproduced"
