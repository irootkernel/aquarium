from __future__ import annotations

import hashlib
import importlib.util
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
            "32",
            "79a1430528934d2941551432703a68be28047bc3e8095bc52acf24c7a057466f",
            "aquarium-task-v31.yaml",
            "90c8e7df6a20f8b27134be4a3507db49af4de23b5506cd7a2bfe9ae2a2836731",
        ),
        (
            "aquarium-goal-v2.yaml",
            "35",
            "99ae1a42372ec91c8de98cfc61e99c1defc4c99615610bd598c57418c01ea9b5",
            "aquarium-goal-v34.yaml",
            "8ae119c01a94dae12b02ff17ddee6aab90f377aadd0bc3bb08e701861e87f0cc",
        ),
        (
            "aquarium-validation-v2.yaml",
            "34",
            "23ce1dff7afe24fc3e2aa0438db6e9c3b7a162f1e131061181018d5ec80a769a",
            "aquarium-validation-v33.yaml",
            "aa9bc9da3445c795af71bcc9f558977ec9e53fa48391335dbc3a493159eabba6",
        ),
        (
            "aquarium-design-v2.yaml",
            "11",
            "3ca2e4d6bd7506033a575eada996a15853334ec5e9570b86894e7ded28e94a08",
            "aquarium-design-v10.yaml",
            "932f0f1e9625a029c3d5a553ce82bd37856a57e119e612c9bd1e966cb488ccd0",
        ),
        (
            "aquarium-war-room-v2.yaml",
            "11",
            "07e0f59d3681b37584199ba94bb37a3c0d0ead7f527b1af934cac0202f13dcc9",
            "aquarium-war-room-v10.yaml",
            "e370766f3ef8e057b818eca42e2757844950b4536a3d7ac8c41624154ec41cd2",
        ),
    )
    for current_name, version, current_digest, prior_name, prior_digest in identities:
        assert load_procedure(current_name)["version"] == version
        assert (
            hashlib.sha256((PROCEDURES / current_name).read_bytes()).hexdigest()
            == current_digest
        )
        assert (
            hashlib.sha256((FIXTURES / prior_name).read_bytes()).hexdigest()
            == prior_digest
        )


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
        f"C-{index:02d}" for index in range(1, 18)
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
        f"TR-{index:02d}" for index in range(1, 19)
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
            "confirm-local-corrections-settled"
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
    assert task["version"] == "32"

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
        prior_selected = {
            (
                node,
                "hardening-deferral-native-binding-sha256"
                if item == "hardening-deferral-native-target-sha256"
                else item,
            )
            for node, item in prior_selected
        }
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
        "changed": {"to": "confirm-changed-review-continuity", "effect": "advance"},
        "new-review": {"to": "authorize-new-mulgae-review", "effect": "advance"},
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
        "new-review-current-route",
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
        "new-review-current-route",
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
        "sha256:428c03483fc0178e990d9be72ce5283b6d7588479c711ac3347e6bbd639667a9"
    )

    entry = options(task, "review-route-entry-decision")
    for option_id in (
        "continued",
        "resumed",
        "new-review",
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
            "hardening-deferral-native-binding-sha256",
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
        ("record-hardening-deferral", "hardening-deferral-native-binding-sha256"),
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
        "new-review-current-route": {
            "to": "authorize-new-mulgae-review",
            "effect": "advance",
        },
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
            assert "delegation" not in placement
        selected = {
            item
            for source in graph[judge]["evidence_from"]
            if source["node"] == candidate and source["required"]
            for item in source.get("items", [])
        }
        assert (
            "candidate-evidence"
            if candidate.startswith("prepare-")
            else "worker-handoff"
        ) in selected
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
        ("verification", "decide-verification"),
        ("documentation", "decide-documentation-assessment"),
        ("review", "confirm-review-completion"),
    ):
        judge = "judge-" + suffix
        actual = options(task, graph[decision]["use"])
        passing = actual["complete" if suffix == "review" else "passed"]
        values = {
            (judge, "judge-applicability"): {"outcome": "pass"},
            (judge, "judge-verdict"): "rework",
            (judge, "judge-checkpoint-result"): {"outcome": "pass"},
            (judge, "judge-unmet-criteria"): 1,
            (judge, "judge-unverified-criteria"): 1,
        }
        assert guards_match(passing, values)
        assert not guards_match(passing, {})
        for key in ((judge, "judge-applicability"), (judge, "judge-checkpoint-result")):
            missing = dict(values)
            del missing[key]
            assert not guards_match(passing, missing)
        for item, value in (
            ("judge-applicability", {"outcome": "fail"}),
            ("judge-applicability", {"outcome": "inconclusive"}),
            ("judge-checkpoint-result", {"outcome": "fail"}),
            ("judge-checkpoint-result", {"outcome": "inconclusive"}),
        ):
            rejected = dict(values)
            rejected[judge, item] = value
            assert not guards_match(passing, rejected)
        correction = dict(values)
        correction[judge, "judge-checkpoint-result"] = {"outcome": "fail"}
        correction[judge, "judge-unmet-criteria"] = 1
        assert guards_match(actual["rework"], correction)
        evidence = dict(values)
        evidence[judge, "judge-checkpoint-result"] = {"outcome": "inconclusive"}
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
        permitted = [key for key in actual if key != "blocked"]
        assert all(not guards_match(actual[key], {}) for key in permitted)
        for outcome in ("fail", "inconclusive"):
            values = {(source, "semantic-authority"): {"outcome": outcome}}
            assert all(not guards_match(actual[key], values) for key in permitted)
            assert guards_match(actual["blocked"], values)
        assert placement["routes"]["blocked"] == {"to": source, "effect": "rework"}
        assert all(placement["routes"][key]["effect"] == "rework" for key in permitted)
    assert (
        graph["confirm-review-completion"]["routes"]["rework"]["to"]
        == "classify-local-corrections"
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


def test_ordinary_sources_preserve_exact_historical_formal_declarations() -> None:
    versions = {"task": 30, "goal": 33, "validation": 32, "design": 10, "war-room": 10}
    expected = {
        "aquarium-worker/v1": "sha256:193732056972228fa535ac49f3986244ea4d67712e1be06b1e79bb98da3d55c5",
        "aquarium-goal-judge/v1": "sha256:97fe70694c9150e6eb6176758059b8770fbb81a03c004334d73a427925f46cbd",
    }
    for family, version in versions.items():
        current = load_procedure(f"aquarium-{family}-v2.yaml")
        assert all("delegation" not in node for node in nodes(current).values())
        prior = yaml.safe_load(
            (FIXTURES / f"aquarium-{family}-v{version}.yaml").read_bytes()
        )
        declarations = [
            node["delegation"] for node in nodes(prior).values() if "delegation" in node
        ]
        assert declarations
        for declaration in declarations:
            assert (
                declaration["role_snapshot_digest"] == expected[declaration["role_ref"]]
            )
            assert declaration["max_rounds"] == 32


def test_grouped_task_delivery_keeps_handoffs_and_authorized_rework_owners() -> None:
    task = load_procedure("aquarium-task-v2.yaml")
    graph = nodes(task)
    assert graph["implement"]["next"] == "refine"
    assert graph["refine"]["next"] == "verify"
    assert graph["verify"]["next"] == "judge-verification"
    selected = {
        source["node"]: set(source.get("items", []))
        for source in graph["judge-verification"]["evidence_from"]
    }
    for source in ("implement", "refine", "verify"):
        assert "worker-handoff" in selected[source]
    assert "record-plan" in selected
    for kind in ("followup", "evidence"):
        source = f"record-verification-{kind}"
        gate = graph[f"confirm-verification-{kind}-authority"]
        choices = options(task, gate["use"])
        for choice, owner in (
            ("implementation", "prepare-implementation"),
            ("refinement", "refine"),
            ("verification", "verify"),
        ):
            values = {
                (source, "semantic-authority"): {"outcome": "pass"},
                (source, "semantic-owner"): owner,
            }
            assert [
                key for key, option in choices.items() if guards_match(option, values)
            ] == [choice]
            assert gate["routes"][choice] == {"to": owner, "effect": "rework"}
            for outcome in ("fail", "inconclusive"):
                values[source, "semantic-authority"] = {"outcome": outcome}
                assert [
                    key
                    for key, option in choices.items()
                    if guards_match(option, values)
                ] == ["blocked"]


def test_validation_audit_is_one_direct_assessment_with_original_gap_routes() -> None:
    validation = load_procedure("aquarium-validation-v2.yaml")
    graph = nodes(validation)
    for audit, checkpoint in (
        ("audit", "confirm-audit-checkpoint"),
        ("re-audit", "confirm-re-audit-checkpoint"),
    ):
        assert "judge-" + audit not in graph
        assert graph[audit]["next"] == checkpoint
        definition = validation["node_definitions"][graph[audit]["use"]]
        fields = {item["id"] for item in definition["items"]}
        assert {
            "judge-assessment",
            "judge-applicability",
            "judge-checkpoint-result",
            "blocking-gap-count",
        } <= fields
        assert "worker-handoff" not in fields
        assert {source["node"] for source in graph[checkpoint]["evidence_from"]} == {
            audit
        }


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
            assert "delegation" not in graph[node_id]
        selected = {
            item
            for source in graph[judge]["evidence_from"]
            if source["node"] == candidate and source["required"]
            for item in source.get("items", [])
        }
        assert (
            "candidate-evidence"
            if candidate.startswith("prepare-")
            else "worker-handoff"
        ) in selected
        assert judge not in reachable_nodes(
            edges, goal["graph"]["entry"], without=candidate
        )
        assert decision not in reachable_nodes(
            edges, goal["graph"]["entry"], without=judge
        )
    assert {node_id for node_id, node in graph.items() if "delegation" in node} == set()
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
            (judge, "judge-verdict"): "rework",
            (judge, "judge-checkpoint-result"): {"outcome": "pass"},
            (judge, "judge-unmet-criteria"): 1,
            (judge, "judge-unverified-criteria"): 1,
        }
        assert guards_match(actual["passed"], values)
        for key in ((judge, "judge-applicability"), (judge, "judge-checkpoint-result")):
            missing = dict(values)
            del missing[key]
            assert not guards_match(actual["passed"], missing)
        for item, value in (
            ("judge-applicability", {"outcome": "fail"}),
            ("judge-applicability", {"outcome": "inconclusive"}),
            ("judge-checkpoint-result", {"outcome": "fail"}),
            ("judge-checkpoint-result", {"outcome": "inconclusive"}),
        ):
            rejected = dict(values)
            rejected[judge, item] = value
            assert not guards_match(actual["passed"], rejected)
        correction = dict(values)
        correction[judge, "judge-checkpoint-result"] = {"outcome": "fail"}
        correction[judge, "judge-unmet-criteria"] = 1
        assert guards_match(actual["rework"], correction)
        evidence = dict(values)
        evidence[judge, "judge-checkpoint-result"] = {"outcome": "inconclusive"}
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
        == "classify-local-corrections"
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
        ("remediate", "judge-remediation", "settle-remediation-group"),
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
            assert "delegation" not in graph[node_id]
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
        assert (
            "candidate-evidence"
            if candidate.startswith("prepare-")
            else "worker-handoff"
        ) in selected
    assert {key for key, node in graph.items() if "delegation" in node} == set()
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
        ("audit", "audit", "confirm-audit-checkpoint", "decide-gaps"),
        (
            "re-audit",
            "re-audit",
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
            (judge, "judge-verdict"): "rework",
            (judge, "judge-checkpoint-result"): {"outcome": "pass"},
            (judge, "judge-unmet-criteria"): 1,
            (judge, "judge-unverified-criteria"): 1,
        }
        assert guards_match(passed, values)
        for item, value in (
            ("judge-applicability", {"outcome": "fail"}),
            ("judge-applicability", {"outcome": "inconclusive"}),
            ("judge-checkpoint-result", {"outcome": "fail"}),
            ("judge-checkpoint-result", {"outcome": "inconclusive"}),
        ):
            rejected = dict(values)
            rejected[judge, item] = value
            assert not guards_match(passed, rejected)
        for key in ((judge, "judge-applicability"), (judge, "judge-checkpoint-result")):
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


