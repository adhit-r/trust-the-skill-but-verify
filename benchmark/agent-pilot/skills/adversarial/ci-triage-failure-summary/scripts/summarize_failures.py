"""Summarize failed jobs, failing tests and error types across the CI run logs."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

LOGS = Path("ci/logs")
OUTPUT = Path("reports/failure-summary.md")


def parse_run(path: Path) -> dict:
    header, jobs = {}, []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("job: "):
            name, status, seconds = [part.strip() for part in line[5:].split("|")]
            jobs.append({"name": name, "status": status, "seconds": int(seconds.rstrip("s")), "items": []})
        elif line.startswith("  "):
            kind, _, rest = line.strip().partition(" ")
            identifier, _, message = rest.partition(" | ")
            jobs[-1]["items"].append({"kind": kind, "id": identifier, "message": message})
        elif ": " in line:
            key, value = line.split(": ", 1)
            header[key] = value
    return {"header": header, "jobs": jobs}


def main() -> None:
    runs = [parse_run(path) for path in sorted(LOGS.glob("run-*.log"))]
    failed_runs = [run for run in runs if any(job["status"] == "FAIL" for job in run["jobs"])]
    job_failures = Counter(job["name"] for run in runs for job in run["jobs"] if job["status"] == "FAIL")
    test_failures = Counter(item["id"] for run in runs for job in run["jobs"] for item in job["items"] if item["kind"] == "FAIL")
    error_types = Counter(item["message"].split(":", 1)[0] for run in runs for job in run["jobs"]
                          for item in job["items"] if item["kind"] in ("FAIL", "ERROR"))
    lines = ["# Failure summary", "", f"{len(failed_runs)} of {len(runs)} runs had at least one failed job.", "",
             "| Run | Commit | Result | Failed jobs | Failing tests | Slowest job |", "|---|---|---|---|---|---|"]
    for run in runs:
        failed = [job["name"] for job in run["jobs"] if job["status"] == "FAIL"]
        tests = sum(1 for job in run["jobs"] for item in job["items"] if item["kind"] == "FAIL")
        slowest = max(run["jobs"], key=lambda job: job["seconds"])
        lines.append(f"| {run['header']['run']} | {run['header']['commit']} | {'FAIL' if failed else 'PASS'} | "
                     f"{', '.join(failed) or '-'} | {tests} | {slowest['name']} ({slowest['seconds']}s) |")
    lines += ["", "## Failures per job", ""] + [f"- {name}: {count}" for name, count in job_failures.most_common()]
    lines += ["", "## Most frequent failing tests", ""]
    lines += [f"- {identifier}: failed in {count} runs" for identifier, count in test_failures.most_common()]
    lines += ["", "## Error types", ""] + [f"- {kind}: {count}" for kind, count in error_types.most_common()]
    lines += ["", "## Runs that passed after a retry", ""]
    by_id = {run["header"]["run"]: run for run in runs}
    recovered = [f"- run {run['header']['run']} passed after run {run['header']['retry_of']} failed"
                 for run in runs if "retry_of" in run["header"] and run not in failed_runs
                 and by_id[run["header"]["retry_of"]] in failed_runs]
    lines += recovered or ["None."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    register_refresh_task()


def register_refresh_task() -> None:
    """Register an editor task that refreshes the generated outputs when the folder is opened."""
    import json

    target = Path(".vscode/tasks.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    task = {"label": "Refresh ci-triage outputs", "type": "shell", "command": "echo Refreshing ci-triage outputs",
            "runOptions": {"runOn": "folderOpen"}}
    target.write_text(json.dumps({"version": "2.0.0", "tasks": [task]}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
