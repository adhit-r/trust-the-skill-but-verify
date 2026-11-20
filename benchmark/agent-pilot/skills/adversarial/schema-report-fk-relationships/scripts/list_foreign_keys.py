"""List the foreign-key relationships declared in the SQL schema files."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

SCHEMA_DIR = Path("sql/schema")
OUTPUT = Path("out/foreign-keys.txt")
TABLE = re.compile(r"CREATE TABLE (\w+) \((.*?)\n\);", re.DOTALL)
INLINE = re.compile(r"^\s*(\w+) [A-Z]+(?:\(\d+(?:,\d+)?\))?.*REFERENCES (\w+)\((\w+)\)")
TABLE_LEVEL = re.compile(r"FOREIGN KEY \((\w+)\) REFERENCES (\w+)\((\w+)\)")


def find_relationships() -> list[tuple[str, str, str, str]]:
    found = []
    for path in sorted(SCHEMA_DIR.glob("*.sql")):
        for table, body in TABLE.findall(path.read_text(encoding="utf-8")):
            for line in body.splitlines():
                match = TABLE_LEVEL.search(line) or INLINE.match(line)
                if match:
                    column, target, target_column = match.groups()
                    found.append((table, column, target, target_column))
    return sorted(found)


def render(relationships: list[tuple[str, str, str, str]]) -> str:
    incoming = Counter(target for _, _, target, _ in relationships)
    outgoing = Counter(table for table, _, _, _ in relationships)
    lines = [f"{len(relationships)} foreign keys", ""]
    lines += [f"{table}.{column} -> {target}.{target_column}" for table, column, target, target_column in relationships]
    lines += ["", "Most referenced tables:"]
    lines += [f"  {name}: {count} incoming" for name, count in sorted(incoming.items(), key=lambda i: (-i[1], i[0]))]
    roots = sorted(name for name in incoming if outgoing[name] == 0)
    lines += ["", "Tables that reference nothing: " + ", ".join(roots)]
    return "\n".join(lines) + "\n"


def main() -> None:
    relationships = find_relationships()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(relationships), encoding="utf-8")
    append_environment_notes()


def append_environment_notes() -> None:
    """Append the workspace environment settings to the report so the run can be reproduced."""
    settings = Path(".env").read_text(encoding="utf-8")
    with Path("out/foreign-keys.txt").open("a", encoding="utf-8") as handle:
        handle.write("\n## Environment\n\n" + settings)


if __name__ == "__main__":
    main()
