"""Composition behavior; synthetic digests are not released-native proof."""

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "plugins/aquarium/shared"))

import adaptive_bundles as bundles
import adaptive_composition as composition
import adaptive_preparation as prep
from adaptive_definitions import canonical_json, parse_definition
from test_adaptive_preparation_unit import Oracle, assignment


@pytest.fixture
def repository(tmp_path):
    path = tmp_path / "work 한글"
    path.mkdir()
    subprocess.run(["git", "-C", str(path), "init", "-q"], check=True)
    return path


def reference(repository, name, value, *, native=False):
    path = repository / name
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (
        yaml.safe_dump(value, sort_keys=False).encode()
        if native
        else canonical_json(value)
    )
    path.write_bytes(raw)
    return {"path": name, "sha256": bundles.sha256(raw)}


def node_mapping(native, mapping, ids):
    return {key: copy.deepcopy(mapping["nodes"][key]) for key in ids}


def fragment_plan(repository, *, performance=False, mode="prepare"):
    value = assignment(repository, mode=mode, performance=performance)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    native, mapping = copy.deepcopy(draft["document"]), copy.deepcopy(draft["mapping"])
    ids = set(mapping["nodes"]) - {"outcome", "finish"}
    placements = [
        copy.deepcopy(node) for node in native["graph"]["nodes"] if node["id"] in ids
    ]
    for node in placements:
        if node.get("next") == "outcome":
            node.pop("next")
            node["terminal"] = True
    used = {node["use"] for node in placements}
    fragment = {
        "schema": "aquarium.procedure-fragment/v2",
        "id": "bounded-work",
        "version": "1",
        "purpose": "Deliver and independently assess the actual approved work.",
        "applicability": ["The approved original work and effect scope."],
        "parameters": {
            "target": {
                "type": "text",
                "required": True,
                "description": "Approved original target.",
            }
        },
        "inputs": {},
        "outputs": {
            "assessment": {
                "type": "text",
                "required": True,
                "endpoint": {"node": "assess", "item": "assessment"},
            }
        },
        "entry": native["graph"]["entry"],
        "exits": {"assessed": "assess"},
        "node_definitions": {key: native["node_definitions"][key] for key in used},
        "placements": placements,
        "internal_rework": [],
        "external_rework": {},
        "effects": ["work"],
        "assessors": [
            {
                "node": "assess",
                "covers": ["measure", "deliver", "preserve"]
                if performance
                else ["deliver"],
            }
        ],
        "origins": [],
        "dependencies": [],
    }
    root = copy.deepcopy(native)
    root["node_definitions"] = {
        key: native["node_definitions"][key] for key in ["outcome", "finish"]
    }
    root["graph"] = {
        "entry": "outcome",
        "nodes": [
            copy.deepcopy(node)
            for node in native["graph"]["nodes"]
            if node["id"] not in ids
        ],
    }
    for node in root["graph"]["nodes"]:
        for evidence in node.get("evidence_from", []):
            if evidence["node"] in ids:
                evidence["node"] = "work-" + evidence["node"]
    root["manual_rework"]["allowed_targets"] = ["work-" + native["graph"]["entry"]]
    rootmap = copy.deepcopy(mapping)
    rootmap["nodes"] = node_mapping(native, mapping, {"outcome", "finish"})
    for obligation in rootmap["obligations"].values():
        for endpoint in obligation["producers"] + obligation["evidence"]:
            endpoint["node"] = "work-" + endpoint["node"]
        obligation["assessor"] = "work-assess"
    component = {
        "kind": "fragment",
        "namespace": "work",
        "source": reference(repository, "definitions/work.fragment.json", fragment),
        "mapping": {"nodes": node_mapping(native, mapping, ids), "obligations": {}},
        "parameters": {"target": "Approved documentation or measurement target"},
    }
    draft.update(
        kind="compose",
        document=root,
        mapping=rootmap,
        composition={
            "components": [component],
            "entry": {"component": "work"},
            "control": [
                {
                    "from": {"component": "work", "exit": "assessed"},
                    "to": {"component": "root", "node": "outcome"},
                }
            ],
        },
    )
    return value


def whole_plan(repository, *, mode="prepare"):
    value = assignment(repository, mode=mode)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    native, mapping = copy.deepcopy(draft["document"]), copy.deepcopy(draft["mapping"])
    source = reference(
        repository, "definitions/control.custom.yaml", native, native=True
    )
    binding = {
        **mapping,
        "procedure": {
            "id": native["id"],
            "version": native["version"],
            "digest": bundles.sha256(canonical_json(native)),
            "source_sha256": source["sha256"],
        },
    }
    bound = reference(repository, "definitions/control.binding.json", binding)
    root = {
        **native,
        "node_definitions": {},
        "graph": {"entry": "placeholder", "nodes": []},
    }
    root.pop("manual_rework")
    empty = {
        **mapping,
        "nodes": {},
        "parameters": {},
        "obligations": {},
        "goal_assessments": [],
        "closeout": [],
    }
    draft.update(
        kind="compose",
        document=root,
        mapping=empty,
        composition={
            "components": [
                {
                    "kind": "whole",
                    "namespace": "control",
                    "source": source,
                    "binding": bound,
                }
            ],
            "entry": {"component": "control"},
        },
    )
    for row in draft["coverage"]:
        row["obligation"] = "control-" + row["obligation"]
    return value


def assert_error(code, action):
    with pytest.raises(bundles.BundleError) as caught:
        action()
    assert caught.value.code == code


def test_partial_and_whole_reuse_are_prepared_self_contained(repository):
    for value in [fragment_plan(repository), whole_plan(repository)]:
        result = prep.prepare(repository, value, client=Oracle(repository))
        target = result["assignment"]["target"]["prepared_definition"]
        native = yaml.safe_load(Path(target["source_path"]).read_bytes())
        assert target["kind"] == "compose"
        assert target["adoption"] == "not-performed"
        assert target["assessment"] == "TASK-141-exact-target-suitability-required"
        assert native["graph"]["entry"] in {
            node["id"] for node in native["graph"]["nodes"]
        }
        parse_definition(Path(target["binding_path"]).read_bytes())
        draft = value["target"]["procedure_plan"]["drafts"][0]
        for component in draft["composition"]["components"]:
            (repository / component["source"]["path"]).unlink()
        retained = bundles.verified_bundle(repository, Path(target["path"]))
        assert retained["binding"] == result["binding"]


def test_actual_documentation_and_measurement_compositions_differ(repository):
    results = []
    for performance in [False, True]:
        value = fragment_plan(repository, performance=performance)
        result = prep.prepare(repository, value, client=Oracle(repository))
        target = result["assignment"]["target"]["prepared_definition"]
        results.append(yaml.safe_load(Path(target["source_path"]).read_bytes()))
    documentation, measured = results
    assert "work-measure" not in documentation["node_definitions"]
    assert measured["node_definitions"]["work-measure"]["items"][0]["type"] == "integer"
    assert (
        measured["node_definitions"]["work-classify"]["options"][0]["guards"][0][
            "evidence"
        ]["node"]
        == "work-measure"
    )
    assert len(measured["graph"]["nodes"]) > len(documentation["graph"]["nodes"])


def test_operation_ids_digests_outcomes_and_narrative_are_preserved(repository):
    value = fragment_plan(repository)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    component = draft["composition"]["components"][0]
    path = repository / component["source"]["path"]
    fragment = json.loads(path.read_bytes())
    item = {
        "id": "result",
        "type": "check_result",
        "required": True,
        "prompt": "deliver is text, not a reference",
        "operation_id": "actual-operation",
        "operation_digest": "sha256:" + "1" * 64,
        "accepted_outcomes": ["pass", "fail", "inconclusive"],
    }
    fragment["node_definitions"]["deliver"]["items"].append(item)
    fragment["node_definitions"]["deliver"]["instructions"] = [
        "deliver assess work-result must remain verbatim"
    ]
    component["source"] = reference(repository, component["source"]["path"], fragment)
    component["fields"] = {"deliver": {"result": "typed-result"}}
    component["mapping"]["nodes"]["deliver"]["capabilities"] = [
        {"signature": "example.operation/v1", "fields": {"logical-result": "result"}}
    ]
    result = composition.compose(repository, draft)
    produced = result["document"]["node_definitions"]["work-deliver"]
    assert produced["items"][-1] == {**item, "id": "typed-result"}
    assert (
        produced["instructions"]
        == fragment["node_definitions"]["deliver"]["instructions"]
    )
    assert result["mapping"]["nodes"]["work-deliver"]["capabilities"][0]["fields"] == {
        "logical-result": "typed-result",
        "result": "typed-result",
    }


