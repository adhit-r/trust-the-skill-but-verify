# docs-forge Live Adversarial npx Runtime-Pair Result

This artifact records a bounded comparison of the same package-name
`npx --registry http://127.0.0.1:9/ docs-forge --help` fail-closed
probe across a host Node synthetic-home observer and an RP3 Node
container observer.

| Runtime Profile | npx Exit | Registry | Fail Closed | Source Mutations | Home Mutations | Result |
| --- | ---: | --- | --- | ---: | ---: | --- |
| LIVE_NODE_NPX_PACKAGE_NAME_LOOPBACK_REGISTRY_FAIL_CLOSED | 1 | `http://127.0.0.1:9/` | yes | 0 | 0 | passed |
| RP3_NODE_NPX_PACKAGE_NAME_LOOPBACK_REGISTRY_FAIL_CLOSED | 1 | `http://127.0.0.1:9/` | yes | 0 | 0 | passed |

## Required Pair Checks

| Check | Result |
| --- | --- |
| `both_child_results_passed` | pass |
| `both_failed_closed` | pass |
| `same_registry_url` | pass |
| `same_registry_endpoint_class` | pass |
| `same_npx_command_shape` | pass |
| `both_package_name_npx` | pass |
| `no_local_tarball_npx` | pass |
| `no_successful_registry_acquisition` | pass |
| `no_public_registry_acquisition` | pass |
| `no_package_install_commands` | pass |
| `no_lifecycle_scripts` | pass |
| `no_help_execution` | pass |
| `no_source_mutations` | pass |
| `no_home_mutations` | pass |
| `same_loopback_registry_event_observed` | pass |
| `no_public_internet_contact` | pass |
| `no_runtime_drift_claims_added` | pass |

## Boundary

- This is an adversarial package-name npx runtime-pair scaffold, not a runtime-drift result.
- Exact nonzero exit-code equality is informational; both profiles must fail closed.
- It does not execute public-registry package acquisition, package install behavior, lifecycle scripts, docs generation, or user/global installation.
- No packet capture was performed.
