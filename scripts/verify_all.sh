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
"$PYTHON_BIN" tools/adapter_smoke.py
"$PYTHON_BIN" tools/validate_contracts.py --self-test contracts/*.yaml
"$PYTHON_BIN" tools/verify_source_provenance.py --manifest benchmark/manifests/repo-audit-mvp.json
"$PYTHON_BIN" tools/verify_source_provenance.py --manifest benchmark/manifests/network-egress-mvp.json
"$PYTHON_BIN" tools/verify_source_provenance.py --manifest benchmark/manifests/mcp-tool-workflow-mini.json
"$PYTHON_BIN" tools/verify_source_provenance.py --manifest benchmark/manifests/rp4-mcp-connected-mini.json
"$PYTHON_BIN" tools/verify_source_provenance.py --manifest benchmark/manifests/rp1-restricted-hosted-mvp.json
"$PYTHON_BIN" tools/verify_source_provenance.py --manifest benchmark/manifests/rp5-plugin-style-mvp.json
"$PYTHON_BIN" tools/verify_source_provenance.py --manifest benchmark/manifests/rp6-policy-hardened-mvp.json
"$PYTHON_BIN" tools/verify_source_provenance.py --manifest benchmark/manifests/data-extraction-mini.json
"$PYTHON_BIN" tools/verify_source_provenance.py --manifest benchmark/manifests/local-file-operation-mini.json
"$PYTHON_BIN" tools/verify_source_provenance.py --manifest benchmark/manifests/docs-forge-mini.json
"$PYTHON_BIN" tools/verify_source_provenance.py --manifest benchmark/manifests/audit-lens-acme.json
while IFS= read -r -d '' planned_manifest; do
  "$PYTHON_BIN" tools/verify_source_provenance.py --manifest "$planned_manifest"
done < <(find benchmark/manifests -maxdepth 1 -name '*-planned*.json' -print0 | sort -z)
"$PYTHON_BIN" tools/validate_benchmark_cases.py --self-test benchmark/manifests/benchmark-cases-current.json
"$PYTHON_BIN" tools/validate_benchmark_scale_gap.py
"$PYTHON_BIN" tools/validate_planned_inclusion_mvp.py
"$PYTHON_BIN" tools/validate_planned_inclusion_repeat_stability.py
"$PYTHON_BIN" tools/validate_traces.py results/fixtures/strengthening/rp2-rp3-repeat-stability/_runs/rp*/trace.jsonl
"$PYTHON_BIN" tools/validate_main_rp2_rp3_repeat_stability.py
"$PYTHON_BIN" tools/validate_traces.py results/fixtures/strengthening/rp2-rp3-main-repeat-stability/_runs/rp*/trace.jsonl
"$PYTHON_BIN" tools/validate_data_extraction_mvp.py
"$PYTHON_BIN" tools/validate_traces.py \
  results/raw/rp2-a4fa2e1ac41c/trace.jsonl \
  results/raw/rp3-7f2abf86c6b8/trace.jsonl \
  results/raw/rp2-41585d449341/trace.jsonl \
  results/raw/rp3-4cfb89d0c64d/trace.jsonl \
  results/raw/rp2-887dc1aa459b/trace.jsonl \
  results/raw/rp3-aca0adaecf78/trace.jsonl
"$PYTHON_BIN" tools/validate_local_file_operation_mvp.py
"$PYTHON_BIN" tools/validate_traces.py \
  results/raw/rp2-c0908d7c4e3b/trace.jsonl \
  results/raw/rp3-0c9ad135cbc0/trace.jsonl \
  results/raw/rp2-7c1546701eec/trace.jsonl \
  results/raw/rp3-29ae66d19b6a/trace.jsonl \
  results/raw/rp2-c814dd826046/trace.jsonl \
  results/raw/rp3-9d9969439b67/trace.jsonl
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
"$PYTHON_BIN" tools/validate_docs_forge_live_npx_rp3_node_observer.py
"$PYTHON_BIN" tools/validate_traces.py results/live/docs-forge-installer/npx_rp3_node_observer_trace.jsonl
"$PYTHON_BIN" tools/validate_docs_forge_live_npx_observer.py \
  --result results/live/docs-forge-installer/npx_runtime_pair_rp2_result.json \
  --report results/live/docs-forge-installer/npx_runtime_pair_rp2_report.md \
  --trace results/live/docs-forge-installer/npx_runtime_pair_rp2_trace.jsonl
"$PYTHON_BIN" tools/validate_docs_forge_live_npx_rp3_node_observer.py \
  --result results/live/docs-forge-installer/npx_runtime_pair_rp3_result.json \
  --report results/live/docs-forge-installer/npx_runtime_pair_rp3_report.md \
  --trace results/live/docs-forge-installer/npx_runtime_pair_rp3_trace.jsonl
