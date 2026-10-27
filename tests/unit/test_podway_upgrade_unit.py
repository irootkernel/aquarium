"""Offline checks of manual VM preparation; no installed or functional claims."""

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

RECIPES = Path(__file__).resolve().parents[1] / "vm/recipes"
sys.path.insert(0, str(RECIPES))
SPEC = importlib.util.spec_from_file_location(
    "manual_podway_upgrade", RECIPES / "podway_upgrade.py"
)
upgrade = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(upgrade)


@pytest.fixture
def environment(tmp_path, monkeypatch):
    binary = tmp_path / "podway"
    binary.write_bytes(b"prior")
    state = {
        "stage": "prior",
        "inventory": [],
        "skills": True,
        "configuration": {
            "config_sha256": "d" * 64,
            "marketplaces": {"fixture": "/released/marketplace"},
            "installed_plugin": {"name": "aquarium", "version": "0.1.21"},
            "settings": {"model": "fixture"},
            "enabled_plugins": {"aquarium": True},
        },
        "rules": [],
    }

    def profile(name):
        candidate = name == "podway-candidate"
        return {
            "components": [
                {
                    "name": "podway",
                    "version": "v0.2.15" if candidate else "v0.2.14",
                    "executable_sha256": "sha256:"
                    + hashlib.sha256(
                        b"candidate" if candidate else b"prior"
                    ).hexdigest(),
                },
                {"name": "use-podway", "skill_tree": {"sha256": "b" * 64}},
            ]
        }

    context = SimpleNamespace(
        root=tmp_path,
        home=tmp_path / "home",
        checkout=tmp_path,
        profile=profile,
        inputs={
            "candidate": {"git_sha": "a" * 40},
            "podway_upgrade": {
                "contract_generation": 2,
                "source_commit": "released-source",
                "contract_manifest_digest": "sha256:" + "c" * 64,
            },
        },
        snapshot=lambda *args, **kwargs: state["inventory"],
    )
    results = tmp_path / "results"
    results.mkdir()

    def native(argv, **kwargs):
        candidate = "--contract-generation" in argv
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                {
                    "schema": "podway.output/v4",
                    "result": {
                        "schema": "podway.version-result/v2",
                        "version": "v0.2.15" if candidate else "v0.2.14",
                        **context.inputs["podway_upgrade"],
                    },
                }
            ),
        )

    run = Mock(side_effect=native)
    monkeypatch.setattr(upgrade.lib, "run", run)
    monkeypatch.setattr(upgrade.lib, "context_value", lambda name: str(binary))
    monkeypatch.setattr(upgrade.lib, "skill_tree_digest", lambda *args: "b" * 64)
    monkeypatch.setattr(upgrade.lib, "verify_guest_identity", dict)
    monkeypatch.setattr(upgrade.lib, "verify_sealed_inputs", lambda root: {})
    monkeypatch.setattr(upgrade.lib, "guard", lambda root: {})
    monkeypatch.setattr(upgrade.lib, "results_directory", lambda suite: results)
    monkeypatch.setattr(upgrade.lib, "finish", Mock(return_value=0))
    skills = lambda stage: {
        "comparisons": {"all_passed": state["skills"]},
        "effective_configuration": state["configuration"],
        "scopes": [{"scope": "codex-rules", "entries": state["rules"]}],
    }
    return context, state, binary, results, run, skills


@pytest.mark.parametrize("stage", ["prior", "candidate"])
def test_manual_observation_uses_the_selected_writers_grammar(environment, stage):
    context, _state, binary, _results, run, _skills = environment
    if stage == "candidate":
        binary.write_bytes(b"candidate")
    upgrade.observe_tools(context, stage)
    assert ("--contract-generation" in run.call_args.args[0]) == (stage == "candidate")


def test_unverified_executable_is_never_run(environment):
    context, _state, binary, _results, run, _skills = environment
    binary.write_bytes(b"unexpected")
    with pytest.raises(upgrade.lib.RecipeError):
        upgrade.observe_tools(context, "prior")
    run.assert_not_called()


def test_manual_phase_captures_are_not_overwritten(environment):
    context, _state, _binary, results, run, skills = environment
    assert upgrade.run(context, "prepare", skills) == 0
    before = (results / "prepared.json").read_bytes()
    with pytest.raises(upgrade.lib.RecipeError):
        upgrade.run(context, "prepare", skills)
    assert (results / "prepared.json").read_bytes() == before
    assert run.call_count == 1


def test_restore_requires_candidate_and_exact_baseline_inventory(environment):
    context, state, binary, results, _run, skills = environment
    upgrade.run(context, "prepare", skills)
    with pytest.raises(upgrade.lib.RecipeError):
        upgrade.run(context, "consumer-cleanup", skills)
    binary.write_bytes(b"candidate")
    upgrade.run(context, "candidate", skills)
    binary.write_bytes(b"prior")
    state["inventory"] = [
        {
            "installation_scope": "user-global",
            "relative_path": "unexpected",
            "sha256": "a" * 64,
            "executable": False,
        }
    ]
    with pytest.raises(upgrade.lib.RecipeError):
        upgrade.run(context, "consumer-cleanup", skills)
    assert not (results / "consumer-cleanup.json").exists()
    state["inventory"] = []
    assert upgrade.run(context, "consumer-cleanup", skills) == 0
    document = json.loads((results / "consumer-cleanup.json").read_text())
    assert document["consumer_cleanup"] == "verified"
    assert "unverified" in document["functional_cases"]
    assert upgrade.lib.finish.call_args.kwargs == {"consumer_cleanup": "verified"}


def test_guest_rejection_precedes_every_phase_write(environment, monkeypatch):
    context, _state, _binary, results, run, skills = environment
    monkeypatch.setattr(
        upgrade.lib,
        "verify_guest_identity",
        Mock(side_effect=upgrade.lib.IdentityError("wrong guest")),
    )
    with pytest.raises(upgrade.lib.IdentityError):
        upgrade.run(context, "prepare", skills)
    assert list(results.iterdir()) == []
    run.assert_not_called()


@pytest.mark.parametrize("drift", ["configuration", "registration", "plugin", "rules"])
def test_restored_files_cannot_hide_consumer_state_drift(environment, drift):
    context, state, binary, results, _run, skills = environment
    upgrade.run(context, "prepare", skills)
    binary.write_bytes(b"candidate")
    upgrade.run(context, "candidate", skills)
    binary.write_bytes(b"prior")
    if drift == "configuration":
        state["configuration"]["settings"]["model"] = "changed"
    elif drift == "registration":
        state["configuration"]["marketplaces"]["fixture"] = "/wrong/source"
    elif drift == "plugin":
        state["configuration"]["installed_plugin"]["enabled"] = False
    else:
        state["rules"] = [
            {"relative_path": ".codex/rules/leftover.md", "sha256": "a" * 64}
        ]
    with pytest.raises(upgrade.lib.RecipeError):
        upgrade.run(context, "consumer-cleanup", skills)
    assert not (results / "consumer-cleanup.json").exists()
    upgrade.lib.finish.assert_not_called()
