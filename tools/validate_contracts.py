#!/usr/bin/env python3
"""Validate RM-05 security contracts.

This is a lightweight semantic validator for the research artifacts. It is not
the runtime trace checker; it catches malformed contract structure and matching
rules early enough to keep benchmark items reproducible.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment guard
    raise SystemExit("PyYAML is required to validate YAML contracts") from exc

try:  # Optional; the fallback validator below mirrors the schema-critical checks.
    import jsonschema
except ImportError:  # pragma: no cover - optional dependency
    jsonschema = None


REQUIRED_TOP = {
    "schema_version",
    "contract_id",
    "contract_version",
    "skill_id",
    "task_id",
    "task",
    "activation",
    "access",
    "approval_required",
    "canaries",
    "expected_outputs",
    "severity_overrides",
    "rules",
}

ALLOWED_TOP = REQUIRED_TOP | {
    "description",
    "category",
    "attack_family",
    "metadata",
}

ACCESS_SURFACES = {
    "filesystem",
    "shell",
    "network",
    "tools",
    "sinks",
    "persistence",
    "context",
    "credentials",
}

SEVERITIES = {"low", "medium", "high", "critical"}
DRIFT_CLASSES = {"D1", "D2", "D3", "D4", "D5"}
PATH_ANCHORS = ("./", "~/", "/", "env:", "cred:")
APPROVAL_EVENTS = {
    "filesystem.read",
    "filesystem.write",
    "filesystem.delete",
    "filesystem.modify",
    "network.connect",
    "network.send",
    "shell.exec",
    "process.exec",
    "tool.call",
    "persistence.write",
}
SINK_TYPES = {
    "local_report",
    "generated_summary",
    "fake_http",
    "external_http",
    "tool_message",
    "persistent_state",
    "stdout_log",
    "stderr_log",
    "local_json",
    "local_html",
    "dashboard_bundle",
    "docs_bundle",
    "approved_output_tree",
    "output_tree",
    "source_tree",
    "connector_log",
}
SCHEMA_PATH = Path("schemas/security_contract.schema.json")


class ValidationError(Exception):
    """One contract validation error."""


def load_yaml(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValidationError("root must be a mapping")
    return data


def normalize_path_pattern(pattern: str) -> str:
    if "\x00" in pattern:
        raise ValidationError(f"path pattern {pattern!r} contains NUL")
    if not pattern.startswith(PATH_ANCHORS):
        raise ValidationError(
            f"path pattern {pattern!r} must start with one of {PATH_ANCHORS}"
        )
    if pattern.startswith(("env:", "cred:")):
        return pattern
    anchor = pattern[:2] if pattern.startswith(("./", "~/")) else "/"
    remainder = pattern[2:] if anchor in {"./", "~/"} else pattern[1:]
    parts: list[str] = []
    for part in remainder.split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            if not parts:
                raise ValidationError(f"path pattern {pattern!r} escapes its anchor")
            parts.pop()
            continue
        parts.append(part)
    if anchor == "/":
        return "/" + "/".join(parts)
    return anchor + "/".join(parts)


def validate_domain_pattern(pattern: str) -> None:
    if pattern != pattern.lower():
        raise ValidationError(f"domain pattern {pattern!r} must be lowercase")
    if "://" in pattern or "/" in pattern:
        raise ValidationError(f"domain pattern {pattern!r} must be a host pattern")
    if pattern == "*":
        return
    if "*" in pattern:
        if not pattern.startswith("*.") or pattern.count("*") != 1:
            raise ValidationError(
                f"domain wildcard {pattern!r} must be full leftmost label"
            )
    labels = pattern[2:].split(".") if pattern.startswith("*.") else pattern.split(".")
    if any(not label for label in labels):
        raise ValidationError(f"domain pattern {pattern!r} has an empty label")


def match_path_glob(pattern: str, observed_path: str) -> bool:
    """Match normalized path globs using segment-aware * and recursive **."""
    pattern = normalize_path_pattern(pattern)
    observed_path = normalize_path_pattern(observed_path)
    pattern_parts = pattern.split("/")
    observed_parts = observed_path.split("/")

    def match_parts(p_index: int, o_index: int) -> bool:
        while p_index < len(pattern_parts):
            token = pattern_parts[p_index]
            if token == "**":
                if p_index == len(pattern_parts) - 1:
                    return True
                return any(match_parts(p_index + 1, next_index) for next_index in range(o_index, len(observed_parts) + 1))
            if o_index >= len(observed_parts):
                return False
            if not fnmatch.fnmatchcase(observed_parts[o_index], token):
                return False
            p_index += 1
            o_index += 1
        return o_index == len(observed_parts)

    return match_parts(0, 0)


def match_domain(pattern: str, hostname: str) -> bool:
    """Match exact host, leftmost-label wildcard, or deny-all wildcard."""
    pattern = pattern.lower().rstrip(".")
    hostname = hostname.lower().rstrip(".")
    validate_domain_pattern(pattern)
    if pattern == "*":
        return True
    if pattern.startswith("*."):
        suffix = pattern[2:]
        return hostname.endswith("." + suffix) and hostname != suffix
    return hostname == pattern


def match_command(rule_match: dict[str, Any], argv: list[str], executable: str | None = None) -> bool:
    """Match command rules without parsing shell strings."""
    if "argv_exact" in rule_match:
        return argv == rule_match["argv_exact"]
    if "argv_prefix" in rule_match:
        prefix = rule_match["argv_prefix"]
        return argv[: len(prefix)] == prefix
    if "executable" in rule_match:
        observed = executable or (argv[0] if argv else "")
        pattern = rule_match["executable"]
        if pattern == "*":
            return bool(observed)
        observed_name = PurePosixPath(observed).name
        return fnmatch.fnmatchcase(observed_name, pattern) or fnmatch.fnmatchcase(observed, pattern)
    return False


def rule_specificity(rule_match: dict[str, Any]) -> tuple[int, int]:
    """Return rough specificity: exact/targeted rules beat broad globs."""
    if "argv_exact" in rule_match:
        return (90, len(rule_match["argv_exact"]))
    if "argv_prefix" in rule_match:
        return (80, len(rule_match["argv_prefix"]))
    if "executable" in rule_match:
        value = rule_match["executable"]
        return (10 if value == "*" else 70, len(value))
    if "domain" in rule_match:
        return (90, len(rule_match["domain"]))
    if "domain_glob" in rule_match:
        value = rule_match["domain_glob"]
        if value == "*":
            return (10, 0)
        return (70, len(value))
    if "path_glob" in rule_match:
        value = normalize_path_pattern(rule_match["path_glob"])
        if "**" in value:
            base = 40
        elif "*" in value or "?" in value:
            base = 60
        else:
            base = 90
        return (base, len(value))
    if "sink_type" in rule_match and "destination_glob" in rule_match:
        return (75, len(rule_match.get("destination_glob", "")))
    if "sink_type" in rule_match:
        return (50, len(rule_match["sink_type"]))
    if "tool_name" in rule_match and "method" in rule_match and "resource_uri_glob" in rule_match:
        return (90, len(rule_match["tool_name"]) + len(rule_match["method"]) + len(rule_match["resource_uri_glob"]))
    if "tool_name" in rule_match and "method" in rule_match:
        return (80, len(rule_match["tool_name"]) + len(rule_match["method"]))
    if "tool_name" in rule_match:
        return (70, len(rule_match["tool_name"]))
    return (1, 0)


def match_rule(rule_match: dict[str, Any], event: dict[str, Any]) -> bool:
    """Match a rule against a minimal normalized event dict."""
    if "path_glob" in rule_match:
        path = event.get("path") or event.get("target")
        if not isinstance(path, str) or not match_path_glob(rule_match["path_glob"], path):
            return False
    if "operation" in rule_match and event.get("operation") not in {None, rule_match["operation"]}:
        return False
    if "domain" in rule_match:
        host = event.get("domain") or event.get("hostname")
        if not isinstance(host, str) or not match_domain(rule_match["domain"], host):
            return False
    if "domain_glob" in rule_match:
        host = event.get("domain") or event.get("hostname")
        if not isinstance(host, str) or not match_domain(rule_match["domain_glob"], host):
            return False
    if any(key in rule_match for key in ("argv_exact", "argv_prefix", "executable")):
        argv = event.get("argv") or []
        if not isinstance(argv, list) or not match_command(rule_match, argv, event.get("executable")):
            return False
    if "tool_name" in rule_match and event.get("tool_name") != rule_match["tool_name"]:
        return False
    if "method" in rule_match and event.get("method") not in {None, rule_match["method"]}:
        return False
    if "sink_type" in rule_match and event.get("sink_type") != rule_match["sink_type"]:
        return False
    if "destination_glob" in rule_match:
        dest = event.get("destination")
        if not isinstance(dest, str) or not match_path_glob(rule_match["destination_glob"], dest):
            return False
    if "store_type" in rule_match and event.get("store_type") not in {None, rule_match["store_type"]}:
        return False
    if "source_type" in rule_match and event.get("source_type") not in {None, rule_match["source_type"]}:
        return False
    if "credential_type" in rule_match and event.get("credential_type") not in {None, rule_match["credential_type"]}:
        return False
    return True


def resolve_allow_deny(rule_bag: dict[str, Any], event: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    """Resolve allow/deny with documented specificity and deny-on-tie behavior."""
    matches: list[tuple[str, tuple[int, int], dict[str, Any]]] = []
    for side in ("allow", "deny"):
        for rule in rule_bag.get(side, []) or []:
            rule_match = rule.get("match", {})
            if isinstance(rule_match, dict) and match_rule(rule_match, event):
                matches.append((side, rule_specificity(rule_match), rule))
    if not matches:
        return ("unmatched", None)
    best_score = max(score for _, score, _ in matches)
    best = [item for item in matches if item[1] == best_score]
    deny = next((rule for side, _, rule in best if side == "deny"), None)
    if deny is not None:
        return ("deny", deny)
    return ("allow", best[0][2])


def resolve_ref(schema: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise ValidationError(f"unsupported schema ref {ref!r}")
    current: Any = schema
    for part in ref[2:].split("/"):
        current = current[part]
    if not isinstance(current, dict):
        raise ValidationError(f"schema ref {ref!r} does not resolve to object")
    return current


def type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "null":
        return value is None
    return True


def fallback_schema_validate(value: Any, node: dict[str, Any], schema: dict[str, Any], location: str) -> list[str]:
    """Small JSON Schema subset validator for the schema features used here."""
    if "$ref" in node:
        node = resolve_ref(schema, node["$ref"])

    errors: list[str] = []
    if "enum" in node and value not in node["enum"]:
        errors.append(f"{location}: {value!r} is not one of {node['enum']!r}")

    expected_type = node.get("type")
    if expected_type is not None:
        expected_types = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(type_matches(value, item) for item in expected_types):
            errors.append(f"{location}: expected {expected_types}, got {type(value).__name__}")
            return errors

    if isinstance(value, str) and "minLength" in node and len(value) < node["minLength"]:
        errors.append(f"{location}: string is shorter than minLength {node['minLength']}")

    if isinstance(value, list):
        if "minItems" in node and len(value) < node["minItems"]:
            errors.append(f"{location}: array has fewer than {node['minItems']} items")
        item_schema = node.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(fallback_schema_validate(item, item_schema, schema, f"{location}[{index}]"))
        if node.get("uniqueItems") and len(value) != len({repr(item) for item in value}):
            errors.append(f"{location}: array items are not unique")

    if isinstance(value, dict):
        required = node.get("required", [])
        for key in required:
            if key not in value:
                errors.append(f"{location}: missing required property {key!r}")
        properties = node.get("properties", {})
        if node.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append(f"{location}: unknown property {key!r}")
        additional = node.get("additionalProperties")
        for key, child in value.items():
            if key in properties:
                errors.extend(fallback_schema_validate(child, properties[key], schema, f"{location}.{key}"))
            elif isinstance(additional, dict):
                errors.extend(fallback_schema_validate(child, additional, schema, f"{location}.{key}"))
        if "minProperties" in node and len(value) < node["minProperties"]:
            errors.append(f"{location}: object has fewer than {node['minProperties']} properties")

    if isinstance(value, int) and not isinstance(value, bool):
        if "minimum" in node and value < node["minimum"]:
            errors.append(f"{location}: integer is less than minimum {node['minimum']}")
        if "maximum" in node and value > node["maximum"]:
            errors.append(f"{location}: integer is greater than maximum {node['maximum']}")

    return errors


def run_json_schema_validation(data: dict[str, Any], path: str, schema_path: Path) -> list[str]:
    """Run JSON Schema validation, using a local subset fallback if needed."""
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    if jsonschema is None:
        return [f"{path}: schema {message}" for message in fallback_schema_validate(data, schema, schema, "<root>")]
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda error: list(error.path))
    messages: list[str] = []
    for error in errors:
        location = ".".join(str(part) for part in error.path) or "<root>"
        messages.append(f"{path}: schema {location}: {error.message}")
    return messages


def validate_rule(path: str, rule: dict[str, Any], errors: list[str]) -> None:
    rule_id = rule.get("id")
    if not isinstance(rule_id, str) or not rule_id.strip():
        errors.append(f"{path}: rule is missing non-empty id")
    if not isinstance(rule.get("event_type"), str) or not rule["event_type"].strip():
        errors.append(f"{path}: rule {rule_id or '<missing>'} missing event_type")
    match = rule.get("match")
    if not isinstance(match, dict) or not match:
        errors.append(f"{path}: rule {rule_id or '<missing>'} missing match object")
        return
    for key in ("path_glob", "path_regex", "cwd_glob", "destination_glob"):
        value = match.get(key)
        if isinstance(value, str):
            try:
                normalize_path_pattern(value)
            except ValidationError as exc:
                errors.append(f"{path}: rule {rule_id} {exc}")
    for key in ("domain", "domain_glob"):
        value = match.get(key)
        if isinstance(value, str):
            try:
                validate_domain_pattern(value)
            except ValidationError as exc:
                errors.append(f"{path}: rule {rule_id} {exc}")
    if "argv_exact" in match and "executable" in match:
        errors.append(f"{path}: rule {rule_id} cannot use both argv_exact and executable")
    if "argv_prefix" in match and not isinstance(match["argv_prefix"], list):
        errors.append(f"{path}: rule {rule_id} argv_prefix must be a list")
    if "argv_exact" in match and not isinstance(match["argv_exact"], list):
        errors.append(f"{path}: rule {rule_id} argv_exact must be a list")
    severity = rule.get("severity")
    if severity is not None and severity not in SEVERITIES:
        errors.append(f"{path}: rule {rule_id} invalid severity {severity!r}")
    for drift in rule.get("drift_classes", []) or []:
        if drift not in DRIFT_CLASSES:
            errors.append(f"{path}: rule {rule_id} invalid drift class {drift!r}")


def collect_rule_objects(obj: Any) -> Iterable[dict[str, Any]]:
    if isinstance(obj, dict):
        if "id" in obj and "match" in obj and "event_type" in obj:
            yield obj
        for value in obj.values():
            yield from collect_rule_objects(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from collect_rule_objects(value)


def collect_ids(obj: Any) -> list[str]:
    ids: list[str] = []
    if isinstance(obj, dict):
        value = obj.get("id")
        if isinstance(value, str):
            ids.append(value)
        for child in obj.values():
            ids.extend(collect_ids(child))
    elif isinstance(obj, list):
        for child in obj:
            ids.extend(collect_ids(child))
    return ids


def validate_contract(path: str) -> list[str]:
    errors: list[str] = []
    try:
        data = load_yaml(path)
    except Exception as exc:
        return [f"{path}: {exc}"]

    errors.extend(run_json_schema_validation(data, path, SCHEMA_PATH))

    unknown = sorted(set(data) - ALLOWED_TOP)
    missing = sorted(REQUIRED_TOP - set(data))
    if unknown:
        errors.append(f"{path}: unknown top-level fields {unknown}")
    if missing:
        errors.append(f"{path}: missing top-level fields {missing}")

    access = data.get("access")
    if not isinstance(access, dict):
        errors.append(f"{path}: access must be a mapping")
    else:
        missing_access = sorted(ACCESS_SURFACES - set(access))
        if missing_access:
            errors.append(f"{path}: missing access surfaces {missing_access}")
        fs = access.get("filesystem")
        if not isinstance(fs, dict):
            errors.append(f"{path}: access.filesystem must be a mapping")
        else:
            for key in ("reads", "writes"):
                if key not in fs:
                    errors.append(f"{path}: access.filesystem.{key} is required")
        for surface, bag in access.items():
            if surface == "filesystem":
                bags = (bag or {}).values() if isinstance(bag, dict) else []
            else:
                bags = [bag]
            for rule_bag in bags:
                if not isinstance(rule_bag, dict):
                    continue
                for side in ("allow", "deny"):
                    if side not in rule_bag or not isinstance(rule_bag[side], list):
                        errors.append(f"{path}: access.{surface}.{side} must be a list")

    for key in ("approval_required", "canaries", "expected_outputs", "severity_overrides", "rules"):
        if not isinstance(data.get(key), list):
            errors.append(f"{path}: {key} must be a list")
    if isinstance(data.get("expected_outputs"), list) and not data["expected_outputs"]:
        errors.append(f"{path}: expected_outputs must not be empty")

    ids = collect_ids(data)
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    if duplicates:
        errors.append(f"{path}: duplicate ids {duplicates}")

    for rule in collect_rule_objects(data):
        validate_rule(path, rule, errors)

    for approval in data.get("approval_required", []) or []:
        if isinstance(approval, dict):
            event_type = approval.get("event_type")
            if event_type not in APPROVAL_EVENTS:
                errors.append(f"{path}: approval {approval.get('id')} unknown event {event_type!r}")
            if action_is_denied_by_contract(data, approval):
                errors.append(
                    f"{path}: approval {approval.get('id')} targets a denied action; "
                    "approval cannot make denied behavior compliant"
                )

    for canary in data.get("canaries", []) or []:
        if not isinstance(canary, dict):
            errors.append(f"{path}: canary entries must be mappings")
            continue
        denied_sinks = canary.get("denied_sinks")
        if not isinstance(denied_sinks, list) or not denied_sinks:
            errors.append(f"{path}: canary {canary.get('id')} needs denied_sinks")
        for sink in denied_sinks or []:
            if sink not in SINK_TYPES:
                errors.append(f"{path}: canary {canary.get('id')} unknown sink {sink!r}")

    return errors


def get_rule_bags_for_event(data: dict[str, Any], event_type: str) -> list[dict[str, Any]]:
    access = data.get("access", {})
    mapping = {
        "filesystem.read": [("filesystem", "reads")],
        "filesystem.write": [("filesystem", "writes")],
        "filesystem.delete": [("filesystem", "writes")],
        "filesystem.modify": [("filesystem", "writes")],
        "shell.exec": [("shell", None)],
        "process.exec": [("shell", None)],
        "network.connect": [("network", None)],
        "network.send": [("network", None)],
        "tool.call": [("tools", None)],
        "persistence.write": [("persistence", None), ("filesystem", "writes"), ("sinks", None)],
        "output.generated": [("sinks", None)],
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


def action_is_denied_by_contract(data: dict[str, Any], approval: dict[str, Any]) -> bool:
    event_type = approval.get("event_type")
    match = approval.get("match")
    if not isinstance(event_type, str) or not isinstance(match, dict):
        return False
    synthetic_event = {
        "path": match.get("path_glob"),
        "target": match.get("path_glob") or match.get("destination_glob"),
        "operation": match.get("operation"),
        "domain": match.get("domain") or match.get("domain_glob"),
        "argv": match.get("argv_exact") or match.get("argv_prefix") or [],
        "executable": match.get("executable"),
        "tool_name": match.get("tool_name"),
        "method": match.get("method"),
        "sink_type": match.get("sink_type"),
        "destination": match.get("destination_glob"),
        "store_type": match.get("store_type"),
        "source_type": match.get("source_type"),
        "credential_type": match.get("credential_type"),
    }
    for bag in get_rule_bags_for_event(data, event_type):
        decision, _ = resolve_allow_deny(bag, synthetic_event)
        if decision == "deny":
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("contracts", nargs="+", help="Contract YAML files to validate")
    parser.add_argument("--self-test", action="store_true", help="Run matcher self-tests before validation")
    args = parser.parse_args()

    if args.self_test:
        assert match_path_glob("./src/**", "./src/index.js")
        assert not match_path_glob("./src/*", "./src/lib/index.js")
        assert match_domain("*.example.com", "api.example.com")
        assert not match_domain("*.example.com", "example.com")
        assert match_command({"argv_exact": ["npm", "test"]}, ["npm", "test"])
        assert not match_command({"argv_exact": ["npm", "test"]}, ["sh", "-c", "npm test"])
        assert match_command({"executable": "*"}, ["python", "-m", "tool"])
        bag = {
            "allow": [{"id": "allow", "event_type": "filesystem.write", "match": {"path_glob": "./reports/**"}}],
            "deny": [{"id": "deny", "event_type": "filesystem.write", "match": {"path_glob": "./**"}}],
        }
        assert resolve_allow_deny(bag, {"path": "./reports/audit.md"})[0] == "allow"
        assert resolve_allow_deny(bag, {"path": "./src/index.js"})[0] == "deny"
        invalid_fixture = Path("contracts/invalid/approval-on-denied-action.yaml")
        if invalid_fixture.exists():
            fixture_errors = validate_contract(str(invalid_fixture))
            assert any("approval" in error and "denied action" in error for error in fixture_errors)

    all_errors: list[str] = []
    for path in args.contracts:
        errors = validate_contract(path)
        if errors:
            all_errors.extend(errors)
        else:
            print(f"ok {path}")

    if all_errors:
        print("\n".join(all_errors), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
