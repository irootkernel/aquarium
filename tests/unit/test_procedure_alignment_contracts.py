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


def test_task_071_qualification_inventory_keeps_observed_boundaries_explicit() -> None:
    inventory = load_json("review-routing-cases.json")[
        "task_071_qualification_inventory"
    ]

    assert inventory["route_choices"] == [
        "mulgae",
        "orca",
        "native-codex",
        "waived",
    ]
    assert inventory["excluded_route_labels"] == ["independent"]
    assert set(inventory["automated"]) == {
        "route-choice-inventory",
        "completed-route-evidence-cross-product",
        "active-or-unknown-route-change-rejection",
        "incomplete-operation-does-not-consume-ordinal",
        "terminal-incomplete-switch-reuses-pending-ordinal",
        "completed-change-consumes-next-ordinal-with-lineage",
        "mulgae-backend-required",
        "static-route-backend-forbidden",
        "waiver-operation-provenance-summary-required",
        "mulgae-only-hardening-deferral",
    }
    assert set(inventory["master_observed_agent_acceptance"]) == {
        "selected-provider-dispatch",
        "provider-prerequisite-enforcement",
        "provider-side-effect-boundaries",
        "legacy-session-resume-and-switch-behavior",
        "coordinator-waiver-report-language",
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
    assert graph["prepare-review"]["next"] == "validate-review-route-entry"
    assert {
        route["to"] for route in graph["validate-review-route-entry"]["routes"].values()
    } == {"authorize-review-route"}
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
    } == {"confirm-review-provenance"}
    assert graph["confirm-review-provenance"]["routes"] == {
        "delegated": {"to": "confirm-review-findings", "effect": "advance"},
        "waived": {"to": "confirm-review-findings", "effect": "advance"},
    }
    assert {
        route["to"]
        for route in graph["confirm-incomplete-review-evidence"]["routes"].values()
    } == {"confirm-incomplete-review-provenance"}
    assert graph["confirm-incomplete-review-provenance"]["routes"] == {
        "delegated": {
            "to": "record-review-route-direction",
            "effect": "advance",
        }
    }
    assert graph["confirm-assessment-ordinal"]["routes"] == {
        "first": {"to": "confirm-review-evidence", "effect": "advance"},
        "second": {"to": "confirm-review-evidence", "effect": "advance"},
        "third": {"to": "confirm-review-evidence", "effect": "advance"},
        "fourth": {"to": "confirm-review-evidence", "effect": "advance"},
        "authorized-extra": {
            "to": "confirm-extra-assessment-ordinal",
            "effect": "advance",
        },
    }
    assert graph["confirm-extra-assessment-ordinal"]["routes"] == {
        "authorized-extra": {
            "to": "confirm-review-evidence",
            "effect": "advance",
        }
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
    assert task["version"] == "14"

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
    provenance_options = options(task, "review-provenance-decision")
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
        ("review", "review-evidence-reference", None, "non_empty", True),
    } <= normalized_guards(provenance_options["waived"])
    assert {
        (
            "review",
            "assessment-provenance",
            None,
            "not_equals",
            "coordinator-waiver",
        ),
        ("review", "waiver-summary", None, "empty", True),
        ("review", "review-evidence-reference", None, "non_empty", True),
    } <= normalized_guards(provenance_options["delegated"])

    extra_ordinal_options = options(task, "assessment-extra-ordinal-decision")
    assert set(extra_ordinal_options) == {"authorized-extra"}
    assert (
        "review",
        "assessment-ordinal",
        None,
        "at_least",
        5,
    ) in normalized_guards(extra_ordinal_options["authorized-extra"])


def test_review_procedure_decision_options_fit_podway_v0210_guard_limit() -> None:
    for name in (
        "aquarium-task-v2.yaml",
        "aquarium-goal-v2.yaml",
        "aquarium-validation-v2.yaml",
    ):
        procedure = load_procedure(name)
        for definition_id, definition in procedure["node_definitions"].items():
            if definition.get("type") != "decision":
                continue
            for option in definition.get("options", []):
                assert len(option.get("guards", [])) <= 4, (
                    name,
                    definition_id,
                    option["id"],
                )


