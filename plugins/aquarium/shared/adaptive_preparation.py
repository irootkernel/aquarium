"""Fit selection and source-only preparation; never admission or execution."""

import contextlib
import copy
import importlib.util
import json
import os
import re
import stat
import sys
import uuid
from pathlib import Path

import yaml
from adaptive_admission import (
    known_source,
    qualify_known,
    reference_binding,
    reference_mapping,
)
from adaptive_bundles import (
    BundleError,
    _ignored_local,
    _rename_exclusive,
    contained,
    directory,
    local_status,
    publication_lock,
    read_regular,
    roots_for,
    sha256,
    verified_bundle,
)
from adaptive_definitions import (
    ASSETS,
    FAMILY_ENTRYPOINTS,
    canonical_json,
    capability_signatures,
    definition_id,
    parse_definition,
    validate_definition,
)


class ProcedureDumper(yaml.SafeDumper):
    """Keep multiline values escaped on one native authoring source line."""


def native_string(dumper, value):
    return dumper.represent_scalar(
        "tag:yaml.org,2002:str",
        value,
        style='"' if any(char in value for char in "\r\n\x85\u2028\u2029") else None,
    )


ProcedureDumper.add_representer(str, native_string)


def usable_reason(value):
    return isinstance(value, str) and bool(value.strip())


def object_value(value, name):
    if not isinstance(value, dict):
        raise BundleError("invalid-input", name + " must be an object")
    return value


def object_rows(value, name):
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise BundleError("invalid-input", name + " must be a list of objects")
    return value


def markdown_section(text, selector):
    if not usable_reason(selector):
        raise BundleError(
            "invalid-input", "Markdown section must be a nonempty heading selector"
        )
    lines = text.splitlines(keepends=True)
    headings, fence = [], None
    paragraph_lines = set()
    for index, line in enumerate(lines):
        content = line.rstrip("\r\n")
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", content)
        if fence is not None:
            if re.fullmatch(
                r" {0,3}" + re.escape(fence[0]) + "{" + str(fence[1]) + r",}[ \t]*",
                content,
            ):
                fence = None
            continue
        if marker:
            fence = (marker[1][0], len(marker[1]))
            continue
        atx = re.match(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?)|[ \t]*)$", content)
        if atx:
            title = re.sub(r"[ \t]+#+[ \t]*$", "", atx[2] or "").strip()
            headings.append((index, index + 1, len(atx[1]), content.strip(), title))
        elif index and re.fullmatch(r" {0,3}(?:=+|-+)[ \t]*", content):
            previous = lines[index - 1].rstrip("\r\n")
            if index - 1 in paragraph_lines:
                headings.append(
                    (
                        index - 1,
                        index + 1,
                        1 if content.lstrip().startswith("=") else 2,
                        previous.strip(),
                        previous.strip(),
                    )
                )
        elif (
            content.strip()
            and not content.startswith(("    ", "\t"))
            and not re.match(
                r"^ {0,3}(?:>[ \t]?|[-+*][ \t]+|[0-9]+[.)][ \t]+)", content
            )
            and not re.fullmatch(
                r" {0,3}(?:(?:\*[ \t]*){3,}|(?:_[ \t]*){3,}|(?:-[ \t]*){3,})", content
            )
        ):
            paragraph_lines.add(index)
    selected = [
        row
        for row in headings
        if selector.strip() == row[3]
        or (not selector.lstrip().startswith("#") and selector.strip() == row[4])
    ]
    if len(selected) != 1:
        raise BundleError(
            "not-established",
            "Markdown section selector is missing, ambiguous or unsupported",
        )
    begin, body, level, _, _ = selected[0]
    end = next(
        (row[0] for row in headings if row[0] > begin and row[2] <= level), len(lines)
    )
    return "".join(lines[body:end])


def source_authority(repository, assignment):
    """Read the actual managed slot and explicit adopted authority, not templates."""
    plan = assignment["target"]["procedure_plan"]
    family = plan["family"]
    filename = (
        "aquarium-" + ("war-room" if family == "diagnosis" else family) + "-v2.yaml"
    )
    path = Path(".podway/procedures") / filename
    sources = []
    try:
        raw = read_regular(repository, path)
    except BundleError as error:
        if error.code != "missing":
            raise
    else:
        inspector_path = (
            Path(__file__).resolve().parents[1]
            / "skills/dev-setup/scripts/inspect_tools.py"
        )
        spec = importlib.util.spec_from_file_location(
            "adaptive_static_source_authority", inspector_path
        )
        inspector = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(inspector)
        current = (ASSETS / "podway/procedures" / filename).read_bytes()
        digest = sha256(raw)
        if raw == current:
            classification = "current_canonical"
        elif (
            digest.removeprefix("sha256:")
            in inspector.PODWAY_PRIOR_CANONICAL_SHA256[filename]
        ):
            classification = "prior_canonical"
        elif raw == inspector.podway_v025_workaround_bytes(filename, current):
            classification = "podway_v0.2.5_workaround"
        else:
            classification = "local_customization"
        sources.append(
            {
                "path": str(path),
                "sha256": digest,
                "classification": classification,
                "original_text": raw.decode("utf-8"),
            }
        )
    adopted = [row for row in sources if row["classification"] == "local_customization"]
    if adopted and not usable_reason(plan.get("customization_disposition")):
        raise BundleError(
            "not-established",
            "Actual adopted managed source needs its existing-envelope preservation basis before selection",
            {"adopted_sources": adopted},
        )
    return {
        "managed_sources": sources,
        "preservation_basis": plan.get("customization_disposition"),
        "semantic_completeness": "requires-independent-original-source-assessment",
    }