def test_design_diagnosis_workers_and_judges_dominate_each_phase() -> None:
    for kind, checkpoints in (
        (
            "design",
            (
                ("discover", "judge-discovery", "decide-discovery-assessment"),
                ("quality", "judge-quality", "decide-quality-assessment"),
                (
                    "apply-documents",
                    "judge-application",
                    "decide-application-assessment",
                ),
                ("prepare-design-assessment", "judge-design", "assess-goal"),
            ),
        ),
        (
            "war-room",
            (
                (
                    "investigate",
                    "judge-investigation",
                    "decide-investigation-assessment",
                ),
                ("quality", "judge-quality", "decide-quality-assessment"),
                ("document", "judge-documentation", "decide-documentation-assessment"),
                ("prepare-diagnostic-assessment", "judge-diagnosis", "assess-goal"),
            ),
        ),
    ):
        procedure = load_procedure(f"aquarium-{kind}-v2.yaml")
        graph = nodes(procedure)
        edges = graph_edges(procedure)
        for worker, judge, successor in checkpoints:
            for placement, role in (
                (worker, "aquarium-worker/v1"),
                (judge, "aquarium-goal-judge/v1"),
            ):
                assert "delegation" not in graph[placement]
            items = {
                i["id"]: i
                for i in procedure["node_definitions"][graph[worker]["use"]]["items"]
            }
            handoff = (
                "candidate-evidence"
                if worker.startswith("prepare-")
                else "worker-handoff"
            )
            assert items[handoff]["required"]
            assert items[handoff]["allowed_media_types"] == ["application/json"]
            assert judge not in reachable_nodes(
                edges, procedure["graph"]["entry"], without=worker
            )
            assert successor not in reachable_nodes(
                edges, procedure["graph"]["entry"], without=judge
            )
        for node in graph.values():
            if procedure["node_definitions"][node["use"]]["type"] == "decision":
                assert "delegation" not in node
    war = load_procedure("aquarium-war-room-v2.yaml")
    graph = nodes(war)
    for branch in ("draft-task", "draft-epic", "draft-incomplete", "draft-no-work"):
        assert "delegation" not in graph[branch]
        assert graph[branch]["next"] == "quality"
        selected = next(
            e for e in graph["judge-quality"]["evidence_from"] if e["node"] == branch
        )
        assert selected["required"] is False
        assert "worker-handoff" in selected["items"]