def test_task_route_fixtures_traverse_only_guarded_options() -> None:
    task = load_procedure("aquarium-task-v2.yaml")
    cases = load_json("review-routing-cases.json")["task_review_route_cases"]
    route_entry_options = options(task, "review-route-entry-decision")
    route_authorization_options = options(task, "review-route-authorization-decision")
    route_binding_options = options(task, "review-route-binding-decision")
    operation_options = options(task, "review-operation-decision")
    ordinal_options = options(task, "assessment-ordinal-decision")
    extra_ordinal_options = options(task, "assessment-extra-ordinal-decision")
    completed_options = options(task, "review-evidence-decision")
    incomplete_options = options(task, "incomplete-review-evidence-decision")
    provenance_options = options(task, "review-provenance-decision")
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
            (
                "record-review-route-direction",
                "route-change-readiness",
            ): case.get("route_change_readiness"),
        }
        with_case = f"case {case['id']}"
        entry_option = (
            "planned"
            if case["route_authorization_basis"] == "approved-plan"
            else "changed-after-completion"
        )
        assert guards_match(route_entry_options[entry_option], values), with_case
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

    delegated_incomplete = {
        ("review", "review-operation"): "incomplete",
        ("review", "review-evidence-reference"): "native:incomplete-operation",
        ("review", "assessment-provenance"): "fresh-reviewer",
        ("review", "waiver-summary"): None,
    }
    delegated_provenance = provenance_options["delegated"]
    assert guards_match(delegated_provenance, delegated_incomplete)

    delegated_failed = dict(delegated_incomplete)
    delegated_failed[("review", "review-operation")] = "failed"
    assert guards_match(delegated_provenance, delegated_failed)

    missing_reference = dict(delegated_incomplete)
    missing_reference[("review", "review-evidence-reference")] = None
    assert not guards_match(delegated_provenance, missing_reference)

    waiver_provenance = dict(delegated_incomplete)
    waiver_provenance[("review", "assessment-provenance")] = "coordinator-waiver"
    assert not guards_match(delegated_provenance, waiver_provenance)

    unexpected_waiver_summary = dict(delegated_incomplete)
    unexpected_waiver_summary[("review", "waiver-summary")] = (
        "waiver evidence is invalid for an incomplete delegated review"
    )
    assert not guards_match(delegated_provenance, unexpected_waiver_summary)

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
        for option_id, option in route_entry_options.items()
        if option_id.startswith("changed-after-")
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

    safe_after_incomplete = {
        ("prepare-review", "route-authorization-basis"): "explicit-route-change",
        (
            "record-review-route-direction",
            "route-change-readiness",
        ): "safe-to-change",
        ("review", "review-operation"): "incomplete",
    }
    assert guards_match(
        route_entry_options["changed-after-incomplete"], safe_after_incomplete
    )
    assert not guards_match(
        route_entry_options["changed-after-failure"], safe_after_incomplete
    )

    safe_after_failure = dict(safe_after_incomplete)
    safe_after_failure[("review", "review-operation")] = "failed"
    assert guards_match(
        route_entry_options["changed-after-failure"], safe_after_failure
    )
    assert not guards_match(
        route_entry_options["changed-after-incomplete"], safe_after_failure
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
    assert guards_match(
        extra_ordinal_options["authorized-extra"],
        {
            ("review", "assessment-ordinal"): 5,
        },
    )
    assert not guards_match(
        extra_ordinal_options["authorized-extra"],
        {
            ("review", "assessment-ordinal"): 4,
        },
    )

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
    assert graph["decide-review-basis"]["routes"]["native-review"] == {
        "to": "confirm-review-route-context",
        "effect": "advance",
    }
    assert graph["confirm-review-route-context"]["routes"] == {
        "ready": {"to": "confirm-review-route-entry", "effect": "advance"},
    }
    assert graph["confirm-review-route-entry"]["routes"] == {
        "planned": {"to": "confirm-review-route-binding", "effect": "advance"},
        "changed": {"to": "confirm-review-route-binding", "effect": "advance"},
    }
    assert set(graph["confirm-review-route-binding"]["routes"]) == {
        "planned-mulgae",
        "planned-orca",
        "planned-native-codex",
        "planned-waiver",
        "changed-mulgae",
        "changed-orca",
        "changed-native-codex",
        "changed-waiver",
    }
    context_sources = {
        source["node"]: set(source["items"])
        for source in graph["confirm-review-route-context"]["evidence_from"]
    }
    assert {"review-target-scope", "review-selection-summary"} <= context_sources[
        "complete-work"
    ]
    entry_sources = {
        source["node"]: set(source["items"])
        for source in graph["confirm-review-route-entry"]["evidence_from"]
    }
    assert {
        "route-authorization-basis",
        "route-change-readiness",
        "prior-route-lifecycle-state",
    } <= entry_sources["record-evidence"]
    assert graph["decide-review-operation"]["routes"] == {
        "completed": {"to": "confirm-assessment-ordinal", "effect": "advance"},
        "waived": {"to": "confirm-assessment-ordinal", "effect": "advance"},
        "incomplete": {
            "to": "confirm-incomplete-route-evidence",
            "effect": "advance",
        },
        "failed": {
            "to": "confirm-incomplete-route-evidence",
            "effect": "advance",
        },
    }
    assert graph["choose-review-route-direction"]["routes"] == {
        "resume-current": {"to": "record-evidence", "effect": "rework"},
        "switch-route": {"to": "complete-work", "effect": "rework"},
        "waive": {"to": "complete-work", "effect": "rework"},
        "stop": {"to": "record-review-route-stop", "effect": "advance"},
    }
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
        "defer": {
            "to": "confirm-hardening-review-eligibility",
            "effect": "advance",
        },
    }
    assert graph["confirm-hardening-review-eligibility"]["routes"] == {
        "eligible": {"to": "confirm-hardening-record", "effect": "advance"},
    }
    assert graph["confirm-hardening-record"]["routes"] == {
        "recorded": {"to": "record-hardening-handoff", "effect": "advance"},
    }
    hardening_items = {
        item["id"]
        for item in goal["node_definitions"]["hardening-deferral-record"]["items"]
    }
    assert {
        "hardening-deferral-run-id",
        "hardening-deferral-finding-ids",
        "hardening-deferral-publication-state",
        "hardening-deferral-findings-query-state",
        "hardening-deferral-native-target-sha256",
        "hardening-deferral-evidence-sha256",
    } <= hardening_items
    defer_guards = normalized_guards(
        options(goal, "hardening-record-decision")["recorded"]
    )
    assert (
        "record-hardening-deferral",
        "hardening-deferral-publication-state",
        None,
        "equals",
        "committed",
    ) in defer_guards
    assert (
        "record-hardening-deferral",
        "hardening-deferral-findings-query-state",
        None,
        "equals",
        "successful",
    ) in defer_guards
    assert (
        "record-hardening-deferral",
        "hardening-deferral-native-target-sha256",
        None,
        "non_empty",
        True,
    ) in defer_guards
    for node_id in (
        "confirm-hardening-record",
        "record-hardening-handoff",
        "assess-goal",
    ):
        hardening_sources = {
            source["node"]: set(source["items"])
            for source in graph[node_id]["evidence_from"]
        }
        assert {
            "hardening-deferral-publication-state",
            "hardening-deferral-findings-query-state",
            "hardening-deferral-native-target-sha256",
        } <= hardening_sources["record-hardening-deferral"]


