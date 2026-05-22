# Acme Corp — CrowdStrike Falcon Endpoint Report
**Generated**: 2026-04-10
**Environment**: Production + Corporate

## Device Summary
| Metric | Count |
|--------|-------|
| Total managed endpoints | 168 |
| macOS (Jamf-managed) | 112 |
| Windows (Intune-managed) | 41 |
| Linux (servers) | 15 |
| Sensor version current | 165 |
| Sensor version outdated (>30 days) | 3 |

## Protection Status
- Prevention policy active: 168/168 (100%)
- FileVault/BitLocker encrypted: 153/153 workstations (100%)
- OS fully patched (within 30 days of release): 149/153 workstations (97.4%)
  - 4 devices pending reboot for macOS 15.4 update

## Detections (Q1 2026)
| Severity | Count | Resolved | Open |
|----------|-------|----------|------|
| Critical | 0 | 0 | 0 |
| High | 1 | 1 | 0 |
| Medium | 7 | 7 | 0 |
| Low | 23 | 21 | 2 |
| Informational | 45 | 45 | 0 |

### Notable Detection
- **2026-02-28 HIGH**: Suspicious PowerShell execution on `ACME-WIN-DEV-04`. Investigation: developer running legitimate build script. False positive, exclusion added after security review.

## Unmanaged Devices
- 0 unmanaged devices detected on corporate network (Cloudflare Access enforces device posture check)
