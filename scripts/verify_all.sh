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
"$PYTHON_BIN" tools/verify_source_provenance.py --manifest benchmark/manifests/repo-audit-mvp.json
"$PYTHON_BIN" tools/verify_source_provenance.py --manifest benchmark/manifests/network-egress-mvp.json
"$PYTHON_BIN" tools/verify_source_provenance.py --manifest benchmark/manifests/mcp-tool-workflow-mini.json
"$PYTHON_BIN" tools/verify_source_provenance.py --manifest benchmark/manifests/docs-forge-mini.json
"$PYTHON_BIN" tools/verify_source_provenance.py --manifest benchmark/manifests/audit-lens-acme.json
"$PYTHON_BIN" tools/validate_external_validity_scaffolds.py
"$PYTHON_BIN" tools/validate_docs_forge_live_installer.py
"$PYTHON_BIN" tools/validate_docs_forge_live_project_local_install.py
"$PYTHON_BIN" tools/validate_traces.py results/live/docs-forge-installer/project_local_install_trace.jsonl
"$PYTHON_BIN" tools/validate_docs_forge_live_runtime_pair.py
"$PYTHON_BIN" tools/validate_traces.py results/live/docs-forge-installer/project_local_runtime_pair_host_trace.jsonl
"$PYTHON_BIN" tools/validate_traces.py results/live/docs-forge-installer/project_local_runtime_pair_minimal_env_trace.jsonl
"$PYTHON_BIN" tools/validate_docs_forge_live_package_observer.py
"$PYTHON_BIN" tools/validate_traces.py results/live/docs-forge-installer/package_observer_trace.jsonl
"$PYTHON_BIN" tools/validate_docs_forge_live_npx_observer.py
"$PYTHON_BIN" tools/validate_traces.py results/live/docs-forge-installer/npx_observer_trace.jsonl
"$PYTHON_BIN" tools/validate_claim_ledger.py
"$PYTHON_BIN" tools/check_no_local_paths.py
"$PYTHON_BIN" tools/validate_traces.py results/raw/*/trace.jsonl

echo "verify_all passed"
