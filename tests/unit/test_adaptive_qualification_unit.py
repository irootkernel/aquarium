"""Objective obligation proofs; synthetic fixtures do not attest actual agents."""

import copy
import json
import sys
import time
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "plugins/aquarium/shared"))

from adaptive_admission import reference_mapping
from adaptive_bundles import sha256
from adaptive_composition import expand
from adaptive_definitions import ASSETS, canonical_json, capability_signatures
from adaptive_predicates import ABSENT, UNKNOWN, Decisions, item_domain
from adaptive_qualification import qualify


def bound(document, mapping):
    return {
        **mapping,
        "procedure": {
            "id": document["id"],
            "version": document["version"],
            "digest": sha256(b"synthetic native digest"),
            "source_sha256": sha256(canonical_json(document)),
        },
    }


def known(family):
    raw = (
        ASSETS / "podway/procedures" / ("aquarium-" + family + "-v2.yaml")
    ).read_bytes()
    document = yaml.safe_load(raw)
    return document, bound(document, reference_mapping(raw))


def with_review(document, mapping, context):
    """A work-specific review operation with current route and internal recovery."""
    registry = capability_signatures()
    control = copy.deepcopy(registry["aquarium.task.review-control/v1"])
    wanted = {
        "review-operation",
        "assessment-ordinal",
        "assessment-ordinal-continuity",
        "review-mode",
        "assessment-kind",
    }
    fields = {key: value for key, value in control["fields"].items() if key in wanted}
    route = copy.deepcopy(
        registry["aquarium.goal.review-control/v1"]["fields"]["route-binding-result"]
    )
    fields["route-binding-result"] = route
    native = yaml.safe_load(
        (ASSETS / "podway/procedures/aquarium-task-v2.yaml").read_bytes()
    )
    native_items = {
        item["id"]: item
        for item in native["node_definitions"]["review-record"]["items"]
    }
    goal = yaml.safe_load(
        (ASSETS / "podway/procedures/aquarium-goal-v2.yaml").read_bytes()
    )
    native_items.update(
        {
            item["id"]: item
            for item in goal["node_definitions"]["evidence-record"]["items"]
            if item["id"] == "route-binding-result"
        }
    )
    items = []
    for name, specification in fields.items():
        item = copy.deepcopy(native_items.get(name, {"id": name, **specification}))
        item.update(prompt="Record actual " + name, required=True)
        item.pop("required_when", None)
        if name == "review-mode":
            item["choices"] = ["remediation-eligible"]
        if name == "assessment-kind":
            item["choices"] = ["work-unit"]
        if name == "assessment-ordinal":
            item["maximum"] = 3
        if item["type"] == "check_result":
            item.setdefault(
                "help",
                "Verify the exact declared operation against current selected review evidence and authority.",
            )
        items.append(item)
    record = {
        "type": "action",
        "title": "Collect the selected technical review",
        "intent": "Record complete selected review evidence without product changes.",
        "instructions": [
            "Recover every expected report from the same pending operation without consuming a new ordinal. Preserve actual incomplete/failed state and authoritative settlement. Accept route change or waiver only under explicit existing user direction and remaining authority; never silently switch or start a new review."
        ],
        "items": items,
    }
    options = [
        {
            "id": "complete",
            "label": "Complete",
            "criteria": "The actual selected operation completed with established route binding and current ordinal.",
            "guards": [
                {
                    "evidence": {"node": "collect-review", "item": "review-operation"},
                    "equals": "complete",
                },
                {
                    "evidence": {
                        "node": "collect-review",
                        "item": "assessment-ordinal-continuity",
                    },
                    "field": "outcome",
                    "equals": "pass",
                },
                {
                    "evidence": {
                        "node": "collect-review",
                        "item": "route-binding-result",
                    },
                    "field": "outcome",
                    "equals": "pass",
                },
                {
                    "evidence": {
                        "node": "collect-review",
                        "item": "assessment-ordinal",
                    },
                    "at_least": 1,
                },
            ],
        },
        {
            "id": "recover",
            "label": "Recover",
            "criteria": "Required selected review evidence remains incomplete; recover under its current owner.",
        },
    ]
    router = {
        "type": "decision",
        "title": "Check selected review delivery",
        "objective": "Preserve current operation and review authority.",
        "prompt": "Is complete review evidence available?",
        "options": options,
        "reason": {
            "required": True,
            "prompt": "Cite complete result or exact recovery gap.",
        },
    }
    document["node_definitions"].update(
        {"collect-review": record, "check-review": router}
    )
    for node in document["graph"]["nodes"]:
        if node.get("next") == "assess":
            node["next"] = "collect-review"
        for edge in node.get("routes", {}).values():
            if edge["to"] == "assess":
                edge["to"] = "collect-review"
    document["graph"]["nodes"] += [
        {"id": "collect-review", "use": "collect-review", "next": "check-review"},
        {
            "id": "check-review",
            "use": "check-review",
            "evidence_from": [
                {
                    "node": "collect-review",
                    "required": True,
                    "items": [item["id"] for item in items],
                }
            ],
            "routes": {
                "complete": {"to": "assess", "effect": "advance"},
                "recover": {"to": "collect-review", "effect": "rework"},
            },
        },
    ]
    mapping.setdefault("capability_definitions", {})["fixture.review-routing/v1"] = {
        "kind": "action",
        "guarantee": "review-routing",
        "fields": {"route-binding-result": route},
        "relationships": [],
    }
    mapping["nodes"]["collect-review"] = {
        "kind": "action",
        "role": "orchestrator",
        "effects": [],
        "capabilities": [
            {"signature": "aquarium.task.review-control/v1", "fields": {}},
            {"signature": "fixture.review-routing/v1", "fields": {}},
        ],
    }
    # Use a minimal declared control signature; unrelated canonical finding-count
    # fields are neither selected obligations nor a native topology requirement.
    mapping["capability_definitions"]["fixture.review-control/v1"] = {
        "kind": "action",
        "guarantee": "review-control",
        "fields": fields,
        "relationships": [],
    }
    mapping["nodes"]["collect-review"]["capabilities"][0]["signature"] = (
        "fixture.review-control/v1"
    )
    mapping["nodes"]["check-review"] = {
        "kind": "decision",
        "role": "orchestrator",
        "effects": [],
        "capabilities": [],
    }
    context["review"] = {"route": "herdr"}
    context["operation_contracts"][sha256(canonical_json(record))] = {
        "roles": ["orchestrator"],
        "effect": "evidence",
        "basis": "Explicit selected review operation with bounded original route/authority and same-operation report recovery.",
        "review_recovery": ["same-operation-recovery", "review-route-change"],
    }
    return document, mapping, context


