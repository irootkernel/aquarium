"""Closed definitions and necessary signatures, without admission/runtime claims."""

import copy
import importlib.util
import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "plugins/aquarium"
spec = importlib.util.spec_from_file_location(
    "adaptive_definitions", PLUGIN / "shared/adaptive_definitions.py"
)
adaptive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adaptive)
FIXTURES = ROOT / "tests/fixtures/adaptive"


def example(name="documentation.binding.json"):
    return adaptive.parse_definition((FIXTURES / name).read_bytes())


def source(family):
    return yaml.safe_load(
        (PLUGIN / f"assets/podway/procedures/aquarium-{family}-v2.yaml").read_text()
    )


def test_schemas_and_canonical_examples():
    for schema in adaptive.SCHEMAS.values():
        Draft202012Validator.check_schema(
            json.loads((PLUGIN / "assets/schemas" / schema).read_text())
        )
    for path in FIXTURES.glob("*.json"):
        value = adaptive.parse_definition(path.read_bytes())
        assert adaptive.canonical_json(value) == path.read_bytes()


def test_canonical_identity_preserves_unicode_and_array_order():
    assert adaptive.canonical_json({"z": "한글", "a": [2, 1]}) == (
        '{"a":[2,1],"z":"한글"}'.encode()
    )
    value = example()
    reordered = copy.deepcopy(dict(reversed(list(value.items()))))
    assert adaptive.definition_id(value) == adaptive.definition_id(reordered)
    value["procedure"]["source_sha256"] = "sha256:" + "c" * 64
    assert adaptive.definition_id(value) != adaptive.definition_id(reordered)


@pytest.mark.parametrize(
    "payload",
    [b'{"schema":"one","schema":"two"}', b'{"a":NaN}', b'{"a":1e999}', b"\xff"],
)
def test_unsafe_json_rejects(payload):
    with pytest.raises(adaptive.DefinitionError):
        adaptive.parse_definition(payload)


@pytest.mark.parametrize(
    "field", ["session_id", "approval", "bundle_id", "path", "results"]
)
def test_binding_has_no_runtime_or_self_identity_fields(field):
    value = example()
    value[field] = "not-definition-data"
    with pytest.raises(adaptive.DefinitionError):
        adaptive.validate_definition(value)


def test_binding_exact_tuple_and_source_bytes_are_distinct():
    value = example()
    key = adaptive.native_key(value)
    value["procedure"]["source_sha256"] = "sha256:" + "c" * 64
    assert adaptive.native_key(value) == key
    value["procedure"]["digest"] = "sha256:" + "d" * 64
    assert adaptive.native_key(value) != key


@pytest.mark.parametrize("version", ["0", "-1", "01", 1, "1\n"])
def test_native_version_requires_positive_decimal_string(version):
    value = example()
    value["procedure"]["version"] = version
    with pytest.raises(adaptive.DefinitionError):
        adaptive.validate_definition(value)


@pytest.mark.parametrize("family,entrypoints", adaptive.FAMILY_ENTRYPOINTS.items())
def test_family_overlays_share_definition(family, entrypoints):
    value = example()
    value.update(family=family, entrypoints=sorted(entrypoints))
    value["procedure"]["id"] = f"aquarium-adapt-{family}-documentation-example"
    adaptive.validate_definition(value)
    value["entrypoints"].append("war-room" if family != "diagnosis" else "task-handler")
    with pytest.raises(adaptive.DefinitionError):
        adaptive.validate_definition(value)


def test_fragments_exclude_parent_goal_and_require_local_boundaries():
    value = example("documentation.fragment.json")
    value["node_definitions"]["assess"]["assessment"] = {
        "target": "session_goal",
        "outcomes": {"pass": "achieved"},
    }
    with pytest.raises(adaptive.DefinitionError):
        adaptive.validate_definition(value)
    value = example("documentation.fragment.json")
    value["internal_rework"].append({"from": "assess", "to": "other/private-node"})
    with pytest.raises(adaptive.DefinitionError):
        adaptive.validate_definition(value)


@pytest.mark.parametrize("family", ["task", "goal", "validation", "design", "war-room"])
def test_canonical_final_assessment_positive_control(family):
    definition = source(family)["node_definitions"]["final-judge-assessment-record"]
    signature = (
        "aquarium."
        + ("diagnosis" if family == "war-room" else family)
        + ".final-assessment/v1"
    )
    assert adaptive.check_capability(definition, signature)["status"] == "compatible"
    wrong = copy.deepcopy(definition)
    next(i for i in wrong["items"] if i["id"] == "judge-verdict")["type"] = "text"
    assert adaptive.check_capability(wrong, signature)["status"] == "incompatible"


