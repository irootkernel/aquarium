"""Sealed release inputs never execute upstream code or modify the baseline."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "podway_release_bundle", ROOT / "tests/vm/host_bundle.py"
)
bundle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bundle)


@pytest.fixture
def release(tmp_path, monkeypatch):
    source = tmp_path / "release"
    hashes = {}
    for relative in bundle.PODWAY_RELEASE_FILES:
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f"synthetic {relative}\n".encode())
        hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    (source / "bin/podway").chmod(0o755)
    monkeypatch.setattr(bundle, "PODWAY_RELEASE_FILES", hashes)
    stable = json.loads((bundle.PROFILES_ROOT / bundle.STABLE_PROFILE_NAME).read_text())
    profile = bundle.derive_candidate_profile(
        stable, "a" * 64, "v0.1.21-dev.123456789abc", "b" * 64
    )
    return source, profile


def test_release_sealing_updates_only_the_selected_candidate(tmp_path, release):
    source, profile = release
    previous = copy.deepcopy(profile)
    files, identity = bundle.seal_podway_release(source, tmp_path / "bundle", profile)
    current = {row["name"]: row for row in profile["components"]}
    before = {row["name"]: row for row in previous["components"]}
    assert current["podway"]["version"] == "v0.2.17"
    assert before["podway"]["version"] == "v0.2.14"
    assert current["use-podway"]["pin"] == {"commit": bundle.PODWAY_RELEASE_COMMIT}
    assert (
        current["use-podway"]["skill_tree"]["sha256"] == identity["skill_tree_sha256"]
    )
    assert all((tmp_path / "bundle" / name).is_file() for name in files)
    assert len(files) == len(bundle.PODWAY_RELEASE_FILES)
    assert bundle._PROFILE_VALIDATOR.validate_profile(profile) == []


@pytest.mark.parametrize("mutation", ["changed", "missing", "extra", "symlink"])
def test_release_sealing_refuses_incomplete_or_unverified_bytes(
    tmp_path, release, mutation
):
    source, profile = release
    path = source / "skills/use-podway/references/goal.md"
    if mutation == "changed":
        path.write_text("changed source")
    elif mutation == "missing":
        path.unlink()
    elif mutation == "extra":
        (source / "skills/use-podway/unexpected").write_text("extra")
    else:
        path.unlink()
        path.symlink_to(source / "skills/use-podway/SKILL.md")
    with pytest.raises(bundle.BundleError):
        bundle.seal_podway_release(source, tmp_path / "bundle", profile)
    assert not (tmp_path / "bundle").exists()


def test_release_sealing_checks_copied_bytes_again(tmp_path, monkeypatch, release):
    source, profile = release
    original_copy = bundle._copy_tree

    def drift(source, target, **kwargs):
        copied = original_copy(source, target, **kwargs)
        (target / "bin/podway").write_text("changed during copy")
        return copied

    monkeypatch.setattr(bundle, "_copy_tree", drift)
    with pytest.raises(bundle.BundleError, match="changed while sealing"):
        bundle.seal_podway_release(source, tmp_path / "bundle", profile)


def test_previous_release_is_sealed_separately(tmp_path, release, monkeypatch):
    source, _ = release
    inventory = {
        name: hashlib.sha256((source / name).read_bytes()).hexdigest()
        for name in bundle.PODWAY_PREVIOUS_RELEASE_FILES
    }
    monkeypatch.setattr(bundle, "PODWAY_PREVIOUS_RELEASE_FILES", inventory)
    files = bundle.seal_release_files(
        source, tmp_path / "bundle", "dependencies/podway-0.2.16", inventory
    )
    assert all((tmp_path / "bundle" / name).is_file() for name in files)
    assert not (tmp_path / "bundle/dependencies/podway-0.2.17").exists()
    (source / "bin/podway").write_bytes(b"tampered previous executable")
    with pytest.raises(bundle.BundleError, match="digest differs"):
        bundle.seal_release_files(source, tmp_path / "refused", "previous", inventory)
    assert not (tmp_path / "refused").exists()
