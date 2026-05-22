# Acme Corp — Change Management Log (Q1 2026)
**Source**: Jira Project CHANGE
**Generated**: 2026-04-10

## Summary
| Metric | Value |
|--------|-------|
| Total change requests | 89 |
| Approved & deployed | 84 |
| Rejected | 3 |
| Rolled back | 2 |
| Emergency changes | 4 |
| Changes with peer review | 89/89 (100%) |

## Emergency Changes

| ID | Date | Description | Approver | Post-Review |
|----|------|-------------|----------|-------------|
| CHANGE-067 | 2026-01-12 | Fix SCIM webhook deprovisioning failure | Sarah Chen | PIR completed 2026-01-15 |
| CHANGE-071 | 2026-02-14 | Remediate S3 bucket public access | Mark Liu | PIR completed 2026-02-16 |
| CHANGE-078 | 2026-03-01 | Patch critical OpenSSL CVE | Alex Thompson | PIR completed 2026-03-03 |
| CHANGE-085 | 2026-03-28 | Hotfix payment processing timeout | Ravi Sharma | PIR completed 2026-03-30 |

## Rollbacks

| ID | Date | Description | Reason | Re-deployed |
|----|------|-------------|--------|-------------|
| CHANGE-044 | 2026-01-22 | Database schema migration v4.2 | Performance regression detected in canary | 2026-01-25 |
| CHANGE-072 | 2026-02-18 | Frontend bundle optimization | CSS rendering issue in Safari | 2026-02-20 |

## Change Approval Workflow
1. Developer creates CHANGE ticket in Jira
2. Technical review by peer (code review in GitHub PR)
3. Manager approval in Jira
4. Security review (for infrastructure/access changes)
5. Deploy via CI/CD (GitHub Actions → AWS)
6. Post-deployment verification within 1 hour