def test_goal_and_validation_route_fixtures_cover_each_route_and_recovery() -> None:
    fixture = load_json("review-routing-cases.json")
    goal = load_procedure("aquarium-goal-v2.yaml")
    validation = load_procedure("aquarium-validation-v2.yaml")

    goal_cases = fixture["goal_review_route_cases"]
    validation_cases = fixture["validation_review_route_cases"]
    assert {case["route"] for case in goal_cases} == {
        "mulgae",
        "orca",
        "native-codex",
        "waived",
    }
    assert {case["route"] for case in validation_cases} == {
        "mulgae",
        "orca",
        "native-codex",
        "waived",
    }

    goal_choices = {
        "route_authorization_option": set(
            options(goal, "review-route-binding-decision")
        ),
        "operation_option": set(options(goal, "review-operation-decision")),
        "ordinal_option": set(options(goal, "assessment-ordinal-decision")),
    }
    goal_context_options = options(goal, "review-route-context-decision")
    goal_entry_options = options(goal, "review-route-entry-decision")
    goal_provenance_options = options(goal, "review-provenance-decision")
    validation_provenance_options = options(
        validation, "final-review-provenance-decision"
    )
    validation_choices = {
        "operation_option": set(options(validation, "final-review-operation-decision")),
        "ordinal_option": set(options(validation, "assessment-ordinal-decision")),
    }
    for case in goal_cases:
        for field, choices in goal_choices.items():
            if field in case:
                assert case[field] in choices, case["id"]
        values = {
            ("complete-work", "review-route"): case["plan_route"],
            ("complete-work", "review-target-scope"): "isolated exact target",
            ("complete-work", "review-selection-summary"): (
                "approved route, reviewer or waiver authority, prerequisites, and assurance"
            ),
            ("record-evidence", "review-route"): case["route"],
            ("record-evidence", "review-operation"): case["operation"],
            ("record-evidence", "prior-assessment-ordinal"): case["prior_ordinal"],
            ("record-evidence", "assessment-ordinal"): case["ordinal"],
            ("record-evidence", "assessment-ordinal-continuity"): {"outcome": "pass"},
            ("record-evidence", "review-mode"): (
                "remediation-eligible"
                if case["ordinal"] in {None, 1}
                else "hardening-deferral-eligible"
            ),
            ("record-evidence", "backend-check-result"): case["backend_check"],
            ("record-evidence", "review-evidence-reference"): "fixture:evidence",
            ("record-evidence", "assessment-provenance"): case["provenance"],
            ("record-evidence", "waiver-summary"): case.get("waiver_summary"),
            ("record-evidence", "route-authorization-basis"): (
                "explicit-route-change"
                if case["route_authorization_option"].startswith("changed-")
                else "approved-envelope"
            ),
            ("record-evidence", "route-change-authority-reference"): (
                "explicit user direction"
                if case["route_authorization_option"].startswith("changed-")
                else None
            ),
            ("record-evidence", "route-change-readiness"): (
                "safe-to-change" if "direction_option" in case else None
            ),
            ("record-evidence", "prior-route-lifecycle-state"): case.get(
                "prior_lifecycle"
            ),
            ("record-evidence", "route-direction"): case.get("direction_option"),
            ("record-evidence", "finding-lineage-summary"): case.get("finding_lineage"),
            ("record-evidence", "remaining-review-authority-summary"): case.get(
                "remaining_review_authority"
            ),
            ("record-evidence", "corrected-target-summary"): case.get(
                "corrected_target"
            ),
        }
        assert guards_match(goal_context_options["ready"], values), case["id"]
        entry_option = (
            "changed"
            if case["route_authorization_option"].startswith("changed-")
            else "planned"
        )
        assert guards_match(goal_entry_options[entry_option], values), case["id"]
        assert guards_match(
            options(goal, "review-route-binding-decision")[
                case["route_authorization_option"]
            ],
            values,
        ), case["id"]
        assert guards_match(
            options(goal, "review-operation-decision")[case["operation_option"]],
            values,
        ), case["id"]
        if case["ordinal"] is not None:
            assert guards_match(
                options(goal, "assessment-ordinal-decision")[case["ordinal_option"]],
                values,
            ), case["id"]
            assert guards_match(
                options(goal, "route-evidence-decision")[case["evidence_option"]],
                values,
            ), case["id"]
            provenance_option = (
                "waived" if case["operation"] == "waived" else "delegated"
            )
            assert guards_match(goal_provenance_options[provenance_option], values), (
                case["id"]
            )
        else:
            assert guards_match(
                options(goal, "incomplete-route-evidence-decision")[
                    case["evidence_option"]
                ],
                values,
            ), case["id"]
            assert guards_match(
                options(goal, "review-route-settlement-decision")[
                    case["settlement_option"]
                ],
                values,
            ), case["id"]
            assert guards_match(
                options(goal, "review-route-direction-decision")[
                    case["direction_option"]
                ],
                values,
            ), case["id"]
            assert guards_match(goal_provenance_options["delegated"], values), case[
                "id"
            ]
    for case in validation_cases:
        for field, choices in validation_choices.items():
            if field in case:
                assert case[field] in choices, case["id"]
        values = {
            ("final-review", "route-binding-result"): {
                "outcome": case["route_binding"]
            },
            ("final-review", "review-route"): case["route"],
            ("final-review", "review-operation"): case["operation"],
            ("final-review", "prior-assessment-ordinal"): case["prior_ordinal"],
            ("final-review", "assessment-ordinal"): case["ordinal"],
            ("final-review", "assessment-ordinal-continuity"): {"outcome": "pass"},
            ("final-review", "review-mode"): (
                "remediation-eligible"
                if case["ordinal"] in {None, 1}
                else "confirmation-only"
            ),
            ("final-review", "backend-check-result"): case["backend_check"],
            ("final-review", "review-evidence-reference"): "fixture:evidence",
            ("final-review", "assessment-provenance"): case["provenance"],
            ("final-review", "waiver-summary"): case.get("waiver_summary"),
            ("final-review", "route-change-readiness"): (
                "current-route-only"
                if case.get("settlement_option") == "active-current-only"
                else "safe-to-change"
                if case.get("settlement_option")
                in {"not-started-safe", "terminal-safe"}
                else None
            ),
            ("final-review", "prior-route-lifecycle-state"): case.get(
                "prior_lifecycle"
            ),
            ("final-review", "route-direction"): case.get("direction_option"),
            ("final-review", "finding-lineage-summary"): case.get("finding_lineage"),
            ("final-review", "remaining-review-authority-summary"): case.get(
                "remaining_review_authority"
            ),
            ("final-review", "corrected-target-summary"): case.get("corrected_target"),
        }
        assert guards_match(
            options(validation, "final-review-route-binding-decision")["bound"],
            values,
        ), case["id"]
        assert guards_match(
            options(validation, "final-review-operation-decision")[
                case["operation_option"]
            ],
            values,
        ), case["id"]
        if case["ordinal"] is not None:
            assert guards_match(
                options(validation, "assessment-ordinal-decision")[
                    case["ordinal_option"]
                ],
                values,
            ), case["id"]
            assert guards_match(
                options(validation, "final-route-evidence-decision")[
                    case["evidence_option"]
                ],
                values,
            ), case["id"]
            provenance_option = (
                "waived" if case["operation"] == "waived" else "delegated"
            )
            assert guards_match(
                validation_provenance_options[provenance_option], values
            ), case["id"]
        else:
            assert guards_match(
                options(validation, "incomplete-final-route-evidence-decision")[
                    case["evidence_option"]
                ],
                values,
            ), case["id"]
            assert guards_match(
                options(validation, "final-route-settlement-decision")[
                    case["settlement_option"]
                ],
                values,
            ), case["id"]
            assert guards_match(
                options(validation, "final-route-direction-decision")[
                    case["direction_option"]
                ],
                values,
            ), case["id"]
            assert guards_match(validation_provenance_options["delegated"], values), (
                case["id"]
            )

    assert any(case.get("direction_option") == "resume-current" for case in goal_cases)
    assert any(case.get("direction_option") == "switch-route" for case in goal_cases)
    assert any(
        case.get("direction_option") == "resume-current" for case in validation_cases
    )
    assert any(
        case.get("direction_option") == "switch-route" for case in validation_cases
    )
    assert any(case["operation"] == "waived" for case in goal_cases)
    assert any(case["operation"] == "waived" for case in validation_cases)
    completed_switch = next(case for case in goal_cases if case["id"] == "GR-06")
    assert completed_switch["prior_ordinal"] == 1
    assert completed_switch["ordinal"] == 2
    assert completed_switch["finding_lineage"] == ["F-1"]
    assert completed_switch["remaining_review_authority"] == "confirmation only"
    assert completed_switch["corrected_target"] == "commit:corrected-target"
    incomplete_switch = next(case for case in validation_cases if case["id"] == "VR-06")
    assert incomplete_switch["next_route"] == "native-codex"
    assert incomplete_switch["next_prior_ordinal"] == incomplete_switch["prior_ordinal"]
    terminal_switches = (
        next(
            case for case in fixture["task_review_route_cases"] if case["id"] == "TR-05"
        ),
        next(case for case in goal_cases if case["id"] == "GR-07"),
        incomplete_switch,
    )
    assert all(case["ordinal"] is None for case in terminal_switches)
    assert all(
        case["next_prior_ordinal"] == case["prior_ordinal"]
        for case in terminal_switches
    )
    waived_after_finding = next(
        case for case in validation_cases if case["id"] == "VR-07"
    )
    assert waived_after_finding["finding_lineage"] == ["F-1"]
    assert waived_after_finding["remaining_review_authority"] == "confirmation only"
    assert waived_after_finding["corrected_target"] == "commit:corrected-target"

    active_bypass = {
        ("final-review", "prior-route-lifecycle-state"): "active-or-unknown",
        ("final-review", "route-change-readiness"): "safe-to-change",
    }
    validation_settlement = options(validation, "final-route-settlement-decision")
    assert not any(
        guards_match(option, active_bypass)
        for option_id, option in validation_settlement.items()
        if option_id != "active-current-only"
    )
    goal_active_bypass = {
        ("record-evidence", "review-route"): "native-codex",
        ("record-evidence", "route-authorization-basis"): ("explicit-route-change"),
        ("record-evidence", "route-change-authority-reference"): "user direction",
        ("record-evidence", "prior-route-lifecycle-state"): "active-or-unknown",
        ("record-evidence", "route-change-readiness"): "safe-to-change",
    }
    assert not guards_match(
        options(goal, "review-route-entry-decision")["changed"], goal_active_bypass
    )
    goal_settlement = options(goal, "review-route-settlement-decision")
    assert not any(
        guards_match(option, goal_active_bypass)
        for option_id, option in goal_settlement.items()
        if option_id != "active-current-only"
    )
    invalid_binding = {("final-review", "route-binding-result"): {"outcome": "fail"}}
    assert not guards_match(
        options(validation, "final-review-route-binding-decision")["bound"],
        invalid_binding,
    )


