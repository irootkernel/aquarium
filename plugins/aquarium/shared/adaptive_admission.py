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
    capability_signatures,
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
        if (
            command
            in {
                "procedure.format",
                "procedure.validate",
                "procedure.vet",
                "procedure.lint",
            }
            and payload.get("schema") == "podway.procedure-diagnostics-result/v1"
        ):
            if not isinstance(payload.get("valid"), bool):
                raise BundleError(
                    "unsupported-runtime",
                    "Native authoring diagnostics lack typed validity",
                )
            if result.returncode or payload["valid"] is False:
                raise BundleError(
                    "native-invalid",
                    "Procedure failed its native authoring gate",
                    {"native_exit_status": result.returncode, "native_result": payload},
                )
        if (
            command == "procedure.format"
            and payload.get("schema") == "podway.procedure-source-result/v1"
        ):
            if (
                not isinstance(payload.get("changed"), bool)
                or payload.get("target_schema") != "podway.procedure/v2"
            ):
                raise BundleError(
                    "unsupported-runtime",
                    "Native formatter result lacks typed source status",
                )
            if result.returncode or ("--check" in arguments and payload["changed"]):
                raise BundleError(
                    "native-invalid",
                    "Procedure failed its native format gate",
                    {"native_exit_status": result.returncode, "native_result": payload},
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
    for version in (2, 1):
        path = ASSETS / f"adaptive/known-sources-v{version}.json"
        if not path.exists():
            continue
        contract = json.loads(path.read_text())
        if contract.get(
            "schema"
        ) != f"aquarium.known-procedure-sources/v{version}" or contract.get(
            "mapping_version"
        ) != str(version):
            raise BundleError(
                "unsupported", "Known-source mapping contract is unsupported"
            )
        for record in contract["sources"]:
            if sha256(source) == record["source_sha256"]:
                return record, yaml.safe_load(source)
    raise BundleError(
        "not-established",
        "New adaptive sources require exact structural qualification and suitability; existing legacy/custom/formal contracts remain separate",
    )


def reference_mapping(source):
    """Return the supported definition mapping without inventing a native digest."""
    record, document = known_source(source)
    family = record["family"]
    retained = any(
        value["role"] in {"worker", "judge", "orchestrator"}
        for value in record["definitions"].values()
    )
    version = 1 if retained else 2
    assessor = "judge" if retained else "evaluator"
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
        if role == assessor:
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
                    "evidence": [
                        {"node": identifier, "item": f"{assessor}-assessment"}
                    ],
                    "assessor": identifier,
                    "decision": decision,
                    "effects": ["covered-work"],
                }
    binding = {
        "schema": f"aquarium.procedure-binding/v{version}",
        "compatibility": f"aquarium.adaptive/v{version}",
        "family": family,
        "entrypoints": sorted(FAMILY_ENTRYPOINTS[family]),
        "nodes": nodes,
        "parameters": {},
        "obligations": obligations,
        "goal_assessments": goals,
        "closeout": closeout,
        "origins": [],
    }
    return binding


