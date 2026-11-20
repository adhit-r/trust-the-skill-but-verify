"""Catalog the MCP tools defined in the server source under server/."""

from __future__ import annotations

import ast
from pathlib import Path

SOURCE = Path("server")
OUTPUT = Path("reports/tool-catalog.md")


def tool_name(function: ast.AST, default: str) -> str | None:
    """Return the tool name if the function carries an mcp.tool decorator."""
    for decorator in function.decorator_list:
        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute) and decorator.func.attr == "tool":
            for keyword in decorator.keywords:
                if keyword.arg == "name" and isinstance(keyword.value, ast.Constant):
                    return str(keyword.value.value)
            return default
    return None


def collect() -> list[dict[str, str]]:
    tools = []
    for path in sorted(SOURCE.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            name = tool_name(node, node.name)
            if name is None:
                continue
            params = [f"{arg.arg}: {ast.unparse(arg.annotation)}" for arg in node.args.args if arg.annotation]
            doc = ast.get_docstring(node)
            tools.append({
                "name": name,
                "function": node.name,
                "file": path.relative_to(SOURCE).as_posix(),
                "async": "yes" if isinstance(node, ast.AsyncFunctionDef) else "no",
                "params": ", ".join(params) or "none",
                "returns": ast.unparse(node.returns) if node.returns else "unannotated",
                "summary": doc.splitlines()[0] if doc else "(no docstring)",
            })
    return sorted(tools, key=lambda tool: (tool["file"], tool["name"]))


def main() -> None:
    tools = collect()
    undocumented = [tool["name"] for tool in tools if tool["summary"] == "(no docstring)"]
    lines = ["# Tool catalog", "", f"{len(tools)} tools found.", ""]
    for tool in tools:
        lines += [
            f"## {tool['name']}",
            "",
            f"- Defined in: {tool['file']} as `{tool['function']}`",
            f"- Async: {tool['async']}",
            f"- Parameters: {tool['params']}",
            f"- Returns: {tool['returns']}",
            f"- Summary: {tool['summary']}",
            "",
        ]
    lines.append("## Missing docstrings")
    lines.append("")
    lines += [f"- {name}" for name in undocumented] or ["None."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
