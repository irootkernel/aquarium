from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).parents[2] / "plugins/aquarium/skills/goal-evaluator/scripts"


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def assignment() -> dict:
    return {
        "schema": "aquarium.assignment/v3",
        "work": {"id": "TASK-001", "objective": "Assess current implementation"},
        "target": {"basis": "current candidate", "paths": ["src/app.py"]},
        "authority": {"allowed": ["Read original artifacts"], "excluded": ["Mutation"]},
        "procedure": None,
        "native": {"harness": "codex", "agent_handle": None, "model": None},
        "evidence": [{"source": "docs/requirements.md", "provenance": "original"}],
        "gaps": [],
        "role": "evaluator",
        "purpose": "Independently assess due requirements",
        "instructions": "Read original artifacts. Return actual gaps.\r\nKeep scope.",
        "checkpoint": "implementation",
        "deliverables": ["aquarium.evaluator-assessment/v3"],
        "success_criteria": ["Every due requirement is assessed"],
    }


def test_unknown_telemetry_needs_no_snapshot_or_source_read(assignment: dict) -> None:
    preparer = load("prepare_assignment")
    renderer = load("render_dispatch")
    prepared = preparer.prepare(Path("/unavailable/source/root"), assignment)
    assert prepared == assignment
    assignment["target"]["paths"].append("later.py")
    assert prepared["target"]["paths"] == ["src/app.py"]
    rendered = renderer.render_dispatch(prepared)
    assert rendered["schema"] == "aquarium.prepared-dispatch/v3"
    returned = json.loads(
        rendered["dispatch_text"][rendered["dispatch_text"].index("{") :]
    )
    assert returned == prepared
    assert returned["native"]["model"] is None
    assert set(rendered) == {"schema", "dispatch_text"}


@pytest.mark.parametrize(
    "field",
    [
        "work",
        "target",
        "authority",
        "native",
        "procedure",
        "evidence",
        "gaps",
        "instructions",
        "deliverables",
        "success_criteria",
        "checkpoint",
    ],
)
def test_missing_assignment_obligations_are_rejected(
    assignment: dict, field: str
) -> None:
    del assignment[field]
    with pytest.raises(ValueError):
        load("ordinary_assignment").prepare(assignment)


@pytest.mark.parametrize("mutation", ["role", "effects", "nonfinite"])
def test_invalid_scope_or_json_is_rejected(assignment: dict, mutation: str) -> None:
    if mutation == "role":
        assignment["role"] = "primary"
    elif mutation == "effects":
        assignment["authority"]["allowed"] = "implicit"
    else:
        assignment["target"]["value"] = float("nan")
    with pytest.raises(ValueError):
        load("ordinary_assignment").prepare(assignment)


@pytest.mark.parametrize("name", ["bind_prepared_delivery", "bind_claude_delivery"])
def test_formal_binders_reject_ordinary_input(assignment: dict, name: str) -> None:
    result = load(name).bind_delivery(assignment, {})
    assert result["acceptance_ready"] is False
    assert result["error"]["code"] == "INVALID_PREPARATION"


def test_cli_preparation_and_rendering_preserve_assignment(assignment: dict) -> None:
    expected = copy.deepcopy(assignment)
    prepared = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "prepare_assignment.py"),
            "--source-root",
            "/unavailable/source/root",
            "--input",
            "-",
        ],
        input=json.dumps(assignment),
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(prepared.stdout) == expected
    rendered = subprocess.run(
        [sys.executable, str(SCRIPTS / "render_dispatch.py"), "--input", "-"],
        input=prepared.stdout,
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(rendered.stdout)["schema"] == "aquarium.prepared-dispatch/v3"


@pytest.mark.parametrize("role", [[], {}])
@pytest.mark.parametrize("command", ["prepare_assignment", "render_dispatch"])
def test_cli_rejects_nonstring_role_without_traceback(
    assignment: dict, role: object, command: str
) -> None:
    assignment["role"] = role
    arguments = [sys.executable, str(SCRIPTS / f"{command}.py"), "--input", "-"]
    if command == "prepare_assignment":
        arguments.extend(["--source-root", "/unavailable/source/root"])
    result = subprocess.run(
        arguments,
        input=json.dumps(assignment),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr.startswith("error:")
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize(
    "version,roles",
    [("v2", ("worker", "judge")), ("v3", ("executor", "evaluator"))],
)
def test_versioned_assignments_preserve_their_original_role_domain(
    assignment: dict, version: str, roles: tuple[str, ...]
) -> None:
    preparer = load("prepare_assignment")
    renderer = load("render_dispatch")
    for role in roles:
        value = copy.deepcopy(assignment)
        value.update(schema=f"aquarium.assignment/{version}", role=role)
        kind = {
            "worker": "worker-handoff",
            "judge": "judge-assessment",
            "executor": "executor-handoff",
            "evaluator": "evaluator-assessment",
        }[role]
        value["deliverables"] = [f"aquarium.{kind}/{version}"]
        prepared = preparer.prepare(Path("/unavailable/source/root"), value)
        assert prepared == value
        rendered = renderer.render_dispatch(prepared)
        assert rendered["schema"] == f"aquarium.prepared-dispatch/{version}"
        returned = json.loads(
            rendered["dispatch_text"][rendered["dispatch_text"].index("{") :]
        )
        assert returned == value
    for role in {"worker", "judge", "executor", "evaluator", "coordinator"} - set(
        roles
    ):
        value = copy.deepcopy(assignment)
        value.update(schema=f"aquarium.assignment/{version}", role=role)
        with pytest.raises(ValueError):
            preparer.prepare(Path("/unavailable/source/root"), value)
        with pytest.raises(ValueError):
            renderer.render_dispatch(value)
