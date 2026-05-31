"""Command-line entrypoints for the SkillDiff research harness."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

from skilldiff.adapters import RunSpec
from skilldiff.adapters.docker import DockerDryRunAdapter
from skilldiff.adapters.local import LocalDryRunAdapter
from skilldiff.adapters.policy import HardenedPolicyAdapter
from skilldiff.adapters.plugin_fixture import PluginFixtureAdapter
from skilldiff.adapters.restricted_hosted import RestrictedHostedSimAdapter
from skilldiff.traces import TraceValidationError, validate_trace_file
from skilldiff.traces.events import build_trace_from_artifacts


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML object")
    return data


def choose_adapter(profile: dict[str, Any]) -> Any:
    adapter_id = profile["adapter"]["adapter_id"]
    if adapter_id == "restricted_hosted_sim":
        return RestrictedHostedSimAdapter()
    if adapter_id == "plugin_fixture_adapter":
        return PluginFixtureAdapter()
    if adapter_id == "local_adapter":
        return LocalDryRunAdapter()
    if adapter_id == "docker_adapter":
        return DockerDryRunAdapter()
    if adapter_id == "hardened_policy_adapter":
        return HardenedPolicyAdapter()
    raise ValueError(f"no RM-07 adapter implementation for {adapter_id}")


def load_task_prompt(contract: dict[str, Any]) -> str:
    task = contract.get("task", {})
    prompt_ref = task.get("prompt_ref")
    if isinstance(prompt_ref, str) and prompt_ref and prompt_ref != "inline":
        prompt_path = Path(prompt_ref)
        if not prompt_path.is_absolute():
            prompt_path = REPO_ROOT / prompt_path
        return prompt_path.read_text(encoding="utf-8")
    return str(task.get("intent", ""))


def cmd_run(args: argparse.Namespace) -> int:
    profile = load_yaml(args.profile)
    contract = load_yaml(args.contract)
    adapter = choose_adapter(profile)
    command = args.command or []
    run_spec = RunSpec(
        skill_id=contract["skill_id"],
        task_id=contract["task_id"],
        contract_id=contract["contract_id"],
        repeat_id=args.repeat_id,
        skill_artifact=args.skill_artifact,
        task_prompt_ref=str(contract.get("task", {}).get("prompt_ref", "inline")),
        variant_id=args.variant_id,
        workspace_seed=args.workspace_seed_id or str(args.workspace),
        output_root=args.output_root,
        dry_run=not args.live,
        command=command,
    )
    task_prompt = load_task_prompt(contract)
    prepared = adapter.prepare(run_spec, profile, args.workspace, contract, task_prompt)
    execution = adapter.run(prepared)
    collected = adapter.collect(prepared, execution)
    cleanup = adapter.cleanup(prepared, execution)
    try:
        trace_path = build_trace_from_artifacts(prepared, execution, collected, cleanup, contract)
    except TraceValidationError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    result = {
        "adapter_outcome": execution.adapter_outcome,
        "exit_code": execution.exit_code,
        "profile_id": profile["profile_id"],
        "run_id": prepared.run_id,
        "trace_path": str(trace_path),
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if execution.exit_code == 0 else 2


def cmd_compare(args: argparse.Namespace) -> int:
    summaries = []
    for trace_path in args.traces:
        events = validate_trace_file(trace_path)
        counter = Counter(event["event_type"] for event in events)
        summaries.append(
            {
                "event_count": len(events),
                "event_types": dict(sorted(counter.items())),
                "profile": events[0]["runtime_profile"],
                "run_id": events[0]["run_id"],
                "trace_path": str(trace_path),
            }
        )
    print(json.dumps({"traces": summaries}, indent=2, sort_keys=True))
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    events = validate_trace_file(args.trace)
    counter = Counter(event["event_type"] for event in events)
    canary_events = [event for event in events if event["canary_observed"]]
    print(f"# Trace Report\n")
    print(f"- Run: `{events[0]['run_id']}`")
    print(f"- Profile: `{events[0]['runtime_profile']}`")
    print(f"- Events: `{len(events)}`")
    print(f"- Canary events: `{len(canary_events)}`")
    print("\n## Event Counts\n")
    for event_type, count in sorted(counter.items()):
        print(f"- `{event_type}`: {count}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    try:
        events = validate_trace_file(args.trace)
    except TraceValidationError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"validated {len(events)} trace event(s)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SkillDiff research harness")
    subparsers = parser.add_subparsers(dest="command_name", required=True)

    run = subparsers.add_parser("run", help="Run one skill-task-profile trace")
    run.add_argument("--profile", type=Path, required=True)
    run.add_argument("--contract", type=Path, required=True)
    run.add_argument("--workspace", type=Path, required=True)
    run.add_argument("--output-root", type=Path, default=Path("results/raw"))
    run.add_argument("--workspace-seed-id", default="")
    run.add_argument("--skill-artifact", default="local-fixture")
    run.add_argument("--variant-id", default="fixture-variant")
    run.add_argument("--repeat-id", type=int, default=0)
    run.add_argument("--live", action="store_true", help="Execute the prepared command when supported")
    run.add_argument("--command", nargs=argparse.REMAINDER, help="Command argv to execute after --command")
    run.set_defaults(func=cmd_run)

    compare = subparsers.add_parser("compare", help="Summarize traces for later differential analysis")
    compare.add_argument("traces", nargs="+", type=Path)
    compare.set_defaults(func=cmd_compare)

    report = subparsers.add_parser("report", help="Print a small Markdown trace report")
    report.add_argument("trace", type=Path)
    report.set_defaults(func=cmd_report)

    validate = subparsers.add_parser("validate-trace", help="Validate one trace.jsonl file")
    validate.add_argument("trace", type=Path)
    validate.set_defaults(func=cmd_validate)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
