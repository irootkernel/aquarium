"""Definition identities and declaration signatures; not runtime admission."""

import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator

ASSETS = Path(__file__).resolve().parents[1] / "assets"
FAMILY_ENTRYPOINTS = {
    "task": {"task-handler"},
    "goal": {"epic-handler"},
    "validation": {"epic-validator", "epic-handler"},
    "design": {"new-feature", "new-project", "refactor"},
    "diagnosis": {"war-room"},
}
SCHEMAS = {
    "aquarium.procedure-binding/v1": "procedure-binding-v1.schema.json",
    "aquarium.procedure-fragment/v1": "procedure-fragment-v1.schema.json",
}


class DefinitionError(ValueError):
    """Invalid Aquarium definition, distinct from native Procedure validity."""


def canonical_json(value):
    """Return the Aquarium UTF-8 definition bytes, without a trailing newline."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def definition_id(value):
    return hashlib.sha256(canonical_json(value)).hexdigest()


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise DefinitionError(f"Duplicate JSON field: {key}")
        result[key] = value
    return result


def _invalid_constant(value):
    raise DefinitionError(f"Non-finite JSON number: {value}")


def parse_definition(data):
    """Parse a closed definition; byte canonicality is checked when retained."""
    try:
        value = json.loads(
            data.decode("utf-8") if isinstance(data, bytes) else data,
            object_pairs_hook=_unique_pairs,
            parse_constant=_invalid_constant,
        )
        canonical_json(value)
    except (UnicodeError, ValueError, TypeError) as exc:
        raise DefinitionError(str(exc)) from exc
    validate_definition(value)
    return value


def validate_definition(value):
    try:
        canonical_json(value)
    except (UnicodeError, ValueError, TypeError) as exc:
        raise DefinitionError(str(exc)) from exc
    discriminator = value.get("schema") if isinstance(value, dict) else None
    schema_name = SCHEMAS.get(discriminator) if isinstance(discriminator, str) else None
    if schema_name is None:
        raise DefinitionError("Unsupported Aquarium definition schema")
    schema = json.loads((ASSETS / "schemas" / schema_name).read_text())
    errors = list(Draft202012Validator(schema).iter_errors(value))
    if errors:
        error = errors[0]
        location = "/".join(str(part) for part in error.absolute_path)
        raise DefinitionError(f"{location or '/'}: {error.message}")
    if value["schema"] == "aquarium.procedure-fragment/v1":
        _validate_fragment(value)
    else:
        nodes = value["nodes"]
        if not nodes:
            raise DefinitionError("Binding requires native placements")
        for declaration in value["goal_assessments"] + value["closeout"]:
            if declaration["node"] not in nodes:
                raise DefinitionError(f"Unknown boundary: {declaration['node']}")
        for declaration in value["closeout"]:
            if any(node not in nodes for node in declaration["requires"]):
                raise DefinitionError("Closeout requires an unknown placement")
        for obligation in value["obligations"].values():
            endpoints = obligation["producers"] + obligation["evidence"]
            references = [e["node"] for e in endpoints] + [obligation["decision"]]
            if obligation["assessor"] is not None:
                references.append(obligation["assessor"])
            if any(node not in nodes for node in references):
                raise DefinitionError("Obligation references an unknown placement")
    return value


def _validate_fragment(value):
    definitions = value["node_definitions"]
    placements = value["placements"]
    ids = [node.get("id") for node in placements]
    if any(not isinstance(node, str) or not node for node in ids) or len(
        set(ids)
    ) != len(ids):
        raise DefinitionError("Fragment placement IDs must be unique nonempty strings")
    known = set(ids)
    by_id = dict(zip(ids, placements))
    if value["entry"] not in known or not value["exits"]:
        raise DefinitionError("Fragment requires one declared entry and named exits")
    if any(node not in known for node in value["exits"].values()):
        raise DefinitionError("Fragment exit references an unknown placement")
    for node in placements:
        if not isinstance(node.get("use"), str) or node["use"] not in definitions:
            raise DefinitionError("Fragment placement references an unknown definition")
    for definition in definitions.values():
        assessment = definition.get("assessment")
        if isinstance(assessment, dict) and assessment.get("target") == "session_goal":
            raise DefinitionError(
                "Ordinary work fragments cannot assess the session goal"
            )
    for port in list(value["inputs"].values()) + list(value["outputs"].values()):
        if port["endpoint"]["node"] not in known:
            raise DefinitionError("Fragment port references an unknown placement")
        placement = by_id[port["endpoint"]["node"]]
        definition = definitions[placement["use"]]
        if definition.get("type") == "action":
            items = definition.get("items", [])
            if not isinstance(items, list) or not any(
                isinstance(item, dict) and item.get("id") == port["endpoint"]["item"]
                for item in items
            ):
                raise DefinitionError("Fragment port references an unknown Action item")
    for edge in value["internal_rework"]:
        if edge["from"] not in known or edge["to"] not in known:
            raise DefinitionError("Internal rework must stay inside its fragment")
    for edge in value["external_rework"].values():
        if edge["from"] not in known:
            raise DefinitionError("External rework references an unknown placement")
    for assessor in value["assessors"]:
        if assessor["node"] not in known or any(
            n not in known for n in assessor["covers"]
        ):
            raise DefinitionError("Assessor boundary references an unknown placement")


def native_key(binding):
    validate_definition(binding)
    if binding["schema"] != "aquarium.procedure-binding/v1":
        raise DefinitionError("Only bindings have a native recovery key")
    procedure = binding["procedure"]
    return procedure["id"], procedure["version"], procedure["digest"]


def capability_signatures():
    return json.loads(
        (ASSETS / "adaptive" / "capability-signatures-v1.json").read_text()
    )


def check_capability(
    definition, signature_id, fields=None, *, signatures=None, criterion_capacity=None
):
    """Check necessary native declarations, leaving evidence/graph proof separate.

    Fields maps semantic signature names to native item aliases. Callers may supply
    an explicitly verified signature registry for a newly defined operation.
    A compatible result proves only this declaration slice, never independence,
    suitability, authority, complete native validity or whole-graph compatibility.
    criterion_capacity, when supplied, is a caller-established upper bound from
    this assessment's exact original criterion basis, not a graph label or digest.
    """
    registry = capability_signatures() if signatures is None else signatures
    signature = registry.get(signature_id)
    if signature is None:
        return {
            "status": "not-established",
            "gaps": [f"Unknown signature: {signature_id}"],
        }
    if definition.get("type") != signature["kind"]:
        return {"status": "incompatible", "gaps": ["Native declaration kind differs"]}
    fields = {} if fields is None else fields
    gaps = []
    unknowns = []
    if signature["kind"] == "decision":
        options = {option["id"] for option in definition.get("options", [])}
        if not set(signature["options"]) <= options:
            gaps.append("Missing required approval options")
        if not definition.get("reason", {}).get("required"):
            gaps.append("Approval reason must be required")
    else:
        items = {item["id"]: item for item in definition.get("items", [])}
        aliases = [fields.get(name, name) for name in signature["fields"]]
        if len(set(aliases)) != len(aliases):
            gaps.append("Typed aliases collapse distinct signature fields")
        for name, expected in signature["fields"].items():
            actual = items.get(fields.get(name, name))
            if actual is None:
                gaps.append(f"Missing required field: {name}")
                continue
            if name in signature.get("criterion_counts", []) and "maximum" in actual:
                capacity_proven = (
                    isinstance(criterion_capacity, int)
                    and not isinstance(criterion_capacity, bool)
                    and criterion_capacity >= 0
                )
                maximum = actual["maximum"]
                if not capacity_proven:
                    unknowns.append(
                        f"{name}: bounded count needs exact criterion capacity"
                    )
                elif not isinstance(maximum, int) or isinstance(maximum, bool):
                    gaps.append(f"{name}: invalid maximum")
                elif maximum < criterion_capacity:
                    gaps.append(f"{name}: maximum cannot record all mandatory gaps")
            for key, wanted in expected.items():
                observed = actual.get(key)
                if key in {"choices", "accepted_outcomes", "allowed_media_types"}:
                    matches = isinstance(observed, list) and set(wanted) <= set(
                        observed
                    )
                elif actual.get("required") is True and (
                    key == "required_when"
                    or (key == "required" and "required_when" in expected)
                ):
                    matches = True
                elif key == "required_when":
                    wanted = [
                        {
                            **condition,
                            "item": fields.get(condition["item"], condition["item"]),
                        }
                        for condition in wanted
                    ]
                    matches = observed == wanted
                    if not matches and observed:
                        unknowns.append(f"{name}: changed conditional requiredness")
                        continue
                else:
                    matches = observed == wanted
                if not matches:
                    gaps.append(f"{name}: incompatible {key}")
    status = "incompatible" if gaps else "not-established" if unknowns else "compatible"
    return {"status": status, "gaps": gaps + unknowns}
