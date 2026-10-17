"""Cross-family recovery with existing adapters; native records are synthetic."""

import copy
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "plugins/aquarium/shared"))
from adaptive_admission import reference_mapping
from adaptive_bundles import BundleError, sha256
from adaptive_definitions import ASSETS, canonical_json, definition_id
from adaptive_execution import execution_context
from adaptive_preparation import prepare
from adaptive_suitability import qualify_prepared
from test_adaptive_preparation_unit import Oracle, assignment

CASES = [
    ("task", "task", "task-handler", "implement"),
    ("goal", "goal", "epic-handler", "complete-work"),
    ("validation", "validation", "epic-validator", "audit"),
    ("design", "design", "new-feature", "discover"),
    ("design", "design", "new-project", "discover"),
    ("design", "design", "refactor", "discover"),
    ("diagnosis", "war-room", "war-room", "investigate"),
]


def fixture(repository, family, name, entrypoint, node):
    subprocess.run(["git", "init", "-q", str(repository)], check=True)
    value = assignment(repository, mode="prepare")
    source = repository / "definitions/origin with 한글.yaml"
    source.parent.mkdir()
    raw = (ASSETS / f"podway/procedures/aquarium-{name}-v2.yaml").read_bytes()
    source.write_bytes(raw)
    mapping = reference_mapping(raw)
    effects = sorted(
        {
            effect
            for declaration in mapping["nodes"].values()
            for effect in declaration["effects"]
        }
    )
    if family in {"task", "goal", "validation"}:
        value["authority"]["review"]["route"] = "herdr"
    plan = value["target"]["procedure_plan"]
    plan.update(
        family=family,
        entrypoint=entrypoint,
        effects=effects,
        review=copy.deepcopy(value["authority"]["review"]),
    )
    value["authority"]["effects"] = effects[:]
    plan["candidates"] = [
        {
            "path": str(source.relative_to(repository)),
            "sha256": sha256(raw),
            "coverage": [
                {**row, "obligation": next(iter(mapping["obligations"]))}
                for row in plan["drafts"][0]["coverage"]
            ],
            "reason": "Known exact source fits the original bounded fixture work.",
        }
    ]
    client = Oracle(repository)
    value = prepare(repository, value, client=client)["assignment"]
    retained = qualify_prepared(repository, value, client=client, retain=True)
    qualification = {
        "assignment": value,
        "pending_operations": [
            {
                "kind": "same-operation-retrieval",
                "reference": "existing native public handle",
                "ordinal_consumed": False,
            }
        ],
    }
    observation = {
        "status": {
            "procedure": retained["binding"]["procedure"],
            "session": {
                "id": str(uuid.uuid4()),
                "lifecycle": "prepared",
                "revision": 0,
            },
            "current": None,
        },
        "guidance": {"node": {"graph_node_id": node}, "readback": []},
        "active_items": [],
        "mutation_templates": [],
    }
    client.health = lambda: copy.deepcopy(observation)
    return source, client, qualification, observation, retained


@pytest.mark.parametrize("family,name,entrypoint,node", CASES)
def test_alias_and_mutated_origin_recover_prepared_then_running_without_new_judge(
    tmp_path, family, name, entrypoint, node
):
    source, client, qualification, observation, retained = fixture(
        tmp_path, family, name, entrypoint, node
    )
    original = Path(retained["retention"]["path"])
    alias = tmp_path / "approved alternative/.local" / original.name
    alias.parent.mkdir(parents=True)
    (alias.parent / ".gitignore").write_text("*\n")
    shutil.copytree(original, alias)
    source.write_text("mutated optional origin library")
    source.unlink()
    roots = ["definitions", "approved alternative"]

    def consume():
        return execution_context(
            tmp_path,
            roots=roots,
            entrypoint=entrypoint,
            qualification=qualification,
            client=client,
        )

    prepared = consume()
    assert prepared["status"] == "prepared-resolved" and prepared["dispatch"] is None
    assert prepared["qualification"]["status"] == "qualified-known"
    observation["status"]["session"].update(lifecycle="running", revision=2)
    current = consume()
    assert current["procedure"]["session"] == observation["status"]["session"]
    assert current["pending_operations"] == qualification["pending_operations"]
    assert current["node"] == node
    assert current["authority"] == qualification["assignment"]["authority"]
    assert current["qualification"]["status"] == "qualified-known"
    assert current["source_path"] in {
        str(original / "procedure.yaml"),
        str(alias / "procedure.yaml"),
    }


