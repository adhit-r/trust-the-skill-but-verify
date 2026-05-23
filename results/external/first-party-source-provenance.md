# First-Party Source Provenance

This artifact verifies that the first-party source repositories referenced by the
publishable fixtures still match their pinned commits, trees, and source hash
lists when checked out from clean ephemeral clones.

| Case | Manifest | Status | Commit | Tree | Pinned Files | Boundary |
| --- | --- | --- | --- | --- | ---: | --- |
| docs-forge | `benchmark/manifests/docs-forge-mini.json` | passed | `40c3693491b4` | `6fbaec7f1656` | 11 | ephemeral_clean_clone_source_provenance_only |
| audit-lens | `benchmark/manifests/audit-lens-acme.json` | passed | `241b584e8e7f` | `1ebe897763e8` | 42 | ephemeral_clean_clone_source_provenance_only |

## Boundary

- This is source-provenance evidence only.
- The full source trees are not vendored into the publishable artifact.
- The real docs-forge Node installer is not executed.
- The full AuditLens product, live connectors, and connector auth flows are not executed.
- No real secrets or public-internet benchmark sinks are introduced by this check.
