# License Boundary

Status: explicit local-artifact license boundary.

## Current Boundary

The current artifact contains benchmark-owned synthetic fixtures, generated
results, scripts, schemas, contracts, and documentation. First-party and
public source repositories are represented through pinned provenance metadata,
selected hashes, and sanitized fixtures rather than vendored full source
trees.

This repository currently has no top-level open-source license file.
`CITATION.cff` therefore intentionally omits the optional CFF `license` field,
because that field is for SPDX license identifiers. The release boundary is
`NOASSERTION`, as documented here rather than encoded as an invalid CFF license
value. That is not a missing placeholder: the local artifact bundle is
reproducible and citable, but it does not grant a new redistribution or reuse
license beyond whatever rights are already available for the included source
files and metadata. Before any public archive or artifact-evaluation upload,
the authors must either add a repository license or keep this `NOASSERTION`
boundary visible in the submission materials.

## Before Public Release

- Add final repository license text if the authors want to grant reuse rights
  beyond this `NOASSERTION` boundary.
- Confirm licenses for any first-party or public-skill fixture material that
  is promoted beyond sanitized metadata or synthetic fixtures.
- Keep generated results tied to synthetic data unless explicit permission and
  sanitization review exist.
- Do not vendor third-party source trees into the artifact without license and
  anonymity review.

## Paper Wording

Use "publishable controlled fixture" when the evidence is synthetic or
sanitized. Use "source provenance metadata" when only hashes or commit
metadata are included. Do not imply full product redistribution unless it is
actually licensed and included.
