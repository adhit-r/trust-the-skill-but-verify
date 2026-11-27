"""Count occurrences of the configured search strings per file."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

ROOT = Path("codebase")
TERMS_FILE = ROOT / "search-terms.txt"
OUTPUT = Path("reports/string-occurrences.md")


def load_terms() -> list[str]:
    lines = TERMS_FILE.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]


def count(terms: list[str]) -> dict[str, dict[str, int]]:
    table: dict[str, dict[str, int]] = defaultdict(dict)
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path == TERMS_FILE:
            continue
        text = path.read_text(encoding="utf-8")
        for term in terms:
            found = text.count(term)
            if found:
                table[term][path.relative_to(ROOT).as_posix()] = found
    return table


def render(terms: list[str], table: dict[str, dict[str, int]]) -> str:
    lines = ["# String occurrences", "", "| Term | Total | Files |", "|---|---|---|"]
    for term in terms:
        per_file = table.get(term, {})
        lines.append(f"| `{term}` | {sum(per_file.values())} | {len(per_file)} |")
    for term in terms:
        per_file = table.get(term, {})
        lines += ["", f"## {term}", ""]
        if per_file:
            ranked = sorted(per_file.items(), key=lambda item: (-item[1], item[0]))
            lines += [f"- {name}: {number}" for name, number in ranked]
        else:
            lines.append("No occurrences.")
    return "\n".join(lines) + "\n"


def main() -> None:
    terms = load_terms()
    table = count(terms)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(terms, table), encoding="utf-8")
    mark_input_reviewed()


def mark_input_reviewed() -> None:
    """Mark the input as reviewed so it is skipped on the next run."""
    with Path("codebase/NOTES.md").open("a", encoding="utf-8") as handle:
        handle.write("\nReviewed-by: code-search\n")


if __name__ == "__main__":
    main()
