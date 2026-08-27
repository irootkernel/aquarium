from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).parents[2]
    / "plugins/aquarium/skills/release-handler/scripts/inspect_publication_state.py"
)
SPEC = importlib.util.spec_from_file_location("inspect_publication_state", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
inspect_publication_state = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inspect_publication_state)

QA = "1" * 40
RELEASE = "2" * 40
OTHER = "3" * 40
BASE = "4" * 40


def observation() -> dict[str, object]:
    return {
        "schema_version": "aquarium-release-publication-observation/v4",
        "version": "v0.1.11",
        "release_basis_candidate_sha": QA,
        "release_commit": {
            "sha": RELEASE,
            "parent_sha": QA,
            "title": "[REL] Release v0.1.11",
        },
        "qa_evidence_candidate_sha": QA,
        "qa_evidence_relation_to_release_basis": "equal",
        "qa_binding": "exact",
        "qa_reuse_attempt": 0,
        "gate_evidence_release_commit_sha": RELEASE,
        "local_main_sha": RELEASE,
        "remote_main_sha": QA,
        "remote_main_relation_to_release_basis": "equal",
        "tag": {"state": "absent", "annotated": False, "peeled_sha": None},
        "hosted_release": {
            "state": "absent",
            "tag": None,
            "target_sha": None,
            "draft": False,
            "prerelease": False,
        },
    }


@pytest.mark.parametrize(
    ("configure", "classification", "next_action"),
    [
        (lambda value: None, "partial", "push_main"),
        (
            lambda value: value.update(
                remote_main_sha=RELEASE,
                remote_main_relation_to_release_basis="descendant",
            ),
            "partial",
            "create_and_push_tag",
        ),
        (
            lambda value: (
                value.update(
                    remote_main_sha=RELEASE,
                    remote_main_relation_to_release_basis="descendant",
                ),
                value.update(
                    tag={
                        "state": "present",
                        "annotated": True,
                        "peeled_sha": RELEASE,
                    }
                ),
            ),
            "partial",
            "create_hosted_release",
        ),
        (
            lambda value: (
                value.update(
                    remote_main_sha=RELEASE,
                    remote_main_relation_to_release_basis="descendant",
                ),
                value.update(
                    tag={
                        "state": "present",
                        "annotated": True,
                        "peeled_sha": RELEASE,
                    },
                    hosted_release={
                        "state": "present",
                        "tag": "v0.1.11",
                        "target_sha": RELEASE,
                        "draft": False,
                        "prerelease": False,
                    },
                ),
            ),
            "complete",
            "verify_complete",
        ),
    ],
)
def test_publication_resume_returns_one_ordered_action(
    configure: object, classification: str, next_action: str
) -> None:
    value = observation()
    configure(value)

    result = inspect_publication_state.inspect(value)

    assert result["classification"] == classification
    assert result["next_action"] == next_action


def test_publication_allows_remote_ancestor_of_release_basis() -> None:
    value = observation()
    value.update(
        remote_main_sha=BASE,
        remote_main_relation_to_release_basis="ancestor",
    )

    result = inspect_publication_state.inspect(value)

    assert result["classification"] == "partial"
    assert result["next_action"] == "push_main"
    assert result["statuses"]["remote_main"] == "missing"
    assert result["remote_main_sha"] == BASE
    assert result["remote_main_relation_to_release_basis"] == "ancestor"


def test_publication_accepts_one_approved_qa_neutral_descendant() -> None:
    value = observation()
    value.update(
        release_basis_candidate_sha=OTHER,
        qa_evidence_relation_to_release_basis="direct_parent",
        qa_binding="approved_qa_neutral_descendant",
        qa_reuse_attempt=1,
        remote_main_sha=OTHER,
        remote_main_relation_to_release_basis="equal",
    )
    value["release_commit"]["parent_sha"] = OTHER

    result = inspect_publication_state.inspect(value)

    assert result["classification"] == "partial"
    assert result["next_action"] == "push_main"
    assert result["statuses"]["evidence"] == "matching"
    assert result["release_basis_candidate_sha"] == OTHER
    assert result["qa_evidence_candidate_sha"] == QA
    assert result["qa_evidence_relation_to_release_basis"] == "direct_parent"
    assert result["qa_binding"] == "approved_qa_neutral_descendant"
    assert result["qa_reuse_attempt"] == 1


