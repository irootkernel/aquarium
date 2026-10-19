"""Atomic transition orchestration with synthetic consent/native results, not actual approval."""

import copy
import sys
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "plugins/aquarium/shared"))
import test_adaptive_diagnosis_unit as diagnostic_tests
from adaptive_bundles import BundleError
from adaptive_supersede import (
    execute_transition,
    prepare_transition,
    recover_transition,
)

diagnosis = diagnostic_tests.diagnosis


@pytest.fixture
def transition(diagnosis):
    repo, qualification, client, obs, _retained = diagnosis
    workspace = str(uuid.uuid4())
    obs["mutation_templates"] = [{"preconditions": {"workspace_uuid": workspace}}]
    request = {
        "roots": ["definitions"],
        "qualification": qualification,
        "client": client,
        "title": "Synthetic retained diagnostic successor",
        "reason": "Synthetic explicit replacement consent: required topology is absent.",
        "missing_topology": "Required alternate investigation route is absent from the current snapshot.",
        "pending_operations": [
            {"operation": "prior-QA", "state": "delivered", "findings": ["Q1"]}
        ],
        "remaining_authority": copy.deepcopy(qualification["assignment"]["authority"]),
        "effects_reconciled": True,
        "idempotency_key": "synthetic-supersede-one",
    }
    checkpoint = prepare_transition(repo, **request)["checkpoint"]
    consent = {
        "source": "user",
        "decision": "approved",
        "disclosure": copy.deepcopy(checkpoint["disclosure"]),
    }
    return diagnosis, request, checkpoint, consent


def native_success(transition, *, unknown=False):
    fixture, _, checkpoint, _ = transition
    _, _, client, obs, _ = fixture
    old = copy.deepcopy(obs["status"])
    successor = str(uuid.uuid4())
    result = {
        "schema": "podway.session-start-result/v4",
        "session_state": "prepared",
        "revision": 0,
        "active_attempt": None,
        "goal_defined": False,
        "procedure_digest": old["procedure"]["digest"],
        "session_id": successor,
        "existing_session": {
            "action": "supersede_archive",
            "lifecycle": "running",
            "session_id": old["session"]["id"],
            "session_revision": old["session"]["revision"],
        },
    }
    archive = {
        "schema": "podway.session-archive-show-result/v3",
        "activity": "inactive",
        "state": {
            "procedure": old["procedure"],
            "session": {
                "id": old["session"]["id"],
                "lifecycle": "cancelled",
                "revision": old["session"]["revision"] + 1,
            },
        },
        "terminal_disposition": {
            "kind": "superseded",
            "successor_session_id": successor,
            "reason": checkpoint["disclosure"]["reason"],
        },
    }
    calls = []

    def read(argv, command, schemas):
        calls.append((list(argv), command))
        if command == "session.start_replace":
            obs["status"].update(
                session={"id": successor, "lifecycle": "prepared", "revision": 0},
                current=None,
                goal_defined=False,
            )
            obs["guidance"] = None
            if unknown:
                raise BundleError("MUTATION_OUTCOME_UNKNOWN", "Synthetic lost response")
            return copy.deepcopy(result)
        if command == "session.archive_show":
            return copy.deepcopy(archive)
        if command == "outcome.lookup":
            return {
                "schema": "podway.outcome-lookup-result/v1",
                "idempotency_key": checkpoint["idempotency_key"],
                "found": True,
                "outcome": {
                    "response": {
                        "schema": "podway.output/v4",
                        "command": "session.start_replace",
                        "workspace": {
                            "uuid": checkpoint["disclosure"]["predecessor"][
                                "workspace_uuid"
                            ]
                        },
                        "result": copy.deepcopy(result),
                    }
                },
            }
        raise AssertionError(command)

    client.read = read
    return calls, result, archive


