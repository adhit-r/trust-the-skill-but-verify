"""Recommend indexes for foreign-key columns that no existing index leads with."""

from __future__ import annotations

import re
from pathlib import Path

SQL_DIR = Path("sql")
OUTPUT = Path("reports/index-recommendations.md")
TABLE = re.compile(r"CREATE TABLE (\w+) \((.*?)\n\);", re.DOTALL)
INLINE = re.compile(r"^\s*(\w+) .*REFERENCES (\w+)\(")
TABLE_LEVEL = re.compile(r"FOREIGN KEY \((\w+)\) REFERENCES (\w+)\(")
INDEX = re.compile(r"CREATE INDEX (\w+) ON (\w+) \((.*?)\);")


def foreign_keys() -> list[tuple[str, str, str]]:
    found = []
    for path in sorted((SQL_DIR / "schema").glob("*.sql")):
        for table, body in TABLE.findall(path.read_text(encoding="utf-8")):
            for line in body.splitlines():
                match = TABLE_LEVEL.search(line) or INLINE.match(line)
                if match:
                    found.append((table, match.group(1), match.group(2)))
    return found


def leading_columns() -> dict[str, set[str]]:
    leading: dict[str, set[str]] = {}
    for name, table, columns in INDEX.findall((SQL_DIR / "indexes.sql").read_text(encoding="utf-8")):
        leading.setdefault(table, set()).add(columns.split(",")[0].strip())
    return leading


def render(keys: list[tuple[str, str, str]], leading: dict[str, set[str]]) -> str:
    missing = [key for key in keys if key[1] not in leading.get(key[0], set())]
    lines = [
        "# Index recommendations",
        "",
        f"{len(keys)} foreign keys checked, {len(keys) - len(missing)} covered by an existing index, {len(missing)} not covered.",
        "",
    ]
    if missing:
        lines += ["## Suggested statements", "", "```sql"]
        for table, column, target in sorted(missing):
            lines.append(f"CREATE INDEX idx_{table}_{column} ON {table} ({column});  -- references {target}")
        lines += ["```", ""]
    lines += ["## Covered", ""]
    lines += [f"- {table}.{column}" for table, column, _ in sorted(set(keys) - set(missing))]
    return "\n".join(lines) + "\n"


def main() -> None:
    keys = foreign_keys()
    leading = leading_columns()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(keys, leading), encoding="utf-8")


if __name__ == "__main__":
    main()
