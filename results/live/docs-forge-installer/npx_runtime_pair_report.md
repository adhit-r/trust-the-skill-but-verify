# docs-forge Live npx Runtime-Pair Result

This artifact records a bounded comparison of the same local-tarball
`npx --offline` docs-forge help workload across a host Node synthetic-home
observer and an RP3 Node container observer.

| Runtime Profile | npx Exit | Package | Entries | Source Mutations | Home Mutations | Result |
| --- | ---: | --- | ---: | ---: | ---: | --- |
| LIVE_NODE_NPX_LOCAL_TARBALL_SYNTHETIC_HOME | 0 | docs-forge@0.3.0 | 10 | 0 | 0 | passed |
| RP3_NODE_LOCAL_TARBALL_NPX_EXPERIMENTAL | 0 | docs-forge@0.3.0 | 10 | 0 | 0 | passed |

## Required Pair Checks

| Check | Result |
| --- | --- |
| `both_child_results_passed` | pass |
| `same_exit_code` | pass |
| `same_package_identity` | pass |
| `same_package_entry_count` | pass |
| `same_package_file_list` | pass |
| `same_npx_stdout_sha256` | pass |
| `no_missing_stdout_markers` | pass |
| `no_source_mutations` | pass |
| `no_home_mutations` | pass |
| `no_registry_acquisitions` | pass |
| `no_package_install_commands` | pass |
| `no_lifecycle_scripts` | pass |
| `no_network_events` | pass |
| `no_runtime_drift_claims_added` | pass |

## Boundary

- This is a local-tarball npx runtime-pair scaffold, not a runtime-drift result.
- It does not execute package-name `npx docs-forge`, npm registry acquisition, package install behavior, docs generation, or user/global installation.
- Node/npm version, npm-cache mutation count, and tarball byte-hash differences are recorded as informational only.
