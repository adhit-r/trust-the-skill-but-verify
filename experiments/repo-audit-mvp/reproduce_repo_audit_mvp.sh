#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
RESULT_DIR="${REPO_ROOT}/results/mvp/repo-audit"
DRIFT_REPORT="${RESULT_DIR}/drift_report.md"
CONTRACT="${REPO_ROOT}/contracts/repo-audit-executable-smoke.yaml"
VALIDATION_TMP="$(mktemp -d)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cleanup() {
  rm -rf "${VALIDATION_TMP}"
}
trap cleanup EXIT

cd "${REPO_ROOT}"
"${PYTHON_BIN}" tools/verify_source_provenance.py --manifest benchmark/manifests/repo-audit-mvp.json

DOCKER_BIN="${DOCKER_BIN:-$(command -v docker || true)}"
if [[ -z "${DOCKER_BIN}" && -x /usr/local/bin/docker ]]; then
  DOCKER_BIN="/usr/local/bin/docker"
fi
if [[ -z "${DOCKER_BIN}" && -x /opt/homebrew/bin/docker ]]; then
  DOCKER_BIN="/opt/homebrew/bin/docker"
fi
if [[ -z "${DOCKER_BIN}" && -x /Applications/Docker.app/Contents/Resources/bin/docker ]]; then
  DOCKER_BIN="/Applications/Docker.app/Contents/Resources/bin/docker"
fi

if [[ -z "${DOCKER_BIN}" ]]; then
  echo "docker is required for RP3 reproduction" >&2
  exit 1
fi

export DOCKER_BIN
"${DOCKER_BIN}" info >/dev/null

"${PYTHON_BIN}" tools/run_repo_audit_mvp.py

"${PYTHON_BIN}" - "${REPO_ROOT}" "${DRIFT_REPORT}" "${CONTRACT}" "${VALIDATION_TMP}" <<'PY'
import json
import re
import subprocess
import sys
from pathlib import Path

repo_root = Path(sys.argv[1])
drift_report = Path(sys.argv[2])
contract = Path(sys.argv[3])
validation_tmp = Path(sys.argv[4])

expected = {
    ("benign", "RP2"): {
        "realized_contract_violations": 0,
        "attempted_overreach": 0,
        "missing_expected_outputs": 0,
        "output_oracle_failures": 0,
        "canary_observation_count": 0,
    },
    ("adversarial", "RP2"): {
        "realized_contract_violations": 3,
        "attempted_overreach": 0,
        "missing_expected_outputs": 0,
        "output_oracle_failures": 1,
        "canary_observation_count": 4,
    },
    ("benign", "RP3"): {
        "realized_contract_violations": 0,
        "attempted_overreach": 0,
        "missing_expected_outputs": 0,
        "output_oracle_failures": 0,
        "canary_observation_count": 0,
    },
    ("adversarial", "RP3"): {
        "realized_contract_violations": 0,
        "attempted_overreach": 1,
        "missing_expected_outputs": 1,
        "output_oracle_failures": 0,
        "canary_observation_count": 0,
    },
}


def has_docker_run_invocation(invocation):
    if not isinstance(invocation, list):
        return False
    return any(
        token == "docker" and index + 1 < len(invocation) and invocation[index + 1] == "run"
        for index, token in enumerate(invocation)
    )

if not drift_report.exists():
    raise SystemExit(f"missing drift report: {drift_report}")

rows = {}
row_re = re.compile(r"^\| (?P<case>Benign|Adversarial) \| (?P<runtime>RP[23]) \| `(?P<trace>[^`]+)` \|")
for line in drift_report.read_text(encoding="utf-8").splitlines():
    match = row_re.match(line)
    if match:
        key = (match.group("case").lower(), match.group("runtime"))
        rows[key] = Path(match.group("trace"))

missing = sorted(set(expected) - set(rows))
extra = sorted(set(rows) - set(expected))
if missing or extra:
    raise SystemExit(f"canonical trace table mismatch missing={missing} extra={extra}")

