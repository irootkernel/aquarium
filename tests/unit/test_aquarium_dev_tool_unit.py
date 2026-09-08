import json
import os
import shutil
import subprocess
import sys
import sysconfig
import venv
from pathlib import Path

import anyio
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "plugins/aquarium/tools/aquarium-dev"
sys.path.insert(0, str(SOURCE))

import aquarium_dev
import dev_manager
import install as runtime_install
import mcp_server
import runtime_entry
from dev_contract import ContractError
from test_aquarium_dev_enrollment_unit import create_repository


@pytest.fixture
def package(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    plugin = tmp_path / "plugin"
    source = plugin / "tools/aquarium-dev"
    shutil.copytree(SOURCE, source, ignore=shutil.ignore_patterns("__pycache__"))
    (plugin / ".codex-plugin").mkdir()
    shutil.copyfile(
        ROOT / "plugins/aquarium/.codex-plugin/plugin.json",
        plugin / ".codex-plugin/plugin.json",
    )
    shutil.copyfile(ROOT / "plugins/aquarium/.mcp.json", plugin / ".mcp.json")
    return source


@pytest.fixture
def dependencies(monkeypatch):
    """Use the test environment's pinned SDK without downloading in the test suite."""
    prepared = []

    def prepare(generation):
        prepared.append(generation)
        venv.EnvBuilder(with_pip=False).create(generation / "venv")
        site_packages = next((generation / "venv/lib").glob("python*/site-packages"))
        (site_packages / "test-sdk.pth").write_text(
            sysconfig.get_path("purelib") + "\n"
        )

    monkeypatch.setattr(runtime_install, "install_dependencies", prepare)
    return prepared


def install(package):
    return runtime_install.install(package, approve_install=True, approve_launcher=True)


def cli(*args):
    return subprocess.run(
        [str(Path.home() / ".local/bin/aquarium-dev"), *map(str, args)],
        capture_output=True,
        check=False,
        text=True,
    )


def test_missing_runtime_diagnosis_and_plugin_start_do_not_install(package):
    assert runtime_install.diagnose(package)["status"] == "missing"
    process = subprocess.run(
        [str(package / "mcp-launcher")], capture_output=True, text=True, check=False
    )
    assert process.returncode == 1
    assert json.loads(process.stderr)["error"]["code"] == "runtime_unavailable"
    assert not runtime_entry.manager_root().parent.exists()


@pytest.mark.parametrize(
    "runtime,launcher", [(False, False), (True, False), (False, True)]
)
def test_install_requires_both_approvals(package, dependencies, runtime, launcher):
    with pytest.raises(runtime_entry.RuntimeUnavailable):
        runtime_install.install(
            package, approve_install=runtime, approve_launcher=launcher
        )
    assert dependencies == []
    assert not runtime_entry.manager_root().exists()


def test_install_is_idempotent_and_cli_uses_installed_runtime(package, dependencies):
    assert install(package)["status"] == "success"
    generation, receipt = runtime_entry.selected_runtime()
    assert install(package)["status"] == "no-change"
    assert dependencies == [generation]
    process = cli("version")
    assert process.returncode == 0, process.stderr
    assert json.loads(process.stdout) == receipt
    assert runtime_install.diagnose(package)["launcher_current"]
    assert not (Path.home() / ".codex").exists()
    assert not (Path.home() / ".aquarium").exists()


@pytest.mark.parametrize(
    "damage", ["missing_receipt", "invalid_receipt", "source", "environment"]
)
def test_install_recovers_without_replacing_damaged_generation(
    package, dependencies, damage
):
    install(package)
    previous, _ = runtime_entry.selected_runtime()
    if damage == "missing_receipt":
        (previous / "runtime.json").unlink()
    elif damage == "invalid_receipt":
        (previous / "runtime.json").write_text("{")
    elif damage == "source":
        (previous / "aquarium_dev.py").write_text("damaged")
    else:
        (previous / "venv/pyvenv.cfg").unlink()
    retained = {
        path: path.read_bytes() for path in previous.glob("*") if path.is_file()
    }
    assert install(package)["status"] == "success"
    recovered, receipt = runtime_entry.selected_runtime()
    assert recovered != previous
    assert previous.is_dir()
    assert {
        path: path.read_bytes() for path in previous.glob("*") if path.is_file()
    } == retained
    assert json.loads(cli("version").stdout) == receipt
    assert install(package)["status"] == "no-change"
    assert dependencies == [previous, recovered]


@pytest.mark.parametrize("linked_path", ["venv", "venv/pyvenv.cfg", "venv/bin"])
def test_install_recovers_from_symbolic_environment(
    package, dependencies, tmp_path, linked_path
):
    install(package)
    previous, receipt = runtime_entry.selected_runtime()
    path = previous / linked_path
    saved = tmp_path / "saved-environment"
    path.rename(saved)
    path.symlink_to(saved, target_is_directory=saved.is_dir())
    assert runtime_install.diagnose(package)["status"] == "broken"
    assert install(package)["status"] == "success"
    recovered, recovered_receipt = runtime_entry.selected_runtime()
    assert recovered != previous
    assert recovered_receipt == receipt
    assert path.is_symlink()
    assert saved.exists()
    assert dependencies == [previous, recovered]
    assert runtime_install.diagnose(package)["status"] == "current"
    assert cli("version").returncode == 0


def test_public_cli_ignores_ambient_python_settings(
    package, dependencies, tmp_path, monkeypatch
):
    install(package)
    _, receipt = runtime_entry.selected_runtime()
    (tmp_path / "json.py").write_text("raise RuntimeError('ambient module imported')\n")
    monkeypatch.setenv("PYTHONHOME", str(tmp_path / "missing-python-home"))
    monkeypatch.setenv("PYTHONPATH", str(tmp_path))
    process = cli("version")
    assert process.returncode == 0, process.stderr
    assert json.loads(process.stdout) == receipt


def test_install_recovers_from_unselected_partial_install(package, dependencies):
    identity = runtime_entry.bundled_identity(package)
    partial = (
        runtime_entry.manager_root()
        / "versions"
        / (
            f"{identity['source_sha256']}-py{sys.version_info.major}.{sys.version_info.minor}"
        )
    )
    partial.mkdir(parents=True)
    (partial / "incomplete").write_text("preserve")
    assert install(package)["status"] == "success"
    assert runtime_entry.selected_runtime()[0] != partial
    assert (partial / "incomplete").read_text() == "preserve"


def test_failed_recovery_keeps_existing_selector_and_allows_retry(
    package, dependencies, monkeypatch
):
    install(package)
    previous, _ = runtime_entry.selected_runtime()
    (previous / "runtime.json").write_text("{")
    root = runtime_entry.manager_root()
    target = os.readlink(root / "current")
    launcher = Path.home() / ".local/bin/aquarium-dev"
    original = launcher.read_bytes()
    with monkeypatch.context() as patch:

        def fail(_):
            raise OSError("installation interrupted")

        patch.setattr(runtime_install, "install_dependencies", fail)
        with pytest.raises(OSError):
            install(package)
    assert os.readlink(root / "current") == target
    assert launcher.read_bytes() == original
    assert list((root / "versions").iterdir()) == [previous]
    assert (previous / "runtime.json").read_text() == "{"
    assert install(package)["status"] == "success"
    assert runtime_entry.selected_runtime()[0] != previous


@pytest.mark.parametrize("failure", ["mkdir", "cleanup"])
def test_failed_install_preserves_original_error(package, monkeypatch, capsys, failure):
    original = OSError("original installation failure")
    mkdir = Path.mkdir
    unlink = os.unlink
    versions = runtime_entry.manager_root() / "versions"

    def fail_mkdir(path, *args, **kwargs):
        if path.parent == versions:
            raise original
        return mkdir(path, *args, **kwargs)

    def fail_install(_):
        raise original

    def fail_unlink(path, *args, **kwargs):
        if kwargs.get("dir_fd") is not None:
            raise PermissionError("cleanup denied")
        return unlink(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        if failure == "mkdir":
            patch.setattr(Path, "mkdir", fail_mkdir)
        else:
            patch.setattr(runtime_install, "install_dependencies", fail_install)
            patch.setattr(os, "unlink", fail_unlink)
        patch.setattr(runtime_install, "__file__", str(package / "install.py"))
        patch.setattr(
            sys,
            "argv",
            ["install.py", "install", "--approve-install", "--approve-launcher"],
        )
        assert runtime_install.main() == 1
    error = json.loads(capsys.readouterr().err)["error"]
    assert error["code"] == "runtime_install_failed"
    assert error["message"] == str(original)
    assert not (runtime_entry.manager_root() / "current").is_symlink()
    assert not (Path.home() / ".local/bin/aquarium-dev").exists()


@pytest.mark.parametrize(
    "stderr", [b"missing test dependency", b"x" * 5000 + b"\xffcause", b""]
)
def test_runtime_diagnosis_retains_environment_failure(package, dependencies, stderr):
    install(package)
    generation, _ = runtime_entry.selected_runtime()
    python = generation / "venv/bin/python"
    python.unlink()
    python.write_text(
        f"#!{sys.executable}\nimport os\nos.write(2, {stderr!r})\nraise SystemExit(17)\n"
    )
    python.chmod(0o755)
    result = runtime_install.diagnose(package)
    assert result["status"] == "broken"
    assert result["action"]
    assert "17" in result["problem"]
    if stderr:
        assert stderr[-4096:].decode("utf-8", errors="replace") in result["problem"]
    assert len(result["problem"]) < 4300


@pytest.mark.parametrize("parent", [".local", ".local/bin"])
def test_launcher_installers_allow_symbolic_parents(
    package, dependencies, tmp_path, parent
):
    destination = tmp_path / "launcher-directory"
    destination.mkdir()
    linked = Path.home() / parent
    linked.parent.mkdir(parents=True, exist_ok=True)
    linked.symlink_to(destination, target_is_directory=True)
    assert install(package)["status"] == "success"
    target = Path.home() / ".local/bin/aquarium-dev"
    assert not target.is_symlink()
    assert runtime_install.diagnose(package)["launcher_current"]
    target.unlink()
    status, _ = dev_manager.install_launcher(
        package / "runtime_entry.py", target, approve_launcher=True
    )
    assert status == "success"
    assert runtime_install.diagnose(package)["launcher_current"]
    assert cli("version").returncode == 0


@pytest.mark.parametrize("dangling", [False, True])
def test_launcher_installers_reject_symbolic_target(package, tmp_path, dangling):
    target = Path.home() / ".local/bin/aquarium-dev"
    target.parent.mkdir(parents=True)
    foreign = tmp_path / "foreign-launcher"
    if not dangling:
        foreign.write_text("foreign launcher")
    target.symlink_to(foreign)
    with pytest.raises(runtime_entry.RuntimeUnavailable):
        install(package)
    with pytest.raises(dev_manager.ManagerError) as rejected:
        dev_manager.install_launcher(
            package / "runtime_entry.py", target, approve_launcher=True
        )
    assert rejected.value.code == "artifact_invalid"
    assert target.is_symlink()
    assert foreign.exists() is not dangling
    if not dangling:
        assert foreign.read_text() == "foreign launcher"


def test_installer_preserves_manager_error_message(package, monkeypatch, capsys):
    error = dev_manager.ManagerError(
        "unsupported_host",
        "Unsupported test host.",
        "Use a supported host.",
        "diagnose",
    )

    def reject():
        raise error

    monkeypatch.setattr(runtime_install, "require_supported_host", reject)
    monkeypatch.setattr(runtime_install, "__file__", str(package / "install.py"))
    monkeypatch.setattr(
        sys,
        "argv",
        ["install.py", "install", "--approve-install", "--approve-launcher"],
    )
    assert runtime_install.main() == 1
    assert json.loads(capsys.readouterr().err)["error"]["message"] == error.message


@pytest.mark.parametrize("operation", ["worker", "cleanup"])
def test_spawned_runtime_ignores_ambient_python_environment(
    tmp_path, monkeypatch, operation
):
    repository = create_repository(tmp_path / "repository")
    host = tmp_path / "host"
    probe = tmp_path / "aquarium_dev.py"
    observed = tmp_path / "observed.json"
    probe.write_text(
        "import json, sys\nfrom pathlib import Path\n"
        f"Path({str(observed)!r}).write_text(json.dumps([sys.flags.ignore_environment, sys.flags.no_user_site, sys.dont_write_bytecode]))\n"
    )
    dev_manager.enroll(
        repository,
        host,
        probe,
        approve_enrollment=True,
        approve_hook=True,
        approve_reenrollment=False,
    )
    monkeypatch.setenv("PYTHONHOME", str(tmp_path / "missing-python"))
    monkeypatch.setenv("PYTHONPATH", str(tmp_path / "ambient"))
    original_popen = subprocess.Popen
    children = []

    def start(command, **kwargs):
        child = original_popen(command, **kwargs)
        if operation in command:
            children.append(child)
        return child

    monkeypatch.setattr(subprocess, "Popen", start)
    if operation == "worker":
        dev_manager.queue_request(repository, host, probe)
    else:
        monkeypatch.setattr(dev_manager, "__file__", str(tmp_path / "dev_manager.py"))
        dev_manager._spawn_cleanup(host, "aquarium", "a" * 40)
    assert len(children) == 1
    assert children[0].wait(timeout=10) == 0
    assert json.loads(observed.read_text()) == [1, 1, True]


@pytest.mark.parametrize("failure", ["dependencies", "selection"])
def test_failed_update_keeps_selected_runtime_and_launcher(
    package, dependencies, monkeypatch, failure
):
    install(package)
    generation, receipt = runtime_entry.selected_runtime()
    launcher = Path.home() / ".local/bin/aquarium-dev"
    original = launcher.read_bytes()
    with (package / "aquarium_dev.py").open("a") as stream:
        stream.write("\n# New package revision.\n")
    if failure == "dependencies":

        def fail(_):
            raise OSError("dependency installation failed")

        monkeypatch.setattr(runtime_install, "install_dependencies", fail)
    else:
        select = runtime_install.select_generation

        def fail(root, target):
            select(root, target)
            if target != f"versions/{generation.name}":
                raise OSError("selection interrupted")

        monkeypatch.setattr(runtime_install, "select_generation", fail)
    with pytest.raises(OSError):
        install(package)
    assert runtime_entry.selected_runtime() == (generation, receipt)
    assert launcher.read_bytes() == original
    assert list((runtime_entry.manager_root() / "versions").iterdir()) == [generation]


def test_legacy_hook_migrates_once_and_survives_runtime_update(
    package, dependencies, tmp_path
):
    repository = create_repository(tmp_path / "repository")
    legacy = subprocess.run(
        [
            sys.executable,
            str(package / "aquarium_dev.py"),
            "enroll",
            "--repository",
            str(repository),
            "--approve-enrollment",
            "--approve-hook",
        ],
        capture_output=True,
        check=False,
        text=True,
    )
    assert legacy.returncode == 0, legacy.stderr
    install(package)
    assert (
        json.loads(cli("diagnose", "--repository", repository).stdout)["details"][
            "hook"
        ]
        == "outdated"
    )
    refused = cli(
        "enroll", "--repository", repository, "--approve-enrollment", "--approve-hook"
    )
    assert refused.returncode != 0
    migrated = cli(
        "enroll",
        "--repository",
        repository,
        "--approve-enrollment",
        "--approve-hook",
        "--approve-reenrollment",
    )
    assert migrated.returncode == 0, migrated.stderr
    hook = repository / ".git/hooks/post-commit"
    original = hook.read_bytes()
    previous, previous_receipt = runtime_entry.selected_runtime()
    with (package / "aquarium_dev.py").open("a") as stream:
        stream.write("\n# New package revision.\n")
    assert runtime_install.diagnose(package)["status"] == "outdated"
    assert runtime_entry.selected_runtime()[0] == previous
    install(package)
    assert previous.is_dir()
    assert runtime_entry.selected_runtime()[0] != previous
    old_runtime = subprocess.run(
        [
            str(previous / "venv/bin/python"),
            str(previous / "aquarium_dev.py"),
            "version",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(old_runtime.stdout) == previous_receipt
    assert hook.read_bytes() == original
    assert (
        json.loads(cli("diagnose", "--repository", repository).stdout)["details"][
            "hook"
        ]
        == "owned"
    )


def test_plugin_rejects_runtime_version_mismatch_without_updating(
    package, dependencies
):
    install(package)
    previous = runtime_entry.selected_runtime()
    with (package / "aquarium_dev.py").open("a") as stream:
        stream.write("\n# New package revision.\n")
    process = subprocess.run(
        [str(package / "mcp-launcher")], capture_output=True, text=True, check=False
    )
    assert process.returncode == 1
    assert json.loads(process.stderr)["error"]["code"] == "runtime_unavailable"
    assert runtime_entry.selected_runtime() == previous
    assert cli("version").returncode == 0


@pytest.mark.parametrize("escape", ["selector", "source", "launcher"])
def test_runtime_rejects_symbolic_escapes(package, dependencies, tmp_path, escape):
    install(package)
    if escape == "selector":
        selector = runtime_entry.manager_root() / "current"
        selector.unlink()
        selector.symlink_to(tmp_path)
        with pytest.raises(runtime_entry.RuntimeUnavailable):
            runtime_entry.selected_runtime()
    elif escape == "source":
        code = package / "aquarium_dev.py"
        code.unlink()
        code.symlink_to(SOURCE / "aquarium_dev.py")
        with pytest.raises(runtime_entry.RuntimeUnavailable):
            install(package)
    else:
        launcher = Path.home() / ".local/bin/aquarium-dev"
        launcher.unlink()
        foreign = tmp_path / "foreign"
        foreign.write_text("foreign")
        launcher.symlink_to(foreign)
        with pytest.raises(runtime_entry.RuntimeUnavailable):
            install(package)
        assert foreign.read_text() == "foreign"


@pytest.mark.parametrize(
    "name,arguments",
    [
        ("aquarium_dev_worker", {}),
        ("aquarium_dev_cleanup", {}),
        ("aquarium_dev_rebuild", {"repository": "/repo", "approve_build": "true"}),
        ("aquarium_dev_rebuild", {"repository": "/repo", "host_root": "/other"}),
        ("aquarium_dev_diagnose", {"repository": "relative"}),
    ],
)
def test_mcp_rejects_invalid_inputs_before_dispatch(monkeypatch, name, arguments):
    def forbidden(_):
        pytest.fail("invalid input reached the manager")

    monkeypatch.setattr(mcp_server, "invoke", forbidden)
    result = anyio.run(mcp_server.call, name, arguments)
    assert result.is_error
    assert result.structured_content["error"]["code"] == "invalid_arguments"


@pytest.mark.parametrize(
    "error", [ContractError("invalid result"), OSError("storage unavailable")]
)
def test_cli_and_mcp_preserve_internal_error_classification(monkeypatch, capsys, error):
    def fail(_):
        raise error

    monkeypatch.setattr(aquarium_dev, "execute", fail)
    argv = ["diagnose", "--repository", "/repo"]
    assert aquarium_dev.main(argv) == 1
    output = capsys.readouterr()
    assert not output.out
    expected = json.loads(output.err)
    assert expected["error"]["code"] == "internal_error"
    result = anyio.run(
        mcp_server.call, "aquarium_dev_diagnose", {"repository": "/repo"}
    )
    assert result.is_error
    assert result.structured_content == expected
    assert json.loads(result.content[0].text) == expected


@pytest.mark.parametrize("signal", [KeyboardInterrupt, SystemExit])
def test_dispatcher_does_not_convert_process_exit_signals(monkeypatch, signal):
    def stop(_):
        raise signal()

    monkeypatch.setattr(aquarium_dev, "execute", stop)
    with pytest.raises(signal):
        aquarium_dev.invoke(["diagnose", "--repository", "/repo"])


def test_mcp_and_cli_share_structured_success_and_error_results(package, tmp_path):
    repository = create_repository(tmp_path / "repository")
    for operation, arguments, argv in (
        (
            "diagnose",
            {"repository": str(repository)},
            ["diagnose", "--repository", str(repository)],
        ),
        (
            "rebuild",
            {"repository": str(repository)},
            ["rebuild", "--repository", str(repository)],
        ),
    ):
        expected, exit_code = aquarium_dev.invoke(argv)
        result = anyio.run(mcp_server.call, f"aquarium_dev_{operation}", arguments)
        assert result.structured_content == expected
        assert json.loads(result.content[0].text) == expected
        assert result.is_error == bool(exit_code)
    assert not runtime_entry.manager_root().parent.exists()


@pytest.mark.parametrize("ambient_python", [False, True])
def test_installed_plugin_exposes_and_calls_tools_over_stdio(
    package, dependencies, tmp_path, monkeypatch, ambient_python
):
    install(package)
    repository = create_repository(tmp_path / "repository")
    plugin = package.parent.parent
    config = json.loads((plugin / ".mcp.json").read_text())["mcp_servers"][
        "aquarium-dev"
    ]
    if ambient_python:
        (tmp_path / "json.py").write_text(
            "raise RuntimeError('ambient module imported')\n"
        )
        monkeypatch.setenv("PYTHONHOME", str(tmp_path / "missing-python-home"))
        monkeypatch.setenv("PYTHONPATH", str(tmp_path))

    async def exercise():
        parameters = StdioServerParameters(
            command=str(plugin / config["command"]),
            args=config["args"],
            cwd=plugin,
            env=dict(os.environ),
        )
        async with (
            stdio_client(parameters) as (reader, writer),
            ClientSession(reader, writer) as session,
        ):
            identity = await session.initialize()
            assert identity.server_info.name == "aquarium-dev"
            tools = (await session.list_tools()).tools
            assert {tool.name for tool in tools} == {
                f"aquarium_dev_{operation}" for operation in mcp_server.OPERATIONS
            }
            result = await session.call_tool(
                "aquarium_dev_diagnose", {"repository": str(repository)}
            )
            assert not result.is_error
            assert result.structured_content["details"]["enrollment"] == "absent"
            refused = await session.call_tool(
                "aquarium_dev_rebuild", {"repository": str(repository)}
            )
            assert refused.is_error
            assert refused.structured_content["error"]["code"] == "approval_required"

    anyio.run(exercise)
    assert not (repository / ".git/hooks/post-commit").exists()
