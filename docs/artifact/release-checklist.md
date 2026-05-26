# Release Checklist

Status: scaffold for final artifact release.

## Verification

- `python3 tools/validate_benchmark_cases.py --self-test benchmark/manifests/benchmark-cases-current.json`
- `python3 tools/build_runtime_report_cards.py --check --output-dir results/derived/runtime-report-cards`
- `python3 tools/validate_gate5_scaffolds.py`
- `python3 tools/validate_claim_ledger.py`
- `python3 tools/check_no_local_paths.py`
- `PYTHON_BIN=python3 make verify`

## Safety

- No real secrets, cookies, auth state, or local credentials.
- No public exfiltration endpoints.
- No local absolute paths in tracked publishable files.
- Synthetic canaries only.
- Claim ledger updated for every promoted number.

## Evidence Boundaries

- Current evidence, promoted full-paper evidence, and future work are separated.
- RP6 remains mitigation/report-card evidence unless scaled utility-preserving
  defense evidence is added.
- RP4 MCP fixture evidence remains local fixture evidence unless external MCP
  traces are promoted under the safety boundary.
