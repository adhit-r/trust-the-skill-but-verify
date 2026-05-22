# Cross-Framework Control Mapping (Crosswalk)

This crosswalk maps equivalent controls across major compliance frameworks. Use it to show organizations how satisfying one control can simultaneously address requirements in other frameworks — the "map once, comply many" principle.

> **For granular per-control mappings across 87 frameworks**, use the OSA connector (`osa_connector.md`). This crosswalk provides domain-level summaries; OSA provides control-level precision via NIST 800-53 as the universal parent.

## How to Use This Crosswalk

1. Find the control domain (left column)
2. Read across to see which controls in each framework address the same requirement
3. When evidence satisfies one control, automatically mark related controls as "partially evidenced"
4. Note: Mappings are approximate — auditors may require framework-specific evidence for each

## Master Crosswalk Table

| Domain | ISO 27001:2022 | SOC 2 TSC | HIPAA Security | NIST CSF 2.0 | PCI DSS v4.0 | GDPR |
|--------|---------------|-----------|----------------|--------------|-------------|------|
| **Information Security Policy** | A.5.1 | CC5.3 | §164.316(a) | GV.PO | 12.1 | Art.24 |
| **Roles & Responsibilities** | A.5.2 | CC1.3 | §164.308(a)(2) | GV.RR | 12.4 | Art.37-39 |
| **Risk Assessment** | A.5.7, CC3.1-3.4 | CC3.1-CC3.4 | §164.308(a)(1)(ii)(A) | ID.RA | 12.3.1 | Art.35 |
| **Asset Management** | A.5.9-A.5.13 | CC6.1 | §164.310(d) | ID.AM | 9.9, 12.5.1 | Art.30 |
| **Access Control Policy** | A.5.15-A.5.18 | CC6.1-CC6.4 | §164.312(a)(1) | PR.AA | 7.1-7.3 | Art.25, Art.32 |
| **Authentication** | A.8.5 | CC6.3 | §164.312(d) | PR.AA | 8.2-8.6 | Art.32 |
| **Encryption** | A.8.24 | CC6.7 | §164.312(a)(2)(iv), §164.312(e)(2)(ii) | PR.DS | 3.4-3.5, 4.1 | Art.32 |
| **Network Security** | A.8.20-A.8.22 | CC6.5-CC6.6 | §164.312(e)(1) | PR.IR | 1.1-1.5 | Art.32 |
| **Malware Protection** | A.8.7 | CC6.8 | §164.308(a)(5)(ii)(B) | PR.IR | 5.1-5.4 | Art.32 |
| **Vulnerability Management** | A.8.8 | CC7.1, CC7.5 | §164.308(a)(1)(ii)(B) | ID.RA | 6.1-6.4, 11.3 | Art.32 |
| **Logging & Monitoring** | A.8.15-A.8.16 | CC7.2-CC7.3 | §164.312(b) | DE.CM, DE.AE | 10.1-10.7 | Art.32 |
| **Incident Response** | A.5.24-A.5.28 | CC7.3-CC7.5 | §164.308(a)(6) | RS.MA, RS.AN | 12.10 | Art.33-34 |
| **Change Management** | A.8.32 | CC8.1 | §164.308(a)(1)(ii)(D) | PR.IP | 6.5.6 | Art.32 |
| **Business Continuity** | A.5.29-A.5.30 | A1.1-A1.3 | §164.308(a)(7) | RC.RP | 12.10.1 | Art.32 |
| **Vendor Management** | A.5.19-A.5.23 | CC9.1-CC9.2 | §164.308(b)(1) | GV.SC | 12.8 | Art.28 |
| **Security Awareness** | A.6.3 | CC1.4 | §164.308(a)(5) | PR.AT | 12.6 | Art.39 |
| **Physical Security** | A.7.1-A.7.6 | CC6.4 | §164.310(a)-(c) | PR.IP | 9.1-9.4 | Art.32 |
| **HR Security** | A.6.1-A.6.2 | CC1.4-CC1.5 | §164.308(a)(3) | GV.RR | 12.7 | Art.32 |
| **Data Classification** | A.5.12-A.5.13 | C1.1 | §164.312(a)(1) | ID.AM | 9.6 | Art.9 |
| **Data Retention/Disposal** | A.8.10 | C1.2, P5.1-P5.2 | §164.310(d)(2)(i) | PR.DS | 3.1 | Art.5(1)(e), Art.17 |
| **Privacy/PII** | A.5.34 | P1.1-P8.1 | §164.530 | PR.DS | 3.4 | Art.5-22 |
| **Secure Development** | A.8.25-A.8.31 | CC8.1 | N/A | PR.IP | 6.5 | Art.25 |
| **Backup** | A.8.13 | A1.2 | §164.308(a)(7)(ii)(A) | PR.IP | 12.3.1 | Art.32 |
| **Audit/Compliance** | A.5.35-A.5.36 | CC4.1-CC4.2 | §164.308(a)(8) | GV.OV | 12.4 | Art.5(2) |

