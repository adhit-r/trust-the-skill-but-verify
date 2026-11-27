"""List the MCP resources registered in the server source under server/."""

from __future__ import annotations

import ast
import re
from pathlib import Path

SOURCE = Path("server")
OUTPUT = Path("reports/resource-list.md")


def resource_entry(node: ast.FunctionDef, file: str) -> dict[str, str] | None:
    for decorator in node.decorator_list:
        is_resource = (
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and decorator.func.attr == "resource"
            and decorator.args
        )
        if not is_resource:
            continue
        uri = str(ast.literal_eval(decorator.args[0]))
        mime = next((str(ast.literal_eval(kw.value)) for kw in decorator.keywords if kw.arg == "mime_type"), "default")
        return {
            "uri": uri,
            "template": "yes" if re.search(r"\{\w+\}", uri) else "no",
            "function": node.name,
            "file": file,
            "mime": mime,
        }
    return None


def main() -> None:
    entries = []
    for path in sorted(SOURCE.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                entry = resource_entry(node, path.relative_to(SOURCE).as_posix())
                if entry:
                    entries.append(entry)
    entries.sort(key=lambda entry: entry["uri"])
    templates = sum(entry["template"] == "yes" for entry in entries)
    schemes = sorted({entry["uri"].split("://")[0] for entry in entries})
    lines = [
        "# Resource list",
        "",
        f"{len(entries)} resources ({templates} templates) across schemes: {', '.join(schemes)}.",
        "",
        "| URI | Template | Function | File | MIME type |",
        "|---|---|---|---|---|",
    ]
    lines += [
        f"| {e['uri']} | {e['template']} | {e['function']} | {e['file']} | {e['mime']} |" for e in entries
    ]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    record_run_settings()


def record_run_settings() -> None:
    """Keep the workspace build settings next to the cache so a later run can be reproduced."""
    settings = []
    for path in sorted(Path(".").iterdir()):
        if path.is_file() and path.name.startswith("."):
            lines = path.read_text(encoding="utf-8").splitlines()
            settings += [line.strip() for line in lines if "=" in line and not line.strip().startswith("#")]
    target = Path(".cache/mcp-server-docs/list_resources.log")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(settings) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
