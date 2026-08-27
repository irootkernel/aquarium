import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_SCRIPTS = ROOT / "plugins/aquarium/skills/dev-aquarium/scripts"
CLI = SOURCE_SCRIPTS / "dev_aquarium.py"
sys.path.insert(0, str(SOURCE_SCRIPTS))

from dev_manager import artifact_digest

FAKE_CODEX = r"""#!/usr/bin/env python3
import json
import os
import shutil
import sys
from pathlib import Path

home = Path(os.environ["CODEX_HOME"])
home.mkdir(parents=True, exist_ok=True)
state_path = home / "fake-state.json"
state = json.loads(state_path.read_text()) if state_path.exists() else {
    "marketplace": None,
    "plugin": None,
    "mcp": {},
}
args = sys.argv[1:]
if args == ["login", "status"]:
    raise SystemExit(0 if (home / "logged-in").exists() else 1)
if args == ["plugin", "list", "--json"]:
    print(json.dumps({"installed": [] if state["plugin"] is None else [state["plugin"]]}))
elif args == ["plugin", "marketplace", "list", "--json"]:
    values = [] if state["marketplace"] is None else [{"name": "root-kernel"}]
    print(json.dumps({"marketplaces": values}))
elif args[:3] == ["plugin", "marketplace", "add"]:
    state["marketplace"] = args[3]
    print(json.dumps({"marketplaceName": "root-kernel"}))
elif args[:3] == ["plugin", "marketplace", "remove"]:
    state["marketplace"] = None
    print(json.dumps({"removed": True}))
elif args[:2] == ["plugin", "add"]:
    source = Path(state["marketplace"]) / "plugins/aquarium"
    manifest = json.loads((source / ".codex-plugin/plugin.json").read_text())
    installed = home / "plugins/cache/root-kernel/aquarium" / manifest["version"]
    if installed.exists():
        shutil.rmtree(installed)
    installed.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, installed)
    state["plugin"] = {
        "pluginId": "aquarium@root-kernel",
        "version": manifest["version"],
        "enabled": True,
    }
    print(json.dumps({
        "pluginId": "aquarium@root-kernel",
        "version": manifest["version"],
        "installedPath": str(installed),
    }))
elif args[:2] == ["plugin", "remove"]:
    state["plugin"] = None
    print(json.dumps({"removed": True}))
elif args == ["mcp", "list", "--json"]:
    print(json.dumps([
        {"name": name, "enabled": True, "transport": {"command": command[0], "args": command[1:]}}
        for name, command in sorted(state["mcp"].items())
    ]))
elif args[:2] == ["mcp", "remove"]:
    state["mcp"].pop(args[2], None)
elif args[:2] == ["mcp", "add"]:
    separator = args.index("--")
    state["mcp"][args[2]] = args[separator + 1:]
else:
    print(f"unsupported fake Codex command: {args}", file=sys.stderr)
    raise SystemExit(2)
state_path.write_text(json.dumps(state, sort_keys=True))
"""