def adaptive(*, performance=False):
    document = yaml.safe_load(
        (ASSETS / "adaptive/reusable/task-goal-control.yaml").read_bytes()
    )
    mapping = json.loads(
        (ASSETS / "adaptive/reusable/task-goal-control.binding.json").read_bytes()
    )
    document["id"] = "aquarium-adapt-task-proof"
    document["version"] = "1"
    text = {
        "id": "documentation",
        "type": "text",
        "prompt": "Deliver the approved document",
        "required": True,
        "min_length": 1,
        "max_length": 2000,
    }
    document["node_definitions"]["deliver"] = {
        "type": "action",
        "title": "Deliver original work",
        "intent": "Produce the approved actual artifact",
        "items": [text],
    }
    document["node_definitions"]["accept"] = {
        "type": "decision",
        "title": "Accept current exact result",
        "objective": "Preserve the actual current acceptance and separate commit grant",
        "prompt": "Is the current exact result accepted?",
        "options": [
            {
                "id": "approved",
                "label": "Approved",
                "criteria": "The actual eligible accepting decision addresses the exact current result.",
            },
            {
                "id": "changes-requested",
                "label": "Changes requested",
                "criteria": "Return the exact owned changes under current authority.",
            },
        ],
        "reason": {
            "required": True,
            "prompt": "Reference the exact accepting decision, current target and remaining grants.",
        },
    }
    nodes = document["graph"]["nodes"]
    nodes.insert(0, {"id": "deliver", "use": "deliver", "next": "assess"})
    next(node for node in nodes if node["id"] == "assess")["evidence_from"] = [
        {"node": "deliver", "required": True, "items": ["documentation"]}
    ]
    for route in next(node for node in nodes if node["id"] == "outcome")[
        "routes"
    ].values():
        route["to"] = "accept"
    nodes.insert(
        -1,
        {
            "id": "accept",
            "use": "accept",
            "evidence_from": [
                {
                    "node": "assess",
                    "required": True,
                    "items": ["judge-assessment", "judge-goal-outcome"],
                }
            ],
            "routes": {
                "approved": {"to": "closeout", "effect": "advance"},
                "changes-requested": {"to": "deliver", "effect": "rework"},
            },
        },
    )
    document["graph"]["entry"] = "deliver"
    mapping["nodes"]["deliver"] = {
        "kind": "action",
        "role": "worker",
        "effects": ["work"],
        "capabilities": [],
    }
    mapping["nodes"]["accept"] = {
        "kind": "decision",
        "role": "orchestrator",
        "effects": [],
        "capabilities": [{"signature": "aquarium.task.approval/v1", "fields": {}}],
    }
    mapping["obligations"]["original-goal"]["producers"] = [
        {"node": "deliver", "item": "documentation"}
    ]
    closeout = document["node_definitions"]["closeout"]
    context = {
        "review": {"route": "not-applicable"},
        "operation_contracts": {
            sha256(canonical_json(closeout)): {
                "roles": ["orchestrator"],
                "effect": "finalization",
                "basis": "Explicit verified fixture result-delivery operation; no product writes or grants.",
            }
        },
    }
    if performance:
        document["node_definitions"]["measure"] = {
            "type": "action",
            "title": "Measure actual latency",
            "intent": "Record the authorized measurement",
            "items": [
                {
                    "id": "latency",
                    "type": "integer",
                    "prompt": "Record measured milliseconds",
                    "required": True,
                    "minimum": 0,
                    "maximum": 100000,
                }
            ],
        }
        document["node_definitions"]["classify"] = {
            "type": "decision",
            "title": "Choose actual work",
            "objective": "Use the actual measurement",
            "prompt": "Is tuning due?",
            "options": [
                {
                    "id": "tune",
                    "label": "Tune",
                    "criteria": "Measured latency exceeds the budget",
                    "guards": [
                        {
                            "evidence": {"node": "measure", "item": "latency"},
                            "at_least": 101,
                        }
                    ],
                },
                {
                    "id": "preserve",
                    "label": "Preserve",
                    "criteria": "Measured latency is within budget",
                    "guards": [
                        {
                            "evidence": {"node": "measure", "item": "latency"},
                            "at_most": 100,
                        }
                    ],
                },
            ],
            "reason": {
                "required": True,
                "prompt": "Cite measurement and actual strategy",
            },
        }
        document["node_definitions"]["preserve"] = {
            **copy.deepcopy(document["node_definitions"]["deliver"]),
            "title": "Preserve verified fast behavior",
        }
        nodes.insert(0, {"id": "measure", "use": "measure", "next": "classify"})
        nodes.insert(
            1,
            {
                "id": "classify",
                "use": "classify",
                "evidence_from": [
                    {"node": "measure", "required": True, "items": ["latency"]}
                ],
                "routes": {
                    "tune": {"to": "deliver", "effect": "advance"},
                    "preserve": {"to": "preserve", "effect": "advance"},
                },
            },
        )
        nodes.insert(3, {"id": "preserve", "use": "preserve", "next": "assess"})
        document["graph"]["entry"] = "measure"
        next(node for node in nodes if node["id"] == "accept")["routes"][
            "changes-requested"
        ]["to"] = "measure"
        next(node for node in nodes if node["id"] == "assess")["evidence_from"] = [
            {"node": "measure", "required": True, "items": ["latency"]},
            {"node": "deliver", "required": False, "items": ["documentation"]},
            {"node": "preserve", "required": False, "items": ["documentation"]},
        ]
        mapping["nodes"]["measure"] = copy.deepcopy(mapping["nodes"]["deliver"])
        mapping["nodes"]["preserve"] = copy.deepcopy(mapping["nodes"]["deliver"])
        mapping["nodes"]["classify"] = {
            "kind": "decision",
            "role": "orchestrator",
            "effects": [],
            "capabilities": [],
        }
        mapping["obligations"]["original-goal"]["producers"] += [
            {"node": "measure", "item": "latency"},
            {"node": "preserve", "item": "documentation"},
        ]
    document, mapping, context = with_review(document, mapping, context)
    return document, bound(document, mapping), context


@pytest.mark.parametrize("family", ["task", "goal", "validation", "design", "war-room"])
def test_current_canonical_structures_use_general_obligation_analysis(family):
    document, binding = known(family)
    result = qualify(document, binding)
    assert result["status"] == "compatible", result["issues"]
    assert result["analysis"]["symbolic_nodes"] > 2


@pytest.mark.parametrize("performance", [False, True])
def test_genuinely_adaptive_work_and_grouped_conditional_evidence_qualify(performance):
    document, binding, context = adaptive(performance=performance)
    result = qualify(document, binding, context=context)
    assert result["status"] == "compatible", result["issues"]


@pytest.mark.parametrize("value", [True])
def test_native_confirm_preserves_typed_reachable_values(value):
    domain = item_domain({"type": "confirm", "required": True}, [{"equals": value}])
    assert domain == [True]
    logic = Decisions({("record", "confirm"): domain})
    selected = logic.predicate(("record", "confirm"), {"equals": value})
    assert selected != 0
    assert (
        logic.all(
            selected, logic.predicate(("record", "confirm"), {"equals": int(value)})
        )
        == 0
    )


@pytest.mark.parametrize(
    "predicate",
    [{"equals": True}, {"not_equals": "pass"}, {"non_empty": True}, {"at_least": 0}],
)
def test_missing_or_unsupported_native_values_remain_explicit_unknown(predicate):
    for domain in [
        [UNKNOWN],
        item_domain({"type": "unsupported", "required": True}, [predicate]),
    ]:
        logic = Decisions({("record", "value"): domain})
        expression = logic.predicate(("record", "value"), predicate)
        assert expression != 0
        assert logic.has_unknown(expression)


@pytest.mark.parametrize(
    "field",
    [
        "judge-goal-outcome",
        "judge-verdict",
        "judge-unmet-criteria",
        "judge-unverified-criteria",
        "judge-applicability",
    ],
)
def test_each_final_fact_is_required_directly_or_through_guarded_chain(field):
    document, binding, context = adaptive()
    for definition in document["node_definitions"].values():
        for option in definition.get("options", []):
            option["guards"] = [
                guard
                for guard in option.get("guards", [])
                if guard["evidence"]["item"] != field
            ]
            if not option["guards"]:
                option.pop("guards")
    result = qualify(document, binding, context=context)
    assert result["status"] == "incompatible"
    assert any(
        row["property"] == "current-final-assessment-and-forward-effects"
        for row in result["issues"]
    )


@pytest.mark.parametrize("case", ["worker-label", "text-verdict", "pass-only"])
def test_binding_labels_cannot_forge_independent_assessment_capabilities(case):
    document, binding, context = adaptive()
    if case == "worker-label":
        binding["nodes"]["assess"]["role"] = "worker"
    else:
        item = next(
            item
            for item in document["node_definitions"]["assess"]["items"]
            if item["id"]
            == ("judge-verdict" if case == "text-verdict" else "judge-applicability")
        )
        if case == "text-verdict":
            item.update(type="text", min_length=1)
            item.pop("choices")
        else:
            item["accepted_outcomes"] = ["pass"]
    result = qualify(document, binding, context=context)
    assert result["status"] == "incompatible"


@pytest.mark.parametrize("declared", [False, True])
def test_post_assessment_effects_distinguish_unknown_from_proven_work(declared):
    document, binding, context = adaptive()
    document["node_definitions"]["polish"] = copy.deepcopy(
        document["node_definitions"]["deliver"]
    )
    document["node_definitions"]["polish"]["title"] = (
        "Change the current target after assessment"
    )
    next(node for node in document["graph"]["nodes"] if node["id"] == "assess")[
        "next"
    ] = "polish"
    document["graph"]["nodes"].append(
        {"id": "polish", "use": "polish", "next": "goal-route"}
    )
    binding["nodes"]["polish"] = {
        "kind": "action",
        "role": "worker",
        "effects": ["work"] if declared else [],
        "capabilities": [],
    }
    result = qualify(document, binding, context=context)
    assert result["status"] == ("incompatible" if declared else "not-established")


@pytest.mark.parametrize("performance", [False, True])
def test_relevant_item_must_be_selected_on_the_actual_producer_path(performance):
    document, binding, context = adaptive(performance=performance)
    document["node_definitions"]["deliver"]["items"].append(
        {
            "id": "unrelated",
            "type": "text",
            "prompt": "Record unrelated bookkeeping",
            "required": True,
        }
    )
    assessor = next(
        node for node in document["graph"]["nodes"] if node["id"] == "assess"
    )
    next(row for row in assessor["evidence_from"] if row["node"] == "deliver")[
        "items"
    ] = ["unrelated"]
    result = qualify(document, binding, context=context)
    assert result["status"] == "incompatible"
    assert any(
        row["property"] == "original-producer-evidence" for row in result["issues"]
    )


def test_analysis_resource_exhaustion_is_never_success():
    document, binding, context = adaptive()
    result = qualify(document, binding, context=context, node_budget=3)
    assert result["status"] == "not-established"
    assert result["issues"][0]["property"] == "analysis-resource"


