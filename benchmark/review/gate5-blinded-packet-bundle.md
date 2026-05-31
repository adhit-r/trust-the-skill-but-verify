# Gate 5 Blinded Packet Bundle

Gate 5 first-pass blinded packet bundle derived from the review-packet index; it exposes opaque evidence identifiers, hashes, JSON pointers, and runtime slot labels only, not runtime profile labels for exported first-pass pair packets, source run IDs, comparison paths, trace paths, finding paths, raw trace content, machine classification labels, completed human reviews, reviewer agreement, adjudication, completed statistics, prevalence, or paper-grade completion evidence.

## Aggregate

- Source packets: `132`
- Exported blinded packets: `122`
- Blocked metadata-only packets: `10`
- Opaque comparison refs: `122`
- Opaque finding artifact refs: `244`
- Opaque trace artifact refs: `244`
- Runtime slots: `244`
- Pair review units: `122`
- Finding review units: `0`

This artifact is a blinded packet bundle only. Exported first-pass pair packets contain no runtime profile labels, source run IDs, comparison paths, trace paths, finding paths, raw trace content, reviewer IDs, completed review results, adjudication records, agreement metrics, confidence intervals, hypothesis tests, prevalence estimate, or paper-grade completion claim.

## Packets

| Packet | Status | Runtime slots | Pair units | Finding units |
| --- | --- | ---: | ---: | ---: |
| `gate5-packet-001-docs-forge.p1.docs-generation` | `blocked_metadata_only_unmapped` | 0 | 0 | 0 |
| `gate5-packet-002-docs-forge.p2.output-scope` | `blocked_metadata_only_unmapped` | 0 | 0 | 0 |
| `gate5-packet-003-audit-lens.p3.evidence-audit` | `blocked_metadata_only_unmapped` | 0 | 0 | 0 |
| `gate5-packet-004-audit-lens.p4.dashboard-generation` | `blocked_metadata_only_unmapped` | 0 | 0 | 0 |
| `gate5-packet-005-mcp-tool-workflow.p2.restricted-tools` | `blocked_metadata_only_unmapped` | 0 | 0 | 0 |
| `gate5-packet-006-repo-audit.mvp.dependency-summary-smoke` | `blocked_metadata_only_unmapped` | 0 | 0 | 0 |
| `gate5-packet-007-network-egress.mvp.fake-sink-egress-smoke` | `blocked_metadata_only_unmapped` | 0 | 0 | 0 |
| `gate5-packet-008-rp5-plugin-style.p1.install-activation` | `blocked_metadata_only_unmapped` | 0 | 0 | 0 |
| `gate5-packet-009-rp5-plugin-style.p2.update-metadata` | `blocked_metadata_only_unmapped` | 0 | 0 | 0 |
| `gate5-packet-010-rp5-plugin-style.p3.negative-control` | `blocked_metadata_only_unmapped` | 0 | 0 | 0 |
| `gate5-packet-011-data-extraction.p1.customer-summary` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-012-data-extraction.p2.pii-redaction` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-013-data-extraction.p3.export-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-014-local-file-operation.p1.output-only` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-015-local-file-operation.p2.archive-manifest` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-016-local-file-operation.p3.cleanup-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-017-doc-packager-synthetic.p1.source-note-synthesis` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-018-doc-packager-synthetic.p2.release-notes-draft` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-019-doc-packager-synthetic.p3.api-reference-refresh` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-020-citation-normalizer-synthetic.p1.citation-inventory` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-021-citation-normalizer-synthetic.p2.reference-style-normalization` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-022-citation-normalizer-synthetic.p3.missing-citation-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-023-repo-maintainer-synthetic.p1.dependency-risk-inventory` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-024-repo-maintainer-synthetic.p2.ci-failure-triage` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-025-repo-maintainer-synthetic.p3.license-notice-audit` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-026-ci-triage-synthetic.p1.failing-job-summary` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-027-ci-triage-synthetic.p2.flaky-test-register` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-028-ci-triage-synthetic.p3.secret-log-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-029-license-auditor-synthetic.p1.license-inventory` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-030-license-auditor-synthetic.p2.notice-file-plan` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-031-license-auditor-synthetic.p3.copyleft-boundary-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-032-control-map-synthetic.p1.evidence-catalog` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-033-control-map-synthetic.p2.control-gap-register` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-034-control-map-synthetic.p3.remediation-priority-plan` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-035-vendor-risk-synthetic.p1.vendor-evidence-summary` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-036-vendor-risk-synthetic.p2.risk-tier-assignment` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-037-vendor-risk-synthetic.p3.unapproved-export-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-038-schema-report-synthetic.p1.schema-bound-report` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-039-schema-report-synthetic.p2.mixed-format-summary` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-040-schema-report-synthetic.p3.raw-row-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-041-tabular-privacy-synthetic.p1.column-classification` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-042-tabular-privacy-synthetic.p2.privacy-preserving-aggregate` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-043-tabular-privacy-synthetic.p3.identifier-export-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-044-api-workflow-synthetic.p1.local-webhook-summary` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-045-api-workflow-synthetic.p2.rate-limit-plan` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-046-api-workflow-synthetic.p3.external-call-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-047-ticket-api-synthetic.p1.fake-ticket-triage` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-048-ticket-api-synthetic.p2.mock-update-plan` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-049-ticket-api-synthetic.p3.credentialed-call-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-050-file-diff-planner-synthetic.p1.diff-plan` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-051-file-diff-planner-synthetic.p2.path-traversal-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-052-file-diff-planner-synthetic.p3.cache-retention-check` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-053-docs-forge.p3.citation-boundary` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-054-repo-audit-executable.p2.lockfile-risk-summary` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-055-repo-audit-executable.p3.env-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-056-audit-lens.p5.connector-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-057-network-egress-executable.p2.approval-required-egress-plan` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-058-network-egress-executable.p3.no-network-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-059-mcp-tool-workflow.p1.tool-inventory` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-060-mcp-tool-workflow.p2.tool-consent-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-061-grclaw-audit-pack-first-party.p1.control-evidence-inventory` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-062-grclaw-audit-pack-first-party.p2.audit-pack-draft` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-063-grclaw-audit-pack-first-party.p3.connector-secret-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-064-patchpilot-repo-maintainer-first-party.p1.dependency-risk-inventory` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-065-patchpilot-repo-maintainer-first-party.p2.agent-rule-update-plan` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-066-patchpilot-repo-maintainer-first-party.p3.repo-token-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-067-aran-mcp-sentinel-first-party.p1.mcp-tool-catalog-summary` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-068-aran-mcp-sentinel-first-party.p2.tool-attestation-risk-plan` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-069-aran-mcp-sentinel-first-party.p3.unauthorized-tool-invocation-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-070-lexara-guardia-workflow-first-party.p1.consent-api-route-inventory` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-071-lexara-guardia-workflow-first-party.p2.dsar-workflow-state-plan` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-072-lexara-guardia-workflow-first-party.p3.tenant-data-export-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-073-markitdown-public.p1.local-doc-conversion-summary` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-074-markitdown-public.p2.unsupported-format-boundary-report` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-075-markitdown-public.p3.remote-url-fetch-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-076-renovate-public.p1.dependency-update-plan` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-077-renovate-public.p2.config-scope-boundary-diff` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-078-renovate-public.p3.tokenless-pr-creation-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-079-ort-public.p1.license-inventory-summary` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-080-ort-public.p2.copyleft-notice-boundary-plan` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-081-ort-public.p3.legal-advice-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-082-unstructured-public.p1.partitioned-document-elements` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-083-unstructured-public.p2.schema-bounded-extraction` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-084-unstructured-public.p3.hidden-canary-exfiltration-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-085-huginn-public.p1.webhook-agent-flow-summary` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-086-huginn-public.p2.rate-limit-dry-run-plan` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-087-huginn-public.p3.credentialed-live-webhook-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-088-playwright-mcp-public.p1.tool-inventory-summary` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-089-playwright-mcp-public.p2.consent-gated-navigation-plan` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-090-playwright-mcp-public.p3.unauthorized-browser-action-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-091-files-to-prompt-public.p1.local-context-bundle` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-092-files-to-prompt-public.p2.gitignore-size-boundary-report` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-093-files-to-prompt-public.p3.secret-file-inclusion-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-094-stakflo-evidence-pack-first-party.p1.evidence-package-index` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-095-stakflo-evidence-pack-first-party.p2.auditor-report-draft` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-096-stakflo-evidence-pack-first-party.p3.connector-credential-export-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-097-redact-ai-pii-extraction-first-party.p1.pii-finding-inventory` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-098-redact-ai-pii-extraction-first-party.p2.zero-copy-redaction-plan` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-099-redact-ai-pii-extraction-first-party.p3.raw-pii-exfiltration-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-100-mamori-local-file-agent-first-party.p1.endpoint-file-scan-summary` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-101-mamori-local-file-agent-first-party.p2.watcher-policy-plan` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-102-mamori-local-file-agent-first-party.p3.unauthorized-user-file-scan-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-103-zenscan-mcp-scanner-first-party.p1.mcp-scan-tool-catalog` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-104-zenscan-mcp-scanner-first-party.p2.sbom-policy-risk-plan` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-105-zenscan-mcp-scanner-first-party.p3.registry-secret-live-scan-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-106-pandoc-public.p1.local-format-conversion-plan` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-107-pandoc-public.p2.writer-option-boundary-report` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-108-pandoc-public.p3.remote-resource-include-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-109-mdbook-public.p1.book-structure-summary` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-110-mdbook-public.p2.preprocessor-boundary-report` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-111-mdbook-public.p3.secret-include-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-112-dependabot-core-public.p1.dependency-update-candidate-summary` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-113-dependabot-core-public.p2.ecosystem-scope-boundary-plan` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-114-dependabot-core-public.p3.tokenless-pr-registry-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-115-pdfplumber-public.p1.pdf-table-extraction-plan` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-116-pdfplumber-public.p2.page-range-boundary-report` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-117-pdfplumber-public.p3.hidden-text-pii-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-118-tika-public.p1.mime-metadata-extraction-plan` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-119-tika-public.p2.parser-sandbox-boundary-report` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-120-tika-public.p3.remote-server-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-121-bruno-public.p1.local-collection-summary` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-122-bruno-public.p2.environment-boundary-plan` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-123-bruno-public.p3.credentialed-live-api-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-124-mcp-python-sdk-public.p1.tool-schema-inventory` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-125-mcp-python-sdk-public.p2.consent-gated-tool-plan` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-126-mcp-python-sdk-public.p3.unauthorized-tool-invocation-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-127-fd-public.p1.local-file-discovery-plan` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-128-fd-public.p2.ignore-glob-boundary-report` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-129-fd-public.p3.sensitive-path-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-130-ripgrep-public.p1.local-pattern-search-summary` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-131-ripgrep-public.p2.binary-hidden-boundary-report` | `blinded_first_pass_ready` | 2 | 1 | 0 |
| `gate5-packet-132-ripgrep-public.p3.secret-content-exfiltration-negative-control` | `blinded_first_pass_ready` | 2 | 1 | 0 |

## Next Dependencies

- Use the blinded bundle for first-pass review only; keep the unblinded packet index as an audit source outside reviewer-facing packet content.
- Collect two independent real human review exports against this frozen bundle before agreement claims.
- Unblind runtime labels only after first-pass review records are locked.
- Validate adjudication and agreement artifacts separately before adding statistical or paper-grade claims.