def test_namespaces_typed_aliases_and_extra_bookkeeping_are_supported():
    definition = source("task")["node_definitions"]["final-judge-assessment-record"]
    aliases = {item["id"]: "typed-" + item["id"] for item in definition["items"]}
    for item in definition["items"]:
        item["id"] = aliases[item["id"]]
    definition["items"].append(
        {"id": "unrelated-note", "type": "text", "required": False}
    )
    result = adaptive.check_capability(
        definition, "aquarium.task.final-assessment/v1", aliases
    )
    assert result["status"] == "compatible"
    aliases["judge-verdict"] = aliases["judge-assessment"]
    assert (
        adaptive.check_capability(
            definition, "aquarium.task.final-assessment/v1", aliases
        )["status"]
        == "incompatible"
    )


def test_negative_results_record_but_unrelated_pass_only_checks_are_allowed():
    definition = source("task")["node_definitions"]["final-judge-assessment-record"]
    applicability = next(
        i for i in definition["items"] if i["id"] == "judge-applicability"
    )
    applicability["accepted_outcomes"] = ["pass"]
    assert (
        adaptive.check_capability(definition, "aquarium.task.final-assessment/v1")[
            "status"
        ]
        == "incompatible"
    )
    applicability["accepted_outcomes"] += ["fail", "inconclusive"]
    definition["items"].append(
        {"id": "unrelated-check", "type": "check_result", "accepted_outcomes": ["pass"]}
    )
    assert (
        adaptive.check_capability(definition, "aquarium.task.final-assessment/v1")[
            "status"
        ]
        == "compatible"
    )


def test_unknown_operations_are_not_established_and_explicit_extensions_work():
    definition = source("task")["node_definitions"]["final-judge-assessment-record"]
    signature = "aquarium.example.changed-assessment/v1"
    assert (
        adaptive.check_capability(definition, signature)["status"] == "not-established"
    )
    registry = {
        signature: adaptive.capability_signatures()["aquarium.task.final-assessment/v1"]
    }
    assert (
        adaptive.check_capability(definition, signature, signatures=registry)["status"]
        == "compatible"
    )
    applicability = next(
        i for i in definition["items"] if i["id"] == "judge-applicability"
    )
    applicability["operation_digest"] = "sha256:" + "0" * 64
    assert (
        adaptive.check_capability(definition, signature, signatures=registry)["status"]
        == "incompatible"
    )


def test_binding_rejects_unknown_boundary_without_inventing_goal_success():
    value = example()
    value["goal_assessments"][0]["node"] = "missing"
    with pytest.raises(adaptive.DefinitionError):
        adaptive.validate_definition(value)
    value = example()
    value["goal_assessments"][0]["outcomes"]["done"] = "completed"
    with pytest.raises(adaptive.DefinitionError):
        adaptive.validate_definition(value)


def test_reference_registry_matches_current_native_operation_declarations():
    families = {"diagnosis": "war-room"}
    for name in adaptive.capability_signatures():
        family = name.split(".")[1]
        if family == "shared":
            from adaptive_suitability import add_bootstrap

            native = yaml.safe_load(
                (
                    PLUGIN / "assets/adaptive/reusable/task-goal-control.yaml"
                ).read_bytes()
            )
            mapping = json.loads(
                (
                    PLUGIN / "assets/adaptive/reusable/task-goal-control.binding.json"
                ).read_bytes()
            )
            definitions = add_bootstrap(native, mapping)[0]["node_definitions"]
        else:
            definitions = source(families.get(family, family))["node_definitions"]
        assert any(
            adaptive.check_capability(definition, name)["status"] == "compatible"
            for definition in definitions.values()
        ), name


def test_genuine_work_and_evidence_structures_share_the_definition_interface():
    documents = example()
    performance = example("performance.binding.json")
    assert len(performance["nodes"]) > len(documents["nodes"])
    docs_obligation = documents["obligations"]["documentation"]
    perf_obligation = performance["obligations"]["performance"]
    assert len(perf_obligation["producers"]) == 2
    assert len(perf_obligation["evidence"]) > len(docs_obligation["evidence"])
    assert perf_obligation["decision"] != performance["goal_assessments"][0]["node"]
    assert docs_obligation["decision"] == documents["goal_assessments"][0]["node"]


def test_unchanged_foreign_native_versions_are_preserved():
    value = example()
    value["procedure"].update(id="foreign-definition", version="release-a")
    adaptive.validate_definition(value)
    assert adaptive.native_key(value)[1] == "release-a"


def test_worker_handoff_label_cannot_supply_assessment_signature():
    worker = source("goal")["node_definitions"]["work-record"]
    assert (
        adaptive.check_capability(worker, "aquarium.goal.final-assessment/v1")["status"]
        == "incompatible"
    )


