"""Flatten explicit definition imports; no execution or runtime library imports."""

import copy
import re

from adaptive_bundles import BundleError, contained, read_regular, sha256
from adaptive_definitions import ASSETS, definition_id, parse_definition

NATIVE_ID = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*")


def fail(message, code="incompatible"):
    raise BundleError(code, message)


def obj(value, name):
    if not isinstance(value, dict):
        fail(name + " must be an object", "invalid-input")
    return value


def rows(value, name):
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        fail(name + " must be a list of objects", "invalid-input")
    return value


def source_bytes(repository, reference):
    obj(reference, "Composition source reference")
    if "asset" in reference:
        path = contained(ASSETS, reference["asset"])
        raw = read_regular(ASSETS, path)
    else:
        path = contained(repository, reference["path"])
        raw = read_regular(repository, path)
    if sha256(raw) != reference["sha256"]:
        fail("Composition source changed", "source-drift")
    return raw


def endpoint_item(document, endpoint):
    obj(endpoint, "Item endpoint")
    nodes = {node["id"]: node for node in document["graph"]["nodes"]}
    node = nodes.get(endpoint["node"])
    if node is None:
        fail("Evidence endpoint names an unknown placement")
    definition = document["node_definitions"][node["use"]]
    items = {item["id"]: item for item in definition.get("items", [])}
    if endpoint.get("item") not in items:
        fail("Evidence endpoint names an unknown Action item")
    return items[endpoint["item"]]


def merge(target, values, name):
    if target.keys() & values.keys():
        fail("Composition " + name + " identities collide")
    target.update(values)


def scoped(namespace, identifier):
    result = namespace + "-" + identifier
    if len(result) > 64 or NATIVE_ID.fullmatch(result) is None:
        fail("Expanded identity violates the native identifier contract")
    return result


def check_shapes(document, mapping):
    if "manual_rework" in document:
        targets = obj(document["manual_rework"], "Manual rework").get(
            "allowed_targets", []
        )
        if not isinstance(targets, list) or any(
            not isinstance(target, str) for target in targets
        ):
            fail("Manual rework targets must be a list of placements", "invalid-input")
    obj(mapping.get("parameters", {}), "Binding parameters")
    rows(mapping.get("origins", []), "Binding origins")
    for definition in obj(document["node_definitions"], "node_definitions").values():
        obj(definition, "Native definition")
        for item in rows(definition.get("items", []), "Native items"):
            rows(item.get("required_when", []), "Native item conditions")
        for option in rows(definition.get("options", []), "Native options"):
            for guard in rows(option.get("guards", []), "Native guards"):
                obj(guard["evidence"], "Guard evidence")
    for node in rows(obj(document["graph"], "graph")["nodes"], "Placements"):
        rows(node.get("evidence_from", []), "Native evidence selectors")
        for route in obj(node.get("routes", {}), "Native routes").values():
            obj(route, "Native route")
    for node in obj(mapping["nodes"], "Binding nodes").values():
        obj(node, "Binding node")
        for capability in rows(node["capabilities"], "Capabilities"):
            obj(capability["fields"], "Capability aliases")
    for obligation in obj(mapping.get("obligations", {}), "Obligations").values():
        obj(obligation, "Obligation")
        rows(obligation["producers"], "Obligation producers")
        rows(obligation["evidence"], "Obligation evidence")
    rows(mapping.get("goal_assessments", []), "Goal boundaries")
    rows(mapping.get("closeout", []), "Closeout boundaries")


