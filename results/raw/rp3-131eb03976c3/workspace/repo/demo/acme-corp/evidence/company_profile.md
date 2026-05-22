# Acme Corp — Company Profile

**Company**: Acme Corp (acmecorp.io)
**Industry**: B2B SaaS — Customer Data Platform
**Employees**: 142
**Founded**: 2019
**HQ**: Austin, TX
**Cloud**: AWS (primary), some GCP
**Customers**: ~380 enterprise clients, mostly financial services and healthcare

## Tech Stack
- **Identity**: Okta (SSO + MFA)
- **HR**: BambooHR
- **Cloud**: AWS (us-east-1, eu-west-1)
- **Source Control**: GitHub Enterprise
- **Endpoint**: Jamf (Mac), Intune (Windows)
- **EDR**: CrowdStrike Falcon
- **SIEM**: Datadog
- **Ticketing**: Jira
- **Communication**: Slack Enterprise Grid
- **Secrets**: HashiCorp Vault
- **Backup**: AWS Backup
- **CDN/WAF**: Cloudflare
- **Training**: KnowBe4
- **Vendor Risk**: SecurityScorecard

## Audit Scope
- SOC 2 Type II (Security, Availability, Confidentiality)
- ISO 27001:2022 Annex A
- Audit period: January 1, 2026 — June 30, 2026
- Auditor: Ernst & Young LLP

## Known Issues
- 3 employees terminated in Q1 whose Okta accounts were deactivated 4-7 days late
- One S3 bucket briefly had public read access (remediated within 2 hours)
- Security awareness training completion is at 91% (target: 100%)
- No formal DR test has been conducted in the last 12 months
- Vendor risk assessment for one critical vendor is overdue by 60 days