def test_absent_native_guard_is_unavailable_and_confirm_false_is_infeasible():
    for predicate in ({"equals": True}, {"not_equals": "pass"}, {"non_empty": True}):
        logic = Decisions({("record", "missing"): [ABSENT]})
        assert logic.predicate(("record", "missing"), predicate) == 0
    logic = Decisions(
        {
            ("record", "confirmed"): item_domain(
                {"type": "confirm", "required": True}, []
            )
        }
    )
    assert logic.predicate(("record", "confirmed"), {"equals": False}) == 0


def insert_action(document, binding, before, identifier, *, declared=True):
    source = {
        "type": "action",
        "title": "Change the actual approved content",
        "intent": "Produce a new target after the existing gate",
        "items": [
            {
                "id": "changed-target",
                "type": "text",
                "prompt": "Record actual changed bytes",
                "required": True,
            }
        ],
    }
    for node in document["graph"]["nodes"]:
        if node.get("next") == before:
            node["next"] = identifier
        for route in node.get("routes", {}).values():
            if route["effect"] == "advance" and route["to"] == before:
                route["to"] = identifier
    document["node_definitions"][identifier] = source
    document["graph"]["nodes"].append(
        {"id": identifier, "use": identifier, "next": before}
    )
    binding["nodes"][identifier] = {
        "kind": "action",
        "role": "worker",
        "effects": ["work"] if declared else [],
        "capabilities": [],
    }


@pytest.mark.parametrize("declared", [False, True])
def test_post_acceptance_effect_is_unknown_or_proven_work_without_exemption(declared):
    document, binding, context = adaptive()
    insert_action(document, binding, "closeout", "late-change", declared=declared)
    result = qualify(document, binding, context=context)
    assert result["status"] == ("incompatible" if declared else "not-established")


@pytest.mark.parametrize("declared", [False, True])
def test_proposal_changes_after_exact_approval_need_renewed_approval(declared):
    document, binding = known("design")
    insert_action(
        document, binding, "apply-documents", "late-proposal", declared=declared
    )
    result = qualify(document, binding)
    expected = "incompatible" if declared else "not-established"
    assert any(
        row["property"] == "exact-approval-before-current-application"
        and row["status"] == expected
        for row in result["issues"]
    )


@pytest.mark.parametrize(
    "family,context",
    [
        ("goal", {"goal_kind": "epic-closeout"}),
        ("validation", {"workflow_owner": "epic-validator"}),
    ],
)
def test_delegated_acceptance_uses_actual_discriminator_context(family, context):
    document, binding = known(family)
    decision = document["node_definitions"][
        next(
            node["use"]
            for node in document["graph"]["nodes"]
            if node["id"] == "approve-closeout"
        )
    ]
    delegated = next(
        option for option in decision["options"] if option["id"] == "delegated"
    )
    delegated["guards"] = [
        guard
        for guard in delegated["guards"]
        if guard["evidence"]["item"] == "acceptance-source"
    ]
    result = qualify(document, binding, context=context)
    assert result["status"] == "incompatible"
    assert any(row["property"] == "acceptance-provenance" for row in result["issues"])


@pytest.mark.parametrize(
    "family,item",
    [
        ("task", "route-direction-continuity"),
        ("goal", "route-binding-result"),
        ("validation", "route-binding-result"),
    ],
)
def test_route_result_cannot_be_replaced_by_signature_presence(family, item):
    document, binding = known(family)
    for definition in document["node_definitions"].values():
        for option in definition.get("options", []):
            option["guards"] = [
                guard
                for guard in option.get("guards", [])
                if guard["evidence"]["item"] != item
            ]
    result = qualify(document, binding)
    assert result["status"] == "incompatible"
    assert any(
        row["property"] == "review-route-result-continuity" for row in result["issues"]
    )


def test_extra_confirmation_ordinal_does_not_reset_authority():
    document, binding = known("goal")
    for definition in document["node_definitions"].values():
        for option in definition.get("options", []):
            option["guards"] = [
                guard
                for guard in option.get("guards", [])
                if guard["evidence"]["item"] != "extra-assessment-authority-reference"
            ]
    result = qualify(document, binding)
    assert result["status"] == "incompatible"
    assert any(
        row["property"] == "extra-confirmation-authority" for row in result["issues"]
    )


def test_typed_aliases_and_namespaces_keep_actual_operation_identity():
    document, binding, context = adaptive(performance=True)
    mapped = {key: value for key, value in binding.items() if key != "procedure"}
    source, mapped, _, _ = expand(
        document,
        mapped,
        "query",
        {
            "assess": {
                "judge-verdict": "assessment-state",
                "judge-applicability": "current-target",
            }
        },
    )
    source["id"] = "aquarium-adapt-task-namespaced"
    result = qualify(source, bound(source, mapped), context=context)
    assert result["status"] == "compatible", result["issues"]


def equivalent_assessment():
    document, binding, context = adaptive()
    fields = next(
        cap
        for cap in binding["nodes"]["assess"]["capabilities"]
        if cap["signature"].endswith("final-assessment/v1")
    )
    from adaptive_definitions import capability_signatures

    signature = copy.deepcopy(capability_signatures()[fields["signature"]])
    fields["signature"] = "repository.current-final-assessment/v1"
    item = next(
        item
        for item in document["node_definitions"]["assess"]["items"]
        if item["id"] == "judge-applicability"
    )
    item["operation_id"] = "repository-current-assessment"
    item["operation_digest"] = sha256(
        b"Explicit equivalent current-source assessment contract"
    )
    signature["fields"]["judge-applicability"]["operation_id"] = item["operation_id"]
    signature["fields"]["judge-applicability"]["operation_digest"] = item[
        "operation_digest"
    ]
    binding["capability_definitions"] = {
        fields["signature"]: signature,
        **binding.get("capability_definitions", {}),
    }
    return document, binding, context


def test_equivalent_explicit_operation_and_self_contained_definition():
    document, binding, context = equivalent_assessment()
    result = qualify(document, binding, context=context)
    assert result["status"] == "compatible", result["issues"]


def test_native_bound_placement_count_uses_shared_analysis_without_path_enumeration():
    document, binding, context = adaptive()
    definition = {
        "type": "action",
        "title": "Carry declared local evidence",
        "intent": "Record harmless bookkeeping",
        "items": [
            {
                "id": "note",
                "type": "text",
                "prompt": "Record a note",
                "required": True,
                "min_length": 1,
            }
        ],
    }
    document["node_definitions"]["note"] = definition
    context["operation_contracts"][sha256(canonical_json(definition))] = {
        "roles": ["orchestrator"],
        "effect": "evidence",
        "basis": "Explicit fixture bookkeeping with no product effects",
    }
    previous = document["graph"]["entry"]
    for ordinal in range(1024 - len(document["graph"]["nodes"])):
        name = "note-" + sha256(str(ordinal).encode())[7:31]
        document["graph"]["nodes"].insert(
            0, {"id": name, "use": "note", "next": previous}
        )
        binding["nodes"][name] = {
            "kind": "action",
            "role": "orchestrator",
            "effects": [],
            "capabilities": [],
        }
        previous = name
    document["graph"]["entry"] = previous
    started = time.monotonic()
    result = qualify(document, binding, context=context)
    assert result["status"] == "compatible", result["issues"]
    assert result["analysis"]["placements"] == 1024
    assert result["analysis"]["symbolic_nodes"] > 2
    assert time.monotonic() - started < 30


def test_confirmation_cannot_run_new_product_work_before_fresh_direction():
    document, binding = known("task")
    insert_action(document, binding, "judge-review", "another-remediation")
    result = qualify(document, binding)
    assert result["status"] == "incompatible"
    assert any(
        row["property"] == "fresh-direction-after-confirmation"
        for row in result["issues"]
    )


def test_unrelated_pass_only_native_operation_has_no_assessment_claim():
    document, binding, context = adaptive()
    operation = {
        "type": "action",
        "title": "Block until the prerequisite passes",
        "intent": "Observe a prerequisite without changing product evidence",
        "items": [
            {
                "id": "prerequisite",
                "type": "check_result",
                "prompt": "Record the prerequisite",
                "required": True,
                "operation_id": "fixture-prerequisite",
                "operation_digest": sha256(b"Actual prerequisite operation"),
                "accepted_outcomes": ["pass"],
            }
        ],
    }
    document["node_definitions"]["prerequisite"] = operation
    document["graph"]["nodes"].insert(
        0,
        {
            "id": "prerequisite",
            "use": "prerequisite",
            "next": document["graph"]["entry"],
        },
    )
    document["graph"]["entry"] = "prerequisite"
    binding["nodes"]["prerequisite"] = {
        "kind": "action",
        "role": "orchestrator",
        "effects": [],
        "capabilities": [],
    }
    context["operation_contracts"][sha256(canonical_json(operation))] = {
        "roles": ["orchestrator"],
        "effect": "evidence",
        "basis": "Explicit no-product-effects prerequisite",
    }
    assert qualify(document, binding, context=context)["status"] == "compatible"


