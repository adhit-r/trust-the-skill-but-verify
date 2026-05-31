#!/usr/bin/env python3
"""Run first-party/public source-mix controlled fixtures through RP6.

This is broader profile-backed report-card evidence for already promoted
source-mix fixtures. It is not live product behavior, source-mix completion,
defense success, commercial-runtime behavior, public-network behavior,
prevalence evidence, or human adjudication evidence.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from repeat_hygiene import add_repeat_id_argument, repeat_seed, repeat_stem


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
MANIFEST_PATH = REPO_ROOT / "benchmark" / "manifests" / "benchmark-cases-current.json"
RP6_PROFILE = REPO_ROOT / "runtimes" / "profiles" / "RP6_policy_hardened.yaml"
RESULTS_ROOT = REPO_ROOT / "results" / "fixtures" / "strengthening" / "source-mix-rp6-report-card"
RUNS_ROOT = RESULTS_ROOT / "_runs"
EXECUTION_LEVEL = "controlled_single_repeat_fixture_rp2_rp3"
SOURCE_LABELS = {"first_party", "public"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def repo_relative(path: str | Path) -> str:
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-")


def run_json(args: list[str]) -> dict[str, Any]:
    completed = subprocess.run(args, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    if completed.returncode not in {0, 2}:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(args)}\n"
            f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"command produced no JSON output: {' '.join(args)}\nSTDERR:\n{completed.stderr}")
    return json.loads(lines[-1])


def run_text(args: list[str]) -> None:
    completed = subprocess.run(args, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(args)}\n"
            f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    print(completed.stdout, end="")


def source_mix_cases(manifest_path: Path = MANIFEST_PATH) -> list[dict[str, Any]]:
    manifest = load_json(manifest_path)
    cases = []
    for case in manifest.get("cases", []):
        execution = case.get("execution", {})
        provenance = case.get("provenance", {})
        source_mix = provenance.get("source_mix", {})
        if execution.get("execution_level") != EXECUTION_LEVEL:
            continue
        if source_mix.get("label") not in SOURCE_LABELS:
            continue
        cases.append(case)
    return sorted(cases, key=lambda case: (case["family_id"], case["provenance"]["task_id"]))


def command_for(case: dict[str, Any]) -> list[str]:
    return [
        "python3",
        "skill/planned_fixture_runner.py",
        "--task-id",
        case["provenance"]["task_id"],
        "--output",
        case["expected_output"]["primary_artifact"],
    ]


def case_out_dir(case: dict[str, Any]) -> Path:
    return RESULTS_ROOT / case["family_id"]


def result_stem(case: dict[str, Any]) -> str:
    return slug(case["provenance"]["task_id"])


def rp6_findings_path(case: dict[str, Any], repeat_id: int) -> Path:
    return case_out_dir(case) / f"{repeat_stem(result_stem(case) + '_rp6', repeat_id)}_contract_findings.json"


def rp2_findings_path(case: dict[str, Any]) -> Path:
    return REPO_ROOT / "results" / "planned-inclusion" / case["family_id"] / f"{result_stem(case)}_contract_findings.json"


def rp3_findings_path(case: dict[str, Any]) -> Path:
    return REPO_ROOT / "results" / "planned-inclusion" / case["family_id"] / f"{result_stem(case)}_rp3_contract_findings.json"


def run_case(case: dict[str, Any], repeat_id: int) -> dict[str, Any]:
    contract = REPO_ROOT / case["contract"]["contract_ref"]
    workspace = REPO_ROOT / case["workspace"]["workspace_ref"]
    result = run_json(
        [
            PYTHON,
            "tools/skilldiff.py",
            "run",
            "--profile",
            str(RP6_PROFILE),
            "--contract",
            str(contract),
            "--workspace",
            str(workspace),
            "--workspace-seed-id",
            repeat_seed(f"source-mix-rp6-{case['family_id']}-{case['provenance']['task_id']}", repeat_id),
            "--variant-id",
            case["case_id"],
            "--output-root",
            repo_relative(RUNS_ROOT),
            "--repeat-id",
            str(repeat_id),
            "--live",
            "--command",
            *command_for(case),
        ]
    )
    actual = (result.get("adapter_outcome"), result.get("exit_code"))
    if actual != ("completed", 0):
        raise RuntimeError(f"unexpected RP6 run outcome for {case['case_id']}: {actual} result={result}")

    out_dir = case_out_dir(case)
    out_dir.mkdir(parents=True, exist_ok=True)
    findings_path = rp6_findings_path(case, repeat_id)
    run_text(
        [
            PYTHON,
            "tools/check_contract.py",
            "--contract",
            str(contract),
            "--trace",
            result["trace_path"],
            "--out-json",
            str(findings_path),
            "--out-md",
            str(out_dir / f"{repeat_stem(result_stem(case) + '_rp6', repeat_id)}_contract_report.md"),
        ]
    )
    annotate_rp6_findings(findings_path)
    write_comparison(case, findings_path, repeat_id)
    findings = load_json(findings_path)
    return {
        "adapter_outcome": result["adapter_outcome"],
        "case_id": case["case_id"],
        "category": case["category"],
        "command": command_for(case),
        "contract": case["contract"]["contract_ref"],
        "exit_code": result["exit_code"],
        "family": case["family_id"],
        "findings_path": repo_relative(findings_path),
        "repeat_id": repeat_id,
        "runtime_profile": findings["runtime_profile"],
        "source_mix_label": case["provenance"]["source_mix"]["label"],
        "summary": findings["summary"],
        "task_id": case["provenance"]["task_id"],
        "trace_path": repo_relative(result["trace_path"]),
        "variant_id": case["case_id"],
    }


def annotate_rp6_findings(path: Path) -> None:
    findings = load_json(path)
    findings["adapter_id"] = "hardened_policy_adapter"
    findings["comparison_role"] = "mitigation_report_card"
    findings["evidence_scope"] = "source_mix_rp6_report_card_fixture"
    findings["comparison_boundary"] = (
        "Source-mix RP6 is broader profile-backed report-card evidence. "
        "RP6-vs-RP2/RP3 disagreements are mitigation/report-card contrasts, not runtime-drift claims."
    )
    path.write_text(json.dumps(findings, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_comparison(case: dict[str, Any], rp6_findings: Path, repeat_id: int) -> None:
    rp2 = rp2_findings_path(case)
    rp3 = rp3_findings_path(case)
    if not rp2.is_file() or not rp3.is_file():
        raise FileNotFoundError(f"{case['case_id']}: missing planned-inclusion RP2/RP3 findings")
    out_prefix = case_out_dir(case) / repeat_stem(f"{result_stem(case)}_rp2_rp3_rp6_comparison", repeat_id)
    run_text(
        [
            PYTHON,
            "tools/compare_contract_runs.py",
            str(rp2),
            str(rp3),
            str(rp6_findings),
            "--out-json",
            str(out_prefix.with_suffix(".json")),
            "--out-md",
            str(out_prefix.with_suffix(".md")),
        ]
    )


def write_reports(rows: list[dict[str, Any]], repeat_id: int) -> None:
    RESULTS_ROOT.mkdir(parents=True, exist_ok=True)
    source_counts = Counter(row["source_mix_label"] for row in rows)
    aggregate = {
        "case_count": len(rows),
        "categories": sorted({row["category"] for row in rows}),
        "families": sorted({row["family"] for row in rows}),
        "family_count": len({row["family"] for row in rows}),
        "repeat_id": repeat_id,
        "repeat_ids": [repeat_id],
        "repeat_observation_count": len(rows),
        "source_mix_counts": dict(sorted(source_counts.items())),
        "rp6_completed_cases": sum(1 for row in rows if row["adapter_outcome"] == "completed" and row["exit_code"] == 0),
        "rp6_realized_contract_violations": sum(row["summary"]["realized_contract_violations"] for row in rows),
        "rp6_attempted_overreach": sum(row["summary"]["attempted_overreach"] for row in rows),
        "rp6_missing_expected_outputs": sum(row["summary"]["missing_expected_outputs"] for row in rows),
        "rp6_output_oracle_failures": sum(row["summary"]["output_oracle_failures"] for row in rows),
        "rp6_canary_observations": sum(row["summary"]["canary_observation_count"] for row in rows),
    }
    report_card = {
        "schema_version": "0.1",
        "report_type": "source_mix_rp6_report_card",
        "boundary": (
            "Broader RP6 profile-backed report-card evidence for first-party/public controlled source-mix fixtures; "
            "not live product behavior, source-mix completion, defense success, commercial-runtime behavior, "
            "public-network behavior, prevalence evidence, or human adjudication evidence."
        ),
        "aggregate": aggregate,
        "cases": rows,
    }
    report_name = f"{repeat_stem('report_card', repeat_id)}.json"
    (RESULTS_ROOT / report_name).write_text(json.dumps(report_card, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown_report(rows, aggregate, repeat_id)
    write_family_reports(rows, repeat_id)


def write_markdown_report(rows: list[dict[str, Any]], aggregate: dict[str, Any], repeat_id: int) -> None:
    lines = [
        "# Source-Mix RP6 Report Card",
        "",
        "Broader RP6 profile-backed report-card evidence for first-party/public controlled source-mix fixtures.",
        "This is not live product behavior, source-mix completion, defense success, commercial-runtime behavior, public-network behavior, prevalence evidence, or human adjudication evidence.",
        "",
        "## Aggregate",
        "",
        f"- Cases: `{aggregate['case_count']}`",
        f"- Families: `{aggregate['family_count']}`",
        f"- Repeat ID: `{repeat_id}`",
        f"- Source mix: `{aggregate['source_mix_counts']}`",
        f"- RP6 completed cases: `{aggregate['rp6_completed_cases']}`",
        f"- RP6 realized contract violations: `{aggregate['rp6_realized_contract_violations']}`",
        f"- RP6 attempted overreach: `{aggregate['rp6_attempted_overreach']}`",
        f"- RP6 missing expected outputs: `{aggregate['rp6_missing_expected_outputs']}`",
        f"- RP6 canary observations: `{aggregate['rp6_canary_observations']}`",
        "",
        "| Family | Task | Source Mix | Category | Outcome | Realized | Attempted | Missing | Canary | Trace |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        summary = row["summary"]
        lines.append(
            "| {family} | `{task}` | {source_mix} | {category} | {outcome}/{exit_code} | {realized} | {attempted} | {missing} | {canary} | `{trace}` |".format(
                family=row["family"],
                task=row["task_id"],
                source_mix=row["source_mix_label"],
                category=row["category"],
                outcome=row["adapter_outcome"],
                exit_code=row["exit_code"],
                realized=summary["realized_contract_violations"],
                attempted=summary["attempted_overreach"],
                missing=summary["missing_expected_outputs"],
                canary=summary["canary_observation_count"],
                trace=row["trace_path"],
            )
        )
    (RESULTS_ROOT / f"{repeat_stem('report_card', repeat_id)}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_family_reports(rows: list[dict[str, Any]], repeat_id: int) -> None:
    by_family: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_family.setdefault(row["family"], []).append(row)
    for family, family_rows in sorted(by_family.items()):
        lines = [
            f"# {family} Source-Mix RP6 Report Card",
            "",
            "Bounded RP6 report-card evidence for the controlled source-mix fixture family.",
            "",
            "| Task | Source Mix | Outcome | Realized | Attempted | Missing | Canary | Trace |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
        ]
        for row in sorted(family_rows, key=lambda item: item["task_id"]):
            summary = row["summary"]
            lines.append(
                "| `{task}` | {source_mix} | {outcome}/{exit_code} | {realized} | {attempted} | {missing} | {canary} | `{trace}` |".format(
                    task=row["task_id"],
                    source_mix=row["source_mix_label"],
                    outcome=row["adapter_outcome"],
                    exit_code=row["exit_code"],
                    realized=summary["realized_contract_violations"],
                    attempted=summary["attempted_overreach"],
                    missing=summary["missing_expected_outputs"],
                    canary=summary["canary_observation_count"],
                    trace=row["trace_path"],
                )
            )
        (RESULTS_ROOT / family / f"{repeat_stem('rp6_report_card', repeat_id)}.md").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family", action="append", default=[], help="Restrict execution to one or more family IDs.")
    parser.add_argument("--case-id", action="append", default=[], help="Restrict execution to one or more case IDs.")
    add_repeat_id_argument(parser)
    args = parser.parse_args(argv)

    cases = source_mix_cases()
    if args.family:
        allowed_families = set(args.family)
        cases = [case for case in cases if case["family_id"] in allowed_families]
    if args.case_id:
        allowed_cases = set(args.case_id)
        cases = [case for case in cases if case["case_id"] in allowed_cases]
    if not cases:
        raise RuntimeError("no first-party/public source-mix cases selected")

    rows = []
    for case in cases:
        print(f"running {case['case_id']} RP6")
        rows.append(run_case(case, args.repeat_id))
    write_reports(rows, args.repeat_id)
    print(f"source-mix RP6 report-card run complete: {len(rows)} case(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
