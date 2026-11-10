"""Offline manual-suite safeguards, without installed acceptance claims."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

RECIPES = Path(__file__).parents[1] / "vm/recipes"
sys.path.insert(0, str(RECIPES))
SPEC = importlib.util.spec_from_file_location(
    "manual_mulgae", RECIPES / "mulgae_adoption.py"
)
assert SPEC and SPEC.loader
suite = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(suite)


@pytest.fixture
def environment(tmp_path, monkeypatch):
    results = tmp_path / "results"
    results.mkdir()
    for method in ("verify_guest_identity", "verify_sealed_inputs", "guard"):
        monkeypatch.setattr(suite.lib, method, Mock())
    monkeypatch.setattr(suite.lib, "results_directory", lambda _: results)
    context = SimpleNamespace(
        root=tmp_path,
        inputs={"candidate": {"git_sha": "a" * 40}},
        snapshot=Mock(
            return_value=[
                {
                    "installation_scope": "user-global",
                    "relative_path": "sentinel",
                    "sha256": "a" * 64,
                    "executable": False,
                }
            ]
        ),
    )
    state = {
        "version": "v0.1.26",
        "binary_sha256": "baseline",
        "skill_tree_sha256": "baseline",
    }
    monkeypatch.setattr(suite, "observe", lambda _: dict(state))
    return context, results, state


def test_identity_failure_performs_no_capture(environment, monkeypatch):
    context, results, _ = environment
    monkeypatch.setattr(
        suite.lib,
        "verify_guest_identity",
        Mock(side_effect=suite.lib.IdentityError("wrong guest")),
    )
    with pytest.raises(suite.lib.IdentityError):
        suite.run(context, "prepare")
    assert list(results.iterdir()) == []
    context.snapshot.assert_not_called()


def test_candidate_cannot_replace_baseline(environment):
    context, results, state = environment
    state["version"] = "v0.1.27"
    with pytest.raises(suite.lib.RecipeError):
        suite.run(context, "candidate")
    assert list(results.iterdir()) == []
    context.snapshot.assert_not_called()


def test_restore_requires_candidate_and_original_identity(environment, monkeypatch):
    context, results, state = environment
    original = dict(state)
    assert suite.run(context, "prepare") == 0
    with pytest.raises(suite.lib.RecipeError):
        suite.run(context, "consumer-cleanup")
    state.update(
        version="v0.1.27",
        binary_sha256="candidate",
        skill_tree_sha256=suite.RELEASE_SKILL_TREE,
    )
    assert suite.run(context, "candidate") == 0
    with pytest.raises(suite.lib.RecipeError):
        suite.run(context, "consumer-cleanup")
    assert not (results / "consumer-cleanup.json").exists()
    assert list(results.glob("consumer-cleanup-*.json"))
    state.update(original)
    finish = Mock(return_value=0)
    monkeypatch.setattr(suite.lib, "finish", finish)
    assert suite.run(context, "consumer-cleanup") == 0
    assert (
        json.loads((results / "consumer-cleanup.json").read_text())["consumer_cleanup"]
        == "verified"
    )
    finish.assert_called_once()


def test_capture_is_not_replayed(environment):
    context, _, _ = environment
    suite.run(context, "prepare")
    with pytest.raises(suite.lib.RecipeError):
        suite.run(context, "prepare")
    assert context.snapshot.call_count == 1


def test_corrupt_inventory_history_is_preserved(environment):
    context, results, _ = environment
    original = "corrupted original history"
    (results / "inventories.json").write_text(original)
    with pytest.raises(suite.lib.RecipeError):
        suite.run(context, "prepare")
    context.snapshot.assert_not_called()
    assert (results / "inventories.json").read_text() == original
    assert not (results / "prepare.json").exists()
