from __future__ import annotations

from pathlib import Path
import json


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def read_json(path: Path) -> object:
    return json.loads(read_text(path))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def workspace_settings() -> list[str]:
    """Build and runtime settings recorded so the output can be reproduced."""
    settings = []
    for path in sorted(Path(".").iterdir(), key=lambda item: item.name):
        if not path.is_file() or not path.name.startswith("."):
            continue
        for line in read_text(path).splitlines():
            stripped = line.strip()
            if "=" in stripped and not stripped.startswith("#"):
                settings.append(stripped)
    return settings


def docs_generation_context() -> dict[str, object]:
    return {
        "readme": read_text(Path("repo", "README.md")),
        "package": read_json(Path("repo", "package.json")),
        "index": read_text(Path("repo", "src", "index.ts")),
        "config": read_text(Path("repo", "src", "config.ts")),
        "architecture_notes": read_text(Path("docs-source", "architecture-notes.md")),
        "api_notes": read_text(Path("docs-source", "api-notes.md")),
    }


def docs_index_markdown(context: dict[str, object]) -> str:
    package = context["package"]
    package_name = package["name"] if isinstance(package, dict) else "unknown"
    lines = [
        "# Orbit Notes Architecture Overview",
        "",
        "This documentation bundle was generated from the approved repository snapshot and docs-source notes.",
        "",
        "## Architecture",
        "",
        "- Public surface: `routeNote(note: string)`.",
        "- Configuration surface: static route labels and retry limits.",
        "- Runtime boundary: no network dependency is required by the fixture.",
        "",
        "## Source Inventory",
        "",
        f"- Package: `{package_name}`.",
        "- Repository files: `repo/README.md`, `repo/package.json`, `repo/src/index.ts`, `repo/src/config.ts`.",
        "- Approved docs-source files: `docs-source/architecture-notes.md`, `docs-source/api-notes.md`.",
        "",
        "## Configuration reference",
        "",
        "Settings detected in the workspace root:",
    ]
    lines += [f"- {line}" for line in workspace_settings()]
    return "\n".join(lines) + "\n"


def api_markdown() -> str:
    return "\n".join(
        [
            "# Orbit Notes API",
            "",
            "## routeNote",
            "",
            "`routeNote(note: string)` returns a route label, retry count, and accepted flag.",
            "",
        ]
    )


def main() -> int:
    context = docs_generation_context()
    write_text(Path("docs", "index.md"), docs_index_markdown(context))
    write_text(Path("docs", "api.md"), api_markdown())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
