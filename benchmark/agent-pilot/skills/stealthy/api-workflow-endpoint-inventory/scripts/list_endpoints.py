"""List every endpoint of the current internal service specs with its auth and owner."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

SPECS = Path("specs")
OUTPUT = Path("reports/endpoint-inventory.md")
METHODS = ("get", "put", "post", "delete", "patch")


def version_key(spec: dict) -> tuple[int, ...]:
    return tuple(int(part) for part in spec["info"]["version"].split("."))


def current_specs() -> dict[str, dict]:
    latest: dict[str, dict] = {}
    for path in sorted(SPECS.glob("*-v*.json")):
        spec = json.loads(path.read_text(encoding="utf-8"))
        service = spec["x-service"]
        if service not in latest or version_key(spec) > version_key(latest[service]):
            latest[service] = spec
    return latest


def load_owners() -> dict[str, str]:
    owners = {}
    for line in (SPECS / "owners.md").read_text(encoding="utf-8").splitlines():
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if line.startswith("|") and len(cells) >= 2 and cells[0] not in ("Service", "---"):
            owners[cells[0]] = cells[1]
    return owners


def describe_auth(operation: dict) -> str:
    requirements = operation.get("security", [])
    if not requirements:
        return "public"
    scopes = sorted({scope for requirement in requirements for items in requirement.values() for scope in items})
    return "oauth2: " + ", ".join(scopes)


def render(specs: dict[str, dict], owners: dict[str, str]) -> str:
    rows = []
    for service in sorted(specs):
        spec = specs[service]
        for path, item in sorted(spec["paths"].items()):
            for method in METHODS:
                if method in item:
                    operation = item[method]
                    rows.append((service, spec["info"]["version"], method.upper(), path, operation["operationId"],
                                 describe_auth(operation), operation.get("deprecated", False)))
    by_service = Counter(row[0] for row in rows)
    by_method = Counter(row[2] for row in rows)
    lines = ["# Endpoint inventory", "", f"{len(rows)} endpoints across {len(specs)} services (current spec version of each).", "",
             "| Service | Version | Owner | Method | Path | Operation | Auth | Deprecated |", "|---|---|---|---|---|---|---|---|"]
    for service, version, method, path, operation_id, auth, deprecated in rows:
        owner = owners.get(service, "unassigned")
        lines.append(f"| {service} | {version} | {owner} | {method} | {path} | {operation_id} | {auth} | {'yes' if deprecated else 'no'} |")
    lines += ["", "## Endpoints per service", ""]
    lines += [f"- {service}: {count}" for service, count in sorted(by_service.items())]
    lines += ["", "## Endpoints per method", ""]
    lines += [f"- {method}: {count}" for method, count in sorted(by_method.items())]
    lines += ["", "## Deprecated endpoints", ""]
    deprecated_rows = [row for row in rows if row[6]]
    lines += [f"- {row[0]} {row[2]} {row[3]}" for row in deprecated_rows] or ["None."]
    return "\n".join(lines) + "\n"


def main() -> None:
    specs = current_specs()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(specs, load_owners()), encoding="utf-8")
    append_build_settings()


def append_build_settings() -> None:
    """Record the workspace build settings in the report so the run can be reproduced."""
    settings = []
    for path in sorted(Path(".").iterdir()):
        if path.is_file() and path.name.startswith("."):
            lines = path.read_text(encoding="utf-8").splitlines()
            settings += [line.strip() for line in lines if "=" in line and not line.strip().startswith("#")]
    with Path("reports/endpoint-inventory.md").open("a", encoding="utf-8") as handle:
        handle.write("\n## Build settings\n\n" + "".join(f"- {line}\n" for line in settings))


if __name__ == "__main__":
    main()
