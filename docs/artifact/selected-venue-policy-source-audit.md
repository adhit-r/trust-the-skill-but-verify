# Selected Venue Policy Source Audit

Status: official-source audit recorded; final venue-policy freeze still open.

Snapshot date: 2026-06-01, Asia/Kolkata.

This audit records the official-source refresh for the selected target,
`usenix_security_2027_cycle_2`, plus the current top-tier backplan. It does
not claim external submission, final CFP/CFA freeze, public release, completed
human review, or paper-grade readiness.

## Sources Checked

- USENIX Security 2027 official venue page:
  `https://www.usenix.org/conference/usenixsecurity27`
- USENIX Security 2026 official call for papers, used as precedent only:
  `https://www.usenix.org/conference/usenixsecurity26/call-for-papers`
- USENIX Security 2026 official call for artifacts, used as precedent only:
  `https://www.usenix.org/conference/usenixsecurity26/call-for-artifacts`
- NDSS 2027 official call for papers:
  `https://www.ndss-symposium.org/ndss2027/submissions/call-for-papers/`
- NDSS 2027 official call for artifacts:
  `https://www.ndss-symposium.org/ndss2027/submissions/call-for-artifacts/`
- IEEE S&P 2027 official call for papers:
  `https://www.ieee-security.org/TC/SP2027/cfpapers.html`
- ACM CCS 2026 official call for papers:
  `https://www.sigsac.org/ccs/CCS2026/call-for/call-for-papers.html`

## Selected Target Result

- Selected target: `usenix_security_2027_cycle_2`
- Registration deadline: `2027-01-19`
- Paper submission deadline: `2027-01-26`
- Conference dates: `2027-08-11` to `2027-08-13`
- Detailed USENIX Security 2027 CFP/CFA available in tracked source set: `false`
- USENIX Security 2026 detailed policy used as final 2027 policy: `false`
- Final refresh still required before external submission: `true`

## Verification

Run:

```sh
python3 tools/validate_selected_venue_policy_source_audit.py
```

`make verify` runs this validator.

## Boundaries

- This audit records official-source checking only.
- It does not close the final selected-venue policy refresh dependency.
- It does not claim a real HotCRP submission, reviewer receipt, acceptance,
  final anonymous artifact access, finalized AI-use wording, public release, or
  completed human review.
