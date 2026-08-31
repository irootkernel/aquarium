import importlib.util
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "plugins/aquarium/skills/aquarium-dev/scripts"
sys.path.insert(0, str(SCRIPT_DIR))

MANAGER_SPEC = importlib.util.spec_from_file_location(
    "aquarium_dev_manager", SCRIPT_DIR / "dev_manager.py"
)
assert MANAGER_SPEC is not None and MANAGER_SPEC.loader is not None
dev_manager = importlib.util.module_from_spec(MANAGER_SPEC)
sys.modules[MANAGER_SPEC.name] = dev_manager
MANAGER_SPEC.loader.exec_module(dev_manager)

CLI_SPEC = importlib.util.spec_from_file_location(
    "aquarium_dev_cli", SCRIPT_DIR / "aquarium_dev.py"
)
assert CLI_SPEC is not None and CLI_SPEC.loader is not None
aquarium_dev = importlib.util.module_from_spec(CLI_SPEC)
CLI_SPEC.loader.exec_module(aquarium_dev)

LAUNCHER_SPEC = importlib.util.spec_from_file_location(
    "aquarium_dev_launcher", SCRIPT_DIR / "aquarium_dev_launcher.py"
)
assert LAUNCHER_SPEC is not None and LAUNCHER_SPEC.loader is not None
launcher = importlib.util.module_from_spec(LAUNCHER_SPEC)
LAUNCHER_SPEC.loader.exec_module(launcher)


@pytest.fixture(autouse=True)
def clear_managed_immutable_flags(tmp_path):
    yield
    for current, directories, files in os.walk(tmp_path):
        os.chflags(current, 0)
        for name in (*directories, *files):
            target = Path(current) / name
            if not target.is_symlink():
                os.chflags(target, 0)


def executable_staging(root: Path, git_sha: str) -> tuple[Path, dict[str, str]]:
    staging = root / f"staging-{git_sha[:8]}"
    artifact = staging / "bin" / "podway"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("#!/bin/sh\nprintf 'development podway\\n'\n", encoding="utf-8")
    artifact.chmod(0o755)
    manifest = {
        "schema": "aquarium-dev-artifact-manifest/v1",
        "project_id": "podway",
        "git_sha": git_sha,
        "development_version": f"v0.2.8-dev.{git_sha[:12]}",
        "artifact_kind": "executable",
        "artifact_path": "bin/podway",
        "sha256": dev_manager.artifact_digest(artifact),
    }
    (staging / ".aquarium-manifest.json").write_text("{}\n", encoding="utf-8")
    return staging, manifest


def test_default_host_root_is_aquarium_dev():
    arguments = aquarium_dev.parser().parse_args(
        ["diagnose", "--repository", str(ROOT)]
    )

    assert arguments.host_root == Path.home() / ".aquarium-dev"


def test_publication_exposes_only_current_executable_in_development_bin(tmp_path):
    host_root = tmp_path / ".aquarium-dev"
    (host_root / "artifacts" / "podway").mkdir(parents=True)
    first_sha = "1" * 40
    second_sha = "2" * 40
    first, first_manifest = executable_staging(tmp_path, first_sha)
    second, second_manifest = executable_staging(tmp_path, second_sha)

    _, first_result = dev_manager._publish(host_root, first, first_manifest)
    selector = host_root / "bin" / "podway"
    assert selector.is_symlink()
    assert selector.resolve() == Path(first_result["artifact"])
    stable_target = os.readlink(selector)
    assert stable_target == "../current/podway/bin/podway"

    _, second_result = dev_manager._publish(host_root, second, second_manifest)
    assert selector.resolve() == Path(second_result["artifact"])
    assert os.readlink(selector) == stable_target
    assert not (host_root / "artifacts" / "podway" / first_sha).exists()
    assert not (host_root / "runtime").exists()


