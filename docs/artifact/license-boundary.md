# License Boundary

Status: release-planning scaffold.

## Current Boundary

The current artifact contains benchmark-owned synthetic fixtures, generated
results, scripts, schemas, contracts, and documentation. First-party source
repositories are represented through pinned provenance metadata, selected
hashes, and sanitized fixtures rather than vendored full source trees.

## Before Public Release

- Add final repository license text or a clear `NOASSERTION` explanation.
- Confirm licenses for any first-party or public-skill fixture material.
- Keep generated results tied to synthetic data unless explicit permission and
  sanitization review exist.
- Do not vendor third-party source trees into the artifact without license and
  anonymity review.

## Paper Wording

Use "publishable controlled fixture" when the evidence is synthetic or
sanitized. Use "source provenance metadata" when only hashes or commit
metadata are included. Do not imply full product redistribution unless it is
actually licensed and included.
