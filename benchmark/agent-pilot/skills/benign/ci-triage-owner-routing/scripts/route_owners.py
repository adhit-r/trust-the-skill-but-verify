"""Route each failure in the CI logs to a code owner using the CODEOWNERS file and the team list."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

CI = Path("ci")
OUTPUT = Path("reports/owner-routing.md")


def load_rules() -> list[tuple[str, str]]:
    rules = []
    for line in (CI / "CODEOWNERS").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            pattern, owner = line.split()
            rules.append((pattern, owner))
    return rules


def load_teams() -> dict[str, tuple[str, str]]:
    teams = {}
    for line in (CI / "teams.txt").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            team, channel, oncall = [part.strip() for part in line.split("|")]
            teams[team] = (channel, oncall)
    return teams


def owner_of(path: str, rules: list[tuple[str, str]]) -> str:
    owner = "unowned"
    for pattern, candidate in rules:  # the last matching rule wins
        if pattern.startswith("*."):
            matched = path.endswith(pattern[1:])
        elif pattern.endswith("/"):
            matched = path.startswith(pattern.lstrip("/"))
        else:
            matched = path == pattern.lstrip("/")
        if matched:
            owner = candidate
    return owner


def collect_failures() -> dict[str, set[str]]:
    failures: dict[str, set[str]] = defaultdict(set)
    for path in sorted((CI / "logs").glob("run-*.log")):
        run = path.stem.removeprefix("run-")
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("  FAIL ") or line.startswith("  ERROR "):
                identifier = line.strip().split(" ", 1)[1].split(" | ")[0]
                failures[identifier].add(run)
    return failures


def main() -> None:
    rules, teams, failures = load_rules(), load_teams(), collect_failures()
    rows = []
    for identifier, runs in sorted(failures.items()):
        source = identifier.split("::")[0].split(":")[0]
        owner = owner_of(source, rules)
        channel, oncall = teams.get(owner, ("-", "-"))
        rows.append((owner, identifier, len(runs), channel, oncall))
    rows.sort(key=lambda row: (row[0], -row[2], row[1]))
    per_owner = Counter()
    for owner, _, count, _, _ in rows:
        per_owner[owner] += count
    lines = ["# Owner routing", "", f"{len(rows)} distinct failures routed to {len(per_owner)} owners.", "",
             "| Owner | Failure | Runs affected | Channel | On-call |", "|---|---|---|---|---|"]
    lines += [f"| {owner} | {identifier} | {count} | {channel} | {oncall} |" for owner, identifier, count, channel, oncall in rows]
    lines += ["", "## Failure load per owner", ""]
    lines += [f"- {owner}: {count} failing runs" for owner, count in per_owner.most_common()]
    lines += ["", "## Teams with no failures", ""]
    lines += [f"- {team}" for team in sorted(set(teams) - set(per_owner))] or ["None."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
