"""Closed native predicate domains and shared guarded-path expressions.

The reduced decision graph retains correlations at merges. Its nodes represent
value partitions, not execution paths or a second workflow cursor.
"""

import json


class AnalysisLimit(Exception):
    """A resource limit leaves a proof unestablished, never successful."""


ABSENT = object()
OTHER = object()
UNKNOWN = object()
UNKNOWN_VARIABLE = object()


class Decisions:
    def __init__(self, domains, *, node_budget=200000, kinds=None):
        self.kinds = {} if kinds is None else kinds
        self.keys = list(domains)
        self.domains = list(domains.values())
        self.indices = {key: index for index, key in enumerate(self.keys)}
        self.nodes = [(float("inf"), ()), (float("inf"), ())]
        self.unique = {}
        self.cache = {}
        self.predicates = {}
        self.node_budget = node_budget
        self.unknowns = {}

    def node(self, variable, children):
        children = tuple(children)
        if len(set(children)) == 1:
            return children[0]
        key = variable, children
        if key not in self.unique:
            if len(self.nodes) >= self.node_budget:
                raise AnalysisLimit("symbolic-node-budget")
            self.unique[key] = len(self.nodes)
            self.nodes.append(key)
        return self.unique[key]

    def unknown(self, key):
        if key not in self.unknowns:
            index = len(self.keys)
            self.keys.append((UNKNOWN_VARIABLE, key))
            self.domains.append([False, True])
            self.unknowns[key] = self.node(index, [0, 1])
        return self.unknowns[key]

    @staticmethod
    def simplified(operation, a, b):
        if a == b:
            return a
        if operation == "and":
            if a == 0 or b == 0:
                return 0
            if a == 1:
                return b
            if b == 1:
                return a
        else:
            if a == 1 or b == 1:
                return 1
            if a == 0:
                return b
            if b == 0:
                return a
        return None

    def combine(self, operation, a, b):
        """Iterative apply avoids a Python recursion limit on native-sized graphs."""
        root = operation, min(a, b), max(a, b)
        stack = [root]
        while stack:
            key = stack[-1]
            if key in self.cache:
                stack.pop()
                continue
            operation, a, b = key
            result = self.simplified(operation, a, b)
            if result is not None:
                self.cache[key] = result
                stack.pop()
                continue
            variable = min(self.nodes[a][0], self.nodes[b][0])
            left = (
                self.nodes[a][1]
                if self.nodes[a][0] == variable
                else [a] * len(self.domains[variable])
            )
            right = (
                self.nodes[b][1]
                if self.nodes[b][0] == variable
                else [b] * len(self.domains[variable])
            )
            dependencies = [
                (operation, min(x, y), max(x, y)) for x, y in zip(left, right)
            ]
            missing = [
                dependency
                for dependency in dependencies
                if dependency not in self.cache
            ]
            if missing:
                stack.extend(missing)
            else:
                self.cache[key] = self.node(
                    variable, [self.cache[dependency] for dependency in dependencies]
                )
                stack.pop()
        return self.cache[root]

    def all(self, *values):
        result = 1
        for value in values:
            result = self.combine("and", result, value)
        return result

    def any(self, *values):
        result = 0
        for value in values:
            result = self.combine("or", result, value)
        return result

    def negate(self, expression):
        done = {0: 1, 1: 0}
        stack = [expression]
        while stack:
            current = stack[-1]
            if current in done:
                stack.pop()
                continue
            variable, children = self.nodes[current]
            missing = [child for child in children if child not in done]
            if missing:
                stack.extend(missing)
            else:
                done[current] = self.node(variable, [done[child] for child in children])
                stack.pop()
        return done[expression]

    def predicate(self, key, predicate):
        cache_key = key, json.dumps(predicate, sort_keys=True)
        if cache_key in self.predicates:
            return self.predicates[cache_key]
        kind = self.kinds.get(key)
        operators = {
            "confirm": {"equals", "not_equals"},
            "choice": {"equals", "not_equals"},
            "integer": {"equals", "not_equals", "at_least", "at_most"},
            "check_result": {"equals", "not_equals"},
            "text": {"empty", "non_empty"},
            "list": {"empty", "non_empty"},
            "artifact": set(),
        }
        operation = set(predicate) - {"field"}
        if kind in operators and not operation <= operators[kind]:
            result = 0
        elif key not in self.indices:
            result = self.unknown(cache_key)
        else:
            children = []
            for value in self.domains[self.indices[key]]:
                known = evaluate(value, predicate)
                children.append(
                    self.unknown(cache_key) if known is None else int(known)
                )
            result = self.node(self.indices[key], children)
        self.predicates[cache_key] = result
        return result

    def has_unknown(self, expression):
        pending, seen = [expression], set()
        while pending:
            current = pending.pop()
            if current < 2 or current in seen:
                continue
            seen.add(current)
            variable, children = self.nodes[current]
            if self.keys[variable][0] is UNKNOWN_VARIABLE:
                return True
            pending.extend(children)
        return False

    def project(self, expression, keys):
        """Existentially discard native suffix values invalidated at re-entry."""
        variables = {self.indices[key] for key in keys if key in self.indices}
        done, pending = {0: 0, 1: 1}, [expression]
        while pending:
            current = pending[-1]
            if current in done:
                pending.pop()
                continue
            variable, children = self.nodes[current]
            missing = [child for child in children if child not in done]
            if missing:
                pending.extend(missing)
                continue
            values = [done[child] for child in children]
            done[current] = (
                self.any(*values)
                if variable in variables
                else self.node(variable, values)
            )
            pending.pop()
        return done[expression]

    def certain(self, expression):
        """Retain counterexamples that do not depend on unresolved facts."""
        done = {0: 0, 1: 1}
        pending = [expression]
        while pending:
            current = pending[-1]
            if current in done:
                pending.pop()
                continue
            variable, children = self.nodes[current]
            missing = [child for child in children if child not in done]
            if missing:
                pending.extend(missing)
                continue
            values = [done[child] for child in children]
            done[current] = (
                self.all(*values)
                if self.keys[variable][0] is UNKNOWN_VARIABLE
                else self.node(variable, values)
            )
            pending.pop()
        return done[expression]

    def witness(self, expression):
        result = []
        while expression > 1:
            variable, children = self.nodes[expression]
            selected = next(index for index, child in enumerate(children) if child)
            value = self.domains[variable][selected]
            result.append(
                {
                    "field": ("unresolved", self.keys[variable][1])
                    if self.keys[variable][0] is UNKNOWN_VARIABLE
                    else self.keys[variable],
                    "value": "absent"
                    if value is ABSENT
                    else "unknown"
                    if value is UNKNOWN
                    else "other"
                    if value is OTHER
                    else value,
                }
            )
            expression = children[selected]
        return result