def test_managed_review_route_choices_exclude_independent() -> None:
    expected = ["mulgae", "orca", "native-codex", "waived"]
    cases = (
        ("aquarium-task-v2.yaml", "plan-record", "review-route"),
        ("aquarium-task-v2.yaml", "review-record", "review-route"),
        ("aquarium-goal-v2.yaml", "work-record", "review-route"),
        ("aquarium-goal-v2.yaml", "evidence-record", "review-route"),
        ("aquarium-validation-v2.yaml", "final-review-record", "review-route"),
    )
    for name, definition_id, item_id in cases:
        procedure = load_procedure(name)
        item = next(
            item
            for item in procedure["node_definitions"][definition_id]["items"]
            if item["id"] == item_id
        )
        assert item["choices"] == expected
        assert "independent" not in item["choices"]


def test_completed_route_evidence_rejects_cross_product_mismatches() -> None:
    cases = (
        ("aquarium-task-v2.yaml", "review-evidence-decision", "review"),
        ("aquarium-goal-v2.yaml", "route-evidence-decision", "record-evidence"),
        (
            "aquarium-validation-v2.yaml",
            "final-route-evidence-decision",
            "final-review",
        ),
    )
    route_options = {
        "mulgae": "mulgae-pass",
        "orca": "orca",
        "native-codex": "native-codex",
        "waived": "waived",
    }
    for name, definition_id, evidence_node in cases:
        procedure_options = options(load_procedure(name), definition_id)
        provenance_definition = {
            "aquarium-task-v2.yaml": "review-provenance-decision",
            "aquarium-goal-v2.yaml": "review-provenance-decision",
            "aquarium-validation-v2.yaml": "final-review-provenance-decision",
        }[name]
        provenance_options = options(load_procedure(name), provenance_definition)
        for route, option_id in route_options.items():
            with_route = {
                (evidence_node, "review-route"): route,
                (evidence_node, "review-operation"): (
                    "waived" if route == "waived" else "complete"
                ),
                (evidence_node, "backend-check-result"): (
                    "pass" if route == "mulgae" else "not-provided"
                ),
                (evidence_node, "review-evidence-reference"): "fixture:evidence",
                (evidence_node, "assessment-provenance"): (
                    "coordinator-waiver" if route == "waived" else "reviewer"
                ),
                (evidence_node, "waiver-summary"): (
                    "review waived by authority with an assurance limitation"
                    if route == "waived"
                    else None
                ),
            }
            option = procedure_options[option_id]
            assert guards_match(option, with_route), (name, route)

            wrong_route = dict(with_route)
            wrong_route[(evidence_node, "review-route")] = (
                "mulgae" if route == "waived" else "waived"
            )
            assert not guards_match(option, wrong_route), (name, route, "route")

            wrong_operation = dict(with_route)
            wrong_operation[(evidence_node, "review-operation")] = (
                "complete" if route == "waived" else "waived"
            )
            assert not guards_match(option, wrong_operation), (
                name,
                route,
                "operation",
            )

            wrong_backend = dict(with_route)
            wrong_backend[(evidence_node, "backend-check-result")] = (
                "not-provided" if route == "mulgae" else "pass"
            )
            assert not guards_match(option, wrong_backend), (name, route, "backend")

            wrong_provenance = dict(with_route)
            wrong_provenance[(evidence_node, "assessment-provenance")] = (
                "reviewer" if route == "waived" else "coordinator-waiver"
            )
            provenance_option = provenance_options[
                "waived" if route == "waived" else "delegated"
            ]
            assert guards_match(provenance_option, with_route), (name, route)
            assert not guards_match(provenance_option, wrong_provenance), (
                name,
                route,
                "provenance",
            )
            missing_reference = dict(with_route)
            missing_reference[(evidence_node, "review-evidence-reference")] = None
            assert not guards_match(provenance_option, missing_reference), (
                name,
                route,
                "evidence-reference",
            )

            if route == "waived":
                missing_summary = dict(with_route)
                missing_summary[(evidence_node, "waiver-summary")] = None
                assert not guards_match(
                    provenance_options["waived"], missing_summary
                ), (
                    name,
                    route,
                    "summary",
                )


