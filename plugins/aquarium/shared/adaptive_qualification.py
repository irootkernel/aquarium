"""Source-level obligation qualification; actual agents and authority stay runtime evidence."""

import copy
import json
from collections import defaultdict, deque

from adaptive_bundles import BundleError, sha256
from adaptive_composition import check_graph, check_shapes
from adaptive_definitions import (
    ASSETS,
    DefinitionError,
    canonical_json,
    capability_signatures,
    check_capability,
    validate_definition,
)
from adaptive_predicates import ABSENT, AnalysisLimit, Decisions, item_domain


def issue(status, property_name, location, **details):
    return {
        "status": status,
        "property": property_name,
        "location": location,
        **details,
    }


def guarantee(signature):
    # Existing reference names identify their versioned meanings. A verified new
    # operation declares its guarantee explicitly in the supplied registry.
    return signature.get("guarantee")


def guarantee_minima(signature):
    """Independent structural floors; custom operations cannot define these away."""
    kind = guarantee(signature)
    assessment = {
        "final-assessment": ["judge-goal-outcome"],
        "phase-assessment": ["judge-checkpoint-result"],
        "audit-assessment": ["audit-result", "judge-checkpoint-result"],
        "confirmation-audit-assessment": ["audit-result", "judge-checkpoint-result"],
        "correction-group-assessment": ["judge-group-result"],
        "quality-assessment": ["judge-checkpoint-result"],
        "application-assessment": ["judge-checkpoint-result"],
        "documentation-assessment": ["judge-checkpoint-result"],
    }
    fields, counts = {}, []
    if kind in assessment or (isinstance(kind, str) and "assessment" in kind):
        fields = {
            "judge-assessment": {
                "type": "artifact",
                "required": True,
                "allowed_media_types": ["application/json"],
            },
            "judge-verdict": {
                "type": "choice",
                "required": True,
                "choices": ["pass", "rework", "evidence-needed"],
            },
            "judge-applicability": {"type": "check_result", "required": True},
        }
        counts = ["judge-unmet-criteria", "judge-unverified-criteria"]
        fields.update(
            {
                name: {"type": "integer", "required": True, "minimum": 0}
                for name in counts
            }
        )
        for name in assessment.get(kind, []):
            fields[name] = (
                {
                    "type": "choice",
                    "required": True,
                    "choices": ["achieved", "not-achieved"],
                }
                if name == "judge-goal-outcome"
                else {"type": "check_result", "required": True}
            )
    elif kind == "approval":
        return [{"kind": "decision", "options": ["approved", "changes-requested"]}]
    elif kind == "review-control":
        # Applicable path proof determines native-review presence; waiver/closeout
        # variants may legitimately make these records conditional.
        fields = {
            "review-operation": {"type": "choice"},
            "assessment-ordinal": {"type": "integer", "minimum": 0},
            "assessment-ordinal-continuity": {"type": "check_result"},
            "review-mode": {"type": "choice", "required": True},
            "assessment-kind": {"type": "choice", "required": True},
        }
    elif kind == "review-routing":
        fields = {}
    elif kind == "acceptance":
        fields = {
            "acceptance-source": {"type": "choice", "required": True},
            "acceptance-authority": {"type": "text", "required": True},
            "accepted-target": {"type": "text", "required": True},
        }
    elif kind == "application-approval":
        fields = {
            "application-approval-result": {"type": "check_result", "required": True}
        }
    elif kind == "upstream-quality":
        fields = {
            "quality-result": {"type": "check_result", "required": True},
            "worker-handoff": {
                "type": "artifact",
                "required": True,
                "allowed_media_types": ["application/json"],
            },
        }
    elif kind == "closeout":
        fields = {"closeout-summary": {"type": "text", "required": True}}
    elif kind == "suitability-bootstrap":
        fields = {
            "suitability-assessment": {
                "type": "artifact",
                "required": True,
                "allowed_media_types": ["application/json"],
            },
            "suitability-target": {"type": "text", "required": True},
            "suitability-timing": {
                "type": "choice",
                "required": True,
                "choices": ["pre-start"],
            },
            "suitability-verdict": {
                "type": "choice",
                "required": True,
                "choices": ["pass", "rework", "evidence-needed"],
            },
            "suitability-current": {"type": "check_result", "required": True},
        }
        counts = ["suitability-unmet", "suitability-unverified"]
        fields.update(
            {
                name: {"type": "integer", "required": True, "minimum": 0}
                for name in counts
            }
        )
    else:
        return []
    variants = [fields]
    if kind == "review-routing":
        variants = [
            {name: {"type": "check_result"}}
            for name in ["route-binding-result", "route-direction-continuity"]
        ]
    result = []
    for variant in variants:
        for name, minimum in variant.items():
            if minimum["type"] == "check_result":
                minimum["accepted_outcomes"] = ["pass", "fail", "inconclusive"]
        result.append({"kind": "action", "fields": variant, "criterion_counts": counts})
    return result