"$PYTHON_BIN" tools/validate_docs_forge_live_npx_runtime_pair.py
"$PYTHON_BIN" tools/validate_traces.py \
  results/live/docs-forge-installer/npx_runtime_pair_rp2_trace.jsonl \
  results/live/docs-forge-installer/npx_runtime_pair_rp3_trace.jsonl
"$PYTHON_BIN" tools/validate_docs_forge_live_npx_adversarial_package_acquisition.py
"$PYTHON_BIN" tools/validate_traces.py results/live/docs-forge-installer/npx_adversarial_package_acquisition_trace.jsonl
"$PYTHON_BIN" tools/validate_docs_forge_live_npx_rp3_node_adversarial_package_acquisition.py
"$PYTHON_BIN" tools/validate_traces.py results/live/docs-forge-installer/npx_rp3_node_adversarial_package_acquisition_trace.jsonl
"$PYTHON_BIN" tools/validate_docs_forge_live_npx_adversarial_package_acquisition.py \
  --result results/live/docs-forge-installer/npx_adversarial_package_acquisition_runtime_pair_host_result.json \
  --report results/live/docs-forge-installer/npx_adversarial_package_acquisition_runtime_pair_host_report.md \
  --trace results/live/docs-forge-installer/npx_adversarial_package_acquisition_runtime_pair_host_trace.jsonl
"$PYTHON_BIN" tools/validate_docs_forge_live_npx_rp3_node_adversarial_package_acquisition.py \
  --result results/live/docs-forge-installer/npx_adversarial_package_acquisition_runtime_pair_rp3_result.json \
  --report results/live/docs-forge-installer/npx_adversarial_package_acquisition_runtime_pair_rp3_report.md \
  --trace results/live/docs-forge-installer/npx_adversarial_package_acquisition_runtime_pair_rp3_trace.jsonl
"$PYTHON_BIN" tools/validate_docs_forge_live_npx_adversarial_package_acquisition_runtime_pair.py
"$PYTHON_BIN" tools/validate_traces.py \
  results/live/docs-forge-installer/npx_adversarial_package_acquisition_runtime_pair_host_trace.jsonl \
  results/live/docs-forge-installer/npx_adversarial_package_acquisition_runtime_pair_rp3_trace.jsonl
"$PYTHON_BIN" tools/validate_rp4_mcp_connected_mvp.py
"$PYTHON_BIN" tools/validate_traces.py \
  results/raw/rp4-mcp-connected-benign/trace.jsonl \
  results/raw/rp4-mcp-connected-adversarial/trace.jsonl
"$PYTHON_BIN" tools/validate_rp1_restricted_hosted_mvp.py --require-artifacts
"$PYTHON_BIN" tools/validate_traces.py results/raw/rp1-*/trace.jsonl
"$PYTHON_BIN" tools/validate_rp5_plugin_fixture_mvp.py
"$PYTHON_BIN" tools/validate_traces.py results/fixtures/rp5-plugin-style/_runs/rp5-*/trace.jsonl
"$PYTHON_BIN" tools/validate_rp6_policy_hardened_mvp.py
"$PYTHON_BIN" tools/validate_traces.py results/raw/rp6-*/trace.jsonl
"$PYTHON_BIN" tools/validate_traces.py results/fixtures/rp6-policy-hardened/_probe_runs/rp6-*/trace.jsonl
"$PYTHON_BIN" tools/validate_strengthening_evidence.py
"$PYTHON_BIN" tools/validate_traces.py results/fixtures/rp6-policy-hardened/ablations/_component_runs/rp6-*/trace.jsonl
"$PYTHON_BIN" tools/validate_traces.py results/fixtures/strengthening/repeat-stability/_runs/rp6-*/trace.jsonl
"$PYTHON_BIN" tools/build_runtime_report_cards.py --check --output-dir results/derived/runtime-report-cards
"$PYTHON_BIN" tools/validate_gate5_scaffolds.py
"$PYTHON_BIN" tools/validate_paired_runtime_summary.py
"$PYTHON_BIN" tools/validate_gate5_inclusion_table.py
"$PYTHON_BIN" tools/validate_gate5_descriptive_rates.py
"$PYTHON_BIN" tools/validate_gate5_review_queue.py
"$PYTHON_BIN" tools/validate_gate5_review_packet_index.py
"$PYTHON_BIN" tools/validate_gate5_blinded_packet_bundle.py
"$PYTHON_BIN" tools/validate_gate5_review_export_templates.py
"$PYTHON_BIN" -c 'import yaml; yaml.safe_load(open("CITATION.cff", encoding="utf-8"))'
"$PYTHON_BIN" tools/validate_claim_ledger.py
"$PYTHON_BIN" tools/check_no_local_paths.py
"$PYTHON_BIN" tools/validate_traces.py results/raw/*/trace.jsonl

echo "verify_all passed"
