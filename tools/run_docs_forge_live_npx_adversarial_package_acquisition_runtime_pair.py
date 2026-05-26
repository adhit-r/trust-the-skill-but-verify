#!/usr/bin/env python3
"""Run bounded docs-forge adversarial package-name npx runtime-pair checks."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "benchmark" / "manifests" / "docs-forge-live-npx-adversarial-package-acquisition-runtime-pair.json"
EXPECTED_PATH = REPO_ROOT / "benchmark" / "expected" / "docs-forge" / "npx-adversarial-package-acquisition-runtime-pair.json"
RP3_MANIFEST_PATH = REPO_ROOT / "benchmark" / "manifests" / "docs-forge-live-npx-rp3-node-adversarial-package-acquisition.json"
DEFAULT_OUTPUT_JSON = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_adversarial_package_acquisition_runtime_pair_result.json"
DEFAULT_OUTPUT_MD = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_adversarial_package_acquisition_runtime_pair_report.md"
DEFAULT_HOST_JSON = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_adversarial_package_acquisition_runtime_pair_host_result.json"
DEFAULT_HOST_MD = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_adversarial_package_acquisition_runtime_pair_host_report.md"
DEFAULT_HOST_TRACE = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_adversarial_package_acquisition_runtime_pair_host_trace.jsonl"
DEFAULT_RP3_JSON = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_adversarial_package_acquisition_runtime_pair_rp3_result.json"
DEFAULT_RP3_MD = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_adversarial_package_acquisition_runtime_pair_rp3_report.md"
DEFAULT_RP3_TRACE = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_adversarial_package_acquisition_runtime_pair_rp3_trace.jsonl"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_required(argv: list[str]) -> None:
    completed = subprocess.run(argv, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(argv)}\n"
            f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )


def observe_version(argv: list[str]) -> str:
    completed = subprocess.run(argv, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        return "unavailable"
    return completed.stdout.strip().splitlines()[0] if completed.stdout.strip() else "unavailable"


def case_for(result: dict[str, Any]) -> dict[str, Any]:
    cases = result.get("cases")
    if not isinstance(cases, list) or len(cases) != 1:
        raise RuntimeError(f"{result.get('artifact_id')}: expected exactly one case")
    return cases[0]


def aggregate_sum(results: list[dict[str, Any]], field: str) -> int:
    return sum(int(result.get("aggregate", {}).get(field, 0)) for result in results)


def npx_command_shape(case: dict[str, Any]) -> list[str]:
    argv = case.get("npx_argv", [])
    if not isinstance(argv, list):
        return []
    return [str(value) for value in argv]


def compare_pair(host_result: dict[str, Any], rp3_result: dict[str, Any]) -> dict[str, Any]:
    host_case = case_for(host_result)
    rp3_case = case_for(rp3_result)
    child_results = [host_result, rp3_result]
    child_cases = [host_case, rp3_case]
    checks = {
        "both_child_results_passed": bool(host_case.get("passed")) and bool(rp3_case.get("passed")),
        "both_failed_closed": bool(host_case.get("fail_closed_observed")) and bool(rp3_case.get("fail_closed_observed")),
        "same_registry_url": host_case.get("registry_url") == rp3_case.get("registry_url"),
        "same_registry_endpoint_class": host_case.get("registry_endpoint_class") == rp3_case.get("registry_endpoint_class"),
        "same_npx_command_shape": npx_command_shape(host_case) == npx_command_shape(rp3_case),
        "both_package_name_npx": all(bool(case.get("npx_package_name_execution")) for case in child_cases),
        "no_local_tarball_npx": not any(bool(case.get("npx_uses_local_tarball")) for case in child_cases),
        "no_successful_registry_acquisition": aggregate_sum(child_results, "registry_acquisitions_observed") == 0,
        "no_public_registry_acquisition": aggregate_sum(child_results, "public_registry_acquisitions_observed") == 0,
        "no_package_install_commands": aggregate_sum(child_results, "package_install_commands_executed") == 0,
        "no_lifecycle_scripts": aggregate_sum(child_results, "lifecycle_scripts_executed") == 0,
        "no_help_execution": not any(bool(case.get("help_marker_observed")) for case in child_cases),
        "no_source_mutations": sum(int(case.get("source_mutation_count", 0)) for case in child_cases) == 0,
        "no_home_mutations": sum(int(case.get("home_mutation_count", 0)) for case in child_cases) == 0,
        "same_loopback_registry_event_observed": all(bool(case.get("loopback_registry_event_observed")) for case in child_cases),
        "no_public_internet_contact": not any(bool(case.get("public_internet_contact_observed")) for case in child_cases),
        "no_runtime_drift_claims_added": aggregate_sum(child_results, "runtime_drift_claims_added") == 0,
    }
    failed_checks = sorted(key for key, value in checks.items() if not value)
    informational = {
        "node_versions": {
            host_result["runtime_profile"]: observe_version(["node", "--version"]),
            rp3_result["runtime_profile"]: rp3_result.get("preflight", {}).get("versions", {}).get("node_version"),
        },
        "npm_versions": {
            host_result["runtime_profile"]: observe_version(["npm", "--version"]),
            rp3_result["runtime_profile"]: rp3_result.get("preflight", {}).get("versions", {}).get("npm_version"),
        },
        "npx_versions": {
            host_result["runtime_profile"]: observe_version(["npx", "--version"]),
            rp3_result["runtime_profile"]: rp3_result.get("preflight", {}).get("versions", {}).get("npx_version"),
        },
        "npm_cache_mutation_counts": {
            host_result["runtime_profile"]: host_case.get("npm_cache_mutation_count"),
            rp3_result["runtime_profile"]: rp3_case.get("npm_cache_mutation_count"),
        },
        "npx_exit_codes": {
            host_result["runtime_profile"]: host_case.get("npx_exit_code"),
            rp3_result["runtime_profile"]: rp3_case.get("npx_exit_code"),
        },
        "npx_stderr_sha256": {
            host_result["runtime_profile"]: host_case.get("npx_stderr_sha256"),
            rp3_result["runtime_profile"]: rp3_case.get("npx_stderr_sha256"),
        },
    }
    return {
        "profile_ids": [host_result["runtime_profile"], rp3_result["runtime_profile"]],
        "checks": checks,
        "failed_checks": failed_checks,
        "required_pair_checks_failed": len(failed_checks),
        "pairwise_disagreements": 0 if not failed_checks else len(failed_checks),
        "informational_differences": informational,
        "informational_differences_are_drift_claims": False,
        "same_exit_code_required": False,
        "exit_code_policy": "nonzero_fail_closed_required_exact_exit_code_informational",
    }


def write_markdown(report: dict[str, Any], output_md: Path) -> None:
    lines = [
        "# docs-forge Live Adversarial npx Runtime-Pair Result",
        "",
        "This artifact records a bounded comparison of the same package-name",
        "`npx --registry http://127.0.0.1:9/ docs-forge --help` fail-closed",
        "probe across a host Node synthetic-home observer and an RP3 Node",
        "container observer.",
        "",
        "| Runtime Profile | npx Exit | Registry | Fail Closed | Source Mutations | Home Mutations | Result |",
        "| --- | ---: | --- | --- | ---: | ---: | --- |",
    ]
    for case in report["cases"]:
        lines.append(
            "| {profile} | {exit_code} | `{registry}` | {fail_closed} | {source} | {home} | {result} |".format(
                profile=case["runtime_profile"],
                exit_code=case["npx_exit_code"],
                registry=case["registry_url"],
                fail_closed="yes" if case["fail_closed_observed"] else "no",
                source=case["source_mutation_count"],
                home=case["home_mutation_count"],
                result="passed" if case["passed"] else "failed",
            )
        )
    lines.extend(["", "## Required Pair Checks", "", "| Check | Result |", "| --- | --- |"])
    for key, value in report["comparison"]["checks"].items():
        lines.append(f"| `{key}` | {'pass' if value else 'fail'} |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- This is an adversarial package-name npx runtime-pair scaffold, not a runtime-drift result.",
            "- Exact nonzero exit-code equality is informational; both profiles must fail closed.",
            "- It does not execute public-registry package acquisition, package install behavior, lifecycle scripts, docs generation, or user/global installation.",
            "- No packet capture was performed.",
        ]
    )
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--container-image-ref")
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--host-json", type=Path, default=DEFAULT_HOST_JSON)
    parser.add_argument("--host-md", type=Path, default=DEFAULT_HOST_MD)
    parser.add_argument("--host-trace", type=Path, default=DEFAULT_HOST_TRACE)
    parser.add_argument("--rp3-json", type=Path, default=DEFAULT_RP3_JSON)
    parser.add_argument("--rp3-md", type=Path, default=DEFAULT_RP3_MD)
    parser.add_argument("--rp3-trace", type=Path, default=DEFAULT_RP3_TRACE)
    args = parser.parse_args(argv)

    source_arg = args.source_root or (Path(os.environ["DOCS_FORGE_SOURCE_ROOT"]) if os.environ.get("DOCS_FORGE_SOURCE_ROOT") else None)
    if source_arg is None:
        raise RuntimeError("DOCS_FORGE_SOURCE_ROOT or --source-root is required for live adversarial npx runtime-pair evidence")
    source_root = source_arg.resolve()
    if not source_root.is_dir():
        raise FileNotFoundError(f"source root does not exist: {source_root}")

    manifest = load_json(MANIFEST_PATH)
    expected = load_json(EXPECTED_PATH)
    rp3_manifest = load_json(RP3_MANIFEST_PATH)
    image_ref = args.container_image_ref or rp3_manifest["runtime_boundary"]["container_image_ref"]
    for path in (args.output_json, args.output_md, args.host_json, args.host_md, args.host_trace, args.rp3_json, args.rp3_md, args.rp3_trace):
        path.parent.mkdir(parents=True, exist_ok=True)

    run_required(
        [
            sys.executable,
            "tools/run_docs_forge_live_npx_adversarial_package_acquisition.py",
            "--source-root",
            str(source_root),
            "--output-json",
            str(args.host_json),
            "--output-md",
            str(args.host_md),
            "--trace",
            str(args.host_trace),
        ]
    )
    run_required(
        [
            sys.executable,
            "tools/run_docs_forge_live_npx_rp3_node_adversarial_package_acquisition.py",
            "--source-root",
            str(source_root),
            "--container-image-ref",
            image_ref,
            "--output-json",
            str(args.rp3_json),
            "--output-md",
            str(args.rp3_md),
            "--trace",
            str(args.rp3_trace),
        ]
    )
    run_required(
        [
            sys.executable,
            "tools/validate_docs_forge_live_npx_adversarial_package_acquisition.py",
            "--result",
            str(args.host_json),
            "--report",
            str(args.host_md),
            "--trace",
            str(args.host_trace),
        ]
    )
    run_required(
        [
            sys.executable,
            "tools/validate_docs_forge_live_npx_rp3_node_adversarial_package_acquisition.py",
            "--result",
            str(args.rp3_json),
            "--report",
            str(args.rp3_md),
            "--trace",
            str(args.rp3_trace),
        ]
    )

    host_result = load_json(args.host_json)
    rp3_result = load_json(args.rp3_json)
    host_case = case_for(host_result)
    rp3_case = case_for(rp3_result)
    comparison = compare_pair(host_result, rp3_result)
    child_results = [host_result, rp3_result]
    report = {
        "schema_version": "0.1",
        "artifact_id": "docs-forge-live-npx-adversarial-package-acquisition-runtime-pair",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "safe_to_publish": True,
        "real_secrets_present": False,
        "excluded_from_mvp_runtime_counts": True,
        "execution_level": manifest["execution_level"],
        "evidence_level": manifest["evidence_level"],
        "source_repo": "adhit-r/docs-forge",
        "source_root": "<DOCS_FORGE_SOURCE_ROOT>",
        "source_commit": manifest["source_boundary"]["fixture_source_commit"],
        "source_tree": manifest["source_boundary"]["fixture_source_tree"],
        "manifest_ref": "benchmark/manifests/docs-forge-live-npx-adversarial-package-acquisition-runtime-pair.json",
        "task_ref": manifest["task_ref"],
        "contract_ref": manifest["contract_ref"],
        "expected_output_ref": manifest["expected_output_ref"],
        "child_result_refs": {
            host_result["runtime_profile"]: {
                "json": args.host_json.resolve().relative_to(REPO_ROOT).as_posix(),
                "markdown": args.host_md.resolve().relative_to(REPO_ROOT).as_posix(),
                "trace": args.host_trace.resolve().relative_to(REPO_ROOT).as_posix(),
            },
            rp3_result["runtime_profile"]: {
                "json": args.rp3_json.resolve().relative_to(REPO_ROOT).as_posix(),
                "markdown": args.rp3_md.resolve().relative_to(REPO_ROOT).as_posix(),
                "trace": args.rp3_trace.resolve().relative_to(REPO_ROOT).as_posix(),
            },
        },
        "result_ref": args.output_json.resolve().relative_to(REPO_ROOT).as_posix(),
        "runtime_profiles": expected["expected_runtime_profiles"],
        "cases": [host_case, rp3_case],
        "comparison": comparison,
        "aggregate": {
            "runtime_profiles_compared": 2,
            "runtime_pair_comparisons_executed": 1,
            "child_results_validated": 2,
            "commands_run": aggregate_sum(child_results, "commands_run"),
            "commands_succeeded": aggregate_sum(child_results, "commands_succeeded"),
            "commands_failed_closed": aggregate_sum(child_results, "commands_failed_closed"),
            "workload_commands_run": expected["expected_workload_commands"],
            "npx_commands_executed": aggregate_sum(child_results, "npx_commands_executed"),
            "npx_package_name_commands_executed": aggregate_sum(child_results, "npx_package_name_commands_executed"),
            "npx_local_tarball_commands_executed": aggregate_sum(child_results, "npx_local_tarball_commands_executed"),
            "registry_acquisition_attempts_observed": aggregate_sum(child_results, "registry_acquisition_attempts_observed"),
            "registry_acquisitions_observed": aggregate_sum(child_results, "registry_acquisitions_observed"),
            "public_registry_acquisitions_observed": aggregate_sum(child_results, "public_registry_acquisitions_observed"),
            "package_install_commands_executed": aggregate_sum(child_results, "package_install_commands_executed"),
            "lifecycle_scripts_executed": aggregate_sum(child_results, "lifecycle_scripts_executed"),
            "source_mutations_observed": int(host_case.get("source_mutation_count", 0)) + int(rp3_case.get("source_mutation_count", 0)),
            "synthetic_home_mutations_observed": int(host_case.get("home_mutation_count", 0)) + int(rp3_case.get("home_mutation_count", 0)),
            "ephemeral_npm_cache_mutations_observed": int(host_case.get("npm_cache_mutation_count", 0)) + int(rp3_case.get("npm_cache_mutation_count", 0)),
            "loopback_registry_events_observed": aggregate_sum(child_results, "loopback_registry_events_observed"),
            "network_events_observed": aggregate_sum(child_results, "network_events_observed"),
            "public_internet_contact_observed": False,
            "public_internet_contact_measured": False,
            "packet_capture_enabled": False,
            "required_pair_checks_failed": comparison["required_pair_checks_failed"],
            "runtime_drift_counts_changed": False,
            "runtime_drift_claims_added": 0,
            "pairwise_disagreements_added": 0,
            "canonical_traces_added": 0,
            "canonical_results_added": 0,
            "live_traces_added": 2,
        },
        "claims_not_supported": [
            "public npm registry acquisition",
            "successful package acquisition",
            "package install behavior",
            "lifecycle-script execution",
            "docs-forge docs-generation workload execution",
            "network egress absence under packet capture",
            "complete Node or npm runtime tracing",
            "runtime-drift claims from adversarial npx package-name runtime-pair scaffold evidence",
        ],
    }
    args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_markdown(report, args.output_md)
    if comparison["failed_checks"]:
        raise RuntimeError(f"docs-forge live adversarial npx runtime pair failed checks: {comparison['failed_checks']}")

    print(args.output_json.resolve().relative_to(REPO_ROOT))
    print(args.output_md.resolve().relative_to(REPO_ROOT))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as exc:
        print(f"docs-forge live adversarial npx runtime pair failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
