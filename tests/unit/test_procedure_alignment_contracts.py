from __future__ import annotations

import hashlib
import json
from itertools import pairwise
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


def test_task_071_current_and_prior_procedure_identities_are_exact() -> None:
    identities = (
        (
            "aquarium-task-v2.yaml",
            "17",
            "ecbd6b3388746eac2fb03e2971a518d210e15567975f930ce9bd7db89b165203",
            "aquarium-task-v16.yaml",
            "a003e94b26e4d4702d6bb6a7f8f0cfb98a5df61a62c358cae3660cba917f18f3",
        ),
        (
            "aquarium-goal-v2.yaml",
            "20",
            "bf0eaa45855755136f9fc439ec654c6351cbec5cb1d7b50999c104bf0dda56b2",
            "aquarium-goal-v19.yaml",
            "fd247c06de794254d5785c84520e1feaa570ce273559208946a28bc84b057163",
        ),
        (
            "aquarium-validation-v2.yaml",
            "19",
            "bc13b16e9f4b49990261ffbd3b2dd66f092699f858645f0ce4da2a1a73523866",
            "aquarium-validation-v18.yaml",
            "4c355c2ec35caed6e454d32364fb8d849f1a02f3772879e314e15fc20c42469b",
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
        f"TR-{index:02d}" for index in range(1, 11)
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


def test_task_review_uses_route_specific_serial_gates() -> None:
    task = load_procedure("aquarium-task-v2.yaml")
    graph = nodes(task)

    assert graph["document"]["next"] == "prepare-review"
    assert graph["prepare-review"]["next"] == "validate-review-route-entry"
    assert graph["classify-review-route-change"]["routes"] == {
        "unsettled": {
            "to": "confirm-review-route-change-readiness",
            "effect": "advance",
        },
        "completed": {
            "to": "authorize-completed-review-route",
            "effect": "advance",
        },
    }
    assert graph["confirm-review-route-change-readiness"]["routes"] == {
        "safe": {
            "to": "authorize-incomplete-review-route",
            "effect": "advance",
        },
        "unsafe": {"to": "prepare-review", "effect": "rework"},
    }
    expected_entries = {
        "planned-mulgae": "enter-mulgae-review-route",
        "planned-orca": "enter-orca-review-route",
        "planned-native-codex": "enter-native-codex-review-route",
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
        "orca": {"to": "decide-orca-review-operation", "effect": "advance"},
        "native-codex": {
            "to": "decide-native-codex-review-operation",
            "effect": "advance",
        },
        "waived": {"to": "confirm-assessment-ordinal", "effect": "advance"},
    }
    for route in ("mulgae", "orca", "native-codex"):
        assert graph[f"decide-{route}-review-operation"]["routes"] == {
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
        "standard": {
            "to": "confirm-first-review-evidence",
            "effect": "advance",
        },
        "authorized-extra": {
            "to": "confirm-extra-review-evidence",
            "effect": "advance",
        },
    }
    for gate in ("confirm-first-review-evidence", "confirm-extra-review-evidence"):
        assert set(graph[gate]["routes"]) == {"mulgae", "static-delegated", "waived"}
    assert graph["decide-backend-check"]["routes"] == {
        "non-failing": {
            "to": "confirm-review-completion",
            "effect": "advance",
        },
        "failed": {
            "to": "decide-task-rework-authority",
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
        "orca": {"to": "enter-orca-review-route", "effect": "advance"},
        "native-codex": {
            "to": "enter-native-codex-review-route",
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
    assert task["version"] == "17"

    evidence = options(task, "review-evidence-decision")
    provenance = options(task, "review-provenance-decision")
    cases = (
        ("mulgae", "complete", "pass", "mulgae", "delegated-reviewer", None),
        (
            "orca",
            "complete",
            "not-provided",
            "static-delegated",
            "delegated-reviewer",
            None,
        ),
        (
            "native-codex",
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
        ("review", "assessment-ordinal", None, "at_least", 1),
    }
    assert normalized_guards(operation["unsettled"]) == {
        ("review", "review-route", None, "not_equals", "waived"),
        ("review", "assessment-ordinal", None, "equals", 0),
    }

    ordinal = options(task, "assessment-ordinal-decision")
    standard = {
        ("prepare-review", "prior-assessment-ordinal"): 3,
        ("review", "assessment-ordinal"): 4,
        ("review", "assessment-ordinal-continuity"): {"outcome": "pass"},
    }
    assert guards_match(ordinal["standard"], standard)
    over_limit = dict(standard)
    over_limit[("review", "assessment-ordinal")] = 5
    assert not guards_match(ordinal["standard"], over_limit)
    authorized = {
        ("review", "assessment-ordinal"): 5,
        ("review", "review-mode"): "confirmation-only",
        ("prepare-review", "extra-assessment-authority-reference"): "user authority",
        ("review", "assessment-ordinal-continuity"): {"outcome": "pass"},
    }
    assert guards_match(ordinal["authorized-extra"], authorized)


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
            *(selected_items(current[node_id]) for node_id in current_node_ids)
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
        "resumed": {
            "to": "authorize-current-review-route-resume",
            "effect": "advance",
        },
    }
    assert graph["classify-review-route-change"]["routes"] == {
        "unsettled": {
            "to": "confirm-review-route-change-readiness",
            "effect": "advance",
        },
        "completed": {
            "to": "authorize-completed-review-route",
            "effect": "advance",
        },
    }

    planned = options(task, "planned-review-route-authorization-decision")
    values = {
        ("record-plan", "review-route"): "orca",
        ("prepare-review", "effective-review-route"): "orca",
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
    assert guards_match(planned["planned-orca"], values)
    assert not guards_match(planned["planned-mulgae"], values)


def test_task_checkpoint_direction_matrix_guards_every_authorization_basis() -> None:
    task = load_procedure("aquarium-task-v2.yaml")
    checkpoint = {
        item["id"]: item
        for item in task["node_definitions"]["review-checkpoint-record"]["items"]
    }
    assert checkpoint["checkpoint-requested-direction"]["choices"] == [
        "not-applicable",
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
        "sha256:2b7ed39dae811563236b629a7f934f69924fdba16728b403b8a5f581abd0fbdd"
    )

    entry = options(task, "review-route-entry-decision")
    for option_id in ("changed", "resumed"):
        assert (
            "prepare-review",
            "route-direction-continuity",
            "outcome",
            "equals",
            "pass",
        ) in normalized_guards(entry[option_id])

    definitions = {
        "planned-review-route-authorization-decision": "not-applicable",
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
            {
                ("prepare-review", "prior-review-operation"): operation,
                ("prepare-review", "prior-assessment-ordinal"): 3,
            },
        )
    assert not guards_match(
        change_state["unsettled"],
        {
            ("prepare-review", "prior-review-operation"): "completed",
            ("prepare-review", "prior-assessment-ordinal"): 3,
        },
    )
    completed_state = {
        ("prepare-review", "prior-review-operation"): "completed",
        ("prepare-review", "prior-route-change-readiness"): "completed-checkpoint",
        ("prepare-review", "prior-assessment-ordinal"): 1,
    }
    assert guards_match(change_state["completed"], completed_state)
    for key, invalid in (
        (("prepare-review", "prior-review-operation"), "failed"),
        (("prepare-review", "prior-route-change-readiness"), "safe-to-change"),
        (("prepare-review", "prior-assessment-ordinal"), 0),
    ):
        mismatched = dict(completed_state)
        mismatched[key] = invalid
        assert not guards_match(change_state["completed"], mismatched)

    incomplete = options(task, "incomplete-review-route-authorization-decision")
    incomplete_switch = {
        ("prepare-review", "effective-review-route"): "orca",
        ("prepare-review", "route-authorization-basis"): "explicit-route-change",
        ("prepare-review", "checkpoint-requested-direction"): "switch-route",
        ("prepare-review", "prior-route-change-readiness"): "safe-to-change",
    }
    assert guards_match(incomplete["changed-orca"], incomplete_switch)
    incomplete_switch[("prepare-review", "prior-route-change-readiness")] = (
        "completed-checkpoint"
    )
    assert not guards_match(incomplete["changed-orca"], incomplete_switch)

    completed = options(task, "completed-review-route-authorization-decision")
    completed_switch = {
        **completed_state,
        ("prepare-review", "effective-review-route"): "orca",
        ("prepare-review", "route-authorization-basis"): "explicit-route-change",
        ("prepare-review", "checkpoint-requested-direction"): "switch-route",
    }
    assert guards_match(completed["completed-change-orca"], completed_switch)
    assert not guards_match(completed["completed-change-waiver"], completed_switch)
    completed_waiver = {
        **completed_state,
        ("prepare-review", "effective-review-route"): "waived",
        ("prepare-review", "route-authorization-basis"): "explicit-waiver",
        ("prepare-review", "checkpoint-requested-direction"): "waive",
    }
    assert guards_match(completed["completed-change-waiver"], completed_waiver)
    assert not guards_match(completed["completed-change-orca"], completed_waiver)


def test_task_route_fixtures_traverse_only_guarded_options() -> None:
    task = load_procedure("aquarium-task-v2.yaml")
    cases = load_json("review-routing-cases.json")["task_review_route_cases"]
    authorization = {
        option_id: option
        for definition in (
            "planned-review-route-authorization-decision",
            "incomplete-review-route-authorization-decision",
            "completed-review-route-authorization-decision",
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
        assert guards_match(operation[case["operation_option"]], values), case["id"]
        if case["ordinal"] > 0:
            values.update(
                {
                    ("prepare-review", "prior-assessment-ordinal"): case[
                        "prior_ordinal"
                    ],
                    ("review", "assessment-ordinal-continuity"): {"outcome": "pass"},
                    ("review", "review-mode"): (
                        "remediation-eligible"
                        if case["ordinal"] == 1
                        else "confirmation-only"
                    ),
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
            for other_provider in {"mulgae", "orca", "native-codex"} - {
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
        "planned-orca",
        "planned-native-codex",
        "planned-waiver",
        "changed-mulgae",
        "changed-orca",
        "changed-native-codex",
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
        "confirm-first-route-evidence",
        "confirm-second-route-evidence",
        "confirm-extra-route-evidence",
    ):
        assert set(graph[node_id]["routes"]) == {
            "mulgae-pass",
            "mulgae-fail",
            "orca",
            "native-codex",
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
    fixture = load_json("review-routing-cases.json")
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
        "orca",
        "native-codex",
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
                "remediation-eligible"
                if case["ordinal"] == 1
                else "hardening-deferral-eligible"
            ),
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
        "orca",
        "native-codex",
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
        ("final-review", "review-route"): "orca",
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
            ("review", "review-route"): "orca",
            ("review", "assessment-ordinal"): 0,
        },
    )
    assert not guards_match(
        task_operation,
        {
            ("review", "review-route"): "orca",
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


def test_goal_and_validation_extra_ordinals_require_current_authority() -> None:
    goal = load_procedure("aquarium-goal-v2.yaml")
    ordinal = options(goal, "assessment-ordinal-decision")["authorized-extra"]
    extra = options(goal, "assessment-extra-ordinal-decision")
    values = {
        ("record-evidence", "prior-assessment-ordinal"): 2,
        ("record-evidence", "assessment-ordinal"): 3,
        ("record-evidence", "review-mode"): "hardening-deferral-eligible",
        ("record-evidence", "extra-assessment-authority-reference"): "user authority",
        ("record-evidence", "assessment-ordinal-continuity"): {"outcome": "pass"},
    }
    assert guards_match(ordinal, values)
    assert guards_match(extra["authorized-extra"], values)
    below_minimum = dict(values)
    below_minimum[("record-evidence", "assessment-ordinal")] = 2
    assert not guards_match(extra["authorized-extra"], below_minimum)
    assert guards_match(extra["invalid-extra"], below_minimum)

    validation = load_procedure("aquarium-validation-v2.yaml")
    admitted = options(validation, "assessment-ordinal-decision")["admitted"]
    assert guards_match(
        admitted,
        {
            ("final-review", "assessment-ordinal"): 3,
            ("final-review", "assessment-ordinal-continuity"): {"outcome": "pass"},
        },
    )


def test_validation_uses_serial_operation_completion_evidence_and_blocker_gates() -> (
    None
):
    procedure = load_procedure("aquarium-validation-v2.yaml")
    graph = nodes(procedure)
    assert graph["final-review"]["next"] == "confirm-final-review-route-binding"
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
        "admitted": {
            "to": "confirm-assessed-final-review-provenance",
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
            "to": "confirm-completion-assessment",
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

        if name == "aquarium-task-v2.yaml":
            stopped_options = options(procedure, "stopped-goal-assessment")
            stopped_values = {
                (
                    "record-stopped-goal-boundary",
                    "goal-outcome-boundary",
                ): "stopped"
            }
            assert graph["confirm-goal-assessment-core"]["routes"]["ready"]["to"] == (
                "assess-goal"
            )
            assert (
                graph["confirm-stopped-goal-boundary"]["routes"]["confirmed"]["to"]
                == "assess-stopped-goal"
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
        "to": "assess-goal",
        "effect": "advance",
    }
    assert graph["confirm-stopped-goal-boundary"]["routes"]["confirmed"] == {
        "to": "assess-stopped-goal",
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
        ("aquarium-validation-v2.yaml", "audit", "stopped-or-incomplete"),
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

        for chain in chains:
            terminal = chain[-1]
            assert terminal in reachable_nodes(edges, entry)
            for dominator in chain[:-1]:
                assert terminal not in reachable_nodes(
                    edges, entry, without=dominator
                ), f"{name}: {dominator} does not dominate {terminal}"
            for predecessor, node_id in pairwise(chain):
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
        stopped = options(procedure, "stopped-goal-assessment")["achieved"]
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
