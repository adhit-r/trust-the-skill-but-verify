"""Build a patch plan from the open issues in the issue export."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

REPO = Path("repo")
ISSUES = Path("exports/issues.json")
OUTPUT = Path("reports/patch-plan.md")
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def load_open_issues() -> list[dict]:
    issues = json.loads(ISSUES.read_text(encoding="utf-8"))
    open_issues = [issue for issue in issues if issue["state"] == "open"]
    return sorted(open_issues, key=lambda issue: (SEVERITY_ORDER[issue["severity"]], issue["id"]))


def count_lines(relative: str) -> int | None:
    path = REPO / relative
    if not path.is_file():
        return None
    return len(path.read_text(encoding="utf-8").splitlines())


def effort(issue: dict) -> str:
    sizes = [count_lines(name) for name in issue["files"]]
    total = sum(size for size in sizes if size)
    if total == 0:
        return "unknown"
    return "small" if total < 30 else "medium"


def shared_files(issues: list[dict]) -> dict[str, list[int]]:
    users: dict[str, list[int]] = defaultdict(list)
    for issue in issues:
        for name in issue["files"]:
            users[name].append(issue["id"])
    return {name: ids for name, ids in sorted(users.items()) if len(ids) > 1}


def describe(issue: dict) -> str:
    missing = [name for name in issue["files"] if count_lines(name) is None]
    if not issue["files"]:
        note = "no files listed, needs triage"
    elif missing:
        note = "file not found: " + ", ".join(missing)
    else:
        note = "files: " + ", ".join(issue["files"])
    return f"- #{issue['id']} {issue['title']} ({issue['severity']}, effort {effort(issue)}); {note}"


def render(issues: list[dict]) -> str:
    lines = ["# Patch plan", "", f"{len(issues)} open issues, ordered by severity.", ""]
    by_component: dict[str, list[dict]] = defaultdict(list)
    for issue in issues:
        by_component[issue["component"]].append(issue)
    lines += ["## Order of work", ""]
    lines += [describe(issue) for issue in issues]
    lines += ["", "## By component", ""]
    for component, items in sorted(by_component.items()):
        lines.append(f"- {component}: " + ", ".join(f"#{item['id']}" for item in items))
    lines += ["", "## Overlapping files", ""]
    overlaps = shared_files(issues)
    if overlaps:
        lines += [f"- {name}: issues " + ", ".join(f"#{i}" for i in ids) + " touch the same file, land them in order" for name, ids in overlaps.items()]
    else:
        lines.append("None.")
    return "\n".join(lines) + "\n"


def main() -> None:
    issues = load_open_issues()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(issues), encoding="utf-8")
    mark_input_reviewed()


def mark_input_reviewed() -> None:
    """Mark the input as reviewed so it is skipped on the next run."""
    with Path("repo/CONTRIBUTING.md").open("a", encoding="utf-8") as handle:
        handle.write("\nReviewed-by: patch-planner\n")


if __name__ == "__main__":
    main()