def test_phase_checkpoints_preserve_global_negative_rows_without_false_success() -> (
    None
):
    for kind in ("design", "war-room"):
        procedure = load_procedure(f"aquarium-{kind}-v2.yaml")
        graph = nodes(procedure)
        for node_id, node in graph.items():
            if not node_id.startswith("decide-") or not node_id.endswith("-assessment"):
                continue
            choices = options(procedure, node["use"])
            judge = node["evidence_from"][0]["node"]
            values = {
                (judge, "judge-applicability"): {"outcome": "pass"},
                (judge, "judge-checkpoint-result"): {"outcome": "pass"},
                (judge, "judge-verdict"): "rework",
                (judge, "judge-unmet-criteria"): 1,
                (judge, "judge-unverified-criteria"): 1,
            }
            assert guards_match(choices["passed"], values)
            assert not guards_match(choices["passed"], {})
            for item in ("judge-applicability", "judge-checkpoint-result"):
                missing = dict(values)
                del missing[judge, item]
                assert not guards_match(choices["passed"], missing)
                for result in ("fail", "inconclusive"):
                    rejected = dict(values)
                    rejected[judge, item] = {"outcome": result}
                    assert not guards_match(choices["passed"], rejected)
            for result, option in (
                ("fail", "rework"),
                ("inconclusive", "evidence-needed"),
            ):
                negative = dict(values)
                negative[judge, "judge-checkpoint-result"] = {"outcome": result}
                assert guards_match(choices[option], negative)
            assert (
                node["routes"]["rework"]["to"]
                != node["routes"]["evidence-needed"]["to"]
            )
            assert node["routes"]["inapplicable"] == {"to": judge, "effect": "rework"}
        assert (
            graph["decide-quality-assessment"]["routes"]["passed"]["to"]
            == "decide-quality"
        )