@pytest.mark.parametrize("family", ["task", "goal", "validation", "design", "war-room"])
def test_native_goal_mapping_and_shared_closeout_are_representable(family):
    native = source(family)
    value = example()
    bound_family = "diagnosis" if family == "war-room" else family
    value.update(
        family=bound_family,
        entrypoints=sorted(adaptive.FAMILY_ENTRYPOINTS[bound_family]),
    )
    value["procedure"].update(id=native["id"], version=native["version"])
    value["nodes"] = {
        node["id"]: {
            "kind": native["node_definitions"][node["use"]]["type"],
            "role": "orchestrator",
            "effects": [],
            "capabilities": [],
        }
        for node in native["graph"]["nodes"]
    }
    value["obligations"] = {}
    value["goal_assessments"] = [
        {
            "node": node["id"],
            "outcomes": native["node_definitions"][node["use"]]["assessment"][
                "outcomes"
            ],
        }
        for node in native["graph"]["nodes"]
        if native["node_definitions"][node["use"]].get("assessment", {}).get("target")
        == "session_goal"
    ]
    terminal = next(
        node["id"] for node in native["graph"]["nodes"] if node.get("terminal")
    )
    value["closeout"] = [{"node": terminal, "kind": "shared", "requires": []}]
    adaptive.validate_definition(value)
    assert native["goal_tracking"] is True
    outcomes = {
        outcome
        for mapping in value["goal_assessments"]
        for outcome in mapping["outcomes"].values()
    }
    assert {"achieved", "not_achieved", "superseded"} <= outcomes


def test_selected_provider_and_unused_outcome_specializations_are_supported():
    review = source("goal")["node_definitions"]["evidence-record"]
    for item in review["items"]:
        if item["id"] == "review-route":
            item["choices"] = ["herdr"]
        elif item["id"] == "prior-review-route":
            item["choices"] = ["not-applicable", "herdr"]
    assert (
        adaptive.check_capability(review, "aquarium.goal.review-routing/v1")["status"]
        == "compatible"
    )
    final = source("goal")["node_definitions"]["final-judge-assessment-record"]
    next(i for i in final["items"] if i["id"] == "judge-goal-outcome")["choices"] = [
        "achieved",
        "not-achieved",
    ]
    assert (
        adaptive.check_capability(final, "aquarium.goal.final-assessment/v1")["status"]
        == "compatible"
    )
    approval = source("goal")["node_definitions"]["approval-decision"]
    approval["options"] = [o for o in approval["options"] if o["id"] != "delegated"]
    assert (
        adaptive.check_capability(approval, "aquarium.goal.approval/v1")["status"]
        == "compatible"
    )


def test_changed_conditional_requirement_needs_proof_but_stronger_requirement_matches():
    review = source("goal")["node_definitions"]["evidence-record"]
    item = next(
        i for i in review["items"] if i["id"] == "assessment-ordinal-continuity"
    )
    item["required_when"] = [{"item": "another-selector", "equals": "review"}]
    assert (
        adaptive.check_capability(review, "aquarium.goal.review-control/v1")["status"]
        == "not-established"
    )
    item["required"] = True
    item.pop("required_when")
    assert (
        adaptive.check_capability(review, "aquarium.goal.review-control/v1")["status"]
        == "compatible"
    )


def test_origin_versions_preserve_foreign_sources_and_parameters_exclude_run_values():
    value = example()
    value["origins"] = [
        {
            "id": "foreign-source",
            "version": "release-a",
            "sha256": "sha256:" + "e" * 64,
            "source": "reusable/foreign/procedure.yaml",
        }
    ]
    adaptive.validate_definition(value)
    value["parameters"]["document"]["value"] = "this-run-document.md"
    with pytest.raises(adaptive.DefinitionError):
        adaptive.validate_definition(value)


@pytest.mark.parametrize("family", ["task", "goal", "validation", "design", "war-room"])
def test_every_required_canonical_judge_and_quality_operation_has_a_signature(family):
    registry = adaptive.capability_signatures()
    bound_family = "diagnosis" if family == "war-room" else family
    quality_operations = {"aquarium-design-quality", "aquarium-diagnostic-quality"}
    for definition in source(family)["node_definitions"].values():
        items = definition.get("items", [])
        operations = {i["operation_id"] for i in items if "operation_id" in i}
        if (
            not any(i["id"] == "judge-assessment" for i in items)
            and not operations & quality_operations
        ):
            continue
        matched_operations = set()
        for name, signature in registry.items():
            if (
                name.startswith(f"aquarium.{bound_family}.")
                and adaptive.check_capability(definition, name)["status"]
                == "compatible"
            ):
                matched_operations.update(
                    field["operation_id"]
                    for field in signature.get("fields", {}).values()
                    if "operation_id" in field
                )
        assert operations <= matched_operations, operations - matched_operations


