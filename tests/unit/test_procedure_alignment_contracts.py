from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/fixtures"
PROCEDURES = ROOT / "plugins/aquarium/assets/podway/procedures"


def load_json(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def load_procedure(name: str) -> dict:
    return yaml.safe_load((PROCEDURES / name).read_text(encoding="utf-8"))


PREDICATE_OPERATORS = (
    "equals",
    "not_equals",
    "empty",
    "non_empty",
    "at_least",
    "at_most",
)


def normalized_guards(option: dict) -> set[tuple[str, str, str | None, str, object]]:
    result = set()
    for guard in option["guards"]:
        operators = [name for name in PREDICATE_OPERATORS if name in guard]
        assert len(operators) == 1
        operator = operators[0]
        evidence = guard["evidence"]
        result.add(
            (
                evidence["node"],
                evidence["item"],
                guard.get("field"),
                operator,
                guard[operator],
            )
        )
    return result


def assert_validation_final_review_contract(procedure: dict) -> None:
    definitions = procedure["node_definitions"]
    graph_nodes = {node["id"]: node for node in procedure["graph"]["nodes"]}
    decision = graph_nodes["decide-final-review"]
    options = {
        option["id"]: option for option in definitions[decision["use"]]["options"]
    }

    assert normalized_guards(options["validated"]) == {
        ("final-review", "final-review-result", "outcome", "equals", "pass"),
        (
            "final-review",
            "pending-applicable-low-dispositions",
            None,
            "equals",
            0,
        ),
        ("final-review", "current-applicable-blockers", None, "equals", 0),
        ("final-review", "required-evidence-gaps", None, "equals", 0),
    }
    assert normalized_guards(options["low-disposition"]) == {
        ("final-review", "final-review-result", "outcome", "equals", "pass"),
        (
            "final-review",
            "pending-applicable-low-dispositions",
            None,
            "at_least",
            1,
        ),
        ("final-review", "current-applicable-blockers", None, "equals", 0),
        ("final-review", "required-evidence-gaps", None, "equals", 0),
    }
    assert normalized_guards(options["incomplete"]) == {
        ("final-review", "final-review-result", "outcome", "equals", "pass"),
        ("final-review", "required-evidence-gaps", None, "at_least", 1),
    }
    assert normalized_guards(options["review-operation-incomplete"]) == {
        (
            "final-review",
            "final-review-result",
            "outcome",
            "not_equals",
            "pass",
        ),
    }

    assert decision["routes"]["validated"] == {
        "to": "assess-goal",
        "effect": "advance",
    }
    assert decision["routes"]["low-disposition"] == {
        "to": "record-low-disposition",
        "effect": "advance",
    }
    assert decision["routes"]["incomplete"] == {
        "to": "record-incomplete",
        "effect": "advance",
    }
    assert decision["routes"]["review-operation-incomplete"] == {
        "to": "record-review-operation-incomplete",
        "effect": "advance",
    }
    selected = {
        (source["node"], item)
        for source in decision["evidence_from"]
        for item in source.get("items", [])
    }
    assert {
        ("final-review", "final-review-result"),
        ("final-review", "pending-applicable-low-dispositions"),
        ("final-review", "current-applicable-blockers"),
        ("final-review", "required-evidence-gaps"),
    } <= selected


def test_selected_shared_operation_descriptors_match_declared_slots() -> None:
    fixture = load_json("procedure-operation-contracts.json")
    expected = {}
    for operation in fixture["operations"]:
        digest = (
            "sha256:"
            + hashlib.sha256(operation["descriptor"].encode("utf-8")).hexdigest()
        )
        assert digest == operation["operation_digest"]
        expected[operation["operation_id"]] = operation["operation_digest"]

    observed: dict[str, set[str]] = {}
    for path in sorted(PROCEDURES.glob("aquarium-*-v2.yaml")):
        procedure = yaml.safe_load(path.read_text(encoding="utf-8"))
        for definition in procedure["node_definitions"].values():
            for item in definition.get("items", []):
                if item.get("type") != "check_result":
                    continue
                operation_id = item["operation_id"]
                if operation_id in expected:
                    observed.setdefault(operation_id, set()).add(
                        item["operation_digest"]
                    )

    assert observed == {
        operation_id: {operation_digest}
        for operation_id, operation_digest in expected.items()
    }


def test_review_routing_fixture_inventory_preserves_low_only_review_bounds() -> None:
    fixture = load_json("review-routing-cases.json")
    cases = fixture["cases"]

    assert [case["id"] for case in cases] == [
        f"RR-{index:03d}" for index in range(1, 41)
    ]
    assert all(case["expected"]["logical_route"] for case in cases)
    assert all(case["expected"]["required_assertions"] for case in cases)
    low_cases = [
        case for case in cases if (case["input"].get("source_low_count") or 0) > 0
    ]
    assert low_cases
    assert any(case["input"].get("pending_low_dispositions") == 0 for case in low_cases)
    settled_low_only_cases = [
        case
        for case in low_cases
        if case["input"].get("pending_low_dispositions") == 0
        and case["input"].get("blocking_findings") == 0
        and case["input"].get("confirmation_needed") == 0
        and case["input"].get("native_review") == "complete"
    ]
    assert settled_low_only_cases
    assert all(
        case["expected"]["additional_automatic_provider_roots_in_this_scope"] == 0
        for case in settled_low_only_cases
    )


def test_correction_matrix_has_complete_inventory_metadata() -> None:
    fixture = load_json("review-routing-cases.json")
    matrix = fixture["correction_acceptance_matrix"]

    assert [case["id"] for case in matrix] == [
        f"C-{index:02d}" for index in range(1, 17)
    ]
    assert all(case["evidence_class"] for case in matrix)
    assert all(case["runner"] for case in matrix)
    assert all(
        case["implementation_status"] in {"implemented", "specified"} for case in matrix
    )
    assert {case["execution_status"] for case in matrix} == {
        "not-recorded-by-this-fixture"
    }


def test_low_completion_routes_to_goal_assessment_without_a_review_loop() -> None:
    for name in (
        "aquarium-task-v2.yaml",
        "aquarium-goal-v2.yaml",
        "aquarium-validation-v2.yaml",
    ):
        procedure = load_procedure(name)
        nodes = {node["id"]: node for node in procedure["graph"]["nodes"]}

        assert nodes["decide-low-result"]["routes"]["passed"]["to"] == (
            "decide-low-completion"
        )
        assert nodes["decide-low-completion"]["routes"]["completed"] == {
            "to": "assess-goal",
            "effect": "advance",
        }


def test_validation_final_review_routes_from_composed_applicable_obligations() -> None:
    procedure = load_procedure("aquarium-validation-v2.yaml")
    definitions = procedure["node_definitions"]
    items = {item["id"] for item in definitions["final-review-record"]["items"]}
    required = {
        "applicable-obligation-summary",
        "pending-applicable-low-dispositions",
        "current-applicable-blockers",
        "required-evidence-gaps",
    }
    assert required <= items

    assert_validation_final_review_contract(procedure)


def test_validation_final_review_contract_rejects_wrong_pending_operand() -> None:
    procedure = load_procedure("aquarium-validation-v2.yaml")
    mutated = copy.deepcopy(procedure)
    options = mutated["node_definitions"]["final-review-decision"]["options"]
    validated = next(option for option in options if option["id"] == "validated")
    pending = next(
        guard
        for guard in validated["guards"]
        if guard["evidence"]["item"] == "pending-applicable-low-dispositions"
    )
    pending["equals"] = 1

    try:
        assert_validation_final_review_contract(mutated)
    except AssertionError:
        pass
    else:
        raise AssertionError("wrong pending-disposition operand was not detected")


def test_user_direction_record_completes_before_the_unset_choice_node() -> None:
    for name in ("aquarium-goal-v2.yaml", "aquarium-validation-v2.yaml"):
        procedure = load_procedure(name)
        nodes = {node["id"]: node for node in procedure["graph"]["nodes"]}

        assert nodes["await-user-direction"]["next"] == "choose-user-direction"
        assert nodes["choose-user-direction"]["use"].endswith("direction-decision")
        instructions = procedure["node_definitions"][
            nodes["await-user-direction"]["use"]
        ]["instructions"]
        assert isinstance(instructions, list) and instructions


def test_goal_kind_contract_keeps_closeout_substitute_narrow() -> None:
    procedure = load_procedure("aquarium-goal-v2.yaml")
    items = {
        item["id"]: item
        for item in procedure["node_definitions"]["evidence-record"]["items"]
    }
    options = {
        option["id"]: option
        for option in procedure["node_definitions"]["review-basis-decision"]["options"]
    }

    assert items["goal-kind"]["choices"] == [
        "member-task",
        "pre-validation-remediation",
        "epic-closeout",
    ]
    assert any(
        guard["evidence"]["item"] == "goal-kind"
        and guard.get("equals") == "epic-closeout"
        for guard in options["final-closeout"]["guards"]
    )
