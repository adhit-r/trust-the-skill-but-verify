#!/usr/bin/env python3
"""Validate the RP1 restricted-hosted current-subset scaffold."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment guard
    raise SystemExit("PyYAML is required to validate the RP1 scaffold") from exc


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = REPO_ROOT / "results" / "fixtures" / "rp1-restricted-hosted"
REPORT_CARD = REPORT_ROOT / "report_card.json"
SCAFFOLD_STATUS = REPORT_ROOT / "scaffold_status.json"
MANIFEST = REPO_ROOT / "benchmark" / "manifests" / "rp1-restricted-hosted-mvp.json"
PROFILE = REPO_ROOT / "runtimes" / "profiles" / "RP1_restricted_hosted.yaml"
CLI_PATH = REPO_ROOT / "src" / "skilldiff" / "cli.py"
EXPECTED_CASE_COUNT = 12
EXPECTED_FAMILIES = ["audit-lens", "docs-forge", "network-egress", "repo-audit"]
EXPECTED_RUNTIME_PROFILES = ["RP1", "RP2", "RP3"]
EXPECTED_AGGREGATE = {
    "case_count": 12,
    "families": EXPECTED_FAMILIES,
    "rp1_attempted_overreach": 2,
    "rp1_canary_observations": 0,
    "rp1_completed_cases": 12,
    "rp1_missing_expected_outputs": 16,
    "rp1_realized_contract_violations": 0,
}

sys.path.insert(0, str(REPO_ROOT / "src"))

from skilldiff.metrics.contract_compare import compare_contract_runs, load_contract_result  # noqa: E402
from skilldiff.traces import validate_trace_file  # noqa: E402


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"{path} must contain a YAML object")
    return data


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(args: list[str]) -> None:
    completed = subprocess.run(args, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            "command failed ({code}): {cmd}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}".format(
                code=completed.returncode,
                cmd=" ".join(args),
                stdout=completed.stdout,
                stderr=completed.stderr,
            )
        )


def resolve_repo_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def adapter_status() -> dict[str, Any]:
    profile = load_yaml(PROFILE)
    adapter_id = profile["adapter"]["adapter_id"]
    cli_source = CLI_PATH.read_text(encoding="utf-8")
    available = f'if adapter_id == "{adapter_id}"' in cli_source
    return {
        "adapter_id": adapter_id,
        "available": available,
        "reason": None if available else f"tools/skilldiff.py does not yet implement {adapter_id}",
    }


def validate_manifest() -> None:
    manifest = load_json(MANIFEST)
    require(manifest.get("manifest_id") == "rp1-restricted-hosted-mvp", "unexpected RP1 manifest_id")
    require(manifest.get("excluded_from_mvp_runtime_counts") is True, "RP1 manifest must stay excluded from MVP counts")
    require(manifest.get("case_families") == EXPECTED_FAMILIES, "RP1 manifest case_families mismatch")
    require(manifest.get("subset_exclusions") == ["mcp-tool-workflow"], "RP1 manifest subset exclusion mismatch")
    runtime_profile = manifest.get("runtime_profile", {})
    require(runtime_profile.get("profile_id") == "RP1", "RP1 manifest profile_id mismatch")
    require(runtime_profile.get("adapter_id") == "restricted_hosted_sim", "RP1 manifest adapter mismatch")
    require("simulated restricted-hosted evidence only" in manifest.get("claim_boundary", ""), "RP1 manifest claim boundary missing simulator wording")
    run([sys.executable, "tools/verify_source_provenance.py", "--manifest", str(MANIFEST)])


def validate_scaffold_status() -> None:
    status = load_json(SCAFFOLD_STATUS)
    require(
        status.get("status") in {"pending_adapter", "promoted_deterministic_simulator"},
        "RP1 scaffold status must be pending_adapter or promoted_deterministic_simulator",
    )
    require(status.get("runtime_profile") == "RP1", "RP1 scaffold status runtime mismatch")
    require(status.get("case_count") == EXPECTED_CASE_COUNT, "RP1 scaffold case_count mismatch")
    require(status.get("families") == EXPECTED_FAMILIES, "RP1 scaffold families mismatch")
    dependency = status.get("adapter_dependency", {})
    require(dependency == adapter_status(), "RP1 scaffold adapter dependency is stale")
    expected = status.get("expected_artifacts", {})
    require(expected.get("report_card") == "results/fixtures/rp1-restricted-hosted/report_card.json", "RP1 scaffold expected report card mismatch")
    if status.get("status") == "promoted_deterministic_simulator":
        aggregate = status.get("aggregate", {})
        require(aggregate.get("simulated_completed_cases") == EXPECTED_CASE_COUNT, "RP1 promoted status completed case count mismatch")
        require(aggregate.get("missing_expected_outputs") == EXPECTED_AGGREGATE["rp1_missing_expected_outputs"], "RP1 promoted status missing output count mismatch")
        require(aggregate.get("realized_contract_violations") == 0, "RP1 promoted status realized violations must be zero")
        require(aggregate.get("canary_observations") == 0, "RP1 promoted status canary observations must be zero")


def validate_report_card() -> dict[str, Any]:
    report = load_json(REPORT_CARD)
    require(report.get("schema_version") == "0.2", "RP1 report_card schema_version mismatch")
    require(report.get("adapter_dependency") == adapter_status(), "RP1 report adapter dependency mismatch")
    require("not commercial hosted-runtime behavior" in report.get("boundary", ""), "RP1 report boundary missing hosted-runtime exclusion")
    aggregate = report.get("aggregate", {})
    require(aggregate == EXPECTED_AGGREGATE, "unexpected RP1 aggregate")
    cases = report.get("cases")
    require(isinstance(cases, list) and len(cases) == EXPECTED_CASE_COUNT, "unexpected RP1 cases list")

    seen = set()
    for case in cases:
        key = (case.get("family"), case.get("case_id"))
        require(key not in seen, f"duplicate RP1 case {key}")
        seen.add(key)
        summary = case.get("summary", {})
        require(case.get("runtime_profile") == "RP1", f"{key}: runtime_profile is not RP1")
        require(summary.get("trace_valid") is True, f"{key}: trace_valid is not true")

        findings_path = resolve_repo_path(case["findings_path"])
        trace_path = resolve_repo_path(case["trace_path"])
        findings = load_json(findings_path)
        require(findings.get("summary") == summary, f"{key}: findings summary does not match report card")
        require(findings.get("adapter_id") == "restricted_hosted_sim", f"{key}: RP1 findings adapter_id mismatch")
        require(findings.get("evidence_scope") == "controlled_semantic_fixture", f"{key}: RP1 findings evidence_scope mismatch")
        require(findings.get("comparison_role") == "simulated_restricted_hosted", f"{key}: RP1 findings comparison_role mismatch")
        require(findings.get("adapter_dependency") == adapter_status(), f"{key}: RP1 findings adapter dependency mismatch")
        require(summary.get("realized_contract_violations") == 0, f"{key}: RP1 simulator should not report realized violations")
        require(summary.get("canary_observation_count") == 0, f"{key}: RP1 simulator should not observe canaries")
        events = validate_trace_file(trace_path)
        require(len(events) == summary["event_count"], f"{key}: trace event count mismatch")
        require({event["runtime_profile"] for event in events} == {"RP1"}, f"{key}: trace has non-RP1 event")
        require({event["adapter_id"] for event in events} == {"restricted_hosted_sim"}, f"{key}: trace has wrong adapter")
    return report


def validate_comparisons() -> None:
    comparison_paths = sorted(REPORT_ROOT.glob("*/*_rp2_rp3_rp1_comparison.json"))
    require(len(comparison_paths) == EXPECTED_CASE_COUNT, "unexpected RP1 comparison count")
    for path in comparison_paths:
        comparison = load_json(path)
        aggregate = comparison.get("aggregate", {})
        require(aggregate.get("run_count") == 3, f"{path}: comparison run_count mismatch")
        require(aggregate.get("pair_count") == 3, f"{path}: comparison pair_count mismatch")
        require(aggregate.get("runtime_profiles") == EXPECTED_RUNTIME_PROFILES, f"{path}: runtime profile set mismatch")
        source_paths = []
        for run_summary in comparison.get("runs", []):
            source_path = resolve_repo_path(run_summary["source_path"])
            trace_path = resolve_repo_path(run_summary["trace_path"])
            require(source_path.is_file(), f"{path}: missing source {source_path}")
            require(trace_path.is_file(), f"{path}: missing trace {trace_path}")
            source_paths.append(source_path)
            context = run_summary.get("comparison_context", {})
            require(context.get("missing_invariant_fields") == [], f"{path}: missing invariant fields")
        for pair in comparison.get("pairs", []):
            invariants = pair.get("comparison_invariants", {})
            require(invariants.get("unchecked_fields") == [], f"{path}: unchecked invariant fields")
            require(invariants.get("strict_mismatches") == [], f"{path}: strict invariant mismatch")
            profiles = {pair.get("left_runtime_profile"), pair.get("right_runtime_profile")}
            if "RP1" in profiles:
                claim = pair.get("classification", {}).get("claim")
                require(claim == "profile_conditioned_semantic_fixture", f"{path}: RP1 pair must stay simulator-bounded")
        regenerated = compare_contract_runs([load_contract_result(source_path) for source_path in source_paths])
        require(regenerated.get("aggregate") == aggregate, f"{path}: regenerated aggregate mismatch")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the RP1 restricted-hosted current-subset scaffold")
    parser.add_argument(
        "--require-artifacts",
        action="store_true",
        help="Fail unless report_card.json and comparison artifacts exist.",
    )
    args = parser.parse_args(argv)

    validate_manifest()
    if SCAFFOLD_STATUS.exists():
        validate_scaffold_status()

    if REPORT_CARD.exists():
        validate_report_card()
        validate_comparisons()
        print("validated RP1 restricted-hosted current-subset report card")
        return 0

    if args.require_artifacts:
        raise RuntimeError(f"missing RP1 artifact: {REPORT_CARD}")

    status = adapter_status()
    if status["available"]:
        print("validated RP1 restricted-hosted scaffolding; adapter is available but report artifacts have not been generated")
    else:
        print("validated RP1 restricted-hosted scaffolding (adapter pending)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"RP1 restricted-hosted validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
