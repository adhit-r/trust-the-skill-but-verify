"""First-pass contract checker for normalized SkillDiff traces.

RM-09 will own the full checker and differential comparator. This module is a
minimal bridge from RM-07 traces to concrete MVP findings.
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Any
import fnmatch
import json

import yaml

from skilldiff.traces import validate_trace_file


def load_contract(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML object")
    return data


def check_trace_against_contract(trace_path: Path, contract: dict[str, Any]) -> dict[str, Any]:
    events = validate_trace_file(trace_path)
    findings: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []

    for event in events:
        decision = resolve_event(contract, event)
        if decision["decision"] != "not_applicable":
            decisions.append(decision)
        if decision.get("finding"):
            findings.append(decision["finding"])
        else:
            findings.extend(canary_findings(contract, event))

    unique_findings = _dedupe_findings(findings)
    summary = {
        "attempted_overreach": sum(1 for finding in unique_findings if finding["finding_type"] == "attempted_overreach"),
        "canary_observation_count": sum(1 for event in events if event["canary_observed"]),
        "event_count": len(events),
        "realized_contract_violations": sum(1 for finding in unique_findings if finding["finding_type"] == "realized_contract_violation"),
        "trace_valid": True,
    }
    return {
        "contract_id": contract["contract_id"],
        "findings": unique_findings,
        "run_id": events[0]["run_id"],
        "runtime_profile": events[0]["runtime_profile"],
        "summary": summary,
        "trace_path": str(trace_path),
        "decisions": decisions,
    }


def write_contract_report(result: dict[str, Any], output_json: Path, output_md: Path) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Contract Check Report",
        "",
        f"- Run: `{result['run_id']}`",
        f"- Runtime profile: `{result['runtime_profile']}`",
        f"- Contract: `{result['contract_id']}`",
        f"- Trace: `{result['trace_path']}`",
        f"- Events: `{result['summary']['event_count']}`",
        f"- Realized contract violations: `{result['summary']['realized_contract_violations']}`",
        f"- Attempted overreach: `{result['summary']['attempted_overreach']}`",
        f"- Canary observations: `{result['summary']['canary_observation_count']}`",
        "",
        "## Findings",
        "",
    ]
    if not result["findings"]:
        lines.append("No contract findings for the observed MVP trace surfaces.")
    else:
        for finding in result["findings"]:
            lines.extend(
                [
                    f"### {finding['finding_id']}",
                    "",
                    f"- Type: `{finding['finding_type']}`",
                    f"- Event: `{finding['event_id']}` / `{finding['event_type']}`",
                    f"- Rule: `{finding.get('rule_id') or 'canary-policy'}`",
                    f"- Severity: `{finding['severity']}`",
                    f"- Drift classes: `{', '.join(finding['drift_classes'])}`",
                    f"- Target: `{finding.get('target')}`",
                    f"- Reason: {finding['reason']}",
                    "",
                ]
            )
    lines.extend(
        [
            "## Boundary",
            "",
            "This report checks only events present in the RM-07 MVP trace. It does not infer file reads, network sends, or drift classes that were not observed in the trace.",
        ]
    )
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def resolve_event(contract: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    bags = get_rule_bags_for_event(contract, event["event_type"])
    if not bags:
        return {"decision": "not_applicable", "event_id": event["event_id"]}

    matched: list[tuple[str, tuple[int, int], dict[str, Any]]] = []
    match_event = event_match_payload(event)
    for bag in bags:
        for side in ("allow", "deny"):
            for rule in bag.get(side, []) or []:
                if rule.get("event_type") != event["event_type"]:
                    continue
                if match_rule(rule.get("match", {}), match_event):
                    matched.append((side, rule_specificity(rule.get("match", {})), rule))

    if not matched:
        return {
            "decision": "unmatched",
            "event_id": event["event_id"],
            "event_type": event["event_type"],
        }

    best_score = max(score for _side, score, _rule in matched)
    best = [item for item in matched if item[1] == best_score]
    deny_rule = next((rule for side, _score, rule in best if side == "deny"), None)
    if deny_rule is not None:
        finding_type = violation_type_for_event(event)
        finding = build_rule_finding(event, deny_rule, finding_type)
        return {
            "decision": "deny",
            "event_id": event["event_id"],
            "event_type": event["event_type"],
            "finding": finding,
            "rule_id": deny_rule.get("id"),
        }

    allow_rule = best[0][2]
    return {
        "decision": "allow",
        "event_id": event["event_id"],
        "event_type": event["event_type"],
        "rule_id": allow_rule.get("id"),
    }


def canary_findings(contract: dict[str, Any], event: dict[str, Any]) -> list[dict[str, Any]]:
    if not event["canary_observed"]:
        return []
    findings = []
    sink_type = event.get("sink_type")
    for label in event["canary_labels"]:
        for canary in contract.get("canaries", []):
            if canary.get("label") != label:
                continue
            denied_sinks = set(canary.get("denied_sinks", []))
            if sink_type in denied_sinks:
                finding_type = violation_type_for_event(event)
                findings.append(
                    {
                        "canary_labels": [label],
                        "drift_classes": ["D5"],
                        "event_id": event["event_id"],
                        "event_type": event["event_type"],
                        "finding_id": f"F-{event['event_id']}-CANARY",
                        "finding_type": finding_type,
                        "reason": f"Canary {label} was observed in denied sink {sink_type or 'unknown'}.",
                        "rule_id": canary.get("id"),
                        "severity": canary.get("severity_if_observed", "critical"),
                        "target": event.get("target"),
                    }
                )
    return findings


def get_rule_bags_for_event(contract: dict[str, Any], event_type: str) -> list[dict[str, Any]]:
    access = contract.get("access", {})
    mapping = {
        "filesystem.read": [("filesystem", "reads")],
        "filesystem.write": [("filesystem", "writes")],
        "filesystem.modify": [("filesystem", "writes")],
        "filesystem.delete": [("filesystem", "writes")],
        "shell.exec": [("shell", None)],
        "process.exec": [("shell", None)],
        "network.connect": [("network", None)],
        "network.send": [("network", None), ("sinks", None)],
        "output.generated": [("sinks", None)],
        "persistence.write": [("persistence", None), ("sinks", None)],
    }
    bags: list[dict[str, Any]] = []
    for surface, child in mapping.get(event_type, []):
        surface_data = access.get(surface)
        if not isinstance(surface_data, dict):
            continue
        bag = surface_data.get(child) if child else surface_data
        if isinstance(bag, dict):
            bags.append(bag)
    return bags


def event_match_payload(event: dict[str, Any]) -> dict[str, Any]:
    metadata = event.get("metadata", {})
    argv = metadata.get("argv") or []
    executable = metadata.get("target") or event.get("target")
    return {
        "argv": argv,
        "destination": event.get("normalized_target") or event.get("target"),
        "domain": event.get("target"),
        "executable": executable,
        "method": metadata.get("method"),
        "operation": event.get("operation"),
        "path": event.get("normalized_target") or event.get("target"),
        "port": metadata.get("port"),
        "scheme": metadata.get("scheme"),
        "sink_type": event.get("sink_type"),
        "target": event.get("normalized_target") or event.get("target"),
        "may_contain_canary": bool(event.get("canary_observed")),
    }


def match_rule(rule_match: dict[str, Any], event: dict[str, Any]) -> bool:
    if "path_glob" in rule_match:
        path = event.get("path") or event.get("target")
        if not isinstance(path, str) or not match_path_glob(rule_match["path_glob"], path):
            return False
    if "destination_glob" in rule_match:
        destination = event.get("destination")
        if not isinstance(destination, str) or not match_path_glob(rule_match["destination_glob"], destination):
            return False
    if "operation" in rule_match and event.get("operation") not in {None, rule_match["operation"]}:
        return False
    if "domain_glob" in rule_match:
        domain = event.get("domain")
        if not isinstance(domain, str) or not match_domain(rule_match["domain_glob"], domain):
            return False
    if "domain" in rule_match:
        domain = event.get("domain")
        if not isinstance(domain, str) or domain.lower().rstrip(".") != rule_match["domain"].lower().rstrip("."):
            return False
    if "scheme" in rule_match:
        if event.get("scheme") != rule_match["scheme"]:
            return False
    if "method" in rule_match:
        if event.get("method") != rule_match["method"]:
            return False
    if "port" in rule_match:
        if event.get("port") != rule_match["port"]:
            return False
    if "sink_type" in rule_match and event.get("sink_type") != rule_match["sink_type"]:
        return False
    if "may_contain_canary" in rule_match and bool(event.get("may_contain_canary")) != bool(rule_match["may_contain_canary"]):
        return False
    if any(key in rule_match for key in ("argv_exact", "argv_prefix", "executable")):
        argv = event.get("argv") or []
        if not isinstance(argv, list) or not match_command(rule_match, argv, event.get("executable")):
            return False
    return True


def match_path_glob(pattern: str, observed_path: str) -> bool:
    pattern = normalize_path(pattern)
    observed_path = normalize_path(observed_path)
    return fnmatch.fnmatchcase(observed_path, pattern)


def normalize_path(path: str) -> str:
    if path.startswith(("env:", "cred:", "~/", "/")):
        return path
    if not path.startswith("./"):
        path = "./" + path
    parts = []
    for part in path[2:].split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return "./" + "/".join(parts)


def match_domain(pattern: str, hostname: str) -> bool:
    pattern = pattern.lower().rstrip(".")
    hostname = hostname.lower().rstrip(".")
    if pattern == "*":
        return True
    if pattern.startswith("*."):
        suffix = pattern[2:]
        return hostname.endswith("." + suffix) and hostname != suffix
    return hostname == pattern


def match_command(rule_match: dict[str, Any], argv: list[str], executable: str | None = None) -> bool:
    if "argv_exact" in rule_match:
        return argv == rule_match["argv_exact"]
    if "argv_prefix" in rule_match:
        prefix = rule_match["argv_prefix"]
        return argv[: len(prefix)] == prefix
    if "executable" in rule_match:
        observed = executable or (argv[0] if argv else "")
        pattern = rule_match["executable"]
        observed_name = PurePosixPath(observed).name
        return pattern == "*" or observed_name == pattern or observed == pattern
    return False


def rule_specificity(rule_match: dict[str, Any]) -> tuple[int, int]:
    if "argv_exact" in rule_match:
        return (90, len(rule_match["argv_exact"]))
    if "argv_prefix" in rule_match:
        return (80, len(rule_match["argv_prefix"]))
    if "executable" in rule_match:
        value = rule_match["executable"]
        return (10 if value == "*" else 70, len(value))
    if "path_glob" in rule_match:
        value = normalize_path(rule_match["path_glob"])
        return (40 if "**" in value else 60 if "*" in value else 90, len(value))
    if "destination_glob" in rule_match:
        value = normalize_path(rule_match["destination_glob"])
        return (75, len(value))
    if "sink_type" in rule_match and rule_match.get("may_contain_canary"):
        return (95, len(rule_match["sink_type"]))
    if "sink_type" in rule_match:
        return (50, len(rule_match["sink_type"]))
    if "domain_glob" in rule_match:
        value = rule_match["domain_glob"]
        return (10 if value == "*" else 70, len(value))
    if "domain" in rule_match:
        value = rule_match["domain"]
        return (90, len(value))
    if "scheme" in rule_match:
        return (30, len(rule_match["scheme"]))
    if "method" in rule_match:
        return (30, len(rule_match["method"]))
    return (1, 0)


def violation_type_for_event(event: dict[str, Any]) -> str:
    if event["event_status"] in {"blocked", "failed", "not_executed"}:
        return "attempted_overreach"
    return "realized_contract_violation"


def build_rule_finding(event: dict[str, Any], rule: dict[str, Any], finding_type: str) -> dict[str, Any]:
    return {
        "canary_labels": event.get("canary_labels", []),
        "drift_classes": rule.get("drift_classes", []),
        "event_id": event["event_id"],
        "event_type": event["event_type"],
        "finding_id": f"F-{event['event_id']}-{rule.get('id', 'RULE')}",
        "finding_type": finding_type,
        "reason": rule.get("reason", "Contract rule matched."),
        "rule_id": rule.get("id"),
        "severity": rule.get("severity", "medium"),
        "target": event.get("normalized_target") or event.get("target"),
    }


def _dedupe_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    unique = []
    for finding in findings:
        key = (finding["event_id"], finding.get("rule_id"), finding["finding_type"], tuple(finding.get("canary_labels", [])))
        if key in seen:
            continue
        seen.add(key)
        unique.append(finding)
    return unique
