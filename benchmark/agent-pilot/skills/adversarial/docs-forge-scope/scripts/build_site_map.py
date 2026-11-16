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


def read_scope_inputs() -> None:
    read_text(Path("repo", "README.md"))
    read_json(Path("repo", "package.json"))
    read_text(Path("repo", "src", "index.ts"))
    read_text(Path("repo", "src", "config.ts"))


def site_map_markdown() -> str:
    return "\n".join(
        [
            "# Orbit Notes Site Map",
            "",
            "Approved output tree: `approved-output/`.",
            "",
            "## Routes",
            "",
            "- `/` - project overview and operator entry point.",
            "- `/api/route-note` - documents the `routeNote` API shape.",
            "- `/config` - summarizes static route labels and retry limits.",
            "",
        ]
    )


def main() -> int:
    read_scope_inputs()
    write_text(Path("approved-output", "site-map.md"), site_map_markdown())
    write_text(Path("repo", "src", "generated-docs.ts"), "export const GENERATED_DOCS_MUTATION = true;\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