@pytest.mark.parametrize("family", ["goal", "validation"])
def test_stopped_native_not_achieved_delivery_still_requires_actual_user(family):
    document, binding = known(family)
    node = next(
        node
        for node in document["graph"]["nodes"]
        if node["id"] == "approve-stopped-closeout"
    )
    definition = document["node_definitions"][node["use"]]
    definition["options"].append(
        {
            "id": "delegated",
            "label": "Delegated",
            "criteria": "Incorrectly accept stopped delivery under internal delegation",
            "guards": [
                {
                    "evidence": {
                        "node": "record-stopped-outcome",
                        "item": "acceptance-source",
                    },
                    "equals": "epic-delegation",
                }
            ],
        }
    )
    node["routes"]["delegated"] = copy.deepcopy(node["routes"]["approved"])
    result = qualify(
        document,
        binding,
        context={"goal_kind": "member-task", "workflow_owner": "epic-handler"},
    )
    assert result["status"] == "incompatible"
    assert any(row["property"] == "acceptance-provenance" for row in result["issues"])


def test_skippable_original_producer_cannot_vacuously_cover_the_goal():
    document, binding, context = adaptive()
    producer = next(
        node for node in document["graph"]["nodes"] if node["id"] == "deliver"
    )
    producer["skip"] = {"allowed": True, "reason_required": True}
    assessor = next(
        node for node in document["graph"]["nodes"] if node["id"] == "assess"
    )
    assessor["evidence_from"][0]["required"] = False
    result = qualify(document, binding, context=context)
    assert result["status"] == "incompatible"
    assert any(
        row["property"] == "applicable-original-producer" for row in result["issues"]
    )


def test_approval_options_can_use_explicit_typed_semantic_aliases():
    document, binding, context = adaptive()
    source = document["node_definitions"]["accept"]
    for option in source["options"]:
        option["id"] = {"approved": "accepted", "changes-requested": "revise"}[
            option["id"]
        ]
    node = next(node for node in document["graph"]["nodes"] if node["id"] == "accept")
    node["routes"] = {
        {"approved": "accepted", "changes-requested": "revise"}[key]: value
        for key, value in node["routes"].items()
    }
    binding["nodes"]["accept"]["capabilities"][0]["fields"] = {
        "approved": "accepted",
        "changes-requested": "revise",
    }
    result = qualify(document, binding, context=context)
    assert result["status"] == "compatible", result["issues"]


@pytest.mark.parametrize("family", ["task", "goal", "validation", "design", "war-room"])
def test_whole_canonical_namespace_expansion_preserves_qualified_control_contracts(
    family,
):
    document, binding = known(family)
    mapping = {key: value for key, value in binding.items() if key != "procedure"}
    document, mapping, _, _ = expand(document, mapping, "n", {})
    document["id"] = "aquarium-adapt-" + mapping["family"] + "-whole"
    document["version"] = "1"
    result = qualify(document, bound(document, mapping))
    assert result["status"] == "compatible", result["issues"]


@pytest.mark.parametrize(
    "mutation",
    [
        "pass-only",
        "missing-negative-verdict",
        "optional-report",
        "wrong-count-type",
        "unbounded-count-claim",
        "missing-actual-field",
    ],
)
def test_custom_signature_cannot_weaken_its_own_final_assessment_guarantee(mutation):
    document, binding, context = equivalent_assessment()
    signature = next(iter(binding["capability_definitions"].values()))
    items = {
        item["id"]: item for item in document["node_definitions"]["assess"]["items"]
    }
    if mutation == "pass-only":
        items["judge-applicability"]["accepted_outcomes"] = ["pass"]
        signature["fields"]["judge-applicability"]["accepted_outcomes"] = ["pass"]
    elif mutation == "missing-negative-verdict":
        items["judge-verdict"]["choices"] = ["pass", "rework"]
        signature["fields"]["judge-verdict"]["choices"] = ["pass", "rework"]
    elif mutation == "optional-report":
        items["judge-assessment"]["required"] = False
        signature["fields"]["judge-assessment"]["required"] = False
    elif mutation == "wrong-count-type":
        items["judge-unmet-criteria"].update(type="text", min_length=1)
        items["judge-unmet-criteria"].pop("minimum")
        signature["fields"]["judge-unmet-criteria"] = {"type": "text", "required": True}
    elif mutation == "unbounded-count-claim":
        signature.pop("criterion_counts")
        items["judge-unmet-criteria"]["maximum"] = 0
    else:
        # Remove the item and the custom signature requirement together. Keep
        # source references internally valid so the guarantee floor is exercised.
        document["node_definitions"]["assess"]["items"].remove(
            items["judge-assessment"]
        )
        signature["fields"].pop("judge-assessment")
        for node in document["graph"]["nodes"]:
            for row in node.get("evidence_from", []):
                if row["node"] == "assess" and "items" in row:
                    row["items"] = [
                        item for item in row["items"] if item != "judge-assessment"
                    ]
    result = qualify(
        document,
        bound(document, {k: v for k, v in binding.items() if k != "procedure"}),
        context=context,
    )
    assert result["status"] == (
        "not-established" if mutation == "unbounded-count-claim" else "incompatible"
    ), result
    assert any(row["property"] == "guarantee-minimum" for row in result["issues"])


@pytest.mark.parametrize(
    "family,placement,renames",
    [
        (
            "task",
            "record-plan",
            {"plan-summary": "current-plan", "worker-handoff": "current-handoff"},
        ),
        ("goal", "record-evidence", {"goal-kind": "current-goal-kind"}),
        ("task", "closeout", {"closeout-summary": "current-closeout"}),
    ],
)
def test_registered_semantic_aliases_remain_closed_and_qualified(
    family, placement, renames
):
    from adaptive_definitions import validate_definition

    document, binding = known(family)
    use = next(
        node["use"] for node in document["graph"]["nodes"] if node["id"] == placement
    )
    aliases = {
        node["id"]: renames for node in document["graph"]["nodes"] if node["use"] == use
    }
    document, mapping, _, _ = expand(
        document,
        {k: v for k, v in binding.items() if k != "procedure"},
        "n",
        aliases,
    )
    document["id"] = "aquarium-adapt-" + mapping["family"] + "-aliased"
    document["version"] = "1"
    current = bound(document, mapping)
    validate_definition(current)
    node = next(
        node for node in document["graph"]["nodes"] if node["id"] == "n-" + placement
    )
    contract = current["semantic_contracts"][
        sha256(canonical_json(document["node_definitions"][node["use"]]))
    ]
    assert contract["basis"]["native_version"] == binding["procedure"]["version"]
    for key in ("relay_outputs", "delivery_items", "output_scopes", "discriminators"):
        if key in contract:
            assert not set(renames) & set(contract[key])
    if placement == "record-plan":
        assert contract["output_scopes"]["current-plan"] == "task-plan"
        assert "current-handoff" in contract["relay_outputs"]
    result = qualify(document, current)
    assert result["status"] == "compatible", result


@pytest.mark.parametrize(
    "family,signature_id",
    [
        ("task", "aquarium.task.phase-assessment/v1"),
        ("validation", "aquarium.validation.audit-assessment/v1"),
        ("validation", "aquarium.validation.confirmation-audit-assessment/v1"),
        ("validation", "aquarium.validation.correction-group-assessment/v1"),
        ("design", "aquarium.design.quality-assessment/v1"),
        ("design", "aquarium.design.application-assessment/v1"),
        ("war-room", "aquarium.diagnosis.documentation-assessment/v1"),
        ("design", "aquarium.design.upstream-quality/v1"),
        ("design", "aquarium.design.application-approval/v1"),
        ("task", "aquarium.task.review-control/v1"),
        ("task", "aquarium.task.review-routing/v1"),
    ],
)
def test_other_recognized_guarantees_preserve_negative_check_recording(
    family, signature_id
):
    from adaptive_definitions import capability_signatures

    document, binding = known(family)
    node, capability = next(
        (node, cap)
        for node, row in binding["nodes"].items()
        for cap in row["capabilities"]
        if cap["signature"] == signature_id
    )
    signature = copy.deepcopy(capability_signatures()[signature_id])
    capability["signature"] = "repository.equivalent-capability/v1"
    binding["capability_definitions"] = {capability["signature"]: signature}
    positive = qualify(document, binding)
    assert positive["status"] == "compatible", positive
    check = next(
        name
        for name, field in signature["fields"].items()
        if field["type"] == "check_result"
    )
    signature["fields"][check]["accepted_outcomes"] = ["pass"]
    placement = next(row for row in document["graph"]["nodes"] if row["id"] == node)
    item = next(
        row
        for row in document["node_definitions"][placement["use"]]["items"]
        if row["id"] == capability["fields"].get(check, check)
    )
    item["accepted_outcomes"] = ["pass"]
    negative = qualify(
        document,
        bound(
            document,
            {key: value for key, value in binding.items() if key != "procedure"},
        ),
    )
    assert negative["status"] == "incompatible", negative
    assert any(row["property"] == "guarantee-minimum" for row in negative["issues"])


