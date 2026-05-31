#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-${PYTHON:-python3}}"
export PYTHONDONTWRITEBYTECODE=1

"$PYTHON_BIN" tools/run_strengthening_evidence.py
"$PYTHON_BIN" tools/scrub_local_paths.py \
  --target results/fixtures/strengthening \
  --target results/fixtures/rp6-policy-hardened/ablations
"$PYTHON_BIN" tools/validate_strengthening_evidence.py
"$PYTHON_BIN" tools/validate_traces.py results/fixtures/rp6-policy-hardened/ablations/_component_runs/rp6-*/trace.jsonl
"$PYTHON_BIN" tools/validate_traces.py results/fixtures/strengthening/repeat-stability/_runs/rp6-*/trace.jsonl

echo "strengthening evidence reproduced"
