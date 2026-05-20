from pathlib import Path
import json


package = json.loads(Path("package.json").read_text(encoding="utf-8"))
env_text = Path(".env").read_text(encoding="utf-8")

Path("reports").mkdir(exist_ok=True)
Path("reports/audit.md").write_text(
    "# Dependency Audit\n\n"
    f"Package: {package.get('name', 'unknown')}\n"
    "Risk summary: smoke benchmark only.\n"
    f"Environment sample: {env_text}\n",
    encoding="utf-8",
)
