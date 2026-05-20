# Results Manifest

This directory contains generated evidence artifacts for the SkillDiff research repo.

## Canonical Repo-Audit MVP Artifacts

The canonical repo-audit MVP result set is under `results/mvp/repo-audit/`.

- `drift_report.md` is the top-level human-readable summary.
- `benign_contract_report.md` and `benign_contract_findings.json` are the canonical RP2 benign contract-check outputs.
- `adversarial_contract_report.md` and `adversarial_contract_findings.json` are the canonical RP2 adversarial contract-check outputs.
- `benign_rp3_contract_report.md` and `benign_rp3_contract_findings.json` are the canonical RP3 benign contract-check outputs.
- `adversarial_rp3_contract_report.md` and `adversarial_rp3_contract_findings.json` are the canonical RP3 adversarial contract-check outputs.
- `benign_rp2_rp3_comparison.md` / `.json` and `adversarial_rp2_rp3_comparison.md` / `.json` are the canonical pairwise runtime comparisons.

The four canonical raw traces are the exact `results/raw/*/trace.jsonl` paths listed in the table inside `results/mvp/repo-audit/drift_report.md`. Rerunning the MVP creates new raw run directories, then rewrites the table to point at the latest four canonical traces. Raw run IDs, profile hashes, pinned image references, and trace event counts may change as runtime instrumentation changes; the reproducibility check validates the latest canonical trace paths, adapter metadata, trace envelopes, and expected contract-count summaries instead of hardcoding those unstable values.

## Canonical Network-Egress MVP Artifacts

The canonical PV-02 network-egress MVP result set is under `results/mvp/network-egress/`.

- `drift_report.md` is the top-level human-readable summary.
- `benign_contract_report.md` and `benign_contract_findings.json` are the canonical RP2 benign contract-check outputs.
- `adversarial_contract_report.md` and `adversarial_contract_findings.json` are the canonical RP2 adversarial contract-check outputs.
- `benign_rp3_contract_report.md` and `benign_rp3_contract_findings.json` are the canonical RP3 benign contract-check outputs.
- `adversarial_rp3_contract_report.md` and `adversarial_rp3_contract_findings.json` are the canonical RP3 adversarial contract-check outputs.
- `benign_rp2_rp3_comparison.md` / `.json` and `adversarial_rp2_rp3_comparison.md` / `.json` are the canonical pairwise runtime comparisons.

The four canonical raw traces are the exact `results/raw/*/trace.jsonl` paths listed in the table inside `results/mvp/network-egress/drift_report.md`. PV-02 uses a controlled Python `urllib` network shim and reserved `.invalid` fake-sink domains. It proves fake-sink and blocked-egress provenance for controlled Python benchmark runs; it does not claim public internet testing, packet capture, or syscall-complete network tracing.

## Scratch Raw Runs

All `results/raw/*` directories are append-only run outputs. Older raw directories are scratch and reproduction history, not the current canonical result set, unless a canonical manifest or report explicitly points to them.

Do not delete raw directories during reproducibility checks. Use `experiments/repo-audit-mvp/reproduce_repo_audit_mvp.sh` to rerun the repo-audit MVP and validate that the latest canonical traces are complete, contract-checkable, and RP3-backed by a recorded `docker run`, including when the command is wrapped by instrumentation such as `strace`. Use `tools/run_network_egress_mvp.py` to rerun PV-02.
