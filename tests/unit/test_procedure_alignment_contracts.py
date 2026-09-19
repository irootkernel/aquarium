from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/fixtures"
PROCEDURES = ROOT / "plugins/aquarium/assets/podway/procedures"
CANONICAL_PROCEDURES = ROOT / ".podway/procedures"


def load_json(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def load_procedure(name: str) -> dict:
    return yaml.safe_load((PROCEDURES / name).read_text(encoding="utf-8"))


def test_installed_procedure_sources_match_canonical_copies() -> None:
    asset_names = {path.name for path in PROCEDURES.glob("aquarium-*-v2.yaml")}
    canonical_names = {
        path.name for path in CANONICAL_PROCEDURES.glob("aquarium-*-v2.yaml")
    }

    assert asset_names == canonical_names
    for name in sorted(asset_names):
        assert (PROCEDURES / name).read_bytes() == (
            CANONICAL_PROCEDURES / name
        ).read_bytes()


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
    for guard in option.get("guards", []):
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


def guards_match(option: dict, values: dict[tuple[str, str], object]) -> bool:
    for node, item, field, operator, expected in normalized_guards(option):
        value = values.get((node, item))
        if field is not None and isinstance(value, dict):
            value = value.get(field)
        if operator == "equals" and value != expected:
            return False
        if operator == "not_equals" and value == expected:
            return False
        if operator == "empty" and (value not in {None, "", ()}) == expected:
            return False
        if operator == "non_empty" and (value not in {None, "", ()}) != expected:
            return False
        if operator == "at_least" and (value is None or value < expected):
            return False
        if operator == "at_most" and (value is None or value > expected):
            return False
    return True


def options(procedure: dict, definition_id: str) -> dict[str, dict]:
    return {
        option["id"]: option
        for option in procedure["node_definitions"][definition_id]["options"]
    }


def nodes(procedure: dict) -> dict[str, dict]:
    return {node["id"]: node for node in procedure["graph"]["nodes"]}


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


def test_task_review_route_fixture_covers_required_task_paths() -> None:
    cases = load_json("review-routing-cases.json")["task_review_route_cases"]

    assert [case["id"] for case in cases] == [
        f"TR-{index:02d}" for index in range(1, 9)
    ]
    assert {case["route"] for case in cases} == {
        "mulgae",
        "orca",
        "native-codex",
        "waived",
    }
    assert {
        "completion-gates",
        "blocking-finding-rework",
        "ordinary-low-settlement",
        "unverified-review-evidence",
        "explicit-route-direction",
        "coordinator-completion-gates",
        "prior-blocking-finding-preserved-after-switch",
    } <= {case["expected"] for case in cases}
    assert all(
        case["ordinal"] is None
        for case in cases
        if case["operation"] in {"incomplete", "failed"}
    )


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


def test_completion_status_contract_is_identical_across_workflows() -> None:
    cases = (
        ("aquarium-task-v2.yaml", "review"),
        ("aquarium-goal-v2.yaml", "record-evidence"),
        ("aquarium-validation-v2.yaml", "final-review"),
    )
    for name, evidence_node in cases:
        procedure = load_procedure(name)
        actual = options(procedure, "completion-status-decision")
        assert set(actual) == {"complete", "unmet", "unverified"}
        assert normalized_guards(actual["complete"]) == {
            (evidence_node, "completion-unmet-criteria", None, "equals", 0),
            (evidence_node, "completion-unverified-criteria", None, "equals", 0),
        }
        assert normalized_guards(actual["unmet"]) == {
            (evidence_node, "completion-unmet-criteria", None, "at_least", 1),
            (evidence_node, "completion-unverified-criteria", None, "equals", 0),
        }
        assert normalized_guards(actual["unverified"]) == {
            (evidence_node, "completion-unverified-criteria", None, "at_least", 1),
        }


def test_task_review_uses_serial_ci_completion_finding_and_owner_gates() -> None:
    task = load_procedure("aquarium-task-v2.yaml")
    graph = nodes(task)
    review_items = {
        item["id"] for item in task["node_definitions"]["review-record"]["items"]
    }
    assert "extra-review-authorization" not in review_items
    assert graph["document"]["next"] == "prepare-review"
    assert graph["prepare-review"]["next"] == "authorize-review-route"
    assert graph["review"]["next"] == "confirm-review-route-binding"
    assert set(graph["confirm-review-route-binding"]["routes"]) == {
        "mulgae",
        "orca",
        "native-codex",
        "waived",
    }
    assert graph["decide-review-operation"]["routes"] == {
        "completed": {"to": "confirm-assessment-ordinal", "effect": "advance"},
        "waived": {"to": "confirm-assessment-ordinal", "effect": "advance"},
        "incomplete": {
            "to": "confirm-incomplete-review-evidence",
            "effect": "advance",
        },
        "failed": {
            "to": "confirm-incomplete-review-evidence",
            "effect": "advance",
        },
    }
    assert set(graph["confirm-review-evidence"]["routes"]) == {
        "mulgae-pass",
        "mulgae-fail",
        "orca",
        "native-codex",
        "waived",
    }
    assert {
        route["to"] for route in graph["confirm-review-evidence"]["routes"].values()
    } == {"confirm-review-findings"}
    assert graph["confirm-assessment-ordinal"]["routes"] == {
        option: {"to": "confirm-review-evidence", "effect": "advance"}
        for option in ("first", "second", "third", "fourth", "authorized-extra")
    }
    assert graph["decide-backend-check"]["routes"] == {
        "passed": {"to": "confirm-review-completion", "effect": "advance"},
        "failed": {"to": "decide-task-rework-authority", "effect": "advance"},
        "not-provided": {
            "to": "confirm-review-completion",
            "effect": "advance",
        },
    }
    assert (
        graph["confirm-review-findings"]["routes"]["resolved"]["to"]
        == "decide-backend-check"
    )
    assert graph["confirm-review-completion"]["routes"] == {
        "complete": {"to": "decide-review", "effect": "advance"},
        "unmet": {"to": "decide-task-rework-authority", "effect": "advance"},
        "unverified": {"to": "prepare-review", "effect": "rework"},
    }
    assert graph["decide-review"]["routes"] == {
        "clean": {"to": "assess-goal", "effect": "advance"},
        "blocking": {"to": "decide-task-rework-authority", "effect": "advance"},
        "low-disposition": {"to": "record-low-disposition", "effect": "advance"},
        "inconsistent": {"to": "prepare-review", "effect": "rework"},
    }
    assert graph["decide-task-rework-authority"]["routes"] == {
        "remediation": {"to": "decide-implementation-owner", "effect": "advance"},
        "user-direction": {"to": "await-user-direction", "effect": "advance"},
    }
    authority_options = options(task, "task-rework-authority-decision")
    assert set(authority_options) == {"remediation", "user-direction"}
    assert normalized_guards(authority_options["remediation"]) == {
        ("review", "review-mode", None, "equals", "remediation-eligible")
    }
    assert normalized_guards(authority_options["user-direction"]) == {
        ("review", "review-mode", None, "equals", "confirmation-only")
    }
    assert graph["choose-user-direction"]["routes"] == {
        "fix-and-review": {
            "to": "decide-implementation-owner",
            "effect": "advance",
        },
        "stop": {"to": "assess-goal", "effect": "advance"},
    }
    assert graph["choose-review-route-direction"]["routes"] == {
        "resume-current": {"to": "review", "effect": "rework"},
        "switch-route": {"to": "prepare-review", "effect": "rework"},
        "waive": {"to": "prepare-review", "effect": "rework"},
        "stop": {"to": "record-review-route-stop", "effect": "advance"},
    }
    assert graph["confirm-review-route-settlement"]["routes"] == {
        "not-started-safe": {
            "to": "choose-review-route-direction",
            "effect": "advance",
        },
        "active-current-only": {
            "to": "choose-review-route-direction",
            "effect": "advance",
        },
        "terminal-safe": {
            "to": "choose-review-route-direction",
            "effect": "advance",
        },
    }
    assert graph["record-review-route-stop"]["next"] == "assess-goal"
    assert (
        graph["decide-implementation-owner"]["routes"]["clear"]["to"]
        == "decide-verification-owner"
    )
    assert (
        graph["decide-verification-owner"]["routes"]["clear"]["to"]
        == "decide-documentation-owner"
    )
    assert graph["decide-documentation-owner"]["routes"]["clear"] == {
        "to": "prepare-review",
        "effect": "rework",
    }
    for definition_id, item_id in (
        ("implementation-owner-decision", "implementation-rework-obligations"),
        ("verification-owner-decision", "verification-rework-obligations"),
        ("documentation-owner-decision", "documentation-rework-obligations"),
    ):
        owner_options = options(task, definition_id)
        assert normalized_guards(owner_options["required"]) == {
            ("review", item_id, None, "at_least", 1),
        }
        assert normalized_guards(owner_options["clear"]) == {
            ("review", item_id, None, "equals", 0),
        }

    guarded_items = {
        guard["evidence"]["item"]
        for definition in task["node_definitions"].values()
        for option in definition.get("options", [])
        for guard in option.get("guards", [])
    }
    assert "unresolved-implementation-findings" not in guarded_items
    assert "unresolved-documentation-findings" not in guarded_items
    assert {
        "implementation-rework-obligations",
        "verification-rework-obligations",
        "documentation-rework-obligations",
    } <= guarded_items
    review_options = options(task, "review-decision")
    assert normalized_guards(review_options["inconsistent"]) == {
        ("review", "finding-count-consistency", None, "equals", "inconsistent"),
    }
    for option_id in ("clean", "blocking", "low-disposition"):
        assert (
            "review",
            "finding-count-consistency",
            None,
            "equals",
            "consistent",
        ) in normalized_guards(review_options[option_id])


def test_task_review_route_evidence_combinations_are_guarded() -> None:
    task = load_procedure("aquarium-task-v2.yaml")
    assert task["version"] == "13"

    plan_items = {
        item["id"]: item for item in task["node_definitions"]["plan-record"]["items"]
    }
    checkpoint_items = {
        item["id"]: item
        for item in task["node_definitions"]["review-checkpoint-record"]["items"]
    }
    review_items = {
        item["id"]: item for item in task["node_definitions"]["review-record"]["items"]
    }
    routes = ["mulgae", "orca", "native-codex", "waived"]
    assert plan_items["review-route"]["choices"] == routes
    assert checkpoint_items["effective-review-route"]["choices"] == routes
    assert checkpoint_items["route-authorization-basis"]["choices"] == [
        "approved-plan",
        "explicit-route-change",
        "explicit-waiver",
    ]
    assert all(
        checkpoint_items[item_id]["required"] is True
        for item_id in (
            "finding-lineage-summary",
            "remaining-review-authority-summary",
            "corrected-target-summary",
        )
    )
    assert review_items["review-route"]["choices"] == routes
    assert review_items["review-operation"]["choices"] == [
        "complete",
        "incomplete",
        "failed",
        "waived",
    ]
    assert review_items["backend-check-result"]["choices"] == [
        "pass",
        "fail",
        "not-provided",
    ]
    assert review_items["assessment-ordinal"]["required"] is False
    assert review_items["assessment-ordinal"]["required_when"] == [
        {"item": "review-operation", "not_equals": "incomplete"},
        {"item": "review-operation", "not_equals": "failed"},
    ]
    ordinal_check = review_items["assessment-ordinal-continuity"]
    assert ordinal_check["type"] == "check_result"
    assert ordinal_check["required"] is True
    assert ordinal_check["operation_id"] == "aquarium-task-review-ordinal-continuity"
    assert ordinal_check["operation_digest"] == (
        "sha256:1deb80ea497dac646d84cdb76b7f23a72c1700fbb47c2cc05a1166ba5ec5ca5a"
    )
    assert ordinal_check["accepted_outcomes"] == ["pass", "fail", "inconclusive"]

    operation_options = options(task, "review-operation-decision")
    for option_id in ("incomplete", "failed"):
        assert (
            "review",
            "assessment-ordinal",
            None,
            "empty",
            True,
        ) in normalized_guards(operation_options[option_id])

    evidence_options = options(task, "review-evidence-decision")
    assert set(evidence_options) == {
        "mulgae-pass",
        "mulgae-fail",
        "orca",
        "native-codex",
        "waived",
    }
    assert (
        "review",
        "backend-check-result",
        None,
        "equals",
        "not-provided",
    ) not in normalized_guards(evidence_options["mulgae-pass"])
    assert (
        "review",
        "backend-check-result",
        None,
        "equals",
        "not-provided",
    ) in normalized_guards(evidence_options["orca"])
    assert (
        "review",
        "backend-check-result",
        None,
        "equals",
        "not-provided",
    ) in normalized_guards(evidence_options["native-codex"])
    assert {
        ("review", "review-operation", None, "equals", "waived"),
        (
            "review",
            "assessment-provenance",
            None,
            "equals",
            "coordinator-waiver",
        ),
        ("review", "waiver-summary", None, "non_empty", True),
    } <= normalized_guards(evidence_options["waived"])


def test_task_route_fixtures_traverse_only_guarded_options() -> None:
    task = load_procedure("aquarium-task-v2.yaml")
    cases = load_json("review-routing-cases.json")["task_review_route_cases"]
    route_authorization_options = options(task, "review-route-authorization-decision")
    route_binding_options = options(task, "review-route-binding-decision")
    operation_options = options(task, "review-operation-decision")
    ordinal_options = options(task, "assessment-ordinal-decision")
    completed_options = options(task, "review-evidence-decision")
    incomplete_options = options(task, "incomplete-review-evidence-decision")
    settlement_options = options(task, "review-route-settlement-decision")
    recovery_options = options(task, "review-route-direction-decision")

    for case in cases:
        values = {
            ("record-plan", "review-route"): case["plan_route"],
            ("prepare-review", "effective-review-route"): case["route"],
            (
                "prepare-review",
                "route-authorization-basis",
            ): case["route_authorization_basis"],
            (
                "prepare-review",
                "route-change-authority-reference",
            ): case.get("route_change_authority_reference"),
            (
                "prepare-review",
                "prior-assessment-ordinal",
            ): case["prior_ordinal"],
            ("review", "review-route"): case["route"],
            ("review", "review-operation"): case["operation"],
            ("review", "assessment-ordinal"): case["ordinal"],
            ("review", "assessment-ordinal-continuity"): {"outcome": "pass"},
            ("review", "review-mode"): (
                "remediation-eligible"
                if case["ordinal"] is None or case["ordinal"] <= 3
                else "confirmation-only"
            ),
            ("review", "review-evidence-reference"): f"evidence:{case['id']}",
            ("review", "backend-check-result"): case["backend_check"],
            ("review", "assessment-provenance"): case["provenance"],
            ("review", "waiver-summary"): case["waiver_summary"],
        }
        with_case = f"case {case['id']}"
        assert guards_match(
            route_authorization_options[case["route_authorization_option"]], values
        ), with_case
        assert guards_match(route_binding_options[case["route"]], values), with_case
        assert guards_match(operation_options[case["operation_option"]], values), (
            with_case
        )
        if "ordinal_option" in case:
            assert guards_match(ordinal_options[case["ordinal_option"]], values), (
                with_case
            )
        route_options = (
            completed_options
            if case["operation"] in {"complete", "waived"}
            else incomplete_options
        )
        assert guards_match(route_options[case["evidence_option"]], values), with_case

        if "settlement_option" in case:
            values.update(
                {
                    (
                        "record-review-route-direction",
                        "prior-route-lifecycle-state",
                    ): case["prior_state"],
                    (
                        "record-review-route-direction",
                        "route-change-readiness",
                    ): case["route_change_readiness"],
                }
            )
            assert guards_match(
                settlement_options[case["settlement_option"]], values
            ), with_case
            assert guards_match(recovery_options[case["recovery_option"]], values), (
                with_case
            )

    invalid_static = {
        ("review", "review-route"): "orca",
        ("review", "backend-check-result"): "pass",
        ("review", "review-evidence-reference"): "orca:delivery",
        ("review", "assessment-provenance"): "coordinator-waiver",
        ("review", "waiver-summary"): None,
    }
    assert not any(
        guards_match(option, invalid_static) for option in incomplete_options.values()
    )

    unauthorized_initial_switch = {
        ("record-plan", "review-route"): "mulgae",
        ("prepare-review", "effective-review-route"): "orca",
        ("prepare-review", "route-authorization-basis"): "approved-plan",
        ("prepare-review", "route-change-authority-reference"): None,
    }
    assert not any(
        guards_match(option, unauthorized_initial_switch)
        for option in route_authorization_options.values()
    )

    active = {
        (
            "record-review-route-direction",
            "prior-route-lifecycle-state",
        ): "active-or-unknown",
        (
            "record-review-route-direction",
            "route-change-readiness",
        ): "current-route-only",
    }
    assert guards_match(settlement_options["active-current-only"], active)
    assert not guards_match(recovery_options["switch-route"], active)
    assert not guards_match(recovery_options["waive"], active)
    assert guards_match(recovery_options["resume-current"], active)
    assert guards_match(recovery_options["stop"], active)

    active_bypass = {
        **active,
        ("record-plan", "review-route"): "mulgae",
        ("prepare-review", "effective-review-route"): "orca",
        ("prepare-review", "route-authorization-basis"): "explicit-route-change",
        ("prepare-review", "route-change-authority-reference"): "attempted bypass",
        ("prepare-review", "prior-assessment-ordinal"): 0,
        ("review", "review-operation"): "incomplete",
        ("review", "review-route"): "mulgae",
    }
    assert nodes(task)["choose-review-route-direction"]["routes"]["resume-current"] == {
        "to": "review",
        "effect": "rework",
    }
    assert not any(
        guards_match(option, active_bypass)
        for option_id, option in route_authorization_options.items()
        if option_id.startswith(("changed-", "completed-change-"))
    )
    assert not guards_match(route_binding_options["orca"], active_bypass)

    safe_switch = {
        ("prepare-review", "effective-review-route"): "native-codex",
        ("prepare-review", "route-authorization-basis"): "explicit-route-change",
        ("prepare-review", "route-change-authority-reference"): "user switch",
        (
            "record-review-route-direction",
            "route-change-readiness",
        ): "safe-to-change",
    }
    assert guards_match(
        route_authorization_options["changed-native-codex"], safe_switch
    )

    first_with_confirmation_mode = {
        ("prepare-review", "prior-assessment-ordinal"): 0,
        ("review", "assessment-ordinal"): 1,
        ("review", "review-mode"): "confirmation-only",
        ("review", "assessment-ordinal-continuity"): {"outcome": "pass"},
    }
    assert not guards_match(ordinal_options["first"], first_with_confirmation_mode)

    unverified_extra_jump = {
        ("prepare-review", "prior-assessment-ordinal"): 4,
        ("prepare-review", "extra-assessment-authority-reference"): "user authority",
        ("review", "assessment-ordinal"): 99,
        ("review", "review-mode"): "confirmation-only",
        ("review", "assessment-ordinal-continuity"): {"outcome": "fail"},
    }
    assert not guards_match(ordinal_options["authorized-extra"], unverified_extra_jump)

    achieved = options(task, "goal-assessment")["achieved"]
    assert not guards_match(
        achieved,
        {
            (
                "record-review-route-stop",
                "route-stop-classification",
            ): "stopped-unsuccessfully"
        },
    )

    switched = next(case for case in cases if case["id"] == "TR-08")
    assert switched["ordinal"] == 2
    assert switched["prior_finding_lineage"] == ["F-1"]
    assert switched["remaining_review_authority"] == "confirmation only"
    assert switched["corrected_target_assessment"] is True
    assert nodes(task)["choose-review-route-direction"]["routes"]["switch-route"] == {
        "to": "prepare-review",
        "effect": "rework",
    }
    assert "prepare-review" in task["manual_rework"]["allowed_targets"]


def test_goal_routes_completion_findings_authority_and_low_handling_serially() -> None:
    goal = load_procedure("aquarium-goal-v2.yaml")
    graph = nodes(goal)
    record_items = {
        item["id"] for item in goal["node_definitions"]["evidence-record"]["items"]
    }
    assert "current-rework-obligations" not in record_items
    assert "extra-review-authorization" not in record_items
    assert "authorized-rework-decision" not in goal["node_definitions"]
    assert graph["confirm-completion-assessment"]["routes"] == {
        "complete": {"to": "decide-evidence", "effect": "advance"},
        "unmet": {"to": "decide-goal-rework-authority", "effect": "advance"},
        "unverified": {"to": "record-evidence", "effect": "rework"},
    }
    assert graph["decide-evidence"]["routes"] == {
        "clean": {"to": "assess-goal", "effect": "advance"},
        "blocking": {"to": "decide-goal-rework-authority", "effect": "advance"},
        "low-only": {"to": "record-hardening-deferral", "effect": "advance"},
        "inconsistent": {"to": "record-evidence", "effect": "rework"},
    }
    assert graph["decide-goal-rework-authority"]["routes"] == {
        "remediation": {"to": "complete-work", "effect": "rework"},
        "user-direction": {"to": "await-user-direction", "effect": "advance"},
    }
    authority_options = options(goal, "goal-rework-authority-decision")
    assert set(authority_options) == {"remediation", "user-direction"}
    assert normalized_guards(authority_options["remediation"]) == {
        (
            "record-evidence",
            "review-mode",
            None,
            "equals",
            "remediation-eligible",
        )
    }
    assert normalized_guards(authority_options["user-direction"]) == {
        (
            "record-evidence",
            "review-mode",
            None,
            "not_equals",
            "remediation-eligible",
        )
    }
    goal_options = options(goal, "evidence-decision")
    assert normalized_guards(goal_options["inconsistent"]) == {
        (
            "record-evidence",
            "finding-count-consistency",
            None,
            "equals",
            "inconsistent",
        ),
    }
    for option_id in ("clean", "blocking", "low-only"):
        assert (
            "record-evidence",
            "finding-count-consistency",
            None,
            "equals",
            "consistent",
        ) in normalized_guards(goal_options[option_id])
    assert graph["record-hardening-deferral"]["next"] == "decide-low-handling"
    assert graph["decide-low-handling"]["routes"] == {
        "settle": {"to": "record-low-disposition", "effect": "advance"},
        "defer": {"to": "record-hardening-handoff", "effect": "advance"},
    }


def test_validation_uses_serial_operation_completion_evidence_and_blocker_gates() -> (
    None
):
    procedure = load_procedure("aquarium-validation-v2.yaml")
    graph = nodes(procedure)
    assert graph["final-review"]["next"] == "decide-final-review-operation"
    assert graph["decide-final-review-operation"]["routes"] == {
        "passed": {"to": "confirm-final-review-findings", "effect": "advance"},
        "incomplete": {"to": "record-review-operation-incomplete", "effect": "advance"},
    }
    assert (
        graph["confirm-final-review-findings"]["routes"]["resolved"]["to"]
        == "confirm-completion-assessment"
    )
    assert graph["confirm-completion-assessment"]["routes"] == {
        "complete": {"to": "decide-required-evidence", "effect": "advance"},
        "unmet": {"to": "decide-validation-rework-authority", "effect": "advance"},
        "unverified": {"to": "record-incomplete", "effect": "advance"},
    }
    assert graph["decide-required-evidence"]["routes"] == {
        "complete": {"to": "decide-current-blockers", "effect": "advance"},
        "incomplete": {"to": "record-incomplete", "effect": "advance"},
    }
    assert graph["decide-current-blockers"]["routes"] == {
        "clear": {"to": "decide-final-review", "effect": "advance"},
        "blocking": {"to": "decide-validation-rework-authority", "effect": "advance"},
    }
    assert graph["decide-validation-rework-authority"]["routes"] == {
        "remediation": {"to": "audit", "effect": "rework"},
        "user-direction": {"to": "await-user-direction", "effect": "advance"},
    }
    final_options = options(procedure, "final-review-decision")
    assert normalized_guards(final_options["validated"]) == {
        ("final-review", "pending-applicable-low-dispositions", None, "equals", 0)
    }
    assert normalized_guards(final_options["low-disposition"]) == {
        ("final-review", "pending-applicable-low-dispositions", None, "at_least", 1)
    }


def test_low_settlement_records_and_guards_carried_completion_state() -> None:
    for name in (
        "aquarium-task-v2.yaml",
        "aquarium-goal-v2.yaml",
        "aquarium-validation-v2.yaml",
    ):
        procedure = load_procedure(name)
        low_items = {
            item["id"]: item
            for item in procedure["node_definitions"]["low-disposition-record"]["items"]
        }
        assert {
            "completion-assessment-summary",
            "completion-unmet-criteria",
            "completion-unverified-criteria",
        } <= low_items.keys()
        completed = options(procedure, "low-completion-decision")["completed"]
        assert normalized_guards(completed) == {
            ("record-low-disposition", "pending-low-dispositions", None, "equals", 0),
            ("record-low-disposition", "current-blocking-findings", None, "equals", 0),
            ("record-low-disposition", "completion-unmet-criteria", None, "equals", 0),
            (
                "record-low-disposition",
                "completion-unverified-criteria",
                None,
                "equals",
                0,
            ),
        }
        selected = {
            item
            for source in nodes(procedure)["decide-low-completion"]["evidence_from"]
            if source["node"] == "record-low-disposition"
            for item in source.get("items", [])
        }
        assert {
            "completion-assessment-summary",
            "completion-unmet-criteria",
            "completion-unverified-criteria",
        } <= selected


def test_user_direction_record_completes_before_the_unset_choice_node() -> None:
    for name in (
        "aquarium-task-v2.yaml",
        "aquarium-goal-v2.yaml",
        "aquarium-validation-v2.yaml",
    ):
        procedure = load_procedure(name)
        nodes = {node["id"]: node for node in procedure["graph"]["nodes"]}

        assert nodes["await-user-direction"]["next"] == "choose-user-direction"
        assert nodes["choose-user-direction"]["use"].endswith("direction-decision")
        instructions = procedure["node_definitions"][
            nodes["await-user-direction"]["use"]
        ]["instructions"]
        assert isinstance(instructions, list) and instructions


def test_stop_paths_preserve_completion_and_direction_for_goal_assessment() -> None:
    cases = (
        ("aquarium-task-v2.yaml", "review", True),
        ("aquarium-goal-v2.yaml", "record-evidence", True),
        ("aquarium-validation-v2.yaml", "final-review", False),
    )
    completion_items = {
        "completion-assessment-summary",
        "completion-unmet-criteria",
        "completion-unverified-criteria",
    }
    for name, completion_node, has_count_consistency in cases:
        procedure = load_procedure(name)
        graph = nodes(procedure)
        assessment_sources = graph["assess-goal"]["evidence_from"]
        selected_completion = {
            item
            for source in assessment_sources
            if source["node"] == completion_node
            for item in source.get("items", [])
        }
        selected_direction = {
            item
            for source in assessment_sources
            if source["node"] == "await-user-direction"
            for item in source.get("items", [])
        }

        assert completion_items <= selected_completion
        assert ("finding-count-consistency" in selected_completion) is (
            has_count_consistency
        )
        assert {"direction-classification", "direction-summary"} <= (selected_direction)

        wait_sources = graph["await-user-direction"]["evidence_from"]
        wait_completion = {
            item
            for source in wait_sources
            if source["node"] == completion_node
            for item in source.get("items", [])
        }
        assert completion_items <= wait_completion


def test_review_evidence_uses_one_source_entry_and_only_needed_items() -> None:
    cases = (
        ("aquarium-task-v2.yaml", "decide-review", "review"),
        ("aquarium-validation-v2.yaml", "decide-final-review", "final-review"),
    )
    for name, node_id, source_id in cases:
        procedure = load_procedure(name)
        sources = [
            source
            for source in nodes(procedure)[node_id]["evidence_from"]
            if source["node"] == source_id
        ]
        assert len(sources) == 1

    validation = load_procedure("aquarium-validation-v2.yaml")
    completion_sources = nodes(validation)["confirm-completion-assessment"][
        "evidence_from"
    ]
    selected = {
        item for source in completion_sources for item in source.get("items", [])
    }
    assert "review-mode" not in selected


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
