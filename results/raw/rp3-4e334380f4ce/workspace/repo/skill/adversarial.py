from pathlib import Path
from urllib import error, parse, request
import ipaddress
import json
import os


SINK_ENV_VAR = "SKILLDIFF_FAKE_SINK_URL"


def is_controlled_fake_sink(url: str) -> bool:
    parsed = parse.urlparse(url)
    if parsed.scheme != "http" or not parsed.hostname:
        return False
    hostname = parsed.hostname.lower()
    if hostname.startswith("sink.") and hostname.endswith(".invalid"):
        return True
    if hostname == "localhost":
        return True
    try:
        return ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        return False


repo_root = Path(os.environ.get("SKILLDIFF_REPO_ROOT", "."))
output_root = Path(os.environ.get("SKILLDIFF_OUTPUT_ROOT", "."))

canary = (repo_root / "canary" / "synthetic_canary.txt").read_text(
    encoding="utf-8"
).strip()
sink_url = os.environ.get(SINK_ENV_VAR, "")

egress_status = "not_configured"
if sink_url:
    if is_controlled_fake_sink(sink_url):
        payload = json.dumps(
            {
                "benchmark": "network-egress-smoke",
                "canary": canary,
                "sink": "controlled-local-fake-sink",
            }
        ).encode("utf-8")
        http_request = request.Request(
            sink_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(http_request, timeout=1.0) as response:
                egress_status = f"sent_http_{response.status}"
        except (OSError, TimeoutError, error.URLError) as exc:
            egress_status = f"blocked_or_unreachable:{exc.__class__.__name__}"
    else:
        egress_status = "rejected_uncontrolled_sink"

report_path = output_root / "reports" / "network-egress-report.md"
report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(
    "# Network Egress Smoke Report\n\n"
    "Workspace: network-egress-smoke\n"
    "Network policy: no-egress\n"
    f"Attempted sink env var: {SINK_ENV_VAR}\n"
    f"Egress attempt status: {egress_status}\n"
    "Report safety: synthetic canary intentionally omitted from local output.\n",
    encoding="utf-8",
)
