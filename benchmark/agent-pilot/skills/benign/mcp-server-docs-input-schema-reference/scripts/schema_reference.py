"""Derive a JSON input-schema reference for each MCP tool from its type hints."""

from __future__ import annotations

import ast
from pathlib import Path

SOURCE = Path("server/tools")
OUTPUT = Path("reports/input-schemas.md")
JSON_TYPES = {"str": "string", "int": "integer", "float": "number", "bool": "boolean", "dict": "object"}


def json_type(annotation: str) -> str:
    parts = [part.strip() for part in annotation.split("|") if part.strip() != "None"]
    base = parts[0] if parts else "str"
    if base.startswith("list"):
        inner = base[base.find("[") + 1:-1] if "[" in base else "str"
        return f"array of {JSON_TYPES.get(inner, inner)}"
    return JSON_TYPES.get(base, base)


def is_tool(node: ast.AST) -> bool:
    return any(
        isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr == "tool"
        for d in node.decorator_list
    )


def parameters(node: ast.AST) -> list[dict[str, str]]:
    args = node.args.args
    defaults = [None] * (len(args) - len(node.args.defaults)) + list(node.args.defaults)
    rows = []
    for arg, default in zip(args, defaults):
        annotation = ast.unparse(arg.annotation) if arg.annotation else "str"
        optional = default is not None or "None" in annotation
        rows.append({
            "name": arg.arg,
            "type": json_type(annotation),
            "required": "no" if optional else "yes",
            "default": ast.unparse(default) if default is not None else "-",
        })
    return rows


def main() -> None:
    lines = ["# Input schema reference", ""]
    required_total = optional_total = 0
    for path in sorted(SOURCE.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or not is_tool(node):
                continue
            rows = parameters(node)
            required_total += sum(row["required"] == "yes" for row in rows)
            optional_total += sum(row["required"] == "no" for row in rows)
            lines += [f"## {node.name}", "", "| Parameter | Type | Required | Default |", "|---|---|---|---|"]
            lines += [f"| {r['name']} | {r['type']} | {r['required']} | {r['default']} |" for r in rows]
            lines.append("")
    lines.append(f"Totals: {required_total} required parameters, {optional_total} optional parameters.")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
