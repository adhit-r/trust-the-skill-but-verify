#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-${PYTHON:-python3}}"

if [[ -n "${AUDIT_LENS_SOURCE_ROOT:-}" ]]; then
  "$PYTHON_BIN" tools/verify_source_provenance.py \
    --manifest benchmark/manifests/audit-lens-acme.json \
    --source-root "$AUDIT_LENS_SOURCE_ROOT"
else
  "$PYTHON_BIN" tools/verify_source_provenance.py \
    --manifest benchmark/manifests/audit-lens-acme.json
fi

DOCKER_BIN="${DOCKER_BIN:-$(command -v docker || true)}"
if [[ -z "${DOCKER_BIN}" && -x /usr/local/bin/docker ]]; then
  DOCKER_BIN="/usr/local/bin/docker"
fi
if [[ -z "${DOCKER_BIN}" && -x /opt/homebrew/bin/docker ]]; then
  DOCKER_BIN="/opt/homebrew/bin/docker"
fi
if [[ -z "${DOCKER_BIN}" && -x /Applications/Docker.app/Contents/Resources/bin/docker ]]; then
  DOCKER_BIN="/Applications/Docker.app/Contents/Resources/bin/docker"
fi

if [[ -z "${DOCKER_BIN}" ]]; then
  echo "docker is required for RP3 reproduction" >&2
  exit 1
fi

export DOCKER_BIN
"${DOCKER_BIN}" info >/dev/null

"$PYTHON_BIN" tools/validate_contracts.py --self-test \
  contracts/audit-lens-evidence-audit.yaml \
  contracts/audit-lens-dashboard-generation.yaml
"$PYTHON_BIN" tools/run_audit_lens_mvp.py

TRACE_PATHS=()
while IFS= read -r trace_path; do
  TRACE_PATHS+=("${trace_path}")
done < <("$PYTHON_BIN" - <<'PY'
from pathlib import Path
import re

report = Path("results/mvp/audit-lens/drift_report.md").read_text(encoding="utf-8")
for match in re.findall(r"`([^`]*results/raw/[^`]*trace\.jsonl)`", report):
    print(match)
PY
)

if [[ "${#TRACE_PATHS[@]}" -ne 8 ]]; then
  echo "expected 8 canonical trace paths in AuditLens drift report, got ${#TRACE_PATHS[@]}" >&2
  exit 1
fi

"$PYTHON_BIN" tools/validate_traces.py "${TRACE_PATHS[@]}"
"$PYTHON_BIN" tools/scrub_local_paths.py --target results/raw --target results/mvp/audit-lens