class Qualification:
    def __init__(
        self, document, binding, context, signatures, operation_contracts, node_budget
    ):
        self.document, self.binding, self.context = document, binding, context
        self.signatures = signatures
        self.nodes = {node["id"]: node for node in document["graph"]["nodes"]}
        self.definitions = {
            identifier: document["node_definitions"][node["use"]]
            for identifier, node in self.nodes.items()
        }
        self.items = {
            (node, item["id"]): item
            for node, definition in self.definitions.items()
            for item in definition.get("items", [])
        }
        self.capabilities = defaultdict(list)
        self.issues = []
        self.current_property = ("declarations", "nodes")
        self.operations = operation_contracts
        self.established_operations = json.loads(
            (ASSETS / "adaptive/operation-contracts-v1.json").read_text()
        )
        self.inspect_declarations()
        predicates = defaultdict(list)
        for definition in self.definitions.values():
            for option in definition.get("options", []):
                for guard in option.get("guards", []):
                    predicates[
                        (guard["evidence"]["node"], guard["evidence"]["item"])
                    ].append(guard)
        for node, definition in self.definitions.items():
            for item in definition.get("items", []):
                for condition in item.get("required_when", []):
                    predicates[(node, condition["item"])].append(
                        {
                            key: value
                            for key, value in condition.items()
                            if key != "item"
                        }
                    )
        needed = set(predicates)
        needed.update(
            (endpoint["node"], endpoint["item"])
            for obligation in binding["obligations"].values()
            for endpoint in obligation["producers"] + obligation["evidence"]
        )
        for rows in self.capabilities.values():
            for node, fields, signature in rows:
                needed.update(
                    (node, fields.get(name, name))
                    for name in set(signature.get("fields", {}))
                    | {
                        field
                        for floor in guarantee_minima(signature)
                        for field in floor.get("fields", {})
                    }
                )
        for key in self.items:
            if key[1] in {
                "goal-kind",
                "workflow-owner",
                "review-evidence-kind",
                "route-authorization-basis",
                "review-route",
                "extra-assessment-authority-reference",
                "local-correction-eligibility",
                "coverage-relationship",
            }:
                needed.add(key)
        pending = list(needed)
        while pending:
            key = pending.pop()
            for condition in self.items.get(key, {}).get("required_when", []):
                dependency = key[0], condition["item"]
                if dependency not in needed:
                    needed.add(dependency)
                    pending.append(dependency)
        self.order = self.topological_order()
        domains = {}
        for node in self.order:
            waiting = [key for key in self.items if key[0] == node and key in needed]
            while waiting:
                ready = [
                    key
                    for key in waiting
                    if all(
                        (node, condition["item"]) in domains
                        for condition in self.items[key].get("required_when", [])
                    )
                ]
                if not ready:
                    raise BundleError(
                        "not-established",
                        "Conditional evidence dependency cycle",
                        {"property": "conditional-presence", "location": node},
                    )
                for key in ready:
                    predicates[key].extend(
                        [
                            {"equals": 0},
                            {"at_least": 1},
                            {"at_most": 3},
                            {"at_least": 4},
                            {"at_least": 5},
                        ]
                    )
                    domains[key] = item_domain(self.items[key], predicates[key])
                    waiting.remove(key)
        for node in self.nodes:
            if self.nodes[node].get("skip", {}).get("allowed"):
                domains[(node, "@execute")] = [False, True]
            if self.definitions[node]["type"] == "decision":
                domains[(node, "@option")] = [
                    option["id"] for option in self.definitions[node]["options"]
                ]
        ordered = {
            key: domains[key]
            for node in self.order
            for key in domains
            if key[0] == node
        }
        self.logic = Decisions(
            dict(reversed(list(ordered.items()))),
            node_budget=node_budget,
            kinds={key: item["type"] for key, item in self.items.items()},
        )
        self.conditions, self.routes, self.last_goals = {}, {}, {}
        self.established_nodes = {}
        self.operation_cache = {node: self.operation(node) for node in self.nodes}
        self.inspect_context()
        self.analyze()

    def inspect_declarations(self):
        for node, declaration in self.binding["nodes"].items():
            definition = self.definitions[node]
            if declaration["kind"] != definition["type"]:
                self.issues.append(issue("incompatible", "native-kind", node))
            for capability in declaration["capabilities"]:
                signature = self.signatures.get(capability["signature"])
                checked = check_capability(
                    definition,
                    capability["signature"],
                    capability["fields"],
                    signatures=self.signatures,
                    criterion_capacity=self.context.get("criterion_capacity"),
                )
                if checked["status"] != "compatible":
                    self.issues.append(
                        issue(
                            checked["status"],
                            "capability",
                            node,
                            signature=capability["signature"],
                            gaps=checked["gaps"],
                            unknown_properties=checked.get("unknown_properties", []),
                        )
                    )
                    if checked["status"] == "incompatible" or signature is None:
                        continue
                kind = guarantee(signature)
                floors = guarantee_minima(signature)
                floor_checks = [
                    check_capability(
                        definition,
                        "guarantee-minimum",
                        capability["fields"],
                        signatures={"guarantee-minimum": floor},
                        criterion_capacity=self.context.get("criterion_capacity"),
                    )
                    for floor in floors
                ]
                if floor_checks and not any(
                    row["status"] == "compatible" for row in floor_checks
                ):
                    floor_check = next(
                        (
                            row
                            for row in floor_checks
                            if row["status"] == "not-established"
                        ),
                        floor_checks[0],
                    )
                    self.issues.append(
                        issue(
                            floor_check["status"],
                            "guarantee-minimum",
                            node,
                            guarantee=kind,
                            gaps=floor_check["gaps"],
                            unknown_properties=floor_check.get(
                                "unknown_properties", []
                            ),
                        )
                    )
                    if floor_check["status"] == "incompatible":
                        continue
                if kind is None:
                    self.issues.append(
                        issue(
                            "not-established",
                            "operation-guarantee",
                            node,
                            signature=capability["signature"],
                        )
                    )
                    continue
                if (
                    "assessment" in kind
                    and kind != "upstream-quality"
                    and declaration["role"] != "judge"
                ):
                    self.issues.append(
                        issue("incompatible", "independent-assessment-role", node)
                    )
                effective = copy.deepcopy(signature)
                for floor in floors:
                    for name, specification in floor.get("fields", {}).items():
                        effective.setdefault("fields", {}).setdefault(
                            name, specification
                        )
                self.capabilities[kind].append((node, capability["fields"], effective))

    def inspect_context(self):
        domains = {
            "goal_kind": {"member-task", "pre-validation-remediation", "epic-closeout"},
            "workflow_owner": {"epic-handler", "epic-validator"},
        }
        for meaning, values in domains.items():
            if meaning in self.context and (
                not isinstance(self.context[meaning], str)
                or self.context[meaning] not in values
            ):
                self.issues.append(
                    issue(
                        "incompatible",
                        "context-discriminator",
                        meaning,
                        value=self.context[meaning],
                    )
                )
        for node, contract in self.operation_cache.items():
            for field, meaning in contract.get("discriminators", {}).items():
                if meaning not in self.context:
                    continue
                item = self.items.get((node, field), {})
                expected = self.context[meaning]
                if not isinstance(expected, str) or expected not in item.get(
                    "choices", []
                ):
                    self.issues.append(
                        issue(
                            "incompatible",
                            "context-discriminator",
                            node,
                            item=field,
                            value=expected,
                            discriminator=meaning,
                        )
                    )

    def continuity_established(self, node, fields):
        item = self.items.get(
            (
                node,
                fields.get(
                    "assessment-ordinal-continuity", "assessment-ordinal-continuity"
                ),
            ),
            {},
        )
        return any(
            item.get("operation_id") == specification.get("operation_id")
            and item.get("operation_digest") == specification.get("operation_digest")
            for signature in capability_signatures().values()
            if signature.get("guarantee") == "review-control"
            for logical, specification in signature.get("fields", {}).items()
            if logical == "assessment-ordinal-continuity"
        )

    def topological_order(self):
        degree = dict.fromkeys(self.nodes, 0)
        forward = defaultdict(list)
        for node, placement in self.nodes.items():
            edges = list(placement.get("routes", {}).values())
            if "next" in placement:
                edges.append({"to": placement["next"], "effect": "advance"})
            for edge in edges:
                if edge["effect"] == "advance":
                    forward[node].append(edge["to"])
                    degree[edge["to"]] += 1
        queue = deque(node for node, count in degree.items() if count == 0)
        order = []
        while queue:
            node = queue.popleft()
            order.append(node)
            for target in forward[node]:
                degree[target] -= 1
                if degree[target] == 0:
                    queue.append(target)
        if len(order) != len(self.nodes):
            raise BundleError(
                "not-established",
                "Native advance cycle needs a supported analysis contract",
                {"property": "advance-cycle"},
            )
        self.forward = forward
        return order

    def predicate(self, node, item, **predicate):
        return self.logic.predicate((node, item), predicate)

    def guards(self, guards):
        return self.logic.all(
            *(
                self.predicate(
                    guard["evidence"]["node"],
                    guard["evidence"]["item"],
                    **{key: value for key, value in guard.items() if key != "evidence"},
                )
                for guard in guards
            )
        )

    def analyze(self):
        logic = self.logic
        incoming = dict.fromkeys(self.nodes, 0)
        incoming[self.document["graph"]["entry"]] = 1
        goals = {node: {} for node in self.nodes}
        for identifier in self.order:
            node, definition = self.nodes[identifier], self.definitions[identifier]
            self.current_property = ("native-completion-and-path", identifier)
            condition = incoming[identifier]
            skipped = 0
            if node.get("skip", {}).get("allowed"):
                executes = self.predicate(identifier, "@execute", equals=True)
                skipped = logic.all(condition, logic.negate(executes))
                condition = logic.all(condition, executes)
            for item in definition.get("items", []):
                if (
                    item.get("required_when")
                    and (identifier, item["id"]) in logic.indices
                ):
                    when = logic.all(
                        *(
                            self.predicate(
                                identifier,
                                row["item"],
                                **{
                                    key: value
                                    for key, value in row.items()
                                    if key != "item"
                                },
                            )
                            for row in item["required_when"]
                        )
                    )
                    # The presence relation is native Action-completion behavior.
                    variable = self.logic.indices[(identifier, item["id"])]
                    present = logic.node(
                        variable,
                        [int(value is not ABSENT) for value in logic.domains[variable]],
                    )
                    condition = logic.all(
                        condition, logic.any(logic.negate(when), present)
                    )
            for item in definition.get("items", []):
                if (
                    item["type"] != "check_result"
                    or (identifier, item["id"]) not in logic.indices
                ):
                    continue
                required_now = (
                    1
                    if item.get("required")
                    else (
                        logic.all(
                            *(
                                self.predicate(
                                    identifier,
                                    row["item"],
                                    **{
                                        key: value
                                        for key, value in row.items()
                                        if key != "item"
                                    },
                                )
                                for row in item["required_when"]
                            )
                        )
                        if item.get("required_when")
                        else 0
                    )
                )
                accepted = logic.any(
                    *(
                        self.predicate(identifier, item["id"], equals=value)
                        for value in item["accepted_outcomes"]
                    )
                )
                condition = logic.all(
                    condition, logic.any(logic.negate(required_now), accepted)
                )
            for record, fields, _ in self.capabilities["review-control"]:
                if record != identifier or not self.continuity_established(
                    record, fields
                ):
                    continue
                field = fields.get(
                    "assessment-ordinal-continuity", "assessment-ordinal-continuity"
                )
                variable = logic.indices[(identifier, field)]
                present = logic.node(
                    variable,
                    [int(value is not ABSENT) for value in logic.domains[variable]],
                )
                passed = logic.all(
                    present,
                    self.equal(record, fields, "assessment-ordinal-continuity", "pass"),
                )
                completed = logic.any(
                    self.equal(record, fields, "review-operation", "complete"),
                    self.equal(record, fields, "review-operation", "waived"),
                )
                # The recognized operation verifies a completed assessment's
                # next ordinal. A faithful pass cannot describe an incomplete
                # operation consuming a completed ordinal.
                condition = logic.all(
                    condition, logic.any(logic.negate(passed), completed)
                )
            if self.operation_cache[identifier].get("owned_correction"):
                eligible = []
                for row in node.get("evidence_from", []):
                    field = "local-correction-eligibility"
                    if (row["node"], field) in self.items and (
                        "items" not in row or field in row["items"]
                    ):
                        eligible.append(
                            self.predicate(row["node"], field, equals="pass")
                        )
                if eligible:
                    # This exact verifier checks the frozen owned delta and its
                    # existing whole-set authority. A faithful pass cannot call
                    # an ineligible delta a locally verified correction.
                    condition = logic.all(
                        condition,
                        logic.any(
                            self.predicate(
                                identifier,
                                "coverage-relationship",
                                not_equals="review-predates-local-correction",
                            ),
                            self.predicate(
                                identifier,
                                "low-disposition-verification",
                                not_equals="pass",
                            ),
                            logic.any(*eligible),
                        ),
                    )
            for field, meaning in (
                self.operation_cache[identifier].get("discriminators", {}).items()
            ):
                if meaning in self.context:
                    condition = logic.all(
                        condition,
                        self.predicate(identifier, field, equals=self.context[meaning]),
                    )
            for record, fields, _ in self.capabilities["review-control"]:
                if record != identifier or not self.continuity_established(
                    record, fields
                ):
                    continue
                ordinal = fields.get("assessment-ordinal", "assessment-ordinal")
                current_limited = self.predicate(record, ordinal, at_most=4)
                prior_candidates = []
                for source, aliases, _ in [(record, fields, None)] + self.capabilities[
                    "review-routing"
                ]:
                    prior = aliases.get(
                        "prior-assessment-ordinal", "prior-assessment-ordinal"
                    )
                    if (source, prior) not in self.items:
                        continue
                    connected = (
                        1
                        if source == record
                        else self.conditions.get(source, 0)
                        if any(
                            row["node"] == source
                            and ("items" not in row or prior in row["items"])
                            for row in self.nodes[record].get("evidence_from", [])
                        )
                        else 0
                    )
                    prior_candidates.append(
                        logic.all(connected, self.predicate(source, prior, at_least=4))
                    )
                # The recognized continuity operation verifies the next ordinal.
                # Its passing result entails this threshold relation; the static
                # declaration does not establish that the operation actually ran.
                if prior_candidates:
                    passed = self.equal(
                        record, fields, "assessment-ordinal-continuity", "pass"
                    )
                    condition = logic.all(
                        condition,
                        logic.any(
                            logic.negate(passed),
                            current_limited,
                            logic.any(*prior_candidates),
                        ),
                    )
            self.conditions[identifier] = condition
            self.last_goals[identifier] = goals[identifier]
            choices = (
                definition.get("options", [])
                if definition["type"] == "decision"
                else [{"id": None}]
            )
            compiled = {
                option["id"]: logic.all(
                    condition, self.guards(option.get("guards", []))
                )
                for option in choices
            }
            forwards = [
                option["id"]
                for option in choices
                if definition["type"] == "decision"
                and node["routes"][option["id"]]["effect"] == "advance"
            ]
            event_needed = bool(definition.get("assessment")) or any(
                identifier == row[0] for row in self.capabilities["approval"]
            )
            if not event_needed:
                event_needed = any(
                    logic.all(compiled[left], compiled[right])
                    for index, left in enumerate(forwards)
                    for right in forwards[index + 1 :]
                )
            for option in choices:
                selected = compiled[option["id"]]
                if definition["type"] == "decision":
                    if event_needed:
                        selected = logic.all(
                            selected,
                            self.predicate(identifier, "@option", equals=option["id"]),
                        )
                    edge = node["routes"][option["id"]]
                    self.routes[(identifier, option["id"])] = selected
                elif "next" in node:
                    selected = logic.any(selected, skipped)
                    edge = {"to": node["next"], "effect": "advance"}
                else:
                    continue
                if edge["effect"] != "advance":
                    continue
                target = edge["to"]
                incoming[target] = logic.any(incoming[target], selected)
                assessment = definition.get("assessment")
                if assessment and assessment.get("target") == "session_goal":
                    key = identifier, option["id"], assessment["outcomes"][option["id"]]
                    goals[target][key] = logic.any(goals[target].get(key, 0), selected)
                else:
                    for key, value in goals[identifier].items():
                        goals[target][key] = logic.any(
                            goals[target].get(key, 0), logic.all(value, selected)
                        )

    def require(self, condition, expected, property_name, location):
        self.current_property = (property_name, location)
        bad = self.logic.all(condition, self.logic.negate(expected))
        if bad:
            certain = self.logic.certain(bad)
            status = "incompatible" if certain else "not-established"
            self.issues.append(
                issue(
                    status,
                    property_name,
                    location,
                    counterexample=self.logic.witness(certain or bad),
                )
            )
        return not bad

    def equal(self, node, fields, logical, value):
        return self.predicate(node, fields.get(logical, logical), equals=value)

    def approval_route(self, node, logical):
        aliases = next(
            (
                fields
                for owner, fields, _ in self.capabilities["approval"]
                if owner == node
            ),
            {},
        )
        return self.routes.get((node, aliases.get(logical, logical)), 0)

    def final_facts(self, node, fields):
        return self.logic.all(
            self.conditions[node],
            *(
                self.equal(node, fields, logical, value)
                for logical, value in [
                    ("judge-goal-outcome", "achieved"),
                    ("judge-verdict", "pass"),
                    ("judge-unmet-criteria", 0),
                    ("judge-unverified-criteria", 0),
                    ("judge-applicability", "pass"),
                ]
            ),
        )

    def present(self, node, item):
        if (node, item) not in self.logic.indices:
            return (
                1
                if self.items.get((node, item), {}).get("required")
                else self.logic.unknown((node, item, "presence"))
            )
        variable = self.logic.indices[(node, item)]
        return self.logic.node(
            variable,
            [int(value is not ABSENT) for value in self.logic.domains[variable]],
        )

    def delivery_items(self, node):
        declared = [
            endpoint["item"]
            for obligation in self.binding["obligations"].values()
            for endpoint in obligation["producers"]
            if endpoint["node"] == node
        ]
        assessment_fields = [
            fields.get(name, name)
            for kind, values in self.capabilities.items()
            if "assessment" in kind
            for owner, fields, signature in values
            if owner == node
            for name in signature["fields"]
            if name
            in {
                "judge-applicability",
                "judge-checkpoint-result",
                "judge-group-result",
                "judge-goal-outcome",
                "judge-assessment",
            }
        ]
        return (
            declared
            or assessment_fields
            or self.operation_cache.get(node, {}).get("delivery_items", [])
        )

    def evidence_reaches(self, producer, consumer, item=None):
        """Follow exact selected endpoints through established faithful relays."""
        items = [item] if item is not None else self.delivery_items(producer)
        tokens = {
            (producer, item): self.logic.all(
                self.conditions[producer], self.present(producer, item)
            )
            for item in items
        }
        reached = 0
        for current in self.order:
            if current == producer:
                continue
            selected = []
            for row in self.nodes[current].get("evidence_from", []):
                for (source, field), value in tokens.items():
                    if source == row["node"] and (
                        "items" not in row or field in row["items"]
                    ):
                        selected.append(value)
            reached = self.logic.all(
                self.conditions[current], self.logic.any(*selected)
            )
            if current == consumer:
                return reached
            outputs = list(
                self.operation_cache.get(current, {}).get("relay_outputs", [])
            )
            for kind, values in self.capabilities.items():
                if "assessment" in kind:
                    outputs += [
                        fields.get("judge-assessment", "judge-assessment")
                        for node, fields, _ in values
                        if node == current
                    ]
            for output in outputs:
                tokens[(current, output)] = self.logic.all(
                    reached, self.present(current, output)
                )
        return 0

    def established_derivation(self, definition, contract):
        proof = contract.get("derivation")
        if not proof:
            return False
        original = proof["definition"]
        inherited = self.established_operations.get(sha256(canonical_json(original)))
        if inherited is None:
            return False
        actual = copy.deepcopy(original)
        fields = proof["local_fields"]
        for item in actual.get("items", []):
            item["id"] = fields.get(item["id"], item["id"])
            for condition in item.get("required_when", []):
                condition["item"] = fields.get(condition["item"], condition["item"])
        for option in actual.get("options", []):
            for guard in option.get("guards", []):
                endpoint = guard["evidence"]
                node, item = endpoint["node"], endpoint["item"]
                endpoint["node"] = proof["nodes"].get(node, node)
                endpoint["item"] = proof["fields"].get(node, {}).get(item, item)
        expected = copy.deepcopy(inherited)
        for key in ("relay_outputs", "delivery_items"):
            if key in expected:
                expected[key] = [fields.get(field, field) for field in expected[key]]
        for key in ("discriminators", "output_scopes"):
            if key in expected:
                expected[key] = {
                    fields.get(field, field): value
                    for field, value in expected[key].items()
                }
        return actual == definition and all(
            value == expected.get(key)
            for key, value in contract.items()
            if key != "derivation"
        )

    def operation(self, node):
        declaration, definition = self.binding["nodes"][node], self.definitions[node]
        restored = copy.deepcopy(definition)
        aliases = {}
        for capability in declaration["capabilities"]:
            for logical, physical in capability["fields"].items():
                aliases[physical] = logical
        for item in restored.get("items", []):
            item["id"] = aliases.get(item["id"], item["id"])
            for condition in item.get("required_when", []):
                condition["item"] = aliases.get(condition["item"], condition["item"])
        direct = self.operations.get(sha256(canonical_json(definition)))
        contract = (
            direct
            if direct is not None
            else self.operations.get(sha256(canonical_json(restored)), {})
        )
        if declaration["role"] not in contract.get("roles", []):
            return {}
        contract = copy.deepcopy(contract)
        established = self.established_operations
        original_contract = established.get(sha256(canonical_json(restored)))
        derived = self.established_derivation(definition, contract)
        known = (
            sha256(canonical_json(definition)) in established
            or original_contract is not None
            or derived
        )
        if direct is not None and original_contract is not None and not derived:
            expected = copy.deepcopy(original_contract)
            reverse = {logical: physical for physical, logical in aliases.items()}
            for field in ("relay_outputs", "delivery_items"):
                if field in expected:
                    expected[field] = [
                        reverse.get(item, item) for item in expected[field]
                    ]
            for field in ("discriminators", "output_scopes"):
                if field in expected:
                    expected[field] = {
                        reverse.get(item, item): value
                        for item, value in expected[field].items()
                    }
            if any(
                value != expected.get(key)
                for key, value in contract.items()
                if key != "derivation"
            ):
                self.issues.append(
                    issue("incompatible", "operation-contract-conflict", node)
                )
                known = False
        self.established_nodes[node] = known
        if not known:
            if contract.get("review_recovery") and not (
                any(
                    owner == node for owner, _, _ in self.capabilities["review-control"]
                )
                and any(
                    owner == node for owner, _, _ in self.capabilities["review-routing"]
                )
            ):
                self.issues.append(
                    issue("not-established", "review-recovery-operation", node)
                )
                contract.pop("review_recovery", None)
            items = {item["id"]: item for item in definition.get("items", [])}
            if contract.get("owned_correction"):
                verified = any(
                    item.get("type") == "check_result"
                    and item.get("operation_id") == original.get("operation_id")
                    and item.get("operation_digest") == original.get("operation_digest")
                    for item in items.values()
                    for native in capability_signatures().values()
                    for name, original in native.get("fields", {}).items()
                    if name == "low-disposition-verification"
                )
                if not verified:
                    self.issues.append(
                        issue("not-established", "owned-correction-operation", node)
                    )
                    contract.pop("owned_correction", None)
            for output in list(contract.get("relay_outputs", [])):
                item = items.get(output, {})
                faithful_shape = (
                    item.get("type") == "artifact"
                    and item.get("required")
                    and "application/json" in item.get("allowed_media_types", [])
                    and any(
                        row.get("required", True)
                        for row in self.nodes[node].get("evidence_from", [])
                    )
                )
                if not faithful_shape:
                    self.issues.append(
                        issue(
                            "not-established",
                            "faithful-relay-operation",
                            node,
                            item=output,
                        )
                    )
                    contract["relay_outputs"].remove(output)
            if contract.get("user_directions"):
                # A custom direction must consume actual user acceptance evidence;
                # its option name or a contract map cannot itself grant effects.
                for option in list(contract["user_directions"]):
                    guards = next(
                        (
                            row.get("guards", [])
                            for row in definition.get("options", [])
                            if row["id"] == option
                        ),
                        [],
                    )
                    user = any(
                        guard.get("equals") == "user"
                        and any(
                            source == guard["evidence"]["node"]
                            and aliases.get("acceptance-source", "acceptance-source")
                            == guard["evidence"]["item"]
                            for source, aliases, _ in self.capabilities["acceptance"]
                        )
                        for guard in guards
                    )
                    if not user:
                        self.issues.append(
                            issue(
                                "not-established",
                                "user-direction-operation",
                                node,
                                option=option,
                            )
                        )
                        del contract["user_directions"][option]
        for key in ("relay_outputs", "delivery_items"):
            if direct is not None:
                continue
            reverse = {logical: physical for physical, logical in aliases.items()}
            contract[key] = [
                reverse.get(field, field) for field in contract.get(key, [])
            ]
        return contract

    def effect(self, node):
        declaration, definition = self.binding["nodes"][node], self.definitions[node]
        contract = self.operation_cache.get(node, {})
        established = self.established_nodes.get(node, False)
        if {"work", "covered-work"} & set(declaration["effects"]) and not established:
            return "work"
        if definition["type"] == "decision":
            return "control"
        if declaration["role"] == "judge" and any(
            node == value[0]
            for kind, values in self.capabilities.items()
            if "assessment" in kind
            for value in values
        ):
            return "assessment"
        contract = self.operation_cache.get(node, {})
        if contract:
            if declaration["role"] == "worker" and contract["effect"] != "work":
                return "unknown"
            return contract["effect"]
        return (
            "work"
            if "work" in declaration["effects"]
            or "covered-work" in declaration["effects"]
            else "unknown"
        )

    def inspect_goals(self):
        self.current_property = ("native-goal-mappings", "graph")
        native = {
            node: definition["assessment"]["outcomes"]
            for node, definition in self.definitions.items()
            if definition.get("assessment", {}).get("target") == "session_goal"
        }
        bound = {
            value["node"]: value["outcomes"]
            for value in self.binding["goal_assessments"]
        }
        if self.document.get("goal_tracking") is not True or native != bound:
            self.issues.append(issue("incompatible", "native-goal-mappings", "graph"))
        finals = self.capabilities["final-assessment"]
        final_conditions = {
            node: self.final_facts(node, fields) for node, fields, _ in finals
        }
        positions = {node: index for index, node in enumerate(self.order)}
        for terminal, placement in self.nodes.items():
            if not placement.get("terminal"):
                continue
            covered = self.logic.any(*self.last_goals[terminal].values())
            self.require(
                self.conditions[terminal],
                covered,
                "native-goal-before-terminal",
                terminal,
            )
            for (goal, option, outcome), condition in self.last_goals[terminal].items():
                if outcome != "achieved":
                    continue
                self.current_property = (
                    "current-final-assessment-and-forward-effects",
                    goal + "." + option,
                )
                qualified = []
                for assessor, _, _ in finals:
                    candidate = self.logic.all(condition, final_conditions[assessor])
                    if not candidate:
                        continue
                    valid = final_conditions[assessor]
                    for work in self.nodes:
                        if self.effect(work) not in {"work", "unknown"}:
                            continue
                        if positions[work] > positions[assessor]:
                            valid = self.logic.all(
                                valid,
                                self.logic.any(
                                    self.logic.negate(self.conditions[work]),
                                    self.logic.unknown((work, "harmless-effect"))
                                    if self.effect(work) == "unknown"
                                    else 0,
                                ),
                            )
                        else:
                            # A required original work producer needs an evidence
                            # connection, including grouped/conditional paths.
                            valid = self.logic.all(
                                valid,
                                self.logic.any(
                                    self.logic.negate(self.conditions[work]),
                                    self.evidence_reaches(work, assessor),
                                    self.logic.unknown((work, "harmless-effect"))
                                    if self.effect(work) == "unknown"
                                    else 0,
                                ),
                            )
                    qualified.append(valid)
                proven = self.logic.any(*qualified)
                self.require(
                    condition,
                    proven,
                    "current-final-assessment-and-forward-effects",
                    goal + "." + option,
                )
                self.inspect_review(condition, goal)
        self.achieved = self.logic.any(
            *(
                condition
                for terminal, placement in self.nodes.items()
                if placement.get("terminal")
                for (_, _, outcome), condition in self.last_goals[terminal].items()
                if outcome == "achieved"
            )
        )
        expected_outcome = self.context.get("expected_outcome", "achieved")
        if not isinstance(expected_outcome, str) or expected_outcome not in {
            "achieved",
            "not_achieved",
            "superseded",
        }:
            self.issues.append(issue("incompatible", "context-goal-outcome", "graph"))
        if expected_outcome == "achieved" and not self.achieved:
            self.issues.append(
                issue("incompatible", "feasible-achieved-continuation", "graph")
            )
        expected = self.logic.any(
            *(
                condition
                for terminal, placement in self.nodes.items()
                if placement.get("terminal")
                for (_, _, outcome), condition in self.last_goals[terminal].items()
                if outcome == expected_outcome
            )
        )
        if expected_outcome != "achieved" and not expected:
            self.issues.append(
                issue("incompatible", "feasible-expected-continuation", "graph")
            )
        self.inspect_reentry()
        self.inspect_obligations()
        self.inspect_acceptance()
        self.inspect_application()
        self.inspect_finalization()
        self.inspect_bootstrap()
        self.inspect_review_recovery()
        for closeout in self.binding["closeout"]:
            for required in closeout["requires"]:
                self.require(
                    self.logic.all(self.conditions[closeout["node"]], self.achieved),
                    self.conditions[required],
                    "closeout-required-placement",
                    closeout["node"],
                )
        self.inspect_confirmation_scope()
        for required in self.context.get("due_capabilities", []):
            if not self.capabilities.get(required):
                self.issues.append(issue("not-established", "due-capability", required))
            else:
                self.require(
                    self.achieved,
                    self.logic.any(
                        *(
                            self.conditions[node]
                            for node, _, _ in self.capabilities[required]
                        )
                    ),
                    "due-capability-execution-path",
                    required,
                )

    def inspect_reentry(self):
        """Check retained gates against actual native target-and-later invalidation."""
        logic = self.logic
        positions = {node: index for index, node in enumerate(self.order)}
        gates = [
            (node, "final-assessment")
            for node, _, _ in self.capabilities["final-assessment"]
        ]
        gates += [(node, "approval") for node, _, _ in self.capabilities["approval"]]
        gates += [
            (node, "application-approval")
            for node, _, _ in self.capabilities["application-approval"]
        ]
        reentries = [
            (node, edge["to"], self.routes[(node, option)])
            for node, placement in self.nodes.items()
            for option, edge in placement.get("routes", {}).items()
            if edge["effect"] == "rework"
        ]
        for target in self.document.get("manual_rework", {}).get("allowed_targets", []):
            reentries += [
                (source, target, self.conditions[source])
                for source in self.nodes
                if self.forward_reaches(target, source)
            ]
        for source, target, selected in reentries:
            self.current_property = ("native-reentry-gate", source)
            suffix = {node for node in self.nodes if self.forward_reaches(target, node)}
            reset = {key for key in logic.indices if key[0] in suffix}
            for gate, meaning in gates:
                if positions[gate] >= positions[target] or not self.forward_reaches(
                    gate, target
                ):
                    continue
                changes = [
                    node
                    for node in suffix
                    if positions[node] > positions[gate]
                    and self.forward_reaches(node, source)
                    and self.effect(node) in {"work", "unknown"}
                    and not (
                        meaning == "approval"
                        and any(
                            node == application
                            for application, _, _ in self.capabilities[
                                "application-approval"
                            ]
                        )
                    )
                ]
                dirty = logic.any(
                    *(
                        logic.all(
                            selected,
                            self.conditions[gate],
                            self.conditions[node],
                            logic.unknown((node, "product-changing-effect"))
                            if self.effect(node) == "unknown"
                            else 1,
                        )
                        for node in changes
                    )
                )
                if not dirty:
                    continue
                retained = logic.project(dirty, reset)
                incoming = dict.fromkeys(self.nodes, 0)
                incoming[target] = retained
                renewals = {node for node, _, _ in self.capabilities[meaning]}
                for node in self.order:
                    condition = incoming[node]
                    if not condition:
                        continue
                    if node in renewals:
                        connected = logic.all(
                            *(self.evidence_reaches(work, node) for work in changes)
                        )
                        basis_proofs = []
                        for original in self.binding["obligations"].values():
                            if original["assessor"] != gate:
                                continue
                            applicable = []
                            for endpoint in original["producers"]:
                                producer, item = endpoint["node"], endpoint["item"]
                                specification = self.items.get((producer, item), {})
                                required = (
                                    1
                                    if specification.get("required")
                                    else (
                                        logic.all(
                                            *(
                                                self.predicate(
                                                    producer,
                                                    row["item"],
                                                    **{
                                                        key: value
                                                        for key, value in row.items()
                                                        if key != "item"
                                                    },
                                                )
                                                for row in specification[
                                                    "required_when"
                                                ]
                                            )
                                        )
                                        if specification.get("required_when")
                                        else int(
                                            endpoint
                                            in self.context.get(
                                                "required_endpoints", []
                                            )
                                        )
                                    )
                                )
                                applicable.append(
                                    logic.all(self.conditions[producer], required)
                                )
                            alternatives = []
                            for row in self.binding["obligations"].values():
                                if (
                                    row["assessor"] != node
                                    or row["source"] != original["source"]
                                ):
                                    continue
                                current = [
                                    endpoint
                                    for endpoint in row["producers"]
                                    if positions[endpoint["node"]] >= positions[target]
                                ]
                                alternatives.append(
                                    logic.all(
                                        logic.any(
                                            *(
                                                logic.all(
                                                    self.conditions[endpoint["node"]],
                                                    self.present(
                                                        endpoint["node"],
                                                        endpoint["item"],
                                                    ),
                                                )
                                                for endpoint in current
                                            )
                                        ),
                                        *(
                                            logic.any(
                                                logic.negate(
                                                    logic.all(
                                                        self.conditions[
                                                            endpoint["node"]
                                                        ],
                                                        self.present(
                                                            endpoint["node"],
                                                            endpoint["item"],
                                                        ),
                                                    )
                                                ),
                                                self.evidence_reaches(
                                                    endpoint["node"],
                                                    node,
                                                    endpoint["item"],
                                                ),
                                            )
                                            for endpoint in current
                                        ),
                                    )
                                )
                            basis_proofs.append(
                                logic.any(
                                    logic.negate(logic.any(*applicable)),
                                    logic.any(*alternatives),
                                )
                            )
                        current_basis = logic.all(*basis_proofs) if basis_proofs else 0
                        condition = logic.all(
                            condition, logic.negate(logic.any(connected, current_basis))
                        )
                        if not condition:
                            continue
                    placement = self.nodes[node]
                    if placement.get("terminal"):
                        self.require(
                            logic.all(condition, self.achieved),
                            0,
                            "native-reentry-retained-gate",
                            source,
                        )
                    if "next" in placement:
                        incoming[placement["next"]] = logic.any(
                            incoming[placement["next"]], condition
                        )
                    for option, edge in placement.get("routes", {}).items():
                        if edge["effect"] == "advance":
                            advanced = logic.all(
                                condition, self.routes.get((node, option), 0)
                            )
                            incoming[edge["to"]] = logic.any(
                                incoming[edge["to"]], advanced
                            )

    def inspect_review_recovery(self):
        if self.binding["family"] not in {
            "task",
            "goal",
            "validation",
        } and not self.context.get("review_required"):
            return
        excluded = set(self.context.get("review", {}).get("excluded_recovery", []))
        for review, fields, _ in self.capabilities["review-control"]:
            states = self.items.get(
                (review, fields.get("review-operation", "review-operation")), {}
            ).get("choices", [])
            if not {"incomplete", "failed"} & set(states):
                continue
            available = set(self.operation_cache[review].get("review_recovery", []))
            for node, contract in self.operation_cache.items():
                if self.forward_reaches(review, node):
                    available.update(contract.get("review_recovery", []))
                    available.update(contract.get("user_directions", {}).values())
            for required in {
                "same-operation-recovery",
                "review-route-change",
            } - excluded:
                if required not in available:
                    self.issues.append(
                        issue(
                            "not-established",
                            "selected-review-recovery",
                            review,
                            capability=required,
                        )
                    )

    def inspect_obligations(self):
        for identifier, obligation in self.binding["obligations"].items():
            self.current_property = ("original-obligation-evidence", identifier)
            assessor = obligation["assessor"]
            if assessor is None or not any(
                assessor == row[0]
                for kind, values in self.capabilities.items()
                if "assessment" in kind
                for row in values
            ):
                self.issues.append(
                    issue("not-established", "original-obligation-assessor", identifier)
                )
                continue
            for endpoint in obligation["producers"] + obligation["evidence"]:
                if (endpoint["node"], endpoint["item"]) not in self.items:
                    self.issues.append(
                        issue(
                            "incompatible",
                            "original-obligation-endpoint",
                            identifier,
                            endpoint=endpoint,
                        )
                    )
            if identifier in self.context.get("required_obligations", []):
                self.require(
                    self.achieved,
                    self.conditions[assessor],
                    "due-original-assessment-path",
                    identifier,
                )
            decision = obligation["decision"]
            if self.definitions[decision]["type"] != "decision":
                self.issues.append(
                    issue("incompatible", "original-obligation-decision", identifier)
                )
            for endpoint in obligation["producers"]:
                producer = endpoint["node"]
                item = self.items.get((producer, endpoint["item"]), {})
                applicable = self.conditions[assessor]
                if not item.get("required"):
                    when = item.get("required_when", [])
                    if when:
                        applicable = self.logic.all(
                            applicable,
                            self.logic.all(
                                *(
                                    self.predicate(
                                        producer,
                                        condition["item"],
                                        **{
                                            key: value
                                            for key, value in condition.items()
                                            if key != "item"
                                        },
                                    )
                                    for condition in when
                                )
                            ),
                        )
                    elif endpoint not in self.context.get("required_endpoints", []):
                        continue
                self.require(
                    self.logic.all(self.conditions[producer], applicable),
                    self.evidence_reaches(producer, assessor, endpoint["item"]),
                    "original-producer-evidence",
                    identifier,
                )
            required_producers = [
                endpoint
                for endpoint in obligation["producers"]
                if self.items.get((endpoint["node"], endpoint["item"]), {}).get(
                    "required"
                )
                or endpoint in self.context.get("required_endpoints", [])
            ]
            if required_producers:
                self.require(
                    self.logic.all(self.conditions[assessor], self.achieved),
                    self.logic.any(
                        *(
                            self.logic.all(
                                self.conditions[endpoint["node"]],
                                self.present(endpoint["node"], endpoint["item"]),
                            )
                            for endpoint in required_producers
                        )
                    ),
                    "applicable-original-producer",
                    identifier,
                )
            consuming = [
                candidate
                for candidate in self.nodes
                if self.definitions[candidate]["type"] == "decision"
                and any(
                    row["node"] == assessor and row.get("required", True)
                    for row in self.nodes[candidate].get("evidence_from", [])
                )
            ]
            # A declared outgoing checkpoint may first check operational status;
            # the semantic result may be consumed by the following Decision.
            reachable, pending = set(), [decision]
            while pending:
                current = pending.pop()
                if current in reachable:
                    continue
                reachable.add(current)
                if self.effect(current) in {"control", "evidence"}:
                    pending.extend(self.forward[current])
            self.require(
                self.logic.all(self.conditions[assessor], self.achieved),
                self.logic.any(
                    *(
                        self.evidence_reaches(assessor, node)
                        for node in consuming
                        if node in reachable
                    )
                ),
                "assessment-decision-evidence",
                identifier,
            )

    def inspect_review(self, condition, location):
        if self.binding["family"] not in {
            "task",
            "goal",
            "validation",
        } and not self.context.get("review_required"):
            return
        route = self.context.get("review", {}).get("route")
        if route is not None and route not in {
            "herdr",
            "mulgae",
            "independent-review",
            "waived",
        }:
            self.issues.append(
                issue("incompatible", "selected-review-route", location, route=route)
            )
        valid = []
        for node, fields, _ in self.capabilities["review-control"]:
            eq = lambda key, value, node=node, fields=fields: self.equal(
                node, fields, key, value
            )
            ordinal = fields.get("assessment-ordinal", "assessment-ordinal")
            completed = self.logic.any(
                eq("review-operation", "complete"), eq("review-operation", "waived")
            )
            mode = self.logic.any(
                self.logic.all(
                    self.predicate(node, ordinal, at_least=1),
                    self.predicate(node, ordinal, at_most=3),
                    eq("assessment-kind", "work-unit"),
                    eq("review-mode", "remediation-eligible"),
                ),
                self.logic.all(
                    self.predicate(node, ordinal, at_least=4),
                    eq("assessment-kind", "remediation-confirmation"),
                    eq("review-mode", "confirmation-only"),
                ),
            )
            native = self.logic.all(
                self.conditions[node],
                completed,
                mode,
                eq("assessment-ordinal-continuity", "pass"),
            )
            if self.binding["family"] == "goal":
                substitute = self.logic.all(
                    eq("goal-kind", "epic-closeout"),
                    eq("review-evidence-kind", "validated-closeout"),
                )
                valid.append(self.logic.any(native, substitute))
            else:
                valid.append(native)
        self.require(
            condition, self.logic.any(*valid), "selected-review-control", location
        )
        routing = []
        for node, fields, _ in self.capabilities["review-routing"]:
            if (
                node,
                fields.get("route-binding-result", "route-binding-result"),
            ) in self.items:
                proof = self.equal(node, fields, "route-binding-result", "pass")
            else:
                planned = self.logic.all(
                    self.equal(
                        node, fields, "route-authorization-basis", "approved-plan"
                    ),
                    self.equal(
                        node, fields, "prior-review-operation", "not-applicable"
                    ),
                    self.equal(node, fields, "prior-review-route", "not-applicable"),
                    self.equal(
                        node, fields, "prior-route-change-readiness", "not-applicable"
                    ),
                )
                continued = self.logic.all(
                    self.predicate(
                        node,
                        fields.get(
                            "route-authorization-basis", "route-authorization-basis"
                        ),
                        not_equals="approved-plan",
                    ),
                    self.equal(node, fields, "route-direction-continuity", "pass"),
                )
                proof = self.logic.any(planned, continued)
            if self.binding["family"] == "goal":
                proof = self.logic.any(
                    proof,
                    self.logic.all(
                        self.equal(node, fields, "goal-kind", "epic-closeout"),
                        self.equal(
                            node, fields, "review-evidence-kind", "validated-closeout"
                        ),
                    ),
                )
            routing.append(self.logic.all(self.conditions[node], proof))
        self.require(
            condition,
            self.logic.any(*routing),
            "review-route-result-continuity",
            location,
        )
        for node, fields, _ in self.capabilities["review-control"]:
            ordinal = fields.get("assessment-ordinal", "assessment-ordinal")
            extra = self.logic.all(
                condition,
                self.conditions[node],
                self.predicate(node, ordinal, at_least=5),
            )
            if (
                node,
                fields.get("review-evidence-kind", "review-evidence-kind"),
            ) in self.items:
                extra = self.logic.all(
                    extra,
                    self.equal(node, fields, "review-evidence-kind", "native-review"),
                )
            authority = fields.get(
                "extra-assessment-authority-reference",
                "extra-assessment-authority-reference",
            )
            if (node, authority) in self.items:
                self.require(
                    extra,
                    self.predicate(node, authority, non_empty=True),
                    "extra-confirmation-authority",
                    node,
                )
            elif extra:
                alternatives = []
                for routing_node, aliases, _ in self.capabilities["review-routing"]:
                    field = aliases.get(
                        "extra-assessment-authority-reference",
                        "extra-assessment-authority-reference",
                    )
                    if (routing_node, field) in self.items:
                        alternatives.append(
                            self.logic.all(
                                self.conditions[routing_node],
                                self.predicate(routing_node, field, non_empty=True),
                            )
                        )
                self.require(
                    extra,
                    self.logic.any(*alternatives),
                    "extra-confirmation-authority",
                    node,
                )

    def inspect_acceptance(self):
        family = self.binding["family"]
        if family not in {"goal", "validation"}:
            return
        logic = self.logic
        meaning = "goal_kind" if family == "goal" else "workflow_owner"
        for node, fields, _ in self.capabilities["approval"]:
            accepted = logic.any(
                *(
                    self.approval_route(node, option)
                    for option in ["approved", "delegated"]
                )
            )
            eligible = []
            for source, contract in self.operation_cache.items():
                for field, discriminator in contract.get("discriminators", {}).items():
                    if discriminator != meaning:
                        continue
                    expected = self.context.get(meaning)
                    value = (
                        self.predicate(source, field, equals=expected)
                        if expected is not None
                        else 1
                    )
                    policy = (
                        self.predicate(source, field, not_equals="epic-closeout")
                        if family == "goal"
                        else self.predicate(source, field, equals="epic-handler")
                    )
                    eligible.append(
                        logic.all(
                            value, policy, self.evidence_reaches(source, node, field)
                        )
                    )
            # Native outcome identity, never a terminal or option spelling, owns
            # the stopped boundary. A new later assessment replaces old mappings.
            stopped = logic.any(
                *(
                    self.conditions[source]
                    for source, contract in self.operation_cache.items()
                    if contract.get("acceptance_policy") == "user-only-boundary"
                    and self.forward_reaches(source, node)
                )
            )
            not_stopped = logic.negate(stopped)
            candidates = []
            for record, aliases, _ in self.capabilities["acceptance"]:
                user = self.equal(record, aliases, "acceptance-source", "user")
                delegation = self.equal(
                    record, aliases, "acceptance-source", "epic-delegation"
                )
                candidates.append(
                    logic.all(
                        self.evidence_reaches(
                            record,
                            node,
                            aliases.get("acceptance-source", "acceptance-source"),
                        ),
                        logic.any(
                            user,
                            logic.all(delegation, logic.any(*eligible), not_stopped),
                        ),
                    )
                )
            self.require(
                accepted, logic.any(*candidates), "acceptance-provenance", node
            )

    def unchanged_between(self, start, end, *, exclude=()):
        valid = 1
        for node in self.order[self.order.index(start) + 1 : self.order.index(end)]:
            if node not in exclude and self.effect(node) in {"work", "unknown"}:
                harmless = (
                    self.logic.unknown((node, "harmless-effect"))
                    if self.effect(node) == "unknown"
                    else 0
                )
                valid = self.logic.all(
                    valid,
                    self.logic.any(self.logic.negate(self.conditions[node]), harmless),
                )
        return valid

    def inspect_application(self):
        logic = self.logic
        approvals = [
            (node, self.approval_route(node, "approved"))
            for node, _, _ in self.capabilities["approval"]
        ]
        for application, fields, _ in self.capabilities["application-approval"]:
            current_approval = logic.any(
                *(
                    logic.all(condition, self.unchanged_between(node, application))
                    for node, condition in approvals
                    if self.order.index(node) < self.order.index(application)
                )
            )
            self.require(
                self.conditions[application],
                current_approval,
                "exact-approval-before-current-application",
                application,
            )
            result = self.equal(
                application, fields, "application-approval-result", "pass"
            )
            for node, _, _ in self.capabilities["final-assessment"]:
                if self.order.index(node) > self.order.index(application):
                    # A later renewed approval and application can supersede this
                    # application, but a Judge alone cannot renew approved bytes.
                    alternatives = [
                        logic.all(result, self.unchanged_between(application, node))
                    ]
                    for later, later_fields, _ in self.capabilities[
                        "application-approval"
                    ]:
                        if (
                            self.order.index(application)
                            < self.order.index(later)
                            < self.order.index(node)
                        ):
                            alternatives.append(
                                logic.all(
                                    self.conditions[later],
                                    self.equal(
                                        later,
                                        later_fields,
                                        "application-approval-result",
                                        "pass",
                                    ),
                                    self.unchanged_between(later, node),
                                )
                            )
                    self.require(
                        logic.all(self.conditions[node], self.conditions[application]),
                        logic.any(*alternatives),
                        "current-application-verification",
                        node,
                    )

    def inspect_finalization(self):
        if self.binding["family"] not in {"task", "goal", "validation"}:
            return
        logic = self.logic
        for terminal, placement in self.nodes.items():
            if not placement.get("terminal"):
                continue
            achieved = logic.any(
                *(
                    condition
                    for (_, _, outcome), condition in self.last_goals[terminal].items()
                    if outcome == "achieved"
                )
            )
            approvals = []
            for approval, _, _ in self.capabilities["approval"]:
                accepted = logic.any(
                    *(
                        self.approval_route(approval, option)
                        for option in (
                            ("approved",)
                            if self.binding["family"] == "task"
                            else ("approved", "delegated")
                        )
                    )
                )
                if self.order.index(approval) >= self.order.index(terminal):
                    continue
                for node in self.order[self.order.index(approval) + 1 :]:
                    if self.effect(node) in {"work", "unknown"}:
                        accepted = logic.all(
                            accepted,
                            logic.any(
                                logic.negate(self.conditions[node]),
                                logic.unknown((node, "harmless-effect"))
                                if self.effect(node) == "unknown"
                                else 0,
                            ),
                        )
                approvals.append(accepted)
            self.require(
                achieved, logic.any(*approvals), "current-final-acceptance", terminal
            )

    def forward_reaches(self, start, target):
        visited, pending = set(), [start]
        while pending:
            node = pending.pop()
            if node == target:
                return True
            if node not in visited:
                visited.add(node)
                pending.extend(self.forward[node])
        return False

    def inspect_confirmation_scope(self):
        logic = self.logic
        for review, fields, _ in self.capabilities["review-control"]:
            exhausted = self.equal(review, fields, "review-mode", "confirmation-only")
            local = 0
            local_field = fields.get(
                "local-correction-eligibility", "local-correction-eligibility"
            )
            item = self.items.get((review, local_field), {})
            if (
                item.get("operation_id") == "aquarium-local-correction-eligibility"
                and item.get("operation_digest")
                == "sha256:c5d1ce604e86d6768f498be4618d6d30935d0b3134ab5290ebbcd0ac82f11c13"
            ):
                local = self.predicate(review, local_field, equals="pass")

            def fresh_before(destination, review=review):
                return logic.any(
                    *(
                        self.routes.get((node, option), 0)
                        for node, contract in self.operation_cache.items()
                        if self.forward_reaches(review, node)
                        and self.order.index(node) <= self.order.index(destination)
                        for option, meaning in contract.get(
                            "user_directions", {}
                        ).items()
                        if meaning == "product-correction"
                    )
                )

            for node in self.nodes:
                if self.effect(node) in {"work", "unknown"} and self.forward_reaches(
                    review, node
                ):
                    owned = 0
                    if self.operation_cache[node].get("owned_correction"):
                        owned = logic.any(
                            local,
                            self.predicate(
                                node,
                                "coverage-relationship",
                                not_equals="review-predates-local-correction",
                            ),
                        )
                    permitted = logic.any(fresh_before(node), owned)
                    applicable = self.logic.all(
                        self.conditions[node],
                        self.conditions[review],
                        exhausted,
                        self.achieved
                        if self.operation_cache[node].get("owned_correction")
                        else 1,
                    )
                    self.require(
                        applicable,
                        permitted,
                        "fresh-direction-after-confirmation",
                        node,
                    )
                for option, edge in self.nodes[node].get("routes", {}).items():
                    if edge["effect"] != "rework" or not self.forward_reaches(
                        review, node
                    ):
                        continue
                    # Ordinary declared goal/evidence/approval rework retains its
                    # original scope. This check concerns review-driven product
                    # remediation, identified through selected review-mode evidence.
                    mode_item = fields.get("review-mode", "review-mode")
                    review_driven = any(
                        row["node"] == review
                        and ("items" not in row or mode_item in row["items"])
                        for row in self.nodes[node].get("evidence_from", [])
                    )
                    final_sources = {
                        source for source, _, _ in self.capabilities["final-assessment"]
                    }
                    if any(
                        guard["evidence"]["node"] in final_sources
                        for choice in self.definitions[node].get("options", [])
                        for guard in choice.get("guards", [])
                    ):
                        review_driven = False
                    if not review_driven:
                        continue
                    direction = (
                        self.operation_cache[node]
                        .get("user_directions", {})
                        .get(option)
                    )
                    if direction in {
                        "same-operation-recovery",
                        "review-route-change",
                        "new-review-authority",
                    }:
                        continue
                    replayed_work = [
                        work
                        for work in self.nodes
                        if self.effect(work) in {"work", "unknown"}
                        and self.forward_reaches(edge["to"], work)
                        and self.forward_reaches(work, node)
                    ]
                    if replayed_work:
                        owned = all(
                            self.operation_cache[work].get("owned_correction")
                            for work in replayed_work
                        )
                        if owned:
                            # Native rework invalidates the verifier suffix. Its
                            # next attempt must establish whole-set authority
                            # again; prior attempt values cannot authorize it.
                            continue
                        owned_basis = (
                            logic.any(
                                local,
                                *(
                                    self.predicate(
                                        work,
                                        "coverage-relationship",
                                        not_equals="review-predates-local-correction",
                                    )
                                    for work in replayed_work
                                ),
                            )
                            if owned
                            else 0
                        )
                        permitted = logic.any(fresh_before(node), owned_basis)
                        self.require(
                            logic.all(self.routes[(node, option)], exhausted),
                            permitted,
                            "fresh-direction-before-product-rework",
                            node + "." + option,
                        )

    def inspect_bootstrap(self):
        for node, fields, _ in self.capabilities["suitability-bootstrap"]:
            if node != self.document["graph"]["entry"]:
                self.issues.append(issue("incompatible", "initial-bootstrap", node))
            passed = self.logic.all(
                self.conditions[node],
                *(
                    self.equal(node, fields, key, value)
                    for key, value in [
                        ("suitability-verdict", "pass"),
                        ("suitability-unmet", 0),
                        ("suitability-unverified", 0),
                        ("suitability-current", "pass"),
                    ]
                ),
            )
            for work in self.nodes:
                if self.effect(work) in {"work", "unknown"}:
                    self.require(
                        self.conditions[work], passed, "suitability-before-work", work
                    )

    def result(self):
        status = (
            "incompatible"
            if any(row["status"] == "incompatible" for row in self.issues)
            else "not-established"
            if self.issues
            else "compatible"
        )
        return {
            "status": status,
            "issues": self.issues,
            "analysis": {
                "placements": len(self.nodes),
                "symbolic_nodes": len(self.logic.nodes),
            },
            "limits": [
                "Native validity is a separate exact-source check.",
                "Faithfully recorded caller evidence is assumed; declarations authenticate no agent or approval.",
                "Runtime evidence, independent suitability and remaining authority stay due.",
            ],
        }


