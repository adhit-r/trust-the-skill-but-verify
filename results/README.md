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

Raw workspace Markdown is local scratch output and is ignored by Git. Keep canonical `trace.jsonl` files and paper-facing result artifacts tracked; do not publish generated prose copied out of raw workspaces.

Do not delete raw directories during reproducibility checks. Use `experiments/repo-audit-mvp/reproduce_repo_audit_mvp.sh` to rerun the repo-audit MVP and validate that the latest canonical traces are complete, contract-checkable, and RP3-backed by a recorded `docker run`, including when the command is wrapped by instrumentation such as `strace`. Use `tools/run_network_egress_mvp.py` to rerun PV-02.

## Derived Benchmark Scale Gap

`results/derived/benchmark-scale-gap.json` and `.md` compute the current
20-skill / 60-triple inventory against the mid-scale and full-paper targets.
`provenance.source_mix.label` is a skill-origin accounting label; case-level
evidence remains represented by `source_kind` and `provenance_level`.

Current source-mix accounting is 1 first-party, 1 public, and 18 synthetic
skills. The mid-scale source-mix gap is 4 first-party and 7 public skills, and
source-mix completion is not claimed.

## Gate 5 Descriptive Rates

`benchmark/manifests/gate5-paper-inclusion.json` freezes the current
60-case inclusion table for descriptive-rate accounting. `results/derived/gate5-descriptive-rates.json`
and `.md` report 22 raw inventory and coverage rate records from that table.

These artifacts are denominator and descriptive-rate evidence only. They do
not claim completed statistics, confidence intervals, hypothesis tests,
reviewer agreement, prevalence, source-mix completion, or paper-grade
completion.

## Gate 5 Manual Review Queue

`benchmark/review/gate5-review-queue.json` and `.md` enumerate 60 queued
case-level review items from the frozen inclusion table. The queue records 50
paired-summary mapped items, 10 unmapped metadata-only items, and 50 items
eligible for first-pass runtime-label blinding.

This is queue evidence only. It does not contain reviewer IDs, completed
review results, adjudication records, percent agreement, Cohen's kappa,
confidence intervals, prevalence estimates, or paper-grade completion claims.

## Gate 5 Review Packet Index

`benchmark/review/gate5-review-packet-index.json` and `.md` expand the review
queue into 60 packet-index records. The index resolves 50 comparison refs, 100
run/finding-file refs, 100 trace refs, and 50 runtime-pair review units. The 10
unmapped queue items remain blocked as metadata-only packets.

This is packet-index evidence only. It contains no raw trace content,
reviewer IDs, completed review results, adjudication records, agreement
metrics, confidence intervals, prevalence estimates, or paper-grade completion
claims.

## Gate 5 Blinded Packet Bundle

`benchmark/review/gate5-blinded-packet-bundle.json` and `.md` derive a
first-pass blinded bundle from the review-packet index. The bundle exports 50
runtime-label-blinded pair-review packets and keeps 10 unmapped cases blocked
as metadata-only records.

This is blinded-bundle export evidence only. Exported first-pass packets use
opaque evidence identifiers and runtime slots; they do not include runtime
profile labels, source run IDs, comparison paths, trace paths, finding paths,
raw trace content, reviewer IDs, completed review results, adjudication
records, agreement metrics, confidence intervals, prevalence estimates, or
paper-grade completion claims.

## Gate 5 Review Export Templates

`benchmark/review/gate5-review-export-templates.json` and `.md` provide two
blank first-pass human-review templates over the blinded bundle. Each template
assigns the same 50 blinded pair-review units to an unassigned human reviewer
slot. The 10 unmapped metadata-only packets remain blocked and unassigned.

This is template evidence only. It contains no completed human reviews, human
reviewer identities, Codex-assisted human-review substitutions, reviewer
agreement, adjudication records, statistics, prevalence estimates, or
paper-grade completion claims.

## Fixture Report Cards

Supplemental runtime-surface evidence that is excluded from RP2/RP3 MVP
aggregate counts lives under `results/fixtures/`.

- `rp4-mcp-connected/` is bounded local MCP fixture evidence.
- `rp6-policy-hardened/` is the RP6 current-case mitigation report card over
  the existing fourteen case variants plus a supplemental network-denial
  policy probe. It is report-card evidence, not a defense-success or RP6
  runtime-drift claim.
- `strengthening/` contains derived reviewer-facing baselines: a
  contract-derived least-privilege budget, a coarse RP2/RP3/RP6 mitigation
  ladder, bounded RP6 component-ablation evidence across six controls, and
  bounded deterministic RP6 repeat stability across repeat IDs 1, 2, and 3.
  These are excluded from MVP runtime-drift counts.
- `rp6-policy-hardened/ablations/component_report_card.json` is the component
  ablation report card; it checks generated RP6 ablation traces against the
  original contracts and is not a defense-success or public-network claim.

## Planned Inclusion Promotion

`results/planned-inclusion/` contains controlled single-repeat RP2/RP3
synthetic fixture evidence for the 44 entries that were previously only
planned inclusion records. Each promoted case has one RP2 trace, one RP3 trace,
two contract-finding files, and one RP2/RP3 comparison.

This directory is denominator and contract-check coverage. It does not claim
live product execution, public-network behavior, commercial-runtime behavior,
source-mix completion, repeat stability, prevalence, defense success, or
runtime-drift findings.

## Planned-Inclusion Repeat Stability

`results/fixtures/strengthening/rp2-rp3-repeat-stability/` contains a separate
bounded deterministic repeat-stability artifact for the 44 planned-inclusion
fixtures. It runs repeat IDs 1, 2, and 3 under RP2 and RP3, for 264 runtime
observations and 132 same-repeat RP2/RP3 pairs.

This artifact intentionally stays outside the broad `*_comparison.json` result
glob used for the paired-runtime denominator layer. It supports only bounded
deterministic fixture stability; it does not claim completed statistics,
reviewer agreement, prevalence, live product behavior, public-network behavior,
commercial-runtime behavior, or defense success.