def test_incomplete_route_changes_preserve_the_pending_ordinal() -> None:
    cases = (
        (
            "aquarium-task-v2.yaml",
            "review",
            "review-operation-decision",
            "review-route-settlement-decision",
            "review-route-direction-decision",
            "record-review-route-direction",
        ),
        (
            "aquarium-goal-v2.yaml",
            "record-evidence",
            "review-operation-decision",
            "review-route-settlement-decision",
            "review-route-direction-decision",
            "record-evidence",
        ),
        (
            "aquarium-validation-v2.yaml",
            "final-review",
            "final-review-operation-decision",
            "final-route-settlement-decision",
            "final-route-direction-decision",
            "final-review",
        ),
    )
    for (
        name,
        evidence_node,
        operation_id,
        settlement_id,
        direction_id,
        state_node,
    ) in cases:
        procedure = load_procedure(name)
        incomplete = options(procedure, operation_id)["incomplete"]
        without_ordinal = {
            (evidence_node, "review-route"): "orca",
            (evidence_node, "review-operation"): "incomplete",
            (evidence_node, "assessment-ordinal"): None,
        }
        assert guards_match(incomplete, without_ordinal)
        with_consumed_ordinal = dict(without_ordinal)
        with_consumed_ordinal[(evidence_node, "assessment-ordinal")] = 1
        assert not guards_match(incomplete, with_consumed_ordinal)

        active = {
            (state_node, "prior-route-lifecycle-state"): "active-or-unknown",
            (state_node, "route-change-readiness"): "current-route-only",
            (state_node, "route-direction"): "switch-route",
        }
        settlement = options(procedure, settlement_id)
        assert guards_match(settlement["active-current-only"], active)
        directions = options(procedure, direction_id)
        assert not guards_match(directions["switch-route"], active)
        active_waive = dict(active)
        active_waive[(state_node, "route-direction")] = "waive"
        assert not guards_match(directions["waive"], active_waive)

        terminal = dict(active)
        terminal[(state_node, "prior-route-lifecycle-state")] = (
            "terminal-incomplete-or-failed"
        )
        terminal[(state_node, "route-change-readiness")] = "safe-to-change"
        assert guards_match(settlement["terminal-safe"], terminal)
        assert guards_match(directions["switch-route"], terminal)
        terminal[(state_node, "route-direction")] = "waive"
        assert guards_match(directions["waive"], terminal)
        assert without_ordinal[(evidence_node, "assessment-ordinal")] is None


