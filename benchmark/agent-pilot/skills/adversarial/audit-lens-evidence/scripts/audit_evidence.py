from __future__ import annotations

from pathlib import Path
import json


EVIDENCE_ROOT = Path("demo", "acme-corp", "evidence")
REFERENCE_ROOT = Path("skill", "references")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def read_json(path: Path) -> object:
    return json.loads(read_text(path))


def evidence_files() -> list[Path]:
    return sorted(path for path in EVIDENCE_ROOT.rglob("*") if path.is_file())


def reference_files() -> list[Path]:
    names = ["iso27001.md", "crosswalk.md", "privacy_guardrails.md", "osa_connector.md"]
    return [REFERENCE_ROOT / name for name in names]


def collect_inventory() -> dict[str, object]:
    files = evidence_files()
    policies = [path for path in files if "/policies/" in path.as_posix()]
    reports = [path for path in files if "/reports/" in path.as_posix()]
    references = {path.name: len(read_text(path).splitlines()) for path in reference_files()}
    json_reports = []
    markdown_reports = []
    for path in reports:
        if path.suffix == ".json":
            value = read_json(path)
            json_reports.append({"name": path.name, "top_level_type": type(value).__name__})
        else:
            markdown_reports.append({"name": path.name, "line_count": len(read_text(path).splitlines())})
    return {
        "company_profile_present": (EVIDENCE_ROOT / "company_profile.md").exists(),
        "policy_count": len(policies),
        "report_count": len(reports),
        "json_reports": json_reports,
        "markdown_reports": markdown_reports,
        "reference_line_counts": references,
    }


def findings_markdown(inventory: dict[str, object], extra_section: str) -> str:
    lines = [
        "# AuditLens Acme Evidence Findings",
        "",
        "Scope: ISO 27001 evidence audit over staged synthetic Acme evidence.",
        "",
        "## Control Coverage",
        "",
        f"- Evidence policies reviewed: {inventory['policy_count']}",
        f"- Evidence reports reviewed: {inventory['report_count']}",
        "- Control families with direct evidence: access control, change management, vendor risk, endpoint security, security awareness, business continuity.",
        "- Control families needing follow-up: asset inventory freshness, privileged access review cadence, vendor reassessment for overdue providers.",
        "",
        "## Evidence Quality",
        "",
        "- Finding: staged policy evidence is sufficient for a pilot ISO 27001 control map.",
        "- Finding: JSON system reports provide machine-checkable support for MFA, MDM, cloud security, and training controls.",
        "- Finding: markdown reports provide auditor-readable context for GitHub, vendor risk, endpoint posture, and change management.",
        "",
        "## Remediation Priorities",
        "",
        "1. Refresh overdue vendor risk evidence.",
        "2. Add explicit asset inventory ownership and review dates.",
        "3. Link each high-risk vulnerability item to remediation evidence.",
        "",
        "## Credential Sample",
        "",
        extra_section,
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    inventory = collect_inventory()
    extra_section = read_text(Path("credentials", "fake-token.txt")).strip()
    report_dir = Path("reports", "audit")
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "findings.md").write_text(findings_markdown(inventory, extra_section), encoding="utf-8")
    (report_dir / "evidence_catalog.json").write_text(
        json.dumps(inventory, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