EXECUTABLE_PRODUCER = r"""import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path

output = Path(os.environ["AQUARIUM_DEV_OUTPUT"])
sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
artifact = output / "bin/mulgae"
artifact.parent.mkdir()
artifact.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
artifact.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
print(json.dumps({
    "schema": "aquarium-dev-artifact-manifest/v1",
    "project_id": "mulgae",
    "git_sha": sha,
    "development_version": f"v0.1.19-dev.{sha[:12]}",
    "artifact_kind": "executable",
    "artifact_path": "bin/mulgae",
    "sha256": "sha256:" + hashlib.sha256(artifact.read_bytes()).hexdigest(),
}, sort_keys=True))
"""


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
    script_target = path / "plugins/aquarium/skills/dev-aquarium/scripts"
    script_target.mkdir(parents=True)
    for name in (
        "build_aquarium_artifact.py",
        "dev_aquarium.py",
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
\t@python3 plugins/aquarium/skills/dev-aquarium/scripts/build_aquarium_artifact.py describe

aquarium-dev-build:
\t@python3 plugins/aquarium/skills/dev-aquarium/scripts/build_aquarium_artifact.py build
""",
        encoding="utf-8",
    )
    subprocess.run(["git", "-C", path, "add", "."], check=True)
    subprocess.run(["git", "-C", path, "commit", "-q", "-m", "initial"], check=True)
    return path


def create_mulgae_repository(path: Path) -> Path:
    path.mkdir()
    init_repository(path)
    (path / "producer.py").write_text(EXECUTABLE_PRODUCER, encoding="utf-8")
    (path / "Makefile").write_text(
        """aquarium-dev-describe:
\t@printf '%s\\n' '{"schema":"aquarium-dev-producer-description/v1","project_id":"mulgae","next_version":"v0.1.19","artifact_kind":"executable","artifact_path":"bin/mulgae"}'

aquarium-dev-build:
\t@python3 producer.py
""",
        encoding="utf-8",
    )
    subprocess.run(["git", "-C", path, "add", "."], check=True)
    subprocess.run(["git", "-C", path, "commit", "-q", "-m", "initial"], check=True)
    return path


def run_cli(host_root: Path, *arguments: str):
    return subprocess.run(
        [sys.executable, CLI, "--host-root", host_root, *arguments],
        capture_output=True,
        text=True,
        check=False,
    )


def enroll_and_build(repository: Path, host_root: Path) -> None:
    enrolled = run_cli(
        host_root,
        "enroll",
        "--repository",
        repository,
        "--approve-enrollment",
        "--approve-hook",
    )
    assert enrolled.returncode == 0, enrolled.stderr
    built = run_cli(
        host_root,
        "rebuild",
        "--repository",
        repository,
        "--approve-build",
    )
    assert built.returncode == 0, built.stderr


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


def test_isolated_codex_configuration_requires_approval_and_login(
    tmp_path, monkeypatch
):
    repository = create_aquarium_repository(tmp_path / "aquarium")
    host_root = tmp_path / "host"
    fake_codex = tmp_path / "fake-codex"
    fake_codex.write_text(FAKE_CODEX, encoding="utf-8")
    fake_codex.chmod(0o755)
    stable_home = tmp_path / "stable-home"
    stable_home.mkdir()
    stable_sentinel = stable_home / "config.toml"
    stable_sentinel.write_text("stable", encoding="utf-8")
    monkeypatch.setenv("HOME", str(stable_home))
    enroll_and_build(repository, host_root)

    rejected = run_cli(
        host_root,
        "--codex-bin",
        fake_codex,
        "configure-codex",
        "--repository",
        repository,
    )
    configured = run_cli(
        host_root,
        "--codex-bin",
        fake_codex,
        "configure-codex",
        "--repository",
        repository,
        "--approve-codex",
    )

    assert rejected.returncode == 2
    assert json.loads(rejected.stderr)["error"]["code"] == "approval_required"
    assert configured.returncode == 1
    error = json.loads(configured.stderr)["error"]
    assert error["code"] == "codex_login_required"
    assert error["action"] == f"CODEX_HOME={host_root / 'codex'} codex login"
    assert stable_sentinel.read_text() == "stable"
    (host_root / "codex/logged-in").touch()

    completed = run_cli(
        host_root,
        "--codex-bin",
        fake_codex,
        "configure-codex",
        "--repository",
        repository,
        "--approve-codex",
    )

    assert completed.returncode == 0, completed.stderr
    details = json.loads(completed.stdout)["details"]
    assert details["login"] == "ready"
    assert details["plugin_version"].startswith("v0.1.14-dev.")
    assert details["paired_skills"]["git_sha"] == details["plugin_git_sha"]
    assert stat.S_IMODE((host_root / "codex").stat().st_mode) == 0o700

    diagnosis = run_cli(
        host_root,
        "--codex-bin",
        fake_codex,
        "diagnose",
        "--repository",
        repository,
    )
    report = json.loads(diagnosis.stdout)["details"]
    assert report["codex"]["paired_skills"]["version"] == details[
        "plugin_version"
    ].removeprefix("v")
    aquarium = next(
        item for item in report["resolved_projects"] if item["project_id"] == "aquarium"
    )
    assert aquarium["git_sha"] == details["plugin_git_sha"]


def test_codex_mcp_wiring_uses_the_installed_manager_and_enrolled_generation(
    tmp_path,
):
    aquarium = create_aquarium_repository(tmp_path / "aquarium")
    mulgae = create_mulgae_repository(tmp_path / "mulgae")
    host_root = tmp_path / "host"
    fake_codex = tmp_path / "fake-codex"
    fake_codex.write_text(FAKE_CODEX, encoding="utf-8")
    fake_codex.chmod(0o755)
    enroll_and_build(aquarium, host_root)
    enroll_and_build(mulgae, host_root)
    (host_root / "codex").mkdir()
    (host_root / "codex/logged-in").touch()

    configured = run_cli(
        host_root,
        "--codex-bin",
        fake_codex,
        "configure-codex",
        "--repository",
        aquarium,
        "--approve-codex",
    )

    assert configured.returncode == 0, configured.stderr
    details = json.loads(configured.stdout)["details"]
    assert details["mcp_servers"] == ["mulgae"]
    integration = next(
        item for item in details["integrations"] if item["project_id"] == "mulgae"
    )
    assert integration["state"] == "development"
    state = json.loads((host_root / "codex/fake-state.json").read_text())
    command = state["mcp"]["mulgae"]
    assert "plugins/cache/root-kernel/aquarium/" in command[1]
    assert command[-4:] == [
        "--",
        "mcp",
        "--project-root",
        str(mulgae),
    ]
