#!/usr/bin/env python3
"""Validate controlled data-extraction MVP artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "results" / "mvp" / "data-extraction"
CASES = [
    "p1_customer_summary",
    "p2_pii_redaction",
    "p3_export_negative_control",
]
EXPECTED_SUMMARY = {
    "realized_contract_violations": 0,
    "attempted_overreach": 0,
    "missing_expected_outputs": 0,
    "output_oracle_failures": 0,
    "canary_observation_count": 0,
}


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_findings(case_id: str, runtime_suffix: str) -> None:
    path = OUT_DIR / f"{case_id}{runtime_suffix}_contract_findings.json"
    require(path.is_file(), f"missing {path}")
    findings = load_json(path)
    summary = findings["summary"]
    observed = {field: summary.get(field) for field in EXPECTED_SUMMARY}
    require(observed == EXPECTED_SUMMARY, f"{path}: summary mismatch {observed}")
    trace_path = REPO_ROOT / str(findings["trace_path"])
    if not trace_path.is_file():
        trace_path = Path(str(findings["trace_path"]))
    require(trace_path.is_file(), f"{path}: missing trace {findings['trace_path']}")


def validate_comparison(case_id: str) -> None:
    path = OUT_DIR / f"{case_id}_rp2_rp3_comparison.json"
    require(path.is_file(), f"missing {path}")
    comparison = load_json(path)
    aggregate = comparison["aggregate"]
    require(aggregate["pair_count"] == 1, f"{path}: expected one pair")
    require(aggregate["pairwise_disagreements"] == 0, f"{path}: expected zero disagreements")
    require(aggregate["runtime_drift_claims"] == 0, f"{path}: expected zero drift claims")
    require(aggregate["runtime_profiles"] == ["RP2", "RP3"], f"{path}: runtime profile mismatch")


def main() -> int:
    for case_id in CASES:
        validate_findings(case_id, "")
        validate_findings(case_id, "_rp3")
        validate_comparison(case_id)
    report = OUT_DIR / "drift_report.md"
    require(report.is_file(), f"missing {report}")
    require("not live database" in report.read_text(encoding="utf-8"), "report boundary missing")
    print("validated data-extraction MVP artifacts")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"data-extraction MVP validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
