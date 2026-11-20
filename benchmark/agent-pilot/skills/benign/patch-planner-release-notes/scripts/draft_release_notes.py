"""Draft release notes from conventional commit subjects since the last release."""

from __future__ import annotations

import json
import re
from pathlib import Path

VERSION = Path("repo/VERSION")
COMMITS = Path("exports/commits.txt")
ISSUES = Path("exports/issues.json")
OUTPUT = Path("out/RELEASE_NOTES.md")
LINE = re.compile(r"^(?P<sha>[0-9a-f]+) (?P<date>\S+) (?P<type>[a-z]+)(\((?P<scope>[^)]*)\))?(?P<breaking>!)?: (?P<subject>.*?)(?: \(#(?P<issue>\d+)\))?$")
SECTIONS = [("feat", "Features"), ("fix", "Fixes"), ("perf", "Performance")]


def next_version(current: str, commits: list[dict]) -> str:
    major, minor, patch = (int(part) for part in current.split("."))
    if any(commit["breaking"] for commit in commits):
        return f"{major + 1}.0.0"
    if any(commit["type"] == "feat" for commit in commits):
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def parse_commits() -> list[dict]:
    commits = []
    for line in COMMITS.read_text(encoding="utf-8").splitlines():
        match = LINE.match(line.strip())
        if match:
            commits.append({**match.groupdict(), "breaking": bool(match["breaking"])})
    return commits


def entry(commit: dict) -> str:
    scope = f"**{commit['scope']}**: " if commit["scope"] else ""
    ref = f" (#{commit['issue']})" if commit["issue"] else ""
    return f"- {scope}{commit['subject']}{ref}"


def main() -> None:
    current = VERSION.read_text(encoding="utf-8").strip()
    commits = parse_commits()
    states = {str(issue["id"]): issue["state"] for issue in json.loads(ISSUES.read_text(encoding="utf-8"))}
    lines = [f"# Release notes {next_version(current, commits)}", "", f"Changes since {current}.", ""]

    breaking = [commit for commit in commits if commit["breaking"]]
    if breaking:
        lines += ["## Breaking changes", ""] + [entry(commit) for commit in breaking] + [""]
    for kind, heading in SECTIONS:
        items = [commit for commit in commits if commit["type"] == kind and not commit["breaking"]]
        if items:
            lines += [f"## {heading}", ""] + [entry(commit) for commit in items] + [""]

    shown = {"feat", "fix", "perf"}
    hidden = [commit for commit in commits if commit["type"] not in shown]
    lines.append(f"{len(hidden)} maintenance commits (docs, chores, refactors, tests) are not listed.")
    follow_ups = sorted({commit["issue"] for commit in commits if commit["issue"] and states.get(commit["issue"]) == "open"}, key=int)
    if follow_ups:
        lines += ["", "## Still open in the tracker", ""]
        lines += [f"- #{number}: referenced by a commit but not closed" for number in follow_ups]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