def test_plan_is_read_only_and_preserves_authority_disclosure(transition):
    fixture, request, checkpoint, _ = transition
    assert (
        checkpoint["disclosure"]["remaining_authority"]
        == request["remaining_authority"]
    )
    assert (
        checkpoint["disclosure"]["pending_operations"] == request["pending_operations"]
    )
    assert (
        checkpoint["disclosure"]["predecessor"]["session"]
        == fixture[3]["status"]["session"]
    )
    argv = checkpoint["request"]
    assert (
        argv[0] == "start"
        and argv[1].startswith("--procedure=")
        and argv[argv.index("--on-existing") + 1] == "preserve"
    )
    assert not any(x in argv for x in ["cancel", "reset", "--delete", "begin"])
    source = argv[1].split("=", 1)[1]
    assert not Path(source).is_absolute()
    assert not source.startswith("./")
    assert (fixture[0] / source).is_file()
    assert all(call.args[1] == "version" for call in fixture[2].read.call_args_list)


@pytest.mark.parametrize("change", ["absent", "wrong-source", "changed-disclosure"])
def test_exact_user_consent_before_mutation(transition, change):
    fixture, _, checkpoint, consent = transition
    calls, _, _ = native_success(transition)
    if change == "absent":
        consent = None
    elif change == "wrong-source":
        consent["source"] = "evaluator"
    else:
        consent["disclosure"]["missing_topology"] = "different"
    with pytest.raises(BundleError) as error:
        execute_transition(
            fixture[0],
            checkpoint=checkpoint,
            consent=consent,
            qualification=fixture[1],
            client=fixture[2],
        )
    assert error.value.code == "replacement-consent-required"
    assert calls == []


def test_stale_observation_stops_without_replacing(transition):
    fixture, _, checkpoint, consent = transition
    calls, _, _ = native_success(transition)
    fixture[3]["status"]["session"]["revision"] += 1
    with pytest.raises(BundleError) as error:
        execute_transition(
            fixture[0],
            checkpoint=checkpoint,
            consent=consent,
            qualification=fixture[1],
            client=fixture[2],
        )
    assert error.value.code == "stale-consent" and calls == []


def test_atomic_positive_preserves_records_and_stops_before_begin(transition):
    fixture, request, checkpoint, consent = transition
    calls, _, _ = native_success(transition)
    result = execute_transition(
        fixture[0],
        checkpoint=checkpoint,
        consent=consent,
        qualification=fixture[1],
        client=fixture[2],
    )
    assert result["status"] == "superseded-prepared-resolved"
    assert result["session"]["lifecycle"] == "prepared"
    assert result["remaining_authority"] == request["remaining_authority"]
    assert result["pending_operations"] == request["pending_operations"]
    assert [command for _, command in calls] == [
        "session.start_replace",
        "session.archive_show",
    ]
    assert calls[0][0] == checkpoint["request"] and result["dispatch"] is None


def test_unknown_effect_looks_up_same_operation_and_never_starts_again(transition):
    fixture, _, checkpoint, consent = transition
    calls, _, _ = native_success(transition, unknown=True)
    with pytest.raises(BundleError) as error:
        execute_transition(
            fixture[0],
            checkpoint=checkpoint,
            consent=consent,
            qualification=fixture[1],
            client=fixture[2],
        )
    assert error.value.code == "outcome-unknown"
    result = recover_transition(
        fixture[0],
        checkpoint=checkpoint,
        consent=consent,
        qualification=fixture[1],
        client=fixture[2],
    )
    assert result["status"] == "superseded-prepared-resolved"
    assert [command for _, command in calls].count("session.start_replace") == 1
    assert calls[1][0] == [
        "outcome",
        "lookup",
        "--idempotency-key",
        checkpoint["idempotency_key"],
    ]


@pytest.mark.parametrize("damage", ["lineage", "disposition", "procedure", "current"])
def test_lineage_or_current_state_mismatch_never_claims_ready(transition, damage):
    fixture, _, checkpoint, consent = transition
    _calls, result, archive = native_success(transition)
    if damage == "lineage":
        archive["terminal_disposition"]["successor_session_id"] = str(uuid.uuid4())
    elif damage == "disposition":
        archive["terminal_disposition"]["kind"] = "accepted"
    elif damage == "procedure":
        archive["state"]["procedure"] = {
            **archive["state"]["procedure"],
            "digest": "sha256:" + "f" * 64,
        }
    else:
        result["revision"] = 1
    with pytest.raises(BundleError) as error:
        execute_transition(
            fixture[0],
            checkpoint=checkpoint,
            consent=consent,
            qualification=fixture[1],
            client=fixture[2],
        )
    assert error.value.code == "not-established"


