# Gate 5 Manual Review Queue

Gate 5 manual review queue scaffold generated from the frozen inclusion table; no completed human reviews, reviewer agreement, adjudication, completed statistics, prevalence, or paper-grade completion claim is made.

## Aggregate

- Queued items: `60`
- Included cases: `60`
- Paired-summary mapped items: `50`
- Paired-summary unmapped items: `10`
- Blinding-eligible items: `50`
- Source-mix items: `first_party=3`, `public=3`, `synthetic=54`

This artifact is a queue only. It contains no reviewer IDs, completed review results, adjudication records, percent agreement, Cohen's kappa, confidence intervals, hypothesis tests, prevalence estimate, or paper-grade completion claim.

## Review Items

| Item | Category | Source mix | Pair status | Blinding | Reasons |
| --- | --- | --- | --- | --- | --- |
| `gate5-review-001-docs-forge.p1.docs-generation` | document automation | `public` | `not_mapped_to_existing_paired_summary_group` | `not_applicable_single_runtime_or_unmapped` | `unmapped_case_metadata_denominator` |
| `gate5-review-002-docs-forge.p2.output-scope` | document automation | `public` | `not_mapped_to_existing_paired_summary_group` | `not_applicable_single_runtime_or_unmapped` | `unmapped_case_metadata_denominator` |
| `gate5-review-003-audit-lens.p3.evidence-audit` | compliance/audit | `first_party` | `not_mapped_to_existing_paired_summary_group` | `not_applicable_single_runtime_or_unmapped` | `unmapped_case_metadata_denominator` |
| `gate5-review-004-audit-lens.p4.dashboard-generation` | compliance/audit | `first_party` | `not_mapped_to_existing_paired_summary_group` | `not_applicable_single_runtime_or_unmapped` | `unmapped_case_metadata_denominator` |
| `gate5-review-005-mcp-tool-workflow.p2.restricted-tools` | MCP/tool workflow | `synthetic` | `not_mapped_to_existing_paired_summary_group` | `not_applicable_single_runtime_or_unmapped` | `unmapped_case_metadata_denominator` |
| `gate5-review-006-repo-audit.mvp.dependency-summary-smoke` | repository maintenance | `synthetic` | `not_mapped_to_existing_paired_summary_group` | `not_applicable_single_runtime_or_unmapped` | `unmapped_case_metadata_denominator` |
| `gate5-review-007-network-egress.mvp.fake-sink-egress-smoke` | API workflow | `synthetic` | `not_mapped_to_existing_paired_summary_group` | `not_applicable_single_runtime_or_unmapped` | `unmapped_case_metadata_denominator` |
| `gate5-review-008-rp5-plugin-style.p1.install-activation` | MCP/tool workflow | `synthetic` | `not_mapped_to_existing_paired_summary_group` | `not_applicable_single_runtime_or_unmapped` | `unmapped_case_metadata_denominator` |
| `gate5-review-009-rp5-plugin-style.p2.update-metadata` | MCP/tool workflow | `synthetic` | `not_mapped_to_existing_paired_summary_group` | `not_applicable_single_runtime_or_unmapped` | `unmapped_case_metadata_denominator` |
| `gate5-review-010-rp5-plugin-style.p3.negative-control` | MCP/tool workflow | `synthetic` | `not_mapped_to_existing_paired_summary_group` | `not_applicable_single_runtime_or_unmapped` | `unmapped_case_metadata_denominator` |
| `gate5-review-011-data-extraction.p1.customer-summary` | data extraction | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-012-data-extraction.p2.pii-redaction` | data extraction | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-013-data-extraction.p3.export-negative-control` | data extraction | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-014-local-file-operation.p1.output-only` | local file operations | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-015-local-file-operation.p2.archive-manifest` | local file operations | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-016-local-file-operation.p3.cleanup-negative-control` | local file operations | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-017-doc-packager-synthetic.p1.source-note-synthesis` | document automation | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-018-doc-packager-synthetic.p2.release-notes-draft` | document automation | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-019-doc-packager-synthetic.p3.api-reference-refresh` | document automation | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-020-citation-normalizer-synthetic.p1.citation-inventory` | document automation | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-021-citation-normalizer-synthetic.p2.reference-style-normalization` | document automation | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-022-citation-normalizer-synthetic.p3.missing-citation-negative-control` | document automation | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-023-repo-maintainer-synthetic.p1.dependency-risk-inventory` | repository maintenance | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-024-repo-maintainer-synthetic.p2.ci-failure-triage` | repository maintenance | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-025-repo-maintainer-synthetic.p3.license-notice-audit` | repository maintenance | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-026-ci-triage-synthetic.p1.failing-job-summary` | repository maintenance | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-027-ci-triage-synthetic.p2.flaky-test-register` | repository maintenance | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-028-ci-triage-synthetic.p3.secret-log-negative-control` | repository maintenance | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-029-license-auditor-synthetic.p1.license-inventory` | repository maintenance | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-030-license-auditor-synthetic.p2.notice-file-plan` | repository maintenance | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-031-license-auditor-synthetic.p3.copyleft-boundary-negative-control` | repository maintenance | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-032-control-map-synthetic.p1.evidence-catalog` | compliance/audit | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-033-control-map-synthetic.p2.control-gap-register` | compliance/audit | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-034-control-map-synthetic.p3.remediation-priority-plan` | compliance/audit | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-035-vendor-risk-synthetic.p1.vendor-evidence-summary` | compliance/audit | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-036-vendor-risk-synthetic.p2.risk-tier-assignment` | compliance/audit | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-037-vendor-risk-synthetic.p3.unapproved-export-negative-control` | compliance/audit | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-038-schema-report-synthetic.p1.schema-bound-report` | data extraction | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-039-schema-report-synthetic.p2.mixed-format-summary` | data extraction | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-040-schema-report-synthetic.p3.raw-row-negative-control` | data extraction | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-041-tabular-privacy-synthetic.p1.column-classification` | data extraction | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-042-tabular-privacy-synthetic.p2.privacy-preserving-aggregate` | data extraction | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-043-tabular-privacy-synthetic.p3.identifier-export-negative-control` | data extraction | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-044-api-workflow-synthetic.p1.local-webhook-summary` | API workflow | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-045-api-workflow-synthetic.p2.rate-limit-plan` | API workflow | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-046-api-workflow-synthetic.p3.external-call-negative-control` | API workflow | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-047-ticket-api-synthetic.p1.fake-ticket-triage` | API workflow | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-048-ticket-api-synthetic.p2.mock-update-plan` | API workflow | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-049-ticket-api-synthetic.p3.credentialed-call-negative-control` | API workflow | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-050-file-diff-planner-synthetic.p1.diff-plan` | local file operations | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-051-file-diff-planner-synthetic.p2.path-traversal-negative-control` | local file operations | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-052-file-diff-planner-synthetic.p3.cache-retention-check` | local file operations | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-053-docs-forge.p3.citation-boundary` | document automation | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-054-repo-audit-executable.p2.lockfile-risk-summary` | repository maintenance | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-055-repo-audit-executable.p3.env-negative-control` | repository maintenance | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-056-audit-lens.p5.connector-negative-control` | compliance/audit | `first_party` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-057-network-egress-executable.p2.approval-required-egress-plan` | API workflow | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-058-network-egress-executable.p3.no-network-negative-control` | API workflow | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-059-mcp-tool-workflow.p1.tool-inventory` | MCP/tool workflow | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-060-mcp-tool-workflow.p2.tool-consent-negative-control` | MCP/tool workflow | `synthetic` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |

## Next Dependencies

- Expand each queued item into a sanitized review packet with trace and finding pointers.
- Collect two independent real human review exports for the frozen item set before agreement claims.
- Adjudicate reviewer disagreements before any adjudicated aggregate is reported.
- Keep agent-assisted triage separate from human agreement evidence.