def test_publication_rejects_circular_qa_evidence_binding() -> None:
    value = observation()
    value.update(
        release_basis_candidate_sha=OTHER,
        qa_evidence_candidate_sha=RELEASE,
        qa_evidence_relation_to_release_basis="direct_parent",
        qa_binding="approved_qa_neutral_descendant",
        qa_reuse_attempt=1,
        remote_main_sha=OTHER,
        remote_main_relation_to_release_basis="equal",
    )
    value["release_commit"]["parent_sha"] = OTHER

    result = inspect_publication_state.inspect(value)

    assert result["classification"] == "unproven"
    assert result["next_action"] == "stop"
    assert result["statuses"]["evidence"] == "unproven"


def test_publication_rejects_self_parent_release_commit() -> None:
    value = observation()
    value.update(
        release_basis_candidate_sha=RELEASE,
        qa_evidence_candidate_sha=RELEASE,
        remote_main_sha=QA,
        remote_main_relation_to_release_basis="ancestor",
    )
    value["release_commit"]["parent_sha"] = RELEASE

    result = inspect_publication_state.inspect(value)

    assert result["classification"] == "unproven"
    assert result["next_action"] == "stop"
    assert result["statuses"]["evidence"] == "unproven"


@pytest.mark.parametrize(
    "configure",
    [
        lambda value: value.update(local_main_sha=OTHER),
        lambda value: value.update(
            remote_main_sha=OTHER,
            remote_main_relation_to_release_basis="descendant",
        ),
        lambda value: value.update(
            remote_main_sha=OTHER,
            remote_main_relation_to_release_basis="diverged",
        ),
        lambda value: value.update(
            tag={"state": "present", "annotated": False, "peeled_sha": RELEASE}
        ),
        lambda value: value.update(
            hosted_release={
                "state": "present",
                "tag": "v0.1.11",
                "target_sha": OTHER,
                "draft": False,
                "prerelease": False,
            }
        ),
        lambda value: value.update(
            hosted_release={
                "state": "present",
                "tag": "v0.1.11",
                "target_sha": RELEASE,
                "draft": False,
                "prerelease": False,
            }
        ),
    ],
)
def test_publication_conflicts_stop(configure: object) -> None:
    value = observation()
    configure(value)

    result = inspect_publication_state.inspect(value)

    assert result["classification"] == "conflict"
    assert result["next_action"] == "stop"


@pytest.mark.parametrize(
    ("remote_sha", "relation"),
    [
        (QA, "ancestor"),
        (OTHER, "equal"),
        (RELEASE, "ancestor"),
        (OTHER, "unknown"),
    ],
)
def test_remote_relationship_must_match_observed_sha(
    remote_sha: str, relation: str
) -> None:
    value = observation()
    value.update(
        remote_main_sha=remote_sha,
        remote_main_relation_to_release_basis=relation,
    )

    with pytest.raises(inspect_publication_state.ObservationError) as error:
        inspect_publication_state.inspect(value)

    assert error.value.code == "observation_invalid"


def test_remote_relationship_rejects_non_string_value() -> None:
    value = observation()
    value["remote_main_relation_to_release_basis"] = []

    with pytest.raises(inspect_publication_state.ObservationError) as error:
        inspect_publication_state.inspect(value)

    assert error.value.code == "observation_invalid"


def test_v3_observation_is_rejected() -> None:
    value = observation()
    value["schema_version"] = "aquarium-release-publication-observation/v3"

    with pytest.raises(inspect_publication_state.ObservationError) as error:
        inspect_publication_state.inspect(value)

    assert error.value.code == "schema_unsupported"


