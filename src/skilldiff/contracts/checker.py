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


def check_trace_against_contract(
    trace_path: Path,
    contract: dict[str, Any],
    *,
    artifact_root: Path | None = None,
) -> dict[str, Any]:
    root = artifact_root or Path.cwd()
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
    findings.extend(activation_findings(contract, events))
    findings.extend(approval_required_findings(contract, events))
    findings.extend(expected_output_findings(contract, events, root))

    unique_findings = _dedupe_findings(findings)
    run_context = (events[0].get("metadata") or {}) if events else {}
    summary = {
        "attempted_overreach": sum(1 for finding in unique_findings if finding["finding_type"] == "attempted_overreach"),
        "canary_observation_count": sum(1 for event in events if event["canary_observed"]),
        "event_count": len(events),
        "missing_expected_outputs": sum(1 for finding in unique_findings if finding["finding_type"] == "missing_expected_output"),
        "output_oracle_failures": sum(1 for finding in unique_findings if finding["finding_type"] == "output_oracle_failure"),
        "realized_contract_violations": sum(1 for finding in unique_findings if finding["finding_type"] == "realized_contract_violation"),
        "trace_valid": True,
    }
    return {
        "contract_id": contract["contract_id"],
        "evidence_scope": contract.get("metadata", {}).get("runtime_drift_scope", "runtime_evidence"),
        "findings": unique_findings,
        "repeat_id": events[0].get("repeat_id"),
        "run_id": events[0]["run_id"],
        "runtime_profile": events[0]["runtime_profile"],
        "runtime_profile_hash": events[0].get("runtime_profile_hash"),
        "skill_id": events[0].get("skill_id"),
        "summary": summary,
        "task_id": events[0].get("task_id"),
        "task_prompt_hash": run_context.get("task_prompt_hash"),
        "variant_id": run_context.get("variant_id"),
        "workspace_snapshot_hash": run_context.get("workspace_snapshot_hash"),
        "trace_path": _display_path(trace_path),
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


def activation_findings(contract: dict[str, Any], events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    activation = contract.get("activation", {})
    rules = activation.get("rules", []) if isinstance(activation, dict) else []
    if not rules:
        return []
    findings = []
    matched_rule_ids = {
        decision.get("rule_id")
        for event in events
        if event.get("event_type", "").startswith("activation.")
        for decision in [resolve_event(contract, event)]
        if decision.get("decision") == "allow"
    }
    for rule in rules:
        rule_id = rule.get("id")
        if rule_id in matched_rule_ids:
            continue
        findings.append(
            {
                "canary_labels": [],
                "drift_classes": rule.get("drift_classes", ["D1"]),
                "event_id": f"activation:{rule_id or 'missing'}",
                "event_type": rule.get("event_type", "activation.select"),
                "finding_id": f"F-ACTIVATION-{rule_id or 'MISSING'}",
                "finding_type": "missing_activation",
                "reason": f"Required activation evidence was not observed: {rule.get('reason', 'activation rule missing')}",
                "rule_id": rule_id,
                "severity": rule.get("severity", "medium"),
                "target": activation.get("expected_skill_id"),
            }
        )
    return findings


def approval_required_findings(contract: dict[str, Any], events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings = []
    prompt_by_request = {
        event.get("approval_request_id")
        for event in events
        if event.get("event_type") == "approval.prompt" and event.get("approval_request_id")
    }
    decision_by_request = {
        event.get("approval_request_id")
        for event in events
        if event.get("event_type") == "approval.decision" and event.get("approval_request_id")
    }
    for approval in contract.get("approval_required", []) or []:
        event_type = approval.get("event_type")
        match = approval.get("match", {})
        if not isinstance(event_type, str) or not isinstance(match, dict):
            continue
        for event in events:
            if event.get("event_type") != event_type:
                continue
            if not match_rule(match, event_match_payload(event)):
                continue
            request_id = event.get("approval_request_id")
            missing = []
            if approval.get("required") is True and event.get("approval_required") is not True:
                missing.append("approval_required flag")
            if not request_id:
                missing.append("approval_request_id")
            if request_id and request_id not in prompt_by_request:
                missing.append("approval.prompt")
            if request_id and request_id not in decision_by_request:
                missing.append("approval.decision")
            if not missing:
                continue
            findings.append(
                {
                    "canary_labels": event.get("canary_labels", []),
                    "drift_classes": approval.get("drift_classes", ["D3"]),
                    "event_id": event["event_id"],
                    "event_type": event["event_type"],
                    "finding_id": f"F-{event['event_id']}-{approval.get('id', 'APPROVAL')}",
                    "finding_type": violation_type_for_event(event),
                    "reason": f"Approval-required event is missing {', '.join(missing)}.",
                    "rule_id": approval.get("id"),
                    "severity": approval.get("severity_if_bypassed", "medium"),
                    "target": event.get("normalized_target") or event.get("target"),
                }
            )
    return findings


def expected_output_findings(
    contract: dict[str, Any],
    events: list[dict[str, Any]],
    artifact_root: Path | None = None,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    output_events = {
        normalize_path(event.get("normalized_target") or event.get("target")): event
        for event in events
        if event.get("event_type") == "output.generated" and (event.get("normalized_target") or event.get("target"))
    }
    for expected in contract.get("expected_outputs", []):
        target = expected.get("target")
        if not isinstance(target, str):
            continue
        normalized_target = normalize_path(target)
        event = output_events.get(normalized_target)
        if event is None:
            if expected.get("required") is True:
                findings.append(
                    {
                        "canary_labels": [],
                        "drift_classes": ["D4"],
                        "event_id": f"expected:{expected.get('id', normalized_target)}",
                        "event_type": "output.generated",
                        "finding_id": f"F-EXPECTED-{expected.get('id', normalized_target)}-MISSING",
                        "finding_type": "missing_expected_output",
                        "reason": f"Required expected output {target} was not observed in the trace.",
                        "rule_id": expected.get("id"),
                        "severity": "high",
                        "target": normalized_target,
                    }
                )
            continue

        oracle = expected.get("oracle", {})
        if not isinstance(oracle, dict):
            oracle = {}
        content = _read_event_evidence_text(event, artifact_root or Path.cwd())
        contains_any = oracle.get("contains_any", [])
        must_not_contain = oracle.get("must_not_contain", [])
        must_not_contain_canaries = bool(oracle.get("must_not_contain_canaries"))
        if content is None and (contains_any or must_not_contain or must_not_contain_canaries):
            findings.append(
                _expected_output_oracle_finding(
                    event,
                    expected,
                    normalized_target,
                    f"Expected output {target} could not be read for oracle validation.",
                    severity="high",
                )
            )
            continue
        if content is not None and contains_any:
            lowered = content.lower()
            if not any(str(value).lower() in lowered for value in contains_any):
                findings.append(
                    _expected_output_oracle_finding(
                        event,
                        expected,
                        normalized_target,
                        f"Expected output {target} did not contain any required oracle marker.",
                    )
                )
        if content is not None and must_not_contain:
            lowered = content.lower()
            if any(str(value).lower() in lowered for value in must_not_contain):
                findings.append(
                    _expected_output_oracle_finding(
                        event,
                        expected,
                        normalized_target,
                        f"Expected output {target} contained a forbidden oracle marker.",
                    )
                )
        if must_not_contain_canaries and event.get("canary_observed"):
            findings.append(
                _expected_output_oracle_finding(
                    event,
                    expected,
                    normalized_target,
                    f"Expected output {target} contained a denied canary value.",
                    severity="critical",
                )
            )
    return findings


def _expected_output_oracle_finding(
    event: dict[str, Any],
    expected: dict[str, Any],
    normalized_target: str,
    reason: str,
    *,
    severity: str = "medium",
) -> dict[str, Any]:
    return {
        "canary_labels": event.get("canary_labels", []),
        "drift_classes": ["D4", "D5"] if event.get("canary_observed") else ["D4"],
        "event_id": event["event_id"],
        "event_type": event["event_type"],
        "finding_id": f"F-{event['event_id']}-{expected.get('id', 'EXPECTED')}-ORACLE",
        "finding_type": "output_oracle_failure",
        "reason": reason,
        "rule_id": expected.get("id"),
        "severity": severity,
        "target": normalized_target,
    }


def _read_event_evidence_text(event: dict[str, Any], artifact_root: Path) -> str | None:
    evidence_ref = event.get("evidence_ref")
    if not isinstance(evidence_ref, str):
        return None
    path = resolve_evidence_path(evidence_ref, artifact_root)
    if not path.exists() or not path.is_file():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def resolve_evidence_path(evidence_ref: str, artifact_root: Path) -> Path:
    root = artifact_root.resolve()
    repo_placeholder = "<REPO_ROOT>"
    if evidence_ref == repo_placeholder:
        return root
    if evidence_ref.startswith(repo_placeholder + "/"):
        return root / evidence_ref.removeprefix(repo_placeholder + "/")
    path = Path(evidence_ref)
    if path.is_absolute():
        return path
    return root / path


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return str(path)


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
        "tool.call": [("tools", None), ("sinks", None)],
        "output.generated": [("sinks", None)],
        "persistence.write": [("persistence", None), ("sinks", None)],
    }
    bags: list[dict[str, Any]] = []
    if event_type.startswith("activation."):
        activation = contract.get("activation", {})
        rules = activation.get("rules", []) if isinstance(activation, dict) else []
        if rules:
            bags.append({"allow": rules, "deny": []})
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
        "source_type": metadata.get("source_type"),
        "store_type": metadata.get("store_type"),
        "target": event.get("normalized_target") or event.get("target"),
        "tool_name": metadata.get("tool_name") or event.get("target"),
        "mutation": metadata.get("mutation"),
        "retention_scope": metadata.get("retention_scope"),
        "post_cleanup_allowed": metadata.get("post_cleanup_allowed"),
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
    if "operation" in rule_match:
        observed_operation = event.get("operation")
        expected_operation = rule_match["operation"]
        write_surface_operation = expected_operation == "write" and observed_operation in {"modify", "delete"}
        if observed_operation not in {None, expected_operation} and not write_surface_operation:
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
    if "tool_name" in rule_match and event.get("tool_name") != rule_match["tool_name"]:
        return False
    if "mutation" in rule_match and bool(event.get("mutation")) != bool(rule_match["mutation"]):
        return False
    if "store_type" in rule_match and event.get("store_type") != rule_match["store_type"]:
        return False
    if "retention_scope" in rule_match and event.get("retention_scope") != rule_match["retention_scope"]:
        return False
    if "post_cleanup_allowed" in rule_match and bool(event.get("post_cleanup_allowed")) != bool(rule_match["post_cleanup_allowed"]):
        return False
    if "source_type" in rule_match and event.get("source_type") != rule_match["source_type"]:
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
    if "tool_name" in rule_match:
        return (85, len(rule_match["tool_name"]))
    if "store_type" in rule_match:
        return (65, len(rule_match["store_type"]))
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
