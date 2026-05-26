#!/usr/bin/env python3
"""Build the Gate 5 review-packet index from the manual review queue."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUEUE = REPO_ROOT / "benchmark" / "review" / "gate5-review-queue.json"
DEFAULT_OUTPUT = REPO_ROOT / "benchmark" / "review" / "gate5-review-packet-index.json"
LOCKED_AT_UTC = "2026-05-26T00:00:00Z"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


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


def line_count(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def build_pair_ref(comparison_ref: str, pair_index: int, pair: dict[str, Any]) -> dict[str, Any]:
    return {
        "comparison_ref": comparison_ref,
        "pair_pointer": f"/pairs/{pair_index}",
        "left_run_id": pair["left_run_id"],
        "right_run_id": pair["right_run_id"],
        "classification_claim": pair.get("classification", {}).get("claim", "unknown"),
        "disagreement_count": int(pair.get("disagreement_count", 0)),
        "only_in_left_count": len(pair.get("only_in_left", [])),
        "only_in_right_count": len(pair.get("only_in_right", [])),
        "shared_finding_count": int(pair.get("shared_finding_count", 0)),
    }


def build_run_and_finding_refs(
    comparison_ref: str,
    run_index: int,
    run: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    finding_path = repo_path(run["source_path"])
    trace_path = repo_path(run["trace_path"])
    if finding_path is None or trace_path is None:
        raise ValueError(f"{comparison_ref}: run refs must be repo-relative paths")
    findings_doc = load_json(finding_path)
    trace_events = trace_event_map(trace_path)

    repeat_id = int(run.get("comparison_context", {}).get("repeat_id", findings_doc.get("repeat_id", 0)))
    run_ref = {
        "comparison_ref": comparison_ref,
        "run_pointer": f"/runs/{run_index}",
        "run_id": run["run_id"],
        "runtime_profile": run["runtime_profile"],
        "repeat_id": repeat_id,
        "finding_ref": run["source_path"],
        "finding_sha256": sha256_file(finding_path),
        "trace_ref": run["trace_path"],
        "trace_sha256": sha256_file(trace_path),
        "trace_valid": bool(run.get("summary", {}).get("trace_valid")),
        "trace_event_count": line_count(trace_path),
        "finding_count": len(findings_doc.get("findings", [])),
    }

    finding_refs: list[dict[str, Any]] = []
    trace_event_refs: list[dict[str, Any]] = []
    for finding_index, finding in enumerate(findings_doc.get("findings", [])):
        event_id = finding.get("event_id") or "unknown"
        trace_event = trace_events.get(event_id)
        if trace_event is None:
            trace_event_status = "event_id_not_in_trace"
            trace_event_line = None
        else:
            trace_event_status = "event_id_found"
            trace_event_line = trace_event["line_number"]
            trace_event_refs.append(
                {
                    "trace_ref": run["trace_path"],
                    "run_id": run["run_id"],
                    "event_id": event_id,
                    "line_number": trace_event["line_number"],
                    "event_type": trace_event["event_type"],
                }
            )
        finding_refs.append(
            {
                "finding_ref": run["source_path"],
                "finding_pointer": f"/findings/{finding_index}",
                "run_id": run["run_id"],
                "runtime_profile": run["runtime_profile"],
                "finding_id": finding.get("finding_id") or f"{run['run_id']}-finding-{finding_index}",
                "finding_type": finding.get("finding_type") or "unknown",
                "severity": finding.get("severity") or "unknown",
                "drift_classes": list(finding.get("drift_classes", [])),
                "event_id": event_id,
                "trace_ref": run["trace_path"],
                "trace_event_status": trace_event_status,
                "trace_event_line": trace_event_line,
            }
        )
    return run_ref, finding_refs, trace_event_refs


def packet_checks() -> dict[str, bool]:
    return {
        "raw_trace_content_included": False,
        "local_path_content_included": False,
        "completed_review_included": False,
        "reviewer_fields_included": False,
        "sanitized_packet_exported": False,
    }


def build_packet(index: int, item: dict[str, Any]) -> dict[str, Any]:
    source_comparisons = item["paired_summary"]["source_comparison_refs"]
    packet_status = (
        "indexed_pending_sanitized_packet_export"
        if source_comparisons
        else "blocked_unmapped_paired_summary"
    )
    blocked_reason = (
        None
        if source_comparisons
        else "No paired-summary source comparison is mapped for this queue item; keep metadata-only until trace/finding evidence is linked."
    )
    packet = {
        "packet_id": f"gate5-packet-{index + 1:03d}-{item['case_id']}",
        "review_item_id": item["review_item_id"],
        "source_queue_pointer": f"/review_items/{index}",
        "case_id": item["case_id"],
        "variant_id": item["variant_id"],
        "sample_batch_id": item["sample_batch_id"],
        "category": item["category"],
        "source_mix_label": item["source_mix_label"],
        "evidence_stage": item["evidence_stage"],
        "packet_status": packet_status,
        "blocked_reason": blocked_reason,
        "runtime_profile_blinding": item["runtime_profile_blinding"],
        "agreement_scope": item["agreement_scope"],
        "base_refs": {
            "manifest_ref": item["refs"]["manifest_ref"],
            "prompt_ref": item["refs"]["prompt_ref"],
            "contract_ref": item["refs"]["contract_ref"],
            "workspace_ref": item["refs"]["workspace_ref"],
            "expected_output_ref": item["refs"]["expected_output_ref"],
            "adjudication_form_ref": item["refs"]["adjudication_form_ref"],
        },
        "comparison_refs": [],
        "run_refs": [],
        "pair_refs": [],
        "finding_refs": [],
        "trace_event_refs": [],
        "semantic_review_units": [],
        "packet_checks": packet_checks(),
    }

    pair_unit_index = 0
    finding_unit_index = 0
    for comparison_ref in source_comparisons:
        comparison_path = repo_path(comparison_ref)
        if comparison_path is None:
            raise ValueError(f"{item['review_item_id']}: comparison ref must be repo-relative")
        comparison = load_json(comparison_path)
        packet["comparison_refs"].append(
            {
                "comparison_ref": comparison_ref,
                "comparison_sha256": sha256_file(comparison_path),
                "run_count": len(comparison.get("runs", [])),
                "pair_count": len(comparison.get("pairs", [])),
            }
        )
        for pair_index, pair in enumerate(comparison.get("pairs", [])):
            pair_ref = build_pair_ref(comparison_ref, pair_index, pair)
            packet["pair_refs"].append(pair_ref)
            packet["semantic_review_units"].append(
                {
                    "unit_id": f"{packet['packet_id']}.pair.{pair_unit_index}",
                    "unit_type": "runtime_pair_comparison",
                    "unit_status": "pending_manual_review",
                    "requires_blinded_runtime_labels": item["runtime_profile_blinding"] == "eligible_for_first_pass_blinding",
                    "claim_boundary": "not_human_reviewed",
                    "comparison_ref": comparison_ref,
                    "pair_pointer": pair_ref["pair_pointer"],
                    "finding_ref": None,
                    "finding_pointer": None,
                }
            )
            pair_unit_index += 1
        for run_index, run in enumerate(comparison.get("runs", [])):
            run_ref, finding_refs, trace_event_refs = build_run_and_finding_refs(
                comparison_ref,
                run_index,
                run,
            )
            packet["run_refs"].append(run_ref)
            packet["trace_event_refs"].extend(trace_event_refs)
            for finding_ref in finding_refs:
                packet["finding_refs"].append(finding_ref)
                packet["semantic_review_units"].append(
                    {
                        "unit_id": f"{packet['packet_id']}.finding.{finding_unit_index}",
                        "unit_type": "contract_finding",
                        "unit_status": "pending_manual_review",
                        "requires_blinded_runtime_labels": item["runtime_profile_blinding"] == "eligible_for_first_pass_blinding",
                        "claim_boundary": "not_human_reviewed",
                        "comparison_ref": comparison_ref,
                        "pair_pointer": None,
                        "finding_ref": finding_ref["finding_ref"],
                        "finding_pointer": finding_ref["finding_pointer"],
                    }
                )
                finding_unit_index += 1
    return packet


def build_index(queue_path: Path = DEFAULT_QUEUE) -> dict[str, Any]:
    queue = load_json(queue_path)
    paired_summary_path = repo_path(queue["input_refs"]["paired_summary_ref"])
    adjudication_form_path = repo_path(queue["input_refs"]["adjudication_form_ref"])
    inclusion_table_path = repo_path(queue["input_refs"]["frozen_inclusion_table_ref"])
    if paired_summary_path is None or adjudication_form_path is None or inclusion_table_path is None:
        raise ValueError("queue input refs must be repo-relative paths")
    inclusion_table = load_json(inclusion_table_path)
    source_manifest_path = repo_path(inclusion_table["source_manifest_ref"])
    if source_manifest_path is None:
        raise ValueError("inclusion-table source manifest ref must be repo-relative")
    packets = [
        build_packet(index, item)
        for index, item in enumerate(queue.get("review_items", []))
    ]
    packet_status_counts = Counter(packet["packet_status"] for packet in packets)
    aggregate = {
        "queue_item_count": len(queue.get("review_items", [])),
        "packet_count": len(packets),
        "indexed_packet_count": int(packet_status_counts.get("indexed_pending_sanitized_packet_export", 0)),
        "blocked_packet_count": int(packet_status_counts.get("blocked_unmapped_paired_summary", 0)),
        "comparison_ref_count": sum(len(packet["comparison_refs"]) for packet in packets),
        "run_ref_count": sum(len(packet["run_refs"]) for packet in packets),
        "pair_ref_count": sum(len(packet["pair_refs"]) for packet in packets),
        "finding_ref_count": sum(len(packet["finding_refs"]) for packet in packets),
        "trace_ref_count": len({run["trace_ref"] for packet in packets for run in packet["run_refs"]}),
        "trace_event_locator_count": sum(len(packet["trace_event_refs"]) for packet in packets),
        "semantic_review_unit_count": sum(len(packet["semantic_review_units"]) for packet in packets),
        "pair_review_unit_count": sum(
            1
            for packet in packets
            for unit in packet["semantic_review_units"]
            if unit["unit_type"] == "runtime_pair_comparison"
        ),
        "finding_review_unit_count": sum(
            1
            for packet in packets
            for unit in packet["semantic_review_units"]
            if unit["unit_type"] == "contract_finding"
        ),
        "packet_status_counts": dict(sorted(packet_status_counts.items())),
    }
    return {
        "schema_version": "0.1",
        "index_id": "gate5-review-packet-index",
        "status": "packet_index_ready_no_completed_reviews",
        "analysis_script": "tools/build_gate5_review_packet_index.py",
        "boundary": (
            "Gate 5 review-packet index over the manual review queue; includes only sanitized refs, "
            "hashes, JSON pointers, and trace event locators, not raw trace content, completed human "
            "reviews, reviewer agreement, adjudication, completed statistics, prevalence, or paper-grade "
            "completion evidence."
        ),
        "input_refs": {
            "review_queue_ref": rel(queue_path),
            "paired_summary_ref": queue["input_refs"]["paired_summary_ref"],
            "adjudication_form_ref": queue["input_refs"]["adjudication_form_ref"],
        },
        "index_lock": {
            "lock_id": "gate5-review-packet-index-current-60-v1",
            "locked_at_utc": LOCKED_AT_UTC,
            "git_head": git_rev_parse("HEAD"),
            "git_tree": git_rev_parse("HEAD^{tree}"),
            "input_hashes": {
                "review_queue_sha256": sha256_file(queue_path),
                "paired_summary_sha256": sha256_file(paired_summary_path),
                "adjudication_form_sha256": sha256_file(adjudication_form_path),
                "inclusion_table_sha256": sha256_file(inclusion_table_path),
                "source_manifest_sha256": sha256_file(source_manifest_path),
            },
        },
        "claim_boundary": {
            "packet_index_only": True,
            "raw_trace_content_included": False,
            "completed_reviews_claimed": False,
            "reviewer_agreement_claimed": False,
            "adjudication_claimed": False,
            "completed_statistics_claimed": False,
            "prevalence_claim": False,
            "paper_grade_completion_claimed": False,
        },
        "aggregate": aggregate,
        "packets": packets,
        "next_dependencies": [
            "Export sanitized blinded packet bundles from this index without raw local-path-bearing trace content.",
            "Collect two independent real human review exports for the same frozen packet set before agreement claims.",
            "Validate completed review exports for distinct human reviewers, no placeholders, and adjudicated disagreements.",
            "Keep agent-assisted triage separate from human agreement evidence.",
        ],
    }


def write_markdown(path: Path, index: dict[str, Any]) -> None:
    aggregate = index["aggregate"]
    lines = [
        "# Gate 5 Review Packet Index",
        "",
        index["boundary"],
        "",
        "## Aggregate",
        "",
        f"- Packets: `{aggregate['packet_count']}`",
        f"- Indexed packets: `{aggregate['indexed_packet_count']}`",
        f"- Blocked packets: `{aggregate['blocked_packet_count']}`",
        f"- Comparison refs: `{aggregate['comparison_ref_count']}`",
        f"- Run refs: `{aggregate['run_ref_count']}`",
        f"- Pair refs: `{aggregate['pair_ref_count']}`",
        f"- Finding refs: `{aggregate['finding_ref_count']}`",
        f"- Trace refs: `{aggregate['trace_ref_count']}`",
        f"- Trace event locators: `{aggregate['trace_event_locator_count']}`",
        f"- Semantic review units: `{aggregate['semantic_review_unit_count']}`",
        "",
        "This artifact is an index only. It contains no raw trace content, reviewer IDs, completed review results, adjudication records, percent agreement, Cohen's kappa, confidence intervals, hypothesis tests, prevalence estimate, or paper-grade completion claim.",
        "",
        "## Packets",
        "",
        "| Packet | Status | Comparisons | Runs | Pairs | Findings | Units |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for packet in index["packets"]:
        lines.append(
            "| `{packet}` | `{status}` | {comparisons} | {runs} | {pairs} | {findings} | {units} |".format(
                packet=packet["packet_id"],
                status=packet["packet_status"],
                comparisons=len(packet["comparison_refs"]),
                runs=len(packet["run_refs"]),
                pairs=len(packet["pair_refs"]),
                findings=len(packet["finding_refs"]),
                units=len(packet["semantic_review_units"]),
            )
        )
    lines.extend(["", "## Next Dependencies", ""])
    for dependency in index["next_dependencies"]:
        lines.append(f"- {dependency}")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    queue_path = args.queue if args.queue.is_absolute() else REPO_ROOT / args.queue
    output_path = args.output if args.output.is_absolute() else REPO_ROOT / args.output
    index = build_index(queue_path)
    write_json(output_path, index)
    write_markdown(output_path.with_suffix(".md"), index)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
