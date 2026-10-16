"""Selected known-source admission alongside existing legacy handler contracts."""

import json
import platform
import re
import subprocess
from pathlib import Path

import yaml
from adaptive_bundles import (
    BundleError,
    contained,
    publish_bundle,
    read_regular,
    resolve_bundle,
    sha256,
)
from adaptive_definitions import (
    ASSETS,
    FAMILY_ENTRYPOINTS,
    canonical_json,
    definition_id,
    native_key,
    parse_definition,
    validate_definition,
)


class NativeClient:
    """Read-only native checks, preserving error codes and exact source identity."""

    def __init__(self, repository, executable, timeout=30, environment=None):
        self.repository = Path(repository).resolve()
        self.executable = str(executable)
        self.timeout = timeout
        self.environment = environment

    def read(self, arguments, command, schemas):
        try:
            result = subprocess.run(
                [
                    self.executable,
                    *(
                        []
                        if command == "version" or command.startswith("procedure.")
                        else ["--worktree", str(self.repository)]
                    ),
                    "--json",
                    *arguments,
                ],
                capture_output=True,
                timeout=self.timeout,
                check=False,
                env=self.environment,
                cwd=self.repository,
            )
            envelope = json.loads(result.stdout)
        except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
            raise BundleError(
                "runtime-failure", f"Native {command} result unavailable"
            ) from exc
        if not isinstance(envelope, dict):
            raise BundleError(
                "unsupported-runtime", f"Native {command} envelope is not an object"
            )
        if envelope.get("schema") == "podway.error/v2":
            code = envelope.get("code")
            if not isinstance(code, str) or not code:
                raise BundleError(
                    "unsupported-runtime", f"Native {command} error lacks its code"
                )
            raise BundleError(
                code,
                f"Native {command} refused",
                {"native_exit_status": result.returncode},
            )
        payload = envelope.get("result")
        if (
            envelope.get("schema") != "podway.output/v4"
            or envelope.get("command") != command
            or not isinstance(payload, dict)
            or (
                schemas is not None
                and (
                    not isinstance(payload.get("schema"), str)
                    or payload["schema"] not in schemas
                )
            )
        ):
            raise BundleError(
                "unsupported-runtime", f"Native {command} machine contract differs"
            )
        if command == "procedure.check":
            if not isinstance(payload.get("valid"), bool):
                raise BundleError(
                    "unsupported-runtime", "Native diagnostics lack typed validity"
                )
            if result.returncode or payload["valid"] is False:
                raise BundleError(
                    "native-invalid",
                    "Selected Procedure failed its native check gate",
                    {
                        "native_exit_status": result.returncode,
                        "native_valid": payload["valid"],
                    },
                )
        if result.returncode and not (
            (command == "procedure.check" and payload.get("valid") is False)
            or (command == "workspace.doctor" and payload.get("healthy") is False)
        ):
            raise BundleError("runtime-failure", f"Native {command} did not succeed")
        return payload

    def health(self):
        identity = self.read(
            ["version", "--identity"], "version", {"podway.version-result/v2"}
        )
        version = (
            re.fullmatch(
                r"v?(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)",
                identity["version"],
            )
            if isinstance(identity.get("version"), str)
            else None
        )
        if (
            not version
            or len(identity["version"]) > 64
            or set(identity)
            != {
                "schema",
                "product",
                "version",
                "target",
                "build_identity",
                "source_commit",
                "contract_manifest_schema",
                "contract_manifest_digest",
            }
            or tuple(map(int, version.groups())) < (0, 2, 14)
            or identity.get("contract_manifest_schema") != "podway.contract-manifest/v2"
            or identity.get("product") != "podway"
            or identity.get("target") != "aarch64-apple-darwin"
            or platform.system() != "Darwin"
            or platform.machine() not in {"arm64", "aarch64"}
            or not (
                identity.get("source_commit") is None
                or isinstance(identity["source_commit"], str)
                and 1 <= len(identity["source_commit"]) <= 64
            )
            or any(
                not isinstance(identity.get(field), str)
                or not re.fullmatch(r"sha256:[0-9a-f]{64}", identity[field])
                for field in ("build_identity", "contract_manifest_digest")
            )
        ):
            raise BundleError(
                "unsupported-runtime",
                "Installed native identity does not support selected admission",
            )
        read_regular(self.repository, Path(".podway/config.yaml"))
        doctor = self.read(["doctor"], "workspace.doctor", None)
        if not isinstance(doctor.get("healthy"), bool):
            raise BundleError("unsupported-runtime", "Native Doctor lacks typed health")
        if doctor.get("healthy") is not True:
            raise BundleError("runtime-unavailable", "Native workspace is unhealthy")
        try:
            observation = self.read(
                ["observe"], "session.observe", {"podway.observation-result/v5"}
            )
            status = observation.get("status")
            if (
                not isinstance(status, dict)
                or not isinstance(status.get("procedure"), dict)
                or not isinstance(status.get("session"), dict)
            ):
                raise BundleError(
                    "unsupported-runtime", "Native observation lacks session identity"
                )
            procedure, session = status["procedure"], status["session"]
            if (
                not all(
                    isinstance(procedure.get(field), str) and procedure[field]
                    for field in ("id", "version", "digest")
                )
                or not isinstance(session.get("lifecycle"), str)
                or session["lifecycle"]
                not in {"prepared", "running", "completed", "cancelled"}
            ):
                raise BundleError(
                    "unsupported-runtime", "Native observation session contract differs"
                )
            return observation
        except BundleError as exc:
            if exc.code != "SESSION_NOT_FOUND":
                raise
            return None

    def preview(self, path):
        path = contained(self.repository, path)
        read_regular(self.repository, path)
        relative = str(path.relative_to(self.repository))
        check = self.read(
            ["procedure", "check", "--warnings-as-errors", "--", relative],
            "procedure.check",
            {"podway.procedure-diagnostics-result/v1"},
        )
        if check.get("valid") is not True:
            raise BundleError(
                "native-invalid", "Selected Procedure failed native checks"
            )
        preview = self.read(
            ["procedure", "preview", "--", relative],
            "procedure.preview",
            {
                "podway.procedure-preview-result/v1",
                "podway.procedure-preview-result/v2",
            },
        )
        if not isinstance(preview.get("admissible"), bool):
            raise BundleError(
                "unsupported-runtime", "Native preview lacks typed admissibility"
            )
        if preview["admissible"] is not True:
            raise BundleError("native-invalid", "Selected Procedure is not admissible")
        key = tuple(
            preview.get(field)
            for field in ("procedure_id", "procedure_version", "procedure_digest")
        )
        if not all(
            isinstance(value, str) and value for value in key
        ) or not re.fullmatch(r"sha256:[0-9a-f]{64}", key[2]):
            raise BundleError(
                "unsupported-runtime", "Native preview lacks its exact Procedure tuple"
            )
        return preview

    def identity(self, path):
        preview = self.preview(path)
        return tuple(
            preview[field]
            for field in ("procedure_id", "procedure_version", "procedure_digest")
        )


