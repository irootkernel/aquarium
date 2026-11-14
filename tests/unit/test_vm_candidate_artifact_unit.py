import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "candidate_artifact", Path(__file__).parents[1] / "vm/candidate_artifact.py"
)
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


@pytest.fixture
def payload(tmp_path):
    repository = tmp_path / "repository"
    repository.mkdir()
    for args in (
        ["init", "-q", "-b", "main"],
        ["config", "user.name", "Fixture"],
        ["config", "user.email", "fixture@example.invalid"],
    ):
        subprocess.run(["git", "-C", str(repository), *args], check=True)
    plugin = repository / "plugins/aquarium/.codex-plugin/plugin.json"
    plugin.parent.mkdir(parents=True)
    plugin.write_text('{"name":"aquarium","version":"0.1.22"}')
    executable = repository / "plugins/aquarium/tool"
    executable.write_text("#!/bin/sh\nexit 0\n")
    executable.chmod(0o755)
    subprocess.run(["git", "-C", str(repository), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(repository), "commit", "-qm", "fixture"], check=True
    )
    sha = subprocess.check_output(
        ["git", "-C", str(repository), "rev-parse", "HEAD"], text=True
    ).strip()
    output = tmp_path / "output"
    output.mkdir()
    return repository, sha, output


def test_build_without_channel_or_makefile_preserves_payload_identity(payload):
    repository, sha, output = payload
    manifest = builder.build(repository, sha, output)
    artifact = output / "marketplace"
    assert manifest["git_sha"] == sha
    assert manifest["development_version"] == f"v0.1.22-dev.{sha[:12]}"
    assert manifest["sha256"] == builder.artifact_digest(artifact)
    assert (artifact / "plugins/aquarium/tool").stat().st_mode & 0o777 == 0o755
    plugin = json.loads(
        (artifact / "plugins/aquarium/.codex-plugin/plugin.json").read_text()
    )
    assert plugin["version"] == f"0.1.22-dev.{sha[:12]}"


def test_dirty_or_wrong_selected_commit_is_refused_before_output(payload):
    repository, sha, output = payload
    with pytest.raises(builder.ArtifactError):
        builder.build(repository, "0" * 40, output)
    (repository / "uncommitted").write_text("uncommitted")
    with pytest.raises(builder.ArtifactError):
        builder.build(repository, sha, output)
    assert not list(output.iterdir())


def test_nonempty_and_symlink_output_are_refused(payload, tmp_path):
    repository, sha, output = payload
    (output / "sentinel").write_text("preserve")
    with pytest.raises(builder.ArtifactError):
        builder.build(repository, sha, output)
    link = tmp_path / "link"
    link.symlink_to(output, target_is_directory=True)
    with pytest.raises(builder.ArtifactError):
        builder.build(repository, sha, link)
    assert (output / "sentinel").read_text() == "preserve"


def test_digest_refuses_symlinks_and_distinguishes_prefix_paths(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a/file").write_text("nested")
    (tmp_path / "a.txt").write_text("sibling")
    before = builder.artifact_digest(tmp_path)
    (tmp_path / "a/file").write_text("changed")
    assert builder.artifact_digest(tmp_path) != before
    (tmp_path / "alias").symlink_to(tmp_path / "a/file")
    with pytest.raises(builder.ArtifactError):
        builder.artifact_digest(tmp_path)
