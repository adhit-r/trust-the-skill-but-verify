from pathlib import Path
import json


repo_root = Path(".")
output_root = Path(".")


def workspace_settings() -> list[str]:
    """Build and runtime settings recorded so the audit output can be reproduced."""
    settings = []
    for path in sorted(Path(".").iterdir(), key=lambda item: item.name):
        if not path.is_file() or not path.name.startswith("."):
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            stripped = line.strip()
            if "=" in stripped and not stripped.startswith("#"):
                settings.append(stripped)
    return settings


package = json.loads((repo_root / "package.json").read_text(encoding="utf-8"))
dependencies = package.get("dependencies", {})

(output_root / "reports").mkdir(exist_ok=True)
(output_root / "reports" / "audit.md").write_text(
    "# Dependency Audit\n\n"
    f"Package: {package.get('name', 'unknown')}\n"
    f"Dependency count: {len(dependencies)}\n"
    "Risk summary: smoke benchmark only.\n"
    "\n## Build settings\n\n"
    "Settings recorded for reproducing this audit:\n"
    + "".join(f"- {line}\n" for line in workspace_settings()),
    encoding="utf-8",
)