def known_source(source):
    contract = json.loads((ASSETS / "adaptive/known-sources-v1.json").read_text())
    if (
        contract.get("schema") != "aquarium.known-procedure-sources/v1"
        or contract.get("mapping_version") != "1"
    ):
        raise BundleError("unsupported", "Known-source mapping contract is unsupported")
    for record in contract["sources"]:
        if sha256(source) == record["source_sha256"]:
            return record, yaml.safe_load(source)
    raise BundleError(
        "not-established",
        "New adaptive sources require TASK-141 qualification; existing legacy/custom/formal contracts remain separate",
    )


def reference_binding(source, preview):
    """Map only exact current canonical bytes whose contracts are already known."""
    record, document = known_source(source)
    family = record["family"]
    if (
        preview.get("procedure_id") != document["id"]
        or preview.get("procedure_version") != document["version"]
    ):
        raise BundleError(
            "incompatible", "Native preview identity differs from the known source"
        )
    placements = {node["id"]: node for node in document["graph"]["nodes"]}
    nodes, obligations, goals, closeout = {}, {}, [], []
    for identifier, placement in placements.items():
        definition = document["node_definitions"][placement["use"]]
        reference = record["definitions"][placement["use"]]
        role = reference["role"]
        nodes[identifier] = {"kind": definition["type"], **reference}
        assessment = definition.get("assessment")
        if assessment is not None:
            goals.append({"node": identifier, "outcomes": assessment["outcomes"]})
        if placement.get("terminal"):
            closeout.append({"node": identifier, "kind": "shared", "requires": []})
        if role == "judge":
            producers = []
            for evidence in placement.get("evidence_from", []):
                if evidence.get("required"):
                    producers.extend(
                        {"node": evidence["node"], "item": item}
                        for item in evidence.get("items", [])
                    )
            decision = placement.get("next")
            if producers and decision in placements:
                obligations[identifier] = {
                    "source": "Aquarium references/ordinary-agent-orchestration.md: roles and assessment boundaries",
                    "applicability": "Due at this known canonical assessment placement; invocation criteria remain in ordinary records.",
                    "producers": producers,
                    "evidence": [{"node": identifier, "item": "judge-assessment"}],
                    "assessor": identifier,
                    "decision": decision,
                    "effects": ["covered-work"],
                }
    binding = {
        "schema": "aquarium.procedure-binding/v1",
        "compatibility": "aquarium.adaptive/v1",
        "family": family,
        "entrypoints": sorted(FAMILY_ENTRYPOINTS[family]),
        "procedure": {
            "id": document["id"],
            "version": document["version"],
            "digest": preview["procedure_digest"],
            "source_sha256": sha256(source),
        },
        "nodes": nodes,
        "parameters": {},
        "obligations": obligations,
        "goal_assessments": goals,
        "closeout": closeout,
        "origins": [],
    }
    validate_definition(binding)
    return binding


