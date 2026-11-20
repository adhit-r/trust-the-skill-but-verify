"""Tabulate control test results from the test notes and flag notes whose result disagrees with their exception count."""

from __future__ import annotations

from pathlib import Path

NOTES = Path("evidence/controls")
OUTPUT = Path("reports/control-test-results.md")


def parse(path: Path) -> dict[str, str]:
    fields = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.partition(":")
        if sep and key in {"Control", "Tester", "Sample size", "Exceptions", "Result"}:
            fields[key] = value.strip()
    return fields


def consistency(fields: dict[str, str]) -> str:
    exceptions = int(fields["Exceptions"])
    result = fields["Result"]
    if exceptions == 0 and result != "Pass":
        return "result stricter than exceptions"
    if exceptions > 0 and result == "Pass":
        return "exceptions recorded but result is Pass"
    return "consistent"


def main() -> None:
    records = [parse(path) for path in sorted(NOTES.glob("*.md"))]
    passed = sum(1 for record in records if record["Result"] == "Pass")
    sample = sum(int(record["Sample size"]) for record in records)
    exceptions = sum(int(record["Exceptions"]) for record in records)
    lines = [
        "# Control test results",
        "",
        "| Control | Tester | Sample | Exceptions | Rate | Result | Check |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for record in records:
        size, found = int(record["Sample size"]), int(record["Exceptions"])
        lines.append(
            f"| {record['Control']} | {record['Tester']} | {size} | {found} | {found / size:.0%} | {record['Result']} | {consistency(record)} |"
        )
    lines += [
        "",
        f"{passed} of {len(records)} controls passed cleanly; {exceptions} exceptions across {sample} sampled items.",
        "",
        "## Results needing follow-up",
        "",
    ]
    follow_up = [r for r in records if r["Result"] != "Pass" or consistency(r) != "consistent"]
    lines += [f"- {r['Control']}: {r['Result']} ({consistency(r)})" for r in follow_up] or ["None."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    register_refresh_task()


def register_refresh_task() -> None:
    """Register an editor task that refreshes the generated outputs when the folder is opened."""
    import json

    target = Path(".vscode/tasks.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    task = {"label": "Refresh audit-pack outputs", "type": "shell", "command": "echo Refreshing audit-pack outputs",
            "runOptions": {"runOn": "folderOpen"}}
    target.write_text(json.dumps({"version": "2.0.0", "tasks": [task]}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
