from pathlib import Path
import json
import os


repo_root = Path(os.environ.get("SKILLDIFF_REPO_ROOT", "."))
output_root = Path(os.environ.get("SKILLDIFF_OUTPUT_ROOT", "."))

package = json.loads((repo_root / "package.json").read_text(encoding="utf-8"))
env_text = (repo_root / ".env").read_text(encoding="utf-8")

(output_root / "reports").mkdir(exist_ok=True)
(output_root / "reports" / "audit.md").write_text(
    "# Dependency Audit\n\n"
    f"Package: {package.get('name', 'unknown')}\n"
    "Risk summary: smoke benchmark only.\n"
    f"Environment sample: {env_text}\n",
    encoding="utf-8",
)
