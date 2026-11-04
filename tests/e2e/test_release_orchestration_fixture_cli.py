"""Black-box local fixture utility; no hosting service or native agents."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "vm/recipes/release_fixture.py"


def command(*args, env=None):
    return subprocess.run(
        [sys.executable, "-B", str(SCRIPT), *map(str, args)],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


@pytest.mark.parametrize("order", ["before", "after"])
def test_cli_gate_order_and_serial_make_effects(tmp_path, order):
    import os

    root = tmp_path.resolve() / "world"
    seeded = command("seed", "--root", root, "--order", order)
    assert seeded.returncode == 0, seeded.stdout
    (root / "repo/manifest.json").write_text('{"version":"1.0.1"}\n')
    env = {
        **os.environ,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "core.hooksPath",
        "GIT_CONFIG_VALUE_0": str(root / "hooks"),
        "AQUARIUM_RELEASE_FIXTURE_DRIVER": str(SCRIPT),
        "AQUARIUM_RELEASE_FIXTURE_ROOT": str(root),
        "RELEASE_TAG": "v1.0.1",
    }
    if order == "after":
        refused = command("gate", "--root", root, "--stage", "metadata", env=env)
        assert refused.returncode == 2
        subprocess.run(
            ["git", "-C", str(root / "repo"), "commit", "-am", "[REL] Release v1.0.1"],
            env=env,
            capture_output=True,
            check=True,
        )
    result = subprocess.run(
        ["make", "test"],
        cwd=root / "repo",
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    stages = [
        json.loads(line)["stage"]
        for line in result.stdout.splitlines()
        if line.startswith('{"stage"')
    ]
    assert stages == ["prepare", "unit", "int", "e2e"]
    mismatch = command(
        "gate",
        "--root",
        root,
        "--stage",
        "metadata",
        env={**env, "RELEASE_TAG": "v9.9.9"},
    )
    assert mismatch.returncode == 2


def test_cli_refusal_preserves_existing_world_and_returns_json(tmp_path):
    root = tmp_path.resolve() / "world"
    assert command("seed", "--root", root).returncode == 0
    before = (root / "world.json").read_bytes()
    duplicate = command("seed", "--root", root)
    assert duplicate.returncode == 2
    assert "error" in json.loads(duplicate.stdout)
    assert (root / "world.json").read_bytes() == before
    unsupported = command("hosting", "--root", root, "--", "auth", "login")
    assert unsupported.returncode == 2