@pytest.mark.parametrize("meaning", ["goal_kind", "workflow_owner"])
@pytest.mark.parametrize("value", ["unsupported", 1, None])
def test_context_vocabulary_cannot_be_author_defined_or_silently_absent(meaning, value):
    document, binding, context = adaptive()
    context[meaning] = value
    result = qualify(document, binding, context=context)
    assert result["status"] == "incompatible"
    assert any(row["property"] == "context-discriminator" for row in result["issues"])


@pytest.mark.parametrize(
    "family,context",
    [
        ("goal", {"goal_kind": "member-task"}),
        ("goal", {"goal_kind": "pre-validation-remediation"}),
        ("goal", {"goal_kind": "epic-closeout"}),
        ("validation", {"workflow_owner": "epic-handler"}),
        ("validation", {"workflow_owner": "epic-validator"}),
    ],
)
def test_supported_family_contexts_have_real_achieved_continuations(family, context):
    document, binding = known(family)
    assert qualify(document, binding, context=context)["status"] == "compatible"


def test_due_success_is_not_established_by_an_impossible_achieved_guard():
    document, binding, context = adaptive()
    item = next(
        item
        for item in document["node_definitions"]["assess"]["items"]
        if item["id"] == "judge-goal-outcome"
    )
    item["choices"].remove("achieved")
    result = qualify(document, binding, context=context)
    assert result["status"] == "incompatible"
    assert any(
        row["property"] == "feasible-achieved-continuation" for row in result["issues"]
    )


@pytest.mark.parametrize("claim", ["evidence", "finalization", "control"])
def test_declared_product_change_dominates_a_custom_effect_claim(claim):
    document, binding, context = adaptive()
    insert_action(document, binding, "goal-route", "polish")
    context["operation_contracts"][
        sha256(canonical_json(document["node_definitions"]["polish"]))
    ] = {
        "roles": ["worker"],
        "effect": claim,
        "basis": "Unsupported attempt to hide a declared product change.",
    }
    result = qualify(document, binding, context=context)
    assert result["status"] == "incompatible"
    assert any(
        row["property"] == "current-final-assessment-and-forward-effects"
        for row in result["issues"]
    )


@pytest.mark.parametrize(
    "claim", ["owned_correction", "user_directions", "relay_outputs"]
)
def test_privileged_custom_labels_need_actual_operation_evidence(claim):
    document, binding, context = adaptive()
    if claim == "user_directions":
        definition = document["node_definitions"]["accept"]
        value = {"approved": "product-correction"}
        role, effect = "orchestrator", "control"
    else:
        definition = document["node_definitions"]["closeout"]
        value = True if claim == "owned_correction" else ["result"]
        role, effect = "orchestrator", "finalization"
    context["operation_contracts"][sha256(canonical_json(definition))] = {
        "roles": [role],
        "effect": effect,
        "basis": "Claim without supporting original evidence.",
        claim: value,
    }
    result = qualify(document, binding, context=context)
    assert result["status"] != "compatible"
    assert any(
        row["property"]
        in {
            "owned-correction-operation",
            "user-direction-operation",
            "faithful-relay-operation",
        }
        for row in result["issues"]
    )


@pytest.mark.parametrize("guarded", [True, False])
def test_custom_continuity_must_not_borrow_completed_operation_implication(guarded):
    document, binding, context = adaptive()
    record = document["node_definitions"]["collect-review"]
    item = next(
        item
        for item in record["items"]
        if item["id"] == "assessment-ordinal-continuity"
    )
    item.update(
        operation_id="repository-positive-ordinal",
        operation_digest=sha256(
            b"Only ordinal positivity; no operation completion guarantee."
        ),
    )
    signature = binding["capability_definitions"]["fixture.review-control/v1"]
    signature["fields"]["assessment-ordinal-continuity"].update(
        operation_id=item["operation_id"], operation_digest=item["operation_digest"]
    )
    if not guarded:
        option = document["node_definitions"]["check-review"]["options"][0]
        option["guards"] = [
            guard
            for guard in option["guards"]
            if guard["evidence"]["item"] != "review-operation"
        ]
    context["operation_contracts"][sha256(canonical_json(record))] = context[
        "operation_contracts"
    ].pop(
        next(
            key
            for key, value in context["operation_contracts"].items()
            if value.get("review_recovery")
        )
    )
    result = qualify(document, binding, context=context)
    assert result["status"] == ("compatible" if guarded else "incompatible")
    if not guarded:
        assert any(
            row["property"] == "selected-review-control" for row in result["issues"]
        )


def test_custom_control_signature_omission_still_consumes_independent_floor_fields():
    document, binding, context = adaptive()
    binding["capability_definitions"]["fixture.review-control/v1"]["fields"].pop(
        "assessment-ordinal-continuity"
    )
    result = qualify(document, binding, context=context)
    assert result["status"] == "compatible", result["issues"]


def test_unrecognized_assessment_guarantee_cannot_hide_a_pass_only_assessor():
    document, binding, context = equivalent_assessment()
    signature = binding["capability_definitions"][
        next(cap["signature"] for cap in binding["nodes"]["assess"]["capabilities"])
    ]
    signature["guarantee"] = "delivery-assessment"
    item = next(
        item
        for item in document["node_definitions"]["assess"]["items"]
        if item["id"] == "judge-applicability"
    )
    item["accepted_outcomes"] = signature["fields"]["judge-applicability"][
        "accepted_outcomes"
    ] = ["pass"]
    result = qualify(document, binding, context=context)
    assert result["status"] == "incompatible"
    assert any(row["property"] == "guarantee-minimum" for row in result["issues"])


def test_task_delegated_option_does_not_establish_final_user_acceptance():
    document, binding, context = adaptive()
    approval = document["node_definitions"]["accept"]
    approval["options"].append(
        {
            "id": "delegated",
            "label": "Delegated",
            "criteria": "Attempt to accept without an actual user decision.",
        }
    )
    placement = next(
        node for node in document["graph"]["nodes"] if node["id"] == "accept"
    )
    placement["routes"]["delegated"] = {"to": "closeout", "effect": "advance"}
    result = qualify(document, binding, context=context)
    assert result["status"] == "incompatible"
    assert any(
        row["property"] == "current-final-acceptance" for row in result["issues"]
    )


@pytest.mark.parametrize("threshold", [10, 113])
@pytest.mark.parametrize("selected", [True, False])
def test_required_when_controller_thresholds_partition_real_conditional_evidence(
    threshold, selected
):
    document, binding, context = adaptive()
    items = document["node_definitions"]["deliver"]["items"]
    items += [
        {
            "id": "count",
            "type": "integer",
            "prompt": "Record actual count",
            "required": True,
            "minimum": threshold - 1,
            "maximum": threshold + 1,
        },
        {
            "id": "detail",
            "type": "text",
            "prompt": "Deliver applicable detail",
            "required": False,
            "min_length": 1,
            "required_when": [{"item": "count", "at_least": threshold}],
        },
    ]
    binding["obligations"]["original-goal"]["producers"].append(
        {"node": "deliver", "item": "detail"}
    )
    if selected:
        next(node for node in document["graph"]["nodes"] if node["id"] == "assess")[
            "evidence_from"
        ][0]["items"].append("detail")
    result = qualify(document, binding, context=context)
    assert result["status"] == ("compatible" if selected else "incompatible")
    if not selected:
        row = next(
            row
            for row in result["issues"]
            if row["property"] == "original-producer-evidence"
        )
        assert any(
            value["field"] == ("deliver", "count") and value["value"] >= threshold
            for value in row["counterexample"]
        )


@pytest.mark.parametrize(
    "capability", ["same-operation-recovery", "review-route-change"]
)
def test_selected_review_missing_internal_or_composed_recovery_is_not_established(
    capability,
):
    document, binding, context = adaptive()
    contract = next(
        value
        for value in context["operation_contracts"].values()
        if value.get("review_recovery")
    )
    contract["review_recovery"].remove(capability)
    result = qualify(document, binding, context=context)
    assert result["status"] == "not-established"
    assert any(
        row["property"] == "selected-review-recovery"
        and row["capability"] == capability
        for row in result["issues"]
    )
    context["review"]["excluded_recovery"] = [capability]
    assert qualify(document, binding, context=context)["status"] == "compatible"


@pytest.mark.parametrize("family", ["task", "goal", "validation", "design", "war-room"])
@pytest.mark.parametrize("mutation", ["goal-tracking", "mapping"])
def test_native_goal_contract_mutations_are_rejected_for_each_family(family, mutation):
    document, binding = known(family)
    if mutation == "goal-tracking":
        document["goal_tracking"] = False
    else:
        binding["goal_assessments"][0]["outcomes"]["achieved"] = "not_achieved"
    result = qualify(document, binding)
    assert result["status"] == "incompatible"
    assert any(row["property"] == "native-goal-mappings" for row in result["issues"])


