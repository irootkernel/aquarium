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


def observation() -> dict[str, object]:
    return {
        "schema_version": "aquarium-release-publication-observation/v1",
        "version": "v0.1.11",
        "qa_candidate_sha": QA,
        "release_commit": {
            "sha": RELEASE,
            "parent_sha": QA,
            "title": "[REL] Release v0.1.11",
        },
        "qa_evidence_candidate_sha": QA,
        "gate_evidence_release_commit_sha": RELEASE,
        "local_main_sha": RELEASE,
        "remote_main_sha": QA,
        "tag": {"state": "absent", "annotated": False, "peeled_sha": None},
        "hosted_release": {"state": "absent", "tag": None, "target_sha": None},
    }


@pytest.mark.parametrize(
    ("configure", "classification", "next_action"),
    [
        (lambda value: None, "partial", "push_main"),
        (
            lambda value: value.update(remote_main_sha=RELEASE),
            "partial",
            "create_and_push_tag",
        ),
        (
            lambda value: (
                value.update(remote_main_sha=RELEASE),
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
                value.update(remote_main_sha=RELEASE),
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


@pytest.mark.parametrize(
    "configure",
    [
        lambda value: value.update(local_main_sha=OTHER),
        lambda value: value.update(remote_main_sha=OTHER),
        lambda value: value.update(
            tag={"state": "present", "annotated": False, "peeled_sha": RELEASE}
        ),
        lambda value: value.update(
            hosted_release={
                "state": "present",
                "tag": "v0.1.11",
                "target_sha": OTHER,
            }
        ),
        lambda value: value.update(
            hosted_release={
                "state": "present",
                "tag": "v0.1.11",
                "target_sha": RELEASE,
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
