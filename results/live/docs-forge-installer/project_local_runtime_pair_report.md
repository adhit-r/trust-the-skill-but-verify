# docs-forge Live Runtime-Pair Install Result

This artifact records bounded live Node runtime-pair evidence for the pinned
docs-forge project-local installer. It compares two local Node executions
against isolated disposable targets: host environment with synthetic HOME
and minimal allowlisted environment with synthetic HOME.

| Runtime Profile | Exit | Target Writes | Unexpected Target Writes | Source Mutations | Home Mutations | Result |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| LIVE_NODE_HOST_ENV_SYNTHETIC_HOME | 0 | 3 | 0 | 0 | 0 | passed |
| LIVE_NODE_MINIMAL_ENV_SYNTHETIC_HOME | 0 | 3 | 0 | 0 | 0 | passed |

## Pairwise Comparison

| Check | Result |
| --- | --- |
| `same_exit_code` | pass |
| `same_argv_sha256` | pass |
| `same_node_version` | pass |
| `same_node_executable_hash` | pass |
| `same_target_initial_snapshot_sha256` | pass |
| `same_target_changed_files` | pass |
| `same_target_changed_file_hashes` | pass |
| `same_stdout_sha256` | pass |
| `same_stderr_sha256` | pass |
| `same_source_skill_sha256` | pass |
| `no_unexpected_target_mutations` | pass |
| `no_source_mutations` | pass |
| `no_home_mutations` | pass |
| `no_env_file_reads` | pass |
| `no_canary_observations` | pass |

## Boundary

- This is live project-local installer evidence, not docs-generation evidence.
- It compares two local Node environment profiles and is excluded from MVP runtime-drift counts.
- It does not run `npx`, install packages, modify user home directories, or execute the Codex marketplace command.
- It does not claim RP2/RP3 runtime drift, public-internet safety under packet capture, or complete Node runtime tracing.
