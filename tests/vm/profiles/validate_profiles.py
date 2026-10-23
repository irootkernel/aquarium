#!/usr/bin/env python3
"""Validate fixed Aquarium VM profiles and inventory contracts offline."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from typing import Any

PROFILE_SCHEMA = "aquarium.vm-profile/v1"
INVENTORY_SCHEMA = "aquarium.vm-inventory/v1"
VALIDATION_SCHEMA = "aquarium.vm-profile-validation/v1"

PROFILE_KEYS = frozenset(
    {
        "schema",
        "profile_id",
        "profile_revision",
        "owner",
        "platform",
        "components",
        "absent_components",
        "effective_configuration",
        "resource",
        "starting_states",
        "inputs",
        "cleanup_expectations",
        "evidence_class",
    }
)
PROFILE_OPTIONAL_KEYS = frozenset(
    {
        "absent_components",
        "effective_configuration",
        "inputs",
        "cleanup_expectations",
    }
)
COMPONENT_KEYS = frozenset(
    {
        "name",
        "role",
        "installation_scope",
        "version",
        "archive_sha256",
        "executable_sha256",
        "tree_sha256",
        "skill_tree",
        "provenance",
        "controller_service",
        "pin",
        "capabilities",
    }
)
COMPONENT_OPTIONAL_KEYS = frozenset(
    {
        "version",
        "archive_sha256",
        "executable_sha256",
        "tree_sha256",
        "skill_tree",
        "provenance",
        "controller_service",
        "pin",
        "capabilities",
    }
)
SKILL_TREE_KEYS = frozenset(
    {"name", "installation_scope", "sha256", "digest_algorithm"}
)
PROVENANCE_KEYS = frozenset(
    {"release_tag", "tag_commit", "build_revision", "archive_sha256"}
)
PLAN_KEYS = frozenset({"schema", "instance", "global_limit", "host_macos_guest_limit"})
CONTROLLER_SERVICE_KEYS = frozenset({"binary_sha256", "plan"})
PIN_KEYS = frozenset({"commit"})
CAPABILITY_KEYS = frozenset({"capabilities", "compiled_backends"})
ABSENT_COMPONENT_KEYS = frozenset({"name", "reason"})
EFFECTIVE_CONFIGURATION_KEYS = frozenset({"controller_selection", "service_limits"})
RESOURCE_KEYS = frozenset({"kind", "capacity"})
STARTING_STATE_KEYS = frozenset({"kind", "aquarium"})
INPUTS_KEYS = frozenset({"bundle_sha256"})
CLEANUP_KEYS = frozenset({"post_cleanup_inventory"})

INVENTORY_KEYS = frozenset(
    {"schema", "phase", "profile_digest", "recipe_digest", "entries"}
)
INVENTORY_ENTRY_KEYS = frozenset(
    {"relative_path", "executable", "sha256", "installation_scope"}
)
INVENTORY_PHASES = frozenset({"before", "candidate", "post_cleanup"})

ROLES = frozenset({"host", "guest"})
RESOURCE_KINDS = frozenset({"utm-macos"})
STARTING_KINDS = frozenset({"product_absent", "prior_version"})
EVIDENCE_CLASSES = frozenset(
    {"development", "candidate-integration", "release-distribution"}
)
INSTALLATION_SCOPES = frozenset(
    {
        "user-global",
        "shared-agents-skills",
        "codex-home-skills",
        "codex-plugin-cache",
        "plugin-assets",
        "project-discovery",
        "guest-path",
    }
)
RELEASE_SERVICE_PLAN_SCHEMA = "haepari.release-service-plan/v1"

MACHINE_LOCAL_KEYS = frozenset(
    {
        "vm_uuid",
        "mac_address",
        "ssh_identity",
        "ssh_mapping",
        "identity_file",
        "known_hosts",
        "known_hosts_reference",
        "connection_reference",
        "installation_id",
        "registered_resource_id",
        "haepari_home",
        "run_root",
        "vm_provisioned",
        "migration_passed",
    }
)
IDENTITY_KEYS = frozenset(
    {
        "installation_id",
        "resource_id",
        "resource_revision",
        "known_resource_ids",
        "service_plan",
        "effective_settings",
    }
)

PROFILE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9.-]*[a-z0-9]$")
SEMVER_RE = re.compile(
    r"^v?(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
    r"(?:[-+][0-9A-Za-z.-]+)?$"
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SHA256_PREFIXED_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
GIT_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
RELEASE_TAG_RE = re.compile(r"^v[0-9][0-9A-Za-z.-]*$")
SERVICE_INSTANCE_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,47}$")


def digest_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


TREE_DIGEST_ALGORITHM = "aquarium-skill-tree-sha256/v1"


def tree_digest(entries: list[dict[str, Any]]) -> str:
    """Compute the complete-tree identity over canonical sorted inventory entries.

    The digest covers every regular file through its relative POSIX path,
    executable bit, and content SHA-256, so an added, removed, changed, or
    permission-changed file changes the value.
    """
    digest = hashlib.sha256(TREE_DIGEST_ALGORITHM.encode("utf-8") + b"\0")
    for entry in sorted(entries, key=lambda item: item["relative_path"].encode()):
        executable = "1" if entry["executable"] else "0"
        line = f"{entry['relative_path']}\t{executable}\t{entry['sha256']}\n"
        digest.update(line.encode("utf-8"))
    return digest.hexdigest()


def tree_digest_from_directory(root: Any) -> str:
    """Compute the same tree digest from an installed directory.

    TASK-088 recipes call this on an installed skill tree to derive the value a
    profile pins. Symlinks and special files (FIFOs, sockets, devices) are
    rejected; directories are structural.
    """
    from pathlib import Path

    directory = Path(root)
    entries: list[dict[str, Any]] = []
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"symlink in skill tree: {path}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError(f"special file in skill tree: {path}")
        mode = path.stat().st_mode
        entries.append(
            {
                "relative_path": path.relative_to(directory).as_posix(),
                "executable": bool(mode & 0o111),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    return tree_digest(entries)


def _exact_keys(
    value: Any,
    allowed: frozenset[str],
    label: str,
    errors: list[str],
    optional: frozenset[str] = frozenset(),
) -> None:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return
    unknown = sorted(set(value) - allowed)
    if unknown:
        errors.append(f"{label} has unknown keys: {', '.join(unknown)}")
    missing = sorted(allowed - set(value) - optional)
    if missing:
        errors.append(f"{label} is missing keys: {', '.join(missing)}")


def _check_machine_local(value: Any, label: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_label = f"{label}.{key}"
            if key in MACHINE_LOCAL_KEYS:
                errors.append(f"{child_label} is a machine-local binding")
            _check_machine_local(child, child_label, errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _check_machine_local(child, f"{label}[{index}]", errors)
    elif isinstance(value, str) and value.startswith(("/", "~/")):
        errors.append(f"{label} contains an absolute or home-relative path")


def _require_semver(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not SEMVER_RE.fullmatch(value):
        errors.append(f"{label} must be a canonical semantic version")


def _require_sha256(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        errors.append(f"{label} must be a lowercase 64-character SHA-256")


def _require_sha256_prefixed(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not SHA256_PREFIXED_RE.fullmatch(value):
        errors.append(f"{label} must be sha256 followed by 64 lowercase hex digits")


def _require_commit(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not GIT_COMMIT_RE.fullmatch(value):
        errors.append(f"{label} must be a 40-character commit SHA")


def _validate_installation_scope(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, str) or value not in INSTALLATION_SCOPES:
        errors.append(f"{label} must be a known installation scope")


def _validate_service_plan(plan: Any, label: str, errors: list[str]) -> None:
    if not isinstance(plan, dict):
        errors.append(f"{label} must be an object")
        return
    _exact_keys(plan, PLAN_KEYS, label, errors)
    if plan.get("schema") != RELEASE_SERVICE_PLAN_SCHEMA:
        errors.append(f"{label}.schema must be {RELEASE_SERVICE_PLAN_SCHEMA}")
    instance = plan.get("instance")
    if not isinstance(instance, str) or not SERVICE_INSTANCE_RE.fullmatch(instance):
        errors.append(f"{label}.instance must be a valid service instance id")
    global_limit = plan.get("global_limit")
    if (
        not isinstance(global_limit, int)
        or isinstance(global_limit, bool)
        or global_limit < 1
    ):
        errors.append(f"{label}.global_limit must be a positive integer")
    host_limit = plan.get("host_macos_guest_limit")
    if (
        not isinstance(host_limit, int)
        or isinstance(host_limit, bool)
        or host_limit not in {1, 2}
    ):
        errors.append(f"{label}.host_macos_guest_limit must be 1 or 2")


def _validate_component(component: Any, index: int, errors: list[str]) -> None:
    label = f"components[{index}]"
    if not isinstance(component, dict):
        errors.append(f"{label} must be an object")
        return
    _exact_keys(
        component, COMPONENT_KEYS, label, errors, optional=COMPONENT_OPTIONAL_KEYS
    )
    name = component.get("name")
    if not isinstance(name, str) or not name:
        errors.append(f"{label}.name must be a non-empty string")
    role = component.get("role")
    if role not in ROLES:
        errors.append(f"{label}.role must be host or guest")
    _validate_installation_scope(
        component.get("installation_scope"), f"{label}.installation_scope", errors
    )
    identity_axes = 0
    if "version" in component:
        _require_semver(component["version"], f"{label}.version", errors)
        identity_axes += 1
    for field in ("archive_sha256", "tree_sha256"):
        if field in component:
            _require_sha256(component[field], f"{label}.{field}", errors)
            identity_axes += 1
    if "executable_sha256" in component:
        _require_sha256_prefixed(
            component["executable_sha256"], f"{label}.executable_sha256", errors
        )
        identity_axes += 1
    if "skill_tree" in component:
        skill_tree = component["skill_tree"]
        skill_label = f"{label}.skill_tree"
        if isinstance(skill_tree, dict):
            _exact_keys(skill_tree, SKILL_TREE_KEYS, skill_label, errors)
            if not isinstance(skill_tree.get("name"), str) or not skill_tree["name"]:
                errors.append(f"{skill_label}.name must be a non-empty string")
            _validate_installation_scope(
                skill_tree.get("installation_scope"),
                f"{skill_label}.installation_scope",
                errors,
            )
            _require_sha256(skill_tree.get("sha256"), f"{skill_label}.sha256", errors)
            if skill_tree.get("digest_algorithm") != TREE_DIGEST_ALGORITHM:
                errors.append(
                    f"{skill_label}.digest_algorithm must be {TREE_DIGEST_ALGORITHM}"
                )
        else:
            errors.append(f"{skill_label} must be an object")
        identity_axes += 1
    if "provenance" in component:
        provenance = component["provenance"]
        provenance_label = f"{label}.provenance"
        if isinstance(provenance, dict):
            unknown = sorted(set(provenance) - PROVENANCE_KEYS)
            if unknown:
                errors.append(
                    f"{provenance_label} has unknown keys: {', '.join(unknown)}"
                )
            release_tag = provenance.get("release_tag")
            if release_tag is not None and (
                not isinstance(release_tag, str)
                or not RELEASE_TAG_RE.fullmatch(release_tag)
            ):
                errors.append(f"{provenance_label}.release_tag must be a release tag")
            for field in ("tag_commit", "build_revision"):
                if field in provenance:
                    _require_commit(
                        provenance[field], f"{provenance_label}.{field}", errors
                    )
                    identity_axes += 1
            if "archive_sha256" in provenance:
                _require_sha256(
                    provenance["archive_sha256"],
                    f"{provenance_label}.archive_sha256",
                    errors,
                )
                identity_axes += 1
        else:
            errors.append(f"{provenance_label} must be an object")
    if "controller_service" in component:
        controller_service = component["controller_service"]
        service_label = f"{label}.controller_service"
        if isinstance(controller_service, dict):
            _exact_keys(
                controller_service, CONTROLLER_SERVICE_KEYS, service_label, errors
            )
            _require_sha256_prefixed(
                controller_service.get("binary_sha256"),
                f"{service_label}.binary_sha256",
                errors,
            )
            _validate_service_plan(
                controller_service.get("plan"), f"{service_label}.plan", errors
            )
        else:
            errors.append(f"{service_label} must be an object")
    if "pin" in component:
        pin = component["pin"]
        if isinstance(pin, dict):
            _exact_keys(pin, PIN_KEYS, f"{label}.pin", errors)
            _require_commit(pin.get("commit"), f"{label}.pin.commit", errors)
            identity_axes += 1
        else:
            errors.append(f"{label}.pin must be an object")
    if "capabilities" in component:
        capabilities = component["capabilities"]
        capabilities_label = f"{label}.capabilities"
        if isinstance(capabilities, dict):
            unknown = sorted(set(capabilities) - CAPABILITY_KEYS)
            if unknown:
                errors.append(
                    f"{capabilities_label} has unknown keys: {', '.join(unknown)}"
                )
            for field in ("capabilities", "compiled_backends"):
                if field in capabilities and not isinstance(capabilities[field], list):
                    errors.append(f"{capabilities_label}.{field} must be a list")
        else:
            errors.append(f"{capabilities_label} must be an object")
    if identity_axes == 0:
        errors.append(f"{label} must pin at least one concrete identity axis")


def _validate_limit_values(limits: Any, label: str, errors: list[str]) -> None:
    if not isinstance(limits, dict):
        errors.append(f"{label} must be an object")
        return
    unknown = sorted(set(limits) - {"global_limit", "host_macos_guest_limit"})
    if unknown:
        errors.append(f"{label} has unknown keys: {', '.join(unknown)}")
    global_limit = limits.get("global_limit")
    if (
        not isinstance(global_limit, int)
        or isinstance(global_limit, bool)
        or global_limit < 1
    ):
        errors.append(f"{label}.global_limit must be a positive integer")
    host_limit = limits.get("host_macos_guest_limit")
    if (
        not isinstance(host_limit, int)
        or isinstance(host_limit, bool)
        or host_limit not in {1, 2}
    ):
        errors.append(f"{label}.host_macos_guest_limit must be 1 or 2")


def _validate_service_limits_consistency(
    components: Any, effective: Any, errors: list[str]
) -> None:
    if not isinstance(components, list) or not isinstance(effective, dict):
        return
    limits = effective.get("service_limits")
    if not isinstance(limits, dict):
        return
    for component in components:
        if not isinstance(component, dict) or component.get("name") != "haepari":
            continue
        service = component.get("controller_service")
        if not isinstance(service, dict) or not isinstance(service.get("plan"), dict):
            continue
        plan_limits = {
            key: service["plan"].get(key)
            for key in ("global_limit", "host_macos_guest_limit")
        }
        if limits != plan_limits:
            errors.append(
                "profile.effective_configuration.service_limits must match the "
                "haepari controller service plan limits"
            )
        return


def validate_profile(document: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(document, dict):
        return ["profile must be an object"]
    _exact_keys(
        document, PROFILE_KEYS, "profile", errors, optional=PROFILE_OPTIONAL_KEYS
    )
    if document.get("schema") != PROFILE_SCHEMA:
        errors.append(f"profile.schema must be {PROFILE_SCHEMA}")
    profile_id = document.get("profile_id")
    if not isinstance(profile_id, str) or not PROFILE_ID_RE.fullmatch(profile_id):
        errors.append("profile.profile_id must be a stable lowercase identity")
    revision = document.get("profile_revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
        errors.append("profile.profile_revision must be a positive integer")
    if not isinstance(document.get("owner"), str) or not document["owner"]:
        errors.append("profile.owner must be a non-empty string")
    if document.get("platform") != "darwin/arm64":
        errors.append("profile.platform must be darwin/arm64")
    components = document.get("components")
    if not isinstance(components, list) or not components:
        errors.append("profile.components must be a non-empty list")
        components = []
    names: set[str] = set()
    for index, component in enumerate(components):
        _validate_component(component, index, errors)
        if isinstance(component, dict) and isinstance(component.get("name"), str):
            if component["name"] in names:
                errors.append(
                    f"components[{index}].name duplicates an earlier component"
                )
            names.add(component["name"])
    absent = document.get("absent_components", [])
    if not isinstance(absent, list):
        errors.append("profile.absent_components must be a list")
    else:
        for index, entry in enumerate(absent):
            label = f"absent_components[{index}]"
            if isinstance(entry, dict):
                _exact_keys(entry, ABSENT_COMPONENT_KEYS, label, errors)
                name = entry.get("name")
                if not isinstance(name, str) or not name:
                    errors.append(f"{label}.name must be a non-empty string")
                elif name in names:
                    errors.append(f"{label}.name is also declared present")
                if not isinstance(entry.get("reason"), str) or not entry["reason"]:
                    errors.append(f"{label}.reason must be a non-empty string")
            else:
                errors.append(f"{label} must be an object")
    effective = document.get("effective_configuration")
    if effective is not None:
        if isinstance(effective, dict):
            unknown = sorted(set(effective) - EFFECTIVE_CONFIGURATION_KEYS)
            if unknown:
                errors.append(
                    "profile.effective_configuration has unknown keys: "
                    + ", ".join(unknown)
                )
            selection = effective.get("controller_selection")
            if selection is not None and selection != "explicit_haepari_home":
                errors.append(
                    "profile.effective_configuration.controller_selection must be "
                    "explicit_haepari_home"
                )
            limits = effective.get("service_limits")
            if limits is not None:
                _validate_limit_values(
                    limits,
                    "profile.effective_configuration.service_limits",
                    errors,
                )
                _validate_service_limits_consistency(components, effective, errors)
        else:
            errors.append("profile.effective_configuration must be an object")
    resource = document.get("resource")
    if not isinstance(resource, dict):
        errors.append("profile.resource must be an object")
    else:
        _exact_keys(resource, RESOURCE_KEYS, "profile.resource", errors)
        if resource.get("kind") not in RESOURCE_KINDS:
            errors.append("profile.resource.kind must be utm-macos")
        if resource.get("capacity") != 1:
            errors.append("profile.resource.capacity must be 1")
    starting_states = document.get("starting_states")
    if not isinstance(starting_states, list) or not starting_states:
        errors.append("profile.starting_states must be a non-empty list")
    else:
        for index, state in enumerate(starting_states):
            label = f"starting_states[{index}]"
            if isinstance(state, dict):
                _exact_keys(
                    state, STARTING_STATE_KEYS, label, errors, optional={"aquarium"}
                )
                kind = state.get("kind")
                if kind not in STARTING_KINDS:
                    errors.append(
                        f"{label}.kind must be product_absent or prior_version"
                    )
                if kind == "prior_version":
                    if "aquarium" not in state:
                        errors.append(f"{label} must name the prior aquarium version")
                    else:
                        _require_semver(state["aquarium"], f"{label}.aquarium", errors)
                if kind == "product_absent" and "aquarium" in state:
                    errors.append(f"{label} must not name an aquarium version")
            else:
                errors.append(f"{label} must be an object")
    inputs = document.get("inputs")
    if inputs is not None:
        if isinstance(inputs, dict):
            unknown = sorted(set(inputs) - INPUTS_KEYS)
            if unknown:
                errors.append(f"profile.inputs has unknown keys: {', '.join(unknown)}")
            if "bundle_sha256" in inputs:
                _require_sha256(
                    inputs["bundle_sha256"], "profile.inputs.bundle_sha256", errors
                )
        else:
            errors.append("profile.inputs must be an object")
    cleanup = document.get("cleanup_expectations")
    if cleanup is not None:
        if isinstance(cleanup, dict):
            unknown = sorted(set(cleanup) - CLEANUP_KEYS)
            if unknown:
                errors.append(
                    "profile.cleanup_expectations has unknown keys: "
                    + ", ".join(unknown)
                )
            if cleanup.get("post_cleanup_inventory") != "required":
                errors.append(
                    "profile.cleanup_expectations.post_cleanup_inventory must be "
                    "'required'"
                )
        else:
            errors.append("profile.cleanup_expectations must be an object")
    if document.get("evidence_class") not in EVIDENCE_CLASSES:
        errors.append("profile.evidence_class must be a supported evidence class")
    _check_machine_local(document, "profile", errors)
    return errors


def validate_inventory(document: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(document, dict):
        return ["inventory must be an object"]
    _exact_keys(document, INVENTORY_KEYS, "inventory", errors)
    if document.get("schema") != INVENTORY_SCHEMA:
        errors.append(f"inventory.schema must be {INVENTORY_SCHEMA}")
    if document.get("phase") not in INVENTORY_PHASES:
        errors.append("inventory.phase must be before, candidate, or post_cleanup")
    for field in ("profile_digest", "recipe_digest"):
        _require_sha256(document.get(field), f"inventory.{field}", errors)
    entries = document.get("entries")
    if not isinstance(entries, list):
        errors.append("inventory.entries must be a list")
    else:
        seen: set[tuple[str, str]] = set()
        for index, entry in enumerate(entries):
            label = f"inventory.entries[{index}]"
            if not isinstance(entry, dict):
                errors.append(f"{label} must be an object")
                continue
            _exact_keys(entry, INVENTORY_ENTRY_KEYS, label, errors)
            path = entry.get("relative_path")
            scope = entry.get("installation_scope")
            if not isinstance(path, str) or not path:
                errors.append(f"{label}.relative_path must be a non-empty string")
            elif (
                path.startswith("/")
                or "\\" in path
                or any(part in {"", ".", ".."} for part in path.split("/"))
            ):
                errors.append(
                    f"{label}.relative_path must be a safe relative POSIX path"
                )
            elif isinstance(scope, str) and (scope, path) in seen:
                errors.append(f"{label} duplicates the {scope} entry for {path}")
            elif isinstance(scope, str):
                seen.add((scope, path))
            if not isinstance(entry.get("executable"), bool):
                errors.append(f"{label}.executable must be a boolean")
            _require_sha256(entry.get("sha256"), f"{label}.sha256", errors)
            _validate_installation_scope(
                entry.get("installation_scope"),
                f"{label}.installation_scope",
                errors,
            )
    _check_machine_local(document, "inventory", errors)
    return errors


def _inventory_entry_key(entry: dict[str, Any]) -> tuple[str, str] | None:
    scope = entry.get("installation_scope")
    path = entry.get("relative_path")
    if isinstance(scope, str) and isinstance(path, str):
        return (scope, path)
    return None


def _entry_identity(key: tuple[str, str]) -> str:
    scope, path = key
    return f"{scope}:{path}"


def compare_inventories(before: Any, candidate: Any) -> dict[str, list[str]]:
    before_entries: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in before.get("entries", []):
        if not isinstance(entry, dict):
            continue
        key = _inventory_entry_key(entry)
        if key is not None:
            before_entries[key] = entry
    candidate_entries: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in candidate.get("entries", []):
        if not isinstance(entry, dict):
            continue
        key = _inventory_entry_key(entry)
        if key is not None:
            candidate_entries[key] = entry
    missing = sorted(
        _entry_identity(key) for key in set(before_entries) - set(candidate_entries)
    )
    added = sorted(
        _entry_identity(key) for key in set(candidate_entries) - set(before_entries)
    )
    changed = sorted(
        _entry_identity(key)
        for key in set(before_entries) & set(candidate_entries)
        if before_entries[key].get("sha256") != candidate_entries[key].get("sha256")
    )
    executable_bit_changed = sorted(
        _entry_identity(key)
        for key in set(before_entries) & set(candidate_entries)
        if before_entries[key].get("sha256") == candidate_entries[key].get("sha256")
        and before_entries[key].get("executable")
        != candidate_entries[key].get("executable")
    )
    return {
        "missing": missing,
        "added": added,
        "changed": changed,
        "executable_bit_changed": executable_bit_changed,
    }


def apply_override(base: Any, override: Any) -> tuple[dict[str, Any] | None, list[str]]:
    errors = validate_profile(override)
    if errors:
        return None, [f"override profile is invalid: {error}" for error in errors]
    if not isinstance(base, dict):
        return None, ["base profile must be an object"]
    merged = dict(base)
    components = []
    replaced: set[str] = set()
    for component in base.get("components", []):
        if not isinstance(component, dict):
            components.append(component)
            continue
        override_component = next(
            (
                item
                for item in override.get("components", [])
                if isinstance(item, dict) and item.get("name") == component.get("name")
            ),
            None,
        )
        if override_component is not None:
            components.append(override_component)
            replaced.add(component.get("name"))
        else:
            components.append(component)
    for component in override.get("components", []):
        if isinstance(component, dict) and component.get("name") not in replaced:
            components.append(component)
    merged["components"] = components
    # A derived profile is a new file: its identity comes from the override,
    # which is itself a validated profile.
    merged["profile_id"] = override.get("profile_id")
    merged["profile_revision"] = override.get("profile_revision")
    errors = validate_profile(merged)
    if errors:
        return None, errors
    return merged, []


def skill_only_override_errors(
    base: Any, override: Any, component_name: str
) -> list[str]:
    errors: list[str] = []
    base_component = next(
        (
            component
            for component in base.get("components", [])
            if isinstance(component, dict) and component.get("name") == component_name
        ),
        None,
    )
    override_component = next(
        (
            component
            for component in override.get("components", [])
            if isinstance(component, dict) and component.get("name") == component_name
        ),
        None,
    )
    if base_component is None or override_component is None:
        return [f"component {component_name} is missing from base or override"]
    if override_component.get("role") != base_component.get("role"):
        errors.append(f"component {component_name} changed its role")
    if override_component.get("installation_scope") != base_component.get(
        "installation_scope"
    ):
        errors.append(f"component {component_name} changed its installation scope")
    for field in (
        "version",
        "archive_sha256",
        "executable_sha256",
        "tree_sha256",
        "provenance",
        "controller_service",
        "pin",
        "capabilities",
    ):
        if override_component.get(field) != base_component.get(field):
            errors.append(
                f"component {component_name} changed {field}; a skill-only override "
                "must retain every non-skill pin"
            )
    if override_component.get("skill_tree") == base_component.get("skill_tree"):
        errors.append(f"component {component_name} did not change its skill tree")
    return errors


def check_identity(recorded: Any, observed: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(recorded, dict) or not isinstance(observed, dict):
        return ["recorded and observed identities must be objects"]
    for label, value in (("recorded", recorded), ("observed", observed)):
        unknown = sorted(set(value) - IDENTITY_KEYS)
        if unknown:
            errors.append(f"{label} identity has unknown keys: {', '.join(unknown)}")
    recorded_id = recorded.get("installation_id")
    observed_id = observed.get("installation_id")
    if isinstance(recorded_id, str) and isinstance(observed_id, str):
        if recorded_id != observed_id:
            errors.append(
                f"installation_id_mismatch: recorded {recorded_id}, observed "
                f"{observed_id}"
            )
    elif isinstance(recorded_id, str) and observed_id is None:
        errors.append("installation_id_unobserved: no surface reported the identity")
    resource_id = recorded.get("resource_id")
    if isinstance(resource_id, str):
        known = observed.get("known_resource_ids")
        if isinstance(known, list) and resource_id not in known:
            errors.append(f"resource_unknown: {resource_id} is not registered")
    recorded_revision = recorded.get("resource_revision")
    observed_revision = observed.get("resource_revision")
    if (
        isinstance(recorded_revision, int)
        and isinstance(observed_revision, int)
        and recorded_revision != observed_revision
    ):
        errors.append(
            f"resource_revision_changed: recorded {recorded_revision}, observed "
            f"{observed_revision}"
        )
    if recorded.get("service_plan") != observed.get("service_plan"):
        errors.append("effective_settings_drift: service plan identity changed")
    if recorded.get("effective_settings") != observed.get("effective_settings"):
        errors.append("settings_drift: effective settings changed")
    return errors


def _load_document(path: str) -> Any:
    with open(path, "rb") as handle:
        return json.loads(handle.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("documents", nargs="+", help="Profile or inventory JSON files")
    arguments = parser.parse_args()
    results = []
    failed = False
    for path in arguments.documents:
        try:
            document = _load_document(path)
        except (OSError, ValueError) as error:
            results.append({"path": path, "errors": [f"unreadable document: {error}"]})
            failed = True
            continue
        if isinstance(document, dict) and document.get("schema") == INVENTORY_SCHEMA:
            errors = validate_inventory(document)
        else:
            errors = validate_profile(document)
        if errors:
            failed = True
        results.append({"path": path, "errors": errors})
    print(json.dumps({"schema_version": VALIDATION_SCHEMA, "documents": results}))
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
