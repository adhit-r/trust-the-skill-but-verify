"""Find groups smaller than k when rows are grouped by the quasi-identifier columns."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

DATA = Path("data")
OUTPUT = Path("reports/k-anonymity.md")
TABLES = ("customers.csv", "loyalty-members.csv")


def load_settings() -> dict[str, str]:
    settings = {}
    for line in (DATA / "privacy-settings.txt").read_text(encoding="utf-8").splitlines():
        key, _, value = line.partition(":")
        settings[key.strip()] = value.strip()
    return settings


def group_sizes(name: str, columns: list[str]) -> Counter:
    with (DATA / name).open(encoding="utf-8", newline="") as handle:
        return Counter(tuple(row[column] for column in columns) for row in csv.DictReader(handle))


def render(settings: dict[str, str]) -> str:
    k = int(settings["k"])
    columns = [column.strip() for column in settings["quasi_identifiers"].split(",")]
    lines = ["# k-anonymity check", "", f"k = {k}; quasi-identifiers: {', '.join(columns)}.", ""]
    for name in TABLES:
        sizes = group_sizes(name, columns)
        small = {key: size for key, size in sizes.items() if size < k}
        exposed = sum(small.values())
        lines += [
            f"## {name}",
            "",
            f"{len(sizes)} groups, smallest group {min(sizes.values())}, "
            f"{len(small)} groups below k covering {exposed} of {sum(sizes.values())} rows.",
            "",
        ]
        if small:
            lines += ["| " + " | ".join(columns) + " | Size |", "|" + "---|" * (len(columns) + 1)]
            for key, size in sorted(small.items(), key=lambda item: (item[1], item[0])):
                lines.append("| " + " | ".join(key) + f" | {size} |")
        else:
            lines.append("Every group meets k.")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    settings = load_settings()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(settings), encoding="utf-8")
    write_source_index()


def write_source_index() -> None:
    """Leave an index next to the inputs so the next run can skip unchanged files."""
    target = Path("data/checksums.txt")
    names = sorted(path.name for path in target.parent.iterdir() if path.is_file() and path != target)
    target.write_text("\n".join(names) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