def evaluate(value, predicate):
    if value is ABSENT:
        # Released native evaluator marks absent evidence unevaluable. Such a
        # guard cannot admit a selection (ADR 0028 / native items.rs).
        return False
    if value is UNKNOWN:
        return None
    if "equals" in predicate or "not_equals" in predicate:
        wanted = predicate.get("equals", predicate.get("not_equals"))
        equal = value is not OTHER and type(value) is type(wanted) and value == wanted
        return equal if "equals" in predicate else not equal
    if "empty" in predicate or "non_empty" in predicate:
        empty = (
            False
            if value is OTHER
            else not (value.strip() if isinstance(value, str) else value)
        )
        return empty if "empty" in predicate else not empty
    if "at_least" in predicate or "at_most" in predicate:
        if not isinstance(value, int) or isinstance(value, bool):
            return None
        return (
            value >= predicate["at_least"]
            if "at_least" in predicate
            else value <= predicate["at_most"]
        )
    return None


def item_domain(item, predicates):
    kind = item["type"]
    if kind == "choice":
        values = list(item["choices"])
    elif kind == "check_result":
        values = ["pass", "fail", "inconclusive"]
    elif kind == "confirm":
        values = [True]
    elif kind == "integer":
        lower, upper = item.get("minimum", -(2**63)), item.get("maximum", 2**63 - 1)
        cuts = {lower, upper + 1}
        for predicate in predicates:
            for key in ("equals", "not_equals", "at_least", "at_most"):
                value = predicate.get(key)
                if isinstance(value, int) and not isinstance(value, bool):
                    cuts.update(
                        {
                            max(lower, min(upper + 1, value)),
                            max(lower, min(upper + 1, value + 1)),
                        }
                    )
        values = sorted(cuts - {upper + 1})
    elif kind == "text":
        values = []
        for predicate in predicates:
            value = predicate.get("equals", predicate.get("not_equals"))
            if (
                isinstance(value, str)
                and item.get("min_length", 0)
                <= len(value)
                <= item.get("max_length", 2**63)
                and value not in values
            ):
                values.append(value)
        if item.get("min_length", 0) == 0 and "" not in values:
            values.append("")
        if item.get("max_length", 1) > 0:
            values.append(OTHER)
    elif kind == "list":
        values = [[]] if item.get("min_items", 0) == 0 else []
        if item.get("max_items", 1) > 0:
            values.append(OTHER)
    else:
        values = [UNKNOWN]
    if not item.get("required", False):
        values.append(ABSENT)
    return values
