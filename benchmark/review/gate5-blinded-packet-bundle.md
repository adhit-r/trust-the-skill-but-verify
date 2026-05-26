# Gate 5 Blinded Packet Bundle

Gate 5 first-pass blinded packet bundle derived from the review-packet index; it exposes opaque evidence identifiers, hashes, JSON pointers, and runtime slot labels only, not runtime profile labels for exported first-pass pair packets, source run IDs, comparison paths, trace paths, finding paths, raw trace content, machine classification labels, completed human reviews, reviewer agreement, adjudication, completed statistics, prevalence, or paper-grade completion evidence.

## Aggregate

- Source packets: `60`
- Exported blinded packets: `50`
- Blocked metadata-only packets: `10`
- Opaque comparison refs: `50`
- Opaque finding artifact refs: `100`
- Opaque trace artifact refs: `100`
- Runtime slots: `100`
- Pair review units: `50`
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

## Next Dependencies

- Use the blinded bundle for first-pass review only; keep the unblinded packet index as an audit source outside reviewer-facing packet content.
- Collect two independent real human review exports against this frozen bundle before agreement claims.
- Unblind runtime labels only after first-pass review records are locked.
- Validate adjudication and agreement artifacts separately before adding statistical or paper-grade claims.
