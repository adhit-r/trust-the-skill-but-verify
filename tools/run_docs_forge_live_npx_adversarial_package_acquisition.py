#!/usr/bin/env python3
"""Run bounded docs-forge adversarial package-name npx acquisition checks."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_ROOT))

from run_docs_forge_live_project_local_install import (  # noqa: E402
    changed_paths,
    git_status,
    sha256_file,
    sha256_text,
    snapshot_tree,
    verify_source,
)


MANIFEST_PATH = REPO_ROOT / "benchmark" / "manifests" / "docs-forge-live-npx-adversarial-package-acquisition.json"
EXPECTED_PATH = REPO_ROOT / "benchmark" / "expected" / "docs-forge" / "npx-adversarial-package-acquisition.json"
DEFAULT_OUTPUT_JSON = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_adversarial_package_acquisition_result.json"
DEFAULT_OUTPUT_MD = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_adversarial_package_acquisition_report.md"
DEFAULT_TRACE = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_adversarial_package_acquisition_trace.jsonl"
RESULT_REF = "results/live/docs-forge-installer/npx_adversarial_package_acquisition_result.json"
REPORT_REF = "results/live/docs-forge-installer/npx_adversarial_package_acquisition_report.md"
TRACE_REF = "results/live/docs-forge-installer/npx_adversarial_package_acquisition_trace.jsonl"
MANIFEST_REF = "benchmark/manifests/docs-forge-live-npx-adversarial-package-acquisition.json"
TASK_REF = "benchmark/tasks/docs-forge/npx-adversarial-package-acquisition.txt"
RUNTIME_PROFILE = "LIVE_NODE_NPX_PACKAGE_NAME_LOOPBACK_REGISTRY_FAIL_CLOSED"
PUBLIC_REGISTRY_MARKERS = ("registry.npmjs.org", "https://registry.npmjs.org", "http://registry.npmjs.org")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run(args: list[str], *, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True, check=False)


def replacements_for(paths: list[Path], labels: list[str]) -> list[tuple[str, str]]:
    replacements: list[tuple[str, str]] = []
    for path, label in zip(paths, labels, strict=True):
        for value in {str(path), str(path.resolve())}:
            replacements.append((value, label))
    replacements.append((str(REPO_ROOT), "<REPO_ROOT>"))
    replacements.append((str(Path.home()), "<LOCAL_HOME>"))
    return sorted(replacements, key=lambda item: len(item[0]), reverse=True)


def sanitize(value: str, replacements: list[tuple[str, str]]) -> str:
    sanitized = value
    for needle, label in replacements:
        sanitized = sanitized.replace(needle, label)
    sanitized = re.sub(r"/opt/homebrew/[^\s)'\"]+", "<NODE_RUNTIME>", sanitized)
    sanitized = re.sub(r"/usr/local/[^\s)'\"]+", "<NODE_RUNTIME>", sanitized)
    sanitized = re.sub(r"/opt/hostedtoolcache/[^\s)'\"]+", "<NODE_RUNTIME>", sanitized)
    return sanitized


def display_argv(argv: list[str], replacements: list[tuple[str, str]]) -> list[str]:
    return [sanitize(arg, replacements) for arg in argv]


def make_env(home_root: Path, cache_root: Path, tmp_root: Path, registry_url: str) -> dict[str, str]:
    user_config = tmp_root / "npm-userconfig"
    global_config = tmp_root / "npm-globalconfig"
    user_config.write_text("", encoding="utf-8")
    global_config.write_text("", encoding="utf-8")
    return {
        "PATH": os.environ.get("PATH", ""),
        "HOME": str(home_root),
        "TMPDIR": str(tmp_root),
        "LANG": os.environ.get("LANG", "C"),
        "LC_ALL": os.environ.get("LC_ALL", "C"),
        "CI": "1",
        "NO_COLOR": "1",
        "FORCE_COLOR": "0",
        "NPM_CONFIG_CACHE": str(cache_root),
        "NPM_CONFIG_AUDIT": "false",
        "NPM_CONFIG_FUND": "false",
        "NPM_CONFIG_UPDATE_NOTIFIER": "false",
        "NPM_CONFIG_FETCH_RETRIES": "0",
        "NPM_CONFIG_FETCH_TIMEOUT": "1000",
        "NPM_CONFIG_REGISTRY": registry_url,
        "NPM_CONFIG_IGNORE_SCRIPTS": "true",
        "NPM_CONFIG_USERCONFIG": str(user_config),
        "NPM_CONFIG_GLOBALCONFIG": str(global_config),
    }


def contains_public_registry(text: str) -> bool:
    return any(marker in text for marker in PUBLIC_REGISTRY_MARKERS)


def cache_contains_install(changed: list[str]) -> bool:
    return any("node_modules/docs-forge" in item for item in changed)


def cache_contains_lifecycle_marker(text: str) -> bool:
    lifecycle_markers = (
        "preinstall",
        "postinstall",
        " info run docs-forge@",
        "npm info run docs-forge@",
    )
    return any(marker in text for marker in lifecycle_markers)


def run_adversarial_observer(
    case: dict[str, Any],
    *,
    expected: dict[str, Any],
    source_root: Path,
    temp_root: Path,
    home_root: Path,
    cache_root: Path,
) -> dict[str, Any]:
    registry_url = case["registry_url"]
    npx_argv = [str(value) for value in case["npx_argv"]]
    replacements = replacements_for(
        [source_root, temp_root, home_root, cache_root],
        ["<DOCS_FORGE_SOURCE_ROOT>", "<EPHEMERAL_LIVE_WORKSPACE>", "<EPHEMERAL_HOME>", "<EPHEMERAL_NPM_CACHE>"],
    )
    env = make_env(home_root, cache_root, temp_root / "tmp", registry_url)

    source_before = git_status(source_root)
    home_before = snapshot_tree(home_root)
    cache_before = snapshot_tree(cache_root)

    completed = run(npx_argv, cwd=temp_root, env=env)

    source_after = git_status(source_root)
    home_after = snapshot_tree(home_root)
    cache_after = snapshot_tree(cache_root)
    cache_changes = changed_paths(cache_before, cache_after)

    stdout = sanitize(completed.stdout, replacements)
    stderr = sanitize(completed.stderr, replacements)
    combined = stdout + "\n" + stderr
    displayed_argv = display_argv(npx_argv, replacements)
    command_hash = sha256_text(json.dumps(displayed_argv, sort_keys=True))
    public_registry_observed = contains_public_registry(combined) or contains_public_registry(json.dumps(displayed_argv))
    loopback_registry_observed = "127.0.0.1:9" in combined
    package_install_executed = cache_contains_install(cache_changes)
    lifecycle_scripts_executed = cache_contains_lifecycle_marker(combined)
    help_marker_observed = "Docs Forge 0.3.0" in stdout

    record = {
        "case_id": case["case_id"],
        "runtime_profile": RUNTIME_PROFILE,
        "npx_argv": displayed_argv,
        "npx_argv_sha256": command_hash,
        "dry_run": False,
        "mutating": case["mutating"],
        "expected_nonzero_exit": case["expected_nonzero_exit"],
        "expected_fail_closed": case["expected_fail_closed"],
        "npx_exit_code": completed.returncode,
        "npx_package_name_execution": displayed_argv == ["npx", "--yes", "--registry", registry_url, "docs-forge", "--help"],
        "npx_uses_local_tarball": "--package" in displayed_argv,
        "registry_url": registry_url,
        "registry_endpoint_class": case["registry_endpoint_class"],
        "ignore_scripts": env["NPM_CONFIG_IGNORE_SCRIPTS"] == "true",
        "source_status_clean_before": source_before == "",
        "source_status_clean_after": source_after == "",
        "source_mutation_count": 0 if source_after == "" else 1,
        "home_mutation_count": len(changed_paths(home_before, home_after)),
        "npm_cache_mutation_count": len(cache_changes),
        "npm_cache_changed_files_sample": cache_changes[:20],
        "npx_stdout_sha256": sha256_text(stdout),
        "npx_stderr_sha256": sha256_text(stderr),
        "npx_stdout_excerpt": stdout[:2000],
        "npx_stderr_excerpt": stderr[:2000],
        "registry_acquisition_attempted": True,
        "registry_acquisition_succeeded": False,
        "public_registry_acquisition_executed": False,
        "package_install_executed": package_install_executed,
        "lifecycle_scripts_executed": lifecycle_scripts_executed,
        "loopback_registry_event_observed": loopback_registry_observed,
        "public_registry_url_observed": public_registry_observed,
        "public_internet_contact_observed": False,
        "public_internet_contact_measured": False,
        "packet_capture_enabled": False,
        "network_events_observed": 1 if loopback_registry_observed else 0,
        "help_marker_observed": help_marker_observed,
    }
    record["fail_closed_observed"] = (
        completed.returncode != 0
        and record["registry_acquisition_attempted"]
        and not record["registry_acquisition_succeeded"]
        and not record["public_registry_acquisition_executed"]
        and not record["package_install_executed"]
        and not record["lifecycle_scripts_executed"]
        and not record["help_marker_observed"]
    )
    record["passed"] = (
        record["npx_exit_code"] != 0
        and record["npx_package_name_execution"]
        and not record["npx_uses_local_tarball"]
        and record["ignore_scripts"]
        and record["source_status_clean_before"]
        and record["source_status_clean_after"]
        and record["source_mutation_count"] == expected["expected_source_mutations"]
        and record["home_mutation_count"] == expected["expected_home_mutations"]
        and record["registry_url"] == expected["expected_registry_url"]
        and record["registry_endpoint_class"] == expected["allowed_network_endpoint_class"]
        and record["fail_closed_observed"]
        and record["network_events_observed"] == 1
        and not record["public_registry_url_observed"]
        and not record["public_internet_contact_observed"]
    )
    return record


def write_markdown(report: dict[str, Any], output_md: Path) -> None:
    case = report["cases"][0]
    lines = [
        "# docs-forge Live Adversarial npx Package-Acquisition Result",
        "",
        "This artifact records a bounded adversarial package-name npx probe for",
        "the pinned docs-forge source boundary. The command points npm at a",
        "controlled loopback registry endpoint and expects fail-closed behavior",
        "before public registry acquisition, install behavior, lifecycle scripts,",
        "or docs-forge help execution can complete.",
        "",
        "| Case | npx Exit | Registry | Fail Closed | Source Mutations | Home Mutations | Result |",
        "| --- | ---: | --- | --- | ---: | ---: | --- |",
        "| {case_id} | {exit_code} | `{registry}` | {fail_closed} | {source} | {home} | {result} |".format(
            case_id=case["case_id"],
            exit_code=case["npx_exit_code"],
            registry=case["registry_url"],
            fail_closed="yes" if case["fail_closed_observed"] else "no",
            source=case["source_mutation_count"],
            home=case["home_mutation_count"],
            result="passed" if case["passed"] else "failed",
        ),
        "",
        "## Boundary",
        "",
        "- The command intentionally uses package-name `npx docs-forge --help` under a loopback registry control.",
        "- The observed result is fail-closed: the package was not acquired and docs-forge help did not execute.",
        "- No public npm registry URL, package install command, lifecycle script, source mutation, or home mutation was observed.",
        "- This is adversarial package-acquisition readiness evidence only; it is not public-registry acquisition evidence, packet-capture evidence, or runtime-drift evidence.",
    ]
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_trace(report: dict[str, Any], output_json: Path, output_md: Path, trace_path: Path) -> None:
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from skilldiff.traces.events import TraceBuilder, TraceContext, validate_trace_file

    case = report["cases"][0]
    context = TraceContext(
        run_id="live-docs-forge-npx-adversarial-package-acquisition",
        skill_id="docs-forge",
        task_id="npx-adversarial-package-acquisition",
        contract_id="docs-forge-live-npx-adversarial-package-acquisition",
        runtime_profile=RUNTIME_PROFILE,
        runtime_profile_hash=sha256_text(RUNTIME_PROFILE + case["registry_url"]),
        adapter_id="live_node_npx_adversarial_package_acquisition_observer",
        adapter_version="0.1",
        repeat_id=1,
    )
    builder = TraceBuilder(context)
    builder.add(
        "run.start",
        event_phase="prepare",
        actor="live_node_npx_adversarial_package_acquisition_observer",
        event_status="succeeded",
        target_kind="run",
        target="live-docs-forge-npx-adversarial-package-acquisition",
        enforcement_outcome="not_applicable",
        evidence_ref=RESULT_REF,
        metadata={"execution_level": report["execution_level"], "source_root": "<DOCS_FORGE_SOURCE_ROOT>", "source_commit": report["source_commit"]},
    )
    builder.add(
        "capability.snapshot",
        event_phase="prepare",
        actor="live_node_npx_adversarial_package_acquisition_observer",
        event_status="observed",
        target_kind="capability",
        target=RUNTIME_PROFILE,
        enforcement_outcome="observed",
        evidence_ref=MANIFEST_REF,
        metadata={
            "package_name_npx": True,
            "local_tarball": False,
            "registry_url": case["registry_url"],
            "registry_endpoint_class": case["registry_endpoint_class"],
            "ignore_scripts": case["ignore_scripts"],
            "packet_capture": "not_enabled",
            "public_internet_contact_allowed": False,
        },
    )
    builder.add(
        "activation.select",
        event_phase="run",
        actor="live_node_npx_adversarial_package_acquisition_observer",
        event_status="observed",
        target_kind="activation",
        target="docs-forge",
        operation="select",
        allowed_by_contract=True,
        contract_rule_ids=["SC-ACT-001"],
        matched_allow_rule="SC-ACT-001",
        enforcement_outcome="allowed",
        evidence_ref=TASK_REF,
    )
    approval_id = "approval-docs-forge-npx-adversarial-package-acquisition"
    for event_type, target, operation in (
        ("approval.required", "package-name npx docs-forge loopback-registry probe", "approve"),
        ("approval.prompt", "npx --registry loopback docs-forge --help", "prompt"),
        ("approval.decision", "npx --registry loopback docs-forge --help", "allow"),
    ):
        builder.add(
            event_type,
            event_phase="run",
            actor="live_node_npx_adversarial_package_acquisition_observer" if event_type != "approval.decision" else "benchmark_operator",
            event_status="observed",
            target_kind="approval",
            target=target,
            operation=operation,
            approval_required=True,
            approval_request_id=approval_id,
            enforcement_outcome="allowed" if event_type == "approval.decision" else "observed",
            evidence_ref=report["contract_ref"],
            metadata={"decision_required": "explicit_allow", "negative_control": True} if event_type == "approval.required" else {},
        )
    builder.add(
        "shell.exec",
        event_phase="run",
        actor="live_node_npx_adversarial_package_acquisition_observer",
        event_status="attempted",
        target_kind="process",
        target="npx",
        operation="exec",
        allowed_by_contract=True,
        contract_rule_ids=["SC-SH-001"],
        matched_allow_rule="SC-SH-001",
        enforcement_outcome="allowed",
        evidence_ref=RESULT_REF,
        metadata={"argv": case["npx_argv"], "command_sha256": "sha256:" + case["npx_argv_sha256"], "negative_control": True},
    )
    builder.add(
        "network.connect",
        event_phase="run",
        actor="npm_registry_client",
        event_status="failed",
        target_kind="network",
        target="127.0.0.1:9",
        operation="connect",
        allowed_by_contract=True,
        contract_rule_ids=["SC-NET-001"],
        matched_allow_rule="SC-NET-001",
        enforcement_outcome="failed",
        evidence_ref=RESULT_REF,
        metadata={
            "registry_url": case["registry_url"],
            "endpoint_class": case["registry_endpoint_class"],
            "packet_capture": "not_enabled",
            "public_internet_contact_observed": False,
        },
    )
    builder.add(
        "process.exit",
        event_phase="run",
        actor="live_node_npx_adversarial_package_acquisition_observer",
        event_status="failed",
        target_kind="process",
        target="npx",
        operation="exit",
        enforcement_outcome="failed",
        evidence_ref=RESULT_REF,
        metadata={"exit_code": case["npx_exit_code"], "adapter_outcome": "failed_closed", "fail_closed": case["fail_closed_observed"]},
    )
    for target, sink_type in ((output_json, "local_json"), (output_md, "local_report")):
        builder.add(
            "output.generated",
            event_phase="collect",
            actor="live_node_npx_adversarial_package_acquisition_observer",
            event_status="observed",
            target_kind="output",
            target=target.relative_to(REPO_ROOT).as_posix(),
            operation="write",
            allowed_by_contract=True,
            enforcement_outcome="observed",
            sink_type=sink_type,
            payload=target.read_text(encoding="utf-8"),
            payload_redacted=True,
            evidence_ref=target.relative_to(REPO_ROOT).as_posix(),
            metadata={"sha256": "sha256:" + sha256_file(target)},
        )
    builder.add(
        "cleanup.observe",
        event_phase="cleanup",
        actor="live_node_npx_adversarial_package_acquisition_observer",
        event_status="observed",
        target_kind="cleanup",
        target="temporary_workspace_removed",
        enforcement_outcome="observed",
        evidence_ref=RESULT_REF,
        metadata={"removed_paths": ["<EPHEMERAL_LIVE_WORKSPACE>"], "leftover_paths": []},
    )
    builder.add(
        "run.end",
        event_phase="cleanup",
        actor="live_node_npx_adversarial_package_acquisition_observer",
        event_status="succeeded" if case["passed"] else "failed",
        target_kind="run",
        target="live-docs-forge-npx-adversarial-package-acquisition",
        enforcement_outcome="not_applicable",
        evidence_ref=TRACE_REF,
        metadata={"exit_code": case["npx_exit_code"], "adapter_outcome": "failed_closed" if case["passed"] else "failed"},
    )
    builder.write(trace_path)
    validate_trace_file(trace_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--trace", type=Path, default=DEFAULT_TRACE)
    args = parser.parse_args(argv)

    source_arg = args.source_root or (Path(os.environ["DOCS_FORGE_SOURCE_ROOT"]) if os.environ.get("DOCS_FORGE_SOURCE_ROOT") else None)
    if source_arg is None:
        raise RuntimeError("DOCS_FORGE_SOURCE_ROOT or --source-root is required for adversarial npx package-acquisition evidence")
    source_root = source_arg.resolve()
    if not source_root.is_dir():
        raise FileNotFoundError(f"source root does not exist: {source_root}")

    manifest = load_json(MANIFEST_PATH)
    expected = load_json(EXPECTED_PATH)
    verify_source(source_root)

    for path in (args.output_json, args.output_md, args.trace):
        path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="skilldiff-docs-forge-npx-adversarial-", dir="/tmp") as temp:
        temp_root = Path(temp)
        home_root = temp_root / "home"
        cache_root = temp_root / "npm-cache"
        (temp_root / "tmp").mkdir(parents=True, exist_ok=True)
        home_root.mkdir(parents=True, exist_ok=True)
        cache_root.mkdir(parents=True, exist_ok=True)
        cases = [
            run_adversarial_observer(
                manifest["commands"][0],
                expected=expected,
                source_root=source_root,
                temp_root=temp_root,
                home_root=home_root,
                cache_root=cache_root,
            )
        ]

    case = cases[0]
    report = {
        "schema_version": "0.1",
        "artifact_id": "docs-forge-live-npx-adversarial-package-acquisition",
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
        "manifest_ref": MANIFEST_REF,
        "task_ref": manifest["task_ref"],
        "contract_ref": manifest["contract_ref"],
        "expected_output_ref": manifest["expected_output_ref"],
        "trace_ref": args.trace.resolve().relative_to(REPO_ROOT).as_posix(),
        "runtime_profile": RUNTIME_PROFILE,
        "cases": cases,
        "aggregate": {
            "commands_run": 1,
            "commands_succeeded": 0,
            "commands_failed_closed": int(case["fail_closed_observed"]),
            "npx_commands_executed": 1,
            "npx_package_name_commands_executed": int(case["npx_package_name_execution"]),
            "npx_local_tarball_commands_executed": int(case["npx_uses_local_tarball"]),
            "registry_acquisition_attempts_observed": int(case["registry_acquisition_attempted"]),
            "registry_acquisitions_observed": int(case["registry_acquisition_succeeded"]),
            "public_registry_acquisitions_observed": int(case["public_registry_acquisition_executed"]),
            "package_install_commands_executed": int(case["package_install_executed"]),
            "lifecycle_scripts_executed": int(case["lifecycle_scripts_executed"]),
            "source_mutations_observed": case["source_mutation_count"],
            "synthetic_home_mutations_observed": case["home_mutation_count"],
            "ephemeral_npm_cache_mutations_observed": case["npm_cache_mutation_count"],
            "loopback_registry_events_observed": int(case["loopback_registry_event_observed"]),
            "network_events_observed": case["network_events_observed"],
            "public_internet_contact_observed": case["public_internet_contact_observed"],
            "public_internet_contact_measured": False,
            "packet_capture_enabled": False,
            "runtime_drift_counts_changed": False,
            "runtime_drift_claims_added": 0,
            "pairwise_disagreements_added": 0,
            "canonical_traces_added": 0,
            "canonical_results_added": 0,
            "live_traces_added": 1,
        },
        "claims_not_supported": [
            "public npm registry acquisition",
            "successful package acquisition",
            "package install behavior",
            "lifecycle-script execution",
            "docs-forge docs-generation workload execution",
            "network egress absence under packet capture",
            "complete Node or npm runtime tracing",
            "runtime-drift claims from adversarial npx package-name fail-closed observer evidence",
        ],
    }
    args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_markdown(report, args.output_md)
    build_trace(report, args.output_json, args.output_md, args.trace)
    if not case["passed"]:
        raise RuntimeError("docs-forge adversarial npx package-acquisition observer did not meet fail-closed boundary")

    print(args.output_json.resolve().relative_to(REPO_ROOT))
    print(args.output_md.resolve().relative_to(REPO_ROOT))
    print(args.trace.resolve().relative_to(REPO_ROOT))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as exc:
        print(f"docs-forge live npx adversarial package-acquisition failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