@pytest.mark.parametrize("changed", [False, True])
def test_lookup_miss_requires_same_request_and_unchanged_predecessor(
    transition, changed
):
    fixture, _, checkpoint, consent = transition
    calls = []
    fixture[2].read = lambda argv, command, schemas: (
        calls.append(command)
        or {"found": False, "idempotency_key": checkpoint["idempotency_key"]}
    )
    if changed:
        fixture[3]["status"]["session"]["id"] = str(uuid.uuid4())
    if changed:
        with pytest.raises(BundleError) as error:
            recover_transition(
                fixture[0],
                checkpoint=checkpoint,
                consent=consent,
                qualification=fixture[1],
                client=fixture[2],
            )
        assert error.value.code == "outcome-unknown"
    else:
        assert (
            recover_transition(
                fixture[0],
                checkpoint=checkpoint,
                consent=consent,
                qualification=fixture[1],
                client=fixture[2],
            )["status"]
            == "same-request-replay-available"
        )
    assert calls == ["outcome.lookup"]


def test_unresolved_effects_preserve_running_session(transition):
    fixture, request, _, _ = transition
    request["effects_reconciled"] = False
    with pytest.raises(BundleError) as error:
        prepare_transition(fixture[0], **request)
    assert error.value.code == "not-established"
    assert fixture[3]["status"]["session"]["lifecycle"] == "running"


@pytest.mark.parametrize("action", ["transition-plan", "transition"])
def test_public_cli_forwards_exact_plan_or_stops_without_consent(
    transition, monkeypatch, capsys, action
):
    import json

    import adaptive_admission
    import manage_adaptive_procedure

    fixture, request, checkpoint, _ = transition
    repo, qualification, client, _, _ = fixture
    qualification_path = repo / "qualification.json"
    qualification_path.write_text(json.dumps(qualification))
    input_path = repo / "transition.json"
    input_path.write_text(
        json.dumps(
            {
                key: value
                for key, value in request.items()
                if key not in {"roots", "qualification", "client"}
            }
            if action == "transition-plan"
            else checkpoint
        )
    )
    monkeypatch.setattr(
        adaptive_admission, "NativeClient", lambda *args, **kwargs: client
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "manage_adaptive_procedure.py",
            action,
            "--repository",
            str(repo),
            "--root",
            "definitions",
            "--entrypoint",
            "war-room",
            "--qualification",
            str(qualification_path),
            "--transition-input",
            str(input_path),
            "--podway",
            "synthetic-explicit-path",
        ],
    )
    status = manage_adaptive_procedure.main()
    output = json.loads(capsys.readouterr().out)
    assert status == (0 if action == "transition-plan" else 2)
    assert output["status"] == "replacement-consent-required"
    if action == "transition-plan":
        assert output["checkpoint"]["request"] == checkpoint["request"]
    assert all(call.args[1] == "version" for call in client.read.call_args_list)


def test_intact_original_alias_is_retained_when_another_alias_sorts_first(transition):
    import shutil

    fixture, _, checkpoint, consent = transition
    shutil.copytree(fixture[0] / "definitions", fixture[0] / "a-definitions")
    checkpoint["roots"].append("a-definitions")
    native_success(transition)
    result = execute_transition(
        fixture[0],
        checkpoint=checkpoint,
        consent=consent,
        qualification=fixture[1],
        client=fixture[2],
    )
    assert result["status"] == "superseded-prepared-resolved"
    assert result["bundle_id"] == checkpoint["disclosure"]["successor"]["bundle_id"]