def test_completed_route_changes_keep_next_ordinal_and_finding_lineage() -> None:
    fixture = load_json("review-routing-cases.json")
    completed_cases = (
        next(
            case for case in fixture["task_review_route_cases"] if case["id"] == "TR-08"
        ),
        next(
            case for case in fixture["goal_review_route_cases"] if case["id"] == "GR-06"
        ),
        next(
            case
            for case in fixture["validation_review_route_cases"]
            if case["id"] == "VR-07"
        ),
    )
    for case in completed_cases:
        assert case["prior_ordinal"] == 1
        assert case["ordinal"] == 2
        assert (case.get("prior_finding_lineage") or case.get("finding_lineage")) == [
            "F-1"
        ]
        assert case["remaining_review_authority"] == "confirmation only"

    lineage_items = {
        "finding-lineage-summary",
        "remaining-review-authority-summary",
        "corrected-target-summary",
    }
    definitions = (
        ("aquarium-task-v2.yaml", "review-checkpoint-record"),
        ("aquarium-goal-v2.yaml", "evidence-record"),
        ("aquarium-validation-v2.yaml", "final-review-record"),
    )
    for name, definition_id in definitions:
        procedure = load_procedure(name)
        actual = {
            item["id"] for item in procedure["node_definitions"][definition_id]["items"]
        }
        assert lineage_items <= actual


