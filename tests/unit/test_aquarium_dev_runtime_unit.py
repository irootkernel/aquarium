import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SOURCE_SCRIPTS = ROOT / "plugins/aquarium/skills/aquarium-dev/scripts"
sys.path.insert(0, str(SOURCE_SCRIPTS))

from dev_manager import artifact_digest


@pytest.fixture(autouse=True)
def clear_managed_immutable_flags(tmp_path):
    yield
    for current, directories, files in os.walk(tmp_path):
        os.chflags(current, 0)
        for name in (*directories, *files):
            target = Path(current) / name
            if not target.is_symlink():
                os.chflags(target, 0)


def init_repository(path: Path) -> None:
    subprocess.run(["git", "init", "-q", "-b", "main", path], check=True)
    subprocess.run(["git", "-C", path, "config", "user.name", "Test"], check=True)
    subprocess.run(
        ["git", "-C", path, "config", "user.email", "test@example.invalid"],
        check=True,
    )


def create_aquarium_repository(path: Path) -> Path:
    path.mkdir()
    init_repository(path)
    script_target = path / "plugins/aquarium/skills/aquarium-dev/scripts"
    script_target.mkdir(parents=True)
    for name in (
        "build_aquarium_artifact.py",
        "aquarium_dev.py",
        "dev_contract.py",
        "dev_manager.py",
    ):
        shutil.copy2(SOURCE_SCRIPTS / name, script_target / name)
    manifest = path / "plugins/aquarium/.codex-plugin/plugin.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps({"name": "aquarium", "version": "0.1.14", "skills": "./skills/"}),
        encoding="utf-8",
    )
    marketplace = path / ".agents/plugins/marketplace.json"
    marketplace.parent.mkdir(parents=True)
    marketplace.write_text(
        json.dumps(
            {
                "name": "root-kernel",
                "plugins": [
                    {
                        "name": "aquarium",
                        "source": {"source": "local", "path": "./plugins/aquarium"},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (path / "Makefile").write_text(
        """aquarium-dev-describe:
\t@python3 plugins/aquarium/skills/aquarium-dev/scripts/build_aquarium_artifact.py describe

aquarium-dev-build:
\t@python3 plugins/aquarium/skills/aquarium-dev/scripts/build_aquarium_artifact.py build
""",
        encoding="utf-8",
    )
    subprocess.run(["git", "-C", path, "add", "."], check=True)
    subprocess.run(["git", "-C", path, "commit", "-q", "-m", "initial"], check=True)
    return path


def test_aquarium_producer_uses_committed_bytes_and_embeds_identity(tmp_path):
    repository = create_aquarium_repository(tmp_path / "aquarium")
    description = subprocess.run(
        ["make", "-s", "aquarium-dev-describe"],
        cwd=repository,
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(description.stdout)["artifact_path"] == "marketplace"
    output = tmp_path / "output"
    output.mkdir()
    environment = os.environ.copy()
    environment["AQUARIUM_DEV_OUTPUT"] = str(output)

    built = subprocess.run(
        ["make", "-s", "aquarium-dev-build"],
        cwd=repository,
        capture_output=True,
        text=True,
        check=True,
        env=environment,
    )

    manifest = json.loads(built.stdout)
    sha = subprocess.check_output(
        ["git", "-C", repository, "rev-parse", "HEAD"], text=True
    ).strip()
    artifact = output / "marketplace"
    plugin = json.loads(
        (artifact / "plugins/aquarium/.codex-plugin/plugin.json").read_text()
    )
    assert manifest["git_sha"] == sha
    assert manifest["development_version"] == f"v0.1.14-dev.{sha[:12]}"
    assert plugin["version"] == f"0.1.14-dev.{sha[:12]}"
    assert manifest["sha256"] == artifact_digest(artifact)

    (repository / "plugins/aquarium/.codex-plugin/plugin.json").write_text("dirty")
    rejected = subprocess.run(
        ["make", "-s", "aquarium-dev-build"],
        cwd=repository,
        capture_output=True,
        text=True,
        check=False,
        env={**environment, "AQUARIUM_DEV_OUTPUT": str(tmp_path / "unused")},
    )
    assert rejected.returncode == 2
    assert "clean working tree" in rejected.stderr
