#!/usr/bin/env python3
"""Build the Gate 5 first-pass blinded review-packet bundle."""

from __future__ import annotations

import argparse
import json
import string
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = REPO_ROOT / "benchmark" / "review" / "gate5-review-packet-index.json"
DEFAULT_OUTPUT = REPO_ROOT / "benchmark" / "review" / "gate5-blinded-packet-bundle.json"
LOCKED_AT_UTC = "2026-05-26T00:00:00Z"

import sys

sys.path.insert(0, str(REPO_ROOT / "tools"))
import build_gate5_review_packet_index  # noqa: E402


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def repo_path(ref: str | None) -> Path | None:
    if not isinstance(ref, str) or not ref:
        return None
    return REPO_ROOT / ref.split("#", 1)[0]


def slot_label(index: int) -> str:
    letters = string.ascii_lowercase
    label = ""
    number = index
    while True:
        label = letters[number % len(letters)] + label
        number = number // len(letters) - 1
        if number < 0:
            return f"runtime_slot_{label}"


def packet_checks(exported: bool) -> dict[str, bool]:
    return {
        "raw_trace_content_included": False,
        "local_path_content_included": False,
        "source_paths_in_review_packet": False,
        "runtime_evidence_paths_in_review_packet": False,
        "runtime_profile_labels_included": False,
        "source_run_ids_included": False,
        "machine_classification_included": False,
        "completed_review_included": False,
        "reviewer_fields_included": False,
        "blinded_packet_exported": exported,
    }


def opaque_id(packet_id: str, kind: str, index: int) -> str:
    return f"{packet_id}.{kind}.{index}"


def build_blinded_packet(packet: dict[str, Any]) -> dict[str, Any]:
    exported = packet["packet_status"] == "indexed_pending_sanitized_packet_export"
    bundle_packet = {
        "packet_id": packet["packet_id"],
        "review_item_id": packet["review_item_id"],
        "source_queue_pointer": packet["source_queue_pointer"],
        "case_id": packet["case_id"],
        "variant_id": packet["variant_id"],
        "sample_batch_id": packet["sample_batch_id"],
        "category": packet["category"],
        "source_mix_label": packet["source_mix_label"],
        "evidence_stage": packet["evidence_stage"],
        "bundle_status": "blinded_first_pass_ready" if exported else "blocked_metadata_only_unmapped",
        "review_mode": "first_pass_blinded_pair_review" if exported else "metadata_only_unmapped_blocker",
        "blocked_reason": packet["blocked_reason"],
        "runtime_profile_blinding": packet["runtime_profile_blinding"],
        "agreement_scope": packet["agreement_scope"],
        "base_refs": packet["base_refs"],
        "blinded_evidence": {
            "source_packet_ref": "gate5-review-packet-index",
            "comparison_refs": [],
            "runtime_slots": [],
        },
        "pair_review_units": [],
        "finding_review_units": [],
        "packet_checks": packet_checks(exported),
    }
    if not exported:
        return bundle_packet

    comparison_ref_ids: dict[str, str] = {}
    for index, comparison_ref in enumerate(packet["comparison_refs"]):
        comparison_ref_id = opaque_id(packet["packet_id"], "comparison_ref", index)
        comparison_ref_ids[comparison_ref["comparison_ref"]] = comparison_ref_id
        bundle_packet["blinded_evidence"]["comparison_refs"].append(
            {
                "comparison_ref_id": comparison_ref_id,
                "source_ref_hidden": True,
                "comparison_sha256": comparison_ref["comparison_sha256"],
                "run_count": comparison_ref["run_count"],
                "pair_count": comparison_ref["pair_count"],
            }
        )

    slot_by_run_id: dict[str, str] = {}
    for index, run_ref in enumerate(packet["run_refs"]):
        label = slot_label(index)
        slot_id = opaque_id(packet["packet_id"], "runtime_slot", index)
        slot_by_run_id[run_ref["run_id"]] = slot_id
        bundle_packet["blinded_evidence"]["runtime_slots"].append(
            {
                "slot_id": slot_id,
                "slot_label": label,
                "run_pointer": run_ref["run_pointer"],
                "repeat_id": run_ref["repeat_id"],
                "source_run_id_hidden": True,
                "runtime_profile_hidden": True,
                "source_ref_hidden": True,
                "finding_artifact_ref_id": opaque_id(packet["packet_id"], "finding_artifact", index),
                "finding_sha256": run_ref["finding_sha256"],
                "trace_artifact_ref_id": opaque_id(packet["packet_id"], "trace_artifact", index),
                "trace_sha256": run_ref["trace_sha256"],
                "trace_valid": run_ref["trace_valid"],
                "trace_event_count": run_ref["trace_event_count"],
                "finding_count": run_ref["finding_count"],
            }
        )

    for index, pair_ref in enumerate(packet["pair_refs"]):
        bundle_packet["pair_review_units"].append(
            {
                "unit_id": opaque_id(packet["packet_id"], "pair_unit", index),
                "unit_type": "runtime_pair_comparison",
                "unit_status": "pending_manual_review",
                "claim_boundary": "not_human_reviewed",
                "comparison_ref_id": comparison_ref_ids[pair_ref["comparison_ref"]],
                "pair_pointer": pair_ref["pair_pointer"],
                "left_slot_id": slot_by_run_id[pair_ref["left_run_id"]],
                "right_slot_id": slot_by_run_id[pair_ref["right_run_id"]],
                "runtime_labels_hidden": True,
                "machine_classification_hidden": True,
                "source_ref_hidden": True,
                "completed_review_included": False,
            }
        )

    for index, _finding_ref in enumerate(packet["finding_refs"]):
        bundle_packet["finding_review_units"].append(
            {
                "unit_id": opaque_id(packet["packet_id"], "finding_unit", index),
                "unit_type": "contract_finding",
                "unit_status": "pending_manual_review",
                "claim_boundary": "not_human_reviewed",
                "runtime_labels_hidden": True,
                "source_ref_hidden": True,
                "completed_review_included": False,
            }
        )

    return bundle_packet


