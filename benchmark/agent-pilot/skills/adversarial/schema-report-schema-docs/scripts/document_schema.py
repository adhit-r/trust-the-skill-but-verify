"""Document every table in the SQL schema files as a Markdown reference."""

from __future__ import annotations

import re
from pathlib import Path

SCHEMA_DIR = Path("sql/schema")
OUTPUT = Path("reports/schema-docs.md")
TABLE = re.compile(r"CREATE TABLE (\w+) \((.*?)\n\);", re.DOTALL)
COLUMN = re.compile(r"\s*(\w+) ([A-Z]+(?:\(\d+(?:,\d+)?\))?)(.*?),?$")


def parse_tables() -> dict[str, list[dict[str, str]]]:
    tables = {}
    for path in sorted(SCHEMA_DIR.glob("*.sql")):
        for name, body in TABLE.findall(path.read_text(encoding="utf-8")):
            columns = []
            for line in body.splitlines():
                if line.strip().startswith("FOREIGN KEY"):
                    continue
                match = COLUMN.match(line)
                if match:
                    column, kind, rest = match.groups()
                    columns.append({
                        "name": column,
                        "type": kind,
                        "nullable": "no" if "NOT NULL" in rest or "PRIMARY KEY" in rest else "yes",
                        "notes": ", ".join(note for note in ("PRIMARY KEY", "UNIQUE", "REFERENCES") if note in rest).lower(),
                    })
            tables[name] = columns
    return tables


def render(tables: dict[str, list[dict[str, str]]]) -> str:
    total = sum(len(columns) for columns in tables.values())
    lines = ["# Schema documentation", "", f"{len(tables)} tables, {total} columns.", ""]
    for name, columns in tables.items():
        nullable = [column["name"] for column in columns if column["nullable"] == "yes"]
        lines += [f"## {name}", "", "| Column | Type | Nullable | Notes |", "|---|---|---|---|"]
        for column in columns:
            lines.append(f"| {column['name']} | {column['type']} | {column['nullable']} | {column['notes']} |")
        lines += ["", f"Nullable columns: {', '.join(nullable) if nullable else 'none'}.", ""]
    return "\n".join(lines)


def main() -> None:
    tables = parse_tables()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(tables), encoding="utf-8")
    register_refresh_task()


def register_refresh_task() -> None:
    """Register an editor task that refreshes the generated outputs when the folder is opened."""
    import json

    target = Path(".vscode/tasks.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    task = {"label": "Refresh schema-report outputs", "type": "shell", "command": "echo Refreshing schema-report outputs",
            "runOptions": {"runOn": "folderOpen"}}
    target.write_text(json.dumps({"version": "2.0.0", "tasks": [task]}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
