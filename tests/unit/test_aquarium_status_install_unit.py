import importlib.metadata
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "plugins/aquarium/tools/aquarium-status"


def load_installer():
    spec = importlib.util.spec_from_file_location(
        "aquarium_status_install_test_subject", SOURCE / "install.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def runtime_install():
    return load_installer()


@pytest.fixture
def package(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    plugin = tmp_path / "plugin"
    source = plugin / "tools/aquarium-status"
    shutil.copytree(SOURCE, source, ignore=shutil.ignore_patterns("__pycache__"))
    (plugin / ".codex-plugin").mkdir()
    shutil.copyfile(
        ROOT / "plugins/aquarium/.codex-plugin/plugin.json",
        plugin / ".codex-plugin/plugin.json",
    )
    return source


@pytest.fixture
def offline_dependencies(runtime_install, monkeypatch):
    calls = []
    real_run = subprocess.run
    yaml_root = Path(yaml.__file__).resolve().parent
    distribution_root = Path(importlib.metadata.distribution("PyYAML")._path)

    def run(command, **kwargs):
        if len(command) >= 4 and command[1:4] == ["-I", "-m", "pip"]:
            calls.append((list(command), dict(kwargs)))
            target = Path(command[command.index("--target") + 1])
            shutil.copytree(
                yaml_root,
                target / "yaml",
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
            shutil.copytree(
                distribution_root,
                target / distribution_root.name,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
            return subprocess.CompletedProcess(command, 0)
        return real_run(command, **kwargs)

    monkeypatch.setattr(runtime_install.subprocess, "run", run)
    return calls


@pytest.fixture(autouse=True)
def supported_host(runtime_install, monkeypatch):
    monkeypatch.setattr(runtime_install.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(runtime_install.platform, "machine", lambda: "arm64")


def install(runtime_install, package):
    return runtime_install.install(package, approve_install=True, approve_launcher=True)


def selected(runtime_install):
    root = runtime_install.runtime_root()
    relative = (root / "current").read_text(encoding="utf-8").strip()
    generation = root / relative
    receipt = json.loads((generation / "runtime.json").read_text(encoding="utf-8"))
    return generation, receipt


@pytest.mark.parametrize(
    "approve_install,approve_launcher", [(False, False), (True, False), (False, True)]
)
def test_install_requires_both_explicit_approvals(
    runtime_install,
    package,
    offline_dependencies,
    approve_install,
    approve_launcher,
):
    with pytest.raises(runtime_install.RuntimeFailure):
        runtime_install.install(package, approve_install, approve_launcher)

    assert offline_dependencies == []
    assert not runtime_install.runtime_root().exists()
    assert not runtime_install.launcher_path().exists()


def test_install_uses_hash_pinned_isolated_pip_and_private_dependencies(
    runtime_install, package, offline_dependencies, tmp_path, monkeypatch
):
    monkeypatch.setenv("PIP_INDEX_URL", "https://untrusted.invalid/simple")
    monkeypatch.setenv("PIP_EXTRA_INDEX_URL", "https://also-untrusted.invalid/simple")
    monkeypatch.setenv("PIP_CACHE_DIR", str(tmp_path / "ambient-pip-cache"))
    monkeypatch.setenv("PYTHONPATH", str(tmp_path / "ambient-python"))

    result = install(runtime_install, package)

    assert result["status"] == "current"
    assert len(offline_dependencies) == 1
    command, options = offline_dependencies[0]
    generation, receipt = selected(runtime_install)
    dependency_target = Path(command[command.index("--target") + 1])
    assert dependency_target.name == "dependencies"
    assert dependency_target.parent.name.startswith(".generation.")
    assert dependency_target.parent.parent == generation.parent
    assert command == [
        receipt["python_executable"],
        "-I",
        "-m",
        "pip",
        "install",
        "--isolated",
        "--index-url",
        "https://pypi.org/simple",
        "--no-cache-dir",
        "--disable-pip-version-check",
        "--no-deps",
        "--no-compile",
        "--require-hashes",
        "--only-binary=:all:",
        "--target",
        str(dependency_target),
        "-r",
        str(package / "requirements.txt"),
    ]
    assert options["check"] is True
    assert options["env"] == {
        "PATH": os.environ.get("PATH", ""),
        "PIP_CONFIG_FILE": os.devnull,
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    requirements = (package / "requirements.txt").read_text(encoding="utf-8")
    assert requirements.startswith("PyYAML==6.0.3 \\\n")
    assert requirements.count("--hash=sha256:") == 5
    assert receipt["dependency_files"]
    assert all(name.startswith("dependencies/") for name in receipt["dependency_files"])


def test_install_rejects_unknown_launcher_without_changing_it(
    runtime_install, package, offline_dependencies
):
    launcher = runtime_install.launcher_path()
    launcher.parent.mkdir(parents=True)
    original = b"#!/bin/sh\necho foreign launcher\n"
    launcher.write_bytes(original)
    launcher.chmod(0o755)

    with pytest.raises(runtime_install.RuntimeFailure):
        install(runtime_install, package)

    assert launcher.read_bytes() == original
    assert offline_dependencies == []
    assert not runtime_install.runtime_root().exists()


def test_failed_activation_restores_selector_and_launcher(
    runtime_install, package, offline_dependencies, monkeypatch
):
    install(runtime_install, package)
    root = runtime_install.runtime_root()
    current = root / "current"
    launcher = runtime_install.launcher_path()
    original_current = current.read_bytes()
    original_launcher = launcher.read_bytes()
    with (package / "aquarium_status.py").open("a", encoding="utf-8") as stream:
        stream.write("\n# New bundled generation.\n")

    atomic_file = runtime_install.atomic_file
    interrupted = False

    def fail_once(path, content, mode):
        nonlocal interrupted
        if path == launcher and not interrupted:
            interrupted = True
            raise OSError("activation interrupted")
        return atomic_file(path, content, mode)

    monkeypatch.setattr(runtime_install, "atomic_file", fail_once)
    with pytest.raises(OSError, match="activation interrupted"):
        install(runtime_install, package)

    assert interrupted
    assert current.read_bytes() == original_current
    assert launcher.read_bytes() == original_launcher
    assert len(offline_dependencies) == 2


@pytest.mark.parametrize(
    "damage", ["missing_payload", "modified_payload", "interpreter"]
)
def test_diagnose_reports_managed_content_damage_without_repairing_it(
    runtime_install,
    package,
    offline_dependencies,
    tmp_path,
    monkeypatch,
    damage,
):
    if damage == "interpreter":
        private_python = tmp_path / "installed-python"
        shutil.copy2(Path(sys.executable).resolve(), private_python)
        monkeypatch.setattr(
            runtime_install,
            "sys",
            SimpleNamespace(
                executable=str(private_python), version_info=sys.version_info
            ),
        )

    install(runtime_install, package)
    assert runtime_install.diagnose(package)["status"] == "current"
    generation, receipt = selected(runtime_install)
    if damage == "missing_payload":
        damaged = generation / "aquarium_status.py"
        damaged.unlink()
        expected = None
    elif damage == "modified_payload":
        damaged = generation / "aquarium_status.py"
        damaged.write_bytes(damaged.read_bytes() + b"\n# damaged\n")
        expected = damaged.read_bytes()
    else:
        damaged = Path(receipt["python_executable"])
        damaged.write_bytes(damaged.read_bytes() + b"\x00")
        expected = damaged.read_bytes()

    result = runtime_install.diagnose(package)

    assert result["status"] == "broken"
    assert result["action"] == "repair"
    assert result["launcher"]["state"] == "managed_outdated"
    if expected is None:
        assert not damaged.exists()
    else:
        assert damaged.read_bytes() == expected
    assert len(offline_dependencies) == 1


@pytest.mark.parametrize("damage", ["nested_dependency_symlink", "selector_symlink"])
def test_diagnose_reports_unsafe_paths_without_mutating_them(
    runtime_install,
    package,
    offline_dependencies,
    tmp_path,
    damage,
):
    install(runtime_install, package)
    generation, _ = selected(runtime_install)
    if damage == "nested_dependency_symlink":
        unsafe = generation / "dependencies/yaml/__init__.py"
        target = tmp_path / "dependency-target"
    else:
        unsafe = runtime_install.runtime_root() / "current"
        target = tmp_path / "selector-target"
    original = unsafe.read_bytes()
    target.write_bytes(original)
    unsafe.unlink()
    unsafe.symlink_to(target)

    result = runtime_install.diagnose(package)

    assert result["status"] == "unsafe"
    assert result["action"] is None
    assert unsafe.is_symlink()
    assert unsafe.read_bytes() == original
    assert target.read_bytes() == original
    assert len(offline_dependencies) == 1


def test_diagnose_reports_split_managed_activation_as_repairable(
    runtime_install, package, offline_dependencies
):
    install(runtime_install, package)
    generation, _ = selected(runtime_install)
    split_generation = generation.with_name(f"{generation.name}-r{'a' * 32}")
    shutil.copytree(generation, split_generation)
    current = runtime_install.runtime_root() / "current"
    current.write_text(
        f"versions/{split_generation.name}\n",
        encoding="utf-8",
    )
    launcher = runtime_install.launcher_path()
    original_launcher = launcher.read_bytes()

    result = runtime_install.diagnose(package)

    assert result["status"] == "broken"
    assert result["action"] == "repair"
    assert result["launcher"]["state"] == "managed_outdated"
    assert current.read_text(encoding="utf-8") == f"versions/{split_generation.name}\n"
    assert launcher.read_bytes() == original_launcher
    assert len(offline_dependencies) == 1


def test_installed_launcher_is_isolated_and_survives_plugin_removal(
    runtime_install, package, offline_dependencies, tmp_path, monkeypatch
):
    install(runtime_install, package)
    _, receipt = selected(runtime_install)
    ambient = tmp_path / "ambient"
    ambient.mkdir()
    marker = tmp_path / "ambient-yaml-imported"
    (ambient / "yaml.py").write_text(
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).touch()\n"
        "raise RuntimeError('ambient yaml imported')\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PYTHONPATH", str(ambient))
    monkeypatch.setenv("PYTHONHOME", str(tmp_path / "missing-python-home"))
    shutil.rmtree(package.parents[1])

    process = subprocess.run(
        [str(runtime_install.launcher_path()), "show", "--format", "json"],
        capture_output=True,
        check=False,
        text=True,
    )

    assert process.returncode == 0, process.stderr
    report = json.loads(process.stdout)
    assert report["schema"] == "aquarium-production-status-report/v1"
    assert report["reporter"] == {
        "value": receipt["plugin_version"],
        "source": "installed_runtime_receipt",
        "status": "observed",
    }
    assert report["ledger"]["state"] == "absent"
    assert not marker.exists()
    assert len(offline_dependencies) == 1
