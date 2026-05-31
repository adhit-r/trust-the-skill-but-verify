#!/usr/bin/env python3
"""Run RP2/RP3 repeat-stability evidence for planned-inclusion fixtures.

This writes a separate strengthening artifact. It intentionally does not
modify `results/planned-inclusion/`, which remains the single-repeat Gate 3
denominator layer.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
MANIFEST_PATH = REPO_ROOT / "benchmark" / "manifests" / "benchmark-cases-current.json"
RESULTS_ROOT = REPO_ROOT / "results" / "fixtures" / "strengthening" / "rp2-rp3-repeat-stability"
RUN_ROOT = RESULTS_ROOT / "_runs"
EXECUTION_LEVEL = "controlled_single_repeat_fixture_rp2_rp3"
DEFAULT_REPEAT_IDS = (1, 2, 3)

EXPECTED_SUMMARY = {
    "realized_contract_violations": 0,
    "attempted_overreach": 0,
    "missing_expected_outputs": 0,
    "output_oracle_failures": 0,
    "canary_observation_count": 0,
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def repo_relative(path: str | Path) -> str:
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-")


def promoted_cases() -> list[dict[str, Any]]:
    manifest = load_json(MANIFEST_PATH)
    cases = [
        case
        for case in manifest.get("cases", [])
        if case.get("execution", {}).get("execution_level") == EXECUTION_LEVEL
        and "planned" in case.get("provenance", {}).get("source_manifest_ref", "")
    ]
    return sorted(cases, key=lambda case: (case["family_id"], case["provenance"]["task_id"]))


def profile_path(runtime: str) -> Path:
    filename = "RP2_local_coding_agent.yaml" if runtime == "rp2" else "RP3_docker_sandbox.yaml"
    return REPO_ROOT / "runtimes" / "profiles" / filename


def runtime_label(runtime: str) -> str:
    return runtime.upper()


def command_for(case: dict[str, Any], runtime: str) -> list[str]:
    task_id = case["provenance"]["task_id"]
    output = case["expected_output"]["primary_artifact"]
    if runtime == "rp3":
        return [
            "python3",
            "-B",
            "/workspace/repo/skill/planned_fixture_runner.py",
            "--task-id",
            task_id,
            "--output",
            output,
        ]
    return [
        "python3",
        "skill/planned_fixture_runner.py",
        "--task-id",
        task_id,
        "--output",
        output,
    ]


def case_out_dir(case: dict[str, Any]) -> Path:
    return RESULTS_ROOT / case["family_id"]


def result_stem(case: dict[str, Any], runtime: str, repeat_id: int) -> str:
    return f"{slug(case['provenance']['task_id'])}_repeat{repeat_id}_{runtime}"


def pair_stem(case: dict[str, Any], repeat_id: int) -> str:
    return f"{slug(case['provenance']['task_id'])}_repeat{repeat_id}_rp2_rp3_pair"


def findings_path(case: dict[str, Any], runtime: str, repeat_id: int) -> Path:
    return case_out_dir(case) / f"{result_stem(case, runtime, repeat_id)}_contract_findings.json"


def pair_path(case: dict[str, Any], repeat_id: int) -> Path:
    return case_out_dir(case) / f"{pair_stem(case, repeat_id)}.json"


def summary_without_event_count(summary: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in summary.items() if key != "event_count"}


def run_case(case: dict[str, Any], runtime: str, repeat_id: int) -> dict[str, Any]:
    contract = REPO_ROOT / case["contract"]["contract_ref"]
    workspace = REPO_ROOT / case["workspace"]["workspace_ref"]
    result = run_json(
        [
            PYTHON,
            "tools/skilldiff.py",
            "run",
            "--profile",
            str(profile_path(runtime)),
            "--contract",
            str(contract),
            "--workspace",
            str(workspace),
            "--workspace-seed-id",
            f"planned-inclusion-{case['family_id']}-{case['provenance']['task_id']}-{runtime}",
            "--variant-id",
            case["case_id"],
            "--output-root",
            str(RUN_ROOT),
            "--repeat-id",
            str(repeat_id),
            "--live",
            "--command",
            *command_for(case, runtime),
        ]
    )
    actual = (result.get("adapter_outcome"), result.get("exit_code"))
    if actual != ("completed", 0):
        raise RuntimeError(f"unexpected run outcome for {case['case_id']}/{runtime}/repeat{repeat_id}: {actual}")

    out_dir = case_out_dir(case)
    out_dir.mkdir(parents=True, exist_ok=True)
    trace_ref = repo_relative(result["trace_path"])
    stem = result_stem(case, runtime, repeat_id)
    run_text(
        [
            PYTHON,
            "tools/check_contract.py",
            "--contract",
            str(contract),
            "--trace",
            trace_ref,
            "--out-json",
            str(out_dir / f"{stem}_contract_findings.json"),
            "--out-md",
            str(out_dir / f"{stem}_contract_report.md"),
        ]
    )
    findings = load_json(findings_path(case, runtime, repeat_id))
    observed = {field: findings["summary"].get(field) for field in EXPECTED_SUMMARY}
    if observed != EXPECTED_SUMMARY:
        raise RuntimeError(f"{case['case_id']}/{runtime}/repeat{repeat_id}: unexpected summary {observed}")
    return {
        "findings_path": repo_relative(findings_path(case, runtime, repeat_id)),
        "repeat_id": repeat_id,
        "run_id": result["run_id"],
        "runtime_profile": runtime_label(runtime),
        "summary": findings["summary"],
        "summary_without_event_count": summary_without_event_count(findings["summary"]),
        "trace_path": trace_ref,
    }


def write_pair(case: dict[str, Any], repeat_id: int) -> dict[str, Any]:
    out_json = pair_path(case, repeat_id)
    out_md = out_json.with_suffix(".md")
    run_text(
        [
            PYTHON,
            "tools/compare_contract_runs.py",
            str(findings_path(case, "rp2", repeat_id)),
            str(findings_path(case, "rp3", repeat_id)),
            "--out-json",
            str(out_json),
            "--out-md",
            str(out_md),
        ]
    )
    pair = load_json(out_json)
    aggregate = pair["aggregate"]
    if aggregate["pairwise_disagreements"] != 0 or aggregate["runtime_drift_claims"] != 0:
        raise RuntimeError(f"{out_json}: repeat pair produced disagreement or drift claim")
    return {
        "pair_path": repo_relative(out_json),
        "pair_report_path": repo_relative(out_md),
        "repeat_id": repeat_id,
        "pairwise_disagreements": aggregate["pairwise_disagreements"],
        "runtime_drift_claims": aggregate["runtime_drift_claims"],
        "classification": pair["pairs"][0]["classification"]["claim"],
    }


def load_existing_observation(case: dict[str, Any], runtime: str, repeat_id: int) -> dict[str, Any]:
    path = findings_path(case, runtime, repeat_id)
    findings = load_json(path)
    return {
        "findings_path": repo_relative(path),
        "repeat_id": repeat_id,
        "run_id": findings["run_id"],
        "runtime_profile": findings["runtime_profile"],
        "summary": findings["summary"],
        "summary_without_event_count": summary_without_event_count(findings["summary"]),
        "trace_path": findings["trace_path"],
    }


def load_existing_pair(case: dict[str, Any], repeat_id: int) -> dict[str, Any]:
    out_json = pair_path(case, repeat_id)
    pair = load_json(out_json)
    aggregate = pair["aggregate"]
    return {
        "pair_path": repo_relative(out_json),
        "pair_report_path": repo_relative(out_json.with_suffix(".md")),
        "repeat_id": repeat_id,
        "pairwise_disagreements": aggregate["pairwise_disagreements"],
        "runtime_drift_claims": aggregate["runtime_drift_claims"],
        "classification": pair["pairs"][0]["classification"]["claim"],
    }


def runtime_stability(observations: list[dict[str, Any]]) -> dict[str, Any]:
    first = observations[0]["summary"]
    first_without_event_count = observations[0]["summary_without_event_count"]
    return {
        "event_counts": {str(row["repeat_id"]): row["summary"]["event_count"] for row in observations},
        "stable_summary_including_event_count": all(row["summary"] == first for row in observations),
        "stable_summary_excluding_event_count": all(
            row["summary_without_event_count"] == first_without_event_count for row in observations
        ),
        "max_realized_contract_violations": max(row["summary"]["realized_contract_violations"] for row in observations),
        "max_attempted_overreach": max(row["summary"]["attempted_overreach"] for row in observations),
        "max_missing_expected_outputs": max(row["summary"]["missing_expected_outputs"] for row in observations),
        "max_output_oracle_failures": max(row["summary"]["output_oracle_failures"] for row in observations),
        "max_canary_observation_count": max(row["summary"]["canary_observation_count"] for row in observations),
    }


def build_report(cases: list[dict[str, Any]], observations: dict[tuple[str, str], list[dict[str, Any]]], pairs: dict[str, list[dict[str, Any]]], repeat_ids: list[int]) -> dict[str, Any]:
    rows = []
    stable_excluding = 0
    stable_including = 0
    trace_paths: set[str] = set()
    finding_paths: set[str] = set()
    classification_counts: Counter[str] = Counter()

    for case in cases:
        runtime_summaries = {}
        for runtime in ("rp2", "rp3"):
            runtime_rows = observations[(case["case_id"], runtime)]
            for row in runtime_rows:
                trace_paths.add(row["trace_path"])
                finding_paths.add(row["findings_path"])
            stability = runtime_stability(runtime_rows)
            runtime_summaries[runtime_label(runtime)] = {
                "observations": runtime_rows,
                "stability": stability,
            }
            if stability["stable_summary_excluding_event_count"]:
                stable_excluding += 1
            if stability["stable_summary_including_event_count"]:
                stable_including += 1
        for pair in pairs[case["case_id"]]:
            classification_counts[pair["classification"]] += 1
        rows.append(
            {
                "case_id": case["case_id"],
                "family_id": case["family_id"],
                "skill_id": case["case_id"].split(".", 1)[0],
                "task_id": case["provenance"]["task_id"],
                "contract_id": case["contract"]["contract_id"],
                "repeat_ids": repeat_ids,
                "runtime_observation_count": 2 * len(repeat_ids),
                "pair_count": len(pairs[case["case_id"]]),
                "runtime_summaries": runtime_summaries,
                "same_repeat_pairs": pairs[case["case_id"]],
            }
        )

    pair_count = sum(len(value) for value in pairs.values())
    return {
        "schema_version": "0.1",
        "report_type": "planned_inclusion_rp2_rp3_repeat_stability",
        "boundary": (
            "Bounded deterministic repeat-stability evidence for controlled synthetic planned-inclusion fixtures. "
            "This is not completed statistics, reviewer agreement, prevalence evidence, live product behavior, "
            "public-network behavior, commercial-runtime behavior, or defense-success evidence."
        ),
        "claim_boundary": {
            "completed_statistics_claimed": False,
            "reviewer_adjudication_claimed": False,
            "prevalence_claim": False,
            "defense_success_claim": False,
            "live_product_claim": False,
            "commercial_runtime_claim": False,
            "public_network_claim": False,
        },
        "aggregate": {
            "case_count": len(cases),
            "repeat_ids": repeat_ids,
            "runtime_profiles": ["RP2", "RP3"],
            "runtime_observation_count": len(trace_paths),
            "trace_valid_count": len(trace_paths),
            "findings_file_count": len(finding_paths),
            "same_repeat_pair_count": pair_count,
            "classification_counts": dict(sorted(classification_counts.items())),
            "pairwise_disagreement_count": sum(pair["pairwise_disagreements"] for pair_list in pairs.values() for pair in pair_list),
            "runtime_drift_claim_count": sum(pair["runtime_drift_claims"] for pair_list in pairs.values() for pair in pair_list),
            "case_runtime_stability_units": len(cases) * 2,
            "summary_match_count_excluding_event_count": stable_excluding,
            "summary_match_count_including_event_count": stable_including,
            "minimum_repeats_for_deterministic_stability_claim": min(len(value) for value in observations.values()),
            "statistical_repeat_stability_claims_supported": 0,
        },
        "cases": rows,
    }


def write_markdown(report: dict[str, Any]) -> None:
    aggregate = report["aggregate"]
    lines = [
        "# Planned-Inclusion RP2/RP3 Repeat Stability",
        "",
        report["boundary"],
        "",
        "## Aggregate",
        "",
        "| Cases | Repeats | Runtime observations | Same-repeat pairs | Pairwise disagreements | Runtime-drift claims | Stable case-runtime units excluding event count |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: |",
        "| {cases} | `{repeats}` | {observations} | {pairs} | {disagreements} | {claims} | {stable} |".format(
            cases=aggregate["case_count"],
            repeats=", ".join(str(repeat_id) for repeat_id in aggregate["repeat_ids"]),
            observations=aggregate["runtime_observation_count"],
            pairs=aggregate["same_repeat_pair_count"],
            disagreements=aggregate["pairwise_disagreement_count"],
            claims=aggregate["runtime_drift_claim_count"],
            stable=aggregate["summary_match_count_excluding_event_count"],
        ),
        "",
        "## Boundary",
        "",
        "This artifact supports only bounded deterministic fixture stability. It does not support statistical, prevalence, reviewer-agreement, live-product, commercial-runtime, public-network, or defense-success claims.",
        "",
    ]
    (RESULTS_ROOT / "repeat_stability.md").write_text("\n".join(lines), encoding="utf-8")


def parse_repeat_ids(args: argparse.Namespace) -> list[int]:
    repeat_ids = args.repeat_id or list(DEFAULT_REPEAT_IDS)
    repeat_ids = sorted(set(repeat_ids))
    if any(repeat_id < 1 for repeat_id in repeat_ids):
        raise ValueError("repeat IDs must be positive integers")
    return repeat_ids


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeat-id", action="append", type=int, default=[], help="Repeat ID to run.")
    parser.add_argument("--family", action="append", default=[], help="Restrict to one or more family IDs.")
    parser.add_argument("--case-id", action="append", default=[], help="Restrict to one or more case IDs.")
    parser.add_argument("--keep-existing", action="store_true", help="Do not remove the repeat-stability output root before running.")
    parser.add_argument("--summarize-existing", action="store_true", help="Build repeat_stability.json/md from existing run outputs.")
    args = parser.parse_args(argv)
    repeat_ids = parse_repeat_ids(args)

    cases = promoted_cases()
    if args.family:
        families = set(args.family)
        cases = [case for case in cases if case["family_id"] in families]
    if args.case_id:
        case_ids = set(args.case_id)
        cases = [case for case in cases if case["case_id"] in case_ids]
    if not cases:
        raise RuntimeError("no planned-inclusion cases selected")

    if RESULTS_ROOT.exists() and not args.keep_existing and not args.summarize_existing:
        shutil.rmtree(RESULTS_ROOT)
    RESULTS_ROOT.mkdir(parents=True, exist_ok=True)

    observations: dict[tuple[str, str], list[dict[str, Any]]] = {}
    pairs: dict[str, list[dict[str, Any]]] = {}
    for case in cases:
        pairs[case["case_id"]] = []
        for repeat_id in repeat_ids:
            for runtime in ("rp2", "rp3"):
                if args.summarize_existing:
                    observations.setdefault((case["case_id"], runtime), []).append(
                        load_existing_observation(case, runtime, repeat_id)
                    )
                else:
                    print(f"repeat-stability {case['case_id']} repeat={repeat_id} {runtime.upper()}")
                    observations.setdefault((case["case_id"], runtime), []).append(run_case(case, runtime, repeat_id))
            if args.summarize_existing:
                pairs[case["case_id"]].append(load_existing_pair(case, repeat_id))
            else:
                pairs[case["case_id"]].append(write_pair(case, repeat_id))

    report = build_report(cases, observations, pairs, repeat_ids)
    write_json(RESULTS_ROOT / "repeat_stability.json", report)
    write_markdown(report)
    print(
        "planned-inclusion repeat stability complete: "
        f"{report['aggregate']['case_count']} cases, "
        f"{report['aggregate']['runtime_observation_count']} observations, "
        f"{report['aggregate']['same_repeat_pair_count']} same-repeat pairs"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
