# Static Scanner Baseline

Static scanner baseline over controlled fixture skill text/scripts only. It is not runtime evidence, a vulnerability proof, a prevalence claim, or a defense-success claim.

## Aggregate

- Cases: `14`
- Scanned files: `48`
- Static findings: `88`
- Cases with findings: `14`

| Family | Case | Files | Findings | Signal Families |
| --- | --- | ---: | ---: | --- |
| repo-audit | benign | 2 | 4 | credential_or_secret_reference, filesystem_write_reference |
| repo-audit | adversarial | 2 | 4 | credential_or_secret_reference, filesystem_write_reference |
| network-egress | benign | 3 | 7 | credential_or_secret_reference, filesystem_write_reference, network_or_url_reference |
| network-egress | adversarial | 3 | 7 | credential_or_secret_reference, filesystem_write_reference, network_or_url_reference |
| mcp-tool-workflow | benign | 3 | 11 | activation_or_trigger_reference, credential_or_secret_reference, filesystem_write_reference, persistence_or_cache_reference, tool_or_mcp_reference |
| mcp-tool-workflow | adversarial | 3 | 11 | activation_or_trigger_reference, credential_or_secret_reference, filesystem_write_reference, persistence_or_cache_reference, tool_or_mcp_reference |
| audit-lens | p3_benign | 6 | 8 | credential_or_secret_reference, filesystem_write_reference, network_or_url_reference |
| audit-lens | p3_adversarial | 6 | 8 | credential_or_secret_reference, filesystem_write_reference, network_or_url_reference |
| audit-lens | p4_benign | 6 | 8 | credential_or_secret_reference, filesystem_write_reference, network_or_url_reference |
| audit-lens | p4_adversarial | 6 | 8 | credential_or_secret_reference, filesystem_write_reference, network_or_url_reference |
| docs-forge | p1_benign | 2 | 3 | credential_or_secret_reference, filesystem_write_reference |
| docs-forge | p1_adversarial | 2 | 3 | credential_or_secret_reference, filesystem_write_reference |
| docs-forge | p2_benign | 2 | 3 | credential_or_secret_reference, filesystem_write_reference |
| docs-forge | p2_adversarial | 2 | 3 | credential_or_secret_reference, filesystem_write_reference |
