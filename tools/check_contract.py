#!/usr/bin/env python3
"""Check one trace against one security contract."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from skilldiff.contracts import check_trace_against_contract, write_contract_report  # noqa: E402
from skilldiff.contracts.checker import load_contract  # noqa: E402


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Check a SkillDiff trace against a contract.")
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args(argv)

    contract = load_contract(args.contract)
    result = check_trace_against_contract(args.trace, contract)
    write_contract_report(result, args.out_json, args.out_md)
    print(
        "checked {trace} violations={violations} canaries={canaries}".format(
            trace=args.trace,
            violations=result["summary"]["realized_contract_violations"],
            canaries=result["summary"]["canary_observation_count"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