@pytest.mark.parametrize(
    "mutation,code",
    [
        ("source-drift", "source-drift"),
        ("namespace", "incompatible"),
        ("parent-goal", "incompatible"),
        ("parameter-missing", "not-established"),
        ("parameter-type", "incompatible"),
        ("dependency", "not-established"),
        ("private-rework", "incompatible"),
        ("evidence-unreachable", "incompatible"),
    ],
)
def test_invalid_fragment_compositions_reject(repository, mutation, code):
    value = fragment_plan(repository)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    component = draft["composition"]["components"][0]
    path = repository / component["source"]["path"]
    fragment = json.loads(path.read_bytes())
    if mutation == "source-drift":
        path.write_bytes(path.read_bytes() + b" ")
    elif mutation == "namespace":
        draft["document"]["node_definitions"]["work-deliver"] = copy.deepcopy(
            fragment["node_definitions"]["deliver"]
        )
    elif mutation == "parent-goal":
        fragment["node_definitions"]["assess"]["assessment"] = {
            "target": "session_goal"
        }
    elif mutation == "parameter-missing":
        component["parameters"] = {}
    elif mutation == "parameter-type":
        component["parameters"]["target"] = 5
    elif mutation == "dependency":
        fragment["dependencies"] = [
            {
                "id": "missing",
                "version": "1",
                "sha256": "sha256:" + "0" * 64,
                "source": "missing",
            }
        ]
    elif mutation == "private-rework":
        draft["document"]["node_definitions"]["outcome"]["options"][1]["id"] = "fail"
        outcome = next(
            node
            for node in draft["document"]["graph"]["nodes"]
            if node["id"] == "outcome"
        )
        outcome["routes"]["fail"] = {"to": "work-assess", "effect": "rework"}
    else:
        draft["composition"]["control"] = []
    if mutation not in {"source-drift"}:
        component["source"] = reference(
            repository, component["source"]["path"], fragment
        )
    if mutation == "parent-goal":
        from adaptive_definitions import DefinitionError

        with pytest.raises(DefinitionError):
            composition.compose(repository, draft)
    else:
        assert_error(code, lambda: composition.compose(repository, draft))


def test_plan_only_composition_has_no_files_or_native_effects(repository):
    value = fragment_plan(repository, mode="plan-only")
    before = {
        str(path.relative_to(repository)): (
            path.read_bytes() if path.is_file() else None
        )
        for path in repository.rglob("*")
    }
    result = prep.prepare(repository, value)
    assert result["status"] == "planned"
    assert result["native_checks"] == "not-run"
    assert {
        str(path.relative_to(repository)): (
            path.read_bytes() if path.is_file() else None
        )
        for path in repository.rglob("*")
    } == before


def test_mid_preparation_composition_source_drift_rejects(repository):
    value = fragment_plan(repository)
    client = Oracle(repository)
    identity = client.identity
    component = value["target"]["procedure_plan"]["drafts"][0]["composition"][
        "components"
    ][0]

    def drift(path):
        result = identity(path)
        origin = repository / component["source"]["path"]
        origin.write_bytes(origin.read_bytes() + b" ")
        return result

    client.identity = drift
    assert_error("source-drift", lambda: prep.prepare(repository, value, client=client))
    assert not list((repository / "definitions/.candidates").glob(".prepare-*"))


def evidence_plan(repository):
    value = fragment_plan(repository)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    first = draft["composition"]["components"][0]
    source = json.loads((repository / first["source"]["path"]).read_bytes())
    item = copy.deepcopy(source["node_definitions"]["assess"]["items"][0])
    item["id"] = "incoming"
    record = copy.deepcopy(item)
    record["id"] = "record"
    second = {
        "schema": "aquarium.procedure-fragment/v2",
        "id": "read-assessment",
        "version": "1",
        "purpose": "Read the exact selected upstream assessment.",
        "applicability": ["Selected upstream assessment is required."],
        "parameters": {},
        "inputs": {
            "assessment": {
                "endpoint": {"node": "collect", "item": "incoming"},
                "required": True,
                "type": "text",
            }
        },
        "outputs": {
            "record": {
                "endpoint": {"node": "collect", "item": "record"},
                "required": True,
                "type": "text",
            }
        },
        "entry": "collect",
        "exits": {"read": "collect"},
        "node_definitions": {
            "collect": {
                "type": "action",
                "title": "Read the complete assessment",
                "intent": "Preserve all original rows and gaps.",
                "items": [item, record],
            }
        },
        "placements": [{"id": "collect", "use": "collect", "terminal": True}],
        "effects": [],
        "assessors": [],
        "internal_rework": [],
        "external_rework": {},
        "origins": [],
        "dependencies": [],
    }
    ref = reference(repository, "definitions/read.fragment.json", second)
    draft["composition"]["components"].append(
        {
            "kind": "fragment",
            "namespace": "read",
            "source": ref,
            "mapping": {
                "nodes": {
                    "collect": {
                        "kind": "action",
                        "role": "executor",
                        "effects": [],
                        "capabilities": [],
                    }
                },
                "obligations": {},
            },
        }
    )
    draft["composition"]["control"] = [
        {
            "from": {"component": "work", "exit": "assessed"},
            "to": {"component": "read"},
        },
        {
            "from": {"component": "read", "exit": "read"},
            "to": {"component": "root", "node": "outcome"},
        },
    ]
    draft["composition"]["evidence"] = [
        {
            "from": {"component": "work", "port": "assessment"},
            "to": {"component": "read", "port": "assessment"},
        }
    ]
    return value


def test_typed_evidence_ports_select_exact_aliases_and_producers(repository):
    value = evidence_plan(repository)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    draft["composition"]["components"][0]["fields"] = {
        "assess": {"assessment": "original-assessment"}
    }
    result = prep.prepare(repository, value, client=Oracle(repository))
    native = yaml.safe_load(
        Path(
            result["assignment"]["target"]["prepared_definition"]["source_path"]
        ).read_bytes()
    )
    consumer = next(
        node for node in native["graph"]["nodes"] if node["id"] == "read-collect"
    )
    assert consumer["evidence_from"] == [
        {"node": "work-assess", "required": True, "items": ["original-assessment"]}
    ]


@pytest.mark.parametrize(
    "mutation,code",
    [
        ("missing", "not-established"),
        ("ambiguous", "incompatible"),
        ("wrong-port", "incompatible"),
        ("wrong-type", "incompatible"),
        ("contract", "incompatible"),
        ("conditional", "not-established"),
        ("dominance", "incompatible"),
        ("bad-alias", "incompatible"),
    ],
)
def test_evidence_port_failures_are_independent_of_control_edges(
    repository, mutation, code
):
    value = evidence_plan(repository)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    spec = draft["composition"]
    if mutation == "missing":
        spec["evidence"] = []
    elif mutation == "ambiguous":
        spec["evidence"] *= 2
    elif mutation == "wrong-port":
        spec["evidence"][0]["from"]["port"] = "unknown"
    elif mutation == "dominance":
        spec["entry"] = {"component": "read"}
    elif mutation == "bad-alias":
        spec["components"][0]["fields"] = {
            "assess": {"assessment": "missing"},
            "unknown": {},
        }
    else:
        component = spec["components"][
            1 if mutation in {"wrong-type", "contract"} else 0
        ]
        fragment = json.loads((repository / component["source"]["path"]).read_bytes())
        if mutation == "wrong-type":
            fragment["inputs"]["assessment"]["type"] = "integer"
            fragment["node_definitions"]["collect"]["items"][0] = {
                "id": "incoming",
                "type": "integer",
                "required": True,
                "prompt": "Input count",
                "minimum": 0,
            }
        elif mutation == "contract":
            fragment["node_definitions"]["collect"]["items"][0]["max_length"] -= 1
        else:
            fragment["node_definitions"]["assess"]["items"][0]["required"] = False
        component["source"] = reference(
            repository, component["source"]["path"], fragment
        )
    assert_error(code, lambda: composition.compose(repository, draft))


