# Selected Venue Policy Snapshot

Status: current official-source snapshot; no external venue submission claimed.

Snapshot date: 2026-06-01, Asia/Kolkata.

Selected policy target for the next review package:

- `usenix_security_2027_cycle_2`
- Submission packaging profile: `anonymous_review`
- Post-acceptance packaging profile: `public_archive`

The official USENIX Security 2027 page lists conference dates and Cycle 2
submission dates, but the detailed USENIX Security 2027 CFP/CFA was not
available when this snapshot was prepared. The detailed artifact and paper
policy entries therefore use USENIX Security 2026 official policy pages as
precedent, not as final 2027 rules.

## Verification

Run:

```sh
python3 tools/build_venue_package_metadata.py --replace --output-dir tmp/venue-package-metadata
python3 tools/validate_venue_package_metadata.py --bundle-dir tmp/venue-package-metadata
python3 tools/validate_selected_venue_policy.py --venue-metadata-dir tmp/venue-package-metadata
```

`make verify` runs the same checks against a temporary metadata directory.

## Boundaries

- This snapshot does not claim HotCRP submission, reviewer receipt, acceptance,
  public release, completed human review, or final 2027 CFP/CFA freeze.
- Refresh official venue sources immediately before any real external
  submission.
- Do not use the deanonymized `public_archive` profile in a double-blind review
  submission.
- Final AI-use wording still has to match the selected venue's then-current
  policy and submission form.