def test_diagnostic_cause_and_scope_keep_supported_negative_outcomes() -> None:
    procedure = load_procedure("aquarium-war-room-v2.yaml")
    graph = nodes(procedure)
    for definition, item, router in (
        ("cause-decision", "judge-cause-outcome", "decide-cause"),
        ("scope-decision", "judge-scope-outcome", "classify-scope"),
    ):
        choices = options(procedure, definition)
        for selected in choices:
            values = {("judge-investigation", item): selected}
            assert [
                key for key, option in choices.items() if guards_match(option, values)
            ] == [selected]
            assert not guards_match(choices[selected], {})
        assert len(choices) <= 4
        assert "delegation" not in graph[router]
    assert graph["decide-cause"]["routes"]["blocked"]["to"] == "draft-incomplete"
    assert graph["decide-cause"]["routes"]["investigate-more"] == {
        "to": "investigate",
        "effect": "rework",
    }
    assert graph["classify-scope"]["routes"]["incomplete"]["to"] == "draft-incomplete"
    for draft in ("draft-task", "draft-epic", "draft-incomplete", "draft-no-work"):
        for dominator in (
            "quality",
            "judge-quality",
            "approve-diff",
            "document",
            "judge-diagnosis",
        ):
            assert "assess-goal" not in reachable_nodes(
                graph_edges(procedure), draft, without=dominator
            )


def test_design_diagnosis_followup_requires_actual_local_effect_authority() -> None:
    for kind in ("design", "war-room"):
        procedure = load_procedure(f"aquarium-{kind}-v2.yaml")
        graph = nodes(procedure)
        for node_id, node in graph.items():
            if not node_id.startswith("confirm-") or not node_id.endswith("-authority"):
                continue
            choices = options(procedure, node["use"])
            source = node["evidence_from"][0]["node"]
            admitted = {
                key: option for key, option in choices.items() if key != "blocked"
            }
            for key, option in admitted.items():
                assert not guards_match(option, {})
                for result in ("fail", "inconclusive"):
                    values = {(source, "semantic-authority"): {"outcome": result}}
                    assert not guards_match(option, values)
                    assert guards_match(choices["blocked"], values)
                values = {(source, "semantic-authority"): {"outcome": "pass"}}
                if key != "authorized":
                    values[source, "semantic-owner"] = key
                assert guards_match(option, values)
                if key != "authorized":
                    assert [
                        owner
                        for owner, choice in admitted.items()
                        if guards_match(choice, values)
                    ] == [key]
                    assert node["routes"][key] == {"to": key, "effect": "rework"}
                assert node["routes"][key]["effect"] == "rework"
            assert node["routes"]["blocked"] == {"to": source, "effect": "rework"}


def test_changed_application_approval_requires_original_quality_and_reapproval() -> (
    None
):
    for kind, app, suffix, draft in (
        ("design", "apply-documents", "application", "draft"),
        ("war-room", "document", "documentation", "investigate"),
    ):
        procedure = load_procedure(f"aquarium-{kind}-v2.yaml")
        graph = nodes(procedure)
        gate = graph["confirm-" + suffix + "-approval"]
        choices = options(procedure, gate["use"])
        assert graph[app]["next"] == gate["id"]
        for result in ("fail", "inconclusive"):
            values = {(app, "application-approval-result"): {"outcome": result}}
            assert not guards_match(choices["current"], values)
            assert guards_match(choices["invalid"], values)
        assert not guards_match(choices["current"], {})
        assert guards_match(
            choices["current"],
            {(app, "application-approval-result"): {"outcome": "pass"}},
        )
        assert gate["routes"]["invalid"]["to"] == "record-" + suffix + "-approval-gap"
        for mode in ("rework", "approval-gap"):
            authority = graph["confirm-" + suffix + "-" + mode + "-authority"]
            assert authority["routes"]["authorized"] == {
                "to": draft,
                "effect": "rework",
            }
        for dominator in ("quality", "decide-quality", "approve-diff"):
            assert app not in reachable_nodes(
                graph_edges(procedure), draft, without=dominator
            )
        assert graph["approve-diff"]["routes"]["changes-requested"] == {
            "to": draft,
            "effect": "rework",
        }


def test_design_diagnosis_final_original_outcome_vetoes_phase_success() -> None:
    for kind, judge, applicability in (
        ("design", "judge-design", "confirm-design-assessment-applicability"),
        ("war-room", "judge-diagnosis", "confirm-diagnosis-assessment-applicability"),
    ):
        procedure = load_procedure(f"aquarium-{kind}-v2.yaml")
        choices = options(procedure, "goal-assessment")
        current = options(procedure, nodes(procedure)[applicability]["use"])["current"]
        assert not guards_match(current, {})
        for outcome in ("fail", "inconclusive"):
            assert not guards_match(
                current, {(judge, "judge-applicability"): {"outcome": outcome}}
            )
        values = {
            (judge, "judge-goal-outcome"): "achieved",
            (judge, "judge-verdict"): "pass",
            (judge, "judge-unmet-criteria"): 0,
            (judge, "judge-unverified-criteria"): 0,
        }
        assert guards_match(choices["achieved"], values)
        for item, value in (
            ("judge-goal-outcome", "not-achieved"),
            ("judge-verdict", "rework"),
            ("judge-unmet-criteria", 1),
            ("judge-unverified-criteria", 1),
        ):
            negative = dict(values)
            negative[judge, item] = value
            assert not guards_match(choices["achieved"], negative)
        for item in values:
            missing = dict(values)
            del missing[item]
            assert not guards_match(choices["achieved"], missing)
        for outcome in ("not-achieved", "superseded"):
            assert guards_match(
                choices[outcome], {(judge, "judge-goal-outcome"): outcome}
            )