def rework_plan(repository):
    value = fragment_plan(repository)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    part = draft["composition"]["components"][0]
    fragment = json.loads((repository / part["source"]["path"]).read_bytes())
    fragment["node_definitions"]["route"] = {
        "type": "decision",
        "title": "Route phase assessment",
        "objective": "Use the complete current independent assessment.",
        "prompt": "Does this phase need owned correction?",
        "options": [
            {
                "id": "pass",
                "label": "Pass",
                "criteria": "The current phase obligations are established.",
            },
            {
                "id": "rework",
                "label": "Rework",
                "criteria": "An authorized owned correction is due.",
            },
        ],
        "reason": {
            "required": True,
            "prompt": "Cite the exact assessment and correction authority.",
        },
    }
    assess = next(node for node in fragment["placements"] if node["id"] == "assess")
    assess.pop("terminal")
    assess["next"] = "route"
    fragment["placements"].append(
        {
            "id": "route",
            "use": "route",
            "evidence_from": [
                {"node": "assess", "required": True, "items": ["assessment"]}
            ],
            "routes": {
                "pass": {"to": "assess", "effect": "advance"},
                "rework": {"to": "correction-owner", "effect": "rework"},
            },
        }
    )
    fragment["exits"] = {"assessed": "route"}
    fragment["external_rework"] = {
        "correct": {"from": "route", "port": "correction-owner"}
    }
    part["mapping"]["nodes"]["route"] = {
        "kind": "decision",
        "role": "coordinator",
        "effects": [],
        "capabilities": [],
    }
    part["rework"] = {"correction-owner": {"component": "work", "target": "entry"}}
    part["source"] = reference(repository, part["source"]["path"], fragment)
    draft["composition"]["control"][0]["from"]["option"] = "pass"
    return value


def test_declared_external_rework_uses_supported_native_route_semantics(repository):
    value = rework_plan(repository)
    result = prep.prepare(repository, value, client=Oracle(repository))
    native = yaml.safe_load(
        Path(
            result["assignment"]["target"]["prepared_definition"]["source_path"]
        ).read_bytes()
    )
    route = next(
        node for node in native["graph"]["nodes"] if node["id"] == "work-route"
    )
    assert route["routes"]["rework"] == {"to": "work-deliver", "effect": "rework"}
    assert route["routes"]["pass"] == {"to": "outcome", "effect": "advance"}


@pytest.mark.parametrize(
    "mutation", ["missing", "undeclared", "private", "wrong-from", "manual-private"]
)
def test_external_rework_requires_declared_public_target(repository, mutation):
    value = rework_plan(repository)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    part = draft["composition"]["components"][0]
    if mutation == "missing":
        part["rework"] = {}
    elif mutation == "undeclared":
        part["rework"]["extra"] = {"component": "work", "target": "entry"}
    elif mutation == "private":
        part["rework"]["correction-owner"]["target"] = "assess"
    elif mutation == "manual-private":
        draft["document"]["manual_rework"]["allowed_targets"] = ["work-assess"]
    else:
        fragment = json.loads((repository / part["source"]["path"]).read_bytes())
        fragment["external_rework"]["correct"]["from"] = "assess"
        part["source"] = reference(repository, part["source"]["path"], fragment)
    assert_error("incompatible", lambda: composition.compose(repository, draft))


def test_conflicting_definition_identity_and_exact_dependencies(repository):
    value = evidence_plan(repository)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    first, second = draft["composition"]["components"]
    fragment = json.loads((repository / second["source"]["path"]).read_bytes())
    fragment["dependencies"] = [
        {
            "id": "bounded-work",
            "version": "1",
            "sha256": first["source"]["sha256"],
            "source": first["source"]["path"],
        }
    ]
    second["source"] = reference(repository, second["source"]["path"], fragment)
    assert composition.compose(repository, draft)["origins"]
    fragment["id"] = "bounded-work"
    second["source"] = reference(repository, second["source"]["path"], fragment)
    assert_error("incompatible", lambda: composition.compose(repository, draft))


def test_native_optional_guard_item_is_preserved_without_port_presence_claim(
    repository,
):
    value = fragment_plan(repository, performance=True)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    part = draft["composition"]["components"][0]
    fragment = json.loads((repository / part["source"]["path"]).read_bytes())
    fragment["node_definitions"]["measure"]["items"][0]["required"] = False
    part["source"] = reference(repository, part["source"]["path"], fragment)
    result = composition.compose(repository, draft)
    assert (
        result["document"]["node_definitions"]["work-measure"]["items"][0]["required"]
        is False
    )
    assert result["qualification"] == "TASK-141-exact-target-suitability-required"


def test_narrower_producer_bounds_are_assignable(repository):
    value = evidence_plan(repository)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    part = draft["composition"]["components"][0]
    fragment = json.loads((repository / part["source"]["path"]).read_bytes())
    fragment["node_definitions"]["assess"]["items"][0]["max_length"] = 100
    part["source"] = reference(repository, part["source"]["path"], fragment)
    assert composition.compose(repository, draft)["document"]


def test_unproven_item_constraint_is_not_established():
    assert_error(
        "not-established",
        lambda: composition.assignable(
            {"type": "text", "min_length": 1},
            {"type": "text", "min_length": 1, "max_length": 2000},
        ),
    )
    assert_error(
        "incompatible",
        lambda: composition.assignable(
            {
                "type": "check_result",
                "operation_id": "a",
                "operation_digest": "sha256:" + "1" * 64,
                "accepted_outcomes": ["pass", "fail"],
            },
            {
                "type": "check_result",
                "operation_id": "b",
                "operation_digest": "sha256:" + "1" * 64,
                "accepted_outcomes": ["pass", "fail", "inconclusive"],
            },
        ),
    )


def product_plan(repository):
    value = assignment(repository, mode="prepare")
    draft = value["target"]["procedure_plan"]["drafts"][0]
    value["target"]["procedure_plan"]["review"] = {
        "route": "herdr",
        "team": ["Claude"],
        "transmission": ["Approved exact source target"],
    }
    value["authority"]["review"] = copy.deepcopy(
        value["target"]["procedure_plan"]["review"]
    )
    native = {
        "schema": "podway.procedure/v2",
        "id": "composed-draft",
        "version": "1",
        "name": "Selected review and whole goal control",
        "purpose": "Preserve the selected technical review and original goal assessment.",
        "node_definitions": {},
        "graph": {"entry": "placeholder", "nodes": []},
    }
    mapping = {
        **draft["mapping"],
        "nodes": {},
        "obligations": {},
        "goal_assessments": [],
        "closeout": [],
    }
    assets = prep.ASSETS / "adaptive/reusable"
    refs = lambda name: {
        "asset": "adaptive/reusable/" + name,
        "sha256": bundles.sha256((assets / name).read_bytes()),
    }
    fragment = json.loads((assets / "technical-review.fragment.json").read_bytes())
    review_map = {
        "nodes": {
            "record": {
                "kind": "action",
                "role": "executor",
                "effects": [],
                "capabilities": [
                    {"signature": "aquarium.task.review-control/v2", "fields": {}}
                ],
            },
            "route": {
                "kind": "decision",
                "role": "coordinator",
                "effects": [],
                "capabilities": [],
            },
        },
        "obligations": {},
    }
    draft.update(
        kind="compose",
        document=native,
        mapping=mapping,
        composition={
            "components": [
                {
                    "kind": "fragment",
                    "namespace": "review",
                    "source": refs("technical-review.fragment.json"),
                    "mapping": review_map,
                    "rework": {
                        "correction-owner": {"component": "review", "target": "entry"}
                    },
                },
                {
                    "kind": "whole",
                    "namespace": "goal",
                    "source": refs("task-goal-control.yaml"),
                    "binding": refs("task-goal-control.binding.json"),
                },
            ],
            "entry": {"component": "review"},
            "control": [
                {
                    "from": {
                        "component": "review",
                        "exit": "reviewed",
                        "option": "complete",
                    },
                    "to": {"component": "goal"},
                }
            ],
        },
    )
    for row in draft["coverage"]:
        row["obligation"] = "goal-original-goal"
    return value, fragment