def test_current_selector_failure_preserves_previous_generation(tmp_path, monkeypatch):
    host_root = tmp_path / ".aquarium-dev"
    (host_root / "artifacts" / "podway").mkdir(parents=True)
    first_sha = "1" * 40
    second_sha = "2" * 40
    first, first_manifest = executable_staging(tmp_path, first_sha)
    second, second_manifest = executable_staging(tmp_path, second_sha)
    dev_manager._publish(host_root, first, first_manifest)
    current = host_root / "current" / "podway"
    command = host_root / "bin" / "podway"
    previous_current = os.readlink(current)
    stable_command = os.readlink(command)
    original_replace = dev_manager.os.replace
    failed = False

    def fail_current_replacement(source, target):
        nonlocal failed
        if Path(target) == current and not failed:
            failed = True
            raise OSError("injected current selector failure")
        return original_replace(source, target)

    monkeypatch.setattr(dev_manager.os, "replace", fail_current_replacement)
    with pytest.raises(dev_manager.ManagerError) as failure:
        dev_manager._publish(host_root, second, second_manifest)

    assert failure.value.code == "publication_failed"
    assert os.readlink(current) == previous_current
    assert os.readlink(command) == stable_command
    assert current.resolve().name == first_sha
    assert command.resolve().parent.parent.name == first_sha


def test_launcher_prepends_development_bin_and_preserves_codex_home(monkeypatch):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: Path("/Users/test")))
    original = {
        "PATH": "/usr/local/bin:/usr/bin",
        "CODEX_HOME": "/Users/test/.codex-hsy",
        "TOKEN": "opaque",
    }

    environment = launcher.development_environment(original)

    assert environment["PATH"] == (
        "/Users/test/.aquarium-dev/bin:/usr/local/bin:/usr/bin"
    )
    assert environment["CODEX_HOME"] == "/Users/test/.codex-hsy"
    assert environment["TOKEN"] == "opaque"
    assert original["PATH"] == "/usr/local/bin:/usr/bin"


def test_launcher_executes_leased_generation_with_derived_environment(
    tmp_path, monkeypatch
):
    observed = {}
    home = tmp_path / "home"
    host_root = home / ".aquarium-dev"
    (host_root / "artifacts" / "podway").mkdir(parents=True)
    git_sha = "1" * 40
    staging, manifest = executable_staging(tmp_path, git_sha)
    _, published = dev_manager._publish(host_root, staging, manifest)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))

    def fake_execve(executable, arguments, environment):
        observed.update(
            executable=executable, arguments=arguments, environment=environment
        )
        raise OSError("stop after capture")

    monkeypatch.setattr(os, "execve", fake_execve)
    assert launcher.main(["podway", "doctor"]) == 127
    assert observed["executable"] == Path(published["artifact"])
    assert observed["arguments"] == ["podway", "doctor"]
    assert (
        observed["environment"]["PATH"]
        .split(os.pathsep)[0]
        .endswith("/.aquarium-dev/bin")
    )


def test_missing_development_tool_falls_back_to_global_path(
    tmp_path, monkeypatch, capsys
):
    home = tmp_path / "home"
    global_bin = tmp_path / "global-bin"
    global_bin.mkdir()
    stable = global_bin / "podway"
    stable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    stable.chmod(0o755)
    original = {
        "PATH": str(global_bin),
        "CODEX_HOME": str(home / ".codex-hsy"),
        "TOKEN": "opaque",
    }
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    monkeypatch.setattr(os, "environ", original.copy())
    observed = {}

    def fake_execve(executable, arguments, environment):
        observed.update(
            executable=executable, arguments=arguments, environment=environment
        )
        raise OSError("stop after capture")

    monkeypatch.setattr(os, "execve", fake_execve)

    assert launcher.main(["podway", "version"]) == 127

    assert "stop after capture" in capsys.readouterr().err
    assert observed["executable"] == stable
    assert observed["arguments"] == ["podway", "version"]
    assert observed["environment"]["PATH"].split(os.pathsep) == [
        str(home / ".aquarium-dev/bin"),
        str(global_bin),
    ]
    assert observed["environment"]["CODEX_HOME"] == original["CODEX_HOME"]
    assert os.environ == original


def test_invalid_development_generation_does_not_fall_back(tmp_path, monkeypatch):
    home = tmp_path / "home"
    host_root = home / ".aquarium-dev"
    current = host_root / "current" / "podway"
    current.parent.mkdir(parents=True)
    current.write_text("invalid", encoding="utf-8")
    global_bin = tmp_path / "global-bin"
    global_bin.mkdir()
    stable = global_bin / "podway"
    stable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    stable.chmod(0o755)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    monkeypatch.setenv("PATH", str(global_bin))
    monkeypatch.setattr(
        os,
        "execve",
        lambda *_args, **_kwargs: pytest.fail("invalid development state fell back"),
    )

    assert launcher.main(["podway", "version"]) == 127