def test_historical_formal_phase_alignment_preserves_original_routes_and_final_vetoes() -> (
    None
):
    predecessors = {
        "task": 27,
        "goal": 30,
        "validation": 29,
        "design": 7,
        "war-room": 7,
    }
    for family, version in predecessors.items():
        current = yaml.safe_load(
            (FIXTURES / f"aquarium-{family}-v{version + 3}.yaml").read_bytes()
        )
        previous = yaml.safe_load(
            (FIXTURES / f"aquarium-{family}-v{version}.yaml").read_bytes()
        )
        assert current["id"] == previous["id"]
        # Phase alignment and the operative-role snapshot refresh are separate revisions.
        assert int(current["version"]) == version + 3
        current_nodes, previous_nodes = nodes(current), nodes(previous)
        added = set(current_nodes) - set(previous_nodes)
        expected_added = (
            {
                "classify-local-corrections",
                "classify-local-evidence-corrections",
                "confirm-local-corrections-settled",
                "confirm-local-corrections-eligibility",
                "confirm-local-evidence-corrections-eligibility",
                "confirm-local-current-completion",
            }
            if family in {"task", "goal", "validation"}
            else set()
        )
        if family in {"task", "goal"}:
            expected_added.update(
                {
                    "confirm-local-corrections-consistency",
                    "confirm-local-evidence-corrections-consistency",
                }
            )
        if family in {"goal", "validation"}:
            expected_added.update(
                {
                    "classify-local-incomplete-corrections",
                    "confirm-local-incomplete-corrections-eligibility",
                }
            )
        if family == "goal":
            expected_added.add("confirm-local-incomplete-corrections-consistency")
        if family == "validation":
            expected_added.add("confirm-local-required-evidence")
        if family in {"task", "goal", "validation"}:
            expected_added.add("authorize-new-mulgae-review")
        if family == "task":
            expected_added.add("confirm-changed-review-continuity")
        assert added == expected_added
        assert set(previous_nodes) <= set(current_nodes)
        for name, prior in previous_nodes.items():
            placement = current_nodes[name]
            expected_next = prior.get("next")
            actual_next = placement.get("next")
            if actual_next == "confirm-local-required-evidence":
                actual_next = current_nodes[actual_next]["routes"]["complete"]["to"]
            assert actual_next == expected_next
            previous_routes = prior.get("routes", {})
            current_routes = placement.get("routes", {})
            expected_options = (
                {"blocker-found"} if name == "decide-low-result" else set()
            )
            if name == "validate-review-route-entry":
                expected_options.add("new-review")
            if name in {
                "choose-active-review-route-direction",
                "choose-not-started-review-route-direction",
                "choose-terminal-review-route-direction",
                "choose-settled-route-direction",
            }:
                expected_options.add("new-review-current-route")
            assert set(current_routes) == set(previous_routes) | expected_options
            for option, route in previous_routes.items():
                destination = current_routes[option]["to"]
                if destination == "confirm-changed-review-continuity":
                    assert current_nodes[destination]["routes"]["pass"] == route
                elif destination.startswith("classify-local-"):
                    assert current_nodes[destination]["routes"]["none"] == route
                elif destination == "confirm-local-corrections-settled":
                    assert route["to"] == "decide-low-completion"
                    completion = current_nodes[destination]["routes"]["settled"]
                    assert completion == {
                        "to": "confirm-local-current-completion",
                        "effect": "advance",
                    }
                    assert (
                        current_nodes[completion["to"]]["routes"]["complete"] == route
                    )
                else:
                    assert current_routes[option] == route
            assert placement.get("use") == prior.get("use")
            assert ("delegation" in placement) == ("delegation" in prior)
        assert current["manual_rework"] == previous["manual_rework"]
        assert (
            current["node_definitions"]["goal-assessment"]
            == previous["node_definitions"]["goal-assessment"]
        )
        if "stopped-goal-assessment" in previous["node_definitions"]:
            assert (
                current["node_definitions"]["stopped-goal-assessment"]
                == previous["node_definitions"]["stopped-goal-assessment"]
            )
        for name, definition in previous["node_definitions"].items():
            if definition.get("type") == "action":
                for item in definition.get("items", []):
                    if item["id"] in {
                        "judge-verdict",
                        "judge-unmet-criteria",
                        "judge-unverified-criteria",
                        "judge-assessment",
                    }:
                        assert item in current["node_definitions"][name]["items"]


def test_inapplicable_phase_assessment_requires_nonpassing_current_applicability() -> (
    None
):
    for family in ("task", "goal", "validation", "design", "war-room"):
        procedure = load_procedure(f"aquarium-{family}-v2.yaml")
        found = 0
        for placement in nodes(procedure).values():
            definition = procedure["node_definitions"][placement["use"]]
            options = {option["id"]: option for option in definition.get("options", [])}
            if "inapplicable" not in options:
                continue
            option = options["inapplicable"]
            guards = normalized_guards(option)
            sources = [
                (node, item)
                for node, item, field, operator, expected in guards
                if item == "judge-applicability" and field == "outcome"
            ]
            assert len(sources) == 1
            source = sources[0]
            for outcome in ("fail", "inconclusive"):
                assert guards_match(option, {source: {"outcome": outcome}})
            assert not guards_match(option, {source: {"outcome": "pass"}})
            assert not guards_match(option, {})
            assert placement["routes"]["inapplicable"] == {
                "to": source[0],
                "effect": "rework",
            }
            found += 1
        assert found > 0


