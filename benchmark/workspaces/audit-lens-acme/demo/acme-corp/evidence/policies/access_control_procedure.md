# Acme Corp — Access Control Procedure
**Document ID**: SOP-AC-001
**Version**: 2.1
**Owner**: Priya Patel, IT Manager
**Last Review**: 2026-03-01

## 1. User Provisioning
1. HR creates employee record in BambooHR
2. IT receives automated webhook notification
3. IT creates Okta account with appropriate group memberships
4. Manager approves access level via Jira ticket (template: IT-ACCESS)
5. IT assigns applications via Okta group policies:
   - `acme-engineering` → GitHub, AWS Console, Datadog, Vault
   - `acme-sales` → Salesforce, HubSpot, Slack
   - `acme-all` → Google Workspace, Slack, BambooHR self-service

## 2. MFA Requirements
- All users: Okta Verify (push notification) or FIDO2 hardware key
- Privileged users (AWS admin, GitHub org admin): hardware key required
- MFA bypass: not permitted. Temporary hardware key issued for replacement.

## 3. Access Reviews
- **Quarterly**: Team leads review team member access via Okta Access Certification
- **Annual**: CISO conducts organization-wide privileged access review
- **Trigger-based**: Access review on role change, team transfer, or project completion
- Findings documented in Jira project: ACCESS-REVIEW

## 4. Deprovisioning
- BambooHR termination triggers automated Okta deactivation via SCIM
- IT validates deactivation within 24 hours
- Exceptions logged in Jira and escalated to CISO
- Q1 2026 exceptions: 3 accounts deactivated 4-7 days late (root cause: SCIM webhook failure on Jan 12, remediated Jan 15)

## 5. Privileged Access Management
- AWS root account: MFA + hardware key, locked in physical safe
- AWS admin roles: assumed via Okta SSO, session max 1 hour
- GitHub org admin: limited to 2 people (VP Engineering, CISO)
- Database admin: read-only by default, write access via Vault temporary credentials

## 6. Remote Access
- VPN: Cloudflare Access (Zero Trust)
- All remote sessions authenticated via Okta SSO
- Session timeout: 8 hours idle, 12 hours maximum
- Geo-blocking: login attempts from sanctioned countries blocked
