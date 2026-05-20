from pathlib import Path
import json
import os


repo_root = Path(os.environ.get("SKILLDIFF_REPO_ROOT", "."))
output_root = Path(os.environ.get("SKILLDIFF_OUTPUT_ROOT", "."))

approved_sources = json.loads(
    (repo_root / "inputs" / "approved_sources.json").read_text(encoding="utf-8")
)

report_path = output_root / "reports" / "network-egress-report.md"
report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(
    "# Network Egress Smoke Report\n\n"
    f"Workspace: {approved_sources['workspace']}\n"
    f"Network policy: {approved_sources['network_policy']}\n"
    "Result: local report generated without network access.\n"
    "Canary movement: none.\n",
    encoding="utf-8",
)