def expand(document, mapping, namespace, fields):
    """Rewrite only grammar-owned references, never narrative/operation identities."""
    check_shapes(document, mapping)
    document, mapping = copy.deepcopy(document), copy.deepcopy(mapping)
    definitions = obj(document["node_definitions"], "node_definitions")
    placements = rows(obj(document["graph"], "graph")["nodes"], "graph.nodes")
    node_ids = {node["id"]: scoped(namespace, node["id"]) for node in placements}
    definition_ids = {key: scoped(namespace, key) for key in definitions}
    aliases, definition_aliases = {}, {}
    for node in placements:
        renamed = obj(fields.get(node["id"], {}), "Item aliases")
        items = definitions[node["use"]].get("items", [])
        known = {item["id"] for item in items}
        if renamed.keys() - known:
            fail("Alias names an unknown item")
        if any(
            not isinstance(v, str) or NATIVE_ID.fullmatch(v) is None or len(v) > 64
            for v in renamed.values()
        ):
            fail("Item alias violates the native identifier contract")
        all_names = [renamed.get(item["id"], item["id"]) for item in items]
        if len(set(all_names)) != len(all_names):
            fail("Item aliases collapse distinct fields")
        if (
            node["use"] in definition_aliases
            and definition_aliases[node["use"]] != renamed
        ):
            fail("Shared definition has conflicting placement aliases")
        definition_aliases[node["use"]] = renamed
        aliases[node["id"]] = renamed
    if fields.keys() - node_ids.keys():
        fail("Alias names an unknown placement")

    def ep(value):
        old = value["node"]
        if old not in node_ids:
            fail("Imported evidence reference escapes its closed subgraph")
        if "item" in value:
            value["item"] = aliases[old].get(value["item"], value["item"])
        value["node"] = node_ids[old]

    for key, definition in definitions.items():
        renamed = definition_aliases.get(key, {})
        for item in definition.get("items", []):
            item["id"] = renamed.get(item["id"], item["id"])
            for condition in item.get("required_when", []):
                condition["item"] = renamed.get(condition["item"], condition["item"])
        for option in definition.get("options", []):
            for guard in option.get("guards", []):
                ep(guard["evidence"])
    for node in placements:
        old = node["id"]
        node["id"], node["use"] = node_ids[old], definition_ids[node["use"]]
        if "next" in node:
            if node["next"] not in node_ids:
                fail("Imported advance reference escapes its closed subgraph")
            node["next"] = node_ids[node["next"]]
        for route in node.get("routes", {}).values():
            if route["to"] in node_ids:
                route["to"] = node_ids[route["to"]]
            elif route["effect"] != "rework":
                fail("Imported advance route escapes its closed subgraph")
        for evidence in node.get("evidence_from", []):
            old_source = evidence["node"]
            if "items" in evidence:
                evidence["items"] = [
                    aliases.get(old_source, {}).get(item, item)
                    for item in evidence["items"]
                ]
            ep(evidence)
    document["node_definitions"] = {
        definition_ids[key]: value for key, value in definitions.items()
    }
    document["graph"]["entry"] = node_ids[document["graph"]["entry"]]
    if "manual_rework" in document:
        document["manual_rework"]["allowed_targets"] = [
            node_ids[node] for node in document["manual_rework"]["allowed_targets"]
        ]
    mapped = {}
    for key, value in obj(mapping["nodes"], "mapping.nodes").items():
        if key not in node_ids:
            fail("Imported binding names an unknown placement")
        for capability in value["capabilities"]:
            original = capability["fields"]
            capability["fields"] = {
                name: aliases[key].get(item, item) for name, item in original.items()
            }
            # A missing logical alias means the original item name, including
            # for explicitly defined operations whose signature is not bundled.
            for item, renamed in aliases[key].items():
                if item not in original:
                    capability["fields"][item] = renamed
        mapped[node_ids[key]] = value
    if set(mapping["nodes"]) != set(node_ids):
        fail("Imported binding does not map every placement")
    mapping["nodes"] = mapped
    obligations = {}
    for key, obligation in mapping.get("obligations", {}).items():
        for endpoint in obligation["producers"] + obligation["evidence"]:
            ep(endpoint)
        for field in ("assessor", "decision"):
            if obligation[field] is not None:
                obligation[field] = node_ids[obligation[field]]
        obligations[namespace + "-" + key] = obligation
    mapping["obligations"] = obligations
    for value in mapping.get("goal_assessments", []) + mapping.get("closeout", []):
        value["node"] = node_ids[value["node"]]
        if "requires" in value:
            value["requires"] = [node_ids[node] for node in value["requires"]]
    mapping["parameters"] = {
        namespace + "-" + key: value
        for key, value in mapping.get("parameters", {}).items()
    }
    return document, mapping, node_ids, aliases