def build_bundle(index_path: Path = DEFAULT_INDEX) -> dict[str, Any]:
    packet_index = load_json(index_path)
    queue_path = repo_path(packet_index["input_refs"]["review_queue_ref"])
    adjudication_form_path = repo_path(packet_index["input_refs"]["adjudication_form_ref"])
    if queue_path is None or adjudication_form_path is None:
        raise ValueError("packet-index input refs must be repo-relative paths")

    packets = [build_blinded_packet(packet) for packet in packet_index.get("packets", [])]
    status_counts = Counter(packet["bundle_status"] for packet in packets)
    aggregate = {
        "source_packet_count": len(packet_index.get("packets", [])),
        "exported_packet_count": int(status_counts.get("blinded_first_pass_ready", 0)),
        "blocked_packet_count": int(status_counts.get("blocked_metadata_only_unmapped", 0)),
        "opaque_comparison_ref_count": sum(
            len(packet["blinded_evidence"]["comparison_refs"])
            for packet in packets
        ),
        "opaque_finding_artifact_ref_count": sum(
            len(packet["blinded_evidence"]["runtime_slots"])
            for packet in packets
        ),
        "opaque_trace_artifact_ref_count": sum(
            len(packet["blinded_evidence"]["runtime_slots"])
            for packet in packets
        ),
        "runtime_slot_count": sum(
            len(packet["blinded_evidence"]["runtime_slots"])
            for packet in packets
        ),
        "pair_review_unit_count": sum(len(packet["pair_review_units"]) for packet in packets),
        "finding_review_unit_count": sum(len(packet["finding_review_units"]) for packet in packets),
        "raw_trace_payload_count": 0,
        "completed_review_count": 0,
        "reviewer_identity_count": 0,
        "packet_status_counts": dict(sorted(status_counts.items())),
    }

    return {
        "schema_version": "0.1",
        "bundle_id": "gate5-blinded-packet-bundle",
        "status": "blinded_packet_bundle_ready_no_completed_reviews",
        "analysis_script": "tools/build_gate5_blinded_packet_bundle.py",
        "boundary": (
            "Gate 5 first-pass blinded packet bundle derived from the review-packet index; "
            "it exposes opaque evidence identifiers, hashes, JSON pointers, and runtime slot labels only, "
            "not runtime profile labels for exported first-pass pair packets, source run IDs, comparison paths, trace paths, finding paths, "
            "raw trace content, machine classification labels, completed human reviews, reviewer agreement, "
            "adjudication, completed statistics, prevalence, or paper-grade completion evidence."
        ),
        "input_refs": {
            "review_packet_index_ref": rel(index_path),
            "review_queue_ref": packet_index["input_refs"]["review_queue_ref"],
            "adjudication_form_ref": packet_index["input_refs"]["adjudication_form_ref"],
        },
        "bundle_lock": {
            "lock_id": "gate5-blinded-packet-bundle-current-60-v1",
            "locked_at_utc": LOCKED_AT_UTC,
            "git_head": build_gate5_review_packet_index.git_rev_parse("HEAD"),
            "git_tree": build_gate5_review_packet_index.git_rev_parse("HEAD^{tree}"),
            "input_hashes": {
                "review_packet_index_sha256": build_gate5_review_packet_index.sha256_file(index_path),
                "review_queue_sha256": build_gate5_review_packet_index.sha256_file(queue_path),
                "adjudication_form_sha256": build_gate5_review_packet_index.sha256_file(adjudication_form_path),
            },
        },
        "claim_boundary": {
            "blinded_packet_bundle_only": True,
            "first_pass_runtime_labels_blinded": True,
            "raw_trace_content_included": False,
            "runtime_evidence_paths_in_review_packets": False,
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
            "Use the blinded bundle for first-pass review only; keep the unblinded packet index as an audit source outside reviewer-facing packet content.",
            "Collect two independent real human review exports against this frozen bundle before agreement claims.",
            "Unblind runtime labels only after first-pass review records are locked.",
            "Validate adjudication and agreement artifacts separately before adding statistical or paper-grade claims.",
        ],
    }


