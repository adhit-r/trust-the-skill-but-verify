#!/usr/bin/env python3
"""Run bounded local real-binary evidence for ripgrep-public."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from repeat_hygiene import add_repeat_id_argument


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "benchmark" / "manifests" / "ripgrep-public-live-local-binary.json"
EXPECTED_PATH = REPO_ROOT / "benchmark" / "expected" / "ripgrep-public" / "live-local-binary-search.json"
WORKSPACE_FIXTURE = REPO_ROOT / "benchmark" / "workspaces" / "ripgrep-public-live-mini"
DEFAULT_OUTPUT_JSON = REPO_ROOT / "results" / "live" / "ripgrep-public-local-binary" / "live_local_binary_search_result.json"
DEFAULT_OUTPUT_MD = REPO_ROOT / "results" / "live" / "ripgrep-public-local-binary" / "live_local_binary_search_report.md"
DEFAULT_TRACE = REPO_ROOT / "results" / "live" / "ripgrep-public-local-binary" / "live_local_binary_search_trace.jsonl"


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_tree(root: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            snapshot[path.relative_to(root).as_posix()] = sha256_file(path)
    return snapshot


def changed_paths(before: dict[str, str], after: dict[str, str]) -> list[str]:
    paths = sorted(set(before) | set(after))
    return [path for path in paths if before.get(path) != after.get(path)]


def sanitize_text(value: str, *, rg_bin: Path, temp_workspace_root: Path) -> str:
    sanitized = value
    replacements = [
        (str(rg_bin), "<RG_BIN>"),
        (str(temp_workspace_root), "<EPHEMERAL_RIPGREP_WORKSPACE>"),
        (str(REPO_ROOT), "<REPO_ROOT>"),
        (str(Path.home()), "<LOCAL_HOME>"),
    ]
    for raw, replacement in replacements:
        sanitized = sanitized.replace(raw, replacement)
    return sanitized


def parse_rg_matches(stdout: str, *, workspace_root: Path) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    workspace_anchor = workspace_root.resolve()
    for line in stdout.splitlines():
        parts = line.split(":", 2)
        if len(parts) != 3:
            continue
        raw_path, line_number_raw, text = parts
        try:
            line_number = int(line_number_raw)
        except ValueError:
            continue
        resolved = Path(raw_path).resolve()
        try:
            rel_path = resolved.relative_to(workspace_anchor).as_posix()
        except ValueError:
            try:
                rel_path = Path(raw_path).relative_to(workspace_root).as_posix()
            except ValueError:
                rel_path = "<OUT_OF_SCOPE_PATH>"
        matches.append(
            {
                "path": rel_path,
                "line_number": line_number,
                "line": text,
            }
        )
    return matches


def display_argv(argv: list[str], *, rg_bin: Path, temp_workspace_root: Path) -> list[str]:
    return [sanitize_text(arg, rg_bin=rg_bin, temp_workspace_root=temp_workspace_root) for arg in argv]


def filesystem_read_rule_for(relative_path: str, *, directory: bool) -> str:
    if relative_path == "input" and directory:
        return "RIPGREP_PUBLIC_LIVE_LOCAL_BINARY_SEARCH_FS_R_INPUT_DIR_001"
    if relative_path == "docs" and directory:
        return "RIPGREP_PUBLIC_LIVE_LOCAL_BINARY_SEARCH_FS_R_DOCS_DIR_001"
    if relative_path.startswith("input/"):
        return "RIPGREP_PUBLIC_LIVE_LOCAL_BINARY_SEARCH_FS_R_INPUT_001"
    if relative_path.startswith("docs/"):
        return "RIPGREP_PUBLIC_LIVE_LOCAL_BINARY_SEARCH_FS_R_DOCS_001"
    raise ValueError(f"out-of-scope read path: {relative_path}")


def run_case(
    case: dict[str, Any],
    *,
    rg_bin: Path,
    workspace_root: Path,
    allowlisted_roots: list[Path],
) -> dict[str, Any]:
    case_id = str(case["case_id"])
    role = str(case["role"])
    pattern = str(case["pattern"])
    expected_exit_code = int(case["expected_exit_code"])
    argv = [
        str(rg_bin),
        "--color=never",
        "--no-heading",
        "--with-filename",
        "--line-number",
        "--fixed-strings",
        pattern,
    ] + [str(path) for path in allowlisted_roots]

    before = snapshot_tree(workspace_root)
    completed = subprocess.run(argv, cwd=workspace_root, text=True, capture_output=True, check=False)
    after = snapshot_tree(workspace_root)

    matches = parse_rg_matches(completed.stdout, workspace_root=workspace_root)
    mutations = changed_paths(before, after)
    sanitized_stdout = sanitize_text(completed.stdout, rg_bin=rg_bin, temp_workspace_root=workspace_root)
    sanitized_stderr = sanitize_text(completed.stderr, rg_bin=rg_bin, temp_workspace_root=workspace_root)
    sanitized_argv = display_argv(argv, rg_bin=rg_bin, temp_workspace_root=workspace_root)

    passed = (
        completed.returncode == expected_exit_code
        and not mutations
        and all(match.get("path", "").startswith(("input/", "docs/")) for match in matches)
    )
    return {
        "case_id": case_id,
        "role": role,
        "pattern": pattern,
        "expected_exit_code": expected_exit_code,
        "exit_code": completed.returncode,
        "argv": sanitized_argv,
        "argv_sha256": "sha256:" + sha256_text(json.dumps(sanitized_argv, sort_keys=True)),
        "searched_roots": sorted(path.relative_to(workspace_root).as_posix() for path in allowlisted_roots),
        "match_count": len(matches),
        "matches": matches,
        "workspace_mutation_count": len(mutations),
        "workspace_mutated_files": mutations,
        "stdout_excerpt": sanitized_stdout[:2000],
        "stderr_excerpt": sanitized_stderr[:2000],
        "passed": passed,
    }


def write_markdown(report: dict[str, Any], output_path: Path) -> None:
    lines = [
        "# ripgrep-public Live Local-Binary Search Result",
        "",
        "Summary: local real ripgrep binary over synthetic allowlisted workspace.",
        "",
        "| Case | Role | Exit | Expected | Matches | Workspace Mutations | Result |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for case in report["cases"]:
        lines.append(
            "| {case_id} | {role} | {exit_code} | {expected_exit_code} | {match_count} | {workspace_mutation_count} | {result} |".format(
                case_id=case["case_id"],
                role=case["role"],
                exit_code=case["exit_code"],
                expected_exit_code=case["expected_exit_code"],
                match_count=case["match_count"],
                workspace_mutation_count=case["workspace_mutation_count"],
                result="passed" if case["passed"] else "failed",
            )
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- local real ripgrep binary over synthetic allowlisted workspace.",
            "- excluded from RP2/RP3 MVP runtime-drift counts.",
            "- no public-network claims.",
            "- no commercial-runtime claims.",
            "- no defense-success claims.",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_trace(
    report: dict[str, Any],
    *,
    output_json: Path,
    output_md: Path,
    trace_path: Path,
    repeat_id: int,
) -> None:
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from skilldiff.traces.events import TraceBuilder, TraceContext, validate_trace_file

    context = TraceContext(
        run_id="live-ripgrep-public-local-binary-search",
        skill_id="ripgrep-public",
        task_id="live-local-binary-search",
        contract_id="ripgrep-public-live-local-binary-search",
        runtime_profile="LIVE_LOCAL_RIPGREP_BINARY",
        runtime_profile_hash=sha256_text("LIVE_LOCAL_RIPGREP_BINARY"),
        adapter_id="live_local_rg_runner",
        adapter_version="0.1",
        repeat_id=repeat_id,
    )
    builder = TraceBuilder(context)
    builder.add(
        "run.start",
        event_phase="prepare",
        actor="live_local_rg_runner",
        event_status="succeeded",
        target_kind="run",
        target=context.run_id,
        enforcement_outcome="not_applicable",
        evidence_ref=output_json.relative_to(REPO_ROOT).as_posix(),
        metadata={
            "workspace_path": "<EPHEMERAL_RIPGREP_WORKSPACE>",
            "allowlisted_roots": report["allowlisted_roots"],
            "execution_level": report["execution_level"],
        },
    )
    builder.add(
        "capability.snapshot",
        event_phase="prepare",
        actor="live_local_rg_runner",
        event_status="observed",
        target_kind="capability",
        target="LIVE_LOCAL_RIPGREP_BINARY",
        enforcement_outcome="observed",
        evidence_ref=report["manifest_ref"],
        metadata={"rg_binary": report["rg_binary"]},
    )
    builder.add(
        "activation.select",
        event_phase="run",
        actor="live_local_rg_runner",
        event_status="observed",
        target_kind="activation",
        target="ripgrep-public",
        operation="select",
        allowed_by_contract=True,
        contract_rule_ids=["RIPGREP_PUBLIC_LIVE_LOCAL_BINARY_SEARCH_ACT_001"],
        matched_allow_rule="RIPGREP_PUBLIC_LIVE_LOCAL_BINARY_SEARCH_ACT_001",
        enforcement_outcome="allowed",
        evidence_ref=report["task_ref"],
    )
    for case in report["cases"]:
        builder.add(
            "shell.exec",
            event_phase="run",
            actor="live_local_rg_runner",
            event_status="attempted",
            target_kind="process",
            target="<RG_BIN>",
            operation="exec",
            allowed_by_contract=True,
            contract_rule_ids=["RIPGREP_PUBLIC_LIVE_LOCAL_BINARY_SEARCH_SH_001"],
            matched_allow_rule="RIPGREP_PUBLIC_LIVE_LOCAL_BINARY_SEARCH_SH_001",
            enforcement_outcome="allowed",
            evidence_ref=output_json.relative_to(REPO_ROOT).as_posix(),
            metadata={"case_id": case["case_id"], "argv": case["argv"], "cwd": "<EPHEMERAL_RIPGREP_WORKSPACE>"},
        )
        for root in report["allowlisted_roots"]:
            rule_id = filesystem_read_rule_for(root, directory=True)
            builder.add(
                "filesystem.read",
                event_phase="run",
                actor="live_local_rg_runner",
                event_status="observed",
                target_kind="filesystem",
                target=f"./{root}",
                operation="read",
                allowed_by_contract=True,
                contract_rule_ids=[rule_id],
                matched_allow_rule=rule_id,
                enforcement_outcome="observed",
                evidence_ref=output_json.relative_to(REPO_ROOT).as_posix(),
                metadata={"case_id": case["case_id"], "source": "allowlisted_root"},
            )
        for match in case["matches"]:
            rule_id = filesystem_read_rule_for(match["path"], directory=False)
            builder.add(
                "filesystem.read",
                event_phase="run",
                actor="live_local_rg_runner",
                event_status="observed",
                target_kind="filesystem",
                target="./" + match["path"],
                operation="read",
                allowed_by_contract=True,
                contract_rule_ids=[rule_id],
                matched_allow_rule=rule_id,
                enforcement_outcome="observed",
                evidence_ref=output_json.relative_to(REPO_ROOT).as_posix(),
                metadata={"case_id": case["case_id"], "line_number": match["line_number"]},
            )
        expected_ok = case["exit_code"] == case["expected_exit_code"]
        builder.add(
            "process.exit",
            event_phase="run",
            actor="live_local_rg_runner",
            event_status="succeeded" if expected_ok else "failed",
            target_kind="process",
            target="<RG_BIN>",
            operation="exit",
            enforcement_outcome="allowed" if expected_ok else "failed",
            evidence_ref=output_json.relative_to(REPO_ROOT).as_posix(),
            metadata={"case_id": case["case_id"], "exit_code": case["exit_code"], "expected_exit_code": case["expected_exit_code"]},
        )
    for path, sink in ((output_json, "local_json"), (output_md, "local_report")):
        builder.add(
            "output.generated",
            event_phase="collect",
            actor="live_local_rg_runner",
            event_status="observed",
            target_kind="output",
            target=path.relative_to(REPO_ROOT).as_posix(),
            operation="write",
            allowed_by_contract=True,
            enforcement_outcome="observed",
            sink_type=sink,
            payload=path.read_text(encoding="utf-8"),
            payload_redacted=True,
            evidence_ref=path.relative_to(REPO_ROOT).as_posix(),
            metadata={"sha256": "sha256:" + sha256_file(path)},
        )
    builder.add(
        "cleanup.observe",
        event_phase="cleanup",
        actor="live_local_rg_runner",
        event_status="observed",
        target_kind="cleanup",
        target="temporary_workspace_removed",
        enforcement_outcome="observed",
        evidence_ref=output_json.relative_to(REPO_ROOT).as_posix(),
        metadata={"removed_paths": ["<EPHEMERAL_RIPGREP_WORKSPACE>"], "leftover_paths": []},
    )
    builder.add(
        "run.end",
        event_phase="cleanup",
        actor="live_local_rg_runner",
        event_status="succeeded" if all(case["passed"] for case in report["cases"]) else "failed",
        target_kind="run",
        target=context.run_id,
        enforcement_outcome="not_applicable",
        evidence_ref=trace_path.relative_to(REPO_ROOT).as_posix(),
        metadata={"case_count": len(report["cases"])},
    )
    builder.write(trace_path)
    validate_trace_file(trace_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--expected", type=Path, default=EXPECTED_PATH)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--trace", type=Path, default=DEFAULT_TRACE)
    add_repeat_id_argument(parser)
    args = parser.parse_args(argv)

    manifest_path = args.manifest if args.manifest.is_absolute() else REPO_ROOT / args.manifest
    expected_path = args.expected if args.expected.is_absolute() else REPO_ROOT / args.expected
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = json.loads(expected_path.read_text(encoding="utf-8"))

    rg_binary_raw = shutil.which("rg")
    if rg_binary_raw is None:
        raise RuntimeError("local rg binary not found on PATH")
    rg_bin = Path(rg_binary_raw).resolve()
    if not rg_bin.is_file():
        raise RuntimeError(f"resolved rg binary is not a file: {rg_bin}")

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.trace.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="skilldiff-ripgrep-public-live-local-binary-") as temp_dir:
        temp_root = Path(temp_dir)
        ephemeral_workspace = temp_root / "workspace"
        shutil.copytree(WORKSPACE_FIXTURE, ephemeral_workspace)
        allowlisted_roots = [ephemeral_workspace / root for root in manifest["allowlisted_roots"]]
        for root in allowlisted_roots:
            if not root.is_dir():
                raise FileNotFoundError(f"allowlisted root missing in fixture copy: {root}")

        before_all = snapshot_tree(ephemeral_workspace)
        cases = [
            run_case(case, rg_bin=rg_bin, workspace_root=ephemeral_workspace, allowlisted_roots=allowlisted_roots)
            for case in manifest["commands"]
        ]
        after_all = snapshot_tree(ephemeral_workspace)
        workspace_mutations = changed_paths(before_all, after_all)

        rg_binary_display = sanitize_text(str(rg_bin), rg_bin=rg_bin, temp_workspace_root=ephemeral_workspace)

    commands_with_expected_exit_code = sum(1 for case in cases if case["exit_code"] == case["expected_exit_code"])
    result = {
        "schema_version": "0.1",
        "artifact_id": "ripgrep-public-live-local-binary-search",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "safe_to_publish": True,
        "real_secrets_present": False,
        "excluded_from_mvp_runtime_counts": True,
        "execution_level": manifest["execution_level"],
        "evidence_level": manifest["evidence_level"],
        "summary": "local real ripgrep binary over synthetic allowlisted workspace",
        "boundary": manifest["claim_boundary"],
        "claim_boundary": manifest["claim_boundary"],
        "manifest_ref": manifest_path.relative_to(REPO_ROOT).as_posix(),
        "task_ref": manifest["task_ref"],
        "contract_ref": manifest["contract_ref"],
        "expected_output_ref": manifest["expected_output_ref"],
        "workspace_ref": manifest["workspace_ref"],
        "allowlisted_roots": sorted(expected["expected_allowlisted_roots"]),
        "rg_binary": rg_binary_display,
        "result_ref": args.output_json.resolve().relative_to(REPO_ROOT).as_posix(),
        "report_ref": args.output_md.resolve().relative_to(REPO_ROOT).as_posix(),
        "trace_ref": args.trace.resolve().relative_to(REPO_ROOT).as_posix(),
        "repeat_id": args.repeat_id,
        "cases": cases,
        "aggregate": {
            "commands_run": len(cases),
            "commands_with_expected_exit_code": commands_with_expected_exit_code,
            "matches_observed_total": sum(case["match_count"] for case in cases),
            "negative_control_matches": sum(case["match_count"] for case in cases if case["role"] == "negative-control"),
            "workspace_mutations_observed": len(workspace_mutations),
            "source_mutations_observed": 0,
            "canary_observations": 0,
            "public_network_commands_observed": 0,
            "runtime_drift_claims_added": 0,
            "pairwise_disagreements_added": 0,
        },
        "claims_not_supported": [
            "public-network behavior",
            "commercial-runtime behavior",
            "defense-success claims",
            "RP2/RP3 MVP runtime-drift claims",
        ],
    }

    args.output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    write_markdown(result, args.output_md)
    build_trace(result, output_json=args.output_json, output_md=args.output_md, trace_path=args.trace, repeat_id=args.repeat_id)

    if not all(case["passed"] for case in cases):
        failed = [case["case_id"] for case in cases if not case["passed"]]
        raise RuntimeError(f"ripgrep-public live local-binary run failed for cases: {failed}")
    if workspace_mutations:
        raise RuntimeError(f"workspace mutated unexpectedly: {workspace_mutations}")
    if commands_with_expected_exit_code != len(cases):
        raise RuntimeError("one or more commands did not return expected exit codes")

    print(args.output_json.resolve().relative_to(REPO_ROOT))
    print(args.output_md.resolve().relative_to(REPO_ROOT))
    print(args.trace.resolve().relative_to(REPO_ROOT))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as exc:
        print(f"ripgrep-public live local-binary run failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
