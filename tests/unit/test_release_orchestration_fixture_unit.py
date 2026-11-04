"""Real local fixture effects; no native providers or installed acceptance."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

RECIPES = Path(__file__).resolve().parents[1] / "vm/recipes"
sys.path.insert(0, str(RECIPES))
import release_fixture as fixture


@pytest.fixture
def world(tmp_path):
    root = tmp_path.resolve() / "world"
    fixture.seed(root, order="before", baseline="previous", mode="full")
    return root


@pytest.mark.parametrize("order", ["before", "after"])
@pytest.mark.parametrize("baseline", ["previous", "first"])
@pytest.mark.parametrize("mode", ["full", "light"])
def test_real_seed_variants_keep_bare_remote_and_clean_candidate(
    tmp_path, order, baseline, mode
):
    root = tmp_path.resolve() / "world"
    fixture.seed(root, order=order, baseline=baseline, mode=mode)
    assert fixture.git(root, "status", "--porcelain") == ""
    assert fixture.git(root, "rev-parse", "HEAD") != fixture.git(
        root, "rev-parse", "main", bare=True
    )
    assert fixture.git(root, "tag") == ("v1.0.0" if baseline == "previous" else "")
    assert [row["tagName"] for row in fixture.hosting(root, ["release", "list"])] == (
        ["v1.0.0"] if baseline == "previous" else []
    )
    assert ("## v1.0.0" in (root / "repo/CHANGELOG.md").read_text()) == (
        baseline == "previous"
    )


def test_bootstrap_ignores_inherited_git_hooks_and_configuration(tmp_path, monkeypatch):
    poison = tmp_path / "poison"
    poison.mkdir()
    hook = poison / "post-commit"
    sentinel = tmp_path / "unwanted"
    hook.write_text(f"#!/bin/sh\ntouch {sentinel}\n")
    hook.chmod(0o700)
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.hooksPath")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", str(poison))
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "foreign.git"))
    root = tmp_path.resolve() / "world"
    fixture.seed(root, order="before", baseline="previous", mode="full")
    assert not sentinel.exists()


def test_seed_preserves_existing_and_symlinked_destinations(world, tmp_path):
    before = (world / "world.json").read_bytes()
    with pytest.raises(fixture.FixtureError):
        fixture.seed(world, order="after", baseline="first", mode="light")
    link = tmp_path / "link"
    link.symlink_to(world, target_is_directory=True)
    with pytest.raises(fixture.FixtureError):
        fixture.seed(link / "other", order="before", baseline="first", mode="full")
    assert (world / "world.json").read_bytes() == before


def metadata(root):
    (root / "repo/manifest.json").write_text(json.dumps({"version": "1.0.1"}))


def test_gate_checks_behavior_mismatch_and_failure_frontier(world, monkeypatch):
    metadata(world)
    monkeypatch.setenv("RELEASE_TAG", "v1.0.1")
    for stage in ("prepare", "unit", "int", "e2e", "metadata"):
        assert fixture.gate(world, stage)["head"] == fixture.git(
            world, "rev-parse", "HEAD"
        )
    monkeypatch.setenv("RELEASE_TAG", "v9.9.9")
    with pytest.raises(fixture.FixtureError, match="mismatch"):
        fixture.gate(world, "metadata")
    monkeypatch.setenv("RELEASE_TAG", "v1.0.1")
    monkeypatch.setenv("AQUARIUM_FIXTURE_FAIL_STAGE", "int")
    with pytest.raises(fixture.FixtureError, match="disclosed"):
        fixture.gate(world, "int")
    monkeypatch.delenv("AQUARIUM_FIXTURE_FAIL_STAGE")
    (world / "repo/greet.py").write_text("print('wrong')\n")
    with pytest.raises(fixture.FixtureError, match="behavior"):
        fixture.gate(world, "e2e")


def test_commit_first_gate_requires_clean_actual_commit(tmp_path, monkeypatch):
    root = tmp_path.resolve() / "world"
    fixture.seed(root, order="after", baseline="previous", mode="full")
    metadata(root)
    monkeypatch.setenv("RELEASE_TAG", "v1.0.1")
    with pytest.raises(fixture.FixtureError, match="clean"):
        fixture.gate(root, "metadata")
    fixture.git(root, "commit", "-am", "[REL] Release v1.0.1")
    assert fixture.gate(root, "metadata")["head"] == fixture.git(
        root, "rev-parse", "HEAD"
    )


@pytest.mark.parametrize(
    "fault", ["missing", "content", "mode", "symlink", "resolution"]
)
def test_native_environment_refuses_wrong_hosting_identity(world, monkeypatch, fault):
    path = world / "bin/gh"
    assert fixture.native_environment(world)["PATH"].split(os.pathsep)[0] == str(
        world / "bin"
    )
    if fault == "missing":
        path.unlink()
    elif fault == "content":
        path.write_text("#!/bin/sh\nexit 0\n")
    elif fault == "mode":
        path.chmod(0o600)
    elif fault == "symlink":
        path.unlink()
        path.symlink_to(sys.executable)
    else:
        monkeypatch.setattr(fixture.shutil, "which", lambda *a, **k: "/production/gh")
    with pytest.raises(fixture.FixtureError):
        fixture.native_environment(world)


def test_explicit_owned_hook_drift_is_available_without_global_hooks(world):
    hook = world / "hooks/post-commit"
    hook.write_text("#!/bin/sh\nprintf drift > hook-effect.txt\n")
    hook.chmod(0o700)
    metadata(world)
    fixture.git(world, "commit", "-am", "[REL] Release v1.0.1")
    assert (world / "repo/hook-effect.txt").read_text() == "drift"


def test_lost_hosting_reply_preserves_real_effect_for_readback(world, monkeypatch):
    original_effects = (world / "hosting/effects.jsonl").read_text().splitlines()
    metadata(world)
    fixture.git(world, "commit", "-am", "[REL] Release v1.0.1")
    sha = fixture.git(world, "rev-parse", "HEAD")
    fixture.git(world, "push", "origin", "main")
    fixture.git(world, "tag", "-a", "v1.0.1", "-m", "release")
    fixture.git(world, "push", "origin", "v1.0.1")
    monkeypatch.setenv("AQUARIUM_FIXTURE_LOST_REPLY", "1")
    command = [
        str(world / "bin/gh"),
        "release",
        "create",
        "v1.0.1",
        "--target",
        sha,
        "--notes",
        "highlights\n\nValidation\nfixture",
    ]
    result = subprocess.run(
        command,
        env=fixture.native_environment(world),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    observed = fixture.observe(world)
    assert {row["tagName"]: row["targetCommitish"] for row in observed["hosting"]}[
        "v1.0.1"
    ] == sha
    assert (
        len((world / "hosting/effects.jsonl").read_text().splitlines())
        == len(original_effects) + 1
    )
    retry = subprocess.run(
        command,
        env=fixture.native_environment(world),
        capture_output=True,
        text=True,
        check=False,
    )
    assert retry.returncode == 2
    assert (
        len((world / "hosting/effects.jsonl").read_text().splitlines())
        == len(original_effects) + 1
    )


def test_hosting_accepts_owned_relative_notes_and_preserves_exact_body(
    world, monkeypatch
):
    notes = world / "notes.md"
    notes.write_text("Highlights\n\nValidation\nexact fixture body\n")
    monkeypatch.chdir(world / "repo")
    fixture.git(world, "tag", "-a", "v1.0.1", "-m", "fixture")
    fixture.git(world, "push", "origin", "v1.0.1")
    result = fixture.hosting(
        world,
        [
            "release",
            "create",
            "v1.0.1",
            "--target",
            "HEAD",
            "--notes-file",
            "../notes.md",
        ],
    )
    assert result["body"] == notes.read_text()


def test_foreign_origin_and_unknown_hosting_command_never_fall_through(world):
    with pytest.raises(fixture.FixtureError, match="unsupported"):
        fixture.hosting(world, ["api", "anything"])
    fixture.git(world, "remote", "set-url", "origin", "https://example.invalid/foreign")
    with pytest.raises(fixture.FixtureError, match="owned local"):
        fixture.observe(world)