@pytest.mark.parametrize("item", ["review-operation", "assessment-ordinal-continuity"])
def test_selected_review_guards_are_actual_obligations(item):
    document, binding, context = adaptive()
    record = document["node_definitions"]["collect-review"]
    if item == "review-operation":
        actual = next(
            value
            for value in record["items"]
            if value["id"] == "assessment-ordinal-continuity"
        )
        actual.update(
            operation_id="only-positive-ordinal",
            operation_digest=sha256(b"No completed-operation implication."),
        )
        binding["capability_definitions"]["fixture.review-control/v1"]["fields"][
            "assessment-ordinal-continuity"
        ].update(
            operation_id=actual["operation_id"],
            operation_digest=actual["operation_digest"],
        )
        context["operation_contracts"][sha256(canonical_json(record))] = {
            "roles": ["orchestrator"],
            "effect": "evidence",
            "basis": "Actual local record operation",
            "review_recovery": ["same-operation-recovery", "review-route-change"],
        }
    option = document["node_definitions"]["check-review"]["options"][0]
    option["guards"] = [
        guard for guard in option["guards"] if guard["evidence"]["item"] != item
    ]
    result = qualify(document, binding, context=context)
    assert result["status"] == "incompatible"
    assert any(row["property"] == "selected-review-control" for row in result["issues"])


def test_real_unknown_placement_is_not_an_epistemic_unknown_variable():
    logic = Decisions({("unknown", "actual"): [False, True]})
    bad = logic.predicate(("unknown", "actual"), {"equals": True})
    assert not logic.has_unknown(bad)
    assert logic.certain(bad) == bad
    unresolved = logic.unknown("unsupported-semantics")
    assert logic.has_unknown(unresolved)
    assert logic.certain(logic.any(bad, unresolved)) == bad


def reentry_source(*, renew=False, manual=False):
    document, binding, context = adaptive()
    definitions, placements = document["node_definitions"], document["graph"]["nodes"]

    def option(name, guards=()):
        return {
            "id": name,
            "label": name,
            "criteria": "Use the actual " + name + " direction.",
            **({"guards": list(guards)} if guards else {}),
        }

    def decision(name, options):
        return {
            "type": "decision",
            "title": name,
            "objective": "Preserve current original evidence",
            "prompt": "Which actual direction applies?",
            "options": options,
            "reason": {"required": True, "prompt": "Cite actual evidence"},
        }

    definitions["choose-work"] = decision(
        "Choose optional polish", [option("polish"), option("finish")]
    )
    definitions["polish"] = {
        "type": "action",
        "title": "Polish actual product",
        "intent": "Change approved product content",
        "items": [
            {
                "id": "result",
                "type": "text",
                "prompt": "Record changed product",
                "required": True,
                "min_length": 1,
            }
        ],
    }
    definitions["settle-polish"] = decision(
        "Settle polish",
        [
            option("back"),
            option(
                "stopped",
                [
                    {
                        "evidence": {"node": "assess", "item": "judge-goal-outcome"},
                        "not_equals": "achieved",
                    }
                ],
            ),
        ],
    )
    next(node for node in placements if node["id"] == "assess")["next"] = "choose-work"
    placements += [
        {
            "id": "choose-work",
            "use": "choose-work",
            "evidence_from": [
                {"node": "assess", "items": ["judge-goal-outcome"], "required": True}
            ],
            "routes": {
                "polish": {"to": "polish", "effect": "advance"},
                "finish": {"to": "goal-route", "effect": "advance"},
            },
        },
        {"id": "polish", "use": "polish", "next": "settle-polish"},
        {
            "id": "settle-polish",
            "use": "settle-polish",
            "evidence_from": [
                {"node": "assess", "items": ["judge-goal-outcome"], "required": True},
                {"node": "polish", "items": ["result"], "required": True},
            ],
            "routes": {
                "back": {
                    "to": "deliver" if renew else "choose-work",
                    "effect": "rework",
                },
                "stopped": {"to": "goal-route", "effect": "advance"},
            },
        },
    ]
    for name in ("choose-work", "settle-polish"):
        binding["nodes"][name] = {
            "kind": "decision",
            "role": "orchestrator",
            "effects": [],
            "capabilities": [],
        }
    binding["nodes"]["polish"] = {
        "kind": "action",
        "role": "worker",
        "effects": ["work"],
        "capabilities": [],
    }
    if manual:
        document["manual_rework"]["allowed_targets"].append("choose-work")
    return (
        document,
        bound(
            document,
            {key: value for key, value in binding.items() if key != "procedure"},
        ),
        context,
    )


@pytest.mark.parametrize("renew,manual", [(False, False), (False, True), (True, False)])
def test_native_suffix_reentry_requires_a_renewed_gate_after_product_changes(
    renew, manual
):
    document, binding, context = reentry_source(renew=renew, manual=manual)
    result = qualify(document, binding, context=context)
    assert result["status"] == ("compatible" if renew else "incompatible"), result[
        "issues"
    ]
    if not renew:
        assert any(
            row["property"] == "native-reentry-retained-gate"
            for row in result["issues"]
        )


def correlation_source(width):
    document, binding, context = adaptive()
    original_entry = document["graph"]["entry"]
    names = ["compare-" + sha256(str(index).encode())[7:27] for index in range(width)]
    relay = {
        "type": "action",
        "title": "Retain matching comparison",
        "intent": "Record current paired evidence without product effects.",
        "items": [
            {
                "id": "note",
                "type": "text",
                "prompt": "Record the matching pair",
                "required": True,
                "min_length": 1,
            }
        ],
    }
    document["node_definitions"]["retain-match"] = relay
    context["operation_contracts"][sha256(canonical_json(relay))] = {
        "roles": ["orchestrator"],
        "effect": "evidence",
        "basis": "Harmless paired-evidence note only.",
    }
    for name in ("left", "right"):
        definition = {
            "type": "action",
            "title": "Record " + name + " values",
            "intent": "Record bounded comparison evidence without product writes.",
            "items": [
                {
                    "id": "bit-" + str(index),
                    "type": "choice",
                    "choices": ["zero", "one"],
                    "prompt": "Record actual comparison value",
                    "required": True,
                }
                for index in range(width)
            ],
        }
        document["node_definitions"][name] = definition
        document["graph"]["nodes"].append(
            {"id": name, "use": name, "next": "right" if name == "left" else names[0]}
        )
        binding["nodes"][name] = {
            "kind": "action",
            "role": "orchestrator",
            "effects": [],
            "capabilities": [],
        }
        context["operation_contracts"][sha256(canonical_json(definition))] = {
            "roles": ["orchestrator"],
            "effect": "evidence",
            "basis": "Actual comparison evidence only; no product mutation",
        }
    for index in range(width):
        identifier, item = names[index], "bit-" + str(index)
        options = [
            {
                "id": value,
                "label": value,
                "criteria": "Both actual values are " + value,
                "guards": [
                    {"evidence": {"node": side, "item": item}, "equals": value}
                    for side in ("left", "right")
                ],
            }
            for value in ("zero", "one")
        ]
        options.append(
            {
                "id": "different",
                "label": "Different",
                "criteria": "The actual evidence differs; retrieve current comparison data.",
            }
        )
        document["node_definitions"][identifier] = {
            "type": "decision",
            "title": "Compare actual paired evidence",
            "objective": "Preserve cross-producer correlation",
            "prompt": "Do actual values agree?",
            "options": options,
            "reason": {"required": True, "prompt": "Cite both actual values"},
        }
        target = names[index + 1] if index + 1 < width else original_entry
        document["graph"]["nodes"].append(
            {
                "id": identifier,
                "use": identifier,
                "evidence_from": [
                    {"node": side, "items": [item], "required": True}
                    for side in ("left", "right")
                ],
                "routes": {
                    "zero": {"to": target, "effect": "advance"},
                    "one": {"to": target, "effect": "advance"},
                    "different": {"to": "left", "effect": "rework"},
                },
            }
        )
        placement = document["graph"]["nodes"][-1]
        for value in ("zero", "one"):
            note = "matched-" + sha256((identifier + value).encode())[7:27]
            placement["routes"][value]["to"] = note
            document["graph"]["nodes"].append(
                {"id": note, "use": "retain-match", "next": target}
            )
            binding["nodes"][note] = {
                "kind": "action",
                "role": "orchestrator",
                "effects": [],
                "capabilities": [],
            }
        binding["nodes"][identifier] = {
            "kind": "decision",
            "role": "orchestrator",
            "effects": [],
            "capabilities": [],
        }
    document["graph"]["entry"] = "left"
    return (
        document,
        bound(
            document,
            {key: value for key, value in binding.items() if key != "procedure"},
        ),
        context,
    )


@pytest.mark.parametrize("required", [False, True])
def test_optional_nonaccepted_check_result_is_a_live_product_change_path(required):
    document, binding, context = optional_result_source(required=required)
    result = qualify(document, binding, context=context)
    assert result["status"] == ("compatible" if required else "incompatible"), result[
        "issues"
    ]