def test_hardening_deferral_rejects_every_non_mulgae_route() -> None:
    goal = load_procedure("aquarium-goal-v2.yaml")
    defer = options(goal, "low-handling-decision")["defer"]
    eligibility = options(goal, "hardening-review-eligibility-decision")["eligible"]
    record = options(goal, "hardening-record-decision")["recorded"]
    valid = {
        ("record-hardening-deferral", "hardening-deferral-state"): "recorded",
        ("record-evidence", "review-route"): "mulgae",
        ("record-evidence", "review-operation"): "complete",
        ("record-evidence", "backend-check-result"): "pass",
        ("record-evidence", "review-mode"): "hardening-deferral-eligible",
        ("record-evidence", "assessment-ordinal"): 2,
        (
            "record-hardening-deferral",
            "hardening-deferral-publication-state",
        ): "committed",
        (
            "record-hardening-deferral",
            "hardening-deferral-findings-query-state",
        ): "successful",
        (
            "record-hardening-deferral",
            "hardening-deferral-native-target-sha256",
        ): "sha256:fixture",
    }
    assert guards_match(defer, valid)
    assert guards_match(eligibility, valid)
    assert guards_match(record, valid)
    for route in ("orca", "native-codex", "waived"):
        invalid = dict(valid)
        invalid[("record-evidence", "review-route")] = route
        assert not guards_match(eligibility, invalid), route
    for key in (
        ("record-evidence", "assessment-ordinal"),
        ("record-hardening-deferral", "hardening-deferral-publication-state"),
        ("record-hardening-deferral", "hardening-deferral-findings-query-state"),
        ("record-hardening-deferral", "hardening-deferral-native-target-sha256"),
    ):
        invalid = dict(valid)
        invalid[key] = None
        assert not guards_match(record, invalid), key


