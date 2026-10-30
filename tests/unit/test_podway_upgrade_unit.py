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
finish = upgrade.lib.finish


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
        marketplace="fixture",
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


@pytest.mark.parametrize("change", ["added", "removed", "modified"])
def test_native_cache_refresh_is_observed_outside_aquarium_restoration(
    environment, change
):
    context, state, binary, results, _run, skills = environment
    entry = {
        "installation_scope": "codex-plugin-cache",
        "relative_path": ".codex/plugins/cache/other-market/plugin/1/SKILL.md",
        "sha256": "a" * 64,
        "executable": False,
    }
    state["inventory"] = [] if change == "added" else [entry]
    upgrade.run(context, "prepare", skills)
    binary.write_bytes(b"candidate")
    upgrade.run(context, "candidate", skills)
    binary.write_bytes(b"prior")
    state["inventory"] = [] if change == "removed" else [{**entry, "sha256": "b" * 64}]
    assert upgrade.run(context, "consumer-cleanup", skills) == 0
    document = json.loads((results / "consumer-cleanup.json").read_text())
    assert document["consumer_cleanup"] == "verified"
    assert len(document["codex_owned_cache_observations"]) == 1


@pytest.mark.parametrize(
    ("scope", "path"),
    [
        ("codex-plugin-cache", ".codex/plugins/cache/fixture/aquarium/1/SKILL.md"),
        ("shared-agents-skills", ".agents/skills/use-podway/SKILL.md"),
        ("user-global", ".codex/plugins/cache/other-market/plugin/1/SKILL.md"),
    ],
)
def test_cache_observation_cannot_hide_owned_or_other_scope_drift(
    environment, scope, path
):
    context, state, binary, results, _run, skills = environment
    upgrade.run(context, "prepare", skills)
    binary.write_bytes(b"candidate")
    upgrade.run(context, "candidate", skills)
    binary.write_bytes(b"prior")
    state["inventory"] = [
        {
            "installation_scope": scope,
            "relative_path": path,
            "sha256": "a" * 64,
            "executable": False,
        }
    ]
    with pytest.raises(upgrade.lib.RecipeError):
        upgrade.run(context, "consumer-cleanup", skills)
    assert not (results / "consumer-cleanup.json").exists()


def test_failed_cache_observation_survives_repair_and_native_finish(
    environment, monkeypatch
):
    context, state, binary, results, _run, skills = environment
    monkeypatch.setattr(upgrade.lib, "finish", finish)
    monkeypatch.setattr(upgrade.lib, "load_inputs", lambda: context.inputs)
    upgrade.run(context, "prepare", skills)
    binary.write_bytes(b"candidate")
    upgrade.run(context, "candidate", skills)
    binary.write_bytes(b"prior")
    state["inventory"] = [
        {
            "installation_scope": "codex-plugin-cache",
            "relative_path": ".codex/plugins/cache/other-market/plugin/1/SKILL.md",
            "sha256": "a" * 64,
            "executable": False,
        }
    ]
    state["configuration"]["settings"]["model"] = "changed"
    with pytest.raises(upgrade.lib.RecipeError):
        upgrade.run(context, "consumer-cleanup", skills)
    failed = json.loads((results / "inventories.json").read_text())[
        "failed_cleanup_observations"
    ]
    assert len(failed) == 1
    assert failed[0]["inventory"] == state["inventory"]
    assert failed[0]["codex_owned_cache_observations"]
    assert failed[0]["violations"]
    state["configuration"]["settings"]["model"] = "fixture"
    state["inventory"] = []
    assert upgrade.run(context, "consumer-cleanup", skills) == 0
    assert (
        json.loads((results / "inventories.json").read_text())[
            "failed_cleanup_observations"
        ]
        == failed
    )
    assert json.loads((results / "result.json").read_text())["outcome"] == "pass"


@pytest.mark.parametrize(
    "original",
    [
        b"not JSON\n",
        b'{"failed_cleanup_observations": false}\n',
        (
            b'{"schema":"aquarium.vm-suite-inventories/v1",'
            b'"inventories":{},"failed_cleanup_observations":false}\n'
        ),
    ],
)
@pytest.mark.parametrize("restoration", ["restored", "wrong-cli", "wrong-skills"])
def test_native_driver_preserves_invalid_cleanup_history(
    environment, monkeypatch, original, restoration
):
    import guest_main

    context, state, binary, results, run, skills = environment
    upgrade.run(context, "prepare", skills)
    binary.write_bytes(b"candidate")
    upgrade.run(context, "candidate", skills)
    binary.write_bytes(b"candidate" if restoration == "wrong-cli" else b"prior")
    state["skills"] = restoration != "wrong-skills"
    path = results / "inventories.json"
    path.write_bytes(original)
    monkeypatch.setattr(upgrade.lib, "finish", finish)
    monkeypatch.setattr(upgrade.lib, "load_inputs", lambda: context.inputs)
    monkeypatch.setattr(guest_main, "Context", lambda: context)
    monkeypatch.setattr(
        guest_main,
        "skill_identity_document",
        lambda _context, stage, **_: skills(stage),
    )
    monkeypatch.setitem(sys.modules, "podway_upgrade", upgrade)
    monkeypatch.setenv("HAEPARI_PARENT_CONTEXT", "fixture-parent")
    monkeypatch.setattr(
        sys,
        "argv",
        ["guest_main.py", "--suite", "podway-upgrade", "--phase", "consumer-cleanup"],
    )
    observed_calls = run.call_count
    assert guest_main.main() == upgrade.lib.OUTCOME_EXITS["incomplete"]
    assert run.call_count == observed_calls
    assert path.read_bytes() == original
    assert not (results / "consumer-cleanup.json").exists()
    result = json.loads((results / "result.json").read_text())
    assert result["outcome"] == "incomplete"
    assert result["consumer_cleanup"] == "unverified"
