# Semia-Style Reachability Approximation

Semia-style static reachability approximation over controlled fixture skill text and SkillDiff contracts. This is explicitly not a Semia reproduction, Semia equivalence result, runtime confirmation, or prevalence claim.

## Aggregate

- Cases: `14`
- Static findings considered: `88`
- Approximation candidates: `88`
- Cases with candidates: `14`
- Runtime confirmation claims supported: `0`
- Semia equivalence claims supported: `0`

| Family | Case | Static Findings | Candidates | Deny Surfaces |
| --- | --- | ---: | ---: | --- |
| repo-audit | benign | 4 | 4 | activation, credentials, filesystem, network, persistence, sinks |
| repo-audit | adversarial | 4 | 4 | activation, credentials, filesystem, network, persistence, sinks |
| network-egress | benign | 7 | 7 | activation, filesystem, network, persistence, sinks |
| network-egress | adversarial | 7 | 7 | activation, filesystem, network, persistence, sinks |
| mcp-tool-workflow | benign | 11 | 11 | activation, credentials, filesystem, network, persistence, sinks, tools |
| mcp-tool-workflow | adversarial | 11 | 11 | activation, credentials, filesystem, network, persistence, sinks, tools |
| audit-lens | p3_benign | 8 | 8 | activation, credentials, filesystem, network, persistence, sinks, tools |
| audit-lens | p3_adversarial | 8 | 8 | activation, credentials, filesystem, network, persistence, sinks, tools |
| audit-lens | p4_benign | 8 | 8 | activation, credentials, filesystem, network, persistence, sinks, tools |
| audit-lens | p4_adversarial | 8 | 8 | activation, credentials, filesystem, network, persistence, sinks, tools |
| docs-forge | p1_benign | 3 | 3 | activation, credentials, filesystem, network, persistence, sinks |
| docs-forge | p1_adversarial | 3 | 3 | activation, credentials, filesystem, network, persistence, sinks |
| docs-forge | p2_benign | 3 | 3 | activation, credentials, filesystem, network, persistence, sinks |
| docs-forge | p2_adversarial | 3 | 3 | activation, credentials, filesystem, network, persistence, sinks |
