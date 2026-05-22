# Acme Corp — Vendor Risk Assessment Summary
**Report Date**: 2026-04-01
**Owner**: Elena Vasquez, DPO
**Next Full Review**: 2026-07-01

## Critical Vendors (Tier 1)

| Vendor | Service | Data Access | Last Assessment | SOC 2 | Status |
|--------|---------|-------------|-----------------|-------|--------|
| AWS | Cloud infrastructure | Customer data (encrypted) | 2025-12-15 | Type II (current) | ✅ Compliant |
| Okta | Identity provider | Employee identities | 2025-11-01 | Type II (current) | ✅ Compliant |
| Cloudflare | CDN/WAF/DNS | Network traffic metadata | 2025-10-20 | Type II (current) | ✅ Compliant |
| Stripe | Payment processing | Customer payment data | 2026-01-15 | Type II (current) + PCI DSS L1 | ✅ Compliant |
| Snowflake | Data warehouse | Customer analytics data | 2025-08-10 | Type II (current) | ⚠️ **OVERDUE** — assessment overdue by 60 days |

## High-Risk Vendors (Tier 2)

| Vendor | Service | Last Assessment | Status |
|--------|---------|-----------------|--------|
| BambooHR | HRMS | 2026-02-01 | ✅ Compliant |
| GitHub | Source control | 2025-12-01 | ✅ Compliant |
| Datadog | Monitoring/SIEM | 2026-01-10 | ✅ Compliant |
| KnowBe4 | Security training | 2025-11-15 | ✅ Compliant |
| CrowdStrike | EDR | 2026-03-01 | ✅ Compliant |

## SecurityScorecard Ratings

| Vendor | Overall Score | Rating | Trend |
|--------|-------------|--------|-------|
| AWS | 95/100 | A | Stable |
| Okta | 88/100 | A | Improving |
| Cloudflare | 92/100 | A | Stable |
| Stripe | 91/100 | A | Stable |
| Snowflake | 85/100 | B | Declining ⚠️ |

## Gaps & Remediation
1. **Snowflake assessment overdue**: Assessment was due 2026-02-01. Vendor risk team has scheduled assessment for 2026-04-15. Tracked in SECURITY-201.
2. **Snowflake SecurityScorecard declining**: Score dropped from 90 to 85 over 6 months. Monitoring closely.
3. **No fourth-party risk assessment**: Acme does not currently assess sub-processors of critical vendors. Planned for Q3 2026.
