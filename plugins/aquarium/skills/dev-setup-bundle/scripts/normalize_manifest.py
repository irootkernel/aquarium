"""Normalize an external Aquarium setup-bundle manifest without mutating it."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError as error:
    if error.name != "yaml":
        raise
    yaml = None  # type: ignore[assignment]

INPUT_SCHEMA = "aquarium.dev-setup-bundle/v1"
OUTPUT_SCHEMA = "aquarium-dev-setup-bundle-plan.v1"
ERROR_SCHEMA = "aquarium-dev-setup-bundle-error.v1"
TOOLS = ("sanho", "mulgae", "gaori", "podway", "ouroboros", "lora", "deslop")
PROJECT_MCP_TOOLS = ("mulgae", "gaori")
AGENTS_GUIDANCE = ("skip", "propose")
TOP_LEVEL_KEYS = ("schema", "defaults", "targets")
DEFAULT_KEYS = ("tools", "project_mcp", "agents_guidance")
TARGET_KEYS = (
    "path",
    "include",
    "exclude",
    "project_mcp_include",
    "project_mcp_exclude",
    "agents_guidance",
)
COMMAND_TIMEOUT_SECONDS = 10.0
MINIMUM_PYTHON_VERSION = (3, 10)
GIT_REPOSITORY_ENVIRONMENT_VARIABLES = frozenset(
    {
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CEILING_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_CONFIG",
        "GIT_CONFIG_COUNT",
        "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_NOSYSTEM",
        "GIT_CONFIG_PARAMETERS",
        "GIT_CONFIG_SYSTEM",
        "GIT_DIR",
        "GIT_DISCOVERY_ACROSS_FILESYSTEM",
        "GIT_GRAFT_FILE",
        "GIT_IMPLICIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_NAMESPACE",
        "GIT_NO_REPLACE_OBJECTS",
        "GIT_OBJECT_DIRECTORY",
        "GIT_PREFIX",
        "GIT_REPLACE_REF_BASE",
        "GIT_SHALLOW_FILE",
        "GIT_WORK_TREE",
    }
)


class ManifestError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ManifestError("invalid_arguments", message)


def fail_manifest(code: str, message: str) -> None:
    raise ManifestError(code, message)


def require_python() -> None:
    if sys.version_info < MINIMUM_PYTHON_VERSION:
        found = ".".join(str(part) for part in sys.version_info[:3])
        fail_manifest(
            "runtime_dependency_unsupported",
            f"Python 3.10 or newer is required; found {found}",
        )


def require_pyyaml() -> Any:
    if yaml is None:
        fail_manifest(
            "runtime_dependency_missing",
            "PyYAML 6.x is required; install it separately before running this skill",
        )

    version = str(getattr(yaml, "__version__", ""))
    match = re.fullmatch(r"(\d+)\.(\d+)(?:\..*)?", version)
    if not match or int(match.group(1)) != 6:
        fail_manifest(
            "runtime_dependency_unsupported",
            f"PyYAML 6.x is required; found {version or 'unknown'}",
        )
    return yaml


def load_yaml_strict(payload: bytes) -> Any:
    yaml_module = require_pyyaml()

    class StrictSafeLoader(yaml_module.SafeLoader):
        def compose_node(self, parent: Any, index: Any) -> Any:
            if self.check_event(yaml_module.AliasEvent):
                event = self.peek_event()
                raise yaml_module.constructor.ConstructorError(
                    None,
                    None,
                    "YAML aliases are not allowed",
                    event.start_mark,
                )
            return super().compose_node(parent, index)

        def construct_mapping(self, node: Any, deep: bool = False) -> dict[Any, Any]:
            if not isinstance(node, yaml_module.MappingNode):
                raise yaml_module.constructor.ConstructorError(
                    None,
                    None,
                    f"expected a mapping node, found {node.id}",
                    node.start_mark,
                )

            if any(
                key_node.tag == "tag:yaml.org,2002:merge"
                for key_node, _value_node in node.value
            ):
                raise yaml_module.constructor.ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    "YAML merge keys are not allowed",
                    node.start_mark,
                )

            self.flatten_mapping(node)
            mapping: dict[Any, Any] = {}
            for key_node, value_node in node.value:
                key = self.construct_object(key_node, deep=deep)
                try:
                    duplicate = key in mapping
                except TypeError as error:
                    raise yaml_module.constructor.ConstructorError(
                        "while constructing a mapping",
                        node.start_mark,
                        "found an unhashable key",
                        key_node.start_mark,
                    ) from error
                if duplicate:
                    raise yaml_module.constructor.ConstructorError(
                        "while constructing a mapping",
                        node.start_mark,
                        f"found duplicate key {key!r}",
                        key_node.start_mark,
                    )
                mapping[key] = self.construct_object(value_node, deep=deep)
            return mapping

    try:
        return yaml_module.load(payload, Loader=StrictSafeLoader)
    except yaml_module.YAMLError as error:
        fail_manifest(
            "invalid_yaml", f"manifest YAML is invalid: {type(error).__name__}"
        )


def require_mapping(value: Any, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail_manifest("invalid_type", f"{location} must be a mapping")
    return value


def require_exact_keys(
    mapping: dict[str, Any],
    allowed: tuple[str, ...],
    required: tuple[str, ...],
    location: str,
) -> None:
    keys = list(mapping)
    if not all(isinstance(key, str) for key in keys):
        fail_manifest("invalid_key", f"{location} keys must be strings")

    unknown = sorted(set(keys) - set(allowed))
    missing = sorted(set(required) - set(keys))
    if unknown:
        fail_manifest(
            "unknown_key", f"{location} has unknown keys: {', '.join(unknown)}"
        )
    if missing:
        fail_manifest(
            "missing_key", f"{location} is missing keys: {', '.join(missing)}"
        )


def require_string_list(
    value: Any, location: str, allowed: tuple[str, ...]
) -> list[str]:
    if not isinstance(value, list):
        fail_manifest("invalid_type", f"{location} must be a sequence")
    if not all(isinstance(item, str) for item in value):
        fail_manifest("invalid_type", f"{location} must contain only strings")
    if len(set(value)) != len(value):
        fail_manifest("duplicate_value", f"{location} must not contain duplicates")

    unsupported = sorted(set(value) - set(allowed))
    if unsupported:
        fail_manifest(
            "unsupported_value",
            f"{location} has unsupported values: {', '.join(unsupported)}",
        )
    return value


def require_agents_guidance(value: Any, location: str) -> str:
    if value not in AGENTS_GUIDANCE:
        fail_manifest("unsupported_value", f"{location} must be skip or propose")
    return value


def ordered(values: list[str], allowed: tuple[str, ...]) -> list[str]:
    return [value for value in allowed if value in values]


def normalize_selection(
    defaults: dict[str, Any], target: dict[str, Any], index: int
) -> dict[str, Any]:
    include_tools = require_string_list(
        target.get("include", []), f"targets[{index}].include", TOOLS
    )
    exclude_tools = require_string_list(
        target.get("exclude", []), f"targets[{index}].exclude", TOOLS
    )
    tool_conflicts = sorted(set(include_tools) & set(exclude_tools))
    if tool_conflicts:
        fail_manifest(
            "conflicting_override",
            f"targets[{index}] includes and excludes: {', '.join(tool_conflicts)}",
        )

    mcp_include = require_string_list(
        target.get("project_mcp_include", []),
        f"targets[{index}].project_mcp_include",
        PROJECT_MCP_TOOLS,
    )
    mcp_exclude = require_string_list(
        target.get("project_mcp_exclude", []),
        f"targets[{index}].project_mcp_exclude",
        PROJECT_MCP_TOOLS,
    )
    mcp_conflicts = sorted(set(mcp_include) & set(mcp_exclude))
    if mcp_conflicts:
        fail_manifest(
            "conflicting_override",
            f"targets[{index}] includes and excludes project MCP: {', '.join(mcp_conflicts)}",
        )

    tools = ordered(
        [
            tool
            for tool in dict.fromkeys(defaults["tools"] + include_tools)
            if tool not in exclude_tools
        ],
        TOOLS,
    )
    if not tools:
        fail_manifest(
            "empty_selection", f"targets[{index}] must select at least one tool"
        )

    project_mcp = ordered(
        list(dict.fromkeys(defaults["project_mcp"] + mcp_include)),
        PROJECT_MCP_TOOLS,
    )
    project_mcp = [tool for tool in project_mcp if tool not in mcp_exclude]
    missing_tools = sorted(set(project_mcp) - set(tools))
    if missing_tools:
        fail_manifest(
            "invalid_mcp_selection",
            f"targets[{index}] project MCP is not an effective tool: {', '.join(missing_tools)}",
        )

    return {
        "tools": tools,
        "project_mcp": project_mcp,
        "agents_guidance": require_agents_guidance(
            target.get("agents_guidance", defaults["agents_guidance"]),
            f"targets[{index}].agents_guidance",
        ),
    }


def clean_git_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for name in list(environment):
        if name in GIT_REPOSITORY_ENVIRONMENT_VARIABLES or name.startswith(
            ("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")
        ):
            environment.pop(name, None)
    environment["LANG"] = "C"
    environment["LC_ALL"] = "C"
    return environment


def resolve_repository(
    path_value: str, manifest_directory: Path
) -> tuple[str | None, str | None, list[str]]:
    candidate = Path(path_value)
    expanded = candidate if candidate.is_absolute() else manifest_directory / candidate
    if not expanded.exists():
        return None, None, ["target_not_found"]

    try:
        completed = subprocess.run(
            [
                "git",
                "-C",
                str(expanded),
                "rev-parse",
                "--path-format=absolute",
                "--show-toplevel",
                "--git-common-dir",
            ],
            env=clean_git_environment(),
            check=False,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None, None, ["target_unresolvable"]
    if completed.returncode != 0:
        return None, None, ["target_not_git_repository"]

    resolved_paths = completed.stdout.splitlines()
    if len(resolved_paths) != 2:
        return None, None, ["target_unresolvable"]
    root = Path(resolved_paths[0])
    common_directory = Path(resolved_paths[1])
    if not root.is_dir() or not common_directory.is_dir():
        return None, None, ["target_not_git_repository"]
    try:
        return (
            str(root.resolve(strict=True)),
            str(common_directory.resolve(strict=True)),
            [],
        )
    except OSError:
        return None, None, ["target_unresolvable"]


def normalize_manifest(path: str) -> dict[str, Any]:
    require_python()
    require_pyyaml()
    manifest_path = Path(path).resolve()
    if not manifest_path.is_file() or not os.access(manifest_path, os.R_OK):
        fail_manifest("manifest_not_found", "manifest must be a readable regular file")

    try:
        payload = manifest_path.read_bytes()
    except OSError:
        fail_manifest("manifest_not_found", "manifest must be a readable regular file")
    document = load_yaml_strict(payload)
    root = require_mapping(document, "manifest")
    require_exact_keys(root, TOP_LEVEL_KEYS, TOP_LEVEL_KEYS, "manifest")
    if root["schema"] != INPUT_SCHEMA:
        fail_manifest("unsupported_schema", f"schema must be {INPUT_SCHEMA}")

    defaults_input = require_mapping(root["defaults"], "defaults")
    require_exact_keys(defaults_input, DEFAULT_KEYS, DEFAULT_KEYS, "defaults")
    defaults = {
        "tools": require_string_list(defaults_input["tools"], "defaults.tools", TOOLS),
        "project_mcp": require_string_list(
            defaults_input["project_mcp"],
            "defaults.project_mcp",
            PROJECT_MCP_TOOLS,
        ),
        "agents_guidance": require_agents_guidance(
            defaults_input["agents_guidance"], "defaults.agents_guidance"
        ),
    }

    targets_input = root["targets"]
    if not isinstance(targets_input, list) or not targets_input:
        fail_manifest("invalid_type", "targets must be a non-empty sequence")

    validated_targets: list[dict[str, Any]] = []
    for index, target_input in enumerate(targets_input):
        target = require_mapping(target_input, f"targets[{index}]")
        require_exact_keys(target, TARGET_KEYS, ("path",), f"targets[{index}]")
        path_value = target["path"]
        if not isinstance(path_value, str) or not path_value:
            fail_manifest(
                "invalid_type",
                f"targets[{index}].path must be a non-empty string",
            )

        selection = normalize_selection(defaults, target, index)
        validated_targets.append(
            {
                "index": index,
                "path": path_value,
                **selection,
            }
        )

    targets: list[dict[str, Any]] = []
    repository_identities: list[str | None] = []
    for target in validated_targets:
        repository, repository_identity, reason_codes = resolve_repository(
            target["path"], manifest_path.parent
        )
        repository_identities.append(repository_identity)
        targets.append(
            {
                "repository": repository,
                "status": "ready" if not reason_codes else "invalid",
                "reason_codes": reason_codes,
                **target,
            }
        )

    identity_counts: dict[str, int] = {}
    for identity in repository_identities:
        if identity is not None:
            identity_counts[identity] = identity_counts.get(identity, 0) + 1
    duplicate_identities = {
        identity for identity, count in identity_counts.items() if count > 1
    }
    for target, identity in zip(targets, repository_identities, strict=True):
        if identity in duplicate_identities:
            target["status"] = "invalid"
            target["reason_codes"] = ["duplicate_git_root"]

    ready_targets = [target for target in targets if target["status"] == "ready"]
    return {
        "schema_version": OUTPUT_SCHEMA,
        "manifest": {
            "path": str(manifest_path),
            "sha256": hashlib.sha256(payload).hexdigest(),
        },
        "shared_tools": ordered(
            list(
                dict.fromkeys(
                    tool for target in ready_targets for tool in target["tools"]
                )
            ),
            TOOLS,
        ),
        "targets": targets,
    }


def parse_arguments() -> argparse.Namespace:
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="External bundle manifest")
    return parser.parse_args()


def emit(payload: dict[str, Any], *, stream: Any = sys.stdout) -> None:
    json.dump(payload, stream, indent=2)
    stream.write("\n")


def main() -> int:
    try:
        require_python()
        arguments = parse_arguments()
        emit(normalize_manifest(arguments.manifest))
        return 0
    except ManifestError as error:
        emit(
            {
                "schema_version": ERROR_SCHEMA,
                "error": {"code": error.code, "message": str(error)},
            },
            stream=sys.stderr,
        )
        return 2
    except Exception as error:  # noqa: BLE001 - keep the CLI error boundary JSON-only
        emit(
            {
                "schema_version": ERROR_SCHEMA,
                "error": {
                    "code": "normalization_failed",
                    "message": "unexpected manifest normalization failure",
                    "type": type(error).__name__,
                },
            },
            stream=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