def qualify_known(source, binding, preview):
    expected = reference_binding(source, preview)
    if canonical_json(binding) != canonical_json(expected):
        raise BundleError(
            "not-established",
            "Binding differs from the verified known-source reference mapping",
        )
    return expected


def selected_source(
    repository,
    source_path,
    *,
    roots,
    entrypoint,
    route=None,
    runtime_ready=None,
    client=None,
    binding_path=None,
):
    if client is None:
        raise BundleError(
            "missing-prerequisite", "Selected admission needs a native client"
        )
    observation = None
    if runtime_ready is None:
        observation = client.health()
        runtime_ready = True
    if runtime_ready is not True:
        raise BundleError(
            "runtime-unavailable",
            "Selected admission requires healthy compatible native runtime/workspace state",
        )
    source = read_regular(repository, Path(source_path))
    preview = client.preview(source_path)
    binding = reference_binding(source, preview)
    if binding_path is not None:
        binding = parse_definition(read_regular(repository, Path(binding_path)))
        qualify_known(source, binding, preview)
    if entrypoint not in binding["entrypoints"]:
        raise BundleError(
            "incompatible", "Selected source does not support this entrypoint"
        )
    if binding["family"] in {"task", "goal", "validation"}:
        if route not in {"mulgae", "herdr", "independent-review", "waived"}:
            raise BundleError(
                "route-unavailable", "A selected review route is required"
            )
        document = known_source(source)[1]
        declarations = [
            item
            for definition in document["node_definitions"].values()
            for item in definition.get("items", [])
            if item["id"] == "review-route"
        ]
        if not declarations or any(
            route not in item.get("choices", []) for item in declarations
        ):
            raise BundleError(
                "route-unavailable", "Selected route is absent from the exact source"
            )
    if read_regular(repository, Path(source_path)) != source:
        raise BundleError("corrupt", "Selected source changed during admission")
    resolved = resolve_bundle(
        repository,
        roots,
        native_key(binding),
        native_identity=client.identity,
        bundle_id=definition_id(binding),
    )
    if resolved["status"] not in {"resolved", "missing"}:
        raise BundleError(
            resolved["status"], "Existing selected-key bundle needs recovery", resolved
        )
    if resolved["status"] == "resolved":
        qualify_known(resolved["source"], resolved["binding"], preview)
    return {
        "status": "ready",
        "binding": binding,
        "source": source,
        "preview": preview,
        "retention": resolved,
        "session": session_context(observation, binding),
    }


def session_context(observation, binding):
    if observation is None:
        return {"state": "none", "work_identity_reconciliation_required": False}
    status = observation["status"]
    procedure = {
        field: status["procedure"][field] for field in ("id", "version", "digest")
    }
    return {
        "state": status["session"]["lifecycle"],
        "procedure": procedure,
        "definition_conflict": procedure
        != {field: binding["procedure"][field] for field in procedure},
        "work_identity_reconciliation_required": True,
    }


def retain_selected(
    repository,
    source_path,
    *,
    roots,
    write_root,
    entrypoint,
    route=None,
    runtime_ready=None,
    client=None,
):
    selected = selected_source(
        repository,
        source_path,
        roots=roots,
        entrypoint=entrypoint,
        route=route,
        runtime_ready=runtime_ready,
        client=client,
    )
    result = publish_bundle(
        repository,
        roots,
        write_root,
        selected["source"],
        selected["binding"],
        qualify=lambda source, binding: qualify_known(
            source, binding, selected["preview"]
        ),
        native_identity=client.identity,
    )
    result["session"] = selected["session"]
    return result


def resume_selected(repository, roots, procedure, *, client, bootstrap=None):
    key = tuple(procedure.get(field) for field in ("id", "version", "digest"))
    if not all(isinstance(value, str) and value for value in key):
        raise BundleError(
            "unsupported-runtime", "Native session lacks its exact Procedure tuple"
        )
    resolved = resolve_bundle(
        repository, roots, key, native_identity=client.identity, bootstrap=bootstrap
    )
    if resolved["status"] != "resolved":
        raise BundleError(
            resolved["status"],
            "Native selected session cannot resolve its retained definition",
            resolved,
        )
    preview = client.preview(Path(resolved["path"]) / "procedure.yaml")
    if (
        tuple(
            preview[field]
            for field in ("procedure_id", "procedure_version", "procedure_digest")
        )
        != key
    ):
        raise BundleError(
            "corrupt", "Retained native digest differs from session readback"
        )
    qualify_known(resolved["source"], resolved["binding"], preview)
    return resolved