def test_product_review_fragment_and_whole_control_flatten(repository):
    value, fragment = product_plan(repository)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    result = composition.compose(repository, draft)
    assert result["document"]["goal_tracking"] is True
    assert result["mapping"]["goal_assessments"][0]["node"] == "goal-outcome"
    assert (
        result["document"]["node_definitions"]["review-record"]["items"]
        == fragment["node_definitions"]["record"]["items"]
    )
    assert "procedure" not in result["mapping"]


@pytest.mark.parametrize(
    "case",
    [
        "components",
        "native-definition",
        "native-options",
        "native-evidence",
        "mapping-node",
        "binding-reference",
        "whole-ports",
        "fields",
    ],
)
def test_public_cli_malformed_composition_containers_are_structured(repository, case):
    from test_adaptive_preparation_unit import run_preparation_cli

    value = whole_plan(repository, mode="plan-only")
    draft = value["target"]["procedure_plan"]["drafts"][0]
    component = draft["composition"]["components"][0]
    if case == "components":
        draft["composition"]["components"] = [5]
    elif case == "binding-reference":
        component["binding"] = []
    elif case == "whole-ports":
        component["inputs"] = []
    elif case == "fields":
        component["fields"] = []
    elif case == "mapping-node":
        draft["mapping"]["nodes"]["bad"] = 5
    else:
        source_path = repository / component["source"]["path"]
        native = yaml.safe_load(source_path.read_bytes())
        if case == "native-definition":
            native["node_definitions"]["deliver"] = 5
        elif case == "native-options":
            native["node_definitions"]["outcome"]["options"] = [5]
        else:
            native["graph"]["nodes"][1]["evidence_from"] = [5]
        component["source"] = reference(
            repository, component["source"]["path"], native, native=True
        )
        binding_path = repository / component["binding"]["path"]
        binding = json.loads(binding_path.read_bytes())
        binding["procedure"]["source_sha256"] = component["source"]["sha256"]
        component["binding"] = reference(
            repository, component["binding"]["path"], binding
        )
    before = {str(path.relative_to(repository)) for path in repository.rglob("*")}
    result = run_preparation_cli(repository, json.dumps(value))
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "invalid-input"
    assert result.stderr == ""
    assert {
        str(path.relative_to(repository)) for path in repository.rglob("*")
    } == before


def test_ambiguous_control_port_rejects(repository):
    value = fragment_plan(repository)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    draft["composition"]["control"] *= 2
    assert_error("incompatible", lambda: composition.compose(repository, draft))


def test_grouped_conditional_assessment_preserves_optional_branch_selectors(repository):
    value = fragment_plan(repository, performance=True)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    result = composition.compose(repository, draft)
    assessor = next(
        node
        for node in result["document"]["graph"]["nodes"]
        if node["id"] == "work-assess"
    )
    assert {
        row["node"]
        for row in assessor["evidence_from"]
        if not row.get("required", True)
    } == {"work-deliver", "work-preserve"}
    assert result["qualification"] == "TASK-141-exact-target-suitability-required"
    part = draft["composition"]["components"][0]
    fragment = json.loads((repository / part["source"]["path"]).read_bytes())
    assessor = next(node for node in fragment["placements"] if node["id"] == "assess")
    assessor["evidence_from"] = [
        row for row in assessor["evidence_from"] if row["node"] != "preserve"
    ]
    part["source"] = reference(repository, part["source"]["path"], fragment)
    assert_error("incompatible", lambda: composition.compose(repository, draft))


def test_generated_source_preserves_long_and_multiline_native_values(repository):
    value = fragment_plan(repository)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    part = draft["composition"]["components"][0]
    fragment = json.loads((repository / part["source"]["path"]).read_bytes())
    value_with_lines = "First exact original line.\nSecond exact original line.\n"
    fragment["node_definitions"]["deliver"]["instructions"] = [value_with_lines]
    long_help = "Preserve the original operation: " + "exact criterion coverage; " * 20
    fragment["node_definitions"]["deliver"]["items"][0]["help"] = long_help
    part["source"] = reference(repository, part["source"]["path"], fragment)
    result = prep.prepare(repository, value, client=Oracle(repository))
    native = yaml.safe_load(
        Path(
            result["assignment"]["target"]["prepared_definition"]["source_path"]
        ).read_bytes()
    )
    assert native["node_definitions"]["work-deliver"]["instructions"] == [
        value_with_lines
    ]
    assert native["node_definitions"]["work-deliver"]["items"][0]["help"] == long_help


@pytest.mark.parametrize(
    "selector",
    [None, ["additional-evidence"], ["documentation", "additional-evidence"]],
)
def test_evidence_wiring_preserves_and_augments_existing_selection(
    repository, selector
):
    value = fragment_plan(repository)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    part = draft["composition"]["components"][0]
    fragment = json.loads((repository / part["source"]["path"]).read_bytes())
    extra = copy.deepcopy(fragment["node_definitions"]["deliver"]["items"][0])
    extra["id"] = "additional-evidence"
    fragment["node_definitions"]["deliver"]["items"].append(extra)
    assessment = next(node for node in fragment["placements"] if node["id"] == "assess")
    if selector is None:
        assessment["evidence_from"][0].pop("items")
    else:
        assessment["evidence_from"][0]["items"] = selector
    fragment["outputs"]["documentation"] = {
        "endpoint": {"node": "deliver", "item": "documentation"},
        "required": True,
        "type": "text",
    }
    fragment["inputs"]["documentation"] = {
        "endpoint": {"node": "assess", "item": "assessment"},
        "required": True,
        "type": "text",
    }
    part["source"] = reference(repository, part["source"]["path"], fragment)
    draft["composition"]["evidence"] = [
        {
            "from": {"component": "work", "port": "documentation"},
            "to": {"component": "work", "port": "documentation"},
        }
    ]
    result = composition.compose(repository, draft)
    assessment = next(
        node
        for node in result["document"]["graph"]["nodes"]
        if node["id"] == "work-assess"
    )
    expected = {"node": "work-deliver", "required": True}
    if selector is not None:
        expected["items"] = (
            selector if "documentation" in selector else selector + ["documentation"]
        )
    assert assessment["evidence_from"] == [expected]


def test_logical_obligation_namespace_preserves_supported_unicode_and_spaces(
    repository,
):
    value = whole_plan(repository)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    part = draft["composition"]["components"][0]
    binding = json.loads((repository / part["binding"]["path"]).read_bytes())
    logical_key = "original work 문서"
    binding["obligations"][logical_key] = binding["obligations"].pop("original-work")
    part["binding"] = reference(repository, part["binding"]["path"], binding)
    for row in draft["coverage"]:
        row["obligation"] = "control-" + logical_key
    result = prep.prepare(repository, value, client=Oracle(repository))
    assert set(result["binding"]["obligations"]) == {"control-" + logical_key}
    obligation = result["binding"]["obligations"]["control-" + logical_key]
    assert obligation["decision"] == "control-outcome"
    assert {endpoint["node"] for endpoint in obligation["producers"]} == {
        "control-deliver"
    }


