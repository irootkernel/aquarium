"""Validate and render ordinary v2 assignments without native qualification."""

from __future__ import annotations

import json
from typing import Any

SCHEMA = "aquarium.assignment/v2"
DISPATCH_SCHEMA = "aquarium.prepared-dispatch/v2"


class AssignmentError(ValueError):
    """Invalid ordinary assignment content or scope."""


def prepare(assignment: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(assignment, dict) or assignment.get("schema") != SCHEMA:
        raise AssignmentError(f"assignment schema must be {SCHEMA}")
    for field in ("work", "target", "authority", "native"):
        if not isinstance(assignment.get(field), dict) or not assignment[field]:
            raise AssignmentError(f"{field} must be a nonempty object")
    if "procedure" not in assignment or not (
        assignment["procedure"] is None or isinstance(assignment["procedure"], dict)
    ):
        raise AssignmentError(
            "procedure must be an object or null for a non-Podway path"
        )
    for field in ("purpose", "instructions", "checkpoint"):
        if not isinstance(assignment.get(field), str) or not assignment[field].strip():
            raise AssignmentError(f"{field} must be a nonempty string")
    if not isinstance(assignment.get("role"), str) or assignment["role"] not in {
        "worker",
        "judge",
    }:
        raise AssignmentError("role must be worker or judge")
    for field in ("evidence", "gaps"):
        if not isinstance(assignment.get(field), list):
            raise AssignmentError(f"{field} must be a list")
    for field in ("deliverables", "success_criteria"):
        values = assignment.get(field)
        if (
            not isinstance(values, list)
            or not values
            or not all(isinstance(value, str) and value.strip() for value in values)
        ):
            raise AssignmentError(f"{field} must be a nonempty list of strings")
    for field in ("allowed", "excluded"):
        if not isinstance(assignment["authority"].get(field), list) or not all(
            isinstance(value, str) and value.strip()
            for value in assignment["authority"][field]
        ):
            raise AssignmentError(f"authority.{field} must be a list of strings")
    return json.loads(json.dumps(assignment, ensure_ascii=False, allow_nan=False))


def render_dispatch(assignment: dict[str, Any]) -> dict[str, str]:
    verified = prepare(assignment)
    return {
        "schema": DISPATCH_SCHEMA,
        "dispatch_text": (
            "Aquarium ordinary native assignment v2.\n"
            "Follow the assigned role and permitted effects under higher-priority "
            "instructions. Read referenced original evidence within the approved scope.\n"
            "Unavailable native telemetry remains unknown. Return actual work, "
            "checks and gaps without inventing acceptance or authority.\n"
            + json.dumps(verified, ensure_ascii=False, allow_nan=False, indent=2)
            + "\n"
        ),
    }