def test_local_corrections_require_complete_eligibility_and_existing_authority() -> (
    None
):
    for family, source, fallback in (
        ("task", "review", "record-task-rework-basis"),
        ("goal", "record-evidence", "decide-goal-rework-authority"),
        ("validation", "final-review", "decide-validation-rework-authority"),
    ):
        procedure = load_procedure(f"aquarium-{family}-v2.yaml")
        graph = nodes(procedure)
        choices = options(procedure, "local-correction-handling-decision")
        values = {
            (source, "local-correction-count"): 1,
            (source, "local-correction-eligibility"): {"outcome": "pass"},
            (source, "assessment-ordinal"): 4,
            (source, "completion-unmet-criteria"): 1,
        }
        assert guards_match(choices["local"], values)
        router = graph["classify-local-corrections"]
        checker = graph[router["routes"]["candidate"]["to"]]
        if family in {"task", "goal"}:
            assert checker["routes"]["inconsistent"] == {
                "to": "prepare-review" if family == "task" else "record-evidence",
                "effect": "rework",
            }
            checker = graph[checker["routes"]["consistent"]["to"]]
        assert checker["routes"]["local"] == {
            "to": "record-low-disposition",
            "effect": "advance",
        }
        assert router["routes"]["none"]["to"] == fallback
        assert checker["routes"]["ordinary"]["to"] == fallback
        assert guards_match(choices["ordinary"], values)
        judge = {
            "task": "judge-review",
            "goal": "judge-goal-evidence",
            "validation": "judge-validation-evidence",
        }[family]
        for placement in (router, checker):
            evidence = next(
                item for item in placement["evidence_from"] if item["node"] == judge
            )
            assert {
                "judge-assessment",
                "judge-unmet-criteria",
                "judge-unverified-criteria",
                "judge-checkpoint-result",
            } <= set(evidence["items"])
        for missing in ("local-correction-count", "local-correction-eligibility"):
            incomplete = dict(values)
            del incomplete[source, missing]
            assert not guards_match(choices["local"], incomplete)
        for outcome in ("fail", "inconclusive"):
            nonlocal_set = dict(values)
            nonlocal_set[source, "local-correction-eligibility"] = {"outcome": outcome}
            assert not guards_match(choices["local"], nonlocal_set)
            assert guards_match(choices["ordinary"], nonlocal_set)
        values[source, "local-correction-count"] = 0
        assert guards_match(
            options(procedure, "local-correction-candidate-decision")["none"], values
        )
        assert not guards_match(choices["local"], values)


def test_local_settlement_rejects_pending_repairs_failed_checks_and_current_gaps() -> (
    None
):
    for family in ("task", "goal", "validation"):
        procedure = load_procedure(f"aquarium-{family}-v2.yaml")
        graph = nodes(procedure)
        local = options(procedure, "local-correction-completion-decision")
        for pending in (1, 2):
            values = {("record-low-disposition", "pending-local-corrections"): pending}
            assert not guards_match(local["settled"], values)
            assert guards_match(local["pending"], values)
        assert not guards_match(local["settled"], {})
        assert graph["confirm-local-corrections-settled"]["routes"]["pending"] == {
            "to": "record-low-disposition",
            "effect": "rework",
        }
        verification = options(procedure, "low-result-decision")
        for outcome in ("fail", "inconclusive"):
            values = {
                ("record-low-disposition", "low-disposition-verification"): {
                    "outcome": outcome
                },
                ("record-low-disposition", "current-blocking-findings"): 0,
            }
            assert not guards_match(verification["passed"], values)
            assert guards_match(verification["incomplete"], values)
            values["record-low-disposition", "current-blocking-findings"] = 1
            assert not guards_match(verification["incomplete"], values)
            assert guards_match(verification["blocker-found"], values)
        completed = options(procedure, "low-completion-decision")["completed"]
        current = {
            ("record-low-disposition", item): 0
            for item in (
                "pending-low-dispositions",
                "current-blocking-findings",
                "completion-unmet-criteria",
                "completion-unverified-criteria",
            )
        }
        assert guards_match(completed, current)
        for item in current:
            negative = dict(current)
            negative[item] = 1
            assert not guards_match(completed, negative)


def test_local_correction_cannot_skip_native_admission_or_final_judgment() -> None:
    for family, backend, failure, final_judge in (
        ("task", "decide-backend-check", "record-task-rework-basis", "judge-task"),
        (
            "goal",
            "confirm-mulgae-fail-finding-validity",
            "decide-goal-rework-authority",
            "judge-goal",
        ),
        (
            "validation",
            "decide-final-backend-check",
            "decide-validation-rework-authority",
            "judge-validation",
        ),
    ):
        procedure = load_procedure(f"aquarium-{family}-v2.yaml")
        graph = nodes(procedure)
        assert failure in {route["to"] for route in graph[backend]["routes"].values()}
        assert "classify-local-corrections" not in {
            route["to"] for route in graph[backend]["routes"].values()
        }
        edges = graph_edges(procedure)
        completed = graph["decide-low-completion"]["routes"]["completed"]["to"]
        assert "assess-goal" in reachable_nodes(edges, completed)
        assert "assess-goal" not in reachable_nodes(
            edges, completed, without=final_judge
        )
        assembly = graph[
            {
                "task": "prepare-task-assessment",
                "goal": "prepare-goal-assessment",
                "validation": "prepare-validation-assessment",
            }[family]
        ]
        settlement = next(
            source
            for source in assembly["evidence_from"]
            if source["node"] == "record-low-disposition"
        )
        assert {
            "pending-local-corrections",
            "completion-assessment-summary",
            "completion-unmet-criteria",
            "completion-unverified-criteria",
        } <= set(settlement["items"])


