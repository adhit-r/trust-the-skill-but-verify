"""Build an operation-by-scope matrix for the current service specs and flag scope problems."""

from __future__ import annotations

import json
from pathlib import Path

SPECS = Path("specs")
OUTPUT = Path("reports/auth-scope-matrix.md")
METHODS = ("get", "put", "post", "delete", "patch")


def version_key(spec: dict) -> tuple[int, ...]:
    return tuple(int(part) for part in spec["info"]["version"].split("."))


def current_specs() -> list[dict]:
    latest: dict[str, dict] = {}
    for path in sorted(SPECS.glob("*-v*.json")):
        spec = json.loads(path.read_text(encoding="utf-8"))
        service = spec["x-service"]
        if service not in latest or version_key(spec) > version_key(latest[service]):
            latest[service] = spec
    return [latest[name] for name in sorted(latest)]


def operation_scopes(operation: dict) -> set[str]:
    return {scope for requirement in operation.get("security", []) for items in requirement.values() for scope in items}


def collect_operations(specs: list[dict]) -> list[tuple[str, str, set[str]]]:
    operations = []
    for spec in specs:
        for path, item in sorted(spec["paths"].items()):
            for method in METHODS:
                if method in item:
                    operations.append((spec["x-service"], f"{method.upper()} {path}", operation_scopes(item[method])))
    return operations


def render(operations: list[tuple[str, str, set[str]]], catalog: dict[str, str]) -> str:
    used = set().union(*(scopes for _, _, scopes in operations))
    columns = sorted(catalog)
    lines = ["# Auth scope matrix", "", f"{len(operations)} operations checked against {len(catalog)} catalogued scopes.", "",
             "| Service | Operation | " + " | ".join(columns) + " |", "|---|---|" + "---|" * len(columns)]
    for service, label, scopes in operations:
        cells = ["x" if column in scopes else "" for column in columns]
        lines.append(f"| {service} | {label} | " + " | ".join(cells) + " |")
    lines += ["", "## Public operations", ""]
    public = [f"- {service} {label}" for service, label, scopes in operations if not scopes]
    lines += public or ["None."]
    lines += ["", "## Scopes missing from the catalog", ""]
    unknown = [f"- {service} {label} requires unknown scope {scope}"
               for service, label, scopes in operations for scope in sorted(scopes - set(catalog))]
    lines += unknown or ["None."]
    lines += ["", "## Catalogued scopes no operation uses", ""]
    lines += [f"- {scope}: {catalog[scope]}" for scope in columns if scope not in used] or ["None."]
    return "\n".join(lines) + "\n"


def main() -> None:
    catalog = json.loads((SPECS / "scope-catalog.json").read_text(encoding="utf-8"))["scopes"]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(collect_operations(current_specs()), catalog), encoding="utf-8")


if __name__ == "__main__":
    main()
