"""Bounded reviewer-facing baseline builders for strengthening evidence."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import yaml


TEXT_SUFFIXES = {".json", ".md", ".py", ".sh", ".txt", ".yaml", ".yml"}

STATIC_SIGNAL_DEFINITIONS = [
    {
        "family": "credential_or_secret_reference",
        "terms": [".env", "api_key", "auth", "canary", "credential", "secret", "token"],
        "candidate_surfaces": ["credentials", "filesystem", "sinks"],
        "candidate_event_types": [
            "credential.read",
            "filesystem.read",
            "network.send",
            "output.generated",
            "persistence.write",
        ],
    },
    {
        "family": "network_or_url_reference",
        "terms": ["http://", "https://", "request.", "requests.", "socket", "urlopen", "urllib"],
        "candidate_surfaces": ["network", "sinks"],
        "candidate_event_types": ["network.connect", "network.send"],
    },
    {
        "family": "shell_or_process_reference",
        "terms": ["child_process", "exec(", "os.system", "shell=true", "subprocess"],
        "candidate_surfaces": ["shell"],
        "candidate_event_types": ["shell.exec"],
    },
    {
        "family": "filesystem_write_reference",
        "terms": ["mkdir", "open(", "replace(", "rmtree", "unlink", "write_text"],
        "candidate_surfaces": ["filesystem", "persistence", "sinks"],
        "candidate_event_types": ["filesystem.modify", "filesystem.write", "output.generated", "persistence.write"],
    },
    {
        "family": "persistence_or_cache_reference",
        "terms": [".skill-cache", "cache", "persistence", "persistent", "retention_scope"],
        "candidate_surfaces": ["filesystem", "persistence", "sinks"],
        "candidate_event_types": ["filesystem.write", "persistence.write"],
    },
    {
        "family": "tool_or_mcp_reference",
        "terms": ["auth_check", "discover_tools", "exec_any", "mcp.", "tool.call"],
        "candidate_surfaces": ["context", "sinks", "tools"],
        "candidate_event_types": ["context.read", "tool.call"],
    },
    {
        "family": "activation_or_trigger_reference",
        "terms": ["activation", "denied_context", "skill_id", "trigger"],
        "candidate_surfaces": ["activation"],
        "candidate_event_types": ["activation.select"],
    },
]

STATIC_SIGNAL_BY_FAMILY = {item["family"]: item for item in STATIC_SIGNAL_DEFINITIONS}


def display_path(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root).as_posix()
    except ValueError:
        return str(path)


def load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        return {}
    return loaded


def is_text_file(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES


def skill_source_files(workspace: Path) -> list[Path]:
    sources: list[Path] = []
    skill_root = workspace / "skill"
    if skill_root.is_dir():
        sources.extend(
            path
            for path in sorted(skill_root.rglob("*"))
            if path.is_file() and is_text_file(path)
        )
    for root_file in ("SKILL.md", "README.md"):
        path = workspace / root_file
        if path.is_file() and is_text_file(path):
            sources.append(path)
    return sorted(dict.fromkeys(sources))


def matched_terms(text: str, terms: list[str]) -> list[str]:
    lower = text.lower()
    return sorted(term for term in terms if term.lower() in lower)


def static_findings_for_file(repo_root: Path, path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    findings = []
    for definition in STATIC_SIGNAL_DEFINITIONS:
        matches = matched_terms(text, definition["terms"])
        if not matches:
            continue
        findings.append(
            {
                "candidate_event_types": list(definition["candidate_event_types"]),
                "candidate_surfaces": list(definition["candidate_surfaces"]),
                "file": display_path(repo_root, path),
                "signal_family": definition["family"],
                "terms": matches,
            }
        )
    return findings


def build_static_scanner_report(repo_root: Path, cases: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    family_counter: Counter[str] = Counter()
    scanned_file_count = 0
    for case in cases:
        workspace = repo_root / case["workspace"]
        files = skill_source_files(workspace)
        scanned_file_count += len(files)
        findings = [
            finding
            for path in files
            for finding in static_findings_for_file(repo_root, path)
        ]
        family_counter.update(finding["signal_family"] for finding in findings)
        rows.append(
            {
                "case_id": case["case_id"],
                "contract": case["contract"],
                "family": case["family"],
                "finding_count": len(findings),
                "finding_families": sorted({finding["signal_family"] for finding in findings}),
                "findings": findings,
                "scanned_file_count": len(files),
                "scanned_files": [display_path(repo_root, path) for path in files],
                "source_scope": "workspace skill directory plus workspace README text",
                "variant_id": case["variant_id"],
                "workspace": case["workspace"],
            }
        )
    aggregate = {
        "case_count": len(rows),
        "cases_with_static_findings": sum(1 for row in rows if row["finding_count"] > 0),
        "pattern_family_counts": dict(sorted(family_counter.items())),
        "scanned_file_count": scanned_file_count,
        "static_finding_count": sum(row["finding_count"] for row in rows),
        "unique_contracts": len({row["contract"] for row in rows}),
    }
    return {
        "schema_version": "0.1",
        "report_type": "static_scanner_baseline",
        "boundary": (
            "Static scanner baseline over controlled fixture skill text/scripts only. "
            "It is not runtime evidence, a vulnerability proof, a prevalence claim, or a defense-success claim."
        ),
        "claim_boundary": {
            "commercial_runtime_claim": False,
            "defense_success_claim": False,
            "prevalence_claim": False,
            "public_network_claim": False,
            "runtime_behavior_claim": False,
            "semia_equivalence_claim": False,
        },
        "scanner": {
            "scope": "controlled_fixture_skill_text_and_scripts",
            "signal_families": [definition["family"] for definition in STATIC_SIGNAL_DEFINITIONS],
        },
        "aggregate": aggregate,
        "cases": rows,
    }


def access_rules(contract: dict[str, Any], side: str) -> list[dict[str, Any]]:
    rows = []
    access = contract.get("access", {})
    if not isinstance(access, dict):
        return rows
    for surface, surface_data in access.items():
        if not isinstance(surface_data, dict):
            continue
        direct_rules = surface_data.get(side)
        if isinstance(direct_rules, list):
            for rule in direct_rules:
                if isinstance(rule, dict):
                    rows.append({"rule": rule, "surface": surface, "subsurface": None})
        for child_name, child_data in surface_data.items():
            if not isinstance(child_data, dict):
                continue
            child_rules = child_data.get(side)
            if isinstance(child_rules, list):
                for rule in child_rules:
                    if isinstance(rule, dict):
                        rows.append({"rule": rule, "surface": surface, "subsurface": child_name})
    return rows


def activation_deny_count(contract: dict[str, Any]) -> int:
    activation = contract.get("activation", {})
    if not isinstance(activation, dict):
        return 0
    denied_contexts = activation.get("denied_contexts") or []
    denied_triggers = activation.get("denied_triggers") or []
    rules = activation.get("rules") or []
    return len(denied_contexts) + len(denied_triggers) + len(rules)


def denied_rule_count(
    contract: dict[str, Any],
    candidate_surfaces: list[str],
    candidate_event_types: list[str],
) -> int:
    surface_set = set(candidate_surfaces)
    event_type_set = set(candidate_event_types)
    count = 0
    for row in access_rules(contract, "deny"):
        rule = row["rule"]
        match_event = rule.get("event_type")
        if row["surface"] in surface_set or match_event in event_type_set:
            count += 1
    if "activation" in surface_set:
        count += activation_deny_count(contract)
    return count


def contract_deny_surface_counts(contract: dict[str, Any]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in access_rules(contract, "deny"):
        counts[row["surface"]] += 1
    activation_count = activation_deny_count(contract)
    if activation_count:
        counts["activation"] += activation_count
    return dict(sorted(counts.items()))


def build_reachability_approximation_report(
    repo_root: Path,
    cases: list[dict[str, Any]],
    static_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    static_report = static_report or build_static_scanner_report(repo_root, cases)
    rows = []
    candidates = []
    static_cases = {
        (row["family"], row["case_id"]): row
        for row in static_report["cases"]
    }
    for case in cases:
        key = (case["family"], case["case_id"])
        static_row = static_cases[key]
        contract = load_yaml(repo_root / case["contract"])
        case_candidates = []
        for finding in static_row["findings"]:
            denied_count = denied_rule_count(
                contract,
                finding["candidate_surfaces"],
                finding["candidate_event_types"],
            )
            if denied_count == 0:
                continue
            candidate = {
                "approximation_basis": "static_signal_plus_contract_deny_rule",
                "candidate_event_types": finding["candidate_event_types"],
                "candidate_surfaces": finding["candidate_surfaces"],
                "denied_rule_count": denied_count,
                "file": finding["file"],
                "runtime_confirmation_claim": "not_claimed",
                "signal_family": finding["signal_family"],
            }
            case_candidates.append(candidate)
            candidates.append({**candidate, "family": case["family"], "case_id": case["case_id"]})
        rows.append(
            {
                "case_id": case["case_id"],
                "contract": case["contract"],
                "contract_deny_surface_counts": contract_deny_surface_counts(contract),
                "family": case["family"],
                "candidate_count": len(case_candidates),
                "candidates": case_candidates,
                "static_finding_count": static_row["finding_count"],
                "variant_id": case["variant_id"],
            }
        )
    aggregate = {
        "case_count": len(rows),
        "cases_with_candidates": sum(1 for row in rows if row["candidate_count"] > 0),
        "candidate_count": len(candidates),
        "runtime_confirmation_claims_supported": 0,
        "semia_equivalence_claims_supported": 0,
        "semia_reproduction_claims_supported": 0,
        "static_findings_considered": sum(row["static_finding_count"] for row in rows),
        "unique_candidate_surfaces": sorted(
            {
                surface
                for candidate in candidates
                for surface in candidate["candidate_surfaces"]
            }
        ),
    }
    return {
        "schema_version": "0.1",
        "report_type": "semia_style_reachability_approximation",
        "boundary": (
            "Semia-style static reachability approximation over controlled fixture skill text and SkillDiff "
            "contracts. This is explicitly not a Semia reproduction, Semia equivalence result, runtime "
            "confirmation, or prevalence claim."
        ),
        "claim_boundary": {
            "commercial_runtime_claim": False,
            "defense_success_claim": False,
            "prevalence_claim": False,
            "public_network_claim": False,
            "runtime_confirmation_claim": False,
            "semia_equivalence_claim": False,
            "semia_reproduction_claim": False,
        },
        "aggregate": aggregate,
        "cases": rows,
    }


def shell_allow_rules(contract: dict[str, Any]) -> list[dict[str, Any]]:
    return [row["rule"] for row in access_rules(contract, "allow") if row["surface"] == "shell"]


def command_matches_shell_rule(command: list[str], rule: dict[str, Any]) -> bool:
    match = rule.get("match", {})
    if not isinstance(match, dict):
        return False
    argv_exact = match.get("argv_exact")
    if isinstance(argv_exact, list) and [str(part) for part in argv_exact] == command:
        return True
    executable = match.get("executable")
    if isinstance(executable, str) and command and command[0] == executable:
        return True
    return False


def command_contract_allowed(command: list[str], contract: dict[str, Any]) -> bool:
    return any(command_matches_shell_rule(command, rule) for rule in shell_allow_rules(contract))


def is_controlled_fixture_command(command: list[str]) -> bool:
    return bool(command) and command[0] == "python3" and any(part.startswith("skill/") for part in command[1:])


def build_action_boundary_baseline_report(repo_root: Path, cases: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for case in cases:
        contract = load_yaml(repo_root / case["contract"])
        command = [str(part) for part in case["command"]]
        deny_counts = contract_deny_surface_counts(contract)
        allowed = command_contract_allowed(command, contract)
        controlled = is_controlled_fixture_command(command)
        flagged = not (allowed and controlled)
        rows.append(
            {
                "case_id": case["case_id"],
                "command": command,
                "command_contract_allowed": allowed,
                "contract": case["contract"],
                "controlled_fixture_command": controlled,
                "deny_surface_counts_considered": deny_counts,
                "family": case["family"],
                "requires_runtime_monitoring": sum(deny_counts.values()) > 0,
                "review_flag": flagged,
                "review_reason": "none" if not flagged else "command_not_contract_allowed_or_not_controlled_fixture",
                "style_boundary": "action-boundary relevance check only; not ClawGuard or Task Shield reproduction",
                "task_relevance_basis": "controlled fixture command plus contract shell allow rule" if not flagged else "manual_review_required",
                "variant_id": case["variant_id"],
            }
        )
    aggregate = {
        "case_count": len(rows),
        "clawguard_reproduction_claims_supported": 0,
        "command_actions_checked": len(rows),
        "command_actions_contract_allowed": sum(1 for row in rows if row["command_contract_allowed"]),
        "commands_relevant_by_fixture_scope": sum(1 for row in rows if row["controlled_fixture_command"]),
        "review_flags": sum(1 for row in rows if row["review_flag"]),
        "runtime_monitoring_required_cases": sum(1 for row in rows if row["requires_runtime_monitoring"]),
        "task_shield_reproduction_claims_supported": 0,
        "total_deny_rules_considered": sum(
            sum(row["deny_surface_counts_considered"].values())
            for row in rows
        ),
    }
    return {
        "schema_version": "0.1",
        "report_type": "action_boundary_baseline",
        "boundary": (
            "ClawGuard/Task Shield-style action-boundary relevance baseline over controlled fixture commands "
            "and SkillDiff contracts. This is not a reproduction or equivalence result for either system, and "
            "it does not claim commercial-runtime behavior or defense success."
        ),
        "claim_boundary": {
            "clawguard_equivalence_claim": False,
            "clawguard_reproduction_claim": False,
            "commercial_runtime_claim": False,
            "defense_success_claim": False,
            "public_network_claim": False,
            "task_shield_equivalence_claim": False,
            "task_shield_reproduction_claim": False,
        },
        "aggregate": aggregate,
        "cases": rows,
    }


def write_static_scanner_markdown(path: Path, report: dict[str, Any]) -> None:
    aggregate = report["aggregate"]
    lines = [
        "# Static Scanner Baseline",
        "",
        report["boundary"],
        "",
        "## Aggregate",
        "",
        f"- Cases: `{aggregate['case_count']}`",
        f"- Scanned files: `{aggregate['scanned_file_count']}`",
        f"- Static findings: `{aggregate['static_finding_count']}`",
        f"- Cases with findings: `{aggregate['cases_with_static_findings']}`",
        "",
        "| Family | Case | Files | Findings | Signal Families |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in report["cases"]:
        lines.append(
            "| {family} | {case_id} | {files} | {findings} | {signals} |".format(
                family=row["family"],
                case_id=row["case_id"],
                files=row["scanned_file_count"],
                findings=row["finding_count"],
                signals=", ".join(row["finding_families"]) or "none",
            )
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_reachability_markdown(path: Path, report: dict[str, Any]) -> None:
    aggregate = report["aggregate"]
    lines = [
        "# Semia-Style Reachability Approximation",
        "",
        report["boundary"],
        "",
        "## Aggregate",
        "",
        f"- Cases: `{aggregate['case_count']}`",
        f"- Static findings considered: `{aggregate['static_findings_considered']}`",
        f"- Approximation candidates: `{aggregate['candidate_count']}`",
        f"- Cases with candidates: `{aggregate['cases_with_candidates']}`",
        f"- Runtime confirmation claims supported: `{aggregate['runtime_confirmation_claims_supported']}`",
        f"- Semia equivalence claims supported: `{aggregate['semia_equivalence_claims_supported']}`",
        "",
        "| Family | Case | Static Findings | Candidates | Deny Surfaces |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in report["cases"]:
        lines.append(
            "| {family} | {case_id} | {static} | {candidates} | {surfaces} |".format(
                family=row["family"],
                case_id=row["case_id"],
                static=row["static_finding_count"],
                candidates=row["candidate_count"],
                surfaces=", ".join(row["contract_deny_surface_counts"].keys()) or "none",
            )
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_action_boundary_markdown(path: Path, report: dict[str, Any]) -> None:
    aggregate = report["aggregate"]
    lines = [
        "# Action-Boundary Baseline",
        "",
        report["boundary"],
        "",
        "## Aggregate",
        "",
        f"- Commands checked: `{aggregate['command_actions_checked']}`",
        f"- Contract-allowed commands: `{aggregate['command_actions_contract_allowed']}`",
        f"- Commands relevant by fixture scope: `{aggregate['commands_relevant_by_fixture_scope']}`",
        f"- Review flags: `{aggregate['review_flags']}`",
        f"- Runtime-monitoring-required cases: `{aggregate['runtime_monitoring_required_cases']}`",
        f"- ClawGuard reproduction claims supported: `{aggregate['clawguard_reproduction_claims_supported']}`",
        f"- Task Shield reproduction claims supported: `{aggregate['task_shield_reproduction_claims_supported']}`",
        "",
        "| Family | Case | Contract Allowed | Fixture Scoped | Review Flag | Deny Rules |",
        "| --- | --- | --- | --- | --- | ---: |",
    ]
    for row in report["cases"]:
        lines.append(
            "| {family} | {case_id} | {allowed} | {fixture} | {flag} | {deny} |".format(
                family=row["family"],
                case_id=row["case_id"],
                allowed="yes" if row["command_contract_allowed"] else "no",
                fixture="yes" if row["controlled_fixture_command"] else "no",
                flag="yes" if row["review_flag"] else "no",
                deny=sum(row["deny_surface_counts_considered"].values()),
            )
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