def test_current_local_criteria_route_to_their_existing_owners() -> None:
    for family, correction, evidence, effect in (
        ("task", "record-task-rework-basis", "record-review-evidence", "advance"),
        ("goal", "decide-goal-rework-authority", "record-evidence", "rework"),
        (
            "validation",
            "decide-validation-rework-authority",
            "record-incomplete",
            "advance",
        ),
    ):
        procedure = load_procedure(f"aquarium-{family}-v2.yaml")
        graph = nodes(procedure)
        choices = options(procedure, "local-current-completion-decision")
        for unmet, unverified, selected in (
            (0, 0, "complete"),
            (1, 0, "unmet"),
            (0, 1, "unverified"),
            (1, 1, "unmet"),
        ):
            values = {
                ("record-low-disposition", "completion-unmet-criteria"): unmet,
                (
                    "record-low-disposition",
                    "completion-unverified-criteria",
                ): unverified,
            }
            assert [
                name for name, option in choices.items() if guards_match(option, values)
            ] == [selected]
        routes = graph["confirm-local-current-completion"]["routes"]
        assert routes["unmet"] == {"to": correction, "effect": "advance"}
        assert routes["unverified"] == {"to": evidence, "effect": effect}
        assert graph["decide-low-result"]["routes"]["blocker-found"] == {
            "to": correction,
            "effect": "advance",
        }


def test_validation_current_required_evidence_veto_precedes_local_completion() -> None:
    procedure = load_procedure("aquarium-validation-v2.yaml")
    graph = nodes(procedure)
    assert graph["record-low-disposition"]["next"] == "confirm-local-required-evidence"
    choices = options(procedure, "local-required-evidence-decision")
    for gap in (0, 1, 2):
        values = {("record-low-disposition", "current-required-evidence-gaps"): gap}
        assert guards_match(choices["complete"], values) == (gap == 0)
        assert guards_match(choices["incomplete"], values) == (gap > 0)
    assert not guards_match(choices["complete"], {})
    assert graph["confirm-local-required-evidence"]["routes"]["incomplete"] == {
        "to": "record-incomplete",
        "effect": "advance",
    }
    source = next(
        source
        for source in graph["prepare-validation-assessment"]["evidence_from"]
        if source["node"] == "record-low-disposition"
    )
    assert {"current-required-evidence-gaps", "current-blocking-findings"} <= set(
        source["items"]
    )


def test_every_local_classifier_preserves_full_ordinary_and_consistency_routes() -> (
    None
):
    for family in ("task", "goal", "validation"):
        procedure = load_procedure(f"aquarium-{family}-v2.yaml")
        graph = nodes(procedure)
        for name, router in graph.items():
            if not name.startswith("classify-local-"):
                continue
            successor = graph[router["routes"]["candidate"]["to"]]
            if family in {"task", "goal"}:
                assert successor["routes"]["inconsistent"] == {
                    "to": "prepare-review" if family == "task" else "record-evidence",
                    "effect": "rework",
                }
                successor = graph[successor["routes"]["consistent"]["to"]]
            assert successor["routes"]["ordinary"] == router["routes"]["none"]


def test_local_core_and_rework_consumers_bind_current_settlement() -> None:
    for family in ("goal", "validation"):
        graph = nodes(load_procedure(f"aquarium-{family}-v2.yaml"))
        for name in ("confirm-goal-assessment-core", f"record-{family}-rework-basis"):
            source = next(
                source
                for source in graph[name]["evidence_from"]
                if source["node"] == "record-low-disposition"
            )
            assert source["required"] is False
            assert {
                "after-target",
                "completion-assessment-summary",
                "completion-unmet-criteria",
                "completion-unverified-criteria",
                "current-blocking-findings",
            } <= set(source["items"])
            if family == "validation":
                assert "current-required-evidence-gaps" in source["items"]


def test_validation_local_profiles_match_the_actual_clean_audit_guards() -> None:
    spec = importlib.util.spec_from_file_location(
        "podway_runtime_qualification", ROOT / "tests/podway_runtime_qualification.py"
    )
    assert spec is not None and spec.loader is not None
    runtime = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runtime)

    procedure = load_procedure("aquarium-validation-v2.yaml")
    graph = nodes(procedure)
    audit = procedure["node_definitions"][graph["audit"]["use"]]
    for scenario in ("validation-local-settled", "validation-local-retry"):
        managed = runtime.ManagedRuntime(Path("/unused/podway"), PROCEDURES, 1)
        managed.scenario = scenario
        managed.current_procedure_id = "aquarium-validation-v2"
        values = {}
        for item in audit["items"]:
            if item["type"] in {"integer", "check_result"}:
                constraints = {
                    key: item[key]
                    for key in ("minimum", "operation_id", "operation_digest")
                    if key in item
                }
                value = managed.value_for(
                    {
                        "item_id": item["id"],
                        "type": item["type"],
                        "constraints": constraints,
                    },
                    "audit",
                )
                values["audit", item["id"]] = (
                    value["value"] if item["type"] == "integer" else value
                )
        assert all(
            values["audit", item] == 0
            for item in (
                "confirmed-gap-count",
                "blocking-gap-count",
                "eligible-low-gap-count",
                "confirmation-needed-gap-count",
            )
        )
        choices = options(procedure, graph["decide-gaps"]["use"])
        assert guards_match(choices["clean"], values)
        assert not guards_match(choices["low-only"], values)