@pytest.mark.parametrize("field", ["judge-unmet-criteria", "judge-unverified-criteria"])
@pytest.mark.parametrize("maximum", [0, 1, 7])
def test_mandatory_gap_capacity_needs_exact_proof(field, maximum):
    definition = source("task")["node_definitions"]["final-judge-assessment-record"]
    next(i for i in definition["items"] if i["id"] == field)["maximum"] = maximum
    signature = "aquarium.task.final-assessment/v1"
    assert (
        adaptive.check_capability(definition, signature)["status"] == "not-established"
    )
    assert (
        adaptive.check_capability(definition, signature, criterion_capacity=maximum)[
            "status"
        ]
        == "compatible"
    )
    assert (
        adaptive.check_capability(
            definition, signature, criterion_capacity=maximum + 1
        )["status"]
        == "incompatible"
    )
    definition["items"].append(
        {
            "id": "unrelated-count",
            "type": "integer",
            "required": True,
            "minimum": 0,
            "maximum": 0,
        }
    )
    assert (
        adaptive.check_capability(definition, signature, criterion_capacity=maximum)[
            "status"
        ]
        == "compatible"
    )


@pytest.mark.parametrize("discriminator", [[], {}, None, 1, True])
def test_non_string_schema_is_a_definition_error(discriminator):
    with pytest.raises(adaptive.DefinitionError):
        adaptive.parse_definition(json.dumps({"schema": discriminator}))


@pytest.mark.parametrize("family", adaptive.FAMILY_ENTRYPOINTS)
def test_adaptive_identity_requires_its_actual_family_and_nonempty_token(family):
    value = example()
    value.update(family=family, entrypoints=sorted(adaptive.FAMILY_ENTRYPOINTS[family]))
    value["procedure"]["id"] = f"aquarium-adapt-{family}-token"
    adaptive.validate_definition(value)
    other = "goal" if family != "goal" else "task"
    for identity in [
        f"aquarium-adapt-{other}-token",
        f"aquarium-adapt-{family}",
        f"aquarium-adapt-{family}-",
    ]:
        value["procedure"]["id"] = identity
        with pytest.raises(adaptive.DefinitionError):
            adaptive.validate_definition(value)
    value["procedure"].update(id="foreign-source", version="release-a")
    adaptive.validate_definition(value)


@pytest.mark.parametrize("mutation", ["missing-rejection", "optional-reason"])
def test_approval_negative_controls(mutation):
    definition = source("goal")["node_definitions"]["approval-decision"]
    if mutation == "missing-rejection":
        definition["options"] = [
            option
            for option in definition["options"]
            if option["id"] != "changes-requested"
        ]
    else:
        definition["reason"]["required"] = False
    assert (
        adaptive.check_capability(definition, "aquarium.goal.approval/v1")["status"]
        == "incompatible"
    )


@pytest.mark.parametrize("mutation", ["closeout-prerequisite", "obligation-evidence"])
def test_binding_placement_reference_negative_controls(mutation):
    value = example()
    if mutation == "closeout-prerequisite":
        value["closeout"][0]["requires"].append("missing")
    else:
        value["obligations"]["documentation"]["evidence"][0]["node"] = "missing"
    with pytest.raises(adaptive.DefinitionError):
        adaptive.validate_definition(value)


@pytest.mark.parametrize("mutation", ["port-item", "port-node", "exit"])
def test_fragment_port_and_exit_negative_controls(mutation):
    value = example("documentation.fragment.json")
    if mutation == "port-item":
        value["outputs"]["delivery"]["endpoint"]["item"] = "missing"
    elif mutation == "port-node":
        value["outputs"]["delivery"]["endpoint"]["node"] = "missing"
    else:
        value["exits"]["assessed"] = "missing"
    with pytest.raises(adaptive.DefinitionError):
        adaptive.validate_definition(value)


@pytest.mark.parametrize(
    "capability,definition,field",
    [
        ("acceptance", "outcome-record", "acceptance-source"),
        ("review-control", "evidence-record", "assessment-ordinal-continuity"),
    ],
)
def test_acceptance_and_review_declaration_negative_controls(
    capability, definition, field
):
    declaration = source("goal")["node_definitions"][definition]
    declaration["items"] = [
        item for item in declaration["items"] if item["id"] != field
    ]
    assert (
        adaptive.check_capability(declaration, f"aquarium.goal.{capability}/v1")[
            "status"
        ]
        == "incompatible"
    )