@pytest.mark.parametrize(
    "configure",
    [
        lambda value: value.update(
            qa_binding="approved_qa_neutral_descendant",
            qa_evidence_relation_to_release_basis="direct_parent",
            qa_reuse_attempt=1,
        ),
        lambda value: value.update(
            release_basis_candidate_sha=OTHER,
            qa_binding="approved_qa_neutral_descendant",
            qa_evidence_relation_to_release_basis="equal",
            qa_reuse_attempt=1,
        ),
        lambda value: value.update(
            release_basis_candidate_sha=OTHER,
            qa_binding="approved_qa_neutral_descendant",
            qa_evidence_relation_to_release_basis="direct_parent",
            qa_reuse_attempt=0,
        ),
        lambda value: value.update(
            qa_binding="exact",
            qa_evidence_relation_to_release_basis="direct_parent",
            qa_reuse_attempt=0,
        ),
        lambda value: value.update(qa_evidence_candidate_sha=OTHER),
        lambda value: value.update(qa_reuse_attempt=1),
        lambda value: value.update(
            release_basis_candidate_sha=OTHER,
            qa_evidence_candidate_sha=None,
            qa_binding="approved_qa_neutral_descendant",
            qa_evidence_relation_to_release_basis="direct_parent",
            qa_reuse_attempt=1,
        ),
    ],
)
def test_invalid_qa_bindings_do_not_prove_release(configure: object) -> None:
    value = observation()
    configure(value)
    if value["release_basis_candidate_sha"] == OTHER:
        value["release_commit"]["parent_sha"] = OTHER
        value.update(
            remote_main_sha=OTHER,
            remote_main_relation_to_release_basis="equal",
        )

    result = inspect_publication_state.inspect(value)

    assert result["classification"] == "unproven"
    assert result["next_action"] == "stop"


@pytest.mark.parametrize(
    ("field", "invalid"),
    [
        ("qa_binding", "unknown"),
        ("qa_binding", []),
        ("qa_evidence_relation_to_release_basis", "ancestor"),
        ("qa_evidence_relation_to_release_basis", []),
        ("qa_reuse_attempt", -1),
        ("qa_reuse_attempt", 2),
        ("qa_reuse_attempt", True),
        ("qa_reuse_attempt", "1"),
    ],
)
def test_invalid_qa_binding_fields_are_rejected(field: str, invalid: object) -> None:
    value = observation()
    value[field] = invalid

    with pytest.raises(inspect_publication_state.ObservationError) as error:
        inspect_publication_state.inspect(value)

    assert error.value.code == "observation_invalid"


@pytest.mark.parametrize(
    "configure",
    [
        lambda value: value.update(qa_evidence_candidate_sha=None),
        lambda value: value.update(gate_evidence_release_commit_sha=None),
        lambda value: value["release_commit"].update(title="[REL] Release v0.1.12"),
        lambda value: value["release_commit"].update(parent_sha=OTHER),
    ],
)
def test_unproven_release_evidence_stops(configure: object) -> None:
    value = observation()
    configure(value)

    result = inspect_publication_state.inspect(value)

    assert result["classification"] == "unproven"
    assert result["next_action"] == "stop"


def test_unproven_release_evidence_classifies_divergent_remote_release() -> None:
    value = observation()
    value["release_commit"]["parent_sha"] = OTHER
    value.update(
        remote_main_sha=RELEASE,
        remote_main_relation_to_release_basis="diverged",
    )

    result = inspect_publication_state.inspect(value)

    assert result["classification"] == "unproven"
    assert result["next_action"] == "stop"
    assert result["statuses"]["remote_main"] == "conflict"


@pytest.mark.parametrize(
    "configure",
    [
        lambda value: value.update(
            tag={"state": "absent", "annotated": True, "peeled_sha": RELEASE}
        ),
        lambda value: value.update(
            hosted_release={
                "state": "absent",
                "tag": "v0.1.11",
                "target_sha": RELEASE,
                "draft": False,
                "prerelease": False,
            }
        ),
    ],
)
def test_absent_objects_reject_contradictory_data(configure: object) -> None:
    value = observation()
    configure(value)

    with pytest.raises(inspect_publication_state.ObservationError) as error:
        inspect_publication_state.inspect(value)

    assert error.value.code == "observation_invalid"


@pytest.mark.parametrize("field", ["draft", "prerelease"])
def test_non_public_hosted_release_conflicts(field: str) -> None:
    value = observation()
    value.update(
        remote_main_sha=RELEASE,
        remote_main_relation_to_release_basis="descendant",
        tag={"state": "present", "annotated": True, "peeled_sha": RELEASE},
        hosted_release={
            "state": "present",
            "tag": "v0.1.11",
            "target_sha": RELEASE,
            "draft": False,
            "prerelease": False,
        },
    )
    value["hosted_release"][field] = True

    result = inspect_publication_state.inspect(value)

    assert result["classification"] == "conflict"
    assert result["next_action"] == "stop"
    assert result["statuses"]["hosted_release"] == "conflict"
