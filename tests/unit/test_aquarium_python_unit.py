"""Shared runtime installation primitives and isolated helper execution."""

import importlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import venv
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "plugins/aquarium/tools/aquarium-python"


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    source = tmp_path / "plugin/tools/aquarium-python"
    shutil.copytree(SOURCE, source, ignore=shutil.ignore_patterns("__pycache__"))
    spec = importlib.util.spec_from_file_location(
        "runtime_subject", source / "runtime.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source


@pytest.fixture
def offline(runtime, monkeypatch):
    module, source = runtime
    real_run = subprocess.run
    real_create = venv.EnvBuilder.create
    calls = []

    def create(builder, path):
        builder.with_pip = False
        return real_create(builder, path)

    def run(command, **kwargs):
        if command[1:4] == ["-I", "-m", "pip"]:
            calls.append(command)
            if command[4] == "install":
                assert "--require-hashes" in command
                assert "--only-binary=:all:" in command
                environment = Path(command[0]).parents[1]
                site = next((environment / "lib").glob("python*/site-packages"))
                for name in (
                    "yaml",
                    "jsonschema",
                    "attrs",
                    "attr",
                    "referencing",
                    "rpds",
                    "jsonschema_specifications",
                    "typing_extensions",
                ):
                    imported = importlib.import_module(name)
                    path = Path(imported.__file__)
                    if path.name == "__init__.py":
                        shutil.copytree(
                            path.parent,
                            site / name,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
                        )
                    else:
                        shutil.copyfile(path, site / path.name)
            return subprocess.CompletedProcess(command, 0)
        return real_run(command, **kwargs)

    monkeypatch.setattr(venv.EnvBuilder, "create", create)
    monkeypatch.setattr(subprocess, "run", run)
    return module, source, calls, real_run


def test_missing_inspection_is_read_only_and_install_requires_approval(runtime):
    module, source = runtime
    assert module.inspect(source)["status"] == "missing-prerequisite"
    assert not module.root().exists()
    with pytest.raises(module.RuntimeFailure, match="approve-install"):
        module.install(source)
    assert not module.root().exists()


def test_bootstrap_cli_needs_no_site_packages(runtime):
    module, source = runtime
    result = subprocess.run(
        [sys.executable, "-I", "-S", str(source / "runtime.py"), "inspect"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["status"] == "missing-prerequisite"
    assert payload["continuation"]["component"] == "aquarium-python"
    assert not module.root().exists()


def test_install_reuses_environment_across_plugin_updates(offline):
    module, source, calls, _ = offline
    first = module.install(source, approved=True)
    assert first["status"] == "current"
    (source / "unrelated-plugin-change.txt").write_text("new plugin version")
    assert module.install(source, approved=True)["interpreter"] == first["interpreter"]
    assert len(calls) == 2


def test_changed_lock_and_damaged_environment_get_new_selections(offline):
    module, source, _, _ = offline
    first = module.install(source, approved=True)
    library = next(
        (Path(first["environment"]) / "lib").glob(
            "python*/site-packages/yaml/__init__.py"
        )
    )
    library.write_text("raise RuntimeError('damaged')")
    assert module.inspect(source)["status"] == "missing-prerequisite"
    repaired = module.install(source, approved=True)
    assert repaired["interpreter"] != first["interpreter"]
    assert Path(first["environment"]).exists()
    lock = source / "requirements.txt"
    lock.write_text(lock.read_text() + "\n# another dependency lock\n")
    changed = module.install(source, approved=True)
    assert changed["interpreter"] != repaired["interpreter"]
    assert Path(repaired["environment"]).exists()


def test_failed_repair_preserves_previous_selection(offline, monkeypatch):
    module, source, _, _ = offline
    first = module.install(source, approved=True)
    selector = module.family(source) / "current"
    previous = selector.read_bytes()
    receipt = Path(first["environment"]) / "runtime.json"
    receipt.write_text("{}")

    def fail(*args, **kwargs):
        raise OSError("installation interrupted")

    monkeypatch.setattr(venv.EnvBuilder, "create", fail)
    with pytest.raises(OSError, match="interrupted"):
        module.install(source, approved=True)
    assert selector.read_bytes() == previous
    assert Path(first["environment"]).exists()
    assert len(list(module.family(source).glob("env-*"))) == 1


def test_run_preserves_process_contract_and_excludes_project_imports(offline, tmp_path):
    module, source, _, real_run = offline
    module.install(source, approved=True)
    helper = source.parents[1] / "shared/helper.py"
    helper.parent.mkdir()
    (helper.parent / "sibling.py").write_text("VALUE = 17\n")
    helper.write_text(
        "import json,sys,os,yaml,jsonschema,sibling\n"
        "print(json.dumps([os.getcwd(),sys.argv[1:],input(),sibling.VALUE]))\n"
        "print('diagnostic',file=sys.stderr)\nraise SystemExit(7)\n"
    )
    project = tmp_path / "non-python-project"
    project.mkdir()
    (project / "yaml.py").write_text("raise RuntimeError('project package')")
    env = dict(os.environ, PYTHONPATH=str(project), VIRTUAL_ENV=str(project / ".venv"))
    result = real_run(
        [
            sys.executable,
            "-I",
            str(source / "runtime.py"),
            "run",
            "shared/helper.py",
            "a b",
        ],
        cwd=project,
        env=env,
        input="stdin\n",
        text=True,
        capture_output=True,
    )
    assert result.returncode == 7, result.stderr
    assert json.loads(result.stdout) == [str(project), ["a b"], "stdin", 17]
    assert result.stderr == "diagnostic\n"
    assert sorted(p.name for p in project.iterdir()) == ["yaml.py"]


@pytest.mark.parametrize("path", ["../outside.py", "/tmp/helper.py"])
def test_run_rejects_paths_outside_plugin(runtime, path):
    module, source = runtime
    with pytest.raises(module.RuntimeFailure, match="relative"):
        module.run(path, [], source)


def test_linked_runtime_root_is_never_written(runtime, tmp_path):
    module, source = runtime
    external = tmp_path / "unowned"
    external.mkdir()
    module.root().parent.mkdir()
    module.root().symlink_to(external, target_is_directory=True)
    with pytest.raises(module.RuntimeFailure, match="Unsafe"):
        module.install(source, approved=True)
    assert list(external.iterdir()) == []


def test_simultaneous_installers_reuse_one_environment(offline):
    module, source, calls, _ = offline
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(lambda _: module.install(source, approved=True), range(2))
        )
    assert results[0]["interpreter"] == results[1]["interpreter"]
    assert len(calls) == 2
    assert len(list(module.family(source).glob("env-*"))) == 1


def test_changed_base_identity_requires_repair(offline):
    module, source, _, _ = offline
    installed = module.install(source, approved=True)
    path = Path(installed["environment"]) / "runtime.json"
    receipt = json.loads(path.read_text())
    receipt["base_sha256"] = "0" * 64
    path.write_text(json.dumps(receipt))
    assert module.inspect(source)["status"] == "missing-prerequisite"
    assert module.install(source, approved=True)["status"] == "current"


def test_helper_signal_is_not_converted_to_wrapper_success(offline):
    module, source, _, real_run = offline
    module.install(source, approved=True)
    helper = source.parents[1] / "stop_helper.py"
    helper.write_text("import os,signal; os.kill(os.getpid(),signal.SIGTERM)\n")
    result = real_run(
        [sys.executable, "-I", str(source / "runtime.py"), "run", "stop_helper.py"],
        capture_output=True,
    )
    assert result.returncode == -15


def test_run_without_environment_never_executes_or_creates_state(runtime):
    module, source = runtime
    marker = source.parents[1] / "helper-ran"
    helper = source.parents[1] / "helper.py"
    helper.write_text(f"from pathlib import Path; Path({str(marker)!r}).touch()\n")
    result = subprocess.run(
        [sys.executable, "-I", str(source / "runtime.py"), "run", "helper.py"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "missing-prerequisite"
    assert json.loads(result.stdout)["continuation"]["component"] == "aquarium-python"
    assert result.stderr == ""
    assert not marker.exists()
    assert not module.root().exists()


@pytest.mark.parametrize("phase", ["install", "check"])
def test_post_creation_pip_failure_removes_only_new_environment(
    offline, monkeypatch, phase
):
    module, source, _, _ = offline
    first = module.install(source, approved=True)
    selector = module.family(source) / "current"
    before = selector.read_bytes()
    (Path(first["environment"]) / "runtime.json").write_text("{}")
    previous_run = module.subprocess.run

    def fail(command, **kwargs):
        if command[1:4] == ["-I", "-m", "pip"] and command[4] == phase:
            assert Path(command[0]).exists()
            raise subprocess.CalledProcessError(1, command)
        return previous_run(command, **kwargs)

    monkeypatch.setattr(module.subprocess, "run", fail)
    with pytest.raises(subprocess.CalledProcessError):
        module.install(source, approved=True)
    assert selector.read_bytes() == before
    assert Path(first["environment"]).is_dir()
    assert list(module.family(source).glob("env-*")) == [Path(first["environment"])]


@pytest.mark.parametrize(
    "script", ["missing.py", "../outside.py", "/tmp/other.py", "runtime.txt"]
)
def test_invalid_helper_is_not_an_environment_repair(runtime, capsys, script):
    module, source = runtime
    (source.parents[1] / "runtime.txt").write_text("not Python")
    assert module.main(["run", script]) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "invalid-arguments"
    assert "continuation" not in result
    assert not module.root().exists()


def test_install_approval_and_subprocess_failure_have_no_repair_continuation(
    runtime, capsys, monkeypatch
):
    module, _ = runtime
    assert module.main(["install"]) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "approval-required"
    assert "continuation" not in result
    assert not module.root().exists()

    def fail(**kwargs):
        raise subprocess.CalledProcessError(1, ["pip", "install"])

    monkeypatch.setattr(module, "install", fail)
    assert module.main(["install", "--approve-install"]) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "install-failed"
    assert "continuation" not in result


def test_pip_configuration_is_disabled_without_changing_caller(offline, monkeypatch):
    module, source, _, _ = offline
    monkeypatch.setenv("PIP_CONFIG_FILE", "/unrelated/settings.ini")
    previous_run = module.subprocess.run
    seen = []

    def record(command, **kwargs):
        if command[1:4] == ["-I", "-m", "pip"]:
            assert "--isolated" in command
            seen.append(kwargs["env"])
        return previous_run(command, **kwargs)

    monkeypatch.setattr(module.subprocess, "run", record)
    module.install(source, approved=True)
    assert len(seen) == 2
    assert all(env["PIP_CONFIG_FILE"] == os.devnull for env in seen)
    assert all(env["PYTHONNOUSERSITE"] == "1" for env in seen)
    assert os.environ["PIP_CONFIG_FILE"] == "/unrelated/settings.ini"


def test_bad_bundled_requirements_are_not_an_environment_gap(runtime, capsys):
    module, source = runtime
    (source / "requirements.txt").unlink()
    result = module.inspect(source)
    assert result["status"] == "invalid-package"
    assert "continuation" not in result
    assert module.main(["install", "--approve-install"]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "invalid-package"
    assert not module.root().exists()


@pytest.mark.parametrize("version,free_threaded", [((3, 15), False), ((3, 13), True)])
def test_uncovered_creator_is_rejected_before_writes(
    runtime, monkeypatch, version, free_threaded
):
    module, source = runtime
    monkeypatch.setattr(module.sys, "version_info", version)
    monkeypatch.setattr(module.sysconfig, "get_config_var", lambda key: free_threaded)
    with pytest.raises(
        module.RuntimeFailure, match="matching host interpreter"
    ) as failure:
        module.install(source, approved=True)
    assert failure.value.status == "unsupported-runtime"
    assert not module.root().exists()


def test_healthy_environment_reused_from_newer_bootstrap(offline, monkeypatch):
    module, source, calls, _ = offline
    first = module.install(source, approved=True)
    monkeypatch.setattr(module.sys, "version_info", (3, 15))
    assert module.install(source, approved=True)["interpreter"] == first["interpreter"]
    assert len(calls) == 2


@pytest.mark.parametrize(
    "helper", ["manage_adaptive_procedure.py", "prepare_adaptive_procedure.py"]
)
def test_direct_opt_out_example_works_without_site_packages_or_managed_environment(
    tmp_path, monkeypatch, helper
):
    home = tmp_path / "empty-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    project = tmp_path / "non-python-project"
    project.mkdir()
    (project / "json.py").write_text("raise RuntimeError('untrusted project import')")
    monkeypatch.setenv("PYTHONPATH", str(project))
    script = ROOT / "plugins/aquarium/shared" / helper
    command = [sys.executable, "-E", "-s", "-B", "-S", str(script)]
    if helper.startswith("manage_"):
        command += [
            "inspect",
            "--repository",
            str(project),
            "--entrypoint",
            "new-feature",
            "--podway-opt-out",
        ]
    else:
        assignment = tmp_path / "assignment.json"
        assignment.write_text(
            json.dumps({"target": {"procedure_plan": {"entrypoint": "new-feature"}}})
        )
        command += [
            "--repository",
            str(project),
            "--assignment",
            str(assignment),
            "--podway-opt-out",
        ]
    result = subprocess.run(
        command, cwd=project, capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["status"] == "podway-inapplicable"
    assert not (home / ".aquarium").exists()


def test_install_validation_failure_does_not_route_back_to_setup(
    runtime, monkeypatch, capsys
):
    module, _ = runtime

    def fail(**kwargs):
        raise module.RuntimeFailure("post-install validation failed")

    monkeypatch.setattr(module, "install", fail)
    assert module.main(["install", "--approve-install"]) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "install-failed"
    assert "continuation" not in result
