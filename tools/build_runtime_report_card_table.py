#!/usr/bin/env python3
"""Build the paper-facing runtime report-card summary table."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CARDS_DIR = REPO_ROOT / "results" / "derived" / "runtime-report-cards"
DEFAULT_OUTPUT = REPO_ROOT / "paper" / "tables" / "runtime-report-card-summary.md"


RUNTIME_ROLES = {
    "RP1": "Restricted-hosted simulator",
    "RP2": "Local controlled fixture",
    "RP3": "Docker-backed controlled fixture",
    "RP5": "Plugin-style fixture",
    "RP6": "Policy-hardened report card",
}

RUNTIME_BOUNDARIES = {
    "RP1": "Simulator-backed only; not hosted-provider behavior.",
    "RP2": "Controlled local adapter evidence; not commercial local-agent behavior.",
    "RP3": "Container-backed supported-trace evidence; not syscall-complete tracing.",
    "RP5": "Fixture-backed plugin lifecycle evidence; not commercial plugin-store or live host API behavior.",
    "RP6": "Mitigation/report-card pilot with utility cost reported; not defense success.",
}


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_cards(cards_dir: Path) -> list[dict[str, Any]]:
    paths = sorted(cards_dir.glob("*_report_card.json"))
    if not paths:
        raise RuntimeError(f"no runtime report-card JSON files found in {display_path(cards_dir)}")
    cards = [load_json(path) for path in paths]
    seen: set[str] = set()
    for card in cards:
        runtime = str(card.get("runtime_profile") or "")
        if not runtime:
            raise RuntimeError(f"{display_path(cards_dir)}: report card missing runtime_profile")
        if runtime in seen:
            raise RuntimeError(f"{display_path(cards_dir)}: duplicate runtime_profile {runtime}")
        seen.add(runtime)
    return sorted(cards, key=lambda card: str(card["runtime_profile"]))


def metric_cell(metric: dict[str, Any]) -> str:
    if not metric.get("supported", False):
        return "NA"
    numerator = metric.get("numerator")
    denominator = metric.get("denominator")
    value = metric.get("value")
    if value is None:
        return "NA"
    return f"{numerator}/{denominator} ({float(value):.3f})"


def value_cell(value: Any) -> str:
    if value is None:
        return "NA"
    return str(value)


def render_table(cards: list[dict[str, Any]]) -> str:
    lines = [
        "# Runtime Report-Card Summary",
        "",
        "This table is generated from `results/derived/runtime-report-cards/*_report_card.json`.",
        "It is paper-facing source material only for the evidence levels named below.",
        "It does not claim commercial-runtime behavior, public-network behavior, defense success, source-mix completion, prevalence, or completed human review.",
        "",
        "| Runtime | Paper role | Runs | Trace-valid | Realized violation runs | Attempted-overreach runs | Missing-output runs | Benign task success | Comparison coverage | Boundary |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for card in cards:
        runtime = str(card["runtime_profile"])
        aggregate = card["aggregate"]
        metrics = card["metrics"]
        evidence = card["evidence_coverage"]
        lines.append(
            "| `{runtime}` | {role} | {runs} | {trace_valid} | {realized} | {attempted} | {missing} | {benign_success} | {comparison_coverage} | {boundary} |".format(
                runtime=runtime,
                role=RUNTIME_ROLES.get(runtime, "Runtime report card"),
                runs=value_cell(aggregate.get("run_count")),
                trace_valid=value_cell(aggregate.get("trace_valid_runs")),
                realized=value_cell(aggregate.get("realized_violation_runs")),
                attempted=value_cell(aggregate.get("attempted_overreach_runs")),
                missing=value_cell(aggregate.get("missing_output_runs")),
                benign_success=metric_cell(metrics["benign_task_success_rate"]),
                comparison_coverage=metric_cell(evidence["comparison_pair_coverage_rate"]),
                boundary=RUNTIME_BOUNDARIES.get(runtime, "Use only with the report-card evidence boundary."),
            )
        )

    lines.extend(
        [
            "",
            "## Reading Notes",
            "",
            "- Realized violation runs and attempted-overreach runs are separate; blocked or failed denied actions are not counted as realized violations.",
            "- `Benign task success` is computed over report-card rows labeled benign; rows with unknown role remain in aggregate run counts but not in that rate.",
            "- `Comparison coverage` is unsupported for profiles with no pairwise comparison denominator, such as the current RP5 fixture.",
            "- RP6 rows are mitigation/report-card evidence and must be reported with missing-output and utility-cost context.",
            "",
            "## Source Artifacts",
            "",
        ]
    )
    for card in cards:
        runtime = str(card["runtime_profile"])
        lines.append(f"- `{runtime}`: `results/derived/runtime-report-cards/{runtime.lower()}_report_card.json`")
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cards-dir", type=Path, default=DEFAULT_CARDS_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true", help="Check that the generated table is up to date.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    cards_dir = args.cards_dir if args.cards_dir.is_absolute() else REPO_ROOT / args.cards_dir
    output = args.output if args.output.is_absolute() else REPO_ROOT / args.output
    expected = render_table(load_cards(cards_dir))
    if args.check:
        if not output.exists():
            print(f"missing runtime report-card summary table: {display_path(output)}", file=sys.stderr)
            return 1
        observed = output.read_text(encoding="utf-8")
        if observed != expected:
            print(f"stale runtime report-card summary table: {display_path(output)}", file=sys.stderr)
            return 1
        print(f"runtime report-card summary table up to date: {display_path(output)}")
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(expected, encoding="utf-8")
    print(display_path(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