def test_global_fallback_excludes_both_aquarium_roots(tmp_path, monkeypatch):
    home = tmp_path / "home"
    production_bin = home / ".aquarium" / "bin"
    development_bin = home / ".aquarium-dev" / "bin"
    for candidate_bin in (production_bin, development_bin):
        candidate_bin.mkdir(parents=True)
        candidate = candidate_bin / "podway"
        candidate.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        candidate.chmod(0o755)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))

    with pytest.raises(OSError, match="global executable are unavailable"):
        launcher.global_executable(
            "podway", {"PATH": f"{development_bin}{os.pathsep}{production_bin}"}
        )


def test_launcher_lease_defers_superseded_generation_cleanup(tmp_path, monkeypatch):
    home = tmp_path / "home"
    host_root = home / ".aquarium-dev"
    (host_root / "artifacts" / "podway").mkdir(parents=True)
    first_sha = "1" * 40
    second_sha = "2" * 40
    first, first_manifest = executable_staging(tmp_path, first_sha)
    second, second_manifest = executable_staging(tmp_path, second_sha)
    dev_manager._publish(host_root, first, first_manifest)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    monkeypatch.setattr(dev_manager, "_spawn_cleanup", lambda *_args: None)
    executable, descriptor = launcher.leased_executable("podway")
    assert executable.parent.parent.name == first_sha
    assert os.get_inheritable(descriptor)
    try:
        dev_manager._publish(host_root, second, second_manifest)
        assert (host_root / "artifacts/podway" / first_sha).exists()
        status, details = dev_manager.cleanup_generation(
            "podway", first_sha, host_root, wait=False
        )
        assert status == "no-change"
        assert details["leased"] is True
    finally:
        os.close(descriptor)

    status, details = dev_manager.cleanup_generation(
        "podway", first_sha, host_root, wait=False
    )
    assert status == "success"
    assert details["removed"] is True


@pytest.mark.parametrize("command", ("unknown", "./podway"))
def test_launcher_rejects_commands_outside_development_channel(
    command, monkeypatch, capsys
):
    monkeypatch.setattr(
        os,
        "execve",
        lambda *_args, **_kwargs: pytest.fail("unsupported command was executed"),
    )

    assert launcher.main([command]) == 2
    assert f"unsupported development command: {command}" in capsys.readouterr().err


def test_missing_required_tool_requests_dev_setup(tmp_path, monkeypatch, capsys):
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    monkeypatch.setenv("PATH", str(tmp_path / "empty-global-bin"))

    assert launcher.main(["dolgorae", "--version"]) == 127
    error = capsys.readouterr().err
    assert "development and global executable are unavailable: dolgorae" in error
    assert "request $aquarium:dev-setup for dolgorae" in error


def test_missing_optional_sanho_does_not_request_dev_setup(
    tmp_path, monkeypatch, capsys
):
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    monkeypatch.setenv("PATH", str(tmp_path / "empty-global-bin"))

    assert launcher.main(["sanho", "--version"]) == 127
    error = capsys.readouterr().err
    assert "development and global executable are unavailable: sanho" in error
    assert "dev-setup" not in error


def test_launcher_install_is_separately_approved_and_user_local(tmp_path, monkeypatch):
    source = SCRIPT_DIR / "aquarium_dev_launcher.py"
    home = tmp_path / "home"
    target = home / ".local" / "bin" / "aquarium-dev"
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    monkeypatch.setattr(dev_manager, "require_supported_host", lambda: None)

    with pytest.raises(dev_manager.ManagerError) as failure:
        dev_manager.install_launcher(source, target, approve_launcher=False)
    assert failure.value.code == "approval_required"

    status, details = dev_manager.install_launcher(
        source, target, approve_launcher=True
    )
    assert status == "success"
    assert details == {"target": str(target)}
    assert target.read_bytes() == source.read_bytes()
    assert target.stat().st_mode & 0o777 == 0o755
