#!/usr/bin/env python3
"""Run bounded docs-forge live Node runtime-pair installer checks."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_ROOT))

from run_docs_forge_live_project_local_install import (  # noqa: E402
    DEFAULT_OUTPUT_MD as PROJECT_LOCAL_OUTPUT_MD,
    DEFAULT_OUTPUT_JSON as PROJECT_LOCAL_OUTPUT_JSON,
    NODE_FS_PRELOAD,
    TARGET_FIXTURE,
    build_trace,
    run,
    run_project_local_install,
    sha256_file,
    sha256_text,
    snapshot_tree,
    verify_source,
)


MANIFEST_PATH = REPO_ROOT / "benchmark" / "manifests" / "docs-forge-live-runtime-pair.json"
PROJECT_LOCAL_MANIFEST_PATH = REPO_ROOT / "benchmark" / "manifests" / "docs-forge-live-project-local-install.json"
EXPECTED_PATH = REPO_ROOT / "benchmark" / "expected" / "docs-forge" / "project-local-runtime-pair.json"
PROJECT_LOCAL_EXPECTED_PATH = REPO_ROOT / "benchmark" / "expected" / "docs-forge" / "project-local-install.json"
DEFAULT_OUTPUT_JSON = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "project_local_runtime_pair_result.json"
DEFAULT_OUTPUT_MD = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "project_local_runtime_pair_report.md"
DEFAULT_HOST_TRACE = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "project_local_runtime_pair_host_trace.jsonl"
DEFAULT_MINIMAL_TRACE = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "project_local_runtime_pair_minimal_env_trace.jsonl"
RUNTIME_PAIR_RESULT_REF = "results/live/docs-forge-installer/project_local_runtime_pair_result.json"
RUNTIME_PAIR_MANIFEST_REF = "benchmark/manifests/docs-forge-live-runtime-pair.json"
RUNTIME_PAIR_TASK_REF = "benchmark/tasks/docs-forge/project-local-runtime-pair.txt"


PROFILE_HOST_ENV = "LIVE_NODE_HOST_ENV_SYNTHETIC_HOME"
PROFILE_MINIMAL_ENV = "LIVE_NODE_MINIMAL_ENV_SYNTHETIC_HOME"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def observe_command(args: list[str], *, cwd: Path, env: dict[str, str]) -> str:
    completed = subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        return "unavailable"
    return completed.stdout.strip()


def node_executable_hash(env: dict[str, str]) -> str:
    node_path = shutil.which("node", path=env.get("PATH"))
    if node_path is None:
        return "unavailable"
    return sha256_file(Path(node_path))


def host_env_with_synthetic_home(home_root: Path, tmp_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["HOME"] = str(home_root)
    env["TMPDIR"] = str(tmp_root)
    env["CI"] = "1"
    env["NO_COLOR"] = "1"
    env["FORCE_COLOR"] = "0"
    env.pop("DEBUG", None)
    env.pop("NODE_DEBUG", None)
    return env


def minimal_env_with_synthetic_home(home_root: Path, tmp_root: Path) -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", ""),
        "HOME": str(home_root),
        "TMPDIR": str(tmp_root),
        "LANG": os.environ.get("LANG", "C"),
        "LC_ALL": os.environ.get("LC_ALL", "C"),
        "CI": "1",
        "NO_COLOR": "1",
        "FORCE_COLOR": "0",
    }


def profile_specs(temp_root: Path) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for profile_id, env_kind, env_factory in (
        (PROFILE_HOST_ENV, "host_env_inherited_except_synthetic_home_and_tmp", host_env_with_synthetic_home),
        (PROFILE_MINIMAL_ENV, "minimal_allowlisted_env", minimal_env_with_synthetic_home),
    ):
        profile_root = temp_root / profile_id.lower()
        home_root = profile_root / "home"
        tmp_root = profile_root / "tmp"
        target_root = profile_root / "target"
        node_preload_path = profile_root / "node_fs_preload.js"
        node_fs_trace_path = profile_root / "node_fs_events.jsonl"
        home_root.mkdir(parents=True, exist_ok=True)
        tmp_root.mkdir(parents=True, exist_ok=True)
        node_preload_path.write_text(NODE_FS_PRELOAD, encoding="utf-8")
        shutil.copytree(TARGET_FIXTURE, target_root)
        env = env_factory(home_root, tmp_root)
        specs.append(
            {
                "profile_id": profile_id,
                "env_kind": env_kind,
                "profile_root": profile_root,
                "home_root": home_root,
                "tmp_root": tmp_root,
                "target_root": target_root,
                "node_preload_path": node_preload_path,
                "node_fs_trace_path": node_fs_trace_path,
                "env": env,
                "target_initial_snapshot_sha256": sha256_text(json.dumps(snapshot_tree(target_root), sort_keys=True)),
            }
        )
    return specs


def compare_cases(cases: list[dict[str, Any]]) -> dict[str, Any]:
    if len(cases) != 2:
        raise RuntimeError(f"expected two runtime-pair cases, observed {len(cases)}")
    left, right = cases
    checks = {
        "same_exit_code": left["exit_code"] == right["exit_code"],
        "same_argv_sha256": left["argv_sha256"] == right["argv_sha256"],
        "same_node_version": left["node_version"] == right["node_version"],
        "same_node_executable_hash": left["node_executable_sha256"] == right["node_executable_sha256"],
        "same_target_initial_snapshot_sha256": left["target_initial_snapshot_sha256"] == right["target_initial_snapshot_sha256"],
        "same_target_changed_files": left["target_changed_files"] == right["target_changed_files"],
        "same_target_changed_file_hashes": left["target_changed_file_hashes"] == right["target_changed_file_hashes"],
        "same_stdout_sha256": left["stdout_sha256"] == right["stdout_sha256"],
        "same_stderr_sha256": left["stderr_sha256"] == right["stderr_sha256"],
        "same_source_skill_sha256": left["source_skill_sha256"] == right["source_skill_sha256"],
        "no_unexpected_target_mutations": left["unexpected_target_mutation_count"] == 0 and right["unexpected_target_mutation_count"] == 0,
        "no_source_mutations": left["source_mutation_count"] == 0 and right["source_mutation_count"] == 0,
        "no_home_mutations": left["home_mutation_count"] == 0 and right["home_mutation_count"] == 0,
        "no_env_file_reads": not left["env_file_read_observed"] and not right["env_file_read_observed"],
        "no_canary_observations": not left["target_canary_hits"]
        and not right["target_canary_hits"]
        and not left["output_canary_observed"]
        and not right["output_canary_observed"],
    }
    failed_checks = sorted(key for key, value in checks.items() if not value)
    target_hash_mismatches = 0 if checks["same_target_changed_file_hashes"] else len(set(left["target_changed_file_hashes"]) | set(right["target_changed_file_hashes"]))
    return {
        "profile_ids": [left["runtime_profile"], right["runtime_profile"]],
        "checks": checks,
        "failed_checks": failed_checks,
        "pairwise_disagreements": len(failed_checks),
        "target_hash_mismatches": target_hash_mismatches,
        "stdout_hashes": {
            left["runtime_profile"]: left["stdout_sha256"],
            right["runtime_profile"]: right["stdout_sha256"],
        },
        "stderr_hashes": {
            left["runtime_profile"]: left["stderr_sha256"],
            right["runtime_profile"]: right["stderr_sha256"],
        },
    }


def write_markdown(report: dict[str, Any], output_md: Path) -> None:
    lines = [
        "# docs-forge Live Runtime-Pair Install Result",
        "",
        "This artifact records bounded live Node runtime-pair evidence for the pinned",
        "docs-forge project-local installer. It compares two local Node executions",
        "against isolated disposable targets: host environment with synthetic HOME",
        "and minimal allowlisted environment with synthetic HOME.",
        "",
        "| Runtime Profile | Exit | Target Writes | Unexpected Target Writes | Source Mutations | Home Mutations | Result |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for case in report["cases"]:
        lines.append(
            "| {profile} | {exit_code} | {expected} | {unexpected} | {source} | {home} | {result} |".format(
                profile=case["runtime_profile"],
                exit_code=case["exit_code"],
                expected=case["expected_target_mutation_count"],
                unexpected=case["unexpected_target_mutation_count"],
                source=case["source_mutation_count"],
                home=case["home_mutation_count"],
                result="passed" if case["passed"] else "failed",
            )
        )
    lines.extend(
        [
            "",
            "## Pairwise Comparison",
            "",
            "| Check | Result |",
            "| --- | --- |",
        ]
    )
    for key, value in report["comparison"]["checks"].items():
        lines.append(f"| `{key}` | {'pass' if value else 'fail'} |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- This is live project-local installer evidence, not docs-generation evidence.",
            "- It compares two local Node environment profiles and is excluded from MVP runtime-drift counts.",
            "- It does not run `npx`, install packages, modify user home directories, or execute the Codex marketplace command.",
            "- It does not claim RP2/RP3 runtime drift, public-internet safety under packet capture, or complete Node runtime tracing.",
        ]
    )
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--host-trace", type=Path, default=DEFAULT_HOST_TRACE)
    parser.add_argument("--minimal-env-trace", type=Path, default=DEFAULT_MINIMAL_TRACE)
    args = parser.parse_args(argv)

    source_arg = args.source_root or (Path(os.environ["DOCS_FORGE_SOURCE_ROOT"]) if os.environ.get("DOCS_FORGE_SOURCE_ROOT") else None)
    if source_arg is None:
        raise RuntimeError("DOCS_FORGE_SOURCE_ROOT or --source-root is required for live runtime-pair evidence")
    source_root = source_arg.resolve()
    if not source_root.is_dir():
        raise FileNotFoundError(f"source root does not exist: {source_root}")

    manifest = load_json(MANIFEST_PATH)
    project_manifest = load_json(PROJECT_LOCAL_MANIFEST_PATH)
    expected = load_json(PROJECT_LOCAL_EXPECTED_PATH)
    pair_expected = load_json(EXPECTED_PATH)
    verify_source(source_root)

    for path in (args.output_json, args.output_md, args.host_trace, args.minimal_env_trace):
        path.parent.mkdir(parents=True, exist_ok=True)

    cases: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="skilldiff-docs-forge-runtime-pair-") as temp:
        temp_root = Path(temp)
        for spec in profile_specs(temp_root):
            env = spec["env"]
            case = run_project_local_install(
                project_manifest["commands"][0],
                expected=expected,
                source_root=source_root,
                temp_root=temp_root,
                target_root=spec["target_root"],
                node_preload_path=spec["node_preload_path"],
                node_fs_trace_path=spec["node_fs_trace_path"],
                runtime_profile=spec["profile_id"],
                env_base=env,
                home_root=spec["home_root"],
            )
            case["environment_model"] = spec["env_kind"]
            case["synthetic_home"] = True
            case["target_initial_snapshot_sha256"] = spec["target_initial_snapshot_sha256"]
            case["node_version"] = observe_command(["node", "--version"], cwd=source_root, env=env)
            case["node_executable_sha256"] = node_executable_hash(env)
            cases.append(case)

    runtime_profile_ids = [case["runtime_profile"] for case in cases]
    if runtime_profile_ids != pair_expected["expected_runtime_profiles"]:
        raise RuntimeError(f"unexpected runtime profile order: {runtime_profile_ids}")

    comparison = compare_cases(cases)
    passed = [case for case in cases if case["passed"]]
    aggregate = {
        "runtime_profiles_compared": len(cases),
        "runtime_pair_comparisons_executed": 1,
        "commands_run": len(cases),
        "commands_succeeded": len(passed),
        "project_local_installs_executed": len([case for case in cases if case["passed"] and not case["dry_run"]]),
        "non_dry_run_installs_executed": len([case for case in cases if not case["dry_run"]]),
        "target_allowed_mutations_observed": sum(case["expected_target_mutation_count"] for case in cases),
        "unexpected_target_mutations_observed": sum(case["unexpected_target_mutation_count"] for case in cases),
        "source_mutations_observed": sum(case["source_mutation_count"] for case in cases),
        "home_mutations_observed": sum(case["home_mutation_count"] for case in cases),
        "env_file_reads_observed": sum(1 for case in cases if case["env_file_read_observed"]),
        "canary_observations": sum(len(case["target_canary_hits"]) + int(case["output_canary_observed"]) for case in cases),
        "network_commands_observed": 0,
        "npx_commands_observed": 0,
        "codex_marketplace_commands_observed": 0,
        "target_hash_mismatches": comparison["target_hash_mismatches"],
        "runtime_drift_counts_changed": False,
        "runtime_drift_claims_added": 0,
        "pairwise_disagreements_added": 0,
        "canonical_traces_added": 0,
        "canonical_results_added": 0,
        "live_traces_added": 2,
    }
    report = {
        "schema_version": "0.1",
        "artifact_id": "docs-forge-live-runtime-pair",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "safe_to_publish": True,
        "real_secrets_present": False,
        "excluded_from_mvp_runtime_counts": True,
        "execution_level": manifest["execution_level"],
        "evidence_level": manifest["evidence_level"],
        "source_repo": "adhit-r/docs-forge",
        "source_root": "<DOCS_FORGE_SOURCE_ROOT>",
        "source_commit": manifest["source_boundary"]["fixture_source_commit"],
        "source_tree": manifest["source_boundary"]["fixture_source_tree"],
        "manifest_ref": RUNTIME_PAIR_MANIFEST_REF,
        "project_local_manifest_ref": PROJECT_LOCAL_MANIFEST_PATH.relative_to(REPO_ROOT).as_posix(),
        "task_ref": manifest["task_ref"],
        "contract_ref": manifest["contract_ref"],
        "expected_output_ref": manifest["expected_output_ref"],
        "target_fixture_ref": manifest["target_fixture_ref"],
        "target_fixture_snapshot_sha256": cases[0]["target_initial_snapshot_sha256"],
        "single_profile_reference_result_refs": {
            "json": PROJECT_LOCAL_OUTPUT_JSON.relative_to(REPO_ROOT).as_posix(),
            "markdown": PROJECT_LOCAL_OUTPUT_MD.relative_to(REPO_ROOT).as_posix(),
        },
        "trace_refs": {
            PROFILE_HOST_ENV: args.host_trace.resolve().relative_to(REPO_ROOT).as_posix(),
            PROFILE_MINIMAL_ENV: args.minimal_env_trace.resolve().relative_to(REPO_ROOT).as_posix(),
        },
        "runtime_profiles": [
            {
                "profile_id": case["runtime_profile"],
                "environment_model": case["environment_model"],
                "synthetic_home": case["synthetic_home"],
                "node_version": case["node_version"],
                "node_executable_sha256": case["node_executable_sha256"],
            }
            for case in cases
        ],
        "cases": cases,
        "comparison": comparison,
        "aggregate": aggregate,
        "claims_not_supported": [
            "full docs-forge product execution",
            "docs-forge docs-generation workload execution",
            "npx docs-forge execution",
            "global or user-scope installation",
            "network egress absence under packet capture",
            "complete Node runtime tracing",
            "RP2/RP3 runtime-drift claims from local Node environment-pair evidence",
        ],
    }

    args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_markdown(report, args.output_md)
    build_trace(
        report,
        args.output_json,
        args.output_md,
        args.host_trace,
        case_index=0,
        run_id="live-docs-forge-runtime-pair-host-env",
        runtime_profile=PROFILE_HOST_ENV,
        result_ref=RUNTIME_PAIR_RESULT_REF,
        manifest_ref=RUNTIME_PAIR_MANIFEST_REF,
        task_ref=RUNTIME_PAIR_TASK_REF,
    )
    build_trace(
        report,
        args.output_json,
        args.output_md,
        args.minimal_env_trace,
        case_index=1,
        run_id="live-docs-forge-runtime-pair-minimal-env",
        runtime_profile=PROFILE_MINIMAL_ENV,
        result_ref=RUNTIME_PAIR_RESULT_REF,
        manifest_ref=RUNTIME_PAIR_MANIFEST_REF,
        task_ref=RUNTIME_PAIR_TASK_REF,
    )

    if len(passed) != len(cases) or comparison["pairwise_disagreements"] != 0:
        failed = ", ".join(case["runtime_profile"] for case in cases if not case["passed"])
        failed_checks = ", ".join(comparison["failed_checks"])
        raise RuntimeError(f"docs-forge live runtime-pair failed: cases={failed or 'none'} checks={failed_checks or 'none'}")

    print(args.output_json.resolve().relative_to(REPO_ROOT))
    print(args.output_md.resolve().relative_to(REPO_ROOT))
    print(args.host_trace.resolve().relative_to(REPO_ROOT))
    print(args.minimal_env_trace.resolve().relative_to(REPO_ROOT))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as exc:
        print(f"docs-forge live runtime-pair failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
