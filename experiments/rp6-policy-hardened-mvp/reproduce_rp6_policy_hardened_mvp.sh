#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-${PYTHON:-python3}}"
export PYTHONDONTWRITEBYTECODE=1

"$PYTHON_BIN" tools/verify_source_provenance.py --manifest benchmark/manifests/rp6-policy-hardened-mvp.json
"$PYTHON_BIN" tools/run_rp6_policy_hardened_mvp.py
"$PYTHON_BIN" tools/scrub_local_paths.py --target results/raw --target results/fixtures
"$PYTHON_BIN" tools/validate_rp6_policy_hardened_mvp.py
"$PYTHON_BIN" tools/validate_traces.py results/raw/rp6-*/trace.jsonl
"$PYTHON_BIN" tools/validate_traces.py results/fixtures/rp6-policy-hardened/_probe_runs/rp6-*/trace.jsonl

echo "RP6 policy-hardened current-case report card reproduced"
