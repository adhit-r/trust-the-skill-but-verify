#!/usr/bin/env python3
"""Validate docs-forge RP3 adversarial package-name npx observer evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "benchmark" / "manifests" / "docs-forge-live-npx-rp3-node-adversarial-package-acquisition.json"
DEFAULT_EXPECTED = REPO_ROOT / "benchmark" / "expected" / "docs-forge" / "npx-rp3-node-adversarial-package-acquisition.json"
DEFAULT_RESULT = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_rp3_node_adversarial_package_acquisition_result.json"
DEFAULT_REPORT = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_rp3_node_adversarial_package_acquisition_report.md"
DEFAULT_TRACE = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_rp3_node_adversarial_package_acquisition_trace.jsonl"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def repo_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise RuntimeError(f"{label}: expected {expected!r}, observed {actual!r}")


def assert_true(value: Any, label: str) -> None:
    if value is not True:
        raise RuntimeError(f"{label}: expected true, observed {value!r}")


def assert_false(value: Any, label: str) -> None:
    if value is not False:
        raise RuntimeError(f"{label}: expected false, observed {value!r}")


def assert_sha256_ref(value: Any, label: str) -> None:
    if not isinstance(value, str) or not value.startswith("sha256:") or len(value) != 71:
        raise RuntimeError(f"{label}: expected sha256 image ref, observed {value!r}")


def assert_no_local_paths(paths: list[Path]) -> None:
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for forbidden in ("/Users/", "/private/var/folders/", "/var/folders/", "/tmp/skilldiff-"):
            if forbidden in text:
                raise RuntimeError(f"{path}: local path leakage detected: {forbidden}")


def assert_no_public_registry_text(paths: list[Path]) -> None:
    public_markers = ("registry.npmjs.org", "https://registry.npmjs.org", "http://registry.npmjs.org")
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for marker in public_markers:
            if marker in text:
                raise RuntimeError(f"{path}: public registry marker observed: {marker}")


def node_major(version: Any) -> int:
    if not isinstance(version, str):
        return 0
    try:
        return int(version.removeprefix("v").split(".", 1)[0])
    except ValueError:
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--expected", type=Path, default=DEFAULT_EXPECTED)
    parser.add_argument("--result", type=Path, default=DEFAULT_RESULT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--trace", type=Path, default=DEFAULT_TRACE)
    args = parser.parse_args(argv)

    manifest_path = repo_path(args.manifest)
    expected_path = repo_path(args.expected)
    result_path = repo_path(args.result)
    report_path = repo_path(args.report)
    trace_path = repo_path(args.trace)
    manifest = load_json(manifest_path)
    expected = load_json(expected_path)
    result = load_json(result_path)

    assert_equal(manifest.get("manifest_id"), "docs-forge-live-npx-rp3-node-adversarial-package-acquisition", "manifest_id")
    assert_equal(result.get("artifact_id"), "docs-forge-live-npx-rp3-node-adversarial-package-acquisition", "artifact_id")
    assert_equal(manifest.get("excluded_from_mvp_runtime_counts"), True, "manifest excluded_from_mvp_runtime_counts")
    assert_equal(result.get("excluded_from_mvp_runtime_counts"), True, "result excluded_from_mvp_runtime_counts")
    assert_equal(manifest.get("execution_level"), "live_rp3_node_container_package_name_npx_fail_closed_observer", "manifest execution_level")
    assert_equal(result.get("execution_level"), "live_rp3_node_container_package_name_npx_fail_closed_observer", "result execution_level")
    assert_equal(manifest.get("evidence_level"), "bounded_docker_network_none_loopback_registry_package_name_npx_attempt", "manifest evidence_level")
    assert_equal(result.get("evidence_level"), "bounded_docker_network_none_loopback_registry_package_name_npx_attempt", "result evidence_level")
    assert_true(result.get("safe_to_publish"), "result safe_to_publish")
    assert_false(result.get("real_secrets_present"), "result real_secrets_present")
    assert_equal(result.get("trace_ref"), trace_path.relative_to(REPO_ROOT).as_posix(), "trace_ref")
    assert_equal(result.get("runtime_profile"), expected["expected_runtime_profile"], "runtime_profile")

    runtime_boundary = manifest.get("runtime_boundary", {})
    assert_sha256_ref(runtime_boundary.get("container_image_ref"), "manifest container_image_ref")
    assert_sha256_ref(result.get("container_image_ref"), "result container_image_ref")
    assert_equal(result.get("container_image_ref"), runtime_boundary.get("container_image_ref"), "container image ref")
    assert_equal(runtime_boundary.get("network_mode"), expected["expected_docker_network_mode"], "runtime network_mode")
    assert_equal(runtime_boundary.get("read_only_rootfs"), expected["expected_read_only_rootfs"], "runtime read_only_rootfs")
    assert_equal(runtime_boundary.get("docker_socket_mounted"), expected["expected_docker_socket_mounted"], "runtime docker_socket_mounted")

    for field in manifest.get("prohibited_live_fields", []):
        if field in manifest:
            raise RuntimeError(f"{manifest_path}: prohibited field present in live manifest: {field}")
    for ref in [
        manifest.get("task_ref"),
        manifest.get("contract_ref"),
        manifest.get("expected_output_ref"),
        runtime_boundary.get("dockerfile_ref"),
    ]:
        if not isinstance(ref, str) or not ref:
            raise RuntimeError(f"{manifest_path}: invalid reference {ref!r}")
        if not (REPO_ROOT / ref).exists():
            raise FileNotFoundError(f"{manifest_path}: missing reference target {ref}")

    preflight = result.get("preflight", {})
    assert_true(preflight.get("passed"), "preflight passed")
    assert_equal(preflight.get("exit_code"), 0, "preflight exit_code")
    assert_equal(preflight.get("docker_network_mode"), "none", "preflight docker_network_mode")
    assert_true(preflight.get("read_only_rootfs"), "preflight read_only_rootfs")
    if node_major(preflight.get("versions", {}).get("node_version")) < expected["minimum_node_major"]:
        raise RuntimeError(f"preflight node version below minimum: {preflight.get('versions', {}).get('node_version')!r}")
    for version_key in ("npm_version", "npx_version", "strace_version", "python_version"):
        if not preflight.get("versions", {}).get(version_key):
            raise RuntimeError(f"preflight missing {version_key}")

    aggregate = result.get("aggregate", {})
    expected_aggregate = {
        "commands_run": expected["expected_total_commands"],
        "commands_succeeded": expected["expected_preflight_commands"],
        "commands_failed_closed": 1,
        "container_preflight_commands_run": expected["expected_preflight_commands"],
        "workload_commands_run": expected["expected_workload_commands"],
        "docker_container_commands_run": expected["expected_total_commands"],
        "docker_network_none_commands_run": expected["expected_total_commands"],
        "docker_read_only_rootfs_commands_run": expected["expected_total_commands"],
        "docker_socket_mounts_observed": 0,
        "npx_commands_executed": 1,
        "npx_package_name_commands_executed": expected["expected_package_name_npx_attempts"],
        "npx_local_tarball_commands_executed": expected["expected_local_tarball_npx_executions"],
        "registry_acquisition_attempts_observed": 1,
        "registry_acquisitions_observed": expected["expected_registry_acquisition_successes"],
        "public_registry_acquisitions_observed": expected["expected_public_registry_acquisitions"],
        "package_install_commands_executed": expected["expected_package_install_commands"],
        "lifecycle_scripts_executed": expected["expected_lifecycle_scripts_executed"],
        "source_mutations_observed": expected["expected_source_mutations"],
        "synthetic_home_mutations_observed": expected["expected_home_mutations"],
        "loopback_registry_events_observed": 1,
        "network_events_observed": 1,
        "public_internet_contact_observed": expected["expected_public_internet_contact_observed"],
        "public_internet_contact_measured": False,
        "packet_capture_enabled": False,
        "runtime_drift_counts_changed": False,
        "runtime_drift_claims_added": expected["expected_runtime_drift_claims"],
        "pairwise_disagreements_added": 0,
        "canonical_traces_added": 0,
        "canonical_results_added": 0,
        "live_traces_added": expected["expected_live_traces"],
    }
    for key, value in expected_aggregate.items():
        assert_equal(aggregate.get(key), value, f"aggregate.{key}")
    cache_mutations = aggregate.get("ephemeral_npm_cache_mutations_observed")
    if not isinstance(cache_mutations, int) or cache_mutations < 0:
        raise RuntimeError(f"aggregate.ephemeral_npm_cache_mutations_observed: expected non-negative int, observed {cache_mutations!r}")

    cases = result.get("cases")
    if not isinstance(cases, list) or len(cases) != 1:
        raise RuntimeError(f"{result_path}: expected one case")
    case = cases[0]
    assert_equal(case.get("case_id"), "rp3_node_package_name_npx_loopback_registry_fail_closed", "case_id")
    assert_true(case.get("passed"), "case passed")
    assert_false(case.get("dry_run"), "case dry_run")
    assert_true(case.get("expected_fail_closed"), "expected_fail_closed")
    assert_true(case.get("fail_closed_observed"), "fail_closed_observed")
    assert_equal(case.get("docker_network_mode"), "none", "case docker_network_mode")
    assert_true(case.get("read_only_rootfs"), "case read_only_rootfs")
    assert_equal(case.get("docker_user"), "1000:1000", "case docker_user")
    assert_false(case.get("docker_socket_mounted"), "case docker_socket_mounted")
    assert_true(case.get("npx_package_name_execution"), "npx_package_name_execution")
    assert_false(case.get("npx_uses_local_tarball"), "npx_uses_local_tarball")
    assert_true(case.get("ignore_scripts"), "ignore_scripts")
    assert_equal(case.get("registry_url"), expected["expected_registry_url"], "registry_url")
    assert_equal(case.get("registry_endpoint_class"), expected["allowed_network_endpoint_class"], "registry_endpoint_class")
    assert_true(case.get("registry_acquisition_attempted"), "registry_acquisition_attempted")
    assert_false(case.get("registry_acquisition_succeeded"), "registry_acquisition_succeeded")
    assert_false(case.get("public_registry_acquisition_executed"), "public_registry_acquisition_executed")
    assert_false(case.get("package_install_executed"), "package_install_executed")
    assert_false(case.get("lifecycle_scripts_executed"), "lifecycle_scripts_executed")
    assert_false(case.get("help_marker_observed"), "help_marker_observed")
    assert_equal(case.get("source_mutation_count"), expected["expected_source_mutations"], "source_mutation_count")
    assert_equal(case.get("home_mutation_count"), expected["expected_home_mutations"], "home_mutation_count")
    assert_true(case.get("loopback_registry_event_observed"), "loopback_registry_event_observed")
    assert_equal(case.get("network_events_observed"), 1, "network_events_observed")
    assert_false(case.get("public_registry_url_observed"), "public_registry_url_observed")
    assert_false(case.get("public_internet_contact_observed"), "public_internet_contact_observed")
    assert_false(case.get("public_internet_contact_measured"), "public_internet_contact_measured")
    assert_false(case.get("packet_capture_enabled"), "packet_capture_enabled")
    npx_exit = case.get("npx_exit_code")
    if not isinstance(npx_exit, int) or npx_exit == 0:
        raise RuntimeError(f"{result_path}: expected nonzero npx_exit_code, observed {npx_exit!r}")
    npx_argv = case.get("npx_argv", [])
    if not isinstance(npx_argv, list) or npx_argv != ["npx", "--yes", "--registry", expected["expected_registry_url"], "docs-forge", "--help"]:
        raise RuntimeError(f"{result_path}: unexpected npx argv {npx_argv!r}")
    npx_docker_argv = case.get("npx_docker_argv", [])
    if not isinstance(npx_docker_argv, list):
        raise RuntimeError(f"{result_path}: npx_docker_argv is not a list")
    for required in ("--network=none", "--read-only", "--user=1000:1000", "--tmpfs=/tmp"):
        if required not in npx_docker_argv:
            raise RuntimeError(f"{result_path}: npx docker argv missing {required}")
    if any("target=/workspace/repo" in str(value) for value in npx_docker_argv):
        raise RuntimeError(f"{result_path}: npx docker argv should not mount source checkout")

    sys.path.insert(0, str(REPO_ROOT / "src"))
    from skilldiff.traces import validate_trace_file

    events = validate_trace_file(trace_path)
    profiles = {event["runtime_profile"] for event in events}
    assert_equal(profiles, {expected["expected_runtime_profile"]}, "trace runtime_profile")
    event_types = {event["event_type"] for event in events}
    for event_type in {"run.start", "capability.snapshot", "activation.select", "approval.decision", "shell.exec", "network.connect", "process.exit", "output.generated", "cleanup.observe", "run.end"}:
        if event_type not in event_types:
            raise RuntimeError(f"{trace_path}: missing trace event type {event_type}")
    network_events = [event for event in events if event["event_type"].startswith("network.")]
    if len(network_events) != 1:
        raise RuntimeError(f"{trace_path}: expected one network event, observed {len(network_events)}")
    network_event = network_events[0]
    assert_equal(network_event.get("event_status"), "failed", "network event_status")
    assert_equal(network_event.get("target"), "127.0.0.1:9", "network target")
    assert_equal(network_event.get("metadata", {}).get("endpoint_class"), expected["allowed_network_endpoint_class"], "network endpoint_class")
    shell_targets = [event.get("target") for event in events if event["event_type"] == "shell.exec"]
    assert_equal(shell_targets, ["container-preflight", "npx"], "trace shell.exec targets")
    npx_exit_events = [event for event in events if event["event_type"] == "process.exit" and event.get("target") == "npx"]
    if len(npx_exit_events) != 1:
        raise RuntimeError(f"{trace_path}: expected one npx process.exit event")
    assert_equal(npx_exit_events[0].get("metadata", {}).get("adapter_outcome"), "failed_closed", "npx process adapter_outcome")

    assert_no_local_paths([result_path, report_path, trace_path])
    assert_no_public_registry_text([result_path, report_path, trace_path])

    print("docs-forge live RP3 Node npx adversarial package-acquisition verified")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"docs-forge live RP3 Node npx adversarial package-acquisition validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
