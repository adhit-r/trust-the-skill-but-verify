#!/usr/bin/env python3
"""Compare two or more contract-check JSON outputs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from skilldiff.metrics import compare_contract_runs, load_contract_result  # noqa: E402
from skilldiff.reports import write_comparison_report  # noqa: E402


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Compare SkillDiff contract-check JSON outputs.")
    parser.add_argument("contract_results", nargs="+", type=Path, help="Contract-check JSON files to compare.")
    parser.add_argument("--out-json", type=Path, required=True, help="Path for the machine-readable JSON report.")
    parser.add_argument("--out-md", type=Path, required=True, help="Path for the Markdown report.")
    args = parser.parse_args(argv)

    results = [load_contract_result(path) for path in args.contract_results]
    report = compare_contract_runs(results)
    write_comparison_report(report, args.out_json, args.out_md)
    print(
        "compared {runs} runs pairs={pairs} disagreements={disagreements} runtime_drift_claims={claims}".format(
            runs=report["aggregate"]["run_count"],
            pairs=report["aggregate"]["pair_count"],
            disagreements=report["aggregate"]["pairwise_disagreements"],
            claims=report["aggregate"]["runtime_drift_claims"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
