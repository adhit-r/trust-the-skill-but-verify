#!/usr/bin/env python3
"""Validate the Gate 5 review-packet index."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = REPO_ROOT / "benchmark" / "review" / "gate5-review-packet-index.json"
SCHEMA_PATH = REPO_ROOT / "schemas" / "gate5_review_packet_index.schema.json"

sys.path.insert(0, str(REPO_ROOT / "tools"))
import build_gate5_review_packet_index  # noqa: E402
import validate_benchmark_cases  # noqa: E402
import validate_gate5_review_queue  # noqa: E402
import validate_paired_runtime_summary  # noqa: E402


PROHIBITED_RESULT_KEYS = {
    "reviewer_id",
    "reviewer_ids",
    "review_timestamp_utc",
    "reviewer_ids_compared",
    "adjudicator_id",
    "adjudication_timestamp_utc",
    "initial_agreement",
    "percent_agreement",
    "cohens_kappa",
    "kappa",
    "wilson_interval",
    "wilson_intervals",
    "bootstrap_interval",
    "bootstrap_intervals",
    "confidence_interval",
    "confidence_intervals",
    "mcnemar",
    "mcnemar_test",
    "hypothesis_test",
    "hypothesis_tests",
    "p_value",
    "p_values",
    "resolved_finding_kind",
    "resolved_drift_class",
    "resolved_severity",
    "resolved_paper_claimable",
}
PROHIBITED_PLACEHOLDERS = {"TBD", "TODO", "PLACEHOLDER"}
LOCAL_PATH_PATTERNS = [
    re.compile(pattern)
    for pattern in (
        "/" + r"Users/[^/\s\"']+",
        "/" + "private/" + r"var/folders/[^\s\"']+",
        "/" + "var/" + r"folders/[^\s\"']+",
    )
]
SECRET_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"(api[_-]?key|secret|token|cookie|authorization)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,}",
        r"bearer\s+[A-Za-z0-9_\-\.]{20,}",
    )
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def repo_path(ref: str | None) -> Path | None:
    if not isinstance(ref, str) or not ref:
        return None
    return REPO_ROOT / ref.split("#", 1)[0]


def git_rev_parse(rev: str) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", rev],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


def require_recorded_git_identity(lock: dict[str, Any]) -> None:
    for key in ("git_head", "git_tree"):
        value = lock.get(key)
        require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value), f"{key} must be a recorded git object id")


def normalize_git_identity(value: dict[str, Any], lock_key: str) -> dict[str, Any]:
    normalized = json.loads(json.dumps(value))
    lock = normalized.get(lock_key, {})
    lock["git_head"] = "<recorded-git-head>"
    lock["git_tree"] = "<recorded-git-tree>"
    return normalized


def line_count(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def trace_event_map(trace_path: Path) -> dict[str, dict[str, Any]]:
    events: dict[str, dict[str, Any]] = {}
    with trace_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            event = json.loads(line)
            event_id = event.get("event_id")
            if isinstance(event_id, str) and event_id:
                events[event_id] = {
                    "line_number": line_number,
                    "event_type": event.get("event_type") or "unknown",
                }
    return events


def validate_schema(index: dict[str, Any], path: Path) -> None:
    schema = load_json(SCHEMA_PATH)
    issues = validate_benchmark_cases._validate_node(index, schema, schema, "<root>")
    first_issue = issues[0] if issues else None
    require(not issues, f"{path}: schema violation: {first_issue}")


def find_prohibited_keys(value: Any, path: str = "<root>") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            normalized_key = key.lower().replace("-", "_")
            if normalized_key in PROHIBITED_RESULT_KEYS:
                hits.append(f"{path}.{key}")
            hits.extend(find_prohibited_keys(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            hits.extend(find_prohibited_keys(child, f"{path}[{index}]"))
    return hits


def find_placeholders(value: Any, path: str = "<root>") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            hits.extend(find_placeholders(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            hits.extend(find_placeholders(child, f"{path}[{index}]"))
    elif isinstance(value, str) and value.strip() in PROHIBITED_PLACEHOLDERS:
        hits.append(path)
    return hits


def scan_text_artifact(path: Path) -> list[str]:
    findings: list[str] = []
    text = path.read_text(encoding="utf-8")
    for line_no, line in enumerate(text.splitlines(), start=1):
        if any(pattern.search(line) for pattern in LOCAL_PATH_PATTERNS):
            findings.append(f"{path.relative_to(REPO_ROOT)}:{line_no}: local path")
        if any(pattern.search(line) for pattern in SECRET_PATTERNS):
            findings.append(f"{path.relative_to(REPO_ROOT)}:{line_no}: secret-like token")
    return findings


def source_comparisons_from_queue(queue: dict[str, Any]) -> set[str]:
    refs: set[str] = set()
    for item in queue.get("review_items", []):
        refs.update(item.get("paired_summary", {}).get("source_comparison_refs", []))
    return refs


def validate_index(path: Path) -> None:
    index = load_json(path)
    validate_schema(index, path)
    require(index.get("schema_version") == "0.1", "schema version mismatch")
    require(index.get("index_id") == "gate5-review-packet-index", "index id mismatch")
    require(
        index.get("status") == "packet_index_ready_no_completed_reviews",
        "status must remain no-completed-reviews",
    )
    require(
        index.get("analysis_script") == "tools/build_gate5_review_packet_index.py",
        "analysis script mismatch",
    )
    boundary = index.get("boundary", "")
    require("review-packet index" in boundary, "boundary must identify packet index")
    require("not raw trace content" in boundary, "boundary must exclude raw trace content")
    require("completed human reviews" in boundary, "boundary must exclude completed human reviews")
    require("reviewer agreement" in boundary, "boundary must exclude reviewer agreement")
    require("prevalence" in boundary, "boundary must exclude prevalence")

    prohibited = find_prohibited_keys(index)
    require(not prohibited, f"prohibited reviewer/statistical result fields present: {prohibited[:3]}")
    placeholders = find_placeholders(index)
    require(not placeholders, f"placeholder values present in packet index: {placeholders[:3]}")

    markdown_path = path.with_suffix(".md")
    require(markdown_path.is_file(), "missing packet-index Markdown")
    scan_findings = scan_text_artifact(path) + scan_text_artifact(markdown_path)
    require(not scan_findings, f"packet-index artifact hygiene failed: {scan_findings[:3]}")

    claim_boundary = index.get("claim_boundary", {})
    require(claim_boundary.get("packet_index_only") is True, "packet_index_only must be true")
    require(claim_boundary.get("raw_trace_content_included") is False, "raw trace content must not be included")
    for key in (
        "completed_reviews_claimed",
        "reviewer_agreement_claimed",
        "adjudication_claimed",
        "completed_statistics_claimed",
        "prevalence_claim",
        "paper_grade_completion_claimed",
    ):
        require(claim_boundary.get(key) is False, f"claim boundary {key} must be false")

    input_refs = index["input_refs"]
    queue_path = repo_path(input_refs["review_queue_ref"])
    paired_summary_path = repo_path(input_refs["paired_summary_ref"])
    adjudication_form_path = repo_path(input_refs["adjudication_form_ref"])
    require(queue_path is not None and queue_path.is_file(), "missing review queue")
    require(paired_summary_path is not None and paired_summary_path.is_file(), "missing paired summary")
    require(adjudication_form_path is not None and adjudication_form_path.is_file(), "missing adjudication form")
    validate_gate5_review_queue.validate_queue(queue_path)
    validate_paired_runtime_summary.validate_summary(paired_summary_path)

    queue = load_json(queue_path)
    inclusion_table_path = repo_path(queue["input_refs"]["frozen_inclusion_table_ref"])
    require(inclusion_table_path is not None and inclusion_table_path.is_file(), "missing inclusion table")
    inclusion_table = load_json(inclusion_table_path)
    source_manifest_path = repo_path(inclusion_table["source_manifest_ref"])
    require(source_manifest_path is not None and source_manifest_path.is_file(), "missing source manifest")

    index_lock = index["index_lock"]
    require_recorded_git_identity(index_lock)
    input_hashes = index_lock["input_hashes"]
    for key, artifact_path in (
        ("review_queue_sha256", queue_path),
        ("paired_summary_sha256", paired_summary_path),
        ("adjudication_form_sha256", adjudication_form_path),
        ("inclusion_table_sha256", inclusion_table_path),
        ("source_manifest_sha256", source_manifest_path),
    ):
        require(
            input_hashes[key] == build_gate5_review_packet_index.sha256_file(artifact_path),
            f"input hash mismatch for {key}",
        )

    recomputed = build_gate5_review_packet_index.build_index(queue_path)
    require(
        normalize_git_identity(index, "index_lock") == normalize_git_identity(recomputed, "index_lock"),
        "Gate 5 review-packet index is stale",
    )

    queue_items = queue.get("review_items", [])
    queue_by_item_id = {item["review_item_id"]: item for item in queue_items}
    aggregate = index["aggregate"]
    packets = index.get("packets", [])
    require(aggregate["queue_item_count"] == len(queue_items), "queue item count mismatch")
    require(aggregate["packet_count"] == len(packets), "packet count mismatch")
    require(len(packets) == len(queue_items), "packet index must contain one packet per queue item")

    packet_status_counts = Counter(packet["packet_status"] for packet in packets)
    require(aggregate["packet_status_counts"] == dict(sorted(packet_status_counts.items())), "status count mismatch")
    require(
        aggregate["packet_count"] == aggregate["indexed_packet_count"] + aggregate["blocked_packet_count"],
        "indexed/blocked packet count mismatch",
    )

    expected_comparisons = source_comparisons_from_queue(queue)
    observed_comparisons: set[str] = set()
    observed_trace_refs: set[str] = set()
    semantic_unit_count = 0
    pair_unit_count = 0
    finding_unit_count = 0
    comparison_ref_count = 0
    run_ref_count = 0
    pair_ref_count = 0
    finding_ref_count = 0
    trace_event_locator_count = 0
    seen_packet_ids: set[str] = set()
    seen_review_item_ids: set[str] = set()

    for index_number, packet in enumerate(packets):
        packet_id = packet["packet_id"]
        review_item_id = packet["review_item_id"]
        require(packet_id not in seen_packet_ids, f"duplicate packet id {packet_id}")
        require(review_item_id not in seen_review_item_ids, f"duplicate review item id {review_item_id}")
        seen_packet_ids.add(packet_id)
        seen_review_item_ids.add(review_item_id)
        require(packet_id.startswith(f"gate5-packet-{index_number + 1:03d}-"), f"{packet_id}: order mismatch")
        require(review_item_id in queue_by_item_id, f"{packet_id}: review item missing from queue")
        queue_item = queue_by_item_id[review_item_id]
        require(packet["source_queue_pointer"] == f"/review_items/{index_number}", f"{packet_id}: bad queue pointer")
        for key in (
            "case_id",
            "variant_id",
            "sample_batch_id",
            "category",
            "source_mix_label",
            "evidence_stage",
            "runtime_profile_blinding",
            "agreement_scope",
        ):
            require(packet[key] == queue_item[key], f"{packet_id}: {key} mismatch")

        for ref_key, must_be_file in (
            ("prompt_ref", True),
            ("contract_ref", True),
            ("workspace_ref", False),
            ("adjudication_form_ref", True),
        ):
            ref_path = repo_path(packet["base_refs"][ref_key])
            require(ref_path is not None, f"{packet_id}: missing {ref_key}")
            if must_be_file:
                require(ref_path.is_file(), f"{packet_id}: missing file {packet['base_refs'][ref_key]}")
            else:
                require(ref_path.is_dir(), f"{packet_id}: missing directory {packet['base_refs'][ref_key]}")
        expected_output_ref = packet["base_refs"]["expected_output_ref"]
        if expected_output_ref is not None:
            expected_path = repo_path(expected_output_ref)
            require(expected_path is not None and expected_path.is_file(), f"{packet_id}: missing expected output")

        checks = packet["packet_checks"]
        for key in (
            "raw_trace_content_included",
            "local_path_content_included",
            "completed_review_included",
            "reviewer_fields_included",
            "sanitized_packet_exported",
        ):
            require(checks[key] is False, f"{packet_id}: {key} must be false")

        source_refs = queue_item["paired_summary"]["source_comparison_refs"]
        if source_refs:
            require(
                packet["packet_status"] == "indexed_pending_sanitized_packet_export",
                f"{packet_id}: mapped packet has wrong status",
            )
            require(packet["blocked_reason"] is None, f"{packet_id}: mapped packet must not be blocked")
            require(packet["comparison_refs"], f"{packet_id}: mapped packet needs comparison refs")
            require(packet["run_refs"], f"{packet_id}: mapped packet needs run refs")
            require(packet["pair_refs"], f"{packet_id}: mapped packet needs pair refs")
            require(packet["semantic_review_units"], f"{packet_id}: mapped packet needs review units")
        else:
            require(
                packet["packet_status"] == "blocked_unmapped_paired_summary",
                f"{packet_id}: unmapped packet has wrong status",
            )
            require(isinstance(packet["blocked_reason"], str) and packet["blocked_reason"], f"{packet_id}: blocked reason missing")
            for field in (
                "comparison_refs",
                "run_refs",
                "pair_refs",
                "finding_refs",
                "trace_event_refs",
                "semantic_review_units",
            ):
                require(not packet[field], f"{packet_id}: unmapped packet must not include {field}")

        packet_comparison_by_ref = {record["comparison_ref"]: record for record in packet["comparison_refs"]}
        packet_run_refs = {(record["comparison_ref"], record["run_pointer"]): record for record in packet["run_refs"]}
        packet_pair_refs = {(record["comparison_ref"], record["pair_pointer"]): record for record in packet["pair_refs"]}
        packet_finding_refs = {
            (record["finding_ref"], record["finding_pointer"]): record
            for record in packet["finding_refs"]
        }

        for comparison_record in packet["comparison_refs"]:
            comparison_ref = comparison_record["comparison_ref"]
            observed_comparisons.add(comparison_ref)
            comparison_path = repo_path(comparison_ref)
            require(comparison_path is not None and comparison_path.is_file(), f"{packet_id}: missing comparison {comparison_ref}")
            require(
                comparison_record["comparison_sha256"] == build_gate5_review_packet_index.sha256_file(comparison_path),
                f"{packet_id}: comparison hash mismatch",
            )
            comparison = load_json(comparison_path)
            runs = comparison.get("runs", [])
            pairs = comparison.get("pairs", [])
            require(comparison_record["run_count"] == len(runs), f"{packet_id}: run count mismatch")
            require(comparison_record["pair_count"] == len(pairs), f"{packet_id}: pair count mismatch")

            for run_index, run in enumerate(runs):
                run_key = (comparison_ref, f"/runs/{run_index}")
                require(run_key in packet_run_refs, f"{packet_id}: missing run ref {run_key}")
                run_ref = packet_run_refs[run_key]
                finding_path = repo_path(run_ref["finding_ref"])
                trace_path = repo_path(run_ref["trace_ref"])
                require(finding_path is not None and finding_path.is_file(), f"{packet_id}: missing finding file")
                require(trace_path is not None and trace_path.is_file(), f"{packet_id}: missing trace file")
                observed_trace_refs.add(run_ref["trace_ref"])
                findings_doc = load_json(finding_path)
                require(run_ref["run_id"] == run["run_id"], f"{packet_id}: run id mismatch")
                require(run_ref["runtime_profile"] == run["runtime_profile"], f"{packet_id}: runtime profile mismatch")
                require(run_ref["finding_ref"] == run["source_path"], f"{packet_id}: finding ref mismatch")
                require(run_ref["trace_ref"] == run["trace_path"], f"{packet_id}: trace ref mismatch")
                require(
                    run_ref["finding_sha256"] == build_gate5_review_packet_index.sha256_file(finding_path),
                    f"{packet_id}: finding hash mismatch",
                )
                require(
                    run_ref["trace_sha256"] == build_gate5_review_packet_index.sha256_file(trace_path),
                    f"{packet_id}: trace hash mismatch",
                )
                require(run_ref["trace_event_count"] == line_count(trace_path), f"{packet_id}: trace count mismatch")
                require(run_ref["finding_count"] == len(findings_doc.get("findings", [])), f"{packet_id}: finding count mismatch")
                require(run_ref["trace_valid"] == bool(run.get("summary", {}).get("trace_valid")), f"{packet_id}: trace-valid mismatch")

                trace_events = trace_event_map(trace_path)
                for finding_index, finding in enumerate(findings_doc.get("findings", [])):
                    finding_key = (run_ref["finding_ref"], f"/findings/{finding_index}")
                    require(finding_key in packet_finding_refs, f"{packet_id}: missing finding ref {finding_key}")
                    finding_ref = packet_finding_refs[finding_key]
                    event_id = finding.get("event_id") or "unknown"
                    require(finding_ref["run_id"] == run_ref["run_id"], f"{packet_id}: finding run mismatch")
                    require(finding_ref["runtime_profile"] == run_ref["runtime_profile"], f"{packet_id}: finding runtime mismatch")
                    require(finding_ref["finding_id"] == (finding.get("finding_id") or f"{run_ref['run_id']}-finding-{finding_index}"), f"{packet_id}: finding id mismatch")
                    require(finding_ref["finding_type"] == (finding.get("finding_type") or "unknown"), f"{packet_id}: finding type mismatch")
                    require(finding_ref["severity"] == (finding.get("severity") or "unknown"), f"{packet_id}: severity mismatch")
                    require(finding_ref["drift_classes"] == list(finding.get("drift_classes", [])), f"{packet_id}: drift class mismatch")
                    require(finding_ref["event_id"] == event_id, f"{packet_id}: event id mismatch")
                    if event_id in trace_events:
                        require(finding_ref["trace_event_status"] == "event_id_found", f"{packet_id}: event should be found")
                        require(
                            finding_ref["trace_event_line"] == trace_events[event_id]["line_number"],
                            f"{packet_id}: trace event line mismatch",
                        )
                    else:
                        require(finding_ref["trace_event_status"] == "event_id_not_in_trace", f"{packet_id}: event should be absent")
                        require(finding_ref["trace_event_line"] is None, f"{packet_id}: absent event needs null line")

            for pair_index, pair in enumerate(pairs):
                pair_key = (comparison_ref, f"/pairs/{pair_index}")
                require(pair_key in packet_pair_refs, f"{packet_id}: missing pair ref {pair_key}")
                pair_ref = packet_pair_refs[pair_key]
                require(pair_ref["left_run_id"] == pair["left_run_id"], f"{packet_id}: left run mismatch")
                require(pair_ref["right_run_id"] == pair["right_run_id"], f"{packet_id}: right run mismatch")
                require(
                    pair_ref["classification_claim"] == pair.get("classification", {}).get("claim", "unknown"),
                    f"{packet_id}: classification mismatch",
                )
                require(pair_ref["disagreement_count"] == int(pair.get("disagreement_count", 0)), f"{packet_id}: disagreement mismatch")
                require(pair_ref["only_in_left_count"] == len(pair.get("only_in_left", [])), f"{packet_id}: left-only mismatch")
                require(pair_ref["only_in_right_count"] == len(pair.get("only_in_right", [])), f"{packet_id}: right-only mismatch")
                require(pair_ref["shared_finding_count"] == int(pair.get("shared_finding_count", 0)), f"{packet_id}: shared mismatch")

        for trace_event_ref in packet["trace_event_refs"]:
            trace_path = repo_path(trace_event_ref["trace_ref"])
            require(trace_path is not None and trace_path.is_file(), f"{packet_id}: missing trace event file")
            trace_events = trace_event_map(trace_path)
            event = trace_events.get(trace_event_ref["event_id"])
            require(event is not None, f"{packet_id}: trace event not found")
            require(trace_event_ref["line_number"] == event["line_number"], f"{packet_id}: trace locator line mismatch")
            require(trace_event_ref["event_type"] == event["event_type"], f"{packet_id}: trace locator type mismatch")

        for unit in packet["semantic_review_units"]:
            require(unit["unit_status"] == "pending_manual_review", f"{packet_id}: unit status mismatch")
            require(unit["claim_boundary"] == "not_human_reviewed", f"{packet_id}: unit boundary mismatch")
            if unit["unit_type"] == "runtime_pair_comparison":
                pair_unit_count += 1
                require(unit["comparison_ref"] in packet_comparison_by_ref, f"{packet_id}: unit comparison missing")
                require((unit["comparison_ref"], unit["pair_pointer"]) in packet_pair_refs, f"{packet_id}: unit pair missing")
                require(unit["finding_ref"] is None and unit["finding_pointer"] is None, f"{packet_id}: pair unit must not set finding")
            elif unit["unit_type"] == "contract_finding":
                finding_unit_count += 1
                require((unit["finding_ref"], unit["finding_pointer"]) in packet_finding_refs, f"{packet_id}: unit finding missing")
                require(unit["comparison_ref"] in packet_comparison_by_ref, f"{packet_id}: finding unit comparison missing")
                require(unit["pair_pointer"] is None, f"{packet_id}: finding unit must not set pair")
            semantic_unit_count += 1

        comparison_ref_count += len(packet["comparison_refs"])
        run_ref_count += len(packet["run_refs"])
        pair_ref_count += len(packet["pair_refs"])
        finding_ref_count += len(packet["finding_refs"])
        trace_event_locator_count += len(packet["trace_event_refs"])

    require(seen_review_item_ids == set(queue_by_item_id), "packets do not match review queue")
    require(observed_comparisons == expected_comparisons, "comparison refs do not match queue")
    require(aggregate["comparison_ref_count"] == comparison_ref_count, "comparison ref count mismatch")
    require(aggregate["run_ref_count"] == run_ref_count, "run ref count mismatch")
    require(aggregate["pair_ref_count"] == pair_ref_count, "pair ref count mismatch")
    require(aggregate["finding_ref_count"] == finding_ref_count, "finding ref count mismatch")
    require(aggregate["trace_ref_count"] == len(observed_trace_refs), "trace ref count mismatch")
    require(aggregate["trace_event_locator_count"] == trace_event_locator_count, "trace event locator count mismatch")
    require(aggregate["semantic_review_unit_count"] == semantic_unit_count, "semantic review unit count mismatch")
    require(aggregate["pair_review_unit_count"] == pair_unit_count, "pair review unit count mismatch")
    require(aggregate["finding_review_unit_count"] == finding_unit_count, "finding review unit count mismatch")

    require(boundary in markdown_path.read_text(encoding="utf-8"), "Markdown boundary is stale")
    markdown = markdown_path.read_text(encoding="utf-8")
    require(f"Packets: `{aggregate['packet_count']}`" in markdown, "Markdown packet count is stale")
    require("This artifact is an index only." in markdown, "Markdown index-only boundary missing")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    args = parser.parse_args(argv)
    index_path = args.index if args.index.is_absolute() else REPO_ROOT / args.index
    validate_index(index_path)
    print("validated Gate 5 review-packet index")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Gate 5 review-packet index validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