def check_graph(document):
    """Check resolved references and evidence dominance independently of control wiring."""
    definitions = document["node_definitions"]
    nodes = {node["id"]: node for node in document["graph"]["nodes"]}
    if len(nodes) != len(document["graph"]["nodes"]):
        fail("Placement identities collide")
    entry = document["graph"]["entry"]
    if entry not in nodes:
        fail("Composed entry is unresolved")
    predecessors = {key: set() for key in nodes}
    forward = {key: set() for key in nodes}
    for node in nodes.values():
        if node["use"] not in definitions:
            fail("Composed definition reference is unresolved")
        routes = list(node.get("routes", {}).values())
        if "next" in node:
            routes.append({"to": node["next"], "effect": "advance"})
        for route in routes:
            if route["to"] not in nodes:
                fail("Composed control/rework target is unresolved")
            if route["effect"] == "advance":
                forward[node["id"]].add(route["to"])
                predecessors[route["to"]].add(node["id"])
    reachable, pending = set(), [entry]
    while pending:
        current = pending.pop()
        if current not in reachable:
            reachable.add(current)
            pending.extend(forward[current])
    if reachable != nodes.keys():
        fail("Composed graph contains unreachable placements")
    dominators = {node: ({entry} if node == entry else set(nodes)) for node in nodes}
    changed = True
    while changed:
        changed = False
        for node in nodes.keys() - {entry}:
            parents = predecessors[node]
            value = {node} | set.intersection(
                *(dominators[parent] for parent in parents)
            )
            if value != dominators[node]:
                dominators[node] = value
                changed = True
    for node in nodes.values():
        selected = node.get("evidence_from", [])
        for evidence in selected:
            producer = evidence["node"]
            if producer not in nodes:
                fail("Dangling evidence producer")
            source = definitions[nodes[producer]["use"]]
            items = {item["id"] for item in source.get("items", [])}
            if set(evidence.get("items", [])) - items:
                fail("Evidence selector names an unknown item")
            if evidence.get("required", True) and (
                producer not in dominators[node["id"]]
                or producer == node["id"]
                or "skip" in nodes[producer]
            ):
                fail("Required evidence is not available on every consumer path")
        definition = definitions[node["use"]]
        for option in definition.get("options", []):
            for guard in option.get("guards", []):
                endpoint = guard["evidence"]
                endpoint_item(document, endpoint)
                if not any(
                    evidence["node"] == endpoint["node"]
                    and evidence.get("required", True)
                    and endpoint["item"] in evidence.get("items", [])
                    for evidence in selected
                ):
                    fail("Guard evidence is not required and explicitly selected")
    for target in document.get("manual_rework", {}).get("allowed_targets", []):
        if target not in nodes:
            fail("Manual rework target is unresolved")


def assignable(producer, consumer):
    """Prove supported native value bounds; unresolved constraints stay explicit."""
    if producer["type"] != consumer["type"]:
        fail("Evidence item types differ")
    ignored = {"id", "prompt", "help", "required", "required_when"}
    handled = {"type"} | ignored
    for lower, upper in [
        ("minimum", "maximum"),
        ("min_length", "max_length"),
        ("min_items", "max_items"),
        ("min_item_length", "max_item_length"),
        ("min_total_length", "max_total_length"),
    ]:
        handled.update({lower, upper})
        for key, lower_bound in [(lower, True), (upper, False)]:
            if key not in consumer:
                continue
            if key not in producer:
                fail(
                    "Producer bounds do not establish input compatibility",
                    "not-established",
                )
            if (
                (producer[key] < consumer[key])
                if lower_bound
                else (producer[key] > consumer[key])
            ):
                fail("Producer bounds exceed the input contract")
    for key in ["choices", "accepted_outcomes", "allowed_media_types"]:
        handled.add(key)
        if key in consumer:
            if key not in producer:
                fail(
                    "Producer values do not establish input compatibility",
                    "not-established",
                )
            if not set(producer[key]) <= set(consumer[key]):
                fail("Producer values exceed the input contract")
    for key in ["operation_id", "operation_digest"]:
        handled.add(key)
        if producer.get(key) != consumer.get(key):
            fail("Evidence semantic operation identities differ")
    for key in (producer.keys() | consumer.keys()) - handled:
        if producer.get(key) != consumer.get(key):
            fail(
                "Additional item constraints need an explicit compatibility proof",
                "not-established",
            )


