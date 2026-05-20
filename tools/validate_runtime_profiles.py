#!/usr/bin/env python3
"""Validate runtime profiles for RM-06.

This validator uses a deterministic local subset of JSON Schema and enforces
benchmark-specific safety invariants. It intentionally avoids optional package
behavior so validation results do not vary across environments.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "schemas" / "runtime_profile.schema.json"
REQUIRED_OPERATIONS = {"prepare", "run", "collect", "cleanup", "capability_snapshot"}
REQUIRED_FEATURES = {
    "activation",
    "filesystem",
    "shell",
    "network",
    "credentials",
    "context",
    "persistence",
    "approvals",
    "tools",
    "mcp_plugin_apis",
    "logging",
    "cleanup",
    "instrumentation",
}
PROFILE_FAMILIES = {
    "RP1": "restricted_hosted",
    "RP2": "local_coding_agent",
    "RP3": "docker_sandbox",
    "RP4": "mcp_connected",
    "RP5": "plugin_style",
    "RP6": "policy_hardened",
}


class ValidationIssue:
    def __init__(self, path: Path | str, message: str, severity: str = "error") -> None:
        self.path = str(path)
        self.message = message
        self.severity = severity

    def __str__(self) -> str:
        return f"{self.severity.upper()} {self.path}: {self.message}"


def load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def load_profile(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError("profile must be a YAML object")
    return data


def canonical_profile_hash(profile: dict[str, Any]) -> str:
    import hashlib

    canonical = copy.deepcopy(profile)
    canonical.get("reproducibility", {}).pop("profile_hash", None)
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_schema(profile: dict[str, Any], path: Path, schema: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for location, message in _validate_node(profile, schema, schema, "<root>"):
        issues.append(ValidationIssue(path, f"schema violation at {location}: {message}"))
    return issues


def _validate_node(
    value: Any,
    schema_node: dict[str, Any],
    root_schema: dict[str, Any],
    location: str,
) -> list[tuple[str, str]]:
    issues: list[tuple[str, str]] = []
    if "$ref" in schema_node:
        schema_node = _resolve_ref(schema_node["$ref"], root_schema)

    if "enum" in schema_node and value not in schema_node["enum"]:
        issues.append((location, f"{value!r} is not one of {schema_node['enum']}"))

    if "type" in schema_node:
        expected_types = schema_node["type"]
        if isinstance(expected_types, str):
            expected_types = [expected_types]
        if not any(_matches_type(value, expected_type) for expected_type in expected_types):
            issues.append((location, f"expected type {expected_types}, got {type(value).__name__}"))
            return issues

    if "minLength" in schema_node and isinstance(value, str) and len(value) < schema_node["minLength"]:
        issues.append((location, f"string shorter than minLength {schema_node['minLength']}"))

    if "pattern" in schema_node and isinstance(value, str):
        if re.search(schema_node["pattern"], value) is None:
            issues.append((location, f"{value!r} does not match {schema_node['pattern']}"))

    if "minimum" in schema_node and isinstance(value, int | float) and value < schema_node["minimum"]:
        issues.append((location, f"{value!r} is less than minimum {schema_node['minimum']}"))

    if "maximum" in schema_node and isinstance(value, int | float) and value > schema_node["maximum"]:
        issues.append((location, f"{value!r} is greater than maximum {schema_node['maximum']}"))

    if isinstance(value, dict):
        properties = schema_node.get("properties", {})
        required = set(schema_node.get("required", []))
        missing = sorted(required - set(value))
        for field in missing:
            issues.append((f"{location}.{field}", "missing required field"))

        additional = schema_node.get("additionalProperties", True)
        for field, field_value in value.items():
            field_location = f"{location}.{field}"
            if field in properties:
                issues.extend(_validate_node(field_value, properties[field], root_schema, field_location))
            elif additional is False:
                issues.append((field_location, "unknown field"))
            elif isinstance(additional, dict):
                issues.extend(_validate_node(field_value, additional, root_schema, field_location))

    if isinstance(value, list):
        if schema_node.get("uniqueItems"):
            serialized = [json.dumps(item, sort_keys=True) for item in value]
            if len(serialized) != len(set(serialized)):
                issues.append((location, "array items must be unique"))
        item_schema = schema_node.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                issues.extend(_validate_node(item, item_schema, root_schema, f"{location}[{index}]"))

    return issues


def _resolve_ref(ref: str, root_schema: dict[str, Any]) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise ValueError(f"unsupported schema ref {ref}")
    node: Any = root_schema
    for part in ref.removeprefix("#/").split("/"):
        node = node[part]
    if not isinstance(node, dict):
        raise ValueError(f"schema ref {ref} does not resolve to an object")
    return node


def _matches_type(value: Any, expected_type: str) -> bool:
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, int | float) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "null":
        return value is None
    raise ValueError(f"unsupported schema type {expected_type}")


def _is_safe_domain(domain: str) -> bool:
    return domain.endswith(".invalid") or domain in {"localhost", "127.0.0.1"}


def validate_semantics(
    profile: dict[str, Any],
    path: Path,
    *,
    allow_pending_hash: bool,
    check_hash: bool,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    profile_id = profile.get("profile_id")
    runtime_family = profile.get("runtime_family")
    expected_family = PROFILE_FAMILIES.get(profile_id)

    if expected_family is None:
        issues.append(ValidationIssue(path, f"unknown profile_id {profile_id!r}"))
    elif runtime_family != expected_family:
        issues.append(ValidationIssue(path, f"{profile_id} must use runtime_family {expected_family}"))

    if path.name.startswith("RP") and profile_id and not path.name.startswith(str(profile_id)):
        issues.append(ValidationIssue(path, f"filename does not match profile_id {profile_id}"))

    adapter = profile.get("adapter", {})
    operations = set(adapter.get("supported_operations", []))
    missing_ops = sorted(REQUIRED_OPERATIONS - operations)
    if missing_ops:
        issues.append(ValidationIssue(path, f"adapter missing operations: {', '.join(missing_ops)}"))
    constraints = adapter.get("runtime_constraints")
    if adapter.get("adapter_id") == "docker_adapter":
        if not constraints:
            issues.append(ValidationIssue(path, "docker_adapter requires adapter.runtime_constraints"))
        else:
            if constraints.get("network_mode") != "none":
                issues.append(ValidationIssue(path, "RP3 docker network_mode must be none"))
            if constraints.get("read_only_rootfs") is not True:
                issues.append(ValidationIssue(path, "RP3 docker root filesystem must be read-only"))
            if constraints.get("docker_socket_mounted") is not False:
                issues.append(ValidationIssue(path, "RP3 must not mount the Docker socket"))
            image_ref = constraints.get("container_image_ref", "")
            base_digest = profile.get("reproducibility", {}).get("base_image_digest", "")
            image_digest = _pinned_image_digest(image_ref)
            if not image_digest:
                issues.append(ValidationIssue(path, "docker container_image_ref must include a sha256 repo digest or image ID"))
            elif image_digest != str(base_digest):
                issues.append(ValidationIssue(path, "container_image_ref digest must match base_image_digest"))
            mount_modes = {mount.get("mode") for mount in constraints.get("mounts", [])}
            if "read_only" not in mount_modes or "read_write" not in mount_modes:
                issues.append(ValidationIssue(path, "docker constraints need read-only seed and writable artifact mounts"))

    features = profile.get("features", {})
    if isinstance(features, dict):
        missing_features = sorted(REQUIRED_FEATURES - set(features))
        if missing_features:
            issues.append(ValidationIssue(path, f"missing feature blocks: {', '.join(missing_features)}"))

    credentials = features.get("credentials", {})
    if credentials.get("host_credentials_allowed") is True:
        issues.append(ValidationIssue(path, "real host credentials are not allowed in benchmark profiles"))

    network = features.get("network", {})
    if network.get("default_egress") == "allow":
        issues.append(ValidationIssue(path, "live external egress cannot be default-allow"))
    for domain in network.get("allowed_domains", []):
        if not _is_safe_domain(domain):
            issues.append(ValidationIssue(path, f"allowed domain {domain!r} is not a safe test domain"))
    for domain in network.get("fake_sink_domains", []):
        if not domain.endswith(".invalid"):
            issues.append(ValidationIssue(path, f"fake sink domain {domain!r} must end with .invalid"))

    filesystem = features.get("filesystem", {})
    cleanup = features.get("cleanup", {})
    writable_roots = []
    for root in filesystem.get("roots", []):
        path_value = root.get("path", "")
        mode = root.get("mode")
        if mode != "deny" and (path_value.startswith("/") or path_value.startswith("..") or path_value.startswith("~")):
            issues.append(ValidationIssue(path, f"non-deny root path {path_value!r} escapes the run workspace"))
        if mode == "read_write":
            writable_roots.append(path_value)
    if writable_roots and not cleanup.get("cleanup_on_failure"):
        issues.append(ValidationIssue(path, "writable roots require cleanup_on_failure"))
    if writable_roots and not cleanup.get("post_cleanup_scan"):
        issues.append(ValidationIssue(path, "writable roots require post_cleanup_scan"))

    persistence = features.get("persistence", {})
    if persistence.get("enabled") and persistence.get("retention_scope") in {"", "none", None}:
        issues.append(ValidationIssue(path, "enabled persistence requires a retention scope"))
    if persistence.get("cross_run_state_allowed"):
        issues.append(ValidationIssue(path, "cross-run state is not allowed in reproducible benchmark profiles"))
    if persistence.get("post_cleanup_allowed"):
        issues.append(ValidationIssue(path, "post-cleanup persistence is not allowed in benchmark profiles"))

    mcp_plugin = features.get("mcp_plugin_apis", {})
    repro = profile.get("reproducibility", {})
    if mcp_plugin.get("enabled"):
        has_fixture_hash = (
            repro.get("mcp_fixture_hash") not in {"", "none", None}
            or repro.get("plugin_fixture_hash") not in {"", "none", None}
        )
        if not has_fixture_hash:
            issues.append(ValidationIssue(path, "enabled MCP/plugin APIs require a fixture hash"))
    if mcp_plugin.get("plugin_storage_allowed") and repro.get("plugin_fixture_hash") in {"", "none", None}:
        issues.append(ValidationIssue(path, "plugin storage requires plugin_fixture_hash"))

    approvals = features.get("approvals", {})
    if not approvals.get("mode"):
        issues.append(ValidationIssue(path, "approval mode must be explicit"))
    if not approvals.get("record_transcript"):
        issues.append(ValidationIssue(path, "approval transcript recording is required"))

    instrumentation = features.get("instrumentation", {})
    if not instrumentation.get("enabled"):
        issues.append(ValidationIssue(path, "instrumentation must be enabled"))
    if not instrumentation.get("capability_snapshot"):
        issues.append(ValidationIssue(path, "capability_snapshot must be enabled"))
    if network.get("enabled") and instrumentation.get("network_monitor") in {"", "disabled", "none"}:
        issues.append(ValidationIssue(path, "enabled network requires network instrumentation"))
    if features.get("shell", {}).get("enabled") and instrumentation.get("process_monitor") in {"", "disabled", "none"}:
        issues.append(ValidationIssue(path, "enabled shell requires process instrumentation"))

    if profile_id == "RP6":
        if filesystem.get("default_read") != "deny" or filesystem.get("default_write") != "deny":
            issues.append(ValidationIssue(path, "RP6 must default-deny filesystem reads and writes"))
        if network.get("enabled"):
            issues.append(ValidationIssue(path, "RP6 must keep network disabled"))
        if credentials.get("host_credentials_allowed"):
            issues.append(ValidationIssue(path, "RP6 must not allow host credentials"))
        if features.get("tools", {}).get("default_tool_policy") != "deny":
            issues.append(ValidationIssue(path, "RP6 must default-deny tool access"))

    actual_hash = repro.get("profile_hash")
    expected_hash = canonical_profile_hash(profile)
    if check_hash:
        if actual_hash == "pending" and allow_pending_hash:
            pass
        elif actual_hash != expected_hash:
            issues.append(
                ValidationIssue(
                    path,
                    f"profile_hash mismatch: expected {expected_hash}, found {actual_hash}",
                )
            )

    return issues


def _pinned_image_digest(image_ref: str) -> str:
    if image_ref.startswith("sha256:"):
        return image_ref
    if "@sha256:" in image_ref:
        return "sha256:" + image_ref.rsplit("@sha256:", 1)[1]
    return ""


def validate_profile(
    profile: dict[str, Any],
    path: Path,
    schema: dict[str, Any],
    *,
    allow_pending_hash: bool = False,
    check_hash: bool = True,
) -> list[ValidationIssue]:
    return validate_schema(profile, path, schema) + validate_semantics(
        profile,
        path,
        allow_pending_hash=allow_pending_hash,
        check_hash=check_hash,
    )


def run_self_test(schema: dict[str, Any], profile_paths: list[Path]) -> list[ValidationIssue]:
    if not profile_paths:
        return [ValidationIssue("self-test", "need at least one valid profile input for self-test")]

    base_profile = load_profile(profile_paths[0])
    failures: list[ValidationIssue] = []

    bad_creds = copy.deepcopy(base_profile)
    bad_creds["features"]["credentials"]["host_credentials_allowed"] = True
    if not validate_profile(bad_creds, Path("self-test-host-creds"), schema, check_hash=False):
        failures.append(ValidationIssue("self-test", "host credential violation was not detected"))

    bad_network = copy.deepcopy(base_profile)
    bad_network["features"]["network"]["enabled"] = True
    bad_network["features"]["network"]["allowed_domains"] = ["example.com"]
    bad_network["features"]["instrumentation"]["network_monitor"] = "shimmed_fake_sink"
    if not validate_profile(bad_network, Path("self-test-network"), schema, check_hash=False):
        failures.append(ValidationIssue("self-test", "unsafe network domain was not detected"))

    bad_ops = copy.deepcopy(base_profile)
    bad_ops["adapter"]["supported_operations"] = ["prepare", "run"]
    if not validate_profile(bad_ops, Path("self-test-ops"), schema, check_hash=False):
        failures.append(ValidationIssue("self-test", "missing adapter operations were not detected"))

    bad_enum = copy.deepcopy(base_profile)
    bad_enum["features"]["shell"]["execution_mode"] = "typo_subprocess"
    if not validate_profile(bad_enum, Path("self-test-enum"), schema, check_hash=False):
        failures.append(ValidationIssue("self-test", "nested schema enum violation was not detected"))

    bad_hash = copy.deepcopy(base_profile)
    bad_hash["reproducibility"]["profile_hash"] = "deadbeef"
    if not validate_profile(bad_hash, Path("self-test-hash"), schema):
        failures.append(ValidationIssue("self-test", "hash mismatch was not detected"))

    return failures


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate RM-06 runtime profile YAML files.")
    parser.add_argument("profiles", nargs="+", type=Path, help="Profile YAML paths")
    parser.add_argument("--allow-pending-hash", action="store_true", help="Allow profile_hash: pending")
    parser.add_argument("--no-hash-check", action="store_true", help="Skip profile_hash validation")
    parser.add_argument("--print-hashes", action="store_true", help="Print canonical profile hashes")
    parser.add_argument("--self-test", action="store_true", help="Run local validator negative tests")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    schema = load_schema()
    all_issues: list[ValidationIssue] = []
    loaded_profiles: list[tuple[Path, dict[str, Any]]] = []

    for profile_path in args.profiles:
        try:
            profile = load_profile(profile_path)
        except Exception as exc:  # noqa: BLE001 - command-line tool should report all load errors.
            all_issues.append(ValidationIssue(profile_path, f"failed to load YAML: {exc}"))
            continue
        loaded_profiles.append((profile_path, profile))
        all_issues.extend(
            validate_profile(
                profile,
                profile_path,
                schema,
                allow_pending_hash=args.allow_pending_hash,
                check_hash=not args.no_hash_check,
            )
        )

    if args.self_test:
        all_issues.extend(run_self_test(schema, [path for path, _profile in loaded_profiles]))

    if args.print_hashes:
        for profile_path, profile in loaded_profiles:
            print(f"{profile_path} {canonical_profile_hash(profile)}")

    for issue in all_issues:
        print(issue, file=sys.stderr)

    if all_issues:
        return 1

    print(f"validated {len(loaded_profiles)} runtime profile(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
