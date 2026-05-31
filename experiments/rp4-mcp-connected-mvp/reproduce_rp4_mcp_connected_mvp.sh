#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-${PYTHON:-python3}}"

"$PYTHON_BIN" tools/validate_runtime_profiles.py --self-test runtimes/profiles/RP4_mcp_connected.yaml
"$PYTHON_BIN" tools/verify_source_provenance.py --manifest benchmark/manifests/rp4-mcp-connected-mini.json
"$PYTHON_BIN" tools/validate_contracts.py --self-test contracts/mcp-tool-workflow-rp4-connected.yaml
"$PYTHON_BIN" tools/run_rp4_mcp_connected_mvp.py
"$PYTHON_BIN" tools/validate_rp4_mcp_connected_mvp.py
"$PYTHON_BIN" tools/validate_traces.py \
  results/raw/rp4-mcp-connected-benign/trace.jsonl \
  results/raw/rp4-mcp-connected-adversarial/trace.jsonl
"$PYTHON_BIN" tools/scrub_local_paths.py --target results/raw --target results/fixtures/rp4-mcp-connected
"$PYTHON_BIN" tools/check_no_local_paths.py