def optional_result_source(*, required=False):
    document, binding, context = adaptive()
    definition = {
        "type": "action",
        "title": "Record optional evidence",
        "intent": "Record external evidence without changing product content.",
        "items": [
            {
                "id": "result",
                "type": "check_result",
                "prompt": "Record actual optional result",
                "help": "Record an external optional result; it does not grant any product effect or assessment passage.",
                "required": required,
                "operation_id": "repository-optional-result",
                "operation_digest": sha256(b"Actual optional external result only."),
                "accepted_outcomes": ["pass"],
            }
        ],
    }
    document["node_definitions"]["probe"] = definition
    document["node_definitions"]["inspect-probe"] = {
        "type": "decision",
        "title": "Inspect recorded evidence",
        "objective": "Route from the actual optional result",
        "prompt": "Did the external result pass?",
        "options": [
            {
                "id": "failed",
                "label": "Failed",
                "criteria": "The recorded optional result is not a pass.",
                "guards": [
                    {
                        "evidence": {"node": "probe", "item": "result"},
                        "field": "outcome",
                        "not_equals": "pass",
                    }
                ],
            },
            {
                "id": "continue",
                "label": "Continue",
                "criteria": "Continue with the current unchanged product.",
            },
        ],
        "reason": {"required": True, "prompt": "Cite actual evidence"},
    }
    document["node_definitions"]["polish"] = {
        "type": "action",
        "title": "Change actual product",
        "intent": "Apply a real content change",
        "items": [
            {
                "id": "result",
                "type": "text",
                "prompt": "Record actual change",
                "required": True,
                "min_length": 1,
            }
        ],
    }
    next(node for node in document["graph"]["nodes"] if node["id"] == "assess")[
        "next"
    ] = "probe"
    document["graph"]["nodes"] += [
        {"id": "probe", "use": "probe", "next": "inspect-probe"},
        {
            "id": "inspect-probe",
            "use": "inspect-probe",
            "evidence_from": [{"node": "probe", "items": ["result"], "required": True}],
            "routes": {
                "failed": {"to": "polish", "effect": "advance"},
                "continue": {"to": "goal-route", "effect": "advance"},
            },
        },
        {"id": "polish", "use": "polish", "next": "goal-route"},
    ]
    for name in ("probe", "polish"):
        binding["nodes"][name] = {
            "kind": "action",
            "role": "orchestrator" if name == "probe" else "worker",
            "effects": [] if name == "probe" else ["work"],
            "capabilities": [],
        }
    binding["nodes"]["inspect-probe"] = {
        "kind": "decision",
        "role": "orchestrator",
        "effects": [],
        "capabilities": [],
    }
    context["operation_contracts"][sha256(canonical_json(definition))] = {
        "roles": ["orchestrator"],
        "effect": "evidence",
        "basis": "Explicit recording-only operation with optional nonaccepted results.",
    }
    return (
        document,
        bound(
            document,
            {key: value for key, value in binding.items() if key != "procedure"},
        ),
        context,
    )


def test_correlated_cross_producer_evidence_stays_practical_under_default_budget():
    document, binding, context = correlation_source(14)
    started = time.monotonic()
    result = qualify(document, binding, context=context)
    assert result["status"] == "compatible", result["issues"]
    assert result["analysis"]["symbolic_nodes"] > 100000
    assert time.monotonic() - started < 30


@pytest.mark.parametrize("proven_defect", [False, True])
def test_natural_analysis_exhaustion_retains_current_property_and_proven_defects(
    proven_defect,
):
    document, binding, context = correlation_source(16)
    if proven_defect:
        binding["nodes"]["deliver"]["kind"] = "decision"
    result = qualify(document, binding, context=context)
    assert result["status"] == ("incompatible" if proven_defect else "not-established")
    resource = next(
        row for row in result["issues"] if row["property"] == "analysis-resource"
    )
    assert resource["location"] in binding["nodes"]
    assert resource["during"] == "native-completion-and-path"
    if proven_defect:
        assert any(
            row["property"] == "native-kind" and row["status"] == "incompatible"
            for row in result["issues"]
        )


def test_unknown_possible_effect_does_not_mask_a_separate_proven_product_change():
    document, binding, context = adaptive()
    insert_action(document, binding, "goal-route", "certain-change")
    insert_action(document, binding, "goal-route", "unknown")
    binding["nodes"]["unknown"]["effects"] = []
    result = qualify(document, binding, context=context)
    assert result["status"] == "incompatible"
    assert any(
        row["property"] == "current-final-assessment-and-forward-effects"
        and row["status"] == "incompatible"
        for row in result["issues"]
    )


def test_actual_bootstrap_alias_preserves_closed_provenance_and_qualification():
    from adaptive_definitions import validate_definition
    from adaptive_suitability import add_bootstrap

    document, binding, context = adaptive()
    document, mapping = add_bootstrap(
        document, {key: value for key, value in binding.items() if key != "procedure"}
    )
    document, mapping, _, _ = expand(
        document,
        mapping,
        "n",
        {"suitability-bootstrap": {"suitability-target": "exact-target"}},
    )
    document["id"], document["version"] = "aquarium-adapt-task-bootstrap-alias", "1"
    current = bound(document, mapping)
    validate_definition(current)
    assert qualify(document, current, context=context)["status"] == "compatible"


def test_no_review_or_not_applicable_cannot_waive_due_task_review():
    document, binding, context = adaptive()
    context["review"]["route"] = "not-applicable"
    result = qualify(document, binding, context=context)
    assert result["status"] == "incompatible"
    assert any(row["property"] == "selected-review-route" for row in result["issues"])
    context["review"]["route"] = "herdr"
    binding["nodes"]["collect-review"]["capabilities"] = []
    result = qualify(document, binding, context=context)
    assert result["status"] == "incompatible"
    assert any(row["property"] == "selected-review-control" for row in result["issues"])


def test_achieved_terminal_cannot_bypass_native_session_goal_assessment():
    document, binding, context = adaptive()
    document["node_definitions"]["choose-entry"] = {
        "type": "decision",
        "title": "Choose actual entry",
        "objective": "Preserve native goal ownership",
        "prompt": "Which entry applies?",
        "options": [
            {
                "id": "normal",
                "label": "Normal",
                "criteria": "Perform original work and native goal assessment.",
            },
            {
                "id": "skip",
                "label": "Skip",
                "criteria": "Attempt unsupported direct completion.",
            },
        ],
        "reason": {"required": True, "prompt": "Cite actual goal evidence"},
    }
    document["node_definitions"]["unassessed-terminal"] = copy.deepcopy(
        document["node_definitions"]["closeout"]
    )
    context["operation_contracts"][
        sha256(canonical_json(document["node_definitions"]["unassessed-terminal"]))
    ] = {
        "roles": ["orchestrator"],
        "effect": "finalization",
        "basis": "Result delivery only; no native goal assessment.",
    }
    document["graph"]["nodes"] += [
        {
            "id": "choose-entry",
            "use": "choose-entry",
            "evidence_guidance": ["Use the actual approved original goal."],
            "routes": {
                "normal": {"to": "deliver", "effect": "advance"},
                "skip": {"to": "unassessed-terminal", "effect": "advance"},
            },
        },
        {"id": "unassessed-terminal", "use": "unassessed-terminal", "terminal": True},
    ]
    document["graph"]["entry"] = "choose-entry"
    for name, kind in [("choose-entry", "decision"), ("unassessed-terminal", "action")]:
        binding["nodes"][name] = {
            "kind": kind,
            "role": "orchestrator",
            "effects": [],
            "capabilities": [],
        }
    result = qualify(document, binding, context=context)
    assert result["status"] == "incompatible"
    assert any(
        row["property"] == "native-goal-before-terminal" for row in result["issues"]
    )


def test_materialized_alias_cannot_forge_established_correction_authority():
    document, binding = known("task")
    shared_use = next(
        node["use"] for node in document["graph"]["nodes"] if node["id"] == "closeout"
    )
    document, mapping, _, _ = expand(
        document,
        {key: value for key, value in binding.items() if key != "procedure"},
        "n",
        {
            node["id"]: {"closeout-summary": "result-summary"}
            for node in document["graph"]["nodes"]
            if node["use"] == shared_use
        },
    )
    use = next(
        node["use"] for node in document["graph"]["nodes"] if node["id"] == "n-closeout"
    )
    contract = mapping["semantic_contracts"][
        sha256(canonical_json(document["node_definitions"][use]))
    ]
    contract["owned_correction"] = True
    document["id"], document["version"] = "aquarium-adapt-task-forged-derivation", "1"
    result = qualify(document, bound(document, mapping))
    assert result["status"] == "incompatible"
    assert any(
        row["property"] == "operation-contract-conflict" for row in result["issues"]
    )


