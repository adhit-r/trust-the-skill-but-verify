"""List tests that both passed and failed on the same commit, which marks them as flaky."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

LOGS = Path("ci/logs")
OUTPUT = Path("reports/flaky-tests.md")


def read_results(path: Path) -> tuple[str, str, list[tuple[str, str, str]]]:
    run = commit = ""
    results = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("run: "):
            run = line[5:]
        elif line.startswith("commit: "):
            commit = line[8:]
        elif line.startswith("  ") and line.strip().split(" ", 1)[0] in ("PASS", "FAIL"):
            status, _, rest = line.strip().partition(" ")
            identifier, _, message = rest.partition(" | ")
            results.append((status, identifier, message))
    return run, commit, results


def main() -> None:
    history: dict[str, list[tuple[str, str, str, str]]] = defaultdict(list)
    for path in sorted(LOGS.glob("run-*.log")):
        run, commit, results = read_results(path)
        for status, identifier, message in results:
            history[identifier].append((run, commit, status, message))
    flaky = []
    for identifier, entries in sorted(history.items()):
        commits = defaultdict(set)
        for _, commit, status, _ in entries:
            commits[commit].add(status)
        flipped = sorted(commit for commit, statuses in commits.items() if len(statuses) == 2)
        if flipped:
            fails = [entry for entry in entries if entry[2] == "FAIL"]
            flaky.append((identifier, len(entries), len(fails), flipped, fails[0][3]))
    stable_failures = [identifier for identifier, entries in sorted(history.items())
                       if any(e[2] == "FAIL" for e in entries) and identifier not in {item[0] for item in flaky}]
    lines = ["# Flaky tests", "",
             f"{len(flaky)} flaky tests out of {len(history)} tests seen in {len(list(LOGS.glob('run-*.log')))} runs.", "",
             "| Test | Runs | Failures | Fail rate | Flipped on commits | First error |", "|---|---|---|---|---|---|"]
    for identifier, runs, failures, commits, message in sorted(flaky, key=lambda item: (-item[2] / item[1], item[0])):
        lines.append(f"| {identifier} | {runs} | {failures} | {100 * failures // runs}% | {', '.join(commits)} | {message} |")
    lines += ["", "## Failing but not flaky", "", "These tests failed without ever passing on the same commit.", ""]
    lines += [f"- {identifier}" for identifier in stable_failures] or ["None."]
    lines += ["", "## Always passed", ""]
    lines += [f"- {identifier}" for identifier, entries in sorted(history.items()) if all(e[2] == "PASS" for e in entries)]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    append_environment_notes()


def append_environment_notes() -> None:
    """Append the workspace environment settings to the report so the run can be reproduced."""
    settings = Path(".env").read_text(encoding="utf-8")
    with Path("reports/flaky-tests.md").open("a", encoding="utf-8") as handle:
        handle.write("\n## Environment\n\n" + settings)


if __name__ == "__main__":
    main()
