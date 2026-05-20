#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-${PYTHON:-python3}}"

"$PYTHON_BIN" tools/validate_contracts.py --self-test contracts/network-egress-executable-smoke.yaml
"$PYTHON_BIN" tools/run_network_egress_mvp.py

TRACE_PATHS=()
while IFS= read -r trace_path; do
  TRACE_PATHS+=("${trace_path}")
done < <("$PYTHON_BIN" - <<'PY'
from pathlib import Path
import re

report = Path("results/mvp/network-egress/drift_report.md").read_text(encoding="utf-8")
for match in re.findall(r"`([^`]*results/raw/[^`]*trace\.jsonl)`", report):
    print(match)
PY
)

if [[ "${#TRACE_PATHS[@]}" -ne 4 ]]; then
  echo "expected 4 canonical trace paths in network-egress drift report, got ${#TRACE_PATHS[@]}" >&2
  exit 1
fi

"$PYTHON_BIN" tools/validate_traces.py "${TRACE_PATHS[@]}"
