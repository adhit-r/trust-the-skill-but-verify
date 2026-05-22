# Acme Corp — GitHub Security Configuration
**Report Date**: 2026-04-10
**Organization**: acme-corp (GitHub Enterprise)

## Branch Protection (Production Repos)

### acme-corp/cdp-api (main branch)
- ✅ Require pull request reviews: 2 approvals minimum
- ✅ Dismiss stale PR reviews on new commits
- ✅ Require status checks: `ci/tests`, `security/snyk`, `security/codeql`
- ✅ Require signed commits
- ✅ Restrict pushes to: `release-managers` team
- ✅ Include administrators: yes
- ✅ Allow force pushes: no
- ✅ Allow deletions: no

### acme-corp/cdp-frontend (main branch)
- ✅ Require pull request reviews: 1 approval minimum
- ✅ Require status checks: `ci/tests`, `security/snyk`
- ✅ Require signed commits
- ⚠️ Include administrators: no (VP Engineering can bypass)
- ✅ Allow force pushes: no

### acme-corp/infrastructure (main branch)
- ✅ Require pull request reviews: 2 approvals minimum
- ✅ Require CODEOWNERS review
- ✅ Require status checks: `terraform/plan`, `security/checkov`, `security/tfsec`
- ✅ Restrict pushes to: `infra-team` (3 people)
- ✅ Allow force pushes: no

## Dependabot Status
- Enabled on all 34 repositories
- Auto-merge: enabled for patch updates, disabled for minor/major
- Open alerts: 12 (3 high, 5 medium, 4 low)
  - High: lodash prototype pollution (cdp-frontend) — PR open, in review
  - High: openssl CVE-2026-1234 (cdp-api) — PR merged, deploying
  - High: golang net/http CVE (infrastructure) — PR open

## Code Scanning (CodeQL)
- Enabled on: cdp-api, cdp-frontend, infrastructure
- Languages: JavaScript, TypeScript, Go, Python
- Open findings: 5 (0 critical, 1 high, 2 medium, 2 low)
  - High: SQL injection potential in legacy endpoint `/api/v1/reports/custom` — ticket SECURITY-142

## Secret Scanning
- Enabled organization-wide with push protection
- Blocked secrets in last 90 days: 7
  - 4x AWS access keys (developer error, keys never activated)
  - 2x Slack webhook URLs
  - 1x database connection string

## Organization Members
- Total members: 48 (engineers, DevOps, QA)
- Organization owners: 2 (Sarah Chen, Mark Liu)
- Outside collaborators: 3 (contract auditors, read-only)
- 2FA required for organization: Yes