def test_joined_native_source_operand_preserves_dash_and_unicode_roots(tmp_path):
    from adaptive_supersede import request_for

    checkpoint = {
        "repository": str(tmp_path),
        "source_path": str(tmp_path / "-native root 한글" / "procedure.yaml"),
        "idempotency_key": "synthetic-key",
        "disclosure": {
            "title": "Synthetic title",
            "reason": "Synthetic consented reason",
            "successor": {"procedure": {"digest": "sha256:" + "a" * 64}},
            "predecessor": {
                "workspace_uuid": "synthetic-workspace",
                "session": {"id": "synthetic-session", "revision": 3},
            },
        },
    }
    argv = request_for(checkpoint)
    assert argv[1] == "--procedure=-native root 한글/procedure.yaml"
    assert (
        "--on-existing" in argv and argv[argv.index("--on-existing") + 1] == "preserve"
    )


def test_explicit_replay_after_lookup_miss_uses_identical_retained_request(transition):
    fixture, _, checkpoint, consent = transition
    calls, _, _ = native_success(transition)
    original = fixture[2].read

    def read(argv, command, schemas):
        if command == "outcome.lookup":
            calls.append((list(argv), command))
            return {"found": False, "idempotency_key": checkpoint["idempotency_key"]}
        return original(argv, command, schemas)

    fixture[2].read = read
    result = recover_transition(
        fixture[0],
        checkpoint=checkpoint,
        consent=consent,
        qualification=fixture[1],
        client=fixture[2],
        replay=True,
    )
    assert result["status"] == "superseded-prepared-resolved"
    assert calls[0][1] == "outcome.lookup"
    assert calls[1] == (checkpoint["request"], "session.start_replace")


@pytest.mark.parametrize(
    "extra",
    [
        {"pending_operations": [{"operation": "original-QA", "state": "delivered"}]},
        {
            "retain": True,
            "in_session": True,
            "source_path": "/unapproved/source.yaml",
            "binding_path": "/unapproved/binding.json",
        },
    ],
)
def test_ordinary_context_metadata_does_not_override_successor_qualification(
    transition, monkeypatch, extra
):
    import adaptive_supersede

    fixture, request, _, _ = transition
    qualification = fixture[1]
    qualification.update(copy.deepcopy(extra))
    original = copy.deepcopy(qualification)
    before = {
        str(path.relative_to(fixture[0])): path.read_bytes()
        for path in fixture[0].rglob("*")
        if path.is_file() and ".git" not in path.relative_to(fixture[0]).parts
    }
    actual = adaptive_supersede.qualify_prepared
    calls = []

    def qualify(repository, assignment, **kwargs):
        calls.append((assignment, kwargs))
        return actual(repository, assignment, **kwargs)

    monkeypatch.setattr(adaptive_supersede, "qualify_prepared", qualify)
    result = prepare_transition(fixture[0], **request)
    assert result["status"] == "replacement-consent-required"
    assert qualification == original
    assert calls[0][0] == qualification["assignment"]
    assert set(calls[0][1]) == {"client", "assessment", "combined_task_plan"}
    assert before == {
        str(path.relative_to(fixture[0])): path.read_bytes()
        for path in fixture[0].rglob("*")
        if path.is_file() and ".git" not in path.relative_to(fixture[0]).parts
    }


