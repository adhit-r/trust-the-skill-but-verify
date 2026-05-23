#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-${PYTHON:-python3}}"
export PYTHONDONTWRITEBYTECODE=1

"$PYTHON_BIN" tools/verify_first_party_sources.py
"$PYTHON_BIN" -m json.tool results/external/first-party-source-provenance.json >/dev/null
"$PYTHON_BIN" tools/validate_external_validity_scaffolds.py
"$PYTHON_BIN" tools/check_no_local_paths.py