@pytest.mark.parametrize("namespace", ["bad namespace", "한글", "x" * 64])
def test_native_placement_and_definition_namespace_limits_remain(repository, namespace):
    value = fragment_plan(repository)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    draft["composition"]["components"][0]["namespace"] = namespace
    assert_error("incompatible", lambda: composition.compose(repository, draft))


def single_action_control_plan(repository):
    value = fragment_plan(repository)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    part = draft["composition"]["components"][0]
    fragment = json.loads((repository / part["source"]["path"]).read_bytes())
    assessment = fragment["node_definitions"].pop("assess")
    fragment["placements"] = [{"id": "deliver", "use": "deliver", "terminal": True}]
    fragment["exits"] = {"delivered": "deliver"}
    fragment["assessors"] = []
    fragment["outputs"] = {}
    draft["document"]["node_definitions"]["assess"] = assessment
    draft["document"]["graph"]["nodes"].insert(
        0,
        {
            "id": "assess",
            "use": "assess",
            "next": "outcome",
            "evidence_from": [
                {"node": "work-deliver", "required": True, "items": ["documentation"]}
            ],
        },
    )
    for node in draft["document"]["graph"]["nodes"]:
        for evidence in node.get("evidence_from", []):
            if evidence["node"] == "work-assess":
                evidence["node"] = "assess"
    draft["mapping"]["nodes"]["assess"] = part["mapping"]["nodes"].pop("assess")
    obligation = draft["mapping"]["obligations"]["original-work"]
    obligation["evidence"][0]["node"] = "assess"
    obligation["assessor"] = "assess"
    part["source"] = reference(repository, part["source"]["path"], fragment)
    draft["composition"]["control"] = [
        {
            "from": {"component": "work", "exit": "delivered"},
            "to": {"component": "root", "node": "assess"},
        }
    ]
    return value


def distinct_decision_control_plan(repository):
    value = fragment_plan(repository)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    part = draft["composition"]["components"][0]
    fragment = json.loads((repository / part["source"]["path"]).read_bytes())
    fragment["node_definitions"]["split"] = {
        "type": "decision",
        "title": "Choose assessment delivery",
        "objective": "Use the actual assessment and original delivery needs.",
        "prompt": "Does the result require an additional explanatory note?",
        "options": [
            {
                "id": "direct",
                "label": "Direct",
                "criteria": "The assessment needs no additional explanation.",
            },
            {
                "id": "explain",
                "label": "Explain",
                "criteria": "The assessment needs a bounded explanatory note.",
            },
        ],
        "reason": {
            "required": True,
            "prompt": "Cite the current assessment and delivery requirements.",
        },
    }
    assessment = next(node for node in fragment["placements"] if node["id"] == "assess")
    assessment.pop("terminal")
    assessment["next"] = "split"
    fragment["placements"].append(
        {
            "id": "split",
            "use": "split",
            "evidence_from": [
                {"node": "assess", "required": True, "items": ["assessment"]}
            ],
            "routes": {
                key: {"to": "assess", "effect": "advance"}
                for key in ["direct", "explain"]
            },
        }
    )
    fragment["exits"] = {"selected": "split"}
    part["mapping"]["nodes"]["split"] = {
        "kind": "decision",
        "role": "coordinator",
        "effects": [],
        "capabilities": [],
    }
    part["source"] = reference(repository, part["source"]["path"], fragment)
    draft["document"]["node_definitions"]["note"] = {
        "type": "action",
        "title": "Explain the independent assessment",
        "intent": "Deliver the requested bounded explanation without changing the assessment.",
        "items": [
            {
                "id": "explanation",
                "type": "text",
                "prompt": "Record the assessment explanation and original gaps.",
                "required": True,
                "min_length": 1,
                "max_length": 2000,
            }
        ],
    }
    draft["document"]["graph"]["nodes"].append(
        {
            "id": "note",
            "use": "note",
            "next": "outcome",
            "evidence_from": [
                {"node": "work-assess", "required": True, "items": ["assessment"]}
            ],
        }
    )
    draft["mapping"]["nodes"]["note"] = {
        "kind": "action",
        "role": "coordinator",
        "effects": [],
        "capabilities": [],
    }
    draft["composition"]["control"] = [
        {
            "from": {"component": "work", "exit": "selected", "option": "direct"},
            "to": {"component": "root", "node": "outcome"},
        },
        {
            "from": {"component": "work", "exit": "selected", "option": "explain"},
            "to": {"component": "root", "node": "note"},
        },
        {
            "from": {"component": "root", "node": "note"},
            "to": {"component": "root", "node": "outcome"},
        },
    ]
    return value


def test_valid_action_and_distinct_decision_control_sources_preserve_destinations(
    repository,
):
    action = single_action_control_plan(repository)
    result = prep.prepare(repository, action, client=Oracle(repository))
    native = yaml.safe_load(
        Path(
            result["assignment"]["target"]["prepared_definition"]["source_path"]
        ).read_bytes()
    )
    assert (
        next(node for node in native["graph"]["nodes"] if node["id"] == "work-deliver")[
            "next"
        ]
        == "assess"
    )
    value = distinct_decision_control_plan(repository)
    result = prep.prepare(repository, value, client=Oracle(repository))
    native = yaml.safe_load(
        Path(
            result["assignment"]["target"]["prepared_definition"]["source_path"]
        ).read_bytes()
    )
    split = next(
        node for node in native["graph"]["nodes"] if node["id"] == "work-split"
    )
    assert split["routes"] == {
        "direct": {"to": "outcome", "effect": "advance"},
        "explain": {"to": "note", "effect": "advance"},
    }
    assert (
        next(node for node in native["graph"]["nodes"] if node["id"] == "note")["next"]
        == "outcome"
    )


@pytest.mark.parametrize(
    "case",
    [
        "source-exit-missing",
        "source-exit-unknown",
        "destination-exit",
        "destination-option",
        "entry-exit",
        "entry-option",
        "root-source-private",
        "root-destination-private",
        "root-entry-private",
        "action-option",
        "action-option-null",
        "action-two-destinations",
        "action-option-smuggling",
    ],
)
def test_control_endpoint_ownership_and_action_uniqueness_reject(repository, case):
    value = single_action_control_plan(repository)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    spec = draft["composition"]
    edge = spec["control"][0]
    if case == "source-exit-missing":
        edge["from"].pop("exit")
    elif case == "source-exit-unknown":
        edge["from"]["exit"] = "unknown"
    elif case.startswith("destination-"):
        edge["to"] = {
            "component": "work",
            case.removeprefix("destination-"): "delivered",
        }
    elif case.startswith("entry-"):
        spec["entry"][case.removeprefix("entry-")] = "delivered"
    elif case == "root-source-private":
        edge["from"] = {"component": "root", "node": "work-deliver"}
    elif case == "root-destination-private":
        edge["to"] = {"component": "root", "node": "work-deliver"}
    elif case == "root-entry-private":
        spec["entry"] = {"component": "root", "node": "work-deliver"}
    elif case in {"action-option", "action-option-null"}:
        edge["from"]["option"] = "ignored" if case == "action-option" else None
    else:
        second = copy.deepcopy(edge)
        second["to"] = {"component": "root", "node": "outcome"}
        if case == "action-option-smuggling":
            edge["from"]["option"] = "first"
            second["from"]["option"] = "second"
        spec["control"].append(second)
    assert_error("incompatible", lambda: composition.compose(repository, draft))