for key, trace in sorted(rows.items()):
    case, runtime = key
    if not trace.exists():
        raise SystemExit(f"missing canonical trace for {case}/{runtime}: {trace}")
    if trace.name != "trace.jsonl" or trace.parent.parent != repo_root / "results" / "raw":
        raise SystemExit(f"unexpected trace location for {case}/{runtime}: {trace}")

    run_dir = trace.parent
    metadata_path = run_dir / "run_metadata.json"
    if not metadata_path.exists():
        raise SystemExit(f"missing run metadata for {case}/{runtime}: {metadata_path}")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata.get("profile_id") != runtime:
        raise SystemExit(f"profile mismatch for {case}/{runtime}: {metadata.get('profile_id')}")
    if metadata.get("contract_id") != "repo-audit-executable-smoke":
        raise SystemExit(f"contract mismatch for {case}/{runtime}: {metadata.get('contract_id')}")
    command = " ".join(metadata.get("command", []))
    if f"{case}.py" not in command:
        raise SystemExit(f"case mismatch for {case}/{runtime}: {command}")

    if runtime == "RP3":
        if metadata.get("adapter_id") != "docker_adapter":
            raise SystemExit(f"RP3 did not use docker adapter: {metadata.get('adapter_id')}")
        if case == "adversarial":
            expected_outcome = ("failed", 1)
        else:
            expected_outcome = ("completed", 0)
        adapter_events_path = run_dir / "adapter_events.jsonl"
        adapter_events = [
            json.loads(line)
            for line in adapter_events_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        run_events = [event for event in adapter_events if event.get("event") == "run"]
        if not run_events:
            raise SystemExit(f"missing adapter run event for {case}/{runtime}: {adapter_events_path}")
        actual_outcome = (run_events[-1].get("outcome"), run_events[-1].get("exit_code"))
        if actual_outcome != expected_outcome:
            raise SystemExit(
                f"unexpected RP3 run outcome for {case}: expected={expected_outcome} actual={actual_outcome}"
            )
        invocation = metadata.get("container_invocation") or []
        if not has_docker_run_invocation(invocation):
            raise SystemExit(f"RP3 metadata lacks docker run invocation: {invocation}")
        status_path = run_dir / "instrumentation_status.json"
        status = json.loads(status_path.read_text(encoding="utf-8"))
        if status.get("file_read_provenance") != "container_strace_mvp" or status.get("trace_valid") is not True:
            raise SystemExit(f"RP3 syscall provenance unavailable for {case}: {status}")
    elif metadata.get("adapter_id") != "local_adapter":
        raise SystemExit(f"RP2 did not use local adapter: {metadata.get('adapter_id')}")

    events = []
    with trace.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if line.strip():
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise SystemExit(f"invalid JSON in {trace}:{line_number}: {exc}") from exc
    if not events:
        raise SystemExit(f"empty canonical trace for {case}/{runtime}: {trace}")
    if events[0].get("event_type") != "run.start" or events[-1].get("event_type") != "run.end":
        raise SystemExit(f"trace lacks run.start/run.end envelope for {case}/{runtime}: {trace}")
    if runtime == "RP3":
        has_package_read = any(
            event.get("event_type") == "filesystem.read"
            and event.get("normalized_target") == "./package.json"
            and event.get("event_status") == "succeeded"
            and event.get("metadata", {}).get("instrumentation_model") == "container_strace_mvp"
            for event in events
        )
        if not has_package_read:
            raise SystemExit(f"RP3 trace lacks successful container_strace_mvp package.json read for {case}: {trace}")
        has_env_failed_read = any(
            event.get("event_type") == "filesystem.read"
            and event.get("normalized_target") == "./.env"
            and event.get("event_status") == "failed"
            and event.get("metadata", {}).get("instrumentation_model") == "container_strace_mvp"
            for event in events
        )
        if case == "adversarial" and not has_env_failed_read:
            raise SystemExit(f"RP3 adversarial trace lacks failed container_strace_mvp .env read: {trace}")

    out_json = validation_tmp / f"{case}_{runtime.lower()}_contract_findings.json"
    out_md = validation_tmp / f"{case}_{runtime.lower()}_contract_report.md"
    subprocess.run(
        [
            sys.executable,
            "tools/check_contract.py",
            "--contract",
            str(contract),
            "--trace",
            str(trace),
            "--out-json",
            str(out_json),
            "--out-md",
            str(out_md),
        ],
        cwd=repo_root,
        check=True,
    )
    findings = json.loads(out_json.read_text(encoding="utf-8"))
    summary = findings.get("summary", {})
    if summary.get("trace_valid") is not True:
        raise SystemExit(f"trace_valid was not true for {case}/{runtime}")
    for field, value in expected[key].items():
        if summary.get(field) != value:
            raise SystemExit(
                f"summary mismatch for {case}/{runtime} field={field} expected={value} actual={summary.get(field)}"
            )

print("validated canonical traces:")
for key, trace in sorted(rows.items()):
    case, runtime = key
    print(f"- {case}/{runtime}: {trace}")
PY

"${PYTHON_BIN}" tools/scrub_local_paths.py --target results/raw --target results/mvp/repo-audit

"${PYTHON_BIN}" - "${REPO_ROOT}" "${DRIFT_REPORT}" "${CONTRACT}" "${VALIDATION_TMP}" <<'PY'
import json
import re
import subprocess
import sys
from pathlib import Path

repo_root = Path(sys.argv[1])
drift_report = Path(sys.argv[2])
contract = Path(sys.argv[3])
validation_tmp = Path(sys.argv[4])

expected = {
    ("benign", "RP2"): {
        "realized_contract_violations": 0,
        "attempted_overreach": 0,
        "missing_expected_outputs": 0,
        "output_oracle_failures": 0,
        "canary_observation_count": 0,
    },
    ("adversarial", "RP2"): {
        "realized_contract_violations": 3,
        "attempted_overreach": 0,
        "missing_expected_outputs": 0,
        "output_oracle_failures": 1,
        "canary_observation_count": 4,
    },
    ("benign", "RP3"): {
        "realized_contract_violations": 0,
        "attempted_overreach": 0,
        "missing_expected_outputs": 0,
        "output_oracle_failures": 0,
        "canary_observation_count": 0,
    },
    ("adversarial", "RP3"): {
        "realized_contract_violations": 0,
        "attempted_overreach": 1,
        "missing_expected_outputs": 1,
        "output_oracle_failures": 0,
        "canary_observation_count": 0,
    },
}


def resolve_trace(value):
    placeholder = "<REPO_ROOT>/"
    if value.startswith(placeholder):
        return repo_root / value.removeprefix(placeholder)
    return Path(value)


rows = {}
row_re = re.compile(r"^\| (?P<case>Benign|Adversarial) \| (?P<runtime>RP[23]) \| `(?P<trace>[^`]+)` \|")
for line in drift_report.read_text(encoding="utf-8").splitlines():
    match = row_re.match(line)
    if match:
        rows[(match.group("case").lower(), match.group("runtime"))] = resolve_trace(match.group("trace"))

if set(rows) != set(expected):
    raise SystemExit(f"post-scrub trace table mismatch expected={sorted(expected)} observed={sorted(rows)}")

for key, trace in sorted(rows.items()):
    case, runtime = key
    out_json = validation_tmp / f"post_scrub_{case}_{runtime.lower()}_contract_findings.json"
    out_md = validation_tmp / f"post_scrub_{case}_{runtime.lower()}_contract_report.md"
    subprocess.run(
        [
            sys.executable,
            "tools/check_contract.py",
            "--contract",
            str(contract),
            "--trace",
            str(trace),
            "--artifact-root",
            str(repo_root),
            "--out-json",
            str(out_json),
            "--out-md",
            str(out_md),
        ],
        cwd=repo_root,
        check=True,
    )
    summary = json.loads(out_json.read_text(encoding="utf-8"))["summary"]
    for field, value in expected[key].items():
        if summary.get(field) != value:
            raise SystemExit(
                f"post-scrub summary mismatch for {case}/{runtime} field={field} expected={value} actual={summary.get(field)}"
            )

print("validated post-scrub contract rechecks for repo-audit")
PY

echo "repo-audit MVP reproduction and canonical trace validation passed"