def test_unrelated_custom_note_cannot_supply_missing_review_recovery():
    document, binding, context = adaptive()
    record = next(
        value
        for value in context["operation_contracts"].values()
        if value.get("review_recovery")
    )
    record["review_recovery"] = []
    context["operation_contracts"][
        sha256(canonical_json(document["node_definitions"]["closeout"]))
    ]["review_recovery"] = ["same-operation-recovery", "review-route-change"]
    result = qualify(document, binding, context=context)
    assert result["status"] == "not-established"
    assert any(
        row["property"] == "selected-review-recovery" for row in result["issues"]
    )
    assert any(
        row["property"] == "review-recovery-operation" for row in result["issues"]
    )


def test_unrelated_later_final_assessor_does_not_clear_reentry_product_changes():
    document, binding, context = reentry_source()
    document["node_definitions"]["unrelated-assessor"] = copy.deepcopy(
        document["node_definitions"]["assess"]
    )
    placement = next(
        node for node in document["graph"]["nodes"] if node["id"] == "choose-work"
    )
    placement["routes"]["finish"]["to"] = "unrelated-assessor"
    document["graph"]["nodes"].append(
        {
            "id": "unrelated-assessor",
            "use": "unrelated-assessor",
            "next": "goal-route",
            "evidence_from": [
                {
                    "node": "collect-review",
                    "items": ["review-operation"],
                    "required": True,
                }
            ],
        }
    )
    binding["nodes"]["unrelated-assessor"] = copy.deepcopy(binding["nodes"]["assess"])
    result = qualify(document, binding, context=context)
    assert result["status"] == "incompatible"
    assert any(
        row["property"] == "native-reentry-retained-gate" for row in result["issues"]
    )


@pytest.mark.parametrize("value", ["not_achieved", "superseded"])
def test_original_non_success_expectation_retains_its_feasible_native_continuation(
    value,
):
    document, binding, context = adaptive()
    context["expected_outcome"] = value
    result = qualify(document, binding, context=context)
    assert result["status"] == "compatible", result["issues"]


@pytest.mark.parametrize("value", [False, [], "unknown-outcome"])
def test_invalid_original_outcome_context_is_typed_incompatible(value):
    document, binding, context = adaptive()
    context["expected_outcome"] = value
    result = qualify(document, binding, context=context)
    assert result["status"] == "incompatible"
    assert any(row["property"] == "context-goal-outcome" for row in result["issues"])


@pytest.mark.parametrize("before", ["assess", "goal-route"])
def test_unknown_effect_counterexample_remains_json_serializable(before):
    document, binding, context = adaptive()
    insert_action(document, binding, before, "unknown", declared=False)
    result = qualify(document, binding, context=context)
    assert result["status"] == "not-established"
    rendered = json.loads(json.dumps(result))
    assert rendered["status"] == "not-established"
    assert any(row.get("counterexample") for row in rendered["issues"])


def test_explicit_operation_registry_cannot_override_established_work_semantics():
    document, binding = known("task")
    use = next(
        node["use"] for node in document["graph"]["nodes"] if node["id"] == "implement"
    )
    body = document["node_definitions"][use]
    result = qualify(
        document,
        binding,
        operation_contracts={
            sha256(canonical_json(body)): {
                "roles": ["worker"],
                "effect": "evidence",
                "basis": "Attempt to hide actual established product work.",
            }
        },
    )
    assert result["status"] == "incompatible"
    assert any(
        row["property"] == "operation-contract-conflict" for row in result["issues"]
    )


def renewal_scopes_source(*, complete=False, inactive_alternative=False):
    document, binding, context = reentry_source()
    if inactive_alternative:
        # A separate original scope is conditionally due and remains inactive.
        document["node_definitions"]["deliver"]["items"] += [
            {
                "id": "scope",
                "type": "choice",
                "required": True,
                "choices": ["first", "both"],
                "prompt": "Record actual original scope",
            },
            {
                "id": "second",
                "type": "text",
                "required": False,
                "required_when": [{"item": "scope", "equals": "both"}],
                "prompt": "Record due second scope",
                "min_length": 1,
            },
        ]
        choice = next(
            option
            for option in document["node_definitions"]["choose-work"]["options"]
            if option["id"] == "polish"
        )
        choice["guards"] = [
            {"evidence": {"node": "deliver", "item": "scope"}, "equals": "first"}
        ]
        next(
            node for node in document["graph"]["nodes"] if node["id"] == "choose-work"
        )["evidence_from"].append(
            {"node": "deliver", "items": ["scope"], "required": True}
        )
    else:
        document["node_definitions"]["deliver"]["items"].append(
            {
                "id": "second",
                "type": "text",
                "required": True,
                "prompt": "Deliver second original scope",
                "min_length": 1,
            }
        )
    next(node for node in document["graph"]["nodes"] if node["id"] == "assess")[
        "evidence_from"
    ][0]["items"].append("second")
    first = binding["obligations"]["original-goal"]
    first["source"] = "original:first"
    second = copy.deepcopy(first)
    second.update(
        source="original:second", producers=[{"node": "deliver", "item": "second"}]
    )
    binding["obligations"]["second"] = second
    definitions, nodes = document["node_definitions"], document["graph"]["nodes"]
    definitions["refresh-artifacts"] = {
        "type": "action",
        "title": "Deliver current original scopes",
        "intent": "Produce current product evidence",
        "items": [
            {
                "id": "documentation",
                "type": "text",
                "required": True,
                "min_length": 1,
                "prompt": "Deliver current first scope",
            }
        ],
    }
    if complete:
        definitions["refresh-artifacts"]["items"].append(
            {
                "id": "second",
                "type": "text",
                "required": True,
                "min_length": 1,
                "prompt": "Deliver current second scope",
            }
        )
    definitions["renewed-current"] = copy.deepcopy(definitions["assessment-current"])
    definitions["renewed-outcome"] = copy.deepcopy(definitions["goal-route"])
    for key in ("renewed-current", "renewed-outcome"):
        for option in definitions[key]["options"]:
            for guard in option.get("guards", []):
                guard["evidence"]["node"] = "renewed-assessor"
    next(node for node in nodes if node["id"] == "choose-work")["routes"]["finish"][
        "to"
    ] = "refresh-artifacts"
    nodes += [
        {
            "id": "refresh-artifacts",
            "use": "refresh-artifacts",
            "next": "renewed-assessor",
        },
        {
            "id": "renewed-assessor",
            "use": "assess",
            "next": "renewed-outcome",
            "evidence_from": [
                {
                    "node": "refresh-artifacts",
                    "items": [
                        item["id"] for item in definitions["refresh-artifacts"]["items"]
                    ],
                    "required": True,
                },
                {"node": "assess", "items": ["judge-assessment"], "required": True},
            ],
        },
        {
            "id": "renewed-outcome",
            "use": "renewed-outcome",
            "evidence_from": [
                {
                    "node": "renewed-assessor",
                    "items": ["judge-goal-outcome"],
                    "required": True,
                }
            ],
            "routes": {
                "achieved": {"to": "renewed-current", "effect": "advance"},
                "other-outcome": {"to": "refresh-artifacts", "effect": "rework"},
            },
        },
        {
            "id": "renewed-current",
            "use": "renewed-current",
            "evidence_from": [
                {
                    "node": "renewed-assessor",
                    "items": [item["id"] for item in definitions["assess"]["items"]],
                    "required": True,
                }
            ],
            "routes": {
                "current": {"to": "goal-route", "effect": "advance"},
                "not-current": {"to": "refresh-artifacts", "effect": "rework"},
            },
        },
    ]
    binding["nodes"]["refresh-artifacts"] = copy.deepcopy(binding["nodes"]["deliver"])
    binding["nodes"]["renewed-assessor"] = copy.deepcopy(binding["nodes"]["assess"])
    for node in ("renewed-current", "renewed-outcome"):
        binding["nodes"][node] = {
            "kind": "decision",
            "role": "orchestrator",
            "effects": [],
            "capabilities": [],
        }
    for identifier, original in [
        ("first-current", first),
        *([("second-current", second)] if complete else []),
    ]:
        current = copy.deepcopy(original)
        current.update(
            assessor="renewed-assessor",
            decision="renewed-current",
            producers=[
                {
                    "node": "refresh-artifacts",
                    "item": "second"
                    if identifier == "second-current"
                    else "documentation",
                }
            ],
            evidence=[{"node": "renewed-assessor", "item": "judge-applicability"}],
        )
        binding["obligations"][identifier] = current
    return (
        document,
        bound(
            document,
            {key: value for key, value in binding.items() if key != "procedure"},
        ),
        context,
    )


@pytest.mark.parametrize(
    "complete,inactive_alternative", [(False, False), (True, False), (False, True)]
)
def test_reentry_renewal_covers_every_applicable_original_scope(
    complete, inactive_alternative
):
    document, binding, context = renewal_scopes_source(
        complete=complete, inactive_alternative=inactive_alternative
    )
    result = qualify(document, binding, context=context)
    assert result["status"] == (
        "compatible" if complete or inactive_alternative else "incompatible"
    ), result["issues"]
    if not complete and not inactive_alternative:
        assert any(
            row["property"] == "native-reentry-retained-gate"
            for row in result["issues"]
        )
