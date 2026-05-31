# Venue Packaging Pass

Status: selected packaging-profile pass; no external venue submission claimed.

## Profiles

This repository keeps two machine-checked artifact metadata profiles:

- `anonymous_review`: double-blind review metadata. Generated metadata omits
  `repository-code`, replaces the CFF author identity with `Anonymous Artifact
  Authors`, and keeps the license field absent until a real SPDX license is
  selected.
- `public_archive`: deanonymized post-acceptance metadata. Generated metadata
  preserves the repository URL and the current artifact-author placeholder, but
  still omits the CFF license field until a real SPDX license is selected.

The current non-human packaging pass selects `anonymous_review` as the next
external-review profile. This is a packaging decision record, not a claim that
any venue has accepted, reviewed, or received the artifact.

## Verification

Run:

```sh
python3 tools/build_venue_package_metadata.py --replace --output-dir tmp/venue-package-metadata
python3 tools/validate_venue_package_metadata.py --bundle-dir tmp/venue-package-metadata
```

`make verify` runs the same build and validation against a temporary output
directory.

## Boundaries

- Do not publish the deanonymized `CITATION.cff` in a double-blind review
  package.
- Do not encode `NOASSERTION` as a CFF license value. Keep the boundary in
  `docs/artifact/license-boundary.md` until a real SPDX license is selected.
- Do not claim public release readiness, completed human review, reviewer
  agreement, or external submission completion from this metadata pass alone.