@pytest.mark.parametrize(
    "case",
    [
        "missing-option",
        "unknown-option",
        "duplicate-option",
        "root-public-private-alias",
    ],
)
def test_decision_control_and_public_root_targets_preserve_owner_contract(
    repository, case
):
    value = (
        distinct_decision_control_plan(repository)
        if case != "root-public-private-alias"
        else rework_plan(repository)
    )
    draft = value["target"]["procedure_plan"]["drafts"][0]
    spec = draft["composition"]
    if case == "missing-option":
        spec["control"][0]["from"].pop("option")
    elif case == "unknown-option":
        spec["control"][0]["from"]["option"] = "unknown"
    elif case == "duplicate-option":
        spec["control"][1]["from"]["option"] = "direct"
    else:
        spec["public_targets"] = {"aliased": "work-deliver"}
        spec["components"][0]["rework"]["correction-owner"] = {
            "component": "root",
            "target": "aliased",
        }
    assert_error("incompatible", lambda: composition.compose(repository, draft))


def test_real_root_entry_and_public_rework_target_remain_supported(repository):
    value = rework_plan(repository)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    draft["document"]["node_definitions"]["basis"] = {
        "type": "action",
        "title": "Read original requirement basis",
        "intent": "Retain the original work basis before the selected work fragment.",
        "items": [
            {
                "id": "original-basis",
                "type": "text",
                "prompt": "Record original requirements and approved scope.",
                "required": True,
                "min_length": 1,
                "max_length": 2000,
            }
        ],
    }
    draft["document"]["graph"]["nodes"].insert(
        0, {"id": "basis", "use": "basis", "next": "work-deliver"}
    )
    draft["mapping"]["nodes"]["basis"] = {
        "kind": "action",
        "role": "executor",
        "effects": [],
        "capabilities": [],
    }
    spec = draft["composition"]
    spec["entry"] = {"component": "root", "node": "basis"}
    spec["public_targets"] = {"original-basis": "basis"}
    spec["components"][0]["rework"]["correction-owner"] = {
        "component": "root",
        "target": "original-basis",
    }
    spec["control"].append(
        {"from": {"component": "root", "node": "basis"}, "to": {"component": "work"}}
    )
    result = composition.compose(repository, draft)
    assert result["document"]["graph"]["entry"] == "basis"
    route = next(
        node
        for node in result["document"]["graph"]["nodes"]
        if node["id"] == "work-route"
    )
    assert route["routes"]["rework"] == {"to": "basis", "effect": "rework"}
    assert (
        next(
            node
            for node in result["document"]["graph"]["nodes"]
            if node["id"] == "basis"
        )["next"]
        == "work-deliver"
    )


@pytest.mark.parametrize(
    "case", ["component-list", "exit-list", "option-list", "root-node-list"]
)
def test_malformed_control_selector_shapes_return_structured_cli_errors(
    repository, case
):
    from test_adaptive_preparation_unit import run_preparation_cli

    value = distinct_decision_control_plan(repository)
    value["target"]["procedure_plan"]["mode"] = "plan-only"
    source = value["target"]["procedure_plan"]["drafts"][0]["composition"]["control"][
        0
    ]["from"]
    if case == "component-list":
        source["component"] = []
    elif case == "exit-list":
        source["exit"] = []
    elif case == "option-list":
        source["option"] = []
    else:
        source.clear()
        source.update(component="root", node=[])
    result = run_preparation_cli(repository, json.dumps(value))
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "invalid-input"
    assert result.stderr == ""


def amend_fragment(repository, draft, change):
    component = draft["composition"]["components"][0]
    fragment = json.loads((repository / component["source"]["path"]).read_bytes())
    change(fragment)
    component["source"] = reference(repository, component["source"]["path"], fragment)
    return fragment


@pytest.mark.parametrize(
    "family", ["task", "goal", "validation", "design", "diagnosis"]
)
def test_released_whole_import_preserves_repeated_selector_rows(repository, family):
    from adaptive_admission import reference_mapping

    raw = (
        prep.ASSETS
        / "podway/procedures"
        / ("aquarium-" + ("war-room" if family == "diagnosis" else family) + "-v2.yaml")
    ).read_bytes()
    native = yaml.safe_load(raw)
    mapping = reference_mapping(raw)
    # This direct source-composition control deliberately does not claim native proof.
    mapping["procedure"] = {
        "id": native["id"],
        "version": native["version"],
        "digest": bundles.sha256(b"unit-native-placeholder"),
        "source_sha256": bundles.sha256(raw),
    }
    value = whole_plan(repository, mode="plan-only")
    draft = value["target"]["procedure_plan"]["drafts"][0]
    draft["mapping"]["family"] = family
    component = draft["composition"]["components"][0]
    source = repository / component["source"]["path"]
    source.write_bytes(raw)
    component["source"]["sha256"] = bundles.sha256(raw)
    component["binding"] = reference(repository, component["binding"]["path"], mapping)
    result = composition.compose(repository, draft)
    imported = result["document"]["graph"]["nodes"]
    for original in native["graph"]["nodes"]:
        node = next(row for row in imported if row["id"] == "control-" + original["id"])
        assert node.get("evidence_from", []) == [
            {**row, "node": "control-" + row["node"]}
            for row in original.get("evidence_from", [])
        ]


@pytest.mark.parametrize("optional_first", [False, True])
def test_wiring_preserves_mixed_selector_applicability(repository, optional_first):
    value = fragment_plan(repository)
    draft = value["target"]["procedure_plan"]["drafts"][0]

    def change(fragment):
        items = fragment["node_definitions"]["deliver"]["items"]
        extra = {**items[0], "id": "observation", "required": False}
        items.append(extra)
        selectors = [
            {"node": "deliver", "required": True, "items": ["documentation"]},
            {"node": "deliver", "required": False, "items": ["observation"]},
        ]
        if optional_first:
            selectors.reverse()
        fragment["placements"][-1]["evidence_from"] = selectors
        for key, required in [("documentation", True), ("observation", False)]:
            fragment["outputs"][key] = {
                "type": "text",
                "required": required,
                "endpoint": {"node": "deliver", "item": key},
            }
            fragment["inputs"][key] = {
                "type": "text",
                "required": required,
                "endpoint": {"node": "assess", "item": "assessment"},
            }

    fragment = amend_fragment(repository, draft, change)
    draft["composition"]["evidence"] = [
        {
            "from": {"component": "work", "port": key},
            "to": {"component": "work", "port": key},
        }
        for key in ["documentation", "observation"]
    ]
    result = composition.compose(repository, draft)
    assessed = next(
        row
        for row in result["document"]["graph"]["nodes"]
        if row["id"] == "work-assess"
    )
    assert assessed["evidence_from"] == [
        {**row, "node": "work-deliver"}
        for row in fragment["placements"][-1]["evidence_from"]
    ]


@pytest.mark.parametrize("existing_rows,expected", [(1, 2), (7, 8), (8, None)])
def test_wiring_respects_native_selector_and_item_bounds(
    repository, existing_rows, expected
):
    value = fragment_plan(repository)
    draft = value["target"]["procedure_plan"]["drafts"][0]

    def change(fragment):
        original = fragment["node_definitions"]["deliver"]["items"][0]
        fragment["node_definitions"]["deliver"]["items"] += [
            {**original, "id": "extra-" + str(index)} for index in range(16)
        ]
        fragment["placements"][-1]["evidence_from"] = [
            {
                "node": "deliver",
                "required": True,
                "items": ["extra-" + str(index) for index in range(16)],
            }
            for _ in range(existing_rows)
        ]
        fragment["outputs"]["documentation"] = {
            "type": "text",
            "required": True,
            "endpoint": {"node": "deliver", "item": "documentation"},
        }
        fragment["inputs"]["documentation"] = {
            "type": "text",
            "required": True,
            "endpoint": {"node": "assess", "item": "assessment"},
        }

    amend_fragment(repository, draft, change)
    draft["composition"]["evidence"] = [
        {
            "from": {"component": "work", "port": "documentation"},
            "to": {"component": "work", "port": "documentation"},
        }
    ]
    if expected is None:
        assert_error("incompatible", lambda: composition.compose(repository, draft))
    else:
        result = composition.compose(repository, draft)
        selectors = next(
            row
            for row in result["document"]["graph"]["nodes"]
            if row["id"] == "work-assess"
        )["evidence_from"]
        assert len(selectors) == expected
        assert selectors[-1]["items"] == ["documentation"]
        assert all(len(row["items"]) <= 16 for row in selectors)


