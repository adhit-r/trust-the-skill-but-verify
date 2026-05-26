#!/usr/bin/env python3
"""Run formerly planned inclusion fixtures through RP2/RP3.

This is controlled single-repeat fixture evidence. It materializes already
approved synthetic inputs into the declared expected output file; it is not
evidence of live product behavior, public-network behavior, prevalence, or
commercial runtime behavior.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
MANIFEST_PATH = REPO_ROOT / "benchmark" / "manifests" / "benchmark-cases-current.json"
RESULTS_ROOT = REPO_ROOT / "results" / "planned-inclusion"
RAW_ROOT = REPO_ROOT / "results" / "raw"
EXECUTION_LEVEL = "controlled_single_repeat_fixture_rp2_rp3"

EXPECTED_SUMMARY = {
    "realized_contract_violations": 0,
    "attempted_overreach": 0,
    "missing_expected_outputs": 0,
    "output_oracle_failures": 0,
    "canary_observation_count": 0,
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def promoted_cases(manifest_path: Path = MANIFEST_PATH) -> list[dict[str, Any]]:
    manifest = load_json(manifest_path)
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


def repo_relative(path: str | Path) -> str:
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-")


def result_stem(case: dict[str, Any], runtime: str) -> str:
    base = slug(case["provenance"]["task_id"])
    return base if runtime == "rp2" else f"{base}_{runtime}"


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


def run_case(case: dict[str, Any], runtime: str) -> dict[str, Any]:
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
            str(RAW_ROOT),
            "--repeat-id",
            "1",
            "--live",
            "--command",
            *command_for(case, runtime),
        ]
    )
    actual = (result.get("adapter_outcome"), result.get("exit_code"))
    if actual != ("completed", 0):
        raise RuntimeError(f"unexpected run outcome for {case['case_id']}/{runtime}: {actual} result={result}")

    out_dir = case_out_dir(case)
    stem = result_stem(case, runtime)
    trace_path = Path(result["trace_path"])
    trace_ref = repo_relative(trace_path)
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
    assert_summary(case, runtime)
    assert_activation(trace_path)
    result["trace_path"] = trace_ref
    return result


def findings_path(case: dict[str, Any], runtime: str) -> Path:
    return case_out_dir(case) / f"{result_stem(case, runtime)}_contract_findings.json"


def load_findings(case: dict[str, Any], runtime: str) -> dict[str, Any]:
    return load_json(findings_path(case, runtime))


def assert_summary(case: dict[str, Any], runtime: str) -> None:
    summary = load_findings(case, runtime)["summary"]
    observed = {field: summary.get(field) for field in EXPECTED_SUMMARY}
    if observed != EXPECTED_SUMMARY:
        raise RuntimeError(f"{case['case_id']}/{runtime} unexpected summary: expected={EXPECTED_SUMMARY} observed={observed}")


def assert_activation(trace_path: Path) -> None:
    if not any(
        json.loads(line).get("event_type") == "activation.select"
        for line in trace_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ):
        raise RuntimeError(f"{trace_path} missing activation.select")


def write_comparison(case: dict[str, Any]) -> None:
    out_dir = case_out_dir(case)
    stem = slug(case["provenance"]["task_id"])
    run_text(
        [
            PYTHON,
            "tools/compare_contract_runs.py",
            str(findings_path(case, "rp2")),
            str(findings_path(case, "rp3")),
            "--out-json",
            str(out_dir / f"{stem}_rp2_rp3_comparison.json"),
            "--out-md",
            str(out_dir / f"{stem}_rp2_rp3_comparison.md"),
        ]
    )


def write_family_summaries(cases: list[dict[str, Any]], results: dict[tuple[str, str], dict[str, Any]]) -> None:
    by_family: dict[str, list[dict[str, Any]]] = {}
    for case in cases:
        by_family.setdefault(case["family_id"], []).append(case)
    for family_id, family_cases in sorted(by_family.items()):
        lines = [
            f"# {family_id} Controlled Fixture Result",
            "",
            "Controlled single-repeat RP2/RP3 synthetic fixture evidence for formerly planned inclusion records.",
            "",
            "| Case | Runtime | Trace | Realized Violations | Attempted Overreach | Missing Outputs | Canary Events |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: |",
        ]
        for case in sorted(family_cases, key=lambda item: item["provenance"]["task_id"]):
            for runtime in ("rp2", "rp3"):
                findings = load_findings(case, runtime)
                summary = findings["summary"]
                lines.append(
                    "| `{case}` | {runtime} | `{trace}` | {violations} | {attempted} | {missing} | {canaries} |".format(
                        case=case["case_id"],
                        runtime=runtime.upper(),
                        trace=results[(case["case_id"], runtime)]["trace_path"],
                        violations=summary["realized_contract_violations"],
                        attempted=summary["attempted_overreach"],
                        missing=summary["missing_expected_outputs"],
                        canaries=summary["canary_observation_count"],
                    )
                )
        lines.extend(
            [
                "",
                "## Boundary",
                "",
                "This is controlled synthetic fixture materialization evidence. It does not claim live product execution, ecosystem prevalence, commercial runtime behavior, public-network behavior, defense success, or repeat stability.",
                "",
            ]
        )
        (RESULTS_ROOT / family_id / "drift_report.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family", action="append", default=[], help="Restrict execution to one or more family IDs.")
    parser.add_argument("--case-id", action="append", default=[], help="Restrict execution to one or more case IDs.")
    args = parser.parse_args(argv)

    cases = promoted_cases()
    if args.family:
        allowed = set(args.family)
        cases = [case for case in cases if case["family_id"] in allowed]
    if args.case_id:
        allowed_cases = set(args.case_id)
        cases = [case for case in cases if case["case_id"] in allowed_cases]
    if not cases:
        raise RuntimeError("no promoted planned-inclusion cases selected")

    results: dict[tuple[str, str], dict[str, Any]] = {}
    for case in cases:
        for runtime in ("rp2", "rp3"):
            print(f"running {case['case_id']} {runtime.upper()}")
            results[(case["case_id"], runtime)] = run_case(case, runtime)
        write_comparison(case)
    write_family_summaries(cases, results)
    print(f"planned inclusion controlled fixture run complete: {len(cases)} case(s), {len(cases) * 2} trace(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