@pytest.mark.parametrize(
    "family,name,entrypoint,node", [CASES[index] for index in [0, 1, 2, 3, 6]]
)
def test_cross_root_conflicting_mapping_stops_before_work(
    tmp_path, family, name, entrypoint, node
):
    _source, client, qualification, observation, retained = fixture(
        tmp_path, family, name, entrypoint, node
    )
    binding = copy.deepcopy(retained["binding"])
    binding["parameters"]["preservation-purpose"] = {
        "type": "text",
        "required": False,
        "description": "A different definition mapping cannot share this native tuple.",
    }
    alias = tmp_path / "alternate/.local" / definition_id(binding)
    alias.mkdir(parents=True)
    (alias.parent / ".gitignore").write_text("*\n")
    alias.joinpath("binding.json").write_bytes(canonical_json(binding))
    alias.joinpath("procedure.yaml").write_bytes(
        Path(retained["retention"]["path"]).joinpath("procedure.yaml").read_bytes()
    )
    observation["status"]["session"]["lifecycle"] = "running"
    with pytest.raises(BundleError) as error:
        execution_context(
            tmp_path,
            roots=["definitions", "alternate"],
            entrypoint=entrypoint,
            qualification=qualification,
            client=client,
        )
    assert error.value.code == "ambiguous"
    assert qualification["pending_operations"][0]["ordinal_consumed"] is False


@pytest.mark.parametrize(
    "family,name,entrypoint,node", [CASES[index] for index in [0, 1, 2, 3, 6]]
)
def test_shared_superseded_lineage_recovery_keeps_pending_and_remaining_authority(
    tmp_path, family, name, entrypoint, node
):
    from adaptive_supersede import (
        execute_transition,
        prepare_transition,
        recover_transition,
    )
    from test_adaptive_supersede_unit import native_success

    _source, client, qualification, observation, retained = fixture(
        tmp_path, family, name, entrypoint, node
    )
    observation["status"]["session"].update(lifecycle="running", revision=3)
    observation["mutation_templates"] = [
        {"preconditions": {"workspace_uuid": str(uuid.uuid4())}}
    ]
    request = {
        "roots": ["definitions"],
        "qualification": qualification,
        "client": client,
        "title": "Synthetic cross-family successor",
        "reason": "Required topology is absent in this synthetic snapshot.",
        "missing_topology": "A distinct required work/evidence route is missing.",
        "pending_operations": qualification["pending_operations"],
        "remaining_authority": copy.deepcopy(qualification["assignment"]["authority"]),
        "effects_reconciled": True,
        "idempotency_key": "synthetic-cross-family-key",
    }
    checkpoint = prepare_transition(tmp_path, **request)["checkpoint"]
    consent = {
        "source": "user",
        "decision": "approved",
        "disclosure": copy.deepcopy(checkpoint["disclosure"]),
    }
    transition = (
        (tmp_path, qualification, client, observation, retained),
        request,
        checkpoint,
        consent,
    )
    calls, result, _archive = native_success(transition, unknown=True)
    with pytest.raises(BundleError) as unknown:
        execute_transition(
            tmp_path,
            checkpoint=checkpoint,
            qualification=qualification,
            consent=consent,
            client=client,
        )
    assert unknown.value.code == "outcome-unknown"
    recovered = recover_transition(
        tmp_path,
        checkpoint=checkpoint,
        consent=consent,
        qualification=qualification,
        client=client,
    )
    assert recovered["status"] == "superseded-prepared-resolved"
    assert recovered["session"]["id"] == result["session_id"]
    assert recovered["remaining_authority"] == request["remaining_authority"]
    assert recovered["pending_operations"] == request["pending_operations"]
    assert sum(command == "session.start_replace" for _, command in calls) == 1
