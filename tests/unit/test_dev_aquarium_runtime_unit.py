import json
import os
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SOURCE_SCRIPTS = ROOT / "plugins/aquarium/skills/dev-aquarium/scripts"
CLI = SOURCE_SCRIPTS / "dev_aquarium.py"
sys.path.insert(0, str(SOURCE_SCRIPTS))

import dev_manager
from dev_manager import ManagerError, artifact_digest


@pytest.fixture(autouse=True)
def clear_managed_immutable_flags(tmp_path):
    yield
    for current, directories, files in os.walk(tmp_path):
        os.chflags(current, 0)
        for name in (*directories, *files):
            target = Path(current) / name
            if not target.is_symlink():
                os.chflags(target, 0)


FAKE_CODEX = r"""#!/usr/bin/env python3
import json
import os
import shutil
import sys
import time
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
failure = os.environ.get("AQUARIUM_TEST_CODEX_FAILURE")
if args == ["plugin", "list", "--json"] and os.environ.get(
    "AQUARIUM_TEST_CODEX_DELAY"
) == "plugin-list":
    time.sleep(0.5)
if args == ["mcp", "list", "--json"] and failure == "mcp-list":
    print("injected mcp-list failure", file=sys.stderr)
    raise SystemExit(1)
if args == ["plugin", "list", "--json"]:
    print(json.dumps({"installed": [] if state["plugin"] is None else [state["plugin"]]}))
elif args == ["plugin", "marketplace", "list", "--json"]:
    values = [] if state["marketplace"] is None else [{"name": "root-kernel"}]
    print(json.dumps({"marketplaces": values}))
elif args[:3] == ["plugin", "marketplace", "add"]:
    if failure == "marketplace-add":
        print("injected marketplace-add failure", file=sys.stderr)
        raise SystemExit(1)
    state["marketplace"] = args[3]
    print(json.dumps({"marketplaceName": "root-kernel"}))
elif args[:3] == ["plugin", "marketplace", "remove"]:
    state["marketplace"] = None
    print(json.dumps({"removed": True}))
elif args[:2] == ["plugin", "add"]:
    if failure == "plugin-add":
        print("injected plugin-add failure", file=sys.stderr)
        raise SystemExit(1)
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
    assert not (host_root / "codex").exists()
    assert stable_sentinel.read_text() == "stable"
    (host_root / "codex").mkdir()
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

    first_sha = details["plugin_git_sha"]
    marker = repository / "revision.txt"
    marker.write_text("next", encoding="utf-8")
    subprocess.run(["git", "-C", repository, "add", marker.name], check=True)
    subprocess.run(
        ["git", "-C", repository, "commit", "-q", "--no-verify", "-m", "next"],
        check=True,
    )
    rebuilt = run_cli(
        host_root,
        "rebuild",
        "--repository",
        repository,
        "--approve-build",
    )
    assert rebuilt.returncode == 0, rebuilt.stderr
    assert (host_root / "artifacts/aquarium" / first_sha).is_dir()

    prior_configuration = (host_root / "codex/fake-state.json").read_bytes()
    (host_root / "codex").chmod(0o750)
    prior_mode = stat.S_IMODE((host_root / "codex").stat().st_mode)
    (host_root / "codex/logged-in").unlink()
    login_blocked = run_cli(
        host_root,
        "--codex-bin",
        fake_codex,
        "configure-codex",
        "--repository",
        repository,
        "--approve-codex",
    )
    assert login_blocked.returncode == 1
    assert json.loads(login_blocked.stderr)["error"]["code"] == "codex_login_required"
    assert (host_root / "artifacts/aquarium" / first_sha).is_dir()
    assert (host_root / "codex/fake-state.json").read_bytes() == prior_configuration
    assert stat.S_IMODE((host_root / "codex").stat().st_mode) == prior_mode
    (host_root / "codex/logged-in").touch()

    updated = run_cli(
        host_root,
        "--codex-bin",
        fake_codex,
        "configure-codex",
        "--repository",
        repository,
        "--approve-codex",
    )

    assert updated.returncode == 0, updated.stderr
    updated_details = json.loads(updated.stdout)["details"]
    assert updated_details["plugin_git_sha"] != first_sha
    assert not (host_root / "artifacts/aquarium" / first_sha).exists()


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


@pytest.mark.parametrize("failure", ("marketplace-add", "plugin-add", "mcp-list"))
def test_codex_configuration_restores_prior_state_after_install_failure(
    tmp_path, monkeypatch, failure
):
    repository = create_aquarium_repository(tmp_path / "aquarium")
    host_root = tmp_path / "host"
    fake_codex = tmp_path / "fake-codex"
    fake_codex.write_text(FAKE_CODEX, encoding="utf-8")
    fake_codex.chmod(0o755)
    enroll_and_build(repository, host_root)
    (host_root / "codex").mkdir()
    (host_root / "codex/logged-in").touch()

    configured = run_cli(
        host_root,
        "--codex-bin",
        fake_codex,
        "configure-codex",
        "--repository",
        repository,
        "--approve-codex",
    )
    assert configured.returncode == 0, configured.stderr
    prior_config = (host_root / "codex/fake-state.json").read_bytes()
    prior_plugins = {
        path.relative_to(host_root / "codex/plugins"): path.read_bytes()
        for path in (host_root / "codex/plugins").rglob("*")
        if path.is_file()
    }
    (host_root / "codex").chmod(0o750)
    prior_mode = stat.S_IMODE((host_root / "codex").stat().st_mode)

    marker = repository / "revision.txt"
    marker.write_text("next", encoding="utf-8")
    subprocess.run(["git", "-C", repository, "add", marker.name], check=True)
    subprocess.run(
        ["git", "-C", repository, "commit", "-q", "--no-verify", "-m", "next"],
        check=True,
    )
    rebuilt = run_cli(
        host_root,
        "rebuild",
        "--repository",
        repository,
        "--approve-build",
    )
    assert rebuilt.returncode == 0, rebuilt.stderr

    monkeypatch.setenv("AQUARIUM_TEST_CODEX_FAILURE", failure)
    failed = run_cli(
        host_root,
        "--codex-bin",
        fake_codex,
        "configure-codex",
        "--repository",
        repository,
        "--approve-codex",
    )

    assert failed.returncode == 1
    assert json.loads(failed.stderr)["error"]["code"] == "codex_not_configured"
    assert (host_root / "codex/fake-state.json").read_bytes() == prior_config
    assert stat.S_IMODE((host_root / "codex").stat().st_mode) == prior_mode
    restored_plugins = {
        path.relative_to(host_root / "codex/plugins"): path.read_bytes()
        for path in (host_root / "codex/plugins").rglob("*")
        if path.is_file()
    }
    assert restored_plugins == prior_plugins

    monkeypatch.delenv("AQUARIUM_TEST_CODEX_FAILURE")
    retried = run_cli(
        host_root,
        "--codex-bin",
        fake_codex,
        "configure-codex",
        "--repository",
        repository,
        "--approve-codex",
    )
    assert retried.returncode == 0, retried.stderr


def test_codex_command_timeout_has_a_bounded_configuration_error(tmp_path, monkeypatch):
    sleeper = tmp_path / "sleeping-codex"
    child_pid = tmp_path / "child-pid"
    sleeper.write_text(
        '#!/bin/sh\nsleep 10 &\necho "$!" > "$AQUARIUM_CHILD_PID"\nwait\n',
        encoding="utf-8",
    )
    sleeper.chmod(0o700)
    monkeypatch.setenv("AQUARIUM_CHILD_PID", str(child_pid))
    started = time.monotonic()
    with pytest.raises(ManagerError) as raised:
        dev_manager._run_codex(
            str(sleeper),
            tmp_path,
            "plugin",
            "list",
            "--json",
            timeout_seconds=0.5,
        )
    elapsed = time.monotonic() - started

    assert raised.value.code == "codex_not_configured"
    assert "within 0.5 seconds" in raised.value.message
    assert elapsed < 2
    descendant = int(child_pid.read_text())
    deadline = time.monotonic() + 1
    while time.monotonic() < deadline:
        try:
            os.kill(descendant, 0)
        except ProcessLookupError:
            break
        time.sleep(0.01)
    else:
        pytest.fail("the timed-out Codex descendant survived process-group cleanup")


def test_codex_configuration_success_is_not_reversed_by_cleanup_failure(tmp_path):
    repository = create_aquarium_repository(tmp_path / "aquarium")
    host_root = tmp_path / "host"
    fake_codex = tmp_path / "fake-codex"
    fake_codex.write_text(FAKE_CODEX, encoding="utf-8")
    fake_codex.chmod(0o755)
    enroll_and_build(repository, host_root)
    (host_root / "codex").mkdir()
    (host_root / "codex/logged-in").touch()
    first = run_cli(
        host_root,
        "--codex-bin",
        fake_codex,
        "configure-codex",
        "--repository",
        repository,
        "--approve-codex",
    )
    assert first.returncode == 0, first.stderr
    first_sha = json.loads(first.stdout)["details"]["plugin_git_sha"]

    marker = repository / "revision.txt"
    marker.write_text("next", encoding="utf-8")
    subprocess.run(["git", "-C", repository, "add", marker.name], check=True)
    subprocess.run(
        ["git", "-C", repository, "commit", "-q", "--no-verify", "-m", "next"],
        check=True,
    )
    rebuilt = run_cli(
        host_root,
        "rebuild",
        "--repository",
        repository,
        "--approve-build",
    )
    assert rebuilt.returncode == 0, rebuilt.stderr
    old_generation = host_root / "artifacts/aquarium" / first_sha
    dev_manager._unseal_managed_tree(old_generation)
    shutil.rmtree(old_generation)
    old_generation.write_text("blocks cleanup", encoding="utf-8")

    updated = run_cli(
        host_root,
        "--codex-bin",
        fake_codex,
        "configure-codex",
        "--repository",
        repository,
        "--approve-codex",
    )

    assert updated.returncode == 0, updated.stderr
    details = json.loads(updated.stdout)["details"]
    assert details["plugin_git_sha"] != first_sha
    assert old_generation.is_file()


def test_next_configuration_recovers_an_interrupted_durable_transaction(tmp_path):
    repository = create_aquarium_repository(tmp_path / "aquarium")
    host_root = tmp_path / "host"
    fake_codex = tmp_path / "fake-codex"
    fake_codex.write_text(FAKE_CODEX, encoding="utf-8")
    fake_codex.chmod(0o755)
    enroll_and_build(repository, host_root)
    codex_home = host_root / "codex"
    codex_home.mkdir()
    (codex_home / "logged-in").touch()
    configured = run_cli(
        host_root,
        "--codex-bin",
        fake_codex,
        "configure-codex",
        "--repository",
        repository,
        "--approve-codex",
    )
    assert configured.returncode == 0, configured.stderr
    codex_home.chmod(0o750)
    prior_state = (codex_home / "fake-state.json").read_bytes()

    transaction = host_root / "transactions/codex-config"
    transaction.parent.mkdir(parents=True, exist_ok=True)
    transaction.mkdir()
    dev_manager._snapshot_codex_configuration(codex_home, transaction)
    (transaction / "home-mode").write_text("750\n", encoding="ascii")
    (transaction / "active").write_text("aquarium-codex-transaction/v1\n")
    (codex_home / "fake-state.json").write_text("{}", encoding="utf-8")
    shutil.rmtree(codex_home / "plugins")
    codex_home.chmod(0o700)
    (codex_home / "logged-in").unlink()

    recovered = run_cli(
        host_root,
        "--codex-bin",
        fake_codex,
        "configure-codex",
        "--repository",
        repository,
        "--approve-codex",
    )

    assert recovered.returncode == 1
    assert json.loads(recovered.stderr)["error"]["code"] == "codex_login_required"
    assert (codex_home / "fake-state.json").read_bytes() == prior_state
    assert (codex_home / "plugins").is_dir()
    assert stat.S_IMODE(codex_home.stat().st_mode) == 0o750
    assert not transaction.exists()

    (codex_home / "logged-in").touch()
    retried = run_cli(
        host_root,
        "--codex-bin",
        fake_codex,
        "configure-codex",
        "--repository",
        repository,
        "--approve-codex",
    )
    assert retried.returncode == 0, retried.stderr


def test_concurrent_codex_configuration_is_serialized(tmp_path, monkeypatch):
    repository = create_aquarium_repository(tmp_path / "aquarium")
    host_root = tmp_path / "host"
    fake_codex = tmp_path / "fake-codex"
    fake_codex.write_text(FAKE_CODEX, encoding="utf-8")
    fake_codex.chmod(0o755)
    enroll_and_build(repository, host_root)
    (host_root / "codex").mkdir()
    (host_root / "codex/logged-in").touch()
    monkeypatch.setenv("AQUARIUM_TEST_CODEX_DELAY", "plugin-list")
    command = [
        sys.executable,
        CLI,
        "--host-root",
        host_root,
        "--codex-bin",
        fake_codex,
        "configure-codex",
        "--repository",
        repository,
        "--approve-codex",
    ]

    first = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    second = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    first_stdout, first_stderr = first.communicate(timeout=30)
    second_stdout, second_stderr = second.communicate(timeout=30)

    assert first.returncode == 0, first_stderr
    assert second.returncode == 0, second_stderr
    assert json.loads(first_stdout)["status"] == "success"
    assert json.loads(second_stdout)["status"] == "success"
    assert not (host_root / "transactions/codex-config").exists()