def read_basis(repository, reference):
    """Read original bytes, not a generated plan's replacement requirements."""
    raw = read_regular(repository, Path(reference["path"]))
    if sha256(raw) != reference["sha256"]:
        raise BundleError(
            "source-drift", "Original source changed", {"path": reference["path"]}
        )
    return raw


def requirements(repository, assignment, *, verify_sources=True, source_reader=None):
    if source_reader is not None and verify_sources:
        raise BundleError(
            "invalid-input", "Original source recovery cannot replace pre-start reads"
        )
    result = {}
    sources = object_rows(
        assignment["work"]["requirement_sources"], "requirement_sources"
    )
    for source in sources:
        role = source.get("role", "requirements")
        family = source.get("family")
        if not isinstance(role, str) or role not in {
            "requirements",
            "adopted-customization",
            "template",
            "historical",
        }:
            raise BundleError("invalid-input", "Unknown requirement-source role")
        if family is not None and (
            not isinstance(family, str) or family not in FAMILY_ENTRYPOINTS
        ):
            raise BundleError("invalid-input", "Unknown requirement-source family")
        if role in {"template", "historical"} or family not in {
            None,
            assignment["target"]["procedure_plan"]["family"],
        }:
            continue
        raw = (
            source_reader(source)
            if source_reader is not None
            else read_basis(repository, source)
            if verify_sources
            else read_regular(repository, Path(source["path"]))
        )
        text = raw.decode("utf-8")
        # Structured original sources retain their own criterion and part identity.
        if source.get("format") == "json":
            rows = object_rows(
                object_value(json.loads(text), "Original JSON source")["criteria"],
                "Original criteria",
            )
        else:
            if source.get("section") is not None:
                text = markdown_section(text, source["section"])
            # Keep paragraphs, nested bullets and compound clauses in the basis.
            rows = [{"id": "whole", "text": text.strip()}]
        for row in rows:
            identifier = source["id"] + ":" + row["id"]
            if identifier in result or not row["text"]:
                raise BundleError(
                    "incompatible", "Original criterion identity is ambiguous"
                )
            parts = object_rows(
                row.get("parts") or [{"id": "whole", "text": row["text"]}],
                "Criterion parts",
            )
            if len({part["id"] for part in parts}) != len(parts):
                raise BundleError(
                    "incompatible", "Compound criterion part identity is ambiguous"
                )
            result[identifier] = {
                "source": source["path"],
                "source_sha256": source["sha256"],
                "text": row["text"],
                "parts": parts,
                "adopted": source.get("role") == "adopted-customization",
            }
    if not result:
        raise BundleError(
            "not-established", "No original requirement inventory is available"
        )
    links = object_value(
        assignment["target"]["procedure_plan"].get("criterion_links", {}),
        "criterion_links",
    )
    for criterion in assignment["success_criteria"]:
        matched = links.get(
            criterion,
            [
                identifier
                for identifier, row in result.items()
                if criterion in {identifier, row["text"]}
            ],
        )
        if not matched or any(identifier not in result for identifier in matched):
            raise BundleError(
                "not-established",
                "Assigned criterion lacks original-source trace",
                {"criterion": criterion},
            )
    return result


def document(repository, entry):
    entry = object_value(entry, "Procedure source reference")
    if entry.get("installed"):
        name = entry["installed"]
        if name not in {
            path.name for path in (ASSETS / "podway/procedures").glob("*.yaml")
        }:
            raise BundleError("incompatible", "Unknown installed default")
        path = ASSETS / "podway/procedures" / name
        if path.is_symlink():
            raise BundleError("unsafe", "Installed source is symlinked")
        raw = path.read_bytes()
        if entry.get("sha256") is not None and sha256(raw) != entry["sha256"]:
            raise BundleError("source-drift", "Installed source changed")
    else:
        raw = read_basis(repository, entry)
    try:
        value = yaml.safe_load(raw)
    except (yaml.YAMLError, UnicodeError, ValueError, RecursionError) as error:
        raise BundleError(
            "native-invalid", "Selected Procedure source is malformed YAML"
        ) from error
    if not isinstance(value, dict) or value.get("schema") != "podway.procedure/v2":
        raise BundleError(
            "native-invalid", "Selected source is not a native Procedure v2"
        )
    return raw, value