def parameter_values(declarations, values):
    obj(values, "Parameter values")
    if values.keys() - declarations.keys():
        fail("Undeclared parameter value")
    for key, declaration in declarations.items():
        if key not in values:
            if declaration["required"]:
                fail("Required composition parameter is unresolved", "not-established")
            continue
        value, kind = values[key], declaration["type"]
        valid = {
            "text": isinstance(value, str),
            "choice": isinstance(value, str),
            "integer": isinstance(value, int) and not isinstance(value, bool),
            "boolean": isinstance(value, bool),
            "artifact": isinstance(value, dict),
            "list": isinstance(value, list),
            "check_result": isinstance(value, dict),
        }[kind]
        if not valid:
            fail("Composition parameter type differs")


def _compose(repository, draft):
    """Return frozen source/mapping; origins remain provenance after preparation."""
    from adaptive_preparation import document

    specification = obj(draft.get("composition"), "composition")
    obj(specification.get("public_targets", {}), "Root public targets")
    result, mapping = copy.deepcopy(draft["document"]), copy.deepcopy(draft["mapping"])
    obj(result, "Composition root document")
    obj(mapping, "Composition root mapping")
    check_shapes(result, mapping)
    root_manual = set(result.get("manual_rework", {}).get("allowed_targets", []))
    root_definitions = set(result["node_definitions"])
    root_nodes = {node["id"] for node in result["graph"]["nodes"]}
    root_obligations = set(mapping["obligations"])
    parts, origins, bases, identities = {}, [], [], {}
    imported = rows(specification["components"], "composition.components")
    for component in imported:
        obj(component.get("public_targets", {}), "Component public targets")
        name = component["namespace"]
        if (
            not isinstance(name, str)
            or NATIVE_ID.fullmatch(name) is None
            or name == "root"
            or name in parts
        ):
            fail("Composition namespace is invalid or ambiguous")
        reference = component["source"]
        raw = source_bytes(repository, reference)
        if component["kind"] == "fragment":
            fragment = parse_definition(raw)
            if fragment["schema"] != "aquarium.procedure-fragment/v1":
                fail("Fragment import has the wrong definition kind")
            native = {
                "node_definitions": fragment["node_definitions"],
                "graph": {"entry": fragment["entry"], "nodes": fragment["placements"]},
            }
            bound = copy.deepcopy(obj(component["mapping"], "fragment mapping"))
            bound["parameters"] = copy.deepcopy(fragment["parameters"])
            check_shapes(native, bound)
            for assessor in fragment["assessors"]:
                if bound["nodes"][assessor["node"]]["role"] != "judge":
                    fail("Fragment assessor boundary does not map to a Judge")
                node = next(
                    node
                    for node in fragment["placements"]
                    if node["id"] == assessor["node"]
                )
                selected = {row["node"] for row in node.get("evidence_from", [])}
                if not set(assessor["covers"]) <= selected:
                    fail("Fragment assessor lacks declared original evidence")
            if bound.get("goal_assessments") or bound.get("closeout"):
                fail("Ordinary fragment mapping cannot claim session-level control")
            obj(bound["nodes"], "Fragment mapping nodes")
            for node in bound["nodes"].values():
                obj(node, "Fragment mapping node")
            if set(fragment["effects"]) - set().union(
                *(set(node["effects"]) for node in bound["nodes"].values())
            ):
                fail("Fragment effects are missing from its binding")
            parameter_values(fragment["parameters"], component.get("parameters", {}))
            identity = (fragment["id"], fragment["version"], sha256(raw))
            exits = fragment["exits"]
        elif component["kind"] == "whole":
            # document() preserves native YAML errors and approved source-byte checks.
            if "asset" in reference:
                import yaml

                try:
                    native = yaml.safe_load(raw)
                except (yaml.YAMLError, ValueError, RecursionError) as error:
                    raise BundleError(
                        "native-invalid", "Whole composition source is malformed"
                    ) from error
                obj(native, "Whole native document")
            else:
                _, native = document(repository, reference)
            bound = parse_definition(source_bytes(repository, component["binding"]))
            if (
                bound["schema"] != "aquarium.procedure-binding/v1"
                or bound["procedure"]["source_sha256"] != sha256(raw)
                or (native["id"], native["version"])
                != (bound["procedure"]["id"], bound["procedure"]["version"])
            ):
                fail("Whole source/binding identities differ")
            if bound["family"] != mapping["family"]:
                fail("Whole control family differs")
            fragment = None
            identity = (native["id"], native["version"], sha256(raw))
            parameter_values(bound["parameters"], component.get("parameters", {}))
            exits = obj(component.get("exits", {}), "Whole control exits")
        else:
            fail("Unknown composition input kind")
        semantic_identity = (
            bound["procedure"]["digest"]
            if fragment is None
            else definition_id(fragment)
        )
        if identities.get(identity[:2], semantic_identity) != semantic_identity:
            fail("Imported definition identity has conflicting source bytes")
        identities[identity[:2]] = semantic_identity
        if fragment is None and native.get("goal_tracking"):
            result["goal_tracking"] = True
        expanded, binding, identifiers, aliases = expand(
            native, bound, name, obj(component.get("fields", {}), "fields")
        )
        merge(result["node_definitions"], expanded["node_definitions"], "definition")
        result["graph"]["nodes"].extend(expanded["graph"]["nodes"])
        merge(mapping["nodes"], binding["nodes"], "binding placement")
        merge(mapping["obligations"], binding.get("obligations", {}), "obligation")
        merge(mapping["parameters"], binding.get("parameters", {}), "parameter")
        mapping["goal_assessments"].extend(binding.get("goal_assessments", []))
        mapping["closeout"].extend(binding.get("closeout", []))
        if "manual_rework" in expanded:
            targets = result.setdefault("manual_rework", {"allowed_targets": []})[
                "allowed_targets"
            ]
            targets.extend(
                target
                for target in expanded["manual_rework"]["allowed_targets"]
                if target not in targets
            )
        ports = {"inputs": {}, "outputs": {}}
        for kind, declared_ports in ports.items():
            for port, declaration in (
                fragment[kind]
                if fragment
                else obj(component.get(kind, {}), "Whole evidence ports")
            ).items():
                declaration = copy.deepcopy(obj(declaration, "Evidence port"))
                endpoint = obj(declaration["endpoint"], "Evidence port endpoint")
                old = endpoint["node"]
                endpoint["node"] = identifiers[old]
                endpoint["item"] = aliases[old].get(endpoint["item"], endpoint["item"])
                actual = endpoint_item(result, endpoint)
                if declaration["type"] != actual["type"]:
                    fail("Port declaration differs from its native item type")
                if (
                    kind == "outputs"
                    and declaration["required"]
                    and (not actual.get("required") or actual.get("required_when"))
                ):
                    fail(
                        "Required output port presence is not established: "
                        + name
                        + ".outputs."
                        + port,
                        "not-established",
                    )
                declared_ports[port] = declaration
        parts[name] = {
            "component": component,
            "fragment": fragment,
            "ids": identifiers,
            "ports": ports,
            "entry": expanded["graph"]["entry"],
            "exits": {key: identifiers[node] for key, node in exits.items()},
            "identity": identity,
            "aliases": aliases,
        }
        origin = {
            "id": identity[0],
            "version": identity[1],
            "sha256": identity[2],
            "source": reference.get("path", "asset:" + reference.get("asset", "")),
        }
        origins.append(origin)
        bases.append(
            {
                "reference": copy.deepcopy(reference),
                "sha256": sha256(raw),
                "binding": copy.deepcopy(component.get("binding")),
                "native_key": [
                    bound["procedure"][key] for key in ("id", "version", "digest")
                ]
                if fragment is None
                else None,
            }
        )
    qualified_aliases = {
        part["ids"][old]: aliases
        for part in parts.values()
        for old, aliases in part["aliases"].items()
    }

    def root_endpoint(endpoint):
        aliases = qualified_aliases.get(endpoint["node"], {})
        if "item" in endpoint:
            endpoint["item"] = aliases.get(endpoint["item"], endpoint["item"])

    for key in root_definitions:
        for option in result["node_definitions"][key].get("options", []):
            for guard in option.get("guards", []):
                root_endpoint(guard["evidence"])
    for node in result["graph"]["nodes"]:
        if node["id"] in root_nodes:
            for evidence in node.get("evidence_from", []):
                if "items" in evidence:
                    aliases = qualified_aliases.get(evidence["node"], {})
                    evidence["items"] = [
                        aliases.get(item, item) for item in evidence["items"]
                    ]
    for key in root_obligations:
        obligation = mapping["obligations"][key]
        for endpoint in obligation["producers"] + obligation["evidence"]:
            root_endpoint(endpoint)
    by_id = {node["id"]: node for node in result["graph"]["nodes"]}
    if len(by_id) != len(result["graph"]["nodes"]):
        fail("Expanded placement identities collide")

    def target(endpoint, *, public=False, source=False):
        obj(endpoint, "Control endpoint")
        if not isinstance(endpoint["component"], str):
            fail("Control component must be a string", "invalid-input")
        if public and any(key in endpoint for key in ("node", "exit", "option")):
            fail("Public rework endpoints require a declared target")
        if (
            not public
            and not source
            and any(key in endpoint for key in ("exit", "option", "target"))
        ):
            fail("Control destinations cannot select a source exit or option")
        if endpoint["component"] == "root":
            if public:
                node = specification.get("public_targets", {})[endpoint["target"]]
            else:
                if "exit" in endpoint or "target" in endpoint:
                    fail("Root control endpoints require a root placement")
                node = endpoint["node"]
            if not isinstance(node, str):
                fail("Root control placement must be a string", "invalid-input")
            if node not in root_nodes:
                fail("Root control endpoint does not belong to the root")
            return node
        part = parts[endpoint["component"]]
        if "node" in endpoint or (not public and "target" in endpoint):
            fail("Component control endpoints cannot select private placements")
        if public:
            declared = part["component"].get("public_targets", {})
            node = (
                part["ids"][declared[endpoint["target"]]]
                if endpoint["target"] != "entry"
                else part["entry"]
            )
        elif source:
            if "exit" not in endpoint:
                fail("Component control sources require a declared exit")
            if not isinstance(endpoint["exit"], str):
                fail("Control exit must be a string", "invalid-input")
            node = part["exits"][endpoint["exit"]]
        else:
            node = part["entry"]
        if node not in by_id:
            fail("Control port is dangling")
        return node

    wired_control = set()
    for edge in rows(specification.get("control", []), "control"):
        source, destination = target(edge["from"], source=True), target(edge["to"])
        node = by_id[source]
        kind = result["node_definitions"][node["use"]]["type"]
        if kind == "action":
            if "option" in edge["from"]:
                fail("Action control exits cannot select a Decision option")
            option = None
        elif kind == "decision":
            option = edge["from"]["option"]
            if not isinstance(option, str):
                fail("Decision control option must be a string", "invalid-input")
            options = {
                value["id"]
                for value in result["node_definitions"][node["use"]]["options"]
            }
            if option not in options or option not in node["routes"]:
                fail("Control port names an unknown Decision option")
        else:
            fail("Control source is not a native Action or Decision")
        control_key = (source, option)
        if control_key in wired_control:
            fail("Control port has ambiguous destinations")
        wired_control.add(control_key)
        if kind == "decision":
            node["routes"][option] = {"to": destination, "effect": "advance"}
        else:
            node.pop("terminal", None)
            node["next"] = destination
    if "entry" in specification:
        result["graph"]["entry"] = target(specification["entry"])
    used_inputs = set()
    for edge in rows(specification.get("evidence", []), "evidence"):
        producer, consumer = edge["from"], edge["to"]
        output = parts[producer["component"]]["ports"]["outputs"][producer["port"]]
        input_port = parts[consumer["component"]]["ports"]["inputs"][consumer["port"]]
        key = (consumer["component"], consumer["port"])
        if key in used_inputs:
            fail("Evidence input has ambiguous producers")
        used_inputs.add(key)
        actual = endpoint_item(result, output["endpoint"])
        expected = endpoint_item(result, input_port["endpoint"])
        if output["type"] != input_port["type"]:
            fail("Evidence port item types differ")
        assignable(actual, expected)
        if input_port["required"] and (
            not output["required"]
            or not actual.get("required")
            or actual.get("required_when")
        ):
            fail(
                "Required evidence input presence is not established: "
                + consumer["component"]
                + ".inputs."
                + consumer["port"],
                "not-established",
            )
        node = by_id[input_port["endpoint"]["node"]]
        evidence = node.setdefault("evidence_from", [])
        source = output["endpoint"]
        matching = [
            row
            for row in evidence
            if row["node"] == source["node"]
            and row.get("required", True) == input_port["required"]
        ]
        if any(
            "items" not in row or source["item"] in row["items"] for row in matching
        ):
            continue
        row = next((row for row in matching if len(row["items"]) < 16), None)
        if row is not None:
            row["items"].append(source["item"])
        elif len(evidence) < 8:
            evidence.append(
                {
                    "node": source["node"],
                    "required": input_port["required"],
                    "items": [source["item"]],
                }
            )
        else:
            fail("Evidence wiring exceeds the released native selector bounds")
    for name, part in parts.items():
        for key, port in part["ports"]["inputs"].items():
            if port["required"] and (name, key) not in used_inputs:
                fail("Required evidence port is unresolved", "not-established")
        fragment = part["fragment"]
        if fragment is None:
            continue
        declarations = fragment["external_rework"]
        supplied = obj(part["component"].get("rework", {}), "External rework bindings")
        if set(supplied) != {edge["port"] for edge in declarations.values()}:
            fail("External rework port is unresolved or undeclared")
        internal = {
            (part["ids"][edge["from"]], part["ids"][edge["to"]])
            for edge in fragment["internal_rework"]
        }
        actual_internal, actual_external = set(), set()
        for old, expanded_id in part["ids"].items():
            for route in by_id[expanded_id].get("routes", {}).values():
                if route["effect"] != "rework":
                    continue
                if route["to"] in part["ids"].values():
                    actual_internal.add((expanded_id, route["to"]))
                else:
                    port = route["to"]
                    if not any(
                        edge["from"] == old and edge["port"] == port
                        for edge in declarations.values()
                    ):
                        fail("Rework escapes a fragment's declared public contract")
                    route["to"] = target(supplied[port], public=True)
                    actual_external.add((old, port))
        if actual_internal != internal or actual_external != {
            (edge["from"], edge["port"]) for edge in declarations.values()
        }:
            fail("Fragment rework declarations differ from actual native routes")
        for dependency in fragment["dependencies"]:
            if not any(
                tuple(dependency[key] for key in ("id", "version", "sha256"))
                == value["identity"]
                for value in parts.values()
            ):
                fail("Exact fragment dependency is unresolved", "not-established")
    owners = {
        identifier: name
        for name, part in parts.items()
        for identifier in part["ids"].values()
    }
    for node in by_id.values():
        for route in node.get("routes", {}).values():
            destination = owners.get(route["to"])
            if (
                route["effect"] == "rework"
                and destination is not None
                and owners.get(node["id"]) != destination
            ):
                part = parts[destination]
                public = {part["entry"]} | {
                    part["ids"][value]
                    for value in part["component"].get("public_targets", {}).values()
                }
                if route["to"] not in public:
                    fail("Rework targets a private imported placement")
    for target_node in root_manual:
        owner = owners.get(target_node)
        if owner is not None:
            part = parts[owner]
            public = {part["entry"]} | {
                part["ids"][value]
                for value in part["component"].get("public_targets", {}).values()
            }
            if target_node not in public:
                fail("Manual rework targets a private imported placement")
    mapping["origins"].extend(origins)
    check_graph(result)
    return {
        "document": result,
        "mapping": mapping,
        "bases": bases,
        "origins": origins,
        "parameters": {
            part["component"]["namespace"]: copy.deepcopy(
                part["component"].get("parameters", {})
            )
            for part in parts.values()
        },
        "qualification": "TASK-141-exact-target-suitability-required",
    }


def compose(repository, draft):
    try:
        return _compose(repository, draft)
    except (KeyError, IndexError) as error:
        raise BundleError(
            "incompatible", "Composition contains an unresolved declaration or port"
        ) from error


def check_bases(repository, bases):
    """Recheck mutable preparation inputs, never origin libraries during resume."""
    for basis in bases:
        raw = source_bytes(repository, basis["reference"])
        if sha256(raw) != basis["sha256"]:
            fail("Composition input changed during preparation", "source-drift")
        if basis["binding"] is not None:
            source_bytes(repository, basis["binding"])


def verify_whole_sources(repository, bases, client, stage, descriptor):
    """Native tuple proof uses only the already authorized ignored stage."""
    import os

    from adaptive_preparation import write_new

    for basis in bases:
        if basis["native_key"] is None:
            continue
        raw = source_bytes(repository, basis["reference"])
        try:
            write_new(descriptor, "import.yaml", raw)
            if tuple(client.identity(stage / "import.yaml")) != tuple(
                basis["native_key"]
            ):
                fail("Imported whole source native tuple differs", "source-drift")
        finally:
            try:
                os.unlink("import.yaml", dir_fd=descriptor)
            except FileNotFoundError:
                pass
