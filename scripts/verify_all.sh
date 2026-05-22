#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-${PYTHON:-python3}}"
export PYTHONDONTWRITEBYTECODE=1

while IFS= read -r -d '' json_file; do
  "$PYTHON_BIN" -m json.tool "$json_file" >/dev/null
done < <(git ls-files -z '*.json')

"$PYTHON_BIN" -m compileall -q src tools
"$PYTHON_BIN" tools/validate_runtime_profiles.py --self-test runtimes/profiles/*.yaml
"$PYTHON_BIN" tools/validate_contracts.py --self-test contracts/*.yaml
"$PYTHON_BIN" tools/verify_source_provenance.py --manifest benchmark/manifests/docs-forge-mini.json
"$PYTHON_BIN" tools/verify_source_provenance.py --manifest benchmark/manifests/audit-lens-acme.json
"$PYTHON_BIN" tools/check_no_local_paths.py
"$PYTHON_BIN" tools/validate_traces.py results/raw/*/trace.jsonl

echo "verify_all passed"