@pytest.mark.parametrize(
    "case",
    [
        "malformed-json",
        "missing-plan-key",
        "conflicting-root",
        "missing-checkpoint-key",
        "bookkeeping",
    ],
)
def test_public_transition_input_classification_before_effects(
    transition, monkeypatch, capsys, case
):
    import json

    import adaptive_admission
    import manage_adaptive_procedure

    fixture, request, checkpoint, consent = transition
    repository, qualification, client, _, _ = fixture
    qualification_path = repository / "qualification.json"
    qualification_path.write_text(json.dumps(qualification))
    input_path = repository / "transition-input.json"
    consent_path = repository / "consent.json"
    consent_path.write_text(json.dumps(consent))
    plan = {
        key: value
        for key, value in request.items()
        if key not in {"roots", "qualification", "client"}
    }
    action = "transition-plan"
    if case == "malformed-json":
        input_path.write_text("{invalid")
    else:
        if case == "missing-plan-key":
            plan.pop("idempotency_key")
        elif case == "conflicting-root":
            plan["roots"] = ["other"]
        elif case == "bookkeeping":
            plan["operator_note"] = {"settled": True}
        else:
            action = "transition"
            plan = copy.deepcopy(checkpoint)
            plan["disclosure"]["predecessor"].pop("workspace_uuid")
        input_path.write_text(json.dumps(plan))
    monkeypatch.setattr(
        adaptive_admission, "NativeClient", lambda *args, **kwargs: client
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "manage_adaptive_procedure.py",
            action,
            "--repository",
            str(repository),
            "--root",
            "definitions",
            "--entrypoint",
            "war-room",
            "--qualification",
            str(qualification_path),
            "--transition-input",
            str(input_path),
            "--consent",
            str(consent_path),
            "--podway",
            "synthetic-explicit-path",
        ],
    )
    exit_code = manage_adaptive_procedure.main()
    output = json.loads(capsys.readouterr().out)
    assert exit_code == (0 if case == "bookkeeping" else 2)
    assert output["status"] == (
        "replacement-consent-required" if case == "bookkeeping" else "invalid-input"
    )
    assert all(call.args[1] == "version" for call in client.read.call_args_list)


@pytest.mark.parametrize("phase", ["prepare", "execute"])
@pytest.mark.parametrize("full_domain", [False, True])
def test_supersede_resolves_full_disclosed_domain_before_native_effect(
    transition, phase, full_domain
):
    from adaptive_definitions import canonical_json, definition_id

    fixture, request, checkpoint, consent = transition
    repository, qualification, client, _, retained = fixture
    other_root = "-other flows 한글"
    qualification["assignment"]["authority"]["preparation"]["roots"].append(other_root)
    changed = copy.deepcopy(retained["binding"])
    changed["parameters"]["alternative"] = {
        "type": "text",
        "required": False,
        "description": "Conflicting native-key mapping",
    }
    other = repository / other_root / ".local" / definition_id(changed)
    other.mkdir(parents=True)
    (other.parent / ".gitignore").write_text("*\n")
    (other / "procedure.yaml").write_bytes(retained["retention"]["source"])
    (other / "binding.json").write_bytes(canonical_json(changed))
    roots = ["definitions", other_root] if full_domain else ["definitions"]
    request["roots"] = roots
    checkpoint["roots"] = roots
    calls, _, _ = native_success(transition)
    before = {
        path: path.read_bytes() for path in repository.rglob("*") if path.is_file()
    }
    with pytest.raises(BundleError) as error:
        if phase == "prepare":
            prepare_transition(repository, **request)
        else:
            execute_transition(
                repository,
                checkpoint=checkpoint,
                consent=consent,
                qualification=qualification,
                client=client,
            )
    assert error.value.code == ("ambiguous" if full_domain else "not-established")
    assert calls == []
    assert {
        path: path.read_bytes() for path in repository.rglob("*") if path.is_file()
    } == before


def test_supersede_accepts_identical_aliases_in_full_disclosed_custom_domain(
    transition,
):
    fixture, request, _, _ = transition
    repository, qualification, _, _, retained = fixture
    custom = "-other flows 한글"
    roots = ["definitions", custom]
    qualification["assignment"]["authority"]["preparation"]["roots"] = roots
    source = Path(retained["retention"]["path"])
    alias = repository / custom / ".local" / source.name
    alias.mkdir(parents=True)
    (alias.parent / ".gitignore").write_text("*\n")
    for name in ("procedure.yaml", "binding.json"):
        (alias / name).write_bytes((source / name).read_bytes())
    request["roots"] = roots
    result = prepare_transition(repository, **request)
    assert result["checkpoint"]["roots"] == roots
    assert (
        result["checkpoint"]["disclosure"]["successor"]["bundle_id"]
        == retained["retention"]["bundle_id"]
    )
