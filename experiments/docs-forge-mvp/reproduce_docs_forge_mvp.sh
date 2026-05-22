#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-${PYTHON:-python3}}"
export PYTHONDONTWRITEBYTECODE=1

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
  contracts/docs-forge-docs-generation.yaml \
  contracts/docs-forge-output-scope.yaml
"$PYTHON_BIN" tools/run_docs_forge_mvp.py

TRACE_PATHS=()
while IFS= read -r trace_path; do
  TRACE_PATHS+=("${trace_path}")
done < <("$PYTHON_BIN" - <<'PY'
from pathlib import Path
import re

report = Path("results/mvp/docs-forge/drift_report.md").read_text(encoding="utf-8")
for match in re.findall(r"`([^`]*results/raw/[^`]*trace\.jsonl)`", report):
    print(match)
PY
)

if [[ "${#TRACE_PATHS[@]}" -ne 8 ]]; then
  echo "expected 8 canonical trace paths in docs-forge drift report, got ${#TRACE_PATHS[@]}" >&2
  exit 1
fi

"$PYTHON_BIN" tools/validate_traces.py "${TRACE_PATHS[@]}"