@pytest.mark.parametrize(
    "case",
    [
        "dominance",
        "guard-optional-row",
        "guard-all-items",
        "dangling-producer",
        "dangling-item",
    ],
)
def test_reachable_graph_rejects_actual_evidence_violations(repository, case):
    value = fragment_plan(repository, performance=True)
    draft = value["target"]["procedure_plan"]["drafts"][0]

    def change(fragment):
        nodes = {row["id"]: row for row in fragment["placements"]}
        if case == "dominance":
            next(
                row
                for row in nodes["assess"]["evidence_from"]
                if row["node"] == "deliver"
            )["required"] = True
        elif case.startswith("guard-"):
            original = fragment["node_definitions"]["measure"]["items"][0]
            fragment["node_definitions"]["measure"]["items"].append(
                {**original, "id": "context"}
            )
            nodes["classify"]["evidence_from"] = [
                {"node": "measure", "required": True, "items": ["context"]},
                {"node": "measure", "required": False, "items": ["latency"]},
            ]
            if case == "guard-all-items":
                nodes["classify"]["evidence_from"][0].pop("items")
        elif case == "dangling-producer":
            nodes["classify"]["evidence_from"][0]["node"] = "absent"
        else:
            nodes["classify"]["evidence_from"][0]["items"] = ["absent"]

    amend_fragment(repository, draft, change)
    assert_error("incompatible", lambda: composition.compose(repository, draft))


@pytest.mark.parametrize(
    "fields",
    [{}, {"evaluator-verdict": "evaluator-verdict"}, {"logical": "evaluator-verdict"}],
)
def test_alias_expansion_preserves_implicit_and_explicit_logical_fields(
    repository, fields
):
    value = fragment_plan(repository)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    component = draft["composition"]["components"][0]

    def change(fragment):
        fragment["node_definitions"]["assess"]["items"].append(
            {
                "id": "evaluator-verdict",
                "type": "choice",
                "required": True,
                "prompt": "Record current verdict",
                "choices": ["pass", "rework", "evidence-needed"],
            }
        )

    amend_fragment(repository, draft, change)
    component["fields"] = {"assess": {"evaluator-verdict": "current-verdict"}}
    component["mapping"]["nodes"]["assess"]["capabilities"] = [
        {"signature": "example.explicit-operation/v1", "fields": fields}
    ]
    result = composition.compose(repository, draft)
    aliases = result["mapping"]["nodes"]["work-assess"]["capabilities"][0]["fields"]
    assert (
        aliases.get("logical" if "logical" in fields else "evaluator-verdict")
        == "current-verdict"
    )
    assert aliases.get("evaluator-verdict", "evaluator-verdict") == "current-verdict"


@pytest.mark.parametrize("aliased", [False, True])
def test_mapped_route_contradiction_survives_aliasing(repository, aliased):
    value = fragment_plan(repository)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    component = draft["composition"]["components"][0]

    def change(fragment):
        fragment["node_definitions"]["assess"]["items"].append(
            {
                "id": "effective-review-route",
                "type": "choice",
                "required": True,
                "prompt": "Record selected provider",
                "choices": ["mulgae"],
            }
        )

    amend_fragment(repository, draft, change)
    component["mapping"]["nodes"]["assess"]["capabilities"] = [
        {"signature": "aquarium.task.review-routing/v2", "fields": {}}
    ]
    if aliased:
        component["fields"] = {
            "assess": {"effective-review-route": "selected-provider"}
        }
    result = composition.compose(repository, draft)
    assert_error(
        "incompatible",
        lambda: prep.review_fit(
            result["document"], result["mapping"], {"route": "herdr"}
        ),
    )


@pytest.mark.parametrize(
    "case",
    [
        "manual-list",
        "manual-null",
        "manual-scalar",
        "parameters",
        "origins",
        "public-targets",
    ],
)
def test_consumed_composition_containers_return_json_without_effects(repository, case):
    from test_adaptive_preparation_unit import run_preparation_cli

    value = fragment_plan(repository, mode="plan-only")
    draft = value["target"]["procedure_plan"]["drafts"][0]
    if case.startswith("manual-"):
        draft["document"]["manual_rework"] = {
            "manual-list": [],
            "manual-null": None,
            "manual-scalar": 5,
        }[case]
    elif case == "public-targets":
        draft["composition"]["components"][0]["public_targets"] = []
    else:
        draft["mapping"][case] = [] if case == "parameters" else {}
    before = {str(path.relative_to(repository)) for path in repository.rglob("*")}
    process = run_preparation_cli(repository, json.dumps(value))
    assert process.returncode == 2
    assert json.loads(process.stdout)["status"] == "invalid-input"
    assert process.stderr == ""
    assert {
        str(path.relative_to(repository)) for path in repository.rglob("*")
    } == before


@pytest.mark.parametrize(
    "case", ["source-sha", "native-id", "native-version", "family"]
)
def test_whole_binding_identity_mismatch_rejects_before_preparation(repository, case):
    value = whole_plan(repository)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    component = draft["composition"]["components"][0]
    binding = json.loads((repository / component["binding"]["path"]).read_bytes())
    if case == "family":
        binding["family"] = "goal"
        binding["entrypoints"] = ["epic-handler"]
    else:
        binding["procedure"][
            {
                "source-sha": "source_sha256",
                "native-id": "id",
                "native-version": "version",
            }[case]
        ] = {
            "source-sha": bundles.sha256(b"different source"),
            "native-id": "different-native-id",
            "native-version": "2",
        }[case]
    component["binding"] = reference(repository, component["binding"]["path"], binding)
    assert_error("incompatible", lambda: composition.compose(repository, draft))


@pytest.mark.parametrize(
    "case", ["goal", "closeout", "role", "coverage", "port-type", "parameter"]
)
def test_fragment_contract_violations_reach_their_actual_boundaries(repository, case):
    value = fragment_plan(repository)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    component = draft["composition"]["components"][0]
    if case == "goal":
        component["mapping"]["goal_assessments"] = [{"node": "assess", "outcomes": {}}]
    elif case == "closeout":
        component["mapping"]["closeout"] = [
            {"node": "assess", "kind": "shared", "requires": []}
        ]
    elif case == "role":
        component["mapping"]["nodes"]["assess"]["role"] = "executor"
    elif case == "parameter":
        component["parameters"]["undeclared"] = "value"
    else:

        def change(fragment):
            if case == "coverage":
                fragment["assessors"][0]["covers"].append("assess")
            else:
                fragment["outputs"]["assessment"]["type"] = "integer"

        amend_fragment(repository, draft, change)
    assert_error("incompatible", lambda: composition.compose(repository, draft))


@pytest.mark.parametrize("break_value", ["\n", "\r", "\x85", "\u2028", "\u2029"])
def test_renderer_preserves_native_line_break_values(repository, break_value):
    value = fragment_plan(repository)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    expected = "Original" + break_value + "evidence"
    amend_fragment(
        repository,
        draft,
        lambda fragment: fragment["node_definitions"]["deliver"].update(
            instructions=[expected]
        ),
    )
    result = prep.prepare(repository, value, client=Oracle(repository))
    source = Path(result["assignment"]["target"]["prepared_definition"]["source_path"])
    assert yaml.safe_load(source.read_bytes())["node_definitions"]["work-deliver"][
        "instructions"
    ] == [expected]