def discover(repository, plan):
    entries, diagnostics = [], []
    for root in roots_for(repository, plan["discovery_roots"]):
        with directory(repository, root, allow_missing=True) as descriptor:
            if descriptor is None:
                continue
        for path in sorted(root.rglob("*")):
            if path.is_dir() and not path.is_symlink():
                continue
            try:
                raw = read_regular(repository, path)
                value = yaml.safe_load(raw)
                if (
                    isinstance(value, dict)
                    and value.get("schema") == "podway.procedure/v2"
                ):
                    identifier, version = value.get("id"), value.get("version")
                    if (
                        not isinstance(identifier, str)
                        or not 1 <= len(identifier) <= 64
                        or not re.fullmatch(
                            r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", identifier
                        )
                        or not isinstance(version, str)
                        or not 1 <= len(version) <= 64
                    ):
                        raise BundleError(
                            "native-invalid",
                            "Historical native identity has invalid types or bounds",
                        )
                    entries.append(
                        {
                            "path": str(path.relative_to(repository)),
                            "sha256": sha256(raw),
                            "id": value["id"],
                            "version": value["version"],
                        }
                    )
            except (
                BundleError,
                yaml.YAMLError,
                UnicodeError,
                KeyError,
                ValueError,
                RecursionError,
            ) as error:
                diagnostics.append(
                    {
                        "path": str(path.relative_to(repository)),
                        "status": getattr(error, "code", "native-invalid"),
                    }
                )
    for path in sorted((ASSETS / "podway/procedures").glob("*.yaml")):
        if path.is_symlink():
            continue
        raw = path.read_bytes()
        value = yaml.safe_load(raw)
        entries.append(
            {
                "installed": path.name,
                "sha256": sha256(raw),
                "id": value["id"],
                "version": value["version"],
            }
        )
    return entries, diagnostics


def endpoint(document, reference):
    placements = {node["id"]: node for node in document["graph"]["nodes"]}
    placement = placements.get(reference["node"])
    if placement is None:
        return False
    definition = document["node_definitions"][placement["use"]]
    return definition.get("type") == "action" and any(
        item["id"] == reference["item"] for item in definition.get("items", [])
    )


def review_fit(document, mapping, review):
    """Check declared route choices without inferring capabilities from item names."""
    signatures = capability_signatures()
    placements = {node["id"]: node for node in document["graph"]["nodes"]}
    checked = []
    for identifier, node in mapping["nodes"].items():
        placement = placements.get(identifier)
        if placement is None:
            continue
        definition = document["node_definitions"][placement["use"]]
        items = {item["id"]: item for item in definition.get("items", [])}
        for capability in node["capabilities"]:
            declared = signatures.get(capability["signature"], {}).get("fields", {})
            aliases = capability["fields"]
            for logical in {"review-route", "effective-review-route"} & (
                declared.keys()
            ):
                actual = aliases.get(logical, logical)
                item = items.get(actual)
                if item is None or item.get("type") != "choice":
                    continue
                if review["route"] != "not-applicable" and review[
                    "route"
                ] not in item.get("choices", []):
                    raise BundleError(
                        "incompatible",
                        "Mapped route declaration contradicts the selected review",
                        {"node": identifier, "item": actual, "route": review["route"]},
                    )
                checked.append({"node": identifier, "item": actual})
    return {
        "status": "not-established",
        "declarations_checked": checked,
        "next_owner": "qualify_adaptive_procedure",
        "reason": "Mapped choices can show contradiction; independent review-control continuity is not established by a selector or its absence.",
    }


