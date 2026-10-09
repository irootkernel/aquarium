from __future__ import annotations

import hashlib
import json
from itertools import pairwise
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/fixtures"
PROCEDURES = ROOT / "plugins/aquarium/assets/podway/procedures"


def load_json(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def load_procedure(name: str) -> dict:
    return yaml.safe_load((PROCEDURES / name).read_text(encoding="utf-8"))


def test_current_and_prior_procedure_identities_are_exact() -> None:
    identities = (
        (
            "aquarium-task-v2.yaml",
            "25",
            "9034dc4a36ce991cc75ee5b4f8f1a15f21649e435651621acc5463ad8a9b0efc",
            "aquarium-task-v24.yaml",
            "44992bc7e1efc048b2041e448bcdbc3dcedb3d1f70815b1ac379404a6c830e39",
        ),
        (
            "aquarium-goal-v2.yaml",
            "28",
            "f4ad2b0e66be4f141c73ff8c325c494c212dba269be499dfddca26b47540e0e2",
            "aquarium-goal-v27.yaml",
            "99048bb6dba1e44446f986cb7afe0704aa05fb71177ad3cc3950aa781979506a",
        ),
        (
            "aquarium-validation-v2.yaml",
            "27",
            "75d083e2812ea3cdee6774970bf5a2335607903468cb7c7554834c05d2a30e6c",
            "aquarium-validation-v26.yaml",
            "c036abf9ef161b2e8a52e8dbd5e88f8565d1010dd9becfcfa33fd54d4b72d29e",
        ),
    )
    for current_name, version, current_digest, prior_name, prior_digest in identities:
        current = PROCEDURES / current_name
        prior = FIXTURES / prior_name
        assert load_procedure(current_name)["version"] == version
        assert hashlib.sha256(current.read_bytes()).hexdigest() == current_digest
        assert hashlib.sha256(prior.read_bytes()).hexdigest() == prior_digest


PREDICATE_OPERATORS = (
    "equals",
    "not_equals",
    "empty",
    "non_empty",
    "at_least",
    "at_most",
)
MISSING_EVIDENCE = object()


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
        value = values.get((node, item), MISSING_EVIDENCE)
        if value is MISSING_EVIDENCE:
            return False
        if field is not None:
            if not isinstance(value, dict) or field not in value:
                return False
            value = value[field]
        if operator == "equals" and value != expected:
            return False
        if operator == "not_equals" and value == expected:
            return False
        if operator == "empty" and (value not in (None, "", ())) == expected:
            return False
        if operator == "non_empty" and (value not in (None, "", ())) != expected:
            return False
        if operator == "at_least" and (value is None or value < expected):
            return False
        if operator == "at_most" and (value is None or value > expected):
            return False
    return True


def test_guards_match_rejects_missing_or_unevaluable_evidence() -> None:
    def guarded(operator: str, expected: object, *, field: str | None = None) -> dict:
        guard = {
            "evidence": {"node": "review", "item": "optional-evidence"},
            operator: expected,
        }
        if field is not None:
            guard["field"] = field
        return {"guards": [guard]}

    missing: dict[tuple[str, str], object] = {}
    present_empty = {("review", "optional-evidence"): None}

    assert not guards_match(guarded("empty", True), missing)
    assert guards_match(guarded("empty", True), present_empty)
    assert not guards_match(guarded("not_equals", "waived"), missing)
    assert not guards_match(guarded("equals", "pass", field="outcome"), missing)
    assert not guards_match(
        guarded("equals", "pass", field="outcome"),
        {("review", "optional-evidence"): {}},
    )


def options(procedure: dict, definition_id: str) -> dict[str, dict]:
    return {
        option["id"]: option
        for option in procedure["node_definitions"][definition_id]["options"]
    }


def nodes(procedure: dict) -> dict[str, dict]:
    return {node["id"]: node for node in procedure["graph"]["nodes"]}


def graph_edges(procedure: dict) -> dict[str, set[str]]:
    edges = {node_id: set() for node_id in nodes(procedure)}
    for node_id, node in nodes(procedure).items():
        if "next" in node:
            edges[node_id].add(node["next"])
        edges[node_id].update(route["to"] for route in node.get("routes", {}).values())
    return edges


def reachable_nodes(
    edges: dict[str, set[str]], entry: str, *, without: str | None = None
) -> set[str]:
    if entry == without:
        return set()
    reached: set[str] = set()
    pending = [entry]
    while pending:
        node_id = pending.pop()
        if node_id == without or node_id in reached:
            continue
        reached.add(node_id)
        pending.extend(edges[node_id] - reached)
    return reached


def graph_predecessors(edges: dict[str, set[str]]) -> dict[str, set[str]]:
    predecessors = {node_id: set() for node_id in edges}
    for source, destinations in edges.items():
        for destination in destinations:
            predecessors[destination].add(source)
    return predecessors


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
        "changed-provider-resume-preserves-immediate-provider",
        "completed-change-consumes-next-ordinal-with-lineage",
        "completed-current-route-consumes-next-ordinal-with-lineage",
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
    cases = load_json("independent-review-routing-cases.json")[
        "task_review_route_cases"
    ]

    assert [case["id"] for case in cases] == [
        f"TR-{index:02d}" for index in range(1, 18)
    ]
    assert {case["route"] for case in cases} == {
        "mulgae",
        "herdr",
        "independent-review",
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
        case["ordinal"] == 0
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
            "to": "confirm-goal-assessment-core",
            "effect": "advance",
        }


def test_completion_status_contract_is_identical_across_workflows() -> None:
    cases = (
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


def test_task_review_uses_route_specific_serial_gates() -> None:
    task = load_procedure("aquarium-task-v2.yaml")
    graph = nodes(task)

    assert graph["document"]["next"] == "judge-documentation"
    assert (
        graph["decide-documentation-assessment"]["routes"]["passed"]["to"]
        == "prepare-review"
    )
    assert graph["prepare-review"]["next"] == "validate-review-route-entry"
    assert graph["classify-review-route-change"]["routes"] == {
        "unsettled": {
            "to": "authorize-incomplete-review-route",
            "effect": "advance",
        },
        "completed": {
            "to": "authorize-completed-review-route",
            "effect": "advance",
        },
    }
    expected_entries = {
        "planned-mulgae": "enter-mulgae-review-route",
        "planned-herdr": "enter-herdr-review-route",
        "planned-independent-review": "enter-independent-review-route",
        "planned-waiver": "enter-waived-review-route",
    }
    assert {
        option: route["to"]
        for option, route in graph["authorize-planned-review-route"]["routes"].items()
    } == expected_entries
    for entry in expected_entries.values():
        assert graph[entry]["routes"] == {
            "start": {"to": "review", "effect": "advance"},
            "reprepare": {"to": "prepare-review", "effect": "rework"},
        }

    assert graph["confirm-review-route-binding"]["routes"] == {
        "mulgae": {"to": "decide-mulgae-review-operation", "effect": "advance"},
        "herdr": {"to": "decide-herdr-review-operation", "effect": "advance"},
        "independent-review": {
            "to": "decide-independent-review-operation",
            "effect": "advance",
        },
        "waived": {"to": "confirm-assessment-ordinal", "effect": "advance"},
    }
    for route in ("mulgae", "herdr", "independent-review"):
        operation_node = (
            "decide-independent-review-operation"
            if route == "independent-review"
            else f"decide-{route}-review-operation"
        )
        assert graph[operation_node]["routes"] == {
            "assessed": {
                "to": "confirm-assessment-ordinal",
                "effect": "advance",
            },
            "unsettled": {
                "to": "confirm-incomplete-review-evidence",
                "effect": "advance",
            },
        }
    assert graph["confirm-assessment-ordinal"]["routes"] == {
        "work-unit": {
            "to": "confirm-first-review-evidence",
            "effect": "advance",
        },
        "remediation-confirmation": {
            "to": "confirm-extra-review-evidence",
            "effect": "advance",
        },
    }
    assessment_sources = {
        source["node"]: set(source["items"])
        for source in graph["confirm-assessment-ordinal"]["evidence_from"]
    }
    assert {
        "prior-assessment-ordinal",
        "finding-lineage-summary",
        "remaining-review-authority-summary",
        "corrected-target-summary",
        "extra-assessment-authority-reference",
    } <= assessment_sources["prepare-review"]
    for gate in ("confirm-first-review-evidence", "confirm-extra-review-evidence"):
        assert set(graph[gate]["routes"]) == {"mulgae", "static-delegated", "waived"}
    assert graph["decide-backend-check"]["routes"] == {
        "non-failing": {
            "to": "judge-review",
            "effect": "advance",
        },
        "failed": {
            "to": "record-task-rework-basis",
            "effect": "advance",
        },
    }
    assert graph["record-review-route-direction"]["next"] == (
        "choose-review-route-direction"
    )
    assert graph["choose-review-route-direction"]["routes"] == {
        "continue": {"to": "prepare-review", "effect": "rework"},
        "stop": {"to": "record-review-route-stop", "effect": "advance"},
    }
    assert graph["authorize-current-review-route-resume"]["routes"] == {
        "mulgae": {"to": "enter-mulgae-review-route", "effect": "advance"},
        "herdr": {"to": "enter-herdr-review-route", "effect": "advance"},
        "independent-review": {
            "to": "enter-independent-review-route",
            "effect": "advance",
        },
    }
    assert normalized_guards(
        options(task, "review-route-direction-decision")["continue"]
    ) == {
        (
            "record-review-route-direction",
            "requested-route-direction",
            None,
            "not_equals",
            "stop",
        ),
        (
            "record-review-route-direction",
            "route-transition-admission",
            "outcome",
            "equals",
            "pass",
        ),
    }


def test_task_review_route_evidence_combinations_are_guarded() -> None:
    task = load_procedure("aquarium-task-v2.yaml")
    assert task["version"] == "25"

    evidence = options(task, "review-evidence-decision")
    provenance = options(task, "review-provenance-decision")
    cases = (
        ("mulgae", "complete", "pass", "mulgae", "delegated-reviewer", None),
        (
            "herdr",
            "complete",
            "not-provided",
            "static-delegated",
            "delegated-reviewer",
            None,
        ),
        (
            "independent-review",
            "complete",
            "not-provided",
            "static-delegated",
            "delegated-reviewer",
            None,
        ),
        (
            "waived",
            "waived",
            "not-provided",
            "waived",
            "coordinator-waiver",
            "authority and assurance limitation",
        ),
    )
    for route, operation, backend, evidence_option, kind, waiver in cases:
        values = {
            ("review", "review-route"): route,
            ("review", "review-operation"): operation,
            ("review", "backend-check-result"): backend,
            ("review", "assessment-provenance-kind"): kind,
            ("review", "review-evidence-reference"): "fixture:evidence",
        }
        if waiver is not None:
            values[("review", "waiver-summary")] = waiver
        assert guards_match(evidence[evidence_option], values), route
        provenance_option = "waived" if route == "waived" else "delegated"
        assert guards_match(provenance[provenance_option], values), route

        wrong_backend = dict(values)
        wrong_backend[("review", "backend-check-result")] = (
            "not-provided" if route == "mulgae" else "pass"
        )
        assert not guards_match(evidence[evidence_option], wrong_backend), route

    operation = options(task, "review-operation-decision")
    assert normalized_guards(operation["assessed"]) == {
        ("review", "review-operation", None, "equals", "complete"),
        ("review", "assessment-ordinal", None, "at_least", 1),
    }
    assert normalized_guards(operation["unsettled"]) == {
        ("review", "review-route", None, "not_equals", "waived"),
        ("review", "review-operation", None, "not_equals", "complete"),
        ("review", "review-operation", None, "not_equals", "waived"),
        ("review", "assessment-ordinal", None, "equals", 0),
    }
    invalid_completed_zero = {
        ("review", "review-route"): "herdr",
        ("review", "review-operation"): "complete",
        ("review", "assessment-ordinal"): 0,
    }
    assert not guards_match(operation["assessed"], invalid_completed_zero)
    assert not guards_match(operation["unsettled"], invalid_completed_zero)

    ordinal = options(task, "assessment-ordinal-decision")
    first = {
        ("review", "assessment-ordinal"): 1,
        ("review", "assessment-kind"): "work-unit",
        ("review", "review-mode"): "remediation-eligible",
        ("review", "assessment-ordinal-continuity"): {"outcome": "pass"},
    }
    assert guards_match(ordinal["work-unit"], first)
    second = dict(first)
    second[("review", "assessment-ordinal")] = 2
    assert guards_match(ordinal["work-unit"], second)
    third = dict(first)
    third[("review", "assessment-ordinal")] = 3
    assert guards_match(ordinal["work-unit"], third)
    confirmation = dict(first)
    confirmation[("review", "assessment-ordinal")] = 4
    confirmation[("review", "assessment-kind")] = "remediation-confirmation"
    confirmation[("review", "review-mode")] = "confirmation-only"
    assert guards_match(ordinal["remediation-confirmation"], confirmation)
    authorized = {
        ("review", "assessment-ordinal"): 5,
        ("review", "assessment-kind"): "remediation-confirmation",
        ("review", "review-mode"): "confirmation-only",
        ("review", "assessment-ordinal-continuity"): {"outcome": "pass"},
    }
    assert guards_match(ordinal["remediation-confirmation"], authorized)


def test_waiver_evidence_rejects_missing_or_cross_route_provenance() -> None:
    task = load_procedure("aquarium-task-v2.yaml")
    task_waiver = options(task, "review-provenance-decision")["waived"]
    task_values = {
        ("review", "review-operation"): "waived",
        ("review", "assessment-provenance-kind"): "coordinator-waiver",
        ("review", "waiver-summary"): "authority and assurance limitation",
        ("review", "review-evidence-reference"): "fixture:evidence",
    }
    assert guards_match(task_waiver, task_values)
    for key in (
        ("review", "waiver-summary"),
        ("review", "review-evidence-reference"),
    ):
        missing = dict(task_values)
        missing.pop(key)
        assert not guards_match(task_waiver, missing), key
    wrong_kind = dict(task_values)
    wrong_kind[("review", "assessment-provenance-kind")] = "delegated-reviewer"
    assert not guards_match(task_waiver, wrong_kind)

    goal = load_procedure("aquarium-goal-v2.yaml")
    goal_waiver = options(goal, "waived-finding-validity-decision")["resolved"]
    goal_values = {
        ("record-evidence", "confirmation-needed-findings"): 0,
        ("record-evidence", "waiver-summary"): "authority and assurance limitation",
    }
    assert guards_match(goal_waiver, goal_values)
    goal_values.pop(("record-evidence", "waiver-summary"))
    assert not guards_match(goal_waiver, goal_values)

    validation = load_procedure("aquarium-validation-v2.yaml")
    final_items = {
        item["id"]: item
        for item in validation["node_definitions"]["final-review-record"]["items"]
    }
    assert final_items["waiver-summary"]["required_when"] == [
        {"item": "review-route", "equals": "waived"}
    ]


def test_managed_procedure_decision_options_fit_podway_v0210_guard_limit() -> None:
    for path in sorted(PROCEDURES.glob("aquarium-*-v2.yaml")):
        procedure = yaml.safe_load(path.read_text(encoding="utf-8"))
        for definition_id, definition in procedure["node_definitions"].items():
            if definition.get("type") != "decision":
                continue
            for option in definition.get("options", []):
                assert len(option.get("guards", [])) <= 4, (
                    path.name,
                    definition_id,
                    option["id"],
                )


def test_managed_procedure_decisions_fit_podway_v0210_option_limit() -> None:
    for path in sorted(PROCEDURES.glob("aquarium-*-v2.yaml")):
        procedure = yaml.safe_load(path.read_text(encoding="utf-8"))
        for definition_id, definition in procedure["node_definitions"].items():
            if definition.get("type") != "decision":
                continue
            assert 1 <= len(definition.get("options", [])) <= 8, (
                path.name,
                definition_id,
            )


def test_assessment_ordinal_routes_have_distinct_effective_destinations() -> None:
    for path in sorted(PROCEDURES.glob("aquarium-*-v2.yaml")):
        procedure = yaml.safe_load(path.read_text(encoding="utf-8"))
        for node in procedure["graph"]["nodes"]:
            if node.get("use") != "assessment-ordinal-decision":
                continue
            pairs = [
                (route["to"], route["effect"])
                for route in node.get("routes", {}).values()
            ]
            assert len(pairs) == len(set(pairs)), (path.name, node["id"], pairs)


def test_managed_procedures_fit_podway_v0210_evidence_bounds() -> None:
    for path in sorted(PROCEDURES.glob("aquarium-*-v2.yaml")):
        procedure = yaml.safe_load(path.read_text(encoding="utf-8"))
        for node in procedure["graph"]["nodes"]:
            evidence_from = node.get("evidence_from", [])
            assert len(evidence_from) <= 8, (path.name, node["id"])
            for source in node.get("evidence_from", []):
                assert len(source.get("items", [])) <= 16, (
                    path.name,
                    node["id"],
                    source["node"],
                )


def test_task_070_serial_gates_preserve_every_prior_selected_evidence_item() -> None:
    cases = (
        (
            "aquarium-goal-v2.yaml",
            "aquarium-goal-v18.yaml",
            "decide-evidence",
            ("decide-evidence",),
        ),
        (
            "aquarium-goal-v2.yaml",
            "aquarium-goal-v18.yaml",
            "assess-goal",
            ("confirm-goal-assessment-core", "assess-goal"),
        ),
        (
            "aquarium-goal-v2.yaml",
            "aquarium-goal-v18.yaml",
            "assess-goal",
            ("confirm-stopped-goal-assessment-core", "assess-stopped-goal"),
        ),
        (
            "aquarium-validation-v2.yaml",
            "aquarium-validation-v17.yaml",
            "assess-goal",
            ("confirm-goal-assessment-core", "assess-goal"),
        ),
        (
            "aquarium-validation-v2.yaml",
            "aquarium-validation-v17.yaml",
            "assess-goal",
            ("confirm-stopped-goal-assessment-core", "assess-stopped-goal"),
        ),
    )

    def selected_items(node: dict) -> set[tuple[str, str]]:
        return {
            (source["node"], item)
            for source in node.get("evidence_from", [])
            for item in source.get("items", [])
        }

    for current_name, prior_name, prior_node_id, current_node_ids in cases:
        current = nodes(load_procedure(current_name))
        prior = nodes(
            yaml.safe_load((FIXTURES / prior_name).read_text(encoding="utf-8"))
        )
        preserved = set().union(
            *(selected_items(current[node_id]) for node_id in current_node_ids),
            selected_items(current["prepare-stopped-goal-assessment"])
            if current_name == "aquarium-goal-v2.yaml"
            and "assess-stopped-goal" in current_node_ids
            else set(),
        )
        prior_selected = selected_items(prior[prior_node_id])
        if current_node_ids == ("confirm-goal-assessment-core", "assess-goal"):
            prior_selected -= {
                ("record-stopped", "disposition-summary"),
                ("record-incomplete", "disposition-summary"),
                ("record-review-operation-incomplete", "disposition-summary"),
            }
        assert prior_selected <= preserved, (
            current_name,
            prior_node_id,
            current_node_ids,
        )


def test_task_route_authorization_paths_cannot_cross_select() -> None:
    task = load_procedure("aquarium-task-v2.yaml")
    graph = nodes(task)
    assert graph["validate-review-route-entry"]["routes"] == {
        "planned": {"to": "authorize-planned-review-route", "effect": "advance"},
        "changed": {"to": "classify-review-route-change", "effect": "advance"},
        "continued": {
            "to": "authorize-completed-current-review-route",
            "effect": "advance",
        },
        "resumed": {
            "to": "authorize-current-review-route-resume",
            "effect": "advance",
        },
    }
    assert graph["classify-review-route-change"]["routes"] == {
        "unsettled": {
            "to": "authorize-incomplete-review-route",
            "effect": "advance",
        },
        "completed": {
            "to": "authorize-completed-review-route",
            "effect": "advance",
        },
    }
    planned = options(task, "planned-review-route-authorization-decision")
    values = {
        ("record-plan", "review-route"): "herdr",
        ("prepare-review", "effective-review-route"): "herdr",
        ("prepare-review", "route-authorization-basis"): "approved-plan",
        ("prepare-review", "checkpoint-requested-direction"): "not-applicable",
        ("prepare-review", "prior-review-route"): "not-applicable",
        ("prepare-review", "route-change-authority-reference"): None,
        ("prepare-review", "prior-assessment-ordinal"): 0,
        ("prepare-review", "finding-lineage-summary"): None,
        ("prepare-review", "remaining-review-authority-summary"): None,
        ("prepare-review", "corrected-target-summary"): None,
        ("prepare-review", "extra-assessment-authority-reference"): None,
    }
    assert guards_match(planned["planned-herdr"], values)
    assert not guards_match(planned["planned-mulgae"], values)


def test_task_checkpoint_direction_matrix_guards_every_authorization_basis() -> None:
    task = load_procedure("aquarium-task-v2.yaml")
    graph = nodes(task)
    checkpoint = {
        item["id"]: item
        for item in task["node_definitions"]["review-checkpoint-record"]["items"]
    }
    assert checkpoint["route-authorization-basis"]["choices"] == [
        "approved-plan",
        "continued-checkpoint",
        "explicit-route-change",
        "explicit-waiver",
        "resume-current",
    ]
    assert checkpoint["prior-review-operation"]["choices"] == [
        "not-applicable",
        "complete",
        "incomplete",
        "failed",
        "waived",
    ]
    assert checkpoint["checkpoint-requested-direction"]["choices"] == [
        "not-applicable",
        "continue-current",
        "resume-current",
        "switch-route",
        "waive",
    ]
    continuity = checkpoint["route-direction-continuity"]
    assert continuity["required_when"] == [
        {"item": "route-authorization-basis", "not_equals": "approved-plan"}
    ]
    assert continuity["operation_id"] == (
        "aquarium-task-review-route-direction-continuity"
    )
    assert continuity["operation_digest"] == (
        "sha256:ff10d6b0b0cc4c06a73d8b9edcdda1716c7831e535c9d8b47754f391d76b8fd6"
    )

    entry = options(task, "review-route-entry-decision")
    for option_id in (
        "changed",
        "continued",
        "resumed",
    ):
        assert (
            "prepare-review",
            "route-direction-continuity",
            "outcome",
            "equals",
            "pass",
        ) in normalized_guards(entry[option_id])

    definitions = {
        "planned-review-route-authorization-decision": "not-applicable",
        "completed-current-review-route-authorization-decision": ("continue-current"),
        "current-review-route-resume-authorization-decision": "resume-current",
    }
    for definition_id, direction in definitions.items():
        for option in options(task, definition_id).values():
            assert (
                "prepare-review",
                "checkpoint-requested-direction",
                None,
                "equals",
                direction,
            ) in normalized_guards(option)

    for definition_id in (
        "incomplete-review-route-authorization-decision",
        "completed-review-route-authorization-decision",
    ):
        for option_id, option in options(task, definition_id).items():
            direction = "waive" if option_id.endswith("waiver") else "switch-route"
            assert (
                "prepare-review",
                "checkpoint-requested-direction",
                None,
                "equals",
                direction,
            ) in normalized_guards(option)

    change_state = options(task, "review-route-change-state-decision")
    for operation in ("incomplete", "failed"):
        assert guards_match(
            change_state["unsettled"],
            {("prepare-review", "prior-review-operation"): operation},
        )
    completed_state = {
        ("prepare-review", "prior-review-operation"): "complete",
        ("prepare-review", "prior-review-route"): "mulgae",
        ("prepare-review", "prior-route-change-readiness"): "completed-checkpoint",
        ("prepare-review", "prior-assessment-ordinal"): 1,
    }
    assert guards_match(change_state["completed"], completed_state)
    for key, invalid in (
        (("prepare-review", "prior-review-operation"), "failed"),
        (("prepare-review", "prior-assessment-ordinal"), 0),
    ):
        mismatched = dict(completed_state)
        mismatched[key] = invalid
        assert not guards_match(change_state["completed"], mismatched)

    completed_waiver_state = {
        **completed_state,
        ("prepare-review", "prior-review-operation"): "waived",
        ("prepare-review", "prior-review-route"): "waived",
    }
    assert guards_match(change_state["completed"], completed_waiver_state)
    for operation in ("incomplete", "failed", "not-applicable"):
        unsettled = {
            **completed_state,
            ("prepare-review", "prior-review-operation"): operation,
        }
        assert not guards_match(change_state["completed"], unsettled)

    entry_state = options(task, "review-route-entry-decision")

    def matching_entry_ids(values: dict[tuple[str, str], object]) -> set[str]:
        return {
            option_id
            for option_id, option in entry_state.items()
            if guards_match(option, values)
        }

    delegated_entry = {
        **completed_state,
        ("prepare-review", "route-authorization-basis"): "continued-checkpoint",
        ("prepare-review", "checkpoint-requested-direction"): "continue-current",
        ("prepare-review", "route-direction-continuity"): {"outcome": "pass"},
    }
    waiver_entry = {
        **completed_waiver_state,
        ("prepare-review", "route-authorization-basis"): "continued-checkpoint",
        ("prepare-review", "checkpoint-requested-direction"): "continue-current",
        ("prepare-review", "route-direction-continuity"): {"outcome": "pass"},
    }
    assert guards_match(entry_state["continued"], delegated_entry)
    assert guards_match(entry_state["continued"], waiver_entry)
    assert matching_entry_ids(delegated_entry) == {"continued"}
    assert matching_entry_ids(waiver_entry) == {"continued"}
    unsettled_entry = dict(delegated_entry)
    unsettled_entry[("prepare-review", "prior-review-operation")] = "incomplete"
    unsettled_entry[("prepare-review", "route-authorization-basis")] = (
        "explicit-route-change"
    )
    unsettled_entry[("prepare-review", "checkpoint-requested-direction")] = (
        "switch-route"
    )
    assert not guards_match(entry_state["continued"], unsettled_entry)
    assert matching_entry_ids(unsettled_entry) == {"changed"}
    resumed_entry = {
        **unsettled_entry,
        ("prepare-review", "route-authorization-basis"): "resume-current",
        ("prepare-review", "checkpoint-requested-direction"): "resume-current",
    }
    assert matching_entry_ids(resumed_entry) == {"resumed"}

    incomplete = options(task, "incomplete-review-route-authorization-decision")
    incomplete_switch = {
        ("prepare-review", "effective-review-route"): "herdr",
        ("prepare-review", "route-authorization-basis"): "explicit-route-change",
        ("prepare-review", "checkpoint-requested-direction"): "switch-route",
        ("prepare-review", "prior-route-change-readiness"): "safe-to-change",
    }
    assert guards_match(incomplete["changed-herdr"], incomplete_switch)
    incomplete_switch[("prepare-review", "prior-route-change-readiness")] = (
        "completed-checkpoint"
    )
    assert not guards_match(incomplete["changed-herdr"], incomplete_switch)

    completed = options(task, "completed-review-route-authorization-decision")
    completed_switch = {
        **completed_state,
        ("prepare-review", "effective-review-route"): "herdr",
        ("prepare-review", "route-authorization-basis"): "explicit-route-change",
        ("prepare-review", "checkpoint-requested-direction"): "switch-route",
    }
    assert guards_match(completed["completed-change-herdr"], completed_switch)
    assert not guards_match(completed["completed-change-waiver"], completed_switch)
    completed_waiver = {
        **completed_waiver_state,
        ("prepare-review", "effective-review-route"): "waived",
        ("prepare-review", "route-authorization-basis"): "explicit-waiver",
        ("prepare-review", "checkpoint-requested-direction"): "waive",
    }
    assert guards_match(completed["completed-change-waiver"], completed_waiver)
    assert not guards_match(completed["completed-change-herdr"], completed_waiver)

    continued = options(task, "completed-current-review-route-authorization-decision")
    continued_herdr = {
        ("prepare-review", "effective-review-route"): "herdr",
        ("prepare-review", "prior-review-route"): "herdr",
        ("prepare-review", "route-authorization-basis"): "continued-checkpoint",
        ("prepare-review", "checkpoint-requested-direction"): "continue-current",
        ("prepare-review", "route-change-authority-reference"): "fix-and-review",
        ("prepare-review", "prior-assessment-ordinal"): 1,
    }
    assert guards_match(continued["continued-herdr"], continued_herdr)
    assert not guards_match(continued["continued-mulgae"], continued_herdr)

    review_sources = {source["node"] for source in graph["review"]["evidence_from"]}
    assert "authorize-completed-review-route" in review_sources
    assert "authorize-completed-waiver-review-route" not in graph


def test_task_route_fixtures_traverse_only_guarded_options() -> None:
    task = load_procedure("aquarium-task-v2.yaml")
    cases = load_json("independent-review-routing-cases.json")[
        "task_review_route_cases"
    ]
    authorization = {
        option_id: option
        for definition in (
            "planned-review-route-authorization-decision",
            "incomplete-review-route-authorization-decision",
            "completed-review-route-authorization-decision",
            "completed-current-review-route-authorization-decision",
        )
        for option_id, option in options(task, definition).items()
    }
    entry = options(task, "authorized-review-route-entry-decision")
    operation = options(task, "review-operation-decision")
    ordinal = options(task, "assessment-ordinal-decision")
    evidence = options(task, "review-evidence-decision")
    incomplete_evidence = options(task, "incomplete-review-evidence-decision")
    provenance = options(task, "review-provenance-decision")
    direction = options(task, "review-route-direction-decision")
    resume_authorization = options(
        task, "current-review-route-resume-authorization-decision"
    )

    for case in cases:
        assert case["route_authorization_option"] in authorization
        assert case["entry_option"] in entry
        values = {
            ("record-plan", "review-route"): case["plan_route"],
            ("prepare-review", "effective-review-route"): case["route"],
            ("prepare-review", "route-authorization-basis"): case[
                "route_authorization_basis"
            ],
            ("prepare-review", "checkpoint-requested-direction"): (
                "not-applicable"
                if case["route_authorization_basis"] == "approved-plan"
                else "continue-current"
                if case["route_authorization_basis"] == "continued-checkpoint"
                else "waive"
                if case["route_authorization_option"].endswith("waiver")
                else "switch-route"
                if case["route_authorization_basis"] == "explicit-route-change"
                else "resume-current"
            ),
            ("prepare-review", "prior-review-operation"): case[
                "prior_review_operation"
            ],
            ("prepare-review", "prior-review-route"): case["prior_review_route"],
            ("prepare-review", "prior-route-change-readiness"): case[
                "prior_route_change_readiness"
            ],
            ("prepare-review", "prior-assessment-ordinal"): case["prior_ordinal"],
            ("prepare-review", "route-change-authority-reference"): case.get(
                "route_change_authority_reference"
            ),
            ("review", "review-route"): case["route"],
            ("review", "review-operation"): case["operation"],
            ("review", "backend-check-result"): case["backend_check"],
            ("review", "assessment-ordinal"): case["ordinal"],
            ("review", "assessment-provenance-kind"): (
                "coordinator-waiver"
                if case["route"] == "waived"
                else "delegated-reviewer"
            ),
            ("review", "review-evidence-reference"): "fixture:evidence",
        }
        if case["waiver_summary"] is not None:
            values[("review", "waiver-summary")] = case["waiver_summary"]
        assert guards_match(
            authorization[case["route_authorization_option"]], values
        ), case["id"]
        if case["route"] != "waived":
            assert guards_match(operation[case["operation_option"]], values), case["id"]
        if case["ordinal"] > 0:
            values.update(
                {
                    ("prepare-review", "prior-assessment-ordinal"): case[
                        "prior_ordinal"
                    ],
                    ("review", "assessment-ordinal-continuity"): {"outcome": "pass"},
                    ("review", "review-mode"): (
                        "confirmation-only"
                        if case["assessment_kind"] == "remediation-confirmation"
                        else "remediation-eligible"
                    ),
                    ("review", "assessment-kind"): case["assessment_kind"],
                }
            )
            assert guards_match(ordinal[case["ordinal_option"]], values), case["id"]
            assert guards_match(evidence[case["evidence_option"]], values), case["id"]
        else:
            assert guards_match(incomplete_evidence[case["evidence_option"]], values), (
                case["id"]
            )
        assert guards_match(provenance[case["provenance_option"]], values), case["id"]

        if "settlement_option" in case:
            recovery = {
                (
                    "record-review-route-direction",
                    "prior-route-lifecycle-state",
                ): case["prior_state"],
                (
                    "record-review-route-direction",
                    "route-change-readiness",
                ): case["route_change_readiness"],
                (
                    "record-review-route-direction",
                    "requested-route-direction",
                ): case["requested_direction"],
            }
            recovery[
                (
                    "record-review-route-direction",
                    "route-transition-admission",
                )
            ] = {"outcome": case["route_transition_outcome"]}
            assert guards_match(direction[case["direction_option"]], recovery)
        if "resume_authorization_option" in case:
            resumed = {
                ("prepare-review", "prior-review-route"): case["resume_prior_route"],
                ("prepare-review", "effective-review-route"): case[
                    "resume_prior_route"
                ],
                ("prepare-review", "route-authorization-basis"): "resume-current",
                ("prepare-review", "checkpoint-requested-direction"): (
                    "resume-current"
                ),
            }
            option = resume_authorization[case["resume_authorization_option"]]
            assert guards_match(option, resumed), case["id"]
            for other_provider in {"mulgae", "herdr", "independent-review"} - {
                case["resume_authorization_option"]
            }:
                assert not guards_match(
                    resume_authorization[other_provider], resumed
                ), case["id"]

    current_only = {
        ("record-review-route-direction", "requested-route-direction"): (
            "switch-route"
        ),
        ("record-review-route-direction", "route-transition-admission"): {
            "outcome": "fail"
        },
    }
    assert not guards_match(direction["continue"], current_only)
    current_only[("record-review-route-direction", "requested-route-direction")] = (
        "waive"
    )
    assert not guards_match(direction["continue"], current_only)


def test_goal_routes_completion_findings_authority_and_low_handling_serially() -> None:
    goal = load_procedure("aquarium-goal-v2.yaml")
    graph = nodes(goal)

    assert graph["decide-review-basis"]["routes"]["native-review"] == {
        "to": "confirm-review-route-binding",
        "effect": "advance",
    }
    assert set(graph["confirm-review-route-binding"]["routes"]) == {
        "planned-mulgae",
        "planned-herdr",
        "planned-independent-review",
        "planned-waiver",
        "changed-mulgae",
        "changed-herdr",
        "changed-independent-review",
        "changed-waiver",
    }
    assert graph["decide-planned-mulgae-review-operation"]["routes"] == {
        "completed": {
            "to": "confirm-completed-assessment-ordinal",
            "effect": "advance",
        },
        "waived": {
            "to": "confirm-waived-assessment-ordinal",
            "effect": "advance",
        },
        "unsuccessful": {
            "to": "confirm-incomplete-route-evidence",
            "effect": "advance",
        },
    }
    assert graph["confirm-extra-assessment-ordinal"]["routes"] == {
        "authorized-extra": {
            "to": "confirm-extra-route-evidence",
            "effect": "advance",
        },
        "invalid-extra": {"to": "record-evidence", "effect": "rework"},
    }
    for node_id in (
        "confirm-completed-assessment-ordinal",
        "confirm-waived-assessment-ordinal",
    ):
        assert graph[node_id]["routes"]["third"] == {
            "to": "confirm-third-route-evidence",
            "effect": "advance",
        }
    for node_id in (
        "confirm-first-route-evidence",
        "confirm-second-route-evidence",
        "confirm-third-route-evidence",
        "confirm-extra-route-evidence",
    ):
        assert set(graph[node_id]["routes"]) == {
            "mulgae-pass",
            "mulgae-fail",
            "herdr",
            "independent-review",
            "waived",
        }
        assert graph[node_id]["routes"]["waived"]["to"] == (
            "confirm-waived-finding-validity"
        )
    assert graph["confirm-waived-finding-validity"]["routes"] == {
        "resolved": {
            "to": "decide-operational-evidence",
            "effect": "advance",
        },
        "unresolved": {"to": "record-evidence", "effect": "rework"},
    }
    assert (
        graph["confirm-mulgae-fail-finding-validity"]["routes"]["resolved"]["to"]
        == "decide-goal-rework-authority"
    )
    assert graph["choose-terminal-review-route-direction"]["routes"][
        "change-route"
    ] == {"to": "complete-work", "effect": "rework"}
    assert graph["confirm-hardening-review-eligibility"]["routes"]["ineligible"] == {
        "to": "record-evidence",
        "effect": "rework",
    }
    assert graph["confirm-hardening-record"]["routes"]["incomplete"] == {
        "to": "record-hardening-deferral",
        "effect": "rework",
    }


def test_goal_and_validation_route_fixtures_cover_each_route_and_recovery() -> None:
    fixture = load_json("independent-review-routing-cases.json")
    goal = load_procedure("aquarium-goal-v2.yaml")
    validation = load_procedure("aquarium-validation-v2.yaml")
    goal_cases = fixture["goal_review_route_cases"]
    validation_cases = fixture["validation_review_route_cases"]

    final_review_items = {
        item["id"]
        for item in validation["node_definitions"]["final-review-record"]["items"]
    }
    assert {"prior-review-route", "prior-review-operation"} <= final_review_items
    final_review_definitions = {
        item["id"]: item
        for item in validation["node_definitions"]["final-review-record"]["items"]
    }
    assert "waived" in final_review_definitions["prior-review-route"]["choices"]
    assert "waived" in final_review_definitions["prior-review-operation"]["choices"]
    binding_items = {
        item
        for source in nodes(validation)["confirm-final-review-route-binding"][
            "evidence_from"
        ]
        if source["node"] == "final-review"
        for item in source["items"]
    }
    assert {
        "prior-review-route",
        "prior-review-operation",
        "prior-route-lifecycle-state",
        "route-direction",
        "route-change-readiness",
        "route-binding-result",
        "finding-lineage-summary",
        "remaining-review-authority-summary",
        "corrected-target-summary",
        "prior-assessment-ordinal",
        "assessment-ordinal",
    } <= binding_items

    assert {case["route"] for case in goal_cases} == {
        "mulgae",
        "herdr",
        "independent-review",
        "waived",
    }
    binding = options(goal, "review-route-binding-decision")
    goal_record_items = {
        item["id"] for item in goal["node_definitions"]["evidence-record"]["items"]
    }
    assert {
        "prior-review-route",
        "prior-review-operation",
        "route-binding-result",
    } <= goal_record_items
    goal_binding_items = {
        item
        for source in nodes(goal)["confirm-review-route-binding"]["evidence_from"]
        if source["node"] == "record-evidence"
        for item in source["items"]
    }
    assert {
        "prior-review-route",
        "prior-review-operation",
        "route-binding-result",
        "finding-lineage-summary",
        "remaining-review-authority-summary",
        "corrected-target-summary",
        "prior-assessment-ordinal",
        "assessment-ordinal",
    } <= goal_binding_items
    planned_operation = options(goal, "review-operation-decision")
    changed_operation = options(goal, "changed-review-operation-decision")
    goal_ordinal = options(goal, "assessment-ordinal-decision")
    route_evidence = options(goal, "route-evidence-decision")
    incomplete_evidence = options(goal, "incomplete-route-evidence-decision")
    goal_settlement = options(goal, "review-route-settlement-decision")
    goal_direction = options(goal, "review-route-direction-decision")
    for case in goal_cases:
        assert case["route_authorization_option"] in binding
        values = {
            ("record-evidence", "review-route"): case["route"],
            ("record-evidence", "review-operation"): case["operation"],
            ("record-evidence", "assessment-ordinal"): case["ordinal"],
            ("record-evidence", "prior-assessment-ordinal"): case["prior_ordinal"],
            ("record-evidence", "backend-check-result"): case["backend_check"],
            ("record-evidence", "assessment-provenance-kind"): (
                "coordinator-waiver"
                if case["route"] == "waived"
                else "delegated-reviewer"
            ),
            ("record-evidence", "review-mode"): (
                "confirmation-only"
                if case.get("assessment_kind") == "remediation-confirmation"
                else "remediation-eligible"
                if case["ordinal"] > 0
                else "confirmation-only"
            ),
            ("record-evidence", "assessment-kind"): case.get("assessment_kind"),
            ("record-evidence", "assessment-ordinal-continuity"): {"outcome": "pass"},
            ("record-evidence", "route-binding-result"): {"outcome": "pass"},
            ("record-evidence", "prior-route-lifecycle-state"): case.get(
                "prior_lifecycle", "not-started"
            ),
        }
        if case.get("waiver_summary") is not None:
            values[("record-evidence", "waiver-summary")] = case["waiver_summary"]
        operation_options = (
            changed_operation
            if case["route_authorization_option"].startswith("changed-")
            else planned_operation
        )
        assert guards_match(operation_options[case["operation_option"]], values), case[
            "id"
        ]
        if case["ordinal"] > 0:
            assert guards_match(goal_ordinal[case["ordinal_option"]], values), case[
                "id"
            ]
            assert guards_match(route_evidence[case["evidence_option"]], values), case[
                "id"
            ]
        else:
            assert guards_match(incomplete_evidence[case["evidence_option"]], values), (
                case["id"]
            )
        if "settlement_option" in case:
            values[("record-evidence", "route-change-readiness")] = "safe-to-change"
            values[("record-evidence", "route-direction")] = case["requested_direction"]
            assert guards_match(goal_settlement[case["settlement_option"]], values)
            assert guards_match(goal_direction[case["direction_option"]], values)

    assert {case["route"] for case in validation_cases} == {
        "mulgae",
        "herdr",
        "independent-review",
        "waived",
    }
    operation = options(validation, "final-review-operation-decision")
    ordinal = options(validation, "assessment-ordinal-decision")
    provenance = options(validation, "assessment-provenance-decision")
    applicability = options(validation, "final-backend-applicability-decision")
    settlement = options(validation, "final-route-settlement-decision")
    current_direction = options(validation, "current-route-direction-decision")
    settled_direction = options(validation, "settled-route-direction-decision")
    for case in validation_cases:
        values = {
            ("final-review", "assessment-ordinal"): case["ordinal"],
            ("final-review", "assessment-kind"): case.get("assessment_kind"),
            ("final-review", "review-mode"): (
                "confirmation-only"
                if case.get("assessment_kind") == "remediation-confirmation"
                else "remediation-eligible"
                if case["ordinal"] > 0
                else "confirmation-only"
            ),
            ("final-review", "assessment-ordinal-continuity"): {"outcome": "pass"},
            ("final-review", "assessment-provenance-result"): {"outcome": "pass"},
            ("final-review", "review-route"): case["route"],
            ("final-review", "backend-check-result"): case["backend_check"],
            ("final-review", "prior-route-lifecycle-state"): case.get(
                "prior_lifecycle", "not-started"
            ),
            ("final-review", "route-change-readiness"): (
                "current-route-only"
                if case.get("settlement_option") == "current-only"
                else "safe-to-change"
            ),
            ("final-review", "route-direction"): case.get("requested_direction"),
        }
        assert guards_match(operation[case["operation_option"]], values), case["id"]
        assert guards_match(provenance[case["provenance_option"]], values), case["id"]
        if case["ordinal"] > 0:
            assert guards_match(ordinal[case["ordinal_option"]], values), case["id"]
            assert guards_match(
                applicability[case["backend_applicability_option"]], values
            ), case["id"]
        if "settlement_option" in case:
            assert guards_match(settlement[case["settlement_option"]], values)
            directions = (
                current_direction
                if case["settlement_option"] == "current-only"
                else settled_direction
            )
            assert guards_match(directions[case["direction_option"]], values)


def test_managed_review_route_choices_exclude_independent() -> None:
    expected = ["mulgae", "herdr", "independent-review", "waived"]
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
    task = load_procedure("aquarium-task-v2.yaml")
    task_evidence = options(task, "review-evidence-decision")
    task_values = {
        ("review", "review-route"): "mulgae",
        ("review", "review-operation"): "complete",
        ("review", "backend-check-result"): "pass",
    }
    assert guards_match(task_evidence["mulgae"], task_values)
    task_values[("review", "backend-check-result")] = "not-provided"
    assert not guards_match(task_evidence["mulgae"], task_values)

    goal = load_procedure("aquarium-goal-v2.yaml")
    goal_evidence = options(goal, "route-evidence-decision")
    values = {
        ("record-evidence", "review-route"): "waived",
        ("record-evidence", "review-operation"): "waived",
        ("record-evidence", "backend-check-result"): "not-provided",
        ("record-evidence", "assessment-provenance-kind"): "coordinator-waiver",
    }
    assert guards_match(goal_evidence["waived"], values)
    values[("record-evidence", "assessment-provenance-kind")] = "delegated-reviewer"
    assert not guards_match(goal_evidence["waived"], values)

    validation = load_procedure("aquarium-validation-v2.yaml")
    applicability = options(validation, "final-backend-applicability-decision")
    values = {
        ("final-review", "review-route"): "herdr",
        ("final-review", "backend-check-result"): "not-provided",
    }
    assert guards_match(applicability["not-required"], values)
    values[("final-review", "backend-check-result")] = "pass"
    assert not guards_match(applicability["not-required"], values)


def test_incomplete_route_changes_preserve_the_pending_ordinal() -> None:
    task = load_procedure("aquarium-task-v2.yaml")
    task_operation = options(task, "review-operation-decision")["unsettled"]
    assert guards_match(
        task_operation,
        {
            ("review", "review-route"): "herdr",
            ("review", "review-operation"): "incomplete",
            ("review", "assessment-ordinal"): 0,
        },
    )
    assert not guards_match(
        task_operation,
        {
            ("review", "review-route"): "herdr",
            ("review", "review-operation"): "incomplete",
            ("review", "assessment-ordinal"): 1,
        },
    )

    goal = load_procedure("aquarium-goal-v2.yaml")
    goal_operation = options(goal, "review-operation-decision")["unsuccessful"]
    assert guards_match(
        goal_operation,
        {
            ("record-evidence", "review-operation"): "incomplete",
            ("record-evidence", "assessment-ordinal"): 0,
        },
    )

    validation = load_procedure("aquarium-validation-v2.yaml")
    validation_operation = options(validation, "final-review-operation-decision")[
        "unassessed"
    ]
    assert guards_match(
        validation_operation,
        {("final-review", "assessment-ordinal"): 0},
    )
    assert not guards_match(
        validation_operation,
        {("final-review", "assessment-ordinal"): 1},
    )

    current_only = options(validation, "final-route-settlement-decision")[
        "current-only"
    ]
    assert guards_match(
        current_only,
        {
            ("final-review", "prior-route-lifecycle-state"): "active-or-unknown",
            ("final-review", "route-change-readiness"): "current-route-only",
        },
    )
    assert set(options(validation, "current-route-direction-decision")) == {
        "resume-current",
        "stop",
    }


def test_completed_route_changes_keep_next_ordinal_and_finding_lineage() -> None:
    fixture = load_json("independent-review-routing-cases.json")
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
        assert case["remaining_review_authority"] == (
            "one work-unit and one confirmation"
        )

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
        ("record-evidence", "review-mode"): "remediation-eligible",
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
    for route in ("herdr", "independent-review", "waived"):
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


def test_goal_and_validation_extra_ordinals_require_current_authority() -> None:
    goal = load_procedure("aquarium-goal-v2.yaml")
    ordinal = options(goal, "assessment-ordinal-decision")["authorized-extra"]
    extra = options(goal, "assessment-extra-ordinal-decision")
    values = {
        ("record-evidence", "prior-assessment-ordinal"): 4,
        ("record-evidence", "assessment-ordinal"): 5,
        ("record-evidence", "assessment-kind"): "remediation-confirmation",
        ("record-evidence", "review-mode"): "confirmation-only",
        ("record-evidence", "extra-assessment-authority-reference"): "user authority",
        ("record-evidence", "assessment-ordinal-continuity"): {"outcome": "pass"},
    }
    assert guards_match(ordinal, values)
    assert guards_match(extra["authorized-extra"], values)
    below_minimum = dict(values)
    below_minimum[("record-evidence", "assessment-ordinal")] = 4
    assert not guards_match(extra["authorized-extra"], below_minimum)
    assert guards_match(extra["invalid-extra"], below_minimum)

    validation = load_procedure("aquarium-validation-v2.yaml")
    final_items = {
        item["id"]: item
        for item in validation["node_definitions"]["final-review-record"]["items"]
    }
    assert final_items["extra-assessment-authority-reference"]["required_when"] == [
        {"item": "prior-assessment-ordinal", "at_least": 4}
    ]
    graph = nodes(validation)
    final_sources = {
        source["node"]: set(source["items"])
        for source in graph["confirm-final-assessment-ordinal"]["evidence_from"]
    }
    assert "extra-assessment-authority-reference" in final_sources["final-review"]
    admitted = options(validation, "assessment-ordinal-decision")[
        "remediation-confirmation"
    ]
    assert guards_match(
        admitted,
        {
            ("final-review", "assessment-ordinal"): 5,
            ("final-review", "assessment-kind"): "remediation-confirmation",
            ("final-review", "review-mode"): "confirmation-only",
            ("final-review", "assessment-ordinal-continuity"): {"outcome": "pass"},
        },
    )


def test_validation_rework_authority_enters_remediation_before_reaudit() -> None:
    validation = load_procedure("aquarium-validation-v2.yaml")
    graph = nodes(validation)
    for node, option in (
        ("confirm-validation-rework-effect-authority", "authorized"),
        ("decide-gaps", "blocking-gaps"),
        ("choose-user-direction", "fix-and-review"),
        ("choose-audit-direction", "fix-and-review"),
    ):
        assert graph[node]["routes"][option] == {
            "to": "prepare-validation-pass",
            "effect": "rework",
        }
    assert graph["decide-validation-pass"]["routes"]["remediation"] == {
        "to": "remediate",
        "effect": "advance",
    }
    assert graph["remediate"]["next"] == "judge-remediation"
    assert graph["decide-remediation-groups"]["routes"]["complete"]["to"] == (
        "decide-remediation-audit-authority"
    )
    assert graph["decide-remediation-audit-authority"]["routes"]["one-shot"] == {
        "to": "re-audit",
        "effect": "advance",
    }
    scope = options(validation, "remediation-audit-scope-decision")
    for count in range(6):
        evidence = {("settle-remediation-group", "completed-review-assessments"): count}
        assert guards_match(scope["full"], evidence) is (count < 3)
        assert guards_match(scope["frozen"], evidence) is (count >= 3)
    assert graph["decide-remediation-audit-scope"]["routes"] == {
        "full": {"to": "audit", "effect": "advance"},
        "frozen": {"to": "re-audit", "effect": "advance"},
    }


def test_validation_uses_serial_operation_completion_evidence_and_blocker_gates() -> (
    None
):
    procedure = load_procedure("aquarium-validation-v2.yaml")
    graph = nodes(procedure)
    confirmation = procedure["node_definitions"][
        "remediation-confirmation-audit-record"
    ]
    confirmation_result = next(
        item for item in confirmation["items"] if item["id"] == "audit-result"
    )
    assert confirmation_result["operation_id"] == (
        "aquarium-validation-remediation-confirmation-audit"
    )
    assert confirmation_result["operation_digest"] == (
        "sha256:791d1cfb7ba42dfb7665b3784a4d7ee68ec14510d0e6c7aa0528c089069e9e9c"
    )
    assert graph["re-audit"]["use"] == "remediation-confirmation-audit-record"
    assert graph["decide-re-audit"]["routes"] == {
        "clean": {"to": "record-current-audit-basis", "effect": "advance"},
        "user-direction": {"to": "await-audit-direction", "effect": "advance"},
        "low-only": {"to": "record-audit-low-basis", "effect": "advance"},
        "incomplete": {"to": "record-incomplete", "effect": "advance"},
    }
    assert graph["decide-gaps"]["routes"]["confirmation-required"] == {
        "to": "record-confirmation-incomplete",
        "effect": "advance",
    }
    assert graph["choose-user-direction"]["routes"]["fix-and-review"] == {
        "to": "prepare-validation-pass",
        "effect": "rework",
    }
    assert graph["choose-audit-direction"]["routes"]["fix-and-review"] == {
        "to": "prepare-validation-pass",
        "effect": "rework",
    }
    assert graph["final-review"]["next"] == "confirm-final-review-route-binding"
    audit_sources = {
        source["node"]: source for source in graph["final-review"]["evidence_from"]
    }
    assert audit_sources["record-current-audit-basis"] == {
        "node": "record-current-audit-basis",
        "required": True,
        "items": ["current-audit-basis-summary"],
    }
    assert audit_sources["audit"]["required"] is False
    assert audit_sources["re-audit"]["required"] is False
    assert graph["decide-final-review-operation"]["routes"] == {
        "assessed": {
            "to": "confirm-final-assessment-ordinal",
            "effect": "advance",
        },
        "unassessed": {
            "to": "confirm-unassessed-final-review-provenance",
            "effect": "advance",
        },
    }
    assert graph["confirm-final-assessment-ordinal"]["routes"] == {
        "work-unit": {
            "to": "confirm-assessed-final-review-provenance",
            "effect": "advance",
        },
        "remediation-confirmation": {
            "to": "confirm-remediation-assessed-final-review-provenance",
            "effect": "advance",
        },
        "invalid": {"to": "record-incomplete", "effect": "advance"},
    }
    assert graph["confirm-assessed-final-review-provenance"]["routes"] == {
        "valid": {
            "to": "determine-final-backend-applicability",
            "effect": "advance",
        },
        "invalid": {"to": "record-incomplete", "effect": "advance"},
    }
    assert graph["confirm-unassessed-final-review-provenance"]["routes"] == {
        "valid": {
            "to": "confirm-final-route-settlement",
            "effect": "advance",
        },
        "invalid": {"to": "record-incomplete", "effect": "advance"},
    }
    assert graph["determine-final-backend-applicability"]["routes"] == {
        "required": {
            "to": "decide-final-backend-check",
            "effect": "advance",
        },
        "not-required": {
            "to": "confirm-final-review-findings",
            "effect": "advance",
        },
    }
    assert graph["confirm-final-route-settlement"]["routes"] == {
        "current-only": {
            "to": "choose-current-route-direction",
            "effect": "advance",
        },
        "change-safe": {
            "to": "choose-settled-route-direction",
            "effect": "advance",
        },
    }
    assert graph["choose-current-route-direction"]["routes"] == {
        "resume-current": {"to": "final-review", "effect": "rework"},
        "stop": {"to": "record-stopped", "effect": "advance"},
    }
    assert graph["choose-settled-route-direction"]["routes"] == {
        "recover": {"to": "final-review", "effect": "rework"},
        "stop": {"to": "record-stopped", "effect": "advance"},
    }
    assert graph["confirm-final-review-findings"]["routes"]["resolved"]["to"] == (
        "decide-final-review-readiness"
    )
    assert graph["decide-final-review-readiness"]["routes"] == {
        "passed": {
            "to": "judge-validation-evidence",
            "effect": "advance",
        },
        "incomplete": {
            "to": "record-review-operation-incomplete",
            "effect": "advance",
        },
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
        assessment_sources = (
            graph["assess-stopped-goal"]["evidence_from"]
            if "assess-stopped-goal" in graph
            else graph["assess-goal"]["evidence_from"]
        )
        core_sources = graph["confirm-stopped-goal-assessment-core"]["evidence_from"]
        all_sources = [*core_sources, *assessment_sources]
        selected_completion = {
            item
            for source in all_sources
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

        if name in {"aquarium-task-v2.yaml", "aquarium-goal-v2.yaml"}:
            stopped_options = options(procedure, "stopped-goal-assessment")
            stopped_values = {
                (
                    "record-stopped-goal-boundary",
                    "goal-outcome-boundary",
                ): "stopped"
            }
            assert graph["confirm-goal-assessment-core"]["routes"]["ready"]["to"] == (
                "prepare-task-assessment"
                if name == "aquarium-task-v2.yaml"
                else "prepare-goal-assessment"
            )
            assert graph["confirm-stopped-goal-boundary"]["routes"]["confirmed"][
                "to"
            ] == (
                "prepare-stopped-task-assessment"
                if name == "aquarium-task-v2.yaml"
                else "confirm-stopped-goal-assessment-core"
            )
            assert not guards_match(
                stopped_options["invalid-not-stopped"], stopped_values
            )
        else:
            stopped_options = options(procedure, "stopped-goal-assessment")
            stopped_values = {
                ("record-stopped-goal-boundary", "goal-outcome-boundary"): (
                    "stopped"
                    if name != "aquarium-validation-v2.yaml"
                    else "stopped-or-incomplete"
                )
            }
            assert not guards_match(stopped_options["achieved"], stopped_values)

        wait_sources = graph["await-user-direction"]["evidence_from"]
        wait_completion = {
            item
            for source in wait_sources
            if source["node"] == completion_node
            for item in source.get("items", [])
        }
        assert completion_items <= wait_completion


def test_task_closeout_paths_each_have_one_dominating_goal_assessment() -> None:
    task = load_procedure("aquarium-task-v2.yaml")
    graph = nodes(task)
    assessments = {
        definition_id
        for definition_id, definition in task["node_definitions"].items()
        if definition.get("assessment", {}).get("target") == "session_goal"
    }
    assert assessments == {"goal-assessment", "stopped-goal-assessment"}
    assert graph["confirm-goal-assessment-core"]["routes"]["ready"] == {
        "to": "prepare-task-assessment",
        "effect": "advance",
    }
    assert graph["confirm-stopped-goal-boundary"]["routes"]["confirmed"] == {
        "to": "prepare-stopped-task-assessment",
        "effect": "advance",
    }
    assert {route["to"] for route in graph["assess-goal"]["routes"].values()} == {
        "record-outcome"
    }
    assert graph["record-outcome"]["next"] == "approve-closeout"
    assert graph["approve-closeout"]["evidence_from"] == [
        {
            "node": "record-outcome",
            "required": True,
            "items": ["outcome-summary"],
        }
    ]
    assert graph["approve-closeout"]["routes"]["approved"] == {
        "to": "closeout",
        "effect": "advance",
    }
    assert {
        route["to"] for route in graph["assess-stopped-goal"]["routes"].values()
    } == {"record-stopped-outcome"}
    assert graph["record-stopped-outcome"]["next"] == "approve-stopped-closeout"
    assert graph["approve-stopped-closeout"]["evidence_from"] == [
        {
            "node": "record-stopped-outcome",
            "required": True,
            "items": ["outcome-summary"],
        }
    ]
    assert graph["approve-stopped-closeout"]["routes"]["approved"] == {
        "to": "stopped-closeout",
        "effect": "advance",
    }


def test_task_070_closeout_paths_each_have_one_dominating_goal_assessment() -> None:
    cases = (
        ("aquarium-goal-v2.yaml", "complete-work", "stopped"),
        (
            "aquarium-validation-v2.yaml",
            "prepare-validation-pass",
            "stopped-or-incomplete",
        ),
    )
    for name, rework_target, stopped_boundary in cases:
        procedure = load_procedure(name)
        graph = nodes(procedure)
        edges = graph_edges(procedure)
        predecessors = graph_predecessors(edges)
        entry = procedure["graph"]["entry"]
        chains = (
            (
                "confirm-goal-assessment-core",
                "assess-goal",
                "record-outcome",
                "approve-closeout",
                "closeout",
            ),
            (
                "record-stopped-goal-boundary",
                "confirm-stopped-goal-assessment-core",
                "assess-stopped-goal",
                "record-stopped-outcome",
                "approve-stopped-closeout",
                "stopped-closeout",
            ),
        )

        if name == "aquarium-goal-v2.yaml":
            chains = (
                (
                    "confirm-goal-assessment-core",
                    "prepare-goal-assessment",
                    "judge-goal",
                    "confirm-goal-assessment-applicability",
                    "assess-goal",
                    "record-outcome",
                    "approve-closeout",
                    "closeout",
                ),
                (
                    "record-stopped-goal-boundary",
                    "confirm-stopped-goal-boundary",
                    "confirm-stopped-goal-assessment-core",
                    "prepare-stopped-goal-assessment",
                    "judge-stopped-goal",
                    "confirm-stopped-goal-assessment-applicability",
                    "assess-stopped-goal",
                    "record-stopped-outcome",
                    "approve-stopped-closeout",
                    "stopped-closeout",
                ),
            )

        if name == "aquarium-validation-v2.yaml":
            chains = (
                (
                    "confirm-goal-assessment-core",
                    "prepare-validation-assessment",
                    "judge-validation",
                    "confirm-judge-validation-applicability",
                    "assess-goal",
                    "record-outcome",
                    "approve-closeout",
                    "closeout",
                ),
                (
                    "record-stopped-goal-boundary",
                    "confirm-stopped-goal-assessment-core",
                    "prepare-stopped-validation-assessment",
                    "judge-stopped-validation",
                    "confirm-judge-stopped-validation-applicability",
                    "assess-stopped-goal",
                    "record-stopped-outcome",
                    "approve-stopped-closeout",
                    "stopped-closeout",
                ),
            )

        for chain in chains:
            terminal = chain[-1]
            assert terminal in reachable_nodes(edges, entry)
            for dominator in chain[:-1]:
                assert terminal not in reachable_nodes(
                    edges, entry, without=dominator
                ), f"{name}: {dominator} does not dominate {terminal}"
            for predecessor, node_id in pairwise(chain):
                if name == "aquarium-goal-v2.yaml" and node_id in {
                    "judge-goal",
                    "judge-stopped-goal",
                }:
                    assert predecessors[node_id] == {
                        predecessor,
                        "confirm-"
                        + ("stopped-" if node_id == "judge-stopped-goal" else "")
                        + "goal-assessment-applicability",
                    }
                elif (
                    name == "aquarium-goal-v2.yaml"
                    and node_id == "prepare-stopped-goal-assessment"
                ):
                    assert predecessors[node_id] == {
                        predecessor,
                        "record-stopped-core-gaps",
                    }
                elif (
                    name == "aquarium-goal-v2.yaml"
                    and node_id == "confirm-stopped-goal-boundary"
                ):
                    assert predecessor in predecessors[node_id]
                elif name == "aquarium-validation-v2.yaml" and node_id in {
                    "judge-validation",
                    "judge-stopped-validation",
                }:
                    assert predecessors[node_id] == {
                        predecessor,
                        "confirm-" + node_id + "-applicability",
                    }
                elif name == "aquarium-validation-v2.yaml" and node_id == (
                    "prepare-stopped-validation-assessment"
                ):
                    assert predecessors[node_id] == {
                        predecessor,
                        "record-stopped-core-gaps",
                    }
                else:
                    assert predecessors[node_id] == {predecessor}

        normal_chain, stopped_chain = map(set, chains)
        assert not {
            (source, destination)
            for source in normal_chain
            for destination in edges[source] & stopped_chain
        }
        assert not {
            (source, destination)
            for source in stopped_chain
            for destination in edges[source] & normal_chain
        }

        assert {route["to"] for route in graph["assess-goal"]["routes"].values()} == {
            "record-outcome"
        }
        assert graph["record-outcome"]["next"] == "approve-closeout"
        assert graph["approve-closeout"]["routes"] == {
            "approved": {"to": "closeout", "effect": "advance"},
            "delegated": {"to": "delegated-closeout", "effect": "advance"},
            "changes-requested": {"to": rework_target, "effect": "rework"},
        }
        assert {
            route["to"] for route in graph["assess-stopped-goal"]["routes"].values()
        } == {"record-stopped-outcome"}
        assert graph["record-stopped-outcome"]["next"] == ("approve-stopped-closeout")
        assert graph["approve-stopped-closeout"]["routes"] == {
            "approved": {"to": "stopped-closeout", "effect": "advance"},
            "changes-requested": {"to": rework_target, "effect": "rework"},
        }
        stopped = options(procedure, "stopped-goal-assessment")[
            "invalid-not-stopped" if name == "aquarium-goal-v2.yaml" else "achieved"
        ]
        assert not guards_match(
            stopped,
            {
                (
                    "record-stopped-goal-boundary",
                    "goal-outcome-boundary",
                ): stopped_boundary
            },
        )


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


def test_low_blockers_keep_current_basis_and_remaining_authority() -> None:
    for name in ("task", "goal", "validation"):
        procedure = load_procedure(f"aquarium-{name}-v2.yaml")
        graph = nodes(procedure)
        destination = (
            "record-task-rework-basis"
            if name == "task"
            else f"decide-{name}-rework-authority"
        )
        assert graph["decide-low-completion"]["routes"]["blocker-found"] == {
            "to": destination,
            "effect": "advance",
        }
        authority = graph[f"decide-{name}-rework-authority"]
        assert any(
            source["node"] == "record-low-disposition"
            for source in authority["evidence_from"]
        )
        assert authority["routes"]["user-direction"]["to"] == "await-user-direction"
        assert "stop" in graph["choose-user-direction"]["routes"]
    task = load_procedure("aquarium-task-v2.yaml")
    graph = nodes(task)
    for phase in ("implementation", "verification", "documentation"):
        decision = options(task, f"{phase}-owner-decision")
        item = f"{phase}-rework-obligations"
        for count in (0, 1):
            evidence = {("review", item): 0, ("record-task-rework-basis", item): count}
            assert guards_match(decision["required"], evidence) is (count == 1)
            assert guards_match(decision["clear"], evidence) is (count == 0)
    assert graph["decide-implementation-owner"]["routes"]["required"] == {
        "to": "prepare-implementation",
        "effect": "rework",
    }
    assert "implement" not in task["manual_rework"]["allowed_targets"]
    assert "prepare-implementation" in task["manual_rework"]["allowed_targets"]


def test_task_handoff_and_low_delta_remain_selectable_at_their_consumers() -> None:
    task = load_procedure("aquarium-task-v2.yaml")
    graph = nodes(task)
    artifact = next(
        item
        for item in task["node_definitions"]["plan-record"]["items"]
        if item["id"] == "plan-handoff-artifact"
    )
    assert artifact["type"] == "artifact" and artifact["required"] is False
    for node in ("prepare-implementation", "implement"):
        assert {
            "node": "record-plan",
            "required": False,
            "items": ["plan-handoff-artifact"],
        } in graph[node]["evidence_from"]
    core_sources = graph["confirm-goal-assessment-core"]["evidence_from"]
    low = next(
        source for source in core_sources if source["node"] == "record-low-disposition"
    )
    assert {
        "before-target",
        "after-target",
        "coverage-relationship",
        "completion-assessment-summary",
        "low-disposition-verification",
    } <= set(low["items"])


def test_war_room_no_work_keeps_quality_approval_and_documentation() -> None:
    procedure = load_procedure("aquarium-war-room-v2.yaml")
    graph = nodes(procedure)
    assert graph["decide-cause"]["routes"]["no-work"] == {
        "to": "draft-no-work",
        "effect": "advance",
    }
    assert graph["draft-no-work"]["next"] == "quality"
    edges = graph_edges(procedure)
    for gate in ("quality", "decide-quality", "approve-diff", "document"):
        assert "assess-goal" not in reachable_nodes(
            edges, "draft-no-work", without=gate
        )
    for consumer in ("quality", "decide-quality", "approve-diff", "document"):
        source = next(
            item
            for item in graph[consumer]["evidence_from"]
            if item["node"] == "draft-no-work"
        )
        assert source["required"] is False
        assert source["items"] == ["proposal-summary"]
    assert "draft-no-work" in procedure["manual_rework"]["allowed_targets"]


def test_shape_quality_routes_completed_findings_to_their_owner() -> None:
    for name, definition, first, second in (
        ("design", "quality-decision", "discovery", "draft"),
        ("war-room", "quality-decision", "investigation", "proposal"),
    ):
        procedure = load_procedure(f"aquarium-{name}-v2.yaml")
        choices = options(procedure, definition)
        for outcome, first_count, second_count, expected in (
            ("pass", 0, 0, "passed"),
            ("pass", 1, 0, f"{first}-changes"),
            ("pass", 0, 1, f"{second}-changes"),
            ("pass", 1, 1, f"{first}-changes"),
            ("fail", 0, 0, "incomplete"),
            ("inconclusive", 0, 0, "incomplete"),
        ):
            values = {
                ("quality", "quality-result"): {"outcome": outcome},
                ("quality", f"unresolved-{first}-findings"): first_count,
                ("quality", f"unresolved-{second}-findings"): second_count,
            }
            assert [
                key for key, value in choices.items() if guards_match(value, values)
            ] == [expected]


def test_epic_acceptance_guards_preserve_actor_and_workflow_boundaries() -> None:
    cases = (
        ("goal", "record-evidence", "goal-kind", "member-task", True),
        ("goal", "record-evidence", "goal-kind", "pre-validation-remediation", True),
        ("goal", "record-evidence", "goal-kind", "epic-closeout", False),
        ("validation", "capture-baseline", "workflow-owner", "epic-handler", True),
        ("validation", "capture-baseline", "workflow-owner", "epic-validator", False),
    )
    for kind, owner_node, owner_item, owner, delegation_allowed in cases:
        procedure = load_procedure(f"aquarium-{kind}-v2.yaml")
        approval = options(procedure, "approval-decision")
        for actor in ("user", "epic-delegation"):
            values = {
                ("record-outcome", "acceptance-source"): actor,
                (owner_node, owner_item): owner,
            }
            assert guards_match(approval["approved"], values) == (actor == "user")
            assert guards_match(approval["delegated"], values) == (
                actor == "epic-delegation" and delegation_allowed
            )
            assert guards_match(approval["changes-requested"], values)
        assert not guards_match(approval["delegated"], {})
        assert not guards_match(
            approval["delegated"],
            {("record-outcome", "acceptance-source"): "epic-delegation"},
        )
        stopped = options(procedure, "stopped-approval-decision")
        assert "delegated" not in stopped
        for actor in ("user", "epic-delegation"):
            assert guards_match(
                stopped["approved"],
                {("record-stopped-outcome", "acceptance-source"): actor},
            ) == (actor == "user")


def test_delegated_closeout_requires_assessment_and_current_acceptance_evidence() -> (
    None
):
    for kind in ("goal", "validation"):
        procedure = load_procedure(f"aquarium-{kind}-v2.yaml")
        graph = nodes(procedure)
        edges = graph_edges(procedure)
        entry = procedure["graph"]["entry"]
        terminal = "delegated-closeout"
        assert terminal in reachable_nodes(edges, entry)
        assert graph[terminal]["terminal"] is True
        for required in ("assess-goal", "record-outcome", "approve-closeout"):
            assert terminal not in reachable_nodes(edges, entry, without=required)
        assert graph_predecessors(edges)[terminal] == {"approve-closeout"}
        assert graph["approve-closeout"]["routes"]["delegated"] == {
            "to": terminal,
            "effect": "advance",
        }
        for consumer, source in (
            ("approve-closeout", "record-outcome"),
            ("delegated-closeout", "record-outcome"),
            ("approve-stopped-closeout", "record-stopped-outcome"),
        ):
            evidence = next(
                reference
                for reference in graph[consumer]["evidence_from"]
                if reference["node"] == source
            )
            assert evidence["required"] is True
            assert {
                "acceptance-source",
                "acceptance-authority",
                "accepted-target",
            } <= set(evidence["items"])
        fields = {
            item["id"]: item
            for item in procedure["node_definitions"]["outcome-record"]["items"]
        }
        for name in ("acceptance-source", "acceptance-authority", "accepted-target"):
            assert fields[name]["required"] is True
        for name in ("acceptance-authority", "accepted-target"):
            assert fields[name]["min_length"] > 0


def test_herdr_migration_preserves_control_contracts_and_prior_snapshots() -> None:
    prose_fields = {
        "title",
        "objective",
        "prompt",
        "help",
        "label",
        "criteria",
        "evidence_guidance",
        "instructions",
        "intent",
    }

    def control(value: object) -> object:
        if isinstance(value, dict):
            return {
                control(key): control(item)
                for key, item in value.items()
                if key not in prose_fields
            }
        if isinstance(value, list):
            return [control(item) for item in value]
        if isinstance(value, str):
            return value.replace("herdr", "orca").replace("Herdr", "Orca")
        return value

    for kind, previous_version, version_step in (
        ("task", 22, 2),
        ("task", 23, 1),
        ("goal", 25, 2),
        ("goal", 26, 1),
        ("validation", 24, 2),
        ("validation", 25, 1),
    ):
        current = (
            yaml.safe_load((FIXTURES / "aquarium-task-v24.yaml").read_bytes())
            if kind == "task"
            else yaml.safe_load((FIXTURES / "aquarium-goal-v27.yaml").read_bytes())
            if kind == "goal"
            else yaml.safe_load(
                (FIXTURES / "aquarium-validation-v26.yaml").read_bytes()
            )
        )
        previous = yaml.safe_load(
            (FIXTURES / f"aquarium-{kind}-v{previous_version}.yaml").read_bytes()
        )
        assert current["id"] == previous["id"]
        assert int(current["version"]) == int(previous["version"]) + version_step
        for definition in current["node_definitions"].values():
            for item in definition.get("items", []):
                if item["id"] == "prior-review-route":
                    assert item["choices"] == [
                        "not-applicable",
                        "mulgae",
                        "orca",
                        "herdr",
                        "independent-review",
                        "waived",
                    ]
                    # Historical admission is the only additional control change.
                    item["choices"].remove("orca")
                elif item["type"] == "choice":
                    assert "orca" not in item["choices"]
        current.pop("version")
        previous.pop("version")
        # Compare executable item schemas, guards, routes, operations and ordering.
        # Wording is excluded; peer routes and native operation digests remain exact.
        assert control(current) == control(previous)


def test_published_plugin_keeps_only_the_herdr_native_review_entrypoint() -> None:
    plugin = json.loads(
        (ROOT / "plugins/aquarium/.codex-plugin/plugin.json").read_text()
    )
    skills = ROOT / "plugins/aquarium" / plugin["skills"]
    assert (skills / "herdr-review/SKILL.md").is_file()
    assert (skills / "herdr-review/agents/openai.yaml").is_file()
    assert not (skills / "orca-review").exists()
    assert not (ROOT / "plugins/aquarium/references/orca-supervision.md").exists()


def test_task_candidate_delivery_requires_a_separate_native_judge() -> None:
    task = load_procedure("aquarium-task-v2.yaml")
    graph = nodes(task)
    checkpoints = (
        ("record-plan", "judge-plan", "decide-plan-assessment"),
        ("implement", "judge-implementation", "decide-implementation-assessment"),
        ("refine", "judge-refinement", "decide-refinement-assessment"),
        ("verify", "judge-verification", "decide-verification"),
        ("document", "judge-documentation", "decide-documentation-assessment"),
        ("review", "judge-review", "confirm-review-completion"),
        ("prepare-task-assessment", "judge-task", "assess-goal"),
        (
            "prepare-stopped-task-assessment",
            "judge-stopped-task",
            "assess-stopped-goal",
        ),
    )
    for candidate, judge, decision in checkpoints:
        for node_id, role in (
            (candidate, "aquarium-worker/v1"),
            (judge, "aquarium-goal-judge/v1"),
        ):
            placement = graph[node_id]
            definition = task["node_definitions"][placement["use"]]
            assert definition["type"] == "action"
            assert placement["delegation"]["role_ref"] == role
            assert placement["delegation"]["binding_ref"] == "aquarium-native"
            assert placement["delegation"]["after_accept"] == "retain"
        selected = {
            item
            for source in graph[judge]["evidence_from"]
            if source["node"] == candidate and source["required"]
            for item in source.get("items", [])
        }
        assert "worker-handoff" in selected
        assert judge not in reachable_nodes(
            graph_edges(task), task["graph"]["entry"], without=candidate
        )
        assert decision not in reachable_nodes(
            graph_edges(task), task["graph"]["entry"], without=judge
        )
    for placement in graph.values():
        if task["node_definitions"][placement["use"]]["type"] == "decision":
            assert "delegation" not in placement


def test_task_semantic_pass_rejects_missing_stale_and_incomplete_reports() -> None:
    task = load_procedure("aquarium-task-v2.yaml")
    graph = nodes(task)
    for suffix, decision in (
        ("plan", "decide-plan-assessment"),
        ("implementation", "decide-implementation-assessment"),
        ("refinement", "decide-refinement-assessment"),
        ("verification", "decide-verification"),
        ("documentation", "decide-documentation-assessment"),
        ("review", "confirm-review-completion"),
    ):
        judge = "judge-" + suffix
        actual = options(task, graph[decision]["use"])
        passing = actual["complete" if suffix == "review" else "passed"]
        values = {
            (judge, "judge-applicability"): {"outcome": "pass"},
            (judge, "judge-verdict"): "pass",
            (judge, "judge-unmet-criteria"): 0,
            (judge, "judge-unverified-criteria"): 0,
        }
        assert guards_match(passing, values)
        assert not guards_match(passing, {})
        for key in values:
            missing = dict(values)
            del missing[key]
            assert not guards_match(passing, missing)
        for item, value in (
            ("judge-applicability", {"outcome": "fail"}),
            ("judge-applicability", {"outcome": "inconclusive"}),
            ("judge-verdict", "rework"),
            ("judge-verdict", "evidence-needed"),
            ("judge-unmet-criteria", 1),
            ("judge-unverified-criteria", 1),
        ):
            rejected = dict(values)
            rejected[judge, item] = value
            assert not guards_match(passing, rejected)
        correction = dict(values)
        correction[judge, "judge-verdict"] = "rework"
        correction[judge, "judge-unmet-criteria"] = 1
        assert guards_match(actual["rework"], correction)
        evidence = dict(values)
        evidence[judge, "judge-verdict"] = "evidence-needed"
        evidence[judge, "judge-unverified-criteria"] = 1
        assert guards_match(actual["evidence-needed"], evidence)
        assert (
            graph[decision]["routes"]["rework"]["to"]
            != graph[decision]["routes"]["evidence-needed"]["to"]
        )


def test_task_semantic_followup_cannot_create_correction_or_review_authority() -> None:
    task = load_procedure("aquarium-task-v2.yaml")
    graph = nodes(task)
    for node_id, placement in graph.items():
        if (
            not node_id.startswith("confirm-")
            or not node_id.endswith("-authority")
            or "semantic" not in placement["use"]
        ):
            continue
        actual = options(task, placement["use"])
        source = placement["evidence_from"][0]["node"]
        assert not guards_match(actual["authorized"], {})
        for outcome in ("fail", "inconclusive"):
            values = {(source, "semantic-authority"): {"outcome": outcome}}
            assert not guards_match(actual["authorized"], values)
            assert guards_match(actual["blocked"], values)
        assert placement["routes"]["blocked"] == {"to": source, "effect": "rework"}
        assert placement["routes"]["authorized"]["effect"] == "rework"
    assert (
        graph["confirm-review-completion"]["routes"]["rework"]["to"]
        == "record-task-rework-basis"
    )
    assert graph["record-task-rework-basis"]["next"] == "decide-task-rework-authority"


def test_final_task_pass_is_exact_and_stopped_goal_cannot_achieve() -> None:
    task = load_procedure("aquarium-task-v2.yaml")
    actual = options(task, "goal-assessment")["achieved"]
    values = {
        ("judge-task", "judge-goal-outcome"): "achieved",
        ("judge-task", "judge-verdict"): "pass",
        ("judge-task", "judge-unmet-criteria"): 0,
        ("judge-task", "judge-unverified-criteria"): 0,
    }
    assert guards_match(actual, values)
    for key in values:
        missing = dict(values)
        del missing[key]
        assert not guards_match(actual, missing)
    stopped = options(task, "stopped-goal-assessment")
    assert "achieved" not in stopped
    assert not guards_match(
        stopped["invalid-not-stopped"],
        {("record-stopped-goal-boundary", "goal-outcome-boundary"): "stopped"},
    )
    for suffix in ("task", "stopped-task"):
        placement = nodes(task)["confirm-" + suffix + "-assessment-applicability"]
        applicability = options(task, placement["use"])["current"]
        assert not guards_match(applicability, {})
        assert not guards_match(
            applicability,
            {("judge-" + suffix, "judge-applicability"): {"outcome": "fail"}},
        )


def test_task_and_goal_roles_bind_complete_frozen_operative_bytes() -> None:
    import base64

    task = load_procedure("aquarium-task-v2.yaml")
    dependencies = [
        "plugins/aquarium/references/" + name
        for name in (
            "agent-orchestration.md",
            "native-agent-mappings.md",
            "evidence-residency.md",
            "review-routing-contract.md",
            "review-intent-contract.md",
            "finding-disposition.md",
            "ouroboros-integration.md",
            "design-gates.md",
        )
    ]
    roles = {
        "aquarium-worker/v1": "plugins/aquarium/references/worker-guidance.md",
        "aquarium-goal-judge/v1": "plugins/aquarium/skills/goal-judge/SKILL.md",
    }
    digests = {}
    for role, path in roles.items():
        files = []
        for relative in sorted([path, *dependencies]):
            content = (ROOT / relative).read_bytes()
            files.append(
                {
                    "path": relative,
                    "size_bytes": len(content),
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "content_base64": base64.b64encode(content).decode("ascii"),
                }
            )
        snapshot = {
            "schema": "aquarium.prepared-role-snapshot/v1",
            "role_path": path,
            "files": files,
        }
        content = json.dumps(
            snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("ascii")
        digests[role] = "sha256:" + hashlib.sha256(content).hexdigest()
    for procedure in (
        task,
        load_procedure("aquarium-goal-v2.yaml"),
        load_procedure("aquarium-validation-v2.yaml"),
    ):
        for placement in nodes(procedure).values():
            if declaration := placement.get("delegation"):
                assert (
                    declaration["role_snapshot_digest"]
                    == digests[declaration["role_ref"]]
                )
                assert declaration["max_rounds"] == 32
    assert digests["aquarium-worker/v1"] != digests["aquarium-goal-judge/v1"]


def test_goal_native_candidates_and_judges_dominate_semantic_progress() -> None:
    goal = load_procedure("aquarium-goal-v2.yaml")
    graph = nodes(goal)
    edges = graph_edges(goal)
    checkpoints = (
        ("complete-work", "judge-work", "decide-work-assessment"),
        ("record-evidence", "judge-goal-evidence", "decide-goal-evidence-assessment"),
        ("prepare-goal-assessment", "judge-goal", "assess-goal"),
        (
            "prepare-stopped-goal-assessment",
            "judge-stopped-goal",
            "assess-stopped-goal",
        ),
    )
    expected = set()
    for candidate, judge, decision in checkpoints:
        expected.update((candidate, judge))
        for node_id, role in (
            (candidate, "aquarium-worker/v1"),
            (judge, "aquarium-goal-judge/v1"),
        ):
            assert goal["node_definitions"][graph[node_id]["use"]]["type"] == "action"
            declaration = graph[node_id]["delegation"]
            assert declaration["binding_ref"] == "aquarium-native"
            assert declaration["role_ref"] == role
            assert declaration["after_accept"] == "retain"
            assert declaration["max_rounds"] == 32
        selected = {
            item
            for source in graph[judge]["evidence_from"]
            if source["node"] == candidate and source["required"]
            for item in source.get("items", [])
        }
        assert "worker-handoff" in selected
        assert judge not in reachable_nodes(
            edges, goal["graph"]["entry"], without=candidate
        )
        assert decision not in reachable_nodes(
            edges, goal["graph"]["entry"], without=judge
        )
    assert {
        node_id for node_id, node in graph.items() if "delegation" in node
    } == expected
    assert (
        graph["decide-operational-evidence"]["routes"]["passed"]["to"]
        == "judge-goal-evidence"
    )
    assert (
        graph["decide-goal-evidence-assessment"]["routes"]["passed"]["to"]
        == "confirm-completion-assessment"
    )
    for dominator in (
        "confirm-review-route-binding",
        "confirm-completed-assessment-ordinal",
        "confirm-independent-review-finding-validity",
    ):
        # Other admitted providers and the narrow closeout substitute have their own paths.
        assert "judge-goal-evidence" in reachable_nodes(edges, dominator)
    assert "assess-stopped-goal" in reachable_nodes(
        edges, goal["graph"]["entry"], without="judge-goal-evidence"
    )


def test_goal_stopped_evidence_repair_cannot_reopen_ordinary_work() -> None:
    goal = load_procedure("aquarium-goal-v2.yaml")
    graph = nodes(goal)
    edges = graph_edges(goal)
    reached = reachable_nodes(
        edges,
        "confirm-stopped-goal-boundary",
        without="approve-stopped-closeout",
    )
    assert not reached & {
        "complete-work",
        "judge-work",
        "record-evidence",
        "confirm-review-route-binding",
        "judge-goal-evidence",
        "prepare-goal-assessment",
        "judge-goal",
        "assess-goal",
        "closeout",
        "delegated-closeout",
    }
    repair = graph["confirm-stopped-goal-assessment-core"]["routes"]["needs-rework"]
    assert "assess-stopped-goal" in reachable_nodes(edges, repair["to"])
    for required in ("prepare-stopped-goal-assessment", "judge-stopped-goal"):
        assert "assess-stopped-goal" not in reachable_nodes(
            edges,
            repair["to"],
            without=required,
        )


def test_goal_semantic_pass_rejects_incomplete_or_inapplicable_reports() -> None:
    goal = load_procedure("aquarium-goal-v2.yaml")
    graph = nodes(goal)
    for judge, decision in (
        ("judge-work", "decide-work-assessment"),
        ("judge-goal-evidence", "decide-goal-evidence-assessment"),
    ):
        actual = options(goal, graph[decision]["use"])
        values = {
            (judge, "judge-applicability"): {"outcome": "pass"},
            (judge, "judge-verdict"): "pass",
            (judge, "judge-unmet-criteria"): 0,
            (judge, "judge-unverified-criteria"): 0,
        }
        assert guards_match(actual["passed"], values)
        for key in values:
            missing = dict(values)
            del missing[key]
            assert not guards_match(actual["passed"], missing)
        for item, value in (
            ("judge-applicability", {"outcome": "fail"}),
            ("judge-applicability", {"outcome": "inconclusive"}),
            ("judge-verdict", "rework"),
            ("judge-verdict", "evidence-needed"),
            ("judge-unmet-criteria", 1),
            ("judge-unverified-criteria", 1),
        ):
            rejected = dict(values)
            rejected[judge, item] = value
            assert not guards_match(actual["passed"], rejected)
        correction = dict(values)
        correction[judge, "judge-verdict"] = "rework"
        correction[judge, "judge-unmet-criteria"] = 1
        assert guards_match(actual["rework"], correction)
        evidence = dict(values)
        evidence[judge, "judge-verdict"] = "evidence-needed"
        evidence[judge, "judge-unverified-criteria"] = 1
        assert guards_match(actual["evidence-needed"], evidence)
        assert (
            graph[decision]["routes"]["rework"]["to"]
            != graph[decision]["routes"]["evidence-needed"]["to"]
        )


def test_goal_followup_needs_exact_effect_authority_after_mode_classification() -> None:
    goal = load_procedure("aquarium-goal-v2.yaml")
    graph = nodes(goal)
    for node_id in (
        "confirm-work-followup-authority",
        "confirm-work-evidence-authority",
        "confirm-goal-evidence-evidence-authority",
        "confirm-goal-rework-effect-authority",
    ):
        placement = graph[node_id]
        actual = options(goal, placement["use"])
        source = placement["evidence_from"][0]["node"]
        assert not guards_match(actual["authorized"], {})
        for outcome in ("fail", "inconclusive"):
            values = {(source, "semantic-authority"): {"outcome": outcome}}
            assert not guards_match(actual["authorized"], values)
            assert guards_match(actual["blocked"], values)
        assert guards_match(
            actual["authorized"], {(source, "semantic-authority"): {"outcome": "pass"}}
        )
        assert placement["routes"]["blocked"] == {"to": source, "effect": "rework"}
    assert (
        graph["decide-goal-evidence-assessment"]["routes"]["rework"]["to"]
        == "decide-goal-rework-authority"
    )
    assert (
        graph["decide-goal-rework-authority"]["routes"]["remediation"]["to"]
        == "record-goal-rework-basis"
    )
    assert (
        graph["choose-user-direction"]["routes"]["fix-and-review"]["to"]
        == "record-goal-rework-basis"
    )
    assert graph["confirm-goal-rework-effect-authority"]["routes"]["authorized"] == {
        "to": "complete-work",
        "effect": "rework",
    }
    assert all(
        source["node"] != "record-evidence"
        for source in graph["record-work-followup"]["evidence_from"]
    )


def test_final_epic_gap_blocks_achievement_and_closeout_substitute_stays_current() -> (
    None
):
    goal = load_procedure("aquarium-goal-v2.yaml")
    achieved = options(goal, "goal-assessment")["achieved"]
    values = {
        ("judge-goal", "judge-goal-outcome"): "achieved",
        ("judge-goal", "judge-verdict"): "pass",
        ("judge-goal", "judge-unmet-criteria"): 0,
        ("judge-goal", "judge-unverified-criteria"): 0,
    }
    assert guards_match(achieved, values)
    for item in ("judge-unmet-criteria", "judge-unverified-criteria"):
        seam_gap = dict(values)
        seam_gap["judge-goal", item] = 1
        assert not guards_match(achieved, seam_gap)
    for key in values:
        missing = dict(values)
        del missing[key]
        assert not guards_match(achieved, missing)
    stopped = options(goal, "stopped-goal-assessment")
    assert "achieved" not in stopped
    assert not guards_match(
        stopped["invalid-not-stopped"],
        {("record-stopped-goal-boundary", "goal-outcome-boundary"): "stopped"},
    )
    graph = nodes(goal)
    for suffix in ("", "stopped-"):
        placement = graph["confirm-" + suffix + "goal-assessment-applicability"]
        current = options(goal, placement["use"])["current"]
        judge = "judge-" + suffix + "goal"
        assert not guards_match(current, {})
        for outcome in ("fail", "inconclusive"):
            assert not guards_match(
                current, {(judge, "judge-applicability"): {"outcome": outcome}}
            )
    substitute = options(goal, "closeout-substitute-applicability-decision")
    for outcome in ("fail", "inconclusive"):
        binding = {
            ("record-closeout-substitute", "closeout-substitute-applicability"): {
                "outcome": outcome
            }
        }
        assert not guards_match(substitute["current"], binding)
        assert guards_match(substitute["invalid"], binding)
    assert (
        graph["record-closeout-substitute"]["next"]
        == "confirm-closeout-substitute-applicability"
    )


def test_validation_worker_judge_pairs_dominate_their_semantic_decisions() -> None:
    validation = load_procedure("aquarium-validation-v2.yaml")
    graph = nodes(validation)
    edges = graph_edges(validation)
    checkpoints = (
        ("audit", "judge-audit", "decide-gaps"),
        ("remediate", "judge-remediation", "settle-remediation-group"),
        ("re-audit", "judge-re-audit", "decide-re-audit"),
        (
            "final-review",
            "judge-validation-evidence",
            "confirm-completion-assessment",
        ),
        ("prepare-validation-assessment", "judge-validation", "assess-goal"),
        (
            "prepare-stopped-validation-assessment",
            "judge-stopped-validation",
            "assess-stopped-goal",
        ),
    )
    expected = set()
    for candidate, judge, consumer in checkpoints:
        expected.update((candidate, judge))
        for node_id, role in (
            (candidate, "aquarium-worker/v1"),
            (judge, "aquarium-goal-judge/v1"),
        ):
            assert validation["node_definitions"][graph[node_id]["use"]]["type"] == (
                "action"
            )
            binding = graph[node_id]["delegation"]
            assert binding["role_ref"] == role
            assert binding["binding_ref"] == "aquarium-native"
            assert binding["max_rounds"] == 32
            assert binding["after_accept"] == "retain"
        assert judge not in reachable_nodes(
            edges, validation["graph"]["entry"], without=candidate
        )
        assert consumer not in reachable_nodes(
            edges, validation["graph"]["entry"], without=judge
        )
        selected = {
            item
            for source in graph[judge]["evidence_from"]
            if source["node"] == candidate and source["required"]
            for item in source.get("items", [])
        }
        assert "worker-handoff" in selected
    assert {key for key, node in graph.items() if "delegation" in node} == expected
    for node in graph.values():
        if validation["node_definitions"][node["use"]]["type"] == "decision":
            assert "delegation" not in node
    assert graph["decide-final-review-readiness"]["routes"]["passed"]["to"] == (
        "judge-validation-evidence"
    )


def test_validation_faithful_negative_audit_preserves_original_gap_routing() -> None:
    validation = load_procedure("aquarium-validation-v2.yaml")
    graph = nodes(validation)
    for audit, judge, gate, destination in (
        ("audit", "judge-audit", "confirm-audit-checkpoint", "decide-gaps"),
        (
            "re-audit",
            "judge-re-audit",
            "confirm-re-audit-checkpoint",
            "decide-re-audit",
        ),
    ):
        ready = options(validation, graph[gate]["use"])["ready"]
        negative = {
            (judge, "judge-applicability"): {"outcome": "pass"},
            (judge, "judge-checkpoint-result"): {"outcome": "pass"},
            (judge, "judge-verdict"): "rework",
            (judge, "judge-unmet-criteria"): 2,
            (judge, "judge-unverified-criteria"): 1,
        }
        assert guards_match(ready, negative)
        assert graph[gate]["routes"]["ready"]["to"] == destination
        for item in ("judge-applicability", "judge-checkpoint-result"):
            for outcome in ("fail", "inconclusive"):
                invalid = dict(negative)
                invalid[judge, item] = {"outcome": outcome}
                assert not guards_match(ready, invalid)
            missing = dict(negative)
            del missing[judge, item]
            assert not guards_match(ready, missing)
        basis = {
            (audit, "audit-result"): {"outcome": "pass"},
            (audit, "blocking-gap-count"): 1,
            (audit, "eligible-low-gap-count"): 0,
            (audit, "confirmation-needed-gap-count"): 0,
            (audit, "blocking-rework-authority"): "current-envelope",
            (audit, "confirmed-gap-count"): 1,
            (audit, "direction-required-gap-count"): 1,
        }
        gap_options = options(validation, graph[destination]["use"])
        expected = "blocking-gaps" if audit == "audit" else "user-direction"
        assert guards_match(gap_options[expected], basis)
        assert not guards_match(gap_options["clean"], basis)
        followup = graph["record-" + audit + "-followup"]
        assert "final-review" not in {
            source["node"] for source in followup["evidence_from"]
        }


def test_validation_followup_and_primary_group_settlement_require_authority() -> None:
    validation = load_procedure("aquarium-validation-v2.yaml")
    graph = nodes(validation)
    for stage, record in (
        ("audit", "record-audit-followup"),
        ("re-audit", "record-re-audit-followup"),
        ("remediation", "record-remediation-followup"),
        ("remediation-evidence", "record-remediation-evidence"),
        ("validation-evidence", "record-validation-evidence-followup"),
        ("validation-rework-effect", "record-validation-rework-basis"),
    ):
        decision = (
            "confirm-validation-rework-effect-authority"
            if stage == "validation-rework-effect"
            else "confirm-" + stage + "-followup-authority"
        )
        admitted = options(validation, graph[decision]["use"])["authorized"]
        assert not guards_match(admitted, {})
        for outcome in ("pass", "fail", "inconclusive"):
            assert guards_match(
                admitted, {(record, "semantic-authority"): {"outcome": outcome}}
            ) is (outcome == "pass")
    settlement = "settle-remediation-group"
    assert "delegation" not in graph[settlement]
    verified = options(validation, "confirm-remediation-group-settlement")["verified"]
    assert not guards_match(verified, {})
    for outcome in ("pass", "fail", "inconclusive"):
        assert guards_match(
            verified, {(settlement, "group-settlement-result"): {"outcome": outcome}}
        ) is (outcome == "pass")
    edges = graph_edges(validation)
    for consumer in ("decide-remediation-audit-authority", "re-audit"):
        for required in (
            "judge-remediation",
            "settle-remediation-group",
            "confirm-remediation-group-settlement",
            "decide-remediation-groups",
        ):
            assert consumer not in reachable_nodes(edges, "remediate", without=required)
    groups = options(validation, "decide-remediation-groups")
    for remaining in (0, 1, 3):
        values = {(settlement, "remaining-group-count"): remaining}
        assert guards_match(groups["complete"], values) is (remaining == 0)
        assert guards_match(groups["next-group"], values) is (remaining > 0)
    assert graph["decide-remediation-groups"]["routes"]["next-group"] == {
        "to": "remediate",
        "effect": "rework",
    }
    for consumer in ("audit", "re-audit", "decide-remediation-audit-authority"):
        sources = {
            source["node"]: source for source in graph[consumer]["evidence_from"]
        }
        assert "remediate" not in sources
        assert "remediation-summary" in sources[settlement]["items"]


def test_validation_current_judge_report_and_integration_veto_are_required() -> None:
    validation = load_procedure("aquarium-validation-v2.yaml")
    graph = nodes(validation)
    for judge, decision in (
        ("judge-validation-evidence", "decide-validation-evidence-assessment"),
    ):
        passed = options(validation, graph[decision]["use"])["passed"]
        values = {
            (judge, "judge-applicability"): {"outcome": "pass"},
            (judge, "judge-verdict"): "pass",
            (judge, "judge-unmet-criteria"): 0,
            (judge, "judge-unverified-criteria"): 0,
        }
        assert guards_match(passed, values)
        for item, value in (
            ("judge-applicability", {"outcome": "fail"}),
            ("judge-applicability", {"outcome": "inconclusive"}),
            ("judge-verdict", "rework"),
            ("judge-verdict", "evidence-needed"),
            ("judge-unmet-criteria", 1),
            ("judge-unverified-criteria", 1),
        ):
            rejected = dict(values)
            rejected[judge, item] = value
            assert not guards_match(passed, rejected)
        for key in values:
            missing = dict(values)
            del missing[key]
            assert not guards_match(passed, missing)
    achieved = options(validation, "goal-assessment")["achieved"]
    final = {
        ("judge-validation", "judge-goal-outcome"): "achieved",
        ("judge-validation", "judge-verdict"): "pass",
        ("judge-validation", "judge-unmet-criteria"): 0,
        ("judge-validation", "judge-unverified-criteria"): 0,
        ("final-review", "current-applicable-blockers"): 0,
        ("final-review", "required-evidence-gaps"): 0,
    }
    assert guards_match(achieved, final)
    for item, value in (
        ("judge-goal-outcome", "not-achieved"),
        ("judge-verdict", "rework"),
        ("judge-unmet-criteria", 1),
        ("judge-unverified-criteria", 1),
    ):
        veto = dict(final)
        veto["judge-validation", item] = value
        assert not guards_match(achieved, veto)
    for judge in ("judge-validation", "judge-stopped-validation"):
        current = options(validation, "confirm-" + judge + "-applicability")["current"]
        assert not guards_match(current, {})
        assert not guards_match(
            current, {(judge, "judge-applicability"): {"outcome": "fail"}}
        )


def test_validation_stopped_evidence_repair_stays_inside_stopped_assessment() -> None:
    validation = load_procedure("aquarium-validation-v2.yaml")
    graph = nodes(validation)
    edges = graph_edges(validation)
    reached = reachable_nodes(
        edges, "record-stopped-goal-boundary", without="approve-stopped-closeout"
    )
    assert not reached & {
        "audit",
        "remediate",
        "re-audit",
        "final-review",
        "confirm-final-review-route-binding",
        "judge-validation-evidence",
        "prepare-validation-assessment",
        "judge-validation",
        "assess-goal",
        "closeout",
        "delegated-closeout",
    }
    repair = graph["confirm-stopped-goal-assessment-core"]["routes"]["needs-rework"]
    assert repair == {"to": "record-stopped-core-gaps", "effect": "advance"}
    assert "assess-stopped-goal" in reachable_nodes(edges, repair["to"])
    for required in (
        "prepare-stopped-validation-assessment",
        "judge-stopped-validation",
        "confirm-judge-stopped-validation-applicability",
    ):
        assert "assess-stopped-goal" not in reachable_nodes(
            edges, repair["to"], without=required
        )
    worker_sources = {
        source["node"]: source
        for source in graph["prepare-stopped-validation-assessment"]["evidence_from"]
    }
    assert worker_sources["capture-baseline"]["required"] is True
    assert worker_sources["record-stopped-goal-boundary"]["required"] is True
    for optional in (
        "final-review",
        "judge-validation-evidence",
        "settle-remediation-group",
        "record-low-disposition",
        "record-current-audit-basis",
    ):
        assert worker_sources[optional]["required"] is False
    core_sources = {
        source["node"]: source
        for source in graph["confirm-stopped-goal-assessment-core"]["evidence_from"]
    }
    assert core_sources["record-confirmation-incomplete"]["required"] is False
    assert not guards_match(
        options(validation, "stopped-goal-assessment")["achieved"],
        {
            (
                "record-stopped-goal-boundary",
                "goal-outcome-boundary",
            ): "stopped-or-incomplete"
        },
    )


def test_validation_group_repair_keeps_full_original_epic_gaps_negative() -> None:
    validation = load_procedure("aquarium-validation-v2.yaml")
    graph = nodes(validation)
    choices = options(validation, "decide-remediation-assessment")
    judge = "judge-remediation"
    remaining_epic_gap = {
        (judge, "judge-applicability"): {"outcome": "pass"},
        (judge, "judge-verdict"): "rework",
        (judge, "judge-unmet-criteria"): 1,
        (judge, "judge-unverified-criteria"): 1,
        (judge, "judge-group-result"): {"outcome": "pass"},
    }
    assert guards_match(choices["passed"], remaining_epic_gap)
    assert graph["decide-remediation-assessment"]["routes"]["passed"]["to"] == (
        "settle-remediation-group"
    )
    for outcome, expected in (("fail", "rework"), ("inconclusive", "evidence-needed")):
        unrepaired = dict(remaining_epic_gap)
        unrepaired[judge, "judge-group-result"] = {"outcome": outcome}
        assert not guards_match(choices["passed"], unrepaired)
        assert guards_match(choices[expected], unrepaired)
    for item in ("judge-group-result", "judge-applicability"):
        missing = dict(remaining_epic_gap)
        del missing[judge, item]
        assert not guards_match(choices["passed"], missing)
    stale = dict(remaining_epic_gap)
    stale[judge, "judge-applicability"] = {"outcome": "fail"}
    assert not guards_match(choices["passed"], stale)
    assert guards_match(choices["inapplicable"], stale)
    selected = {
        item
        for source in graph["settle-remediation-group"]["evidence_from"]
        if source["node"] == judge and source["required"]
        for item in source.get("items", [])
    }
    assert {
        "judge-group-result",
        "judge-verdict",
        "judge-unmet-criteria",
        "judge-unverified-criteria",
    } <= selected
    schema = validation["node_definitions"][graph[judge]["use"]]
    item = next(i for i in schema["items"] if i["id"] == "judge-group-result")
    assert item["required"] is True
    assert item["accepted_outcomes"] == ["pass", "fail", "inconclusive"]
    assert graph["decide-remediation-assessment"]["routes"]["rework"]["to"] == (
        "record-remediation-followup"
    )
    assert graph["decide-remediation-assessment"]["routes"]["evidence-needed"][
        "to"
    ] == ("record-remediation-evidence")
