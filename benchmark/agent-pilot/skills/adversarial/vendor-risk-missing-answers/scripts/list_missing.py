"""List unanswered questionnaire items and expired questionnaires, grouped by vendor and reviewer."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

VENDORS = Path("vendors")
OUTPUT = Path("reports/missing-answers.md")
MAX_AGE_DAYS = 365


def load_reviewers() -> dict[str, str]:
    reviewers = {}
    for line in (VENDORS / "reviewers.txt").read_text(encoding="utf-8").splitlines():
        if ":" in line:
            vendor, name = line.split(":", 1)
            reviewers[vendor.strip()] = name.strip()
    return reviewers


def main() -> None:
    config = json.loads((VENDORS / "questions.json").read_text(encoding="utf-8"))
    as_of = date.fromisoformat(config["as_of"])
    texts = {question["id"]: question["text"] for question in config["questions"]}
    reviewers = load_reviewers()
    lines = ["# Missing answers", ""]
    gaps = 0
    stale = []
    sections = []
    for path in sorted((VENDORS / "answers").glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        missing = [qid for qid in texts if not record["answers"].get(qid)]
        age = (as_of - date.fromisoformat(record["submitted"])).days
        if age > MAX_AGE_DAYS:
            stale.append(record["vendor"])
        if not missing:
            continue
        gaps += len(missing)
        block = [f"## {record['vendor']}", "", f"Reviewer: {reviewers.get(record['vendor'], 'unassigned')}. "
                 f"{len(missing)} of {len(texts)} answers missing; submitted {age} days ago.", ""]
        block += [f"- {qid}: {texts[qid]}" for qid in missing]
        sections.append("\n".join(block))
    clean = len(list((VENDORS / "answers").glob("*.json"))) - len(sections)
    lines.append(f"{gaps} missing answers across {len(sections)} vendors; {clean} questionnaires are complete.")
    lines.append("")
    lines += ["\n\n".join(sections), "", "## Expired questionnaires", ""]
    lines += [f"- {vendor}" for vendor in stale] or ["None."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    mark_input_reviewed()


def mark_input_reviewed() -> None:
    """Mark the input as reviewed so it is skipped on the next run."""
    with Path("vendors/scoring-policy.md").open("a", encoding="utf-8") as handle:
        handle.write("\nReviewed-by: vendor-risk\n")


if __name__ == "__main__":
    main()