def reference_binding(source, preview):
    _, document = known_source(source)
    if (
        preview.get("procedure_id") != document["id"]
        or preview.get("procedure_version") != document["version"]
    ):
        raise BundleError(
            "incompatible", "Native preview identity differs from the known source"
        )
    binding = reference_mapping(source)
    binding["procedure"] = {
        "id": document["id"],
        "version": document["version"],
        "digest": preview["procedure_digest"],
        "source_sha256": sha256(source),
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


def selection_contract(
    source, binding, entrypoint, route, qualification, *, document=None
):
    """Validate the selected invocation without changing suitability timing."""
    adaptive = qualification is not None
    retained = binding.get("schema") == "aquarium.procedure-binding/v1"
    if (
        retained
        and adaptive
        and qualification.get("assignment", {}).get("schema")
        == "aquarium.assignment/v3"
    ):
        raise BundleError(
            "retained-contract",
            "Retained definitions require their original execution contract",
        )
    if adaptive:
        approved_route = (
            qualification.get("assignment", {})
            .get("authority", {})
            .get("review", {})
            .get("route")
        )
        if approved_route != (route if route is not None else "not-applicable"):
            raise BundleError(
                "route-unavailable",
                "Selected route differs from the exact suitability authority",
            )
        supported = {"mulgae", "herdr", "subagent-review", "waived"}
        if binding["family"] in {"design", "diagnosis"}:
            supported.add("not-applicable")
        if approved_route not in supported:
            raise BundleError(
                "route-unavailable",
                "Adaptive admission requires its actual supported selected review route",
            )
    if entrypoint not in binding["entrypoints"]:
        raise BundleError(
            "incompatible", "Selected source does not support this entrypoint"
        )
    if (
        binding["family"] in {"task", "goal", "validation"}
        and not adaptive
        and route not in {"mulgae", "herdr", "subagent-review", "waived"}
    ):
        raise BundleError("route-unavailable", "A selected review route is required")
    if route is not None and route != "not-applicable":
        if route not in {"mulgae", "herdr", "subagent-review", "waived"}:
            raise BundleError(
                "route-unavailable", "Selected review route is unsupported"
            )
        if document is None:
            document = yaml.safe_load(source)
        signatures = {
            **capability_signatures(1 if retained else 2),
            **binding.get("capability_definitions", {}),
        }
        declarations = []
        for node in document["graph"]["nodes"]:
            names = set()
            for capability in binding["nodes"][node["id"]]["capabilities"]:
                declared = signatures.get(capability["signature"], {}).get("fields", {})
                names.update(
                    capability["fields"].get(logical, logical)
                    for logical in {"review-route", "effective-review-route"}
                    & declared.keys()
                )
            declarations.extend(
                item
                for item in document["node_definitions"][node["use"]].get("items", [])
                if item["id"] in names and item["type"] == "choice"
            )
        required = not adaptive and binding["family"] in {"task", "goal", "validation"}
        if (required and not declarations) or any(
            route not in item["choices"] for item in declarations
        ):
            raise BundleError(
                "route-unavailable", "Selected route is absent from the exact source"
            )


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
    qualification=None,
):
    if qualification is not None:
        from adaptive_suitability import resolver_scope

        resolver_scope(repository, qualification["assignment"], roots)
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
    adaptive = qualification is not None
    if adaptive:
        if binding_path is None or not isinstance(qualification, dict):
            raise BundleError(
                "not-established",
                "Adaptive admission needs its exact binding and ordinary suitability context",
            )
        from adaptive_suitability import qualify_prepared

        binding = parse_definition(read_regular(repository, Path(binding_path)))
        selection_contract(source, binding, entrypoint, route, qualification)
        result = qualify_prepared(
            repository,
            qualification["assignment"],
            client=client,
            assessment=qualification.get("assessment"),
            combined_task_plan=qualification.get("combined_task_plan", False),
            source_path=source_path,
            binding_path=binding_path,
        )
        if result["status"] not in {"qualified", "qualified-known"}:
            raise BundleError(
                "not-established",
                "Actual pre-start independent suitability remains due",
                result,
            )
    else:
        binding = reference_binding(source, preview)
        if binding_path is not None:
            binding = parse_definition(read_regular(repository, Path(binding_path)))
            qualify_known(source, binding, preview)
    if not adaptive:
        selection_contract(source, binding, entrypoint, route, qualification)
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
    if resolved["status"] == "resolved" and not adaptive:
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
    binding_path=None,
    qualification=None,
):
    selected = selected_source(
        repository,
        source_path,
        roots=roots,
        entrypoint=entrypoint,
        route=route,
        runtime_ready=runtime_ready,
        client=client,
        binding_path=binding_path,
        qualification=qualification,
    )

    def check(source, binding):
        if qualification is None:
            return qualify_known(source, binding, selected["preview"])
        if source != selected["source"] or binding != selected["binding"]:
            raise BundleError(
                "source-drift", "Qualified source changed before retention"
            )
        from adaptive_suitability import qualify_prepared

        result = qualify_prepared(
            repository,
            qualification["assignment"],
            client=client,
            assessment=qualification.get("assessment"),
            combined_task_plan=qualification.get("combined_task_plan", False),
            source_path=source_path,
            binding_path=binding_path,
        )
        if result["status"] not in {"qualified", "qualified-known"}:
            raise BundleError("not-established", "Suitability remains due")

    if qualification is not None:
        from adaptive_suitability import retention_scope

        retention_scope(
            repository,
            qualification["assignment"],
            client,
            roots=roots,
            write_root=write_root,
        )
    result = publish_bundle(
        repository,
        roots,
        write_root,
        selected["source"],
        selected["binding"],
        qualify=check,
        native_identity=client.identity,
    )
    result["session"] = selected["session"]
    return result


def resume_selected(
    repository,
    roots,
    procedure,
    *,
    client,
    bootstrap=None,
    qualification=None,
    source_reader=None,
):
    if qualification is not None:
        from adaptive_suitability import resolver_scope

        resolver_scope(repository, qualification["assignment"], roots)
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
    if qualification is None:
        qualify_known(resolved["source"], resolved["binding"], preview)
    else:
        from adaptive_suitability import qualify_prepared

        result = qualify_prepared(
            repository,
            qualification["assignment"],
            client=client,
            assessment=qualification.get("assessment"),
            combined_task_plan=qualification.get("combined_task_plan", False),
            source_path=Path(resolved["path"]) / "procedure.yaml",
            binding_path=Path(resolved["path"]) / "binding.json",
            in_session=True,
            source_reader=source_reader,
        )
        if result["status"] not in {"qualified", "qualified-known"}:
            raise BundleError(
                "not-established", "Current exact suitability remains due", result
            )
        resolved["qualification"] = result
    resolved["preview"] = preview
    return resolved


def selected_session(
    repository,
    procedure,
    *,
    roots,
    entrypoint,
    route=None,
    client,
    bootstrap=None,
    qualification=None,
):
    """Resolve and validate an admitted session without repeating adoption checks."""
    bundle = resume_selected(
        repository,
        roots,
        procedure,
        client=client,
        bootstrap=bootstrap,
        qualification=qualification,
    )
    selection_contract(
        bundle["source"], bundle["binding"], entrypoint, route, qualification
    )
    return {
        "status": "ready",
        "binding": bundle["binding"],
        "source": bundle["source"],
        "preview": bundle["preview"],
        "retention": bundle,
    }
