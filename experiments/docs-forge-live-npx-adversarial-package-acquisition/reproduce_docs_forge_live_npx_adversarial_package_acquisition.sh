#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-${PYTHON:-python3}}"
export PYTHONDONTWRITEBYTECODE=1

if [[ -z "${DOCS_FORGE_SOURCE_ROOT:-}" ]]; then
  echo "DOCS_FORGE_SOURCE_ROOT is required for docs-forge adversarial npx package-acquisition evidence" >&2
  exit 2
fi

"$PYTHON_BIN" tools/run_docs_forge_live_npx_adversarial_package_acquisition.py --source-root "$DOCS_FORGE_SOURCE_ROOT"
"$PYTHON_BIN" -m json.tool results/live/docs-forge-installer/npx_adversarial_package_acquisition_result.json >/dev/null
"$PYTHON_BIN" tools/validate_docs_forge_live_npx_adversarial_package_acquisition.py
"$PYTHON_BIN" tools/validate_traces.py results/live/docs-forge-installer/npx_adversarial_package_acquisition_trace.jsonl
"$PYTHON_BIN" tools/check_no_local_paths.py