def fit(assignment, criteria, document, mapping, coverage):
    """Mechanical fit, with semantic sufficiency left to the original assessor."""
    plan = assignment["target"]["procedure_plan"]
    object_value(mapping, "mapping")
    for node in object_value(mapping["nodes"], "mapping.nodes").values():
        object_value(node, "mapping node")
        for capability in object_rows(node["capabilities"], "node.capabilities"):
            object_value(capability["fields"], "capability.fields")
    object_value(document, "native document")
    for definition in object_value(
        document["node_definitions"], "node_definitions"
    ).values():
        object_value(definition, "node definition")
        object_rows(definition.get("items", []), "definition.items")
    object_rows(object_value(document["graph"], "graph")["nodes"], "graph.nodes")
    object_rows(coverage, "coverage")
    for obligation in object_value(mapping["obligations"], "obligations").values():
        object_value(obligation, "obligation")
        object_rows(obligation["producers"], "obligation.producers")
        object_rows(obligation["evidence"], "obligation.evidence")
    object_value(assignment["authority"]["review"], "authority.review")
    if (
        mapping["family"] != plan["family"]
        or plan["entrypoint"] not in mapping["entrypoints"]
    ):
        raise BundleError("incompatible", "Definition family or entrypoint differs")
    requested = set(plan["effects"])
    permitted = set(assignment["authority"]["effects"])
    if not requested <= permitted:
        raise BundleError(
            "authority-required", "Work effects exceed the existing envelope"
        )
    effects = set().union(*(set(node["effects"]) for node in mapping["nodes"].values()))
    if not effects <= requested | {"covered-work"}:
        raise BundleError(
            "incompatible",
            "Definition carries effects outside the work scope",
            {"effects": sorted(effects - requested - {"covered-work"})},
        )
    review = assignment["authority"]["review"]
    if plan["review"] != review:
        raise BundleError(
            "authority-required",
            "Selected review, team or transmission differs from the envelope",
        )
    review_continuity = review_fit(document, mapping, review)
    expected = {
        (identifier, part["id"])
        for identifier, row in criteria.items()
        for part in row["parts"]
    }
    supplied = {(row["criterion"], row["part"]) for row in coverage}
    if supplied != expected or len(supplied) != len(coverage):
        raise BundleError(
            "not-established",
            "Original or compound requirement coverage is incomplete",
            {
                "missing": sorted(expected - supplied),
                "unexpected": sorted(supplied - expected),
            },
        )
    for row in coverage:
        obligation = mapping["obligations"].get(row["obligation"])
        if obligation is None or not usable_reason(row.get("reason")):
            raise BundleError(
                "not-established",
                "Coverage needs an actual obligation and concrete fit reason",
            )
        if not all(
            endpoint(document, value)
            for value in obligation["producers"] + obligation["evidence"]
        ):
            raise BundleError(
                "incompatible", "Coverage endpoint is absent from the actual source"
            )
        placements = {node["id"]: node for node in document["graph"]["nodes"]}
        decision = placements.get(obligation["decision"])
        if (
            decision is None
            or document["node_definitions"][decision["use"]]["type"] != "decision"
        ):
            raise BundleError(
                "incompatible", "Coverage lacks a consuming native Decision"
            )
    adopted = {identifier for identifier, row in criteria.items() if row["adopted"]}
    if adopted and not usable_reason(plan.get("customization_disposition")):
        raise BundleError(
            "not-established",
            "Adopted obligations need the existing envelope disposition",
        )
    return {
        "criteria": criteria,
        "coverage": coverage,
        "effects": plan["effects"],
        "review": copy.deepcopy(review),
        "review_continuity": review_continuity,
        "customization_disposition": plan.get("customization_disposition"),
        "semantic_completeness": "requires-independent-original-source-assessment",
    }


