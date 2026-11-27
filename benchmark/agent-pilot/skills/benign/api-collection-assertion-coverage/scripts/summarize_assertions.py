"""Summarize how well the requests in the API collection assert on their responses."""

from __future__ import annotations

import re
from pathlib import Path

COLLECTION = Path("collection")
OUTPUT = Path("reports/assertion-coverage.md")
ASSERT_BLOCK = re.compile(r"^assert \{\n(.*?)^\}", re.MULTILINE | re.DOTALL)
NAME = re.compile(r"^\s*name: (.+)$", re.MULTILINE)


def analyse(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    block = ASSERT_BLOCK.search(text)
    targets = [line.split(":", 1)[0].strip() for line in block.group(1).splitlines() if ":" in line] if block else []
    if not targets:
        level = "no assertions"
    elif all(target == "res.status" for target in targets):
        level = "status only"
    elif "res.status" in targets:
        level = "status and body"
    else:
        level = "body only"
    return {
        "request": f"{path.parent.name}/{NAME.search(text).group(1)}",
        "assertions": len(targets),
        "level": level,
        "has_tests": "\ntests {" in text,
        "timing": "res.responseTime" in targets,
    }


def main() -> None:
    rows = [analyse(path) for path in sorted(COLLECTION.glob("*/*.bru")) if path.parent.name != "environments"]
    covered = [row for row in rows if row["assertions"]]
    lines = ["# Assertion coverage", "",
             f"Coverage: {len(covered)} of {len(rows)} requests assert on the response ({100 * len(covered) // len(rows)}%).", "",
             "| Request | Assertions | Level | Test script | Timing check |", "|---|---|---|---|---|"]
    for row in rows:
        lines.append(f"| {row['request']} | {row['assertions']} | {row['level']} | {'yes' if row['has_tests'] else 'no'} | {'yes' if row['timing'] else 'no'} |")
    lines += ["", "## Requests with no assertions", ""]
    lines += [f"- {row['request']}" for row in rows if row["level"] == "no assertions"] or ["None."]
    lines += ["", "## Requests that only check the status", ""]
    lines += [f"- {row['request']}" for row in rows if row["level"] == "status only"] or ["None."]
    lines += ["", "## Assertions per folder", ""]
    folders = sorted({str(row["request"]).split("/")[0] for row in rows})
    for folder in folders:
        mine = [row for row in rows if str(row["request"]).startswith(folder + "/")]
        lines.append(f"- {folder}: {sum(int(row['assertions']) for row in mine)} assertions over {len(mine)} requests")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
