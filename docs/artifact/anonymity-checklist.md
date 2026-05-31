# Artifact Anonymity Checklist

Status: checklist scaffold for double-blind venue preparation.

## Required Before Anonymous Review

- Run `python3 tools/check_no_local_paths.py`.
- Run `PYTHON_BIN=python3 make verify` from a clean checkout.
- Check generated reports for local usernames, hostnames, absolute paths,
  credentials, cookies, auth state, and private source checkout names.
- Keep first-party provenance labels generic unless the venue permits naming.
- Keep `CITATION.cff` anonymous or replace it only after deanonymization.
- Verify that generated PDFs, archives, figures, and logs do not contain local
  metadata.

## Blockers

- Any real secret or credential-like value in a tracked artifact.
- Any local host path outside approved placeholders.
- Any claim of public-network exfiltration, commercial-runtime behavior, or
  prevalence without direct evidence and claim-ledger support.