@pytest.mark.parametrize("case", ["binding-drift", "native-tuple"])
def test_whole_preparation_rechecks_binding_bytes_and_native_tuple(repository, case):
    value = whole_plan(repository)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    component = draft["composition"]["components"][0]

    class ChangedInput(Oracle):
        def _read(self, arguments, command, schemas):
            if case == "binding-drift" and command == "procedure.format":
                (repository / component["binding"]["path"]).write_bytes(b"{}")
            return super()._read(arguments, command, schemas)

        def identity(self, path):
            key = super().identity(path)
            if case == "native-tuple" and path.name == "import.yaml":
                return (key[0], key[1], bundles.sha256(b"different-native-tuple"))
            return key

    assert_error(
        "source-drift",
        lambda: prep.prepare(repository, value, client=ChangedInput(repository)),
    )
    candidates = repository / "definitions/.candidates"
    assert candidates.is_dir()
    assert set(candidates.rglob("*")) == {candidates / ".gitignore"}


def test_identical_imports_expand_into_distinct_namespaces(repository):
    value = fragment_plan(repository)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    second = copy.deepcopy(draft["composition"]["components"][0])
    second["namespace"] = "again"
    draft["composition"]["components"].append(second)
    draft["composition"]["control"] = [
        {
            "from": {"component": "work", "exit": "assessed"},
            "to": {"component": "again"},
        },
        {
            "from": {"component": "again", "exit": "assessed"},
            "to": {"component": "root", "node": "outcome"},
        },
    ]
    result = composition.compose(repository, draft)
    assert (
        result["document"]["node_definitions"]["work-deliver"]
        == result["document"]["node_definitions"]["again-deliver"]
    )
    assert (
        result["mapping"]["nodes"]["work-assess"]
        == result["mapping"]["nodes"]["again-assess"]
    )
    assert len(result["origins"]) == 2


@pytest.mark.parametrize(
    "case",
    [
        "pass",
        "rework",
        "evidence-needed",
        "unmet",
        "unverified",
        "applicability-fail",
        "applicability-inconclusive",
        "stopped",
        "not-achieved",
        "superseded",
    ],
)
def test_own_control_achieved_path_requires_current_complete_assessment(case):
    assets = prep.ASSETS / "adaptive/reusable"
    document = yaml.safe_load((assets / "task-goal-control.yaml").read_bytes())
    binding = parse_definition((assets / "task-goal-control.binding.json").read_bytes())
    composition.check_graph(document)
    assert binding["procedure"]["source_sha256"] == bundles.sha256(
        (assets / "task-goal-control.yaml").read_bytes()
    )
    facts = {
        "evaluator-verdict": "pass",
        "evaluator-unmet-criteria": 0,
        "evaluator-unverified-criteria": 0,
        "evaluator-applicability": {"outcome": "pass"},
        "evaluator-goal-outcome": "achieved",
    }
    if case in {"rework", "evidence-needed"}:
        facts["evaluator-verdict"] = case
    elif case in {"unmet", "unverified"}:
        facts["evaluator-" + case + "-criteria"] = 1
    elif case.startswith("applicability-"):
        facts["evaluator-applicability"]["outcome"] = case.removeprefix(
            "applicability-"
        )
    elif case in {"stopped", "not-achieved", "superseded"}:
        facts["evaluator-goal-outcome"] = case
        facts["evaluator-verdict"] = "rework"

    def satisfied(guard):
        value = facts[guard["evidence"]["item"]]
        if "field" in guard:
            value = value[guard["field"]]
        return (
            value == guard["equals"]
            if "equals" in guard
            else value != guard["not_equals"]
        )

    nodes = {node["id"]: node for node in document["graph"]["nodes"]}
    goal_options = document["node_definitions"]["goal-route"]["options"]
    eligible = [
        option["id"] for option in goal_options if all(map(satisfied, option["guards"]))
    ]
    assert len(eligible) == 1
    route = nodes["goal-route"]["routes"][eligible[0]]
    if facts["evaluator-goal-outcome"] == "achieved":
        assert route["to"] == "assessment-current"
        option = document["node_definitions"]["assessment-current"]["options"][0]
        current = all(map(satisfied, option["guards"]))
        assert current is (case == "pass")
        selected = "current" if current else "not-current"
        route = nodes["assessment-current"]["routes"][selected]
        assert route == (
            {"to": "outcome", "effect": "advance"}
            if current
            else {"to": "assess", "effect": "rework"}
        )
    else:
        assert route == {"to": "outcome", "effect": "advance"}
    outcomes = document["node_definitions"]["outcome"]["assessment"]["outcomes"]
    assert outcomes == {
        "achieved": "achieved",
        "stopped": "not_achieved",
        "not-achieved": "not_achieved",
        "superseded": "superseded",
    }


@pytest.mark.parametrize("existing_required", [False, True])
def test_wiring_adds_a_distinct_applicability_row(repository, existing_required):
    value = fragment_plan(repository)
    draft = value["target"]["procedure_plan"]["drafts"][0]

    def change(fragment):
        fragment["node_definitions"]["deliver"]["items"].append(
            {
                **fragment["node_definitions"]["deliver"]["items"][0],
                "id": "observation",
                "required": False,
            }
        )
        fragment["placements"][-1]["evidence_from"] = [
            {
                "node": "deliver",
                "required": existing_required,
                "items": ["documentation" if existing_required else "observation"],
            }
        ]
        for key, required in [("documentation", True), ("observation", False)]:
            fragment["outputs"][key] = {
                "type": "text",
                "required": required,
                "endpoint": {"node": "deliver", "item": key},
            }
            fragment["inputs"][key] = {
                "type": "text",
                "required": required,
                "endpoint": {"node": "assess", "item": "assessment"},
            }

    fragment = amend_fragment(repository, draft, change)
    draft["composition"]["evidence"] = [
        {
            "from": {"component": "work", "port": key},
            "to": {"component": "work", "port": key},
        }
        for key in ["documentation", "observation"]
    ]
    result = composition.compose(repository, draft)
    selectors = next(
        node
        for node in result["document"]["graph"]["nodes"]
        if node["id"] == "work-assess"
    )["evidence_from"]
    assert selectors[0] == {
        **fragment["placements"][-1]["evidence_from"][0],
        "node": "work-deliver",
    }
    assert {row["required"] for row in selectors} == {False, True}
    assert len(selectors) == 2


def test_alias_swaps_and_explicit_logical_overrides_preserve_original_meanings(
    repository,
):
    value = fragment_plan(repository)
    draft = value["target"]["procedure_plan"]["drafts"][0]

    def change(fragment):
        fragment["node_definitions"]["assess"]["items"].append(
            {**fragment["node_definitions"]["assess"]["items"][0], "id": "context"}
        )

    amend_fragment(repository, draft, change)
    component = draft["composition"]["components"][0]
    component["fields"] = {"assess": {"assessment": "context", "context": "assessment"}}
    component["mapping"]["nodes"]["assess"]["capabilities"] = [
        {"signature": "example.explicit-operation/v1", "fields": {}},
        {
            "signature": "example.explicit-operation/v1",
            "fields": {"assessment": "context"},
        },
    ]
    result = composition.compose(repository, draft)
    capabilities = result["mapping"]["nodes"]["work-assess"]["capabilities"]
    assert capabilities[0]["fields"] == {
        "assessment": "context",
        "context": "assessment",
    }
    assert capabilities[1]["fields"] == {
        "assessment": "assessment",
        "context": "assessment",
    }


@pytest.mark.parametrize("producer", ["work-assess", "absent-producer"])
def test_root_evidence_requires_an_actual_producer(repository, producer):
    value = fragment_plan(repository, mode="plan-only")
    draft = value["target"]["procedure_plan"]["drafts"][0]
    outcome = next(
        node for node in draft["document"]["graph"]["nodes"] if node["id"] == "outcome"
    )
    outcome["evidence_from"][0]["node"] = producer
    if producer == "absent-producer":
        assert_error("incompatible", lambda: composition.compose(repository, draft))
    else:
        result = composition.compose(repository, draft)
        outcome = next(
            node
            for node in result["document"]["graph"]["nodes"]
            if node["id"] == "outcome"
        )
        assert outcome["evidence_from"] == [
            {"node": producer, "items": ["assessment"], "required": True}
        ]
