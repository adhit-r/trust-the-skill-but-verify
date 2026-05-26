#!/usr/bin/env python3
"""Validate Gate 3 benchmark case inclusion manifests."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "schemas" / "benchmark_case.schema.json"
SKIP_DIRS = {".git", "__pycache__"}
SKIP_FILES = {".DS_Store"}
CURRENT_STATUS_TO_STAGE = {
    "current_pilot": "pilot",
    "current_mvp": "mvp",
    "planned_inclusion": "planned",
}
CONTRACT_CATEGORY_TO_NORMALIZED = {
    "document-automation": "document automation",
    "repository-maintenance": "repository maintenance",
    "compliance-audit": "compliance/audit",
    "data-extraction": "data extraction",
    "api-workflow": "API workflow",
    "network-egress": "API workflow",
    "mcp-tool-workflow": "MCP/tool workflow",
    "local-file-operations": "local file operations",
    "local-file-operation": "local file operations",
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


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("manifest must be a JSON object")
    return data


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def workspace_snapshot_hash(root: Path) -> str:
    if not root.is_dir():
        raise FileNotFoundError(f"workspace root does not exist: {root}")

    entries: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(root).parts
        if any(part in SKIP_DIRS for part in rel_parts) or path.name in SKIP_FILES:
            continue
        rel = path.relative_to(root).as_posix()
        entries.append(f"{rel}\0{sha256_file(path)}\n")

    digest = hashlib.sha256()
    for entry in entries:
        digest.update(entry.encode("utf-8"))
    return digest.hexdigest()


def validate_schema(manifest: dict[str, Any], path: Path, schema: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for location, message in _validate_node(manifest, schema, schema, "<root>"):
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


def validate_manifest(manifest: dict[str, Any], path: Path, schema: dict[str, Any]) -> list[ValidationIssue]:
    return validate_schema(manifest, path, schema) + validate_semantics(manifest, path)


def validate_semantics(manifest: dict[str, Any], path: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    cases = manifest.get("cases", [])
    if manifest.get("declared_case_count") != len(cases):
        issues.append(
            ValidationIssue(
                path,
                f"declared_case_count {manifest.get('declared_case_count')} does not match {len(cases)} case(s)",
            )
        )

    seen_case_ids: set[str] = set()
    skill_source_mix_labels: dict[str, set[str]] = {}
    skill_source_kinds: dict[str, set[str]] = {}
    skill_source_mix_support: dict[str, set[str]] = {}
    for index, case in enumerate(cases):
        case_id = case.get("case_id")
        prefix = f"{path} case[{index}]"
        if case_id in seen_case_ids:
            issues.append(ValidationIssue(path, f"duplicate case_id {case_id!r}"))
        elif isinstance(case_id, str):
            seen_case_ids.add(case_id)

        provenance = case.get("provenance", {})
        task_prompt = case.get("task_prompt", {})
        contract = case.get("contract", {})
        workspace = case.get("workspace", {})
        execution = case.get("execution", {})
        expected_output = case.get("expected_output", {})
        canary_policy = case.get("canary_policy", {})
        publication_boundary = case.get("publication_boundary", {})
        safety_status = case.get("safety_status", {})

        if not provenance:
            issues.append(ValidationIssue(path, f"{prefix} missing provenance block"))
            continue
        if not execution:
            issues.append(ValidationIssue(path, f"{prefix} missing execution block"))
            continue
        source_kind = provenance.get("source_kind")
        source_mix = provenance.get("source_mix", {})
        source_mix_label = source_mix.get("label")
        skill_id = provenance.get("skill_id")
        if isinstance(skill_id, str) and isinstance(source_mix_label, str):
            skill_source_mix_labels.setdefault(skill_id, set()).add(source_mix_label)
            if isinstance(source_kind, str):
                skill_source_kinds.setdefault(skill_id, set()).add(source_kind)
        if not source_mix.get("label_note"):
            issues.append(ValidationIssue(path, f"{prefix} provenance.source_mix.label_note must be set"))
        if not task_prompt:
            issues.append(ValidationIssue(path, f"{prefix} missing task_prompt block"))
            continue
        if not contract:
            issues.append(ValidationIssue(path, f"{prefix} missing contract block"))
            continue
        if not workspace:
            issues.append(ValidationIssue(path, f"{prefix} missing workspace block"))
            continue
        missing_nested_block = False
        if not expected_output:
            issues.append(ValidationIssue(path, f"{prefix} missing expected_output block"))
            missing_nested_block = True
        if not canary_policy:
            issues.append(ValidationIssue(path, f"{prefix} missing canary_policy block"))
            missing_nested_block = True
        if not publication_boundary:
            issues.append(ValidationIssue(path, f"{prefix} missing publication_boundary block"))
            missing_nested_block = True
        if not safety_status:
            issues.append(ValidationIssue(path, f"{prefix} missing safety_status block"))
            missing_nested_block = True
        if missing_nested_block:
            continue

        case_status = case.get("case_status")
        expected_stage = CURRENT_STATUS_TO_STAGE.get(case_status)
        if expected_stage and execution.get("evidence_stage") != expected_stage:
            issues.append(
                ValidationIssue(
                    path,
                    f"{prefix} case_status {case_status!r} must use execution.evidence_stage {expected_stage!r}",
                )
            )

        source_manifest_ref = provenance.get("source_manifest_ref")
        source_manifest_path = _repo_path(source_manifest_ref)
        if source_manifest_path is None:
            issues.append(ValidationIssue(path, f"{prefix} provenance.source_manifest_ref must be a non-empty repo path"))
            continue
        if not source_manifest_path.is_file():
            issues.append(ValidationIssue(path, f"{prefix} missing source manifest {source_manifest_ref}"))
            continue

        source_manifest = _load_optional_json(source_manifest_path, issues, path, f"{prefix} source manifest")
        if source_manifest is None:
            continue

        if isinstance(skill_id, str):
            support = skill_source_mix_support.setdefault(skill_id, set())
            if _has_first_party_source_provenance(source_manifest):
                support.add("first_party")
            if _has_public_source_provenance(source_manifest):
                support.add("public")

        source_case = _resolve_pointer(
            source_manifest,
            provenance.get("source_case_pointer", ""),
            issues,
            path,
            f"{prefix} provenance.source_case_pointer",
        )
        if source_case is None:
            continue

        _validate_task_prompt(path, prefix, task_prompt, issues)
        contract_data = _validate_contract(path, prefix, contract, task_prompt, case.get("category"), issues)
        _validate_workspace(path, prefix, workspace, issues)
        _require_existing_file(path, prefix, provenance.get("contract_ref"), "provenance.contract_ref", issues)
        _require_existing_path(path, prefix, provenance.get("workspace_ref"), "provenance.workspace_ref", issues)
        _require_existing_file(path, prefix, execution.get("runnable_manifest_ref"), "execution.runnable_manifest_ref", issues)
        oracle_ref = expected_output.get("oracle_ref")
        if oracle_ref not in {None, ""}:
            _require_existing_file(path, prefix, oracle_ref, "expected_output.oracle_ref", issues)
        _require_existing_file(path, prefix, canary_policy.get("canary_source_ref"), "canary_policy.canary_source_ref", issues)

        if expected_output.get("primary_artifact") in {"", None}:
            issues.append(ValidationIssue(path, f"{prefix} expected_output.primary_artifact must be set"))

        if canary_policy.get("synthetic_only") is not True:
            issues.append(ValidationIssue(path, f"{prefix} canary_policy.synthetic_only must be true"))
        if canary_policy.get("real_secrets_allowed") is not False:
            issues.append(ValidationIssue(path, f"{prefix} canary_policy.real_secrets_allowed must be false"))
        if not canary_policy.get("declared_labels"):
            issues.append(ValidationIssue(path, f"{prefix} canary_policy.declared_labels must be non-empty"))
        if not canary_policy.get("denied_sinks"):
            issues.append(ValidationIssue(path, f"{prefix} canary_policy.denied_sinks must be non-empty"))

        if publication_boundary.get("safe_to_publish") is not True:
            issues.append(ValidationIssue(path, f"{prefix} publication_boundary.safe_to_publish must be true"))
        if not publication_boundary.get("boundary_note"):
            issues.append(ValidationIssue(path, f"{prefix} publication_boundary.boundary_note must be set"))
        if not publication_boundary.get("excluded_claims"):
            issues.append(ValidationIssue(path, f"{prefix} publication_boundary.excluded_claims must be non-empty"))

        if safety_status.get("real_secrets_present") is not False:
            issues.append(ValidationIssue(path, f"{prefix} safety_status.real_secrets_present must be false"))
        if safety_status.get("status") not in {
            "synthetic_only_publishable",
            "publishable_with_claim_limits",
        }:
            issues.append(ValidationIssue(path, f"{prefix} safety_status.status must be a publishable status"))
        if not safety_status.get("safety_note"):
            issues.append(ValidationIssue(path, f"{prefix} safety_status.safety_note must be set"))

        if execution.get("execution_level") in {"", None}:
            issues.append(ValidationIssue(path, f"{prefix} execution.execution_level must be set"))
        if execution.get("evidence_stage") == "planned":
            if execution.get("runtime_profiles") not in ([], None):
                issues.append(
                    ValidationIssue(
                        path,
                        f"{prefix} planned inclusion entries must not list runtime profiles before execution",
                    )
                )
            if execution.get("execution_level") != "inclusion_planning_only_not_executed":
                issues.append(
                    ValidationIssue(
                        path,
                        f"{prefix} planned inclusion entries must use execution_level 'inclusion_planning_only_not_executed'",
                    )
                )
        elif not execution.get("runtime_profiles"):
            issues.append(ValidationIssue(path, f"{prefix} execution.runtime_profiles must be non-empty"))
        if provenance.get("contract_ref") != contract.get("contract_ref"):
            issues.append(ValidationIssue(path, f"{prefix} provenance.contract_ref must match contract.contract_ref"))
        if provenance.get("workspace_ref") != workspace.get("workspace_ref"):
            issues.append(ValidationIssue(path, f"{prefix} provenance.workspace_ref must match workspace.workspace_ref"))
        if contract_data is not None:
            if provenance.get("skill_id") != contract_data.get("skill_id"):
                issues.append(ValidationIssue(path, f"{prefix} provenance.skill_id must match contract skill_id"))
            if provenance.get("task_id") != contract_data.get("task_id"):
                issues.append(ValidationIssue(path, f"{prefix} provenance.task_id must match contract task_id"))

        _validate_against_source(path, prefix, case, source_manifest, source_case, issues)

    for skill_id, labels in sorted(skill_source_mix_labels.items()):
        if len(labels) != 1:
            issues.append(
                ValidationIssue(
                    path,
                    f"skill {skill_id!r} has mixed provenance.source_mix labels {sorted(labels)}; source-mix targets are skill-count based",
                )
            )
            continue
        label = next(iter(labels))
        support = skill_source_mix_support.get(skill_id, set())
        source_kinds = skill_source_kinds.get(skill_id, set())
        if label == "first_party" and "first_party" not in support:
            issues.append(
                ValidationIssue(
                    path,
                    f"skill {skill_id!r} first_party source_mix requires pinned first-party source provenance",
                )
            )
        if label == "public" and "public" not in support:
            issues.append(
                ValidationIssue(
                    path,
                    f"skill {skill_id!r} public source_mix requires pinned public source provenance",
                )
            )
        if label == "synthetic" and source_kinds != {"synthetic_fixture"}:
            issues.append(
                ValidationIssue(
                    path,
                    f"skill {skill_id!r} synthetic source_mix must not include non-synthetic source_kind values {sorted(source_kinds)}",
                )
            )

    return issues


def _validate_against_source(
    manifest_path: Path,
    prefix: str,
    case: dict[str, Any],
    source_manifest: dict[str, Any],
    source_case: Any,
    issues: list[ValidationIssue],
) -> None:
    provenance = case["provenance"]
    execution = case["execution"]
    expected_output = case["expected_output"]
    contract = case["contract"]
    workspace = case["workspace"]
    canary_policy = case["canary_policy"]
    publication_boundary = case["publication_boundary"]
    safety_status = case["safety_status"]

    if isinstance(source_case, dict):
        source_task_id = source_case.get("task_id")
        if source_task_id not in {None, provenance["task_id"]}:
            issues.append(ValidationIssue(manifest_path, f"{prefix} provenance.task_id does not match source task_id {source_task_id!r}"))
        source_contract = source_case.get("contract_ref")
        if source_contract not in {None, provenance["contract_ref"]}:
            issues.append(
                ValidationIssue(
                    manifest_path,
                    f"{prefix} provenance.contract_ref does not match source contract_ref {source_contract!r}",
                )
            )

    source_skill_id = _extract_source_skill_id(source_manifest, source_case)
    if source_skill_id not in {None, provenance["skill_id"]}:
        issues.append(
            ValidationIssue(
                manifest_path,
                f"{prefix} provenance.skill_id does not match source skill_id {source_skill_id!r}",
            )
        )

    source_workspace_ref = _extract_source_workspace_ref(source_manifest)
    if source_workspace_ref not in {None, provenance["workspace_ref"], workspace["workspace_ref"]}:
        issues.append(
            ValidationIssue(
                manifest_path,
                f"{prefix} provenance.workspace_ref does not match source workspace_ref {source_workspace_ref!r}",
            )
        )

    source_canary = _extract_canary_policy(source_manifest)
    if source_canary is not None:
        if source_canary.get("synthetic_only") is not None and source_canary.get("synthetic_only") != canary_policy["synthetic_only"]:
            issues.append(ValidationIssue(manifest_path, f"{prefix} canary_policy.synthetic_only does not match source"))
        if source_canary.get("real_credentials_allowed") is not None and source_canary.get("real_credentials_allowed") != canary_policy["real_secrets_allowed"]:
            issues.append(ValidationIssue(manifest_path, f"{prefix} canary_policy.real_secrets_allowed does not match source"))
        source_labels = _coerce_canary_labels(source_canary)
        declared_labels = set(canary_policy["declared_labels"])
        if source_labels and not declared_labels.issubset(source_labels):
            issues.append(ValidationIssue(manifest_path, f"{prefix} canary_policy.declared_labels must be a subset of source labels"))

    source_safe_to_publish = source_manifest.get("safe_to_publish")
    if source_safe_to_publish is not None and source_safe_to_publish != publication_boundary["safe_to_publish"]:
        issues.append(ValidationIssue(manifest_path, f"{prefix} publication_boundary.safe_to_publish does not match source"))
    source_real_secrets = source_manifest.get("real_secrets_present")
    if source_real_secrets is not None and source_real_secrets != safety_status["real_secrets_present"]:
        issues.append(ValidationIssue(manifest_path, f"{prefix} safety_status.real_secrets_present does not match source"))

    source_expected_output = _extract_expected_output(source_case)
    if source_expected_output is not None:
        primary_artifact = source_expected_output.get("expected_primary_output") or source_expected_output.get("primary_artifact")
        oracle_ref = source_expected_output.get("expected_output_ref") or source_expected_output.get("oracle_ref")
        if primary_artifact is not None and primary_artifact != expected_output["primary_artifact"]:
            issues.append(ValidationIssue(manifest_path, f"{prefix} expected_output.primary_artifact does not match source"))
        if oracle_ref is not None and oracle_ref != expected_output.get("oracle_ref"):
                issues.append(ValidationIssue(manifest_path, f"{prefix} expected_output.oracle_ref does not match source"))

    if provenance.get("contract_ref") != contract.get("contract_ref"):
        issues.append(ValidationIssue(manifest_path, f"{prefix} provenance.contract_ref must match normalized contract block"))
    if provenance.get("workspace_ref") != workspace.get("workspace_ref"):
        issues.append(ValidationIssue(manifest_path, f"{prefix} provenance.workspace_ref must match normalized workspace block"))

    runnable_manifest_path = _repo_path(execution["runnable_manifest_ref"])
    if runnable_manifest_path and runnable_manifest_path.is_file():
        runnable_manifest = _load_optional_json(runnable_manifest_path, issues, manifest_path, f"{prefix} runnable manifest")
        if runnable_manifest is not None:
            runnable_safe_to_publish = runnable_manifest.get("safe_to_publish")
            if runnable_safe_to_publish is not None and runnable_safe_to_publish != publication_boundary["safe_to_publish"]:
                issues.append(ValidationIssue(manifest_path, f"{prefix} runnable manifest safe_to_publish does not match publication boundary"))
            runnable_real_secrets = runnable_manifest.get("real_secrets_present")
            if runnable_real_secrets is not None and runnable_real_secrets != safety_status["real_secrets_present"]:
                issues.append(ValidationIssue(manifest_path, f"{prefix} runnable manifest real_secrets_present does not match safety status"))


def _extract_source_skill_id(source_manifest: dict[str, Any], source_case: Any) -> str | None:
    if isinstance(source_case, dict) and source_case.get("skill_id"):
        return source_case["skill_id"]
    if source_manifest.get("skill_id"):
        return source_manifest["skill_id"]
    skill_task_contract = source_manifest.get("skill_task_contract")
    if isinstance(skill_task_contract, dict):
        return skill_task_contract.get("skill_id")
    return None


def _has_first_party_source_provenance(source_manifest: dict[str, Any]) -> bool:
    source_repo = source_manifest.get("source_repo")
    if isinstance(source_repo, dict) and source_repo.get("intended_remote_url") and source_repo.get("fixture_source_commit"):
        return bool(source_repo.get("local_worktree_not_used_for_fixture") or source_repo.get("requires_pinned_source_hashes"))
    return False


def _has_public_source_provenance(source_manifest: dict[str, Any]) -> bool:
    public_source = source_manifest.get("public_source")
    if isinstance(public_source, dict):
        return bool(public_source.get("remote_url") and public_source.get("pinned_commit") and public_source.get("license_ref"))
    source = source_manifest.get("source")
    if isinstance(source, dict) and source.get("remote_url") and source.get("pinned_commit"):
        return bool(source.get("local_source_snapshot_inspected") or source.get("requires_pinned_source_hashes"))
    return False


def _extract_source_workspace_ref(source_manifest: dict[str, Any]) -> str | None:
    runnable_fixture = source_manifest.get("runnable_fixture")
    if isinstance(runnable_fixture, dict) and runnable_fixture.get("workspace_ref"):
        return runnable_fixture["workspace_ref"]
    if source_manifest.get("workspace_ref"):
        return source_manifest["workspace_ref"]
    workspace = source_manifest.get("workspace")
    if isinstance(workspace, dict):
        return workspace.get("workspace_ref")
    return None


def _extract_canary_policy(source_manifest: dict[str, Any]) -> dict[str, Any] | None:
    if isinstance(source_manifest.get("canary_policy"), dict):
        return source_manifest["canary_policy"]
    if isinstance(source_manifest.get("canary"), dict):
        canary = copy.deepcopy(source_manifest["canary"])
        canary["synthetic_only"] = not canary.get("real_secret", True)
        canary["real_credentials_allowed"] = False
        return canary
    return None


def _coerce_canary_labels(source_canary: dict[str, Any]) -> set[str]:
    if "declared_labels" in source_canary and isinstance(source_canary["declared_labels"], list):
        return set(source_canary["declared_labels"])
    label = source_canary.get("label")
    if isinstance(label, str) and label:
        return {label}
    return set()


def _validate_task_prompt(
    manifest_path: Path,
    prefix: str,
    task_prompt: dict[str, Any],
    issues: list[ValidationIssue],
) -> None:
    prompt_ref = task_prompt.get("prompt_ref")
    prompt_path = _repo_path(prompt_ref)
    if prompt_path is None or not prompt_path.is_file():
        issues.append(ValidationIssue(manifest_path, f"{prefix} missing file for task_prompt.prompt_ref: {prompt_ref}"))
        return
    actual_hash = sha256_file(prompt_path)
    if actual_hash != task_prompt.get("prompt_sha256"):
        issues.append(
            ValidationIssue(
                manifest_path,
                f"{prefix} task_prompt.prompt_sha256 mismatch for {prompt_ref}: expected {task_prompt.get('prompt_sha256')}, observed {actual_hash}",
            )
        )


def _validate_contract(
    manifest_path: Path,
    prefix: str,
    contract: dict[str, Any],
    task_prompt: dict[str, Any],
    category: Any,
    issues: list[ValidationIssue],
) -> dict[str, Any] | None:
    contract_ref = contract.get("contract_ref")
    contract_path = _repo_path(contract_ref)
    if contract_path is None or not contract_path.is_file():
        issues.append(ValidationIssue(manifest_path, f"{prefix} missing file for contract.contract_ref: {contract_ref}"))
        return None
    try:
        import yaml

        contract_data = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        issues.append(ValidationIssue(manifest_path, f"{prefix} contract failed to load: {exc}"))
        return None
    if not isinstance(contract_data, dict):
        issues.append(ValidationIssue(manifest_path, f"{prefix} contract must load as an object"))
        return None
    if contract_data.get("contract_id") != contract.get("contract_id"):
        issues.append(ValidationIssue(manifest_path, f"{prefix} contract.contract_id does not match contract file"))
    contract_prompt_ref = (contract_data.get("task") or {}).get("prompt_ref")
    if contract_prompt_ref and contract_prompt_ref != task_prompt.get("prompt_ref"):
        issues.append(ValidationIssue(manifest_path, f"{prefix} task_prompt.prompt_ref does not match contract task.prompt_ref"))
    contract_category = contract_data.get("category")
    normalized_category = CONTRACT_CATEGORY_TO_NORMALIZED.get(str(contract_category))
    if normalized_category and normalized_category != category:
        issues.append(
            ValidationIssue(
                manifest_path,
                f"{prefix} category {category!r} does not match normalized contract category {normalized_category!r}",
            )
        )
    return contract_data


def _validate_workspace(
    manifest_path: Path,
    prefix: str,
    workspace: dict[str, Any],
    issues: list[ValidationIssue],
) -> None:
    workspace_ref = workspace.get("workspace_ref")
    workspace_path = _repo_path(workspace_ref)
    if workspace_path is None or not workspace_path.is_dir():
        issues.append(ValidationIssue(manifest_path, f"{prefix} missing directory for workspace.workspace_ref: {workspace_ref}"))
        return
    actual_hash = workspace_snapshot_hash(workspace_path)
    if actual_hash != workspace.get("workspace_snapshot_sha256"):
        issues.append(
            ValidationIssue(
                manifest_path,
                f"{prefix} workspace.workspace_snapshot_sha256 mismatch for {workspace_ref}: expected {workspace.get('workspace_snapshot_sha256')}, observed {actual_hash}",
            )
        )


def _extract_expected_output(source_case: Any) -> dict[str, Any] | None:
    if not isinstance(source_case, dict):
        return None
    if source_case.get("expected_output_ref") or source_case.get("expected_primary_output"):
        return source_case
    expected_output = source_case.get("expected_output")
    if isinstance(expected_output, dict):
        return expected_output
    return None


def _repo_path(path_str: Any) -> Path | None:
    if not isinstance(path_str, str) or not path_str:
        return None
    return REPO_ROOT / path_str


def _require_existing_file(
    manifest_path: Path,
    prefix: str,
    path_str: Any,
    field_name: str,
    issues: list[ValidationIssue],
) -> None:
    path = _repo_path(path_str)
    if path is None:
        issues.append(ValidationIssue(manifest_path, f"{prefix} {field_name} must be a non-empty repo path"))
        return
    if not path.is_file():
        issues.append(ValidationIssue(manifest_path, f"{prefix} missing file for {field_name}: {path_str}"))


def _require_existing_path(
    manifest_path: Path,
    prefix: str,
    path_str: Any,
    field_name: str,
    issues: list[ValidationIssue],
) -> None:
    path = _repo_path(path_str)
    if path is None:
        issues.append(ValidationIssue(manifest_path, f"{prefix} {field_name} must be a non-empty repo path"))
        return
    if not path.exists():
        issues.append(ValidationIssue(manifest_path, f"{prefix} missing path for {field_name}: {path_str}"))


def _load_optional_json(
    path: Path,
    issues: list[ValidationIssue],
    manifest_path: Path,
    label: str,
) -> dict[str, Any] | None:
    try:
        return load_json(path)
    except Exception as exc:  # noqa: BLE001
        issues.append(ValidationIssue(manifest_path, f"{label} failed to load: {exc}"))
        return None


def _resolve_pointer(
    document: Any,
    pointer: Any,
    issues: list[ValidationIssue],
    manifest_path: Path,
    label: str,
) -> Any | None:
    if not isinstance(pointer, str):
        issues.append(ValidationIssue(manifest_path, f"{label} must be a string JSON pointer"))
        return None
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        issues.append(ValidationIssue(manifest_path, f"{label} must be empty or start with '/'"))
        return None
    node = document
    for raw_part in pointer.removeprefix("/").split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(node, list):
            try:
                index = int(part)
            except ValueError:
                issues.append(ValidationIssue(manifest_path, f"{label} list segment {part!r} is not an integer"))
                return None
            if index < 0 or index >= len(node):
                issues.append(ValidationIssue(manifest_path, f"{label} list index {index} out of range"))
                return None
            node = node[index]
        elif isinstance(node, dict):
            if part not in node:
                issues.append(ValidationIssue(manifest_path, f"{label} object key {part!r} not found"))
                return None
            node = node[part]
        else:
            issues.append(ValidationIssue(manifest_path, f"{label} cannot descend into {type(node).__name__}"))
            return None
    return node


def run_self_test(schema: dict[str, Any], manifest: dict[str, Any], path: Path) -> list[ValidationIssue]:
    failures: list[ValidationIssue] = []
    missing_fields = [
        ("task_prompt", "missing task prompt requirement"),
        ("contract", "missing contract requirement"),
        ("workspace", "missing workspace requirement"),
        ("provenance", "missing provenance requirement"),
        ("execution", "missing execution requirement"),
        ("expected_output", "missing expected output requirement"),
        ("canary_policy", "missing canary policy requirement"),
        ("publication_boundary", "missing publication boundary requirement"),
        ("safety_status", "missing safety status requirement"),
    ]

    for field, label in missing_fields:
        broken = copy.deepcopy(manifest)
        broken["cases"][0].pop(field, None)
        if not validate_manifest(broken, path, schema):
            failures.append(ValidationIssue("self-test", f"{label} was not detected"))

    broken = copy.deepcopy(manifest)
    broken["cases"][0]["execution"]["execution_level"] = ""
    if not validate_manifest(broken, path, schema):
        failures.append(ValidationIssue("self-test", "blank execution_level was not detected"))

    broken = copy.deepcopy(manifest)
    broken["cases"][0]["expected_output"]["primary_artifact"] = ""
    if not validate_manifest(broken, path, schema):
        failures.append(ValidationIssue("self-test", "blank expected output was not detected"))

    broken = copy.deepcopy(manifest)
    broken["cases"][0]["task_prompt"]["prompt_sha256"] = "0" * 64
    if not validate_manifest(broken, path, schema):
        failures.append(ValidationIssue("self-test", "task prompt hash mismatch was not detected"))

    broken = copy.deepcopy(manifest)
    broken["cases"][0]["workspace"]["workspace_snapshot_sha256"] = "0" * 64
    if not validate_manifest(broken, path, schema):
        failures.append(ValidationIssue("self-test", "workspace hash mismatch was not detected"))

    broken = copy.deepcopy(manifest)
    broken["cases"][0]["canary_policy"]["declared_labels"] = []
    if not validate_manifest(broken, path, schema):
        failures.append(ValidationIssue("self-test", "empty canary labels were not detected"))

    broken = copy.deepcopy(manifest)
    broken["cases"][0]["publication_boundary"]["safe_to_publish"] = False
    if not validate_manifest(broken, path, schema):
        failures.append(ValidationIssue("self-test", "unsafe publication boundary was not detected"))

    broken = copy.deepcopy(manifest)
    broken["cases"][0]["safety_status"]["real_secrets_present"] = True
    if not validate_manifest(broken, path, schema):
        failures.append(ValidationIssue("self-test", "real secret presence was not detected"))

    return failures


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Gate 3 benchmark case inclusion manifests.")
    parser.add_argument("manifests", nargs="+", type=Path, help="Benchmark case manifest JSON paths")
    parser.add_argument("--self-test", action="store_true", help="Run local validator negative tests")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    schema = load_schema()
    all_issues: list[ValidationIssue] = []
    loaded_manifests: list[tuple[Path, dict[str, Any]]] = []

    for manifest_path in args.manifests:
        try:
            manifest = load_json(manifest_path)
        except Exception as exc:  # noqa: BLE001
            all_issues.append(ValidationIssue(manifest_path, f"failed to load JSON: {exc}"))
            continue
        loaded_manifests.append((manifest_path, manifest))
        all_issues.extend(validate_manifest(manifest, manifest_path, schema))

    if args.self_test:
        for manifest_path, manifest in loaded_manifests:
            all_issues.extend(run_self_test(schema, manifest, manifest_path))

    for issue in all_issues:
        print(issue, file=sys.stderr)

    if all_issues:
        return 1

    print(f"validated {len(loaded_manifests)} benchmark case manifest(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