def select(repository, assignment, *, client=None):
    """Use caller-approved locations only; plan-only never calls a native tool."""
    validator_path = (
        Path(__file__).resolve().parents[1]
        / "skills/goal-judge/scripts/ordinary_assignment.py"
    )
    specification = importlib.util.spec_from_file_location(
        "adaptive_ordinary_assignment", validator_path
    )
    validator = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(validator)
    try:
        assignment = validator.prepare(assignment)
    except validator.AssignmentError as error:
        raise BundleError("incompatible", str(error)) from error
    if assignment["role"] != "worker":
        raise BundleError(
            "incompatible", "Preparation requires its ordinary Worker assignment"
        )
    plan = object_value(assignment["target"]["procedure_plan"], "procedure_plan")
    object_rows(plan.get("candidates", []), "candidates")
    for draft in object_rows(plan.get("drafts", []), "drafts"):
        if draft.get("revision_of") is not None:
            object_value(draft["revision_of"], "draft.revision_of")
        if draft.get("kind") != "compose":
            mapping = object_value(draft.get("mapping"), "draft.mapping")
            object_value(mapping.get("nodes"), "draft.mapping.nodes")
    if (
        plan["family"] not in FAMILY_ENTRYPOINTS
        or plan["entrypoint"] not in FAMILY_ENTRYPOINTS[plan["family"]]
    ):
        raise BundleError("incompatible", "Unsupported family/entrypoint pair")
    criteria = requirements(repository, assignment)
    authority_basis = source_authority(repository, assignment)
    discovered, considered = discover(repository, plan)
    known_discovered = []
    for source in discovered:
        try:
            raw, _ = document(repository, source)
            record, _ = known_source(raw)
        except BundleError as error:
            considered.append(
                {
                    "source": source.get("path", source.get("installed")),
                    "status": error.code,
                    "reason": str(error),
                }
            )
            continue
        if record["family"] == plan["family"]:
            known_discovered.append(source)
    declared = {
        entry.get("path", entry.get("installed"))
        for entry in plan.get("candidates", [])
    }
    dismissed = object_value(plan.get("source_dispositions", {}), "source_dispositions")
    if any(not usable_reason(value) for value in dismissed.values()):
        raise BundleError(
            "not-established",
            "Known-source limitations need concrete current fit reasons",
        )
    considered.extend(
        {"source": key, "status": "not-selected", "reason": reason}
        for key, reason in dismissed.items()
    )
    for entry in plan.get("candidates", []):
        try:
            raw, native = document(repository, entry)
            mapping = (
                parse_definition(read_basis(repository, entry["binding"]))
                if entry.get("binding")
                else reference_mapping(raw)
            )
            if mapping.get("procedure", {}).get("source_sha256", sha256(raw)) != sha256(
                raw
            ):
                raise BundleError(
                    "source-drift", "Candidate binding and source bytes differ"
                )
            evidence = fit(assignment, criteria, native, mapping, entry["coverage"])
            evidence["source_authority"] = authority_basis
            known_adaptive = False
            try:
                known_source(raw)
            except BundleError as error:
                if error.code != "not-established":
                    raise
                from adaptive_suitability import established_reuse

                if (
                    not isinstance(entry.get("prior_suitability"), dict)
                    or "procedure" not in mapping
                ):
                    raise BundleError(
                        "not-established",
                        "Existing adaptive reuse needs its actual prior ordinary suitability evidence and exact supported binding",
                    ) from None
                grant = assignment["authority"].get("preparation", {})
                native_client = client if plan["mode"] == "prepare" else None
                if (
                    native_client is not None
                    and grant.get("native_authoring") is not True
                ):
                    raise BundleError(
                        "authority-required",
                        "Current preparation authority does not cover native reuse checks",
                    )
                established_reuse(
                    repository,
                    raw,
                    mapping,
                    client=native_client,
                    roots=grant.get("roots", plan["discovery_roots"]),
                    prior=entry["prior_suitability"],
                    criteria=criteria,
                    context={
                        **assignment["target"].get("qualification_context", {}),
                        "review": assignment["authority"]["review"],
                    },
                )
                known_adaptive = True
            if "procedure" in mapping and not known_adaptive:
                qualify_known(
                    raw,
                    mapping,
                    {
                        "procedure_id": native["id"],
                        "procedure_version": native["version"],
                        "procedure_digest": mapping["procedure"]["digest"],
                    },
                )
            if not usable_reason(entry.get("reason")):
                raise BundleError(
                    "not-established", "Reuse needs a current work-specific reason"
                )
            evidence["review_continuity"].update(
                status="known-contract-preserved",
                next_owner="original-workflow-checkpoints",
                reason="Exact known definition preserves its established structural review contract; actual selected review execution remains due.",
            )
            return {
                "kind": "reuse",
                "source": raw,
                "document": native,
                "mapping": mapping,
                "entry": entry,
                "reason": entry["reason"],
                "plan": evidence,
                "considered": considered,
                "assessment": "preserve-original-checkpoints",
                "known_adaptive": known_adaptive,
                "prior_suitability": entry.get("prior_suitability")
                if known_adaptive
                else None,
            }
        except BundleError as error:
            if error.details.get("candidate_reuse_pending"):
                raise
            if error.code in {
                "source-drift",
                "authority-required",
                "native-invalid",
                "unsafe",
            }:
                raise
            considered.append(
                {
                    "source": entry.get("path", entry.get("installed")),
                    "status": error.code,
                    "reason": str(error),
                    "details": error.details,
                }
            )
    declared_hashes = {
        entry["sha256"]
        for entry in discovered
        if entry.get("path", entry.get("installed")) in declared
        or dismissed.get(entry.get("path", entry.get("installed")))
    }
    missing = {
        entry["sha256"]: entry
        for entry in known_discovered
        if entry["sha256"] not in declared_hashes
    }
    if missing:
        raise BundleError(
            "not-established",
            "Known reuse needs current fit consideration before generation",
            {"discovered": list(missing.values()), "considered": considered},
        )
    for draft in sorted(
        plan.get("drafts", []),
        key=lambda entry: {"adapt": 0, "compose": 1, "author": 2}.get(entry["kind"], 3),
    ):
        composition = None
        if draft["kind"] == "compose":
            from adaptive_composition import compose

            composition = compose(repository, draft)
        if draft["kind"] not in {"adapt", "compose", "author"}:
            raise BundleError("incompatible", "Unknown preparation strategy")
        if draft["kind"] == "adapt":
            document(repository, draft["base"])
        current_document = composition["document"] if composition else draft["document"]
        current_mapping = composition["mapping"] if composition else draft["mapping"]
        evidence = fit(
            assignment, criteria, current_document, current_mapping, draft["coverage"]
        )
        if composition:
            evidence["composition"] = {
                "origins": composition["origins"],
                "parameters": composition["parameters"],
                "qualification": composition["qualification"],
            }
        evidence["source_authority"] = authority_basis
        if not usable_reason(draft.get("reason")):
            raise BundleError(
                "not-established", "Authoring needs a current work-specific reason"
            )
        return {
            "kind": draft["kind"],
            "document": copy.deepcopy(current_document),
            "mapping": copy.deepcopy(current_mapping),
            "composition_bases": composition["bases"] if composition else [],
            "entry": draft,
            "reason": draft["reason"],
            "plan": evidence,
            "considered": considered,
            "assessment": "TASK-141-exact-target-suitability-required",
        }
    raise BundleError(
        "not-established",
        "No adequate definition or bounded authoring draft",
        {"considered": considered, "criteria": criteria},
    )


