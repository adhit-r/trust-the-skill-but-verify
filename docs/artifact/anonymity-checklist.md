# Artifact Anonymity Checklist

Status: checklist scaffold for double-blind venue preparation.

## Required Before Anonymous Review

- Run `python3 tools/check_no_local_paths.py`.
- Run `PYTHON_BIN=python3 make verify` from a clean checkout.
- Build and validate anonymous-review metadata:
  `python3 tools/build_venue_package_metadata.py --replace --output-dir tmp/venue-package-metadata`
- Validate anonymous-review metadata:
  `python3 tools/validate_venue_package_metadata.py --bundle-dir tmp/venue-package-metadata`
- Build an anonymous-review candidate bundle:
  `python3 tools/build_artifact_release_bundle.py --replace --packaging-profile anonymous_review --output-dir tmp/artifact-release-bundle-anonymous-review`
- Validate the anonymous-review candidate bundle:
  `python3 tools/validate_artifact_release_bundle.py --packaging-profile anonymous_review --bundle-dir tmp/artifact-release-bundle-anonymous-review`
- Check generated reports for local usernames, hostnames, absolute paths,
  credentials, cookies, auth state, and private source checkout names.
- Keep first-party provenance labels generic unless the venue permits naming.
- Keep `CITATION.cff` anonymous or replace it only after deanonymization.
- Do not use the default local-machine or `public_archive` bundle as a
  double-blind artifact package; those profiles intentionally preserve
  deanonymized repository metadata.
- Verify that generated PDFs, archives, figures, and logs do not contain local
  metadata.

## Blockers

- Any real secret or credential-like value in a tracked artifact.
- Any local host path outside approved placeholders.
- Any claim of public-network exfiltration, commercial-runtime behavior, or
  prevalence without direct evidence and claim-ledger support.