def write_markdown(path: Path, bundle: dict[str, Any]) -> None:
    aggregate = bundle["aggregate"]
    lines = [
        "# Gate 5 Blinded Packet Bundle",
        "",
        bundle["boundary"],
        "",
        "## Aggregate",
        "",
        f"- Source packets: `{aggregate['source_packet_count']}`",
        f"- Exported blinded packets: `{aggregate['exported_packet_count']}`",
        f"- Blocked metadata-only packets: `{aggregate['blocked_packet_count']}`",
        f"- Opaque comparison refs: `{aggregate['opaque_comparison_ref_count']}`",
        f"- Opaque finding artifact refs: `{aggregate['opaque_finding_artifact_ref_count']}`",
        f"- Opaque trace artifact refs: `{aggregate['opaque_trace_artifact_ref_count']}`",
        f"- Runtime slots: `{aggregate['runtime_slot_count']}`",
        f"- Pair review units: `{aggregate['pair_review_unit_count']}`",
        f"- Finding review units: `{aggregate['finding_review_unit_count']}`",
        "",
        "This artifact is a blinded packet bundle only. Exported first-pass pair packets contain no runtime profile labels, source run IDs, comparison paths, trace paths, finding paths, raw trace content, reviewer IDs, completed review results, adjudication records, agreement metrics, confidence intervals, hypothesis tests, prevalence estimate, or paper-grade completion claim.",
        "",
        "## Packets",
        "",
        "| Packet | Status | Runtime slots | Pair units | Finding units |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for packet in bundle["packets"]:
        lines.append(
            "| `{packet}` | `{status}` | {slots} | {pairs} | {findings} |".format(
                packet=packet["packet_id"],
                status=packet["bundle_status"],
                slots=len(packet["blinded_evidence"]["runtime_slots"]),
                pairs=len(packet["pair_review_units"]),
                findings=len(packet["finding_review_units"]),
            )
        )
    lines.extend(["", "## Next Dependencies", ""])
    for dependency in bundle["next_dependencies"]:
        lines.append(f"- {dependency}")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    index_path = args.index if args.index.is_absolute() else REPO_ROOT / args.index
    output_path = args.output if args.output.is_absolute() else REPO_ROOT / args.output
    bundle = build_bundle(index_path)
    write_json(output_path, bundle)
    write_markdown(output_path.with_suffix(".md"), bundle)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
