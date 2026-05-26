#!/usr/bin/env python3
"""Build Gate 5 blank human-review export templates from the blinded bundle."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE = REPO_ROOT / "benchmark" / "review" / "gate5-blinded-packet-bundle.json"
DEFAULT_OUTPUT = REPO_ROOT / "benchmark" / "review" / "gate5-review-export-templates.json"
LOCKED_AT_UTC = "2026-05-26T00:00:00Z"

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


def blank_response() -> dict[str, Any]:
    return {
        "response_status": "not_started",
        "finding_kind": None,
        "drift_class": None,
        "severity": None,
        "task_success": None,
        "expected_output_status": None,
        "canary_status": None,
        "paper_claimable": None,
        "exclusion_reason": None,
        "evidence_summary": None,
        "uncertainty_or_notes": None,
    }


def build_review_item(packet: dict[str, Any], pair_unit: dict[str, Any]) -> dict[str, Any]:
    return {
        "review_item_id": f"{packet['review_item_id']}::{pair_unit['unit_id']}",
        "packet_id": packet["packet_id"],
        "case_id": packet["case_id"],
        "variant_id": packet["variant_id"],
        "category": packet["category"],
        "source_mix_label": packet["source_mix_label"],
        "evidence_stage": packet["evidence_stage"],
        "unit_id": pair_unit["unit_id"],
        "unit_type": pair_unit["unit_type"],
        "comparison_ref_id": pair_unit["comparison_ref_id"],
        "pair_pointer": pair_unit["pair_pointer"],
        "left_slot_id": pair_unit["left_slot_id"],
        "right_slot_id": pair_unit["right_slot_id"],
        "base_refs": packet["base_refs"],
        "blinding": {
            "runtime_labels_hidden": True,
            "source_run_ids_hidden": True,
            "machine_classification_hidden": True,
            "runtime_evidence_paths_hidden": True,
        },
        "response": blank_response(),
    }


def build_template(reviewer_slot: str, exported_packets: list[dict[str, Any]]) -> dict[str, Any]:
    review_items = [
        build_review_item(packet, pair_unit)
        for packet in exported_packets
        for pair_unit in packet["pair_review_units"]
    ]
    return {
        "export_id": f"gate5-{reviewer_slot}-first-pass-template",
        "export_kind": "human_review_template",
        "template_status": "not_started",
        "review_pass": "first_pass_blinded_pair_review",
        "assignment": {
            "reviewer_slot": reviewer_slot,
            "reviewer_kind": "unassigned_human",
            "human_identity_claimed": False,
            "codex_assisted": False,
            "counts_as_human_review": False,
        },
        "claim_boundary": {
            "template_only": True,
            "completed_review_claimed": False,
            "agreement_claimed": False,
            "adjudication_claimed": False,
        },
        "review_items": review_items,
    }


def build_templates(bundle_path: Path = DEFAULT_BUNDLE) -> dict[str, Any]:
    bundle = load_json(bundle_path)
    adjudication_form_path = repo_path(bundle["input_refs"]["adjudication_form_ref"])
    if adjudication_form_path is None:
        raise ValueError("blinded-bundle adjudication form ref must be repo-relative")

    exported_packets = [
        packet
        for packet in bundle.get("packets", [])
        if packet["bundle_status"] == "blinded_first_pass_ready"
    ]
    blocked_packets = [
        {
            "packet_id": packet["packet_id"],
            "review_item_id": packet["review_item_id"],
            "case_id": packet["case_id"],
            "blocked_reason": packet["blocked_reason"],
            "review_assignment_status": "not_assigned_metadata_only_unmapped",
        }
        for packet in bundle.get("packets", [])
        if packet["bundle_status"] == "blocked_metadata_only_unmapped"
    ]
    templates = [
        build_template("reviewer_a", exported_packets),
        build_template("reviewer_b", exported_packets),
    ]
    status_counts = Counter(template["template_status"] for template in templates)
    pair_count = bundle["aggregate"]["pair_review_unit_count"]
    aggregate = {
        "template_count": len(templates),
        "source_packet_count": bundle["aggregate"]["source_packet_count"],
        "assigned_packet_count_per_template": len(exported_packets),
        "blocked_packet_count": len(blocked_packets),
        "assigned_pair_review_unit_count_per_template": pair_count,
        "assigned_finding_review_unit_count_per_template": bundle["aggregate"]["finding_review_unit_count"],
        "completed_review_export_count": 0,
        "completed_pair_review_unit_count": 0,
        "human_reviewer_identity_count": 0,
        "agreement_metric_count": 0,
        "adjudication_record_count": 0,
        "template_status_counts": dict(sorted(status_counts.items())),
    }
    return {
        "schema_version": "0.1",
        "template_package_id": "gate5-review-export-templates",
        "status": "review_export_templates_ready_no_completed_reviews",
        "analysis_script": "tools/build_gate5_review_export_templates.py",
        "boundary": (
            "Gate 5 blank first-pass human-review export templates over the blinded packet bundle; "
            "these templates are not completed reviews and include no human reviewer identity, "
            "agreement metric, adjudication record, completed statistic, prevalence estimate, or paper-grade completion evidence."
        ),
        "input_refs": {
            "blinded_packet_bundle_ref": rel(bundle_path),
            "adjudication_form_ref": bundle["input_refs"]["adjudication_form_ref"],
        },
        "package_lock": {
            "lock_id": "gate5-review-export-templates-current-50x2-v1",
            "locked_at_utc": LOCKED_AT_UTC,
            "git_head": build_gate5_review_packet_index.git_rev_parse("HEAD"),
            "git_tree": build_gate5_review_packet_index.git_rev_parse("HEAD^{tree}"),
            "input_hashes": {
                "blinded_packet_bundle_sha256": build_gate5_review_packet_index.sha256_file(bundle_path),
                "adjudication_form_sha256": build_gate5_review_packet_index.sha256_file(adjudication_form_path),
            },
        },
        "claim_boundary": {
            "review_export_templates_only": True,
            "completed_human_reviews_claimed": False,
            "human_reviewer_identity_claimed": False,
            "reviewer_agreement_claimed": False,
            "adjudication_claimed": False,
            "completed_statistics_claimed": False,
            "prevalence_claim": False,
            "paper_grade_completion_claimed": False,
            "codex_assisted_review_counted_as_human": False,
        },
        "aggregate": aggregate,
        "templates": templates,
        "blocked_packets": blocked_packets,
        "next_dependencies": [
            "Copy one template per real independent human reviewer and fill every response before using it as completed review evidence.",
            "Do not count Codex-assisted or synthetic reviewer outputs as human review evidence.",
            "Run the completed-review validator before computing agreement or adjudication artifacts.",
            "Compute agreement and adjudication in separate artifacts after two completed human exports cover the same frozen item set.",
        ],
    }


def write_markdown(path: Path, package: dict[str, Any]) -> None:
    aggregate = package["aggregate"]
    lines = [
        "# Gate 5 Review Export Templates",
        "",
        package["boundary"],
        "",
        "## Aggregate",
        "",
        f"- Templates: `{aggregate['template_count']}`",
        f"- Assigned packets per template: `{aggregate['assigned_packet_count_per_template']}`",
        f"- Assigned pair-review units per template: `{aggregate['assigned_pair_review_unit_count_per_template']}`",
        f"- Blocked metadata-only packets: `{aggregate['blocked_packet_count']}`",
        f"- Completed review exports: `{aggregate['completed_review_export_count']}`",
        f"- Human reviewer identities claimed: `{aggregate['human_reviewer_identity_count']}`",
        f"- Agreement metrics: `{aggregate['agreement_metric_count']}`",
        f"- Adjudication records: `{aggregate['adjudication_record_count']}`",
        "",
        "This artifact is a review-template package only. It contains no completed human reviews, reviewer identities, reviewer agreement, adjudication records, statistics, prevalence estimates, or paper-grade completion claims.",
        "",
        "## Templates",
        "",
        "| Export | Reviewer slot | Status | Items | Counts as human review |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for template in package["templates"]:
        lines.append(
            "| `{export}` | `{slot}` | `{status}` | {items} | `{counts}` |".format(
                export=template["export_id"],
                slot=template["assignment"]["reviewer_slot"],
                status=template["template_status"],
                items=len(template["review_items"]),
                counts=template["assignment"]["counts_as_human_review"],
            )
        )
    lines.extend(["", "## Blocked Packets", ""])
    lines.append(f"`{aggregate['blocked_packet_count']}` packets remain metadata-only and are not assigned to the first-pass review templates.")
    lines.extend(["", "## Next Dependencies", ""])
    for dependency in package["next_dependencies"]:
        lines.append(f"- {dependency}")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    bundle_path = args.bundle if args.bundle.is_absolute() else REPO_ROOT / args.bundle
    output_path = args.output if args.output.is_absolute() else REPO_ROOT / args.output
    package = build_templates(bundle_path)
    write_json(output_path, package)
    write_markdown(output_path.with_suffix(".md"), package)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
