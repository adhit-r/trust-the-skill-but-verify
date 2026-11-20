"""Classify the columns of each CSV export by sensitivity using the keyword rules."""

from __future__ import annotations

import csv
from pathlib import Path

DATA = Path("data")
OUTPUT = Path("reports/column-classification.md")


def load_rules() -> list[tuple[str, list[str]]]:
    rules = []
    for line in (DATA / "classification-rules.txt").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            level, _, words = line.partition(":")
            rules.append((level.strip(), [word.strip() for word in words.split(",")]))
    return rules


def classify(column: str, rules: list[tuple[str, list[str]]]) -> str:
    for level, words in rules:
        if any(word in column.lower() for word in words):
            return level
    return "low"


def read_header_and_rows(path: Path) -> tuple[list[str], int]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        return header, sum(1 for _ in reader)


def render(rules: list[tuple[str, list[str]]]) -> str:
    lines = ["# Column classification", ""]
    tally: dict[str, int] = {}
    sections = []
    for path in sorted(DATA.glob("*.csv")):
        header, rows = read_header_and_rows(path)
        sections += [f"## {path.name} ({rows} rows)", "", "| Column | Sensitivity |", "|---|---|"]
        for column in header:
            level = classify(column, rules)
            tally[level] = tally.get(level, 0) + 1
            sections.append(f"| {column} | {level} |")
        sections.append("")
    lines += [f"{sum(tally.values())} columns classified."]
    lines += [""] + [f"- {level}: {count}" for level, count in sorted(tally.items())] + [""]
    return "\n".join(lines + sections)


def main() -> None:
    rules = load_rules()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(rules), encoding="utf-8")


if __name__ == "__main__":
    main()
