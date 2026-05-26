#!/usr/bin/env python3
"""Build a bounded benchmark-scale gap report.

This report is an inclusion-planning artifact. It compares the current
machine-readable case inventory against the mid-scale and full-paper target
distributions without claiming that the current inventory already satisfies
either target.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "benchmark" / "manifests" / "benchmark-cases-current.json"
DEFAULT_OUTPUT = REPO_ROOT / "results" / "derived" / "benchmark-scale-gap.json"

CATEGORIES = [
    "document automation",
    "repository maintenance",
    "compliance/audit",
    "data extraction",
    "API workflow",
    "MCP/tool workflow",
    "local file operations",
]

SOURCE_MIX_LABELS = ["first_party", "public", "synthetic"]

TARGETS = {
    "mid_scale_20_60": {
        "target_skill_count": 20,
        "target_triple_count": 60,
        "triples_per_skill": 3,
        "category_distribution": {
            "document automation": 3,
            "repository maintenance": 4,
            "compliance/audit": 3,
            "data extraction": 3,
            "API workflow": 3,
            "MCP/tool workflow": 2,
            "local file operations": 2,
        },
        "source_mix_target": {
            "first_party": 5,
            "public": 8,
            "synthetic": 7,
        },
    },
    "full_paper_40_120": {
        "target_skill_count": 40,
        "target_triple_count": 120,
        "triples_per_skill": 3,
        "category_distribution": {
            "document automation": 6,
            "repository maintenance": 7,
            "compliance/audit": 5,
            "data extraction": 6,
            "API workflow": 6,
            "MCP/tool workflow": 5,
            "local file operations": 5,
        },
        "source_mix_target": {
            "first_party": 9,
            "public": 17,
            "synthetic": 14,
        },
    },
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def zero_filled_counts(counter: Counter[str]) -> dict[str, int]:
    return {category: int(counter.get(category, 0)) for category in CATEGORIES}


def target_gap(target_distribution: dict[str, int], current_counts: dict[str, int]) -> dict[str, int]:
    return {
        category: max(int(target_distribution[category]) - int(current_counts.get(category, 0)), 0)
        for category in CATEGORIES
    }


def source_mix_gap(target_distribution: dict[str, int], current_counts: dict[str, int]) -> dict[str, int]:
    return {
        label: max(int(target_distribution[label]) - int(current_counts.get(label, 0)), 0)
        for label in SOURCE_MIX_LABELS
    }


def sorted_deficits(gaps: dict[str, int]) -> list[dict[str, Any]]:
    return [
        {"category": category, "skill_gap": gap}
        for category, gap in sorted(gaps.items(), key=lambda item: (-item[1], item[0]))
        if gap > 0
    ]


def sorted_source_mix_deficits(gaps: dict[str, int]) -> list[dict[str, Any]]:
    return [
        {"source_mix": label, "skill_gap": gap}
        for label, gap in sorted(gaps.items(), key=lambda item: (-item[1], item[0]))
        if gap > 0
    ]


def build_report(manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    cases = manifest.get("cases", [])
    triple_category_counts = zero_filled_counts(Counter(case["category"] for case in cases))
    triple_keys = {
        (
            case["provenance"]["skill_id"],
            case["provenance"]["task_id"],
            case["provenance"]["contract_ref"],
        )
        for case in cases
    }
    skill_to_categories: dict[str, set[str]] = {}
    for case in cases:
        skill_to_categories.setdefault(case["provenance"]["skill_id"], set()).add(case["category"])
    skill_category_counts = zero_filled_counts(
        Counter(
            next(iter(categories))
            for categories in skill_to_categories.values()
            if len(categories) == 1
        )
    )
    multi_category_skills = sorted(
        skill for skill, categories in skill_to_categories.items() if len(categories) != 1
    )
    skill_to_source_mix: dict[str, set[str]] = {}
    for case in cases:
        skill_to_source_mix.setdefault(case["provenance"]["skill_id"], set()).add(
            case["provenance"]["source_mix"]["label"]
        )
    source_mix_skill_counts = {
        label: int(
            Counter(
                next(iter(labels))
                for labels in skill_to_source_mix.values()
                if len(labels) == 1
            ).get(label, 0)
        )
        for label in SOURCE_MIX_LABELS
    }
    multi_source_mix_skills = sorted(
        skill for skill, labels in skill_to_source_mix.items() if len(labels) != 1
    )
    status_counts = dict(sorted(Counter(case["case_status"] for case in cases).items()))
    evidence_stage_counts = dict(sorted(Counter(case["execution"]["evidence_stage"] for case in cases).items()))
    source_kind_counts = dict(sorted(Counter(case["provenance"]["source_kind"] for case in cases).items()))
    source_mix_case_counts = {
        label: int(Counter(case["provenance"]["source_mix"]["label"] for case in cases).get(label, 0))
        for label in SOURCE_MIX_LABELS
    }
    provenance_level_counts = dict(sorted(Counter(case["provenance"]["provenance_level"] for case in cases).items()))
    runtime_profile_counts = dict(
        sorted(
            Counter(
                profile
                for case in cases
                for profile in case["execution"]["runtime_profiles"]
            ).items()
        )
    )

    targets: dict[str, Any] = {}
    for target_id, target in TARGETS.items():
        gaps = target_gap(target["category_distribution"], skill_category_counts)
        mix_gaps = source_mix_gap(target["source_mix_target"], source_mix_skill_counts)
        target_skill_category_total = sum(target["category_distribution"].values())
        target_source_mix_total = sum(target["source_mix_target"].values())
        targets[target_id] = {
            **target,
            "target_skill_category_total": target_skill_category_total,
            "target_source_mix_total": target_source_mix_total,
            "skill_shortfall": max(target["target_skill_count"] - len(skill_to_categories), 0),
            "triple_shortfall": max(target["target_triple_count"] - len(triple_keys), 0),
            "skill_category_gaps": gaps,
            "skill_category_shortfall": sum(gaps.values()),
            "largest_category_deficits": sorted_deficits(gaps),
            "source_mix_skill_gaps": mix_gaps,
            "source_mix_skill_shortfall": sum(mix_gaps.values()),
            "largest_source_mix_deficits": sorted_source_mix_deficits(mix_gaps),
            "source_mix_gap_status": "computed_from_explicit_case_source_mix_labels_no_completion_claim",
        }

    planned_count = status_counts.get("planned_inclusion", 0)
    next_actions = [
        "Add public and additional first-party skills before claiming source-mix target completion.",
        "Keep every promoted entry tied to tracked prompt, prompt hash, workspace snapshot hash, contract, expected output, canary policy, publication boundary, and safety status.",
    ]
    if planned_count:
        next_actions.insert(
            0,
            "Promote planned inclusion entries into executable RP2/RP3 traces, contract reports, and pairwise comparisons before claiming executed mid-scale evidence.",
        )
    else:
        next_actions.insert(
            0,
            "Add repeat coverage, source-mix evidence depth, and adjudication evidence before claiming paper-grade mid-scale completion.",
        )

    return {
        "schema_version": "0.1",
        "report_type": "benchmark_scale_gap",
        "source_manifest": manifest_path.relative_to(REPO_ROOT).as_posix(),
        "boundary": (
            "Current-to-target benchmark scale gap report. Current inventory entries are not proof that the "
            "mid-scale 20/60 or full-paper 40/120 floors are complete as paper-grade evidence; execution "
            "evidence remains bounded by runtime profiles, repeat coverage, adjudication, and source-mix labels."
        ),
        "source_mix_label_scope": (
            "provenance.source_mix.label is a skill-origin/source-mix accounting label; "
            "provenance.source_kind and provenance_level remain case-level evidence labels."
        ),
        "claim_boundary": {
            "mid_scale_floor_claimed": False,
            "full_paper_floor_claimed": False,
            "prevalence_claim": False,
            "source_mix_gap_claimed": False,
            "source_mix_gap_computed": True,
            "source_mix_completion_claimed": False,
            "current_entries_are_skill_count_claim": False,
            "current_entries_are_triple_count_claim": False,
        },
        "current": {
            "declared_case_count": manifest["declared_case_count"],
            "case_entry_count": len(cases),
            "unique_skill_count": len(skill_to_categories),
            "unique_skill_task_contract_triple_count": len(triple_keys),
            "skill_category_counts": skill_category_counts,
            "triple_category_counts": triple_category_counts,
            "case_status_counts": status_counts,
            "evidence_stage_counts": evidence_stage_counts,
            "source_kind_counts": source_kind_counts,
            "source_mix_case_counts": source_mix_case_counts,
            "source_mix_skill_counts": source_mix_skill_counts,
            "provenance_level_counts": provenance_level_counts,
            "runtime_profile_counts": runtime_profile_counts,
            "multi_category_skills": multi_category_skills,
            "multi_source_mix_skills": multi_source_mix_skills,
            "missing_categories": [
                category for category, count in skill_category_counts.items() if count == 0
            ],
        },
        "targets": targets,
        "next_actions": next_actions,
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    current = report["current"]
    mid = report["targets"]["mid_scale_20_60"]
    full = report["targets"]["full_paper_40_120"]
    lines = [
        "# Benchmark Scale Gap",
        "",
        report["boundary"],
        "",
        report["source_mix_label_scope"],
        "",
        "## Current Inventory",
        "",
        f"- Case entries: `{current['case_entry_count']}`",
        f"- Unique skills: `{current['unique_skill_count']}`",
        f"- Unique skill-task-contract triples: `{current['unique_skill_task_contract_triple_count']}`",
        f"- Declared case count: `{current['declared_case_count']}`",
        f"- Missing categories: `{', '.join(current['missing_categories'])}`",
        "- Source-mix skill counts: `first_party={first_party}`, `public={public}`, `synthetic={synthetic}`".format(
            first_party=current["source_mix_skill_counts"]["first_party"],
            public=current["source_mix_skill_counts"]["public"],
            synthetic=current["source_mix_skill_counts"]["synthetic"],
        ),
        "",
        "| Category | Current Skills | Current Triples | Mid-Scale Skill Target | Mid-Scale Skill Gap | Full-Paper Skill Target | Full-Paper Skill Gap |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for category in CATEGORIES:
        lines.append(
            "| {category} | {current_skill_count} | {current_triple_count} | {mid_target} | {mid_gap} | {full_target} | {full_gap} |".format(
                category=category,
                current_skill_count=current["skill_category_counts"][category],
                current_triple_count=current["triple_category_counts"][category],
                mid_target=mid["category_distribution"][category],
                mid_gap=mid["skill_category_gaps"][category],
                full_target=full["category_distribution"][category],
                full_gap=full["skill_category_gaps"][category],
            )
        )
    lines.extend(
        [
            "",
            "## Source Mix",
            "",
            "| Source Mix | Current Skills | Current Cases | Mid-Scale Skill Target | Mid-Scale Skill Gap | Full-Paper Skill Target | Full-Paper Skill Gap |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for label in SOURCE_MIX_LABELS:
        lines.append(
            "| {label} | {current_skill_count} | {current_case_count} | {mid_target} | {mid_gap} | {full_target} | {full_gap} |".format(
                label=label,
                current_skill_count=current["source_mix_skill_counts"][label],
                current_case_count=current["source_mix_case_counts"][label],
                mid_target=mid["source_mix_target"][label],
                mid_gap=mid["source_mix_skill_gaps"][label],
                full_target=full["source_mix_target"][label],
                full_gap=full["source_mix_skill_gaps"][label],
            )
        )
    lines.extend(
        [
            "",
            "## Target Boundaries",
            "",
            f"- Mid-scale skill shortfall: `{mid['skill_shortfall']}`",
            f"- Mid-scale triple shortfall: `{mid['triple_shortfall']}`",
            f"- Full-paper skill shortfall: `{full['skill_shortfall']}`",
            f"- Full-paper triple shortfall: `{full['triple_shortfall']}`",
            f"- Mid-scale source-mix skill shortfall: `{mid['source_mix_skill_shortfall']}`",
            f"- Full-paper source-mix skill shortfall: `{full['source_mix_skill_shortfall']}`",
            "- Source-mix gaps are computed from explicit manifest labels, but source-mix completion is not claimed.",
            "- This artifact does not claim benchmark prevalence, source-mix completion, repeat/statistical readiness, or 40/120 completion.",
            "",
            "## Next Actions",
            "",
        ]
    )
    for action in report["next_actions"]:
        lines.append(f"- {action}")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    manifest_path = args.manifest if args.manifest.is_absolute() else REPO_ROOT / args.manifest
    output_path = args.output if args.output.is_absolute() else REPO_ROOT / args.output
    report = build_report(manifest_path)
    write_json(output_path, report)
    write_markdown(output_path.with_suffix(".md"), report)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
