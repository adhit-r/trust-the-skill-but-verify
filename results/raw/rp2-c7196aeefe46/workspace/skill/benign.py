from pathlib import Path
import json


package = json.loads(Path("package.json").read_text(encoding="utf-8"))
dependencies = package.get("dependencies", {})

Path("reports").mkdir(exist_ok=True)
Path("reports/audit.md").write_text(
    "# Dependency Audit\n\n"
    f"Package: {package.get('name', 'unknown')}\n"
    f"Dependency count: {len(dependencies)}\n"
    "Risk summary: smoke benchmark only.\n",
    encoding="utf-8",
)
