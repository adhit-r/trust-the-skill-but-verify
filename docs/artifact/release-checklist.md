# Release Checklist

Status: local machine-only bundle path available; no completed human review.

## Verification

- Dry-run regenerated outputs without touching tracked paper artifacts:
  `PYTHON_BIN=python3 ARTIFACT_OUTPUT_ROOT=tmp/artifact-release-validation bash scripts/reproduce_paper_tables.sh`
- Before exporting a release bundle, rebuild the tracked paper-facing artifacts:
  `PYTHON_BIN=python3 make reproduce-paper-tables`
- The bundle builder copies the current repository files, and the bundle
  validator compares bundled file hashes back to those current repository
  files. Do not treat a dry-run `ARTIFACT_OUTPUT_ROOT` reproduction as a fresh
  bundle source.
- `python3 tools/build_artifact_release_bundle.py --replace --output-dir tmp/artifact-release-bundle`
- `python3 tools/validate_artifact_release_bundle.py --bundle-dir tmp/artifact-release-bundle`
- `python3 tools/build_venue_package_metadata.py --replace --output-dir tmp/venue-package-metadata`
- `python3 tools/validate_venue_package_metadata.py --bundle-dir tmp/venue-package-metadata`
- Anonymous review candidate:
  `python3 tools/build_artifact_release_bundle.py --replace --packaging-profile anonymous_review --output-dir tmp/artifact-release-bundle-anonymous-review`
- Validate anonymous review candidate:
  `python3 tools/validate_artifact_release_bundle.py --packaging-profile anonymous_review --bundle-dir tmp/artifact-release-bundle-anonymous-review`
- Public archive candidate:
  `python3 tools/build_artifact_release_bundle.py --replace --packaging-profile public_archive --output-dir tmp/artifact-release-bundle-public-archive`
- Validate public archive candidate:
  `python3 tools/validate_artifact_release_bundle.py --packaging-profile public_archive --bundle-dir tmp/artifact-release-bundle-public-archive`
- `PYTHON_BIN=python3 make artifact-release-bundle`
- `PYTHON_BIN=python3 make validate-artifact-release-bundle`
- `PYTHON_BIN=python3 make venue-package-metadata`
- `PYTHON_BIN=python3 make validate-venue-package-metadata`
- `python3 tools/validate_benchmark_cases.py --self-test benchmark/manifests/benchmark-cases-current.json`
- `python3 tools/build_runtime_report_cards.py --check --output-dir results/derived/runtime-report-cards`
- `python3 tools/validate_gate5_scaffolds.py`
- `python3 tools/validate_artifact_metadata.py`
- `python3 tools/validate_claim_ledger.py`
- `python3 tools/check_no_local_paths.py`
- `PYTHON_BIN=python3 make verify`
- If a GitHub app scanner skips or fails because an artifact PR is too large,
  perform a compensating dependency/workflow review before treating the PR as
  release-clean. At minimum, inspect changes to dependency manifests, lockfiles,
  Dockerfiles, GitHub workflows, and custom GitHub actions.

## Safety

- Clean local bundle path only; do not label the bundle as a public release or external review artifact.
- No public network access, credentials, secrets, auth state, cookies, or local browser/session exports.
- No real secrets, cookies, auth state, or local credentials.
- No public exfiltration endpoints.
- No local absolute paths in tracked publishable files.
- Synthetic canaries only.
- Claim ledger updated for every promoted number.
- Exclude raw scratch and raw trace directories from the release bundle unless a separate review explicitly promotes them.

## Evidence Boundaries

- Current evidence, promoted full-paper evidence, and future work are separated.
- The selected packaging-profile pass validates `anonymous_review` and
  `public_archive` candidate metadata without claiming actual external
  submission, public release, completed human review, or reviewer agreement.
- The machine-only release bundle contains paper-facing derived artifacts,
  aggregate repeat-stability reports, the claim ledger, method boundaries,
  release manifests, and checksums only.
- The machine-only release bundle does not claim completed human review, reviewer agreement, adjudication, external review, or paper-grade completion.
- RP6 remains mitigation/report-card evidence unless scaled utility-preserving
  defense evidence is added.
- RP4 MCP fixture evidence remains local fixture evidence unless external MCP
  traces are promoted under the safety boundary.
