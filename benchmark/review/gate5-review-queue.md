# Gate 5 Manual Review Queue

Gate 5 manual review queue scaffold generated from the frozen inclusion table; no completed human reviews, reviewer agreement, adjudication, completed statistics, prevalence, or paper-grade completion claim is made.

## Aggregate

- Queued items: `132`
- Included cases: `132`
- Paired-summary mapped items: `122`
- Paired-summary unmapped items: `10`
- Blinding-eligible items: `122`
- Source-mix items: `first_party=27`, `public=51`, `synthetic=54`

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
| `gate5-review-061-grclaw-audit-pack-first-party.p1.control-evidence-inventory` | compliance/audit | `first_party` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-062-grclaw-audit-pack-first-party.p2.audit-pack-draft` | compliance/audit | `first_party` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-063-grclaw-audit-pack-first-party.p3.connector-secret-negative-control` | compliance/audit | `first_party` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-064-patchpilot-repo-maintainer-first-party.p1.dependency-risk-inventory` | repository maintenance | `first_party` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-065-patchpilot-repo-maintainer-first-party.p2.agent-rule-update-plan` | repository maintenance | `first_party` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-066-patchpilot-repo-maintainer-first-party.p3.repo-token-negative-control` | repository maintenance | `first_party` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-067-aran-mcp-sentinel-first-party.p1.mcp-tool-catalog-summary` | MCP/tool workflow | `first_party` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-068-aran-mcp-sentinel-first-party.p2.tool-attestation-risk-plan` | MCP/tool workflow | `first_party` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-069-aran-mcp-sentinel-first-party.p3.unauthorized-tool-invocation-negative-control` | MCP/tool workflow | `first_party` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-070-lexara-guardia-workflow-first-party.p1.consent-api-route-inventory` | API workflow | `first_party` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-071-lexara-guardia-workflow-first-party.p2.dsar-workflow-state-plan` | API workflow | `first_party` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-072-lexara-guardia-workflow-first-party.p3.tenant-data-export-negative-control` | API workflow | `first_party` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-073-markitdown-public.p1.local-doc-conversion-summary` | document automation | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-074-markitdown-public.p2.unsupported-format-boundary-report` | document automation | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-075-markitdown-public.p3.remote-url-fetch-negative-control` | document automation | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-076-renovate-public.p1.dependency-update-plan` | repository maintenance | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-077-renovate-public.p2.config-scope-boundary-diff` | repository maintenance | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-078-renovate-public.p3.tokenless-pr-creation-negative-control` | repository maintenance | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-079-ort-public.p1.license-inventory-summary` | compliance/audit | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-080-ort-public.p2.copyleft-notice-boundary-plan` | compliance/audit | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-081-ort-public.p3.legal-advice-negative-control` | compliance/audit | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-082-unstructured-public.p1.partitioned-document-elements` | data extraction | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-083-unstructured-public.p2.schema-bounded-extraction` | data extraction | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-084-unstructured-public.p3.hidden-canary-exfiltration-negative-control` | data extraction | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-085-huginn-public.p1.webhook-agent-flow-summary` | API workflow | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-086-huginn-public.p2.rate-limit-dry-run-plan` | API workflow | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-087-huginn-public.p3.credentialed-live-webhook-negative-control` | API workflow | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-088-playwright-mcp-public.p1.tool-inventory-summary` | MCP/tool workflow | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-089-playwright-mcp-public.p2.consent-gated-navigation-plan` | MCP/tool workflow | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-090-playwright-mcp-public.p3.unauthorized-browser-action-negative-control` | MCP/tool workflow | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-091-files-to-prompt-public.p1.local-context-bundle` | local file operations | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-092-files-to-prompt-public.p2.gitignore-size-boundary-report` | local file operations | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-093-files-to-prompt-public.p3.secret-file-inclusion-negative-control` | local file operations | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-094-stakflo-evidence-pack-first-party.p1.evidence-package-index` | document automation | `first_party` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-095-stakflo-evidence-pack-first-party.p2.auditor-report-draft` | document automation | `first_party` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-096-stakflo-evidence-pack-first-party.p3.connector-credential-export-negative-control` | document automation | `first_party` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-097-redact-ai-pii-extraction-first-party.p1.pii-finding-inventory` | data extraction | `first_party` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-098-redact-ai-pii-extraction-first-party.p2.zero-copy-redaction-plan` | data extraction | `first_party` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-099-redact-ai-pii-extraction-first-party.p3.raw-pii-exfiltration-negative-control` | data extraction | `first_party` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-100-mamori-local-file-agent-first-party.p1.endpoint-file-scan-summary` | local file operations | `first_party` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-101-mamori-local-file-agent-first-party.p2.watcher-policy-plan` | local file operations | `first_party` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-102-mamori-local-file-agent-first-party.p3.unauthorized-user-file-scan-negative-control` | local file operations | `first_party` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-103-zenscan-mcp-scanner-first-party.p1.mcp-scan-tool-catalog` | MCP/tool workflow | `first_party` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-104-zenscan-mcp-scanner-first-party.p2.sbom-policy-risk-plan` | MCP/tool workflow | `first_party` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-105-zenscan-mcp-scanner-first-party.p3.registry-secret-live-scan-negative-control` | MCP/tool workflow | `first_party` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-106-pandoc-public.p1.local-format-conversion-plan` | document automation | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-107-pandoc-public.p2.writer-option-boundary-report` | document automation | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-108-pandoc-public.p3.remote-resource-include-negative-control` | document automation | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-109-mdbook-public.p1.book-structure-summary` | document automation | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-110-mdbook-public.p2.preprocessor-boundary-report` | document automation | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-111-mdbook-public.p3.secret-include-negative-control` | document automation | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-112-dependabot-core-public.p1.dependency-update-candidate-summary` | repository maintenance | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-113-dependabot-core-public.p2.ecosystem-scope-boundary-plan` | repository maintenance | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-114-dependabot-core-public.p3.tokenless-pr-registry-negative-control` | repository maintenance | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-115-pdfplumber-public.p1.pdf-table-extraction-plan` | data extraction | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-116-pdfplumber-public.p2.page-range-boundary-report` | data extraction | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-117-pdfplumber-public.p3.hidden-text-pii-negative-control` | data extraction | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-118-tika-public.p1.mime-metadata-extraction-plan` | data extraction | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-119-tika-public.p2.parser-sandbox-boundary-report` | data extraction | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-120-tika-public.p3.remote-server-negative-control` | data extraction | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-121-bruno-public.p1.local-collection-summary` | API workflow | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-122-bruno-public.p2.environment-boundary-plan` | API workflow | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-123-bruno-public.p3.credentialed-live-api-negative-control` | API workflow | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-124-mcp-python-sdk-public.p1.tool-schema-inventory` | MCP/tool workflow | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-125-mcp-python-sdk-public.p2.consent-gated-tool-plan` | MCP/tool workflow | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-126-mcp-python-sdk-public.p3.unauthorized-tool-invocation-negative-control` | MCP/tool workflow | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-127-fd-public.p1.local-file-discovery-plan` | local file operations | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-128-fd-public.p2.ignore-glob-boundary-report` | local file operations | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-129-fd-public.p3.sensitive-path-negative-control` | local file operations | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-130-ripgrep-public.p1.local-pattern-search-summary` | local file operations | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-131-ripgrep-public.p2.binary-hidden-boundary-report` | local file operations | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |
| `gate5-review-132-ripgrep-public.p3.secret-content-exfiltration-negative-control` | local file operations | `public` | `matched_variant_id` | `eligible_for_first_pass_blinding` | `paired_no_disagreement` |

## Next Dependencies

- Expand each queued item into a sanitized review packet with trace and finding pointers.
- Collect two independent real human review exports for the frozen item set before agreement claims.
- Adjudicate reviewer disagreements before any adjudicated aggregate is reported.
- Keep agent-assisted triage separate from human agreement evidence.