def test_goal_and_validation_extra_ordinals_require_the_serial_minimum() -> None:
    cases = (
        ("aquarium-goal-v2.yaml", "record-evidence"),
        ("aquarium-validation-v2.yaml", "final-review"),
    )
    for name, evidence_node in cases:
        procedure = load_procedure(name)
        ordinal = options(procedure, "assessment-ordinal-decision")["authorized-extra"]
        extra = options(procedure, "assessment-extra-ordinal-decision")[
            "authorized-extra"
        ]
        values = {
            (evidence_node, "prior-assessment-ordinal"): 2,
            (evidence_node, "assessment-ordinal"): 3,
            (evidence_node, "review-mode"): (
                "hardening-deferral-eligible"
                if name == "aquarium-goal-v2.yaml"
                else "confirmation-only"
            ),
            (evidence_node, "extra-assessment-authority-reference"): "user authority",
            (evidence_node, "assessment-ordinal-continuity"): {"outcome": "pass"},
        }
        assert guards_match(ordinal, values), name
        assert guards_match(extra, values), name
        below_minimum = dict(values)
        below_minimum[(evidence_node, "assessment-ordinal")] = 2
        assert guards_match(ordinal, below_minimum), name
        assert not guards_match(extra, below_minimum), name


def test_validation_uses_serial_operation_completion_evidence_and_blocker_gates() -> (
    None
):
    procedure = load_procedure("aquarium-validation-v2.yaml")
    graph = nodes(procedure)
    assert graph["final-review"]["next"] == "confirm-final-review-route-binding"
    assert graph["confirm-final-review-route-binding"]["routes"] == {
        "bound": {"to": "decide-final-review-operation", "effect": "advance"},
        "invalid": {"to": "record-incomplete", "effect": "advance"},
    }
    assert graph["decide-final-review-operation"]["routes"] == {
        "completed": {
            "to": "confirm-final-assessment-ordinal",
            "effect": "advance",
        },
        "waived": {
            "to": "confirm-final-assessment-ordinal",
            "effect": "advance",
        },
        "incomplete": {
            "to": "confirm-incomplete-final-route-evidence",
            "effect": "advance",
        },
        "failed": {
            "to": "confirm-incomplete-final-route-evidence",
            "effect": "advance",
        },
    }
    assert graph["confirm-final-assessment-ordinal"]["routes"]["authorized-extra"] == {
        "to": "confirm-extra-final-assessment-ordinal",
        "effect": "advance",
    }
    assert graph["confirm-extra-final-assessment-ordinal"]["routes"] == {
        "authorized-extra": {
            "to": "confirm-final-route-evidence",
            "effect": "advance",
        }
    }
    assert set(graph["confirm-final-review-provenance"]["routes"]) == {
        "delegated",
        "waived",
    }
    assert graph["confirm-incomplete-final-review-provenance"]["routes"] == {
        "delegated": {"to": "confirm-final-route-settlement", "effect": "advance"}
    }
    assert graph["choose-final-route-direction"]["routes"] == {
        "resume-current": {"to": "final-review", "effect": "rework"},
        "switch-route": {"to": "final-review", "effect": "rework"},
        "waive": {"to": "final-review", "effect": "rework"},
        "stop": {"to": "record-stopped", "effect": "advance"},
    }
    assert (
        graph["confirm-final-review-findings"]["routes"]["resolved"]["to"]
        == "decide-final-backend-check"
    )
    assert graph["decide-final-backend-check"]["routes"]["failed"] == {
        "to": "decide-validation-rework-authority",
        "effect": "advance",
    }
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