def author_checks(client, path, *, format_source, stage_descriptor=None):
    relative = str(Path(path).relative_to(client.repository))
    identity = client.read(
        ["version", "--identity"], "version", {"podway.version-result/v2"}
    )
    if not format_source:
        preview = client.preview(path)
        return preview, {
            "identity": identity,
            "checks": [],
            "check_and_preview": preview,
        }
    formatted = client.read(
        ["procedure", "format", "--", relative],
        "procedure.format",
        {"podway.procedure-source-result/v1", "podway.procedure-diagnostics-result/v1"},
    )
    if not isinstance(formatted.get("document"), str):
        raise BundleError(
            "unsupported-runtime", "Native formatter lacks canonical source"
        )
    if stage_descriptor is not None:
        verify_directory(client.repository, path.parent, stage_descriptor)
    with directory(client.repository, path.parent) as opened:
        parent = stage_descriptor if stage_descriptor is not None else opened
        descriptor = os.open(
            path.name, os.O_WRONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent
        )
        with os.fdopen(descriptor, "wb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise BundleError("unsafe", "Formatter target is not a regular file")
            os.ftruncate(stream.fileno(), 0)
            stream.write(formatted["document"].encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())
    results = []
    for operation, flags in [
        ("format", ["--check"]),
        ("validate", []),
        ("vet", []),
        ("lint", ["--warnings-as-errors"]),
    ]:
        payload = client.read(
            ["procedure", operation, *flags, "--", relative],
            "procedure." + operation,
            {
                "podway.procedure-source-result/v1",
                "podway.procedure-diagnostics-result/v1",
            }
            if operation == "format"
            else {"podway.procedure-diagnostics-result/v1"},
        )
        results.append({"command": "procedure." + operation, "result": payload})
    preview = client.preview(path)
    return preview, {
        "identity": identity,
        "checks": results,
        "check_and_preview": preview,
    }


def allocate_identity(repository, roots, family, draft):
    used = {}
    entries, _ = discover(
        repository,
        {"discovery_roots": [str(root.relative_to(repository)) for root in roots]},
    )
    for entry in entries:
        used.setdefault(entry["id"], set()).add(str(entry["version"]))
    if draft.get("revision_of"):
        _, base = document(repository, draft["revision_of"])
        identifier = base["id"]
        if not re.fullmatch(
            r"aquarium-adapt-" + family + r"-[a-z0-9]+(?:-[a-z0-9]+)*", identifier
        ) or not re.fullmatch(r"[1-9][0-9]*", base["version"]):
            raise BundleError(
                "incompatible",
                "Only an adaptive identity can receive an authored revision",
            )
        versions = used.get(identifier, set()) | {base["version"]}
        if any(not re.fullmatch(r"[1-9][0-9]*", version) for version in versions):
            raise BundleError(
                "incompatible", "Adaptive revision history is not positive decimal"
            )
        version = str(max(map(int, versions)) + 1)
    else:
        identifier = "aquarium-adapt-" + family + "-" + uuid.uuid4().hex
        while identifier in used:
            identifier = "aquarium-adapt-" + family + "-" + uuid.uuid4().hex
        version = "1"
    if len(identifier) > 64 or len(version) > 64:
        raise BundleError("incompatible", "Generated identity exceeds native limits")
    return identifier, version


def check_basis(repository, assignment, selected):
    if selected.get("composition_bases"):
        from adaptive_composition import check_bases

        check_bases(repository, selected["composition_bases"])
    requirements(repository, assignment)
    if source_authority(repository, assignment) != selected["plan"]["source_authority"]:
        raise BundleError(
            "source-drift", "Managed source authority changed during preparation"
        )
    if selected["kind"] == "reuse":
        raw, _ = document(repository, selected["entry"])
        if raw != selected["source"]:
            raise BundleError("source-drift", "Reuse source changed during preparation")
        if selected["entry"].get("binding"):
            read_basis(repository, selected["entry"]["binding"])
    for key in ("base", "revision_of"):
        if selected["entry"].get(key):
            document(repository, selected["entry"][key])


def verify_directory(repository, path, descriptor):
    with directory(repository, path) as current:
        if (os.fstat(current).st_dev, os.fstat(current).st_ino) != (
            os.fstat(descriptor).st_dev,
            os.fstat(descriptor).st_ino,
        ):
            raise BundleError(
                "unsafe", "Candidate directory changed during preparation"
            )


def cleanup_owned(parent, name, stage, failure):
    try:
        entry = os.stat(name, dir_fd=parent, follow_symlinks=False)
    except FileNotFoundError:
        return
    if (entry.st_dev, entry.st_ino) != (os.fstat(stage).st_dev, os.fstat(stage).st_ino):
        return
    try:
        for filename in ("procedure.yaml", "binding.json"):
            with contextlib.suppress(FileNotFoundError):
                os.unlink(filename, dir_fd=stage)
        os.rmdir(name, dir_fd=parent)
    except OSError as error:
        raise BundleError(
            "runtime-failure",
            "Owned preparation stage could not be cleaned",
            {
                "stage": name,
                "cleanup_error": str(error),
                "preparation_failure": getattr(failure, "code", None),
            },
        ) from error


def write_new(descriptor, name, content):
    output = os.open(
        name,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o600,
        dir_fd=descriptor,
    )
    with os.fdopen(output, "wb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    os.fsync(descriptor)


def prepare(repository, assignment, *, client=None, bootstrap=False, opt_out=False):
    from adaptive_entrypoint import EntryPointError, branch

    target = assignment.get("target", {}) if isinstance(assignment, dict) else {}
    plan = target.get("procedure_plan", {}) if isinstance(target, dict) else {}
    entrypoint = plan.get("entrypoint") if isinstance(plan, dict) else None
    try:
        skipped = branch(repository, entrypoint, opt_out=opt_out)
    except EntryPointError as error:
        raise BundleError(error.code, str(error)) from error
    if skipped is not None:
        return skipped
    repository = Path(repository).expanduser().resolve()
    selected = select(repository, assignment, client=client)
    plan = assignment["target"]["procedure_plan"]
    if plan["mode"] == "plan-only":
        return {
            "status": "planned",
            "selection": {
                key: value
                for key, value in selected.items()
                if key not in {"source", "document", "mapping", "entry"}
            },
            "writes": [],
            "native_checks": "not-run",
        }
    if plan["mode"] != "prepare":
        raise BundleError("incompatible", "Preparation mode is unsupported")
    grant = assignment["authority"].get("preparation")
    if (
        not isinstance(grant, dict)
        or grant.get("native_authoring") is not True
        or client is None
    ):
        raise BundleError(
            "authority-required",
            "Existing envelope must cover native source preparation",
        )
    if Path(client.repository).resolve() != repository:
        raise BundleError(
            "unsafe", "Native source checks must use the preparation worktree"
        )
    roots = roots_for(repository, grant["roots"])
    write_root = contained(repository, Path(grant["write_root"]))
    if write_root not in roots or any(
        root not in roots for root in roots_for(repository, plan["discovery_roots"])
    ):
        raise BundleError(
            "authority-required",
            "Preparation locations differ from disclosed discovery/write scope",
        )
    check_basis(repository, assignment, selected)
    with publication_lock(repository):
        native = copy.deepcopy(selected["document"])
        if selected["kind"] != "reuse":
            qualification = assignment["target"].get("qualification_context", {})
            for invocation, retained in [
                ("operation_contracts", "semantic_contracts"),
                ("signatures", "capability_definitions"),
            ]:
                if qualification.get(invocation):
                    destination = selected["mapping"].setdefault(retained, {})
                    for key, value in qualification[invocation].items():
                        if key in destination and destination[key] != value:
                            raise BundleError(
                                "incompatible",
                                "Conflicting retained semantic definition",
                            )
                        destination[key] = copy.deepcopy(value)
        if bootstrap and selected["kind"] != "reuse":
            from adaptive_suitability import add_bootstrap

            native, selected["mapping"] = add_bootstrap(native, selected["mapping"])
        if selected["kind"] != "reuse":
            native["id"], native["version"] = allocate_identity(
                repository, roots, plan["family"], selected["entry"]
            )
        temporary = ".prepare-" + uuid.uuid4().hex
        # Ignore and tracked-target checks precede every definition-byte write.
        local = _ignored_local(
            repository, write_root, temporary, local_name=".candidates"
        )
        stage = local / temporary
        with directory(repository, local) as parent:
            os.mkdir(temporary, dir_fd=parent)
            stage_descriptor = os.open(
                temporary, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent
            )
            try:
                if selected.get("composition_bases"):
                    from adaptive_composition import verify_whole_sources

                    verify_whole_sources(
                        repository,
                        selected["composition_bases"],
                        client,
                        stage,
                        stage_descriptor,
                    )
                source = (
                    selected["source"]
                    if selected["kind"] == "reuse"
                    else yaml.dump(
                        native,
                        Dumper=ProcedureDumper,
                        sort_keys=False,
                        allow_unicode=True,
                        width=float("inf"),
                    ).encode("utf-8")
                )
                write_new(stage_descriptor, "procedure.yaml", source)
                verify_directory(repository, local, parent)
                verify_directory(repository, stage, stage_descriptor)
                semantic_before = None
                if selected["mapping"].get("semantic_contracts"):
                    validation = client.read(
                        [
                            "procedure",
                            "validate",
                            "--",
                            str((stage / "procedure.yaml").relative_to(repository)),
                        ],
                        "procedure.validate",
                        {"podway.procedure-diagnostics-result/v1"},
                    )
                    if not isinstance(validation.get("digest"), str):
                        raise BundleError(
                            "unsupported-runtime",
                            "Native validation lacks semantic source identity",
                        )
                    semantic_before = (
                        native["id"],
                        native["version"],
                        validation["digest"],
                    )
                preview, observations = author_checks(
                    client,
                    stage / "procedure.yaml",
                    format_source=selected["kind"] != "reuse",
                    stage_descriptor=stage_descriptor,
                )
                source = read_regular(repository, stage / "procedure.yaml")
                if semantic_before is not None:
                    observations["semantic_contract_validation"] = {
                        "native": validation,
                        "pre_format_tuple": semantic_before,
                        "post_format_tuple": [
                            preview[key]
                            for key in (
                                "procedure_id",
                                "procedure_version",
                                "procedure_digest",
                            )
                        ],
                    }
                    if tuple(semantic_before) != tuple(
                        preview[key]
                        for key in (
                            "procedure_id",
                            "procedure_version",
                            "procedure_digest",
                        )
                    ):
                        raise BundleError(
                            "source-drift",
                            "Native formatting changed the semantic contract target",
                        )
                    actual_definitions = yaml.safe_load(source)["node_definitions"]
                    contracts = selected["mapping"]["semantic_contracts"]
                    for key, definition in native["node_definitions"].items():
                        contract = contracts.get(sha256(canonical_json(definition)))
                        if contract is not None:
                            identity = sha256(canonical_json(actual_definitions[key]))
                            if (
                                identity in contracts
                                and contracts[identity] != contract
                            ):
                                raise BundleError(
                                    "incompatible",
                                    "Formatted semantic contract identity conflicts",
                                )
                            contracts[identity] = copy.deepcopy(contract)
                if selected["kind"] == "reuse":
                    binding = (
                        selected["mapping"]
                        if "procedure" in selected["mapping"]
                        else reference_binding(source, preview)
                    )
                    if selected.get("known_adaptive"):
                        from adaptive_suitability import established_reuse

                        established_reuse(
                            repository,
                            source,
                            binding,
                            client=client,
                            roots=grant["roots"],
                            prior=selected["prior_suitability"],
                            criteria=requirements(repository, assignment),
                            context={
                                **assignment["target"].get("qualification_context", {}),
                                "review": assignment["authority"]["review"],
                            },
                        )
                    else:
                        qualify_known(source, binding, preview)
                else:
                    binding = {
                        **selected["mapping"],
                        "procedure": {
                            "id": native["id"],
                            "version": native["version"],
                            "digest": preview["procedure_digest"],
                            "source_sha256": sha256(source),
                        },
                    }
                    validate_definition(binding)
                expected = (
                    binding["procedure"]["id"],
                    binding["procedure"]["version"],
                    binding["procedure"]["digest"],
                )
                if (
                    tuple(client.identity(stage / "procedure.yaml")) != expected
                    or sha256(read_regular(repository, stage / "procedure.yaml"))
                    != binding["procedure"]["source_sha256"]
                ):
                    raise BundleError(
                        "source-drift",
                        "Exact source changed during native verification",
                    )
                check_basis(repository, assignment, selected)
                candidate = definition_id(binding)
                _ignored_local(
                    repository, write_root, candidate, local_name=".candidates"
                )
                write_new(stage_descriptor, "binding.json", canonical_json(binding))
                verify_directory(repository, local, parent)
                verify_directory(repository, stage, stage_descriptor)
                output = local / candidate
                with directory(repository, output, allow_missing=True) as existing:
                    if existing is not None:
                        retained = verified_bundle(repository, output)
                        if (
                            retained["source"] != source
                            or retained["binding"] != binding
                            or tuple(client.identity(output / "procedure.yaml"))
                            != expected
                        ):
                            raise BundleError(
                                "corrupt", "Existing prepared candidate differs"
                            )
                    else:
                        try:
                            _rename_exclusive(parent, temporary, candidate)
                        except FileExistsError as error:
                            raise BundleError(
                                "publication-conflict",
                                "A competing candidate target was preserved",
                            ) from error
                        os.fsync(parent)
                local_status(repository, output)
                verify_directory(repository, local, parent)
                retained = verified_bundle(repository, output)
                if (
                    retained["binding"] != binding
                    or retained["source"] != source
                    or tuple(client.identity(output / "procedure.yaml")) != expected
                ):
                    raise BundleError(
                        "corrupt", "Published candidate could not be verified"
                    )
            finally:
                failure = sys.exc_info()[1]
                try:
                    cleanup_owned(parent, temporary, stage_descriptor, failure)
                finally:
                    os.close(stage_descriptor)
    result = copy.deepcopy(assignment)
    result["target"]["prepared_definition"] = {
        "kind": selected["kind"],
        "reason": selected["reason"],
        "bundle_id": definition_id(binding),
        "procedure": binding["procedure"],
        "path": str(output),
        "source_path": str(output / "procedure.yaml"),
        "binding_path": str(output / "binding.json"),
        "coverage_plan": selected["plan"],
        "assessment": selected["assessment"],
        "adoption": "not-performed",
        **(
            {"prior_suitability": selected["prior_suitability"]}
            if selected.get("known_adaptive")
            else {}
        ),
        "storage": {
            "directory": str(local),
            "permitted_local_effects": [
                "Create disclosed candidate directories",
                "Exclusively create local self-ignore policy when needed",
                "Retain complete execution-definition source and binding",
            ],
        },
        "native": observations,
    }
    if selected.get("known_adaptive"):
        from adaptive_suitability import current_basis

        result["target"]["prepared_definition"]["reuse_basis"] = current_basis(
            repository, result
        )
    return {
        "status": "prepared",
        "assignment": result,
        "binding": binding,
        "considered": selected["considered"],
        "qualification": selected["assessment"],
        "activation": "unchanged-handlers",
    }