## AI Governance Crosswalk

| Domain | ISO 42001 | EU AI Act | NIST AI RMF |
|--------|-----------|-----------|-------------|
| **AI Policy & Governance** | A.2.1-A.2.3 | Art. 9 (Risk Mgmt System), Art. 17 (QMS) | GOVERN 1 (Policies) |
| **AI Roles & Accountability** | A.3.1-A.3.4 | Art. 26 (Deployer obligations) | GOVERN 2 (Accountability) |
| **AI Resources & Competence** | A.4.1-A.4.5 | Art. 15 (Accuracy/Robustness) | GOVERN 3 (Workforce) |
| **AI Lifecycle Management** | A.5.1-A.5.9 | Art. 9 (Risk Mgmt throughout lifecycle) | MAP 1 (Context), MEASURE 2 (Evaluation) |
| **Data Governance for AI** | A.6.1-A.6.7 | Art. 10 (Data Governance) | MAP 2 (Risk identification) |
| **AI Transparency & Explainability** | A.7.1-A.7.5 | Art. 13 (Transparency), Art. 52 (Disclosure) | GOVERN 4 (Culture), MAP 1.6 (Limitations) |
| **Responsible AI Use** | A.8.1-A.8.6 | Art. 14 (Human Oversight), Art. 26 (Deployer) | MANAGE 1 (Risk treatment) |
| **AI Third-Party Risk** | A.9.1-A.9.4 | Art. 28 (Notified bodies) | GOVERN 6 (Third-party management) |
| **AI Bias & Fairness** | A.6.5, A.5.5 | Art. 10(2)(f) (Bias examination) | MEASURE 1.2 (Fairness metrics) |
| **AI Incident Management** | A.8.5 | Art. 73 (Serious incident reporting) | MANAGE 2 (Risk response) |
| **AI Monitoring & Drift** | A.5.7, A.8.4 | Art. 72 (Post-market monitoring) | MEASURE 2.2 (Post-deployment), MEASURE 3.2 (Drift) |
| **AI Documentation** | Clause 7.5 | Art. 11 (Technical documentation) | MANAGE 4 (Documentation) |
## Cross-Certification Effort Matrix

When an organization already holds one certification and pursues another:

| From → To | ISO 27001 | SOC 2 | HIPAA | PCI DSS |
|-----------|-----------|-------|-------|---------|
| **ISO 27001** | — | ~40% new work | ~35% new work | ~50% new work |
| **SOC 2** | ~45% new work | — | ~40% new work | ~55% new work |
| **HIPAA** | ~50% new work | ~45% new work | — | ~60% new work |
| **PCI DSS** | ~55% new work | ~50% new work | ~55% new work | — |

These are rough estimates. Actual effort depends on scope, existing documentation quality, and organizational maturity.

## Framework Selection Guide

| If the organization is... | Start with... | Reason |
|--------------------------|--------------|--------|
| A B2B SaaS startup | SOC 2 Type II | Most requested by enterprise customers |
| Healthcare / handles PHI | HIPAA | Legal requirement |
| Processes payment cards | PCI DSS | Contractual/legal requirement |
| European market / handles EU data | GDPR | Legal requirement |
| Government contractor | NIST CSF → FedRAMP | Federal requirement |
| Enterprise / global | ISO 27001 | Broadest international recognition |
| Building a security program from scratch | NIST CSF | Best educational structure, free |
| **Building or deploying AI systems** | **ISO 42001** | **Only certifiable AI management standard** |
| **AI company selling in the EU** | **EU AI Act + ISO 42001** | **EU AI Act is law; ISO 42001 supports conformity assessment** |
| **US company using generative AI** | **NIST AI RMF** | **Voluntary but increasingly expected by regulators and customers** |
| **AI + data-heavy company** | **ISO 42001 + GDPR** | **AI governance + data protection covers the full risk surface** |