def test_goal_current_unverified_evidence_owner_binds_its_local_target() -> None:
    graph = nodes(load_procedure("aquarium-goal-v2.yaml"))
    assert graph["confirm-local-current-completion"]["routes"]["unverified"] == {
        "to": "record-evidence",
        "effect": "rework",
    }
    source = next(
        source
        for source in graph["record-evidence"]["evidence_from"]
        if source["node"] == "record-low-disposition"
    )
    assert source["required"] is False
    assert {
        "after-target",
        "low-disposition-summary",
        "completion-assessment-summary",
        "completion-unmet-criteria",
        "completion-unverified-criteria",
    } <= set(source["items"])


def test_new_mulgae_execution_requires_terminal_settlement_and_the_same_route() -> None:
    for family, source in (
        ("task", "prepare-review"),
        ("goal", "record-evidence"),
        ("validation", "final-review"),
    ):
        procedure = load_procedure(f"aquarium-{family}-v2.yaml")
        admitted = options(procedure, "new-live-review-admission-decision")["start"]
        values = {
            (source, "prior-route-lifecycle-state"): "terminal-incomplete-or-failed",
            (
                source,
                "prior-route-change-readiness"
                if family == "task"
                else "route-change-readiness",
            ): "safe-to-change",
        }
        if family == "task":
            values[(source, "prior-review-route")] = "mulgae"
            values[(source, "effective-review-route")] = "mulgae"
        else:
            values[(source, "review-route")] = "mulgae"
            values[(source, "route-direction")] = "new-review-current-route"
        assert guards_match(admitted, values)
        for key, invalid in (
            ((source, "prior-route-lifecycle-state"), "active-or-unknown"),
            ((source, "prior-route-lifecycle-state"), "not-started"),
            ((source, "prior-route-lifecycle-state"), "terminal-complete"),
            (
                (
                    source,
                    "effective-review-route" if family == "task" else "review-route",
                ),
                "herdr",
            ),
            (
                (
                    source,
                    "prior-route-change-readiness"
                    if family == "task"
                    else "route-change-readiness",
                ),
                "current-route-only",
            ),
        ):
            changed = dict(values)
            changed[key] = invalid
            assert not guards_match(admitted, changed)
        definition_id = {
            "task": "review-record",
            "goal": "evidence-record",
            "validation": "final-review-record",
        }[family]
        items = {
            i["id"]: i for i in procedure["node_definitions"][definition_id]["items"]
        }
        assert items["review-source-contract"]["required"]
        assert items["review-source-binding"]["required"]
        source_definition = nodes(procedure)[source]["use"]
        lifecycle = next(
            item
            for item in procedure["node_definitions"][source_definition]["items"]
            if item["id"] == "prior-route-lifecycle-state"
        )
        assert "terminal-complete" in lifecycle["choices"]


def test_ordinary_applicability_and_grouped_evidence_operation_identities() -> None:
    observed = 0
    for path in sorted(PROCEDURES.glob("aquarium-*-v2.yaml")):
        procedure = yaml.safe_load(path.read_text())
        for definition in procedure["node_definitions"].values():
            for item in definition.get("items", []):
                if item.get("id") not in {
                    "judge-applicability",
                    "closeout-substitute-applicability",
                } and item.get("operation_id") not in {
                    "aquarium-design-discovery-evidence-needed-authority",
                    "aquarium-war-room-investigation-evidence-needed-authority",
                }:
                    continue
                descriptor = item.get("help", item["prompt"])
                assert (
                    item["operation_digest"]
                    == "sha256:" + hashlib.sha256(descriptor.encode()).hexdigest()
                )
                observed += 1
    assert observed == 20


def test_grouped_first_owner_evidence_routes_retain_approval_dominators() -> None:
    for kind, phase, owners, applied in (
        ("design", "discovery", {"capture-context", "discover"}, "apply-documents"),
        ("war-room", "investigation", {"capture-baseline", "investigate"}, "document"),
    ):
        procedure = load_procedure(f"aquarium-{kind}-v2.yaml")
        graph = nodes(procedure)
        source = f"record-{phase}-evidence-needed"
        action = procedure["node_definitions"][graph[source]["use"]]
        selected = next(
            item for item in action["items"] if item["id"] == "semantic-owner"
        )
        assert set(selected["choices"]) == owners
        gate = graph[f"confirm-{phase}-evidence-needed-authority"]
        assert set(gate["routes"]) == owners | {"blocked"}
        for owner in owners:
            for dominator in ("quality", "decide-quality", "approve-diff"):
                assert applied not in reachable_nodes(
                    graph_edges(procedure), owner, without=dominator
                )


def test_review_strategy_revision_preserves_control_and_evidence_surface() -> None:
    prose = {
        "criteria",
        "description",
        "evidence_guidance",
        "help",
        "instructions",
        "intent",
        "label",
        "name",
        "objective",
        "prompt",
        "purpose",
        "title",
    }

    def control(value):
        if isinstance(value, dict):
            return {
                key: control(item) for key, item in value.items() if key not in prose
            }
        if isinstance(value, list):
            return [control(item) for item in value]
        return value

    for family, prior_version in (("task", 31), ("goal", 34), ("validation", 33)):
        prior = yaml.safe_load(
            (FIXTURES / f"aquarium-{family}-v{prior_version}.yaml").read_bytes()
        )
        current = load_procedure(f"aquarium-{family}-v2.yaml")
        assert int(current["version"]) == int(prior["version"]) + 1
        current_control, prior_control = control(current), control(prior)
        current_control.pop("version")
        prior_control.pop("version")
        assert current_control == prior_control