def qualify(
    document,
    binding,
    *,
    context=None,
    signatures=None,
    operation_contracts=None,
    node_budget=200000,
):
    """Qualify a natively checked exact source; no providers, files or sessions."""
    context = {} if context is None else context
    registry = capability_signatures()
    supplied_signatures = {
        **(signatures or {}),
        **binding.get("capability_definitions", {}),
    }
    conflicts = [
        key
        for key, value in supplied_signatures.items()
        if key in registry and registry[key] != value
    ]
    if conflicts:
        return {
            "status": "incompatible",
            "issues": [
                issue("incompatible", "capability-contract-conflict", key)
                for key in conflicts
            ],
        }
    registry = {**registry, **supplied_signatures}
    contracts = json.loads(
        (ASSETS / "adaptive/operation-contracts-v1.json").read_text()
    )
    supplied = {
        **(operation_contracts or {}),
        **binding.get("semantic_contracts", {}),
        **context.get("operation_contracts", {}),
    }
    conflicting = [
        key
        for key, value in supplied.items()
        if key in contracts and contracts[key] != value
    ]
    if conflicting:
        return {
            "status": "incompatible",
            "issues": [
                issue("incompatible", "operation-contract-conflict", key)
                for key in conflicting
            ],
        }
    contracts = {**contracts, **supplied}
    analysis = None
    try:
        validate_definition(binding)
        check_shapes(document, binding)
        check_graph(document)
        if set(binding["nodes"]) != {node["id"] for node in document["graph"]["nodes"]}:
            return {
                "status": "incompatible",
                "issues": [
                    issue("incompatible", "binding-placement-coverage", "nodes")
                ],
            }
        analysis = Qualification.__new__(Qualification)
        analysis.__init__(document, binding, context, registry, contracts, node_budget)
        analysis.inspect_goals()
        return analysis.result()
    except AnalysisLimit as error:
        issues = list(getattr(analysis, "issues", []))
        property_name, location = getattr(
            analysis, "current_property", ("initialization", "graph")
        )
        issues.append(
            issue(
                "not-established",
                "analysis-resource",
                location,
                resource=str(error),
                during=property_name,
            )
        )
        return {
            "status": "incompatible"
            if any(row["status"] == "incompatible" for row in issues)
            else "not-established",
            "issues": issues,
        }
    except DefinitionError as error:
        return {
            "status": "incompatible",
            "issues": [
                issue(
                    "incompatible", "binding-definition", "binding", detail=str(error)
                )
            ],
        }
    except BundleError as error:
        return {
            "status": error.code if error.code == "not-established" else "incompatible",
            "issues": [
                issue(error.code, "source-structure", "graph", detail=str(error))
            ],
        }
