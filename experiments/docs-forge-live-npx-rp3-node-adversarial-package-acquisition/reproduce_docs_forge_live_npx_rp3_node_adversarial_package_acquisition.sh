#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-${PYTHON:-python3}}"
IMAGE_REF="${SKILLDIFF_RP3_NODE_IMAGE_REF:-sha256:2ad42c75739973d9bebb233eed1e6e6056c32655a621dd4246d620aba0cef955}"
export PYTHONDONTWRITEBYTECODE=1

if [[ -z "${DOCS_FORGE_SOURCE_ROOT:-}" ]]; then
  echo "DOCS_FORGE_SOURCE_ROOT is required for docs-forge RP3 Node adversarial npx package-acquisition evidence" >&2
  exit 2
fi

if ! docker image inspect "$IMAGE_REF" >/dev/null 2>&1; then
  echo "Docker image $IMAGE_REF is required. Build runtimes/docker/rp3-node first or set SKILLDIFF_RP3_NODE_IMAGE_REF." >&2
  exit 2
fi

"$PYTHON_BIN" tools/run_docs_forge_live_npx_rp3_node_adversarial_package_acquisition.py --source-root "$DOCS_FORGE_SOURCE_ROOT" --container-image-ref "$IMAGE_REF"
"$PYTHON_BIN" -m json.tool results/live/docs-forge-installer/npx_rp3_node_adversarial_package_acquisition_result.json >/dev/null
"$PYTHON_BIN" tools/validate_docs_forge_live_npx_rp3_node_adversarial_package_acquisition.py
"$PYTHON_BIN" tools/validate_traces.py results/live/docs-forge-installer/npx_rp3_node_adversarial_package_acquisition_trace.jsonl
"$PYTHON_BIN" tools/check_no_local_paths.py
