import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "plugins/aquarium/skills/aquarium-dev/scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import aquarium_dev_launcher as launcher
import dev_manager

CONTROLLER = r"""#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("operation", choices=("status", "plan", "apply"))
parser.add_argument("--json", action="store_true")
parser.add_argument("--runtime-root", type=Path, required=True)
parser.add_argument("--generation-root", type=Path)
parser.add_argument("--plan-token")
args = parser.parse_args()
project_id = "gaori"
active_path = args.runtime_root / "active"
active = active_path.read_text(encoding="utf-8").strip() if active_path.exists() else None
busy = (args.runtime_root / "busy").exists()

if args.operation == "status":
    state = "absent" if active is None else ("busy" if busy else "ready")
    result = {
        "schema": "aquarium-dev-service-status/v1",
        "project_id": project_id,
        "state": state,
        "active_git_sha": active,
        "busy": busy,
        "recovery_required": False,
    }
else:
    target = args.generation_root.name
    if busy and active != target:
        action = "defer"
    elif active is None:
        action = "install"
    elif active == target:
        action = "no-change"
    else:
        action = "activate"
    token = None
    if action != "defer":
        token = "sha256:" + hashlib.sha256(
            f"{action}:{active}:{target}".encode("utf-8")
        ).hexdigest()
    if args.operation == "plan":
        result = {
            "schema": "aquarium-dev-service-plan/v1",
            "project_id": project_id,
            "target_git_sha": target,
            "action": action,
            "active_git_sha": active,
            "busy": busy,
            "plan_token": token,
        }
    else:
        if args.plan_token != token or action == "defer":
            raise SystemExit(2)
        if (args.runtime_root / "fail-apply").exists():
            raise SystemExit(3)
        args.runtime_root.mkdir(parents=True, exist_ok=True)
        active_path.write_text(target, encoding="utf-8")
        result = {
            "schema": "aquarium-dev-service-result/v1",
            "project_id": project_id,
            "status": "activated" if action != "no-change" else "no-change",
            "active_git_sha": target,
            "recovery_required": False,
        }
print(json.dumps(result, sort_keys=True))
"""


@pytest.fixture(autouse=True)
def clear_managed_immutable_flags(tmp_path):
    yield
    for current, directories, files in os.walk(tmp_path):
        os.chflags(current, 0)
        for name in (*directories, *files):
            target = Path(current) / name
            if not target.is_symlink():
                os.chflags(target, 0)


def managed_staging(root: Path, git_sha: str) -> tuple[Path, dict[str, str]]:
    staging = root / f"staging-{git_sha[:8]}"
    bundle = staging / "bundle"
    command = bundle / "bin/gaori"
    controller = bundle / "libexec/aquarium-dev-service"
    command.parent.mkdir(parents=True)
    controller.parent.mkdir(parents=True)
    command.write_text("#!/bin/sh\nprintf 'managed gaori\\n'\n", encoding="utf-8")
    controller.write_text(CONTROLLER, encoding="utf-8")
    command.chmod(0o755)
    controller.chmod(0o755)
    manifest = {
        "schema": "aquarium-dev-artifact-manifest/v2",
        "project_id": "gaori",
        "git_sha": git_sha,
        "development_version": f"v0.2.0-dev.{git_sha[:12]}",
        "artifact_kind": "managed-service",
        "artifact_path": "bundle",
        "command_path": "bin/gaori",
        "controller_path": "libexec/aquarium-dev-service",
        "sha256": dev_manager.artifact_digest(bundle),
    }
    (staging / ".aquarium-manifest.json").write_text(
        json.dumps(manifest) + "\n", encoding="utf-8"
    )
    return staging, manifest


def test_generic_managed_service_requires_plan_and_approved_apply(tmp_path):
    host_root = tmp_path / "host"
    (host_root / "artifacts/gaori").mkdir(parents=True)
    git_sha = "1" * 40
    staging, manifest = managed_staging(tmp_path, git_sha)

    status, published = dev_manager._publish(host_root, staging, manifest)

    assert status == "success"
    assert published["pending"] == str(host_root / "pending/gaori")
    assert not (host_root / "current/gaori").exists()
    assert not (host_root / "bin/gaori").exists()
    plan_status, details = dev_manager.plan_managed_service("gaori", host_root)
    assert plan_status == "diagnosed"
    assert details["plan"]["action"] == "install"
    with pytest.raises(dev_manager.ManagerError) as failure:
        dev_manager.apply_managed_service(
            "gaori",
            host_root,
            details["plan"]["plan_token"],
            approve_service=False,
        )
    assert failure.value.code == "approval_required"

    apply_status, applied = dev_manager.apply_managed_service(
        "gaori",
        host_root,
        details["plan"]["plan_token"],
        approve_service=True,
    )

    assert apply_status == "success"
    assert applied["status"]["state"] == "ready"
    assert (host_root / "current/gaori").resolve().name == git_sha
    assert (host_root / "bin/gaori").resolve() == (
        host_root / "artifacts/gaori" / git_sha / "bundle/bin/gaori"
    )
    assert not (host_root / "pending/gaori").exists()


def test_busy_service_keeps_old_pair_until_idle_activation(tmp_path):
    host_root = tmp_path / "host"
    (host_root / "artifacts/gaori").mkdir(parents=True)
    first_sha = "1" * 40
    second_sha = "2" * 40
    first, first_manifest = managed_staging(tmp_path, first_sha)
    second, second_manifest = managed_staging(tmp_path, second_sha)
    dev_manager._publish(host_root, first, first_manifest)
    _, first_plan = dev_manager.plan_managed_service("gaori", host_root)
    dev_manager.apply_managed_service(
        "gaori",
        host_root,
        first_plan["plan"]["plan_token"],
        approve_service=True,
    )
    runtime = host_root / "runtime/gaori"
    (runtime / "busy").write_text("busy\n", encoding="utf-8")

    dev_manager._publish(host_root, second, second_manifest)
    _, deferred = dev_manager.plan_managed_service("gaori", host_root)

    assert deferred["plan"]["action"] == "defer"
    assert (host_root / "current/gaori").resolve().name == first_sha
    assert (host_root / "pending/gaori").resolve().name == second_sha
    status, result = dev_manager.apply_managed_service(
        "gaori", host_root, "", approve_service=True
    )
    assert status == "no-change"
    assert result["deferred"] is True
    (runtime / "busy").unlink()
    _, ready = dev_manager.plan_managed_service("gaori", host_root)
    dev_manager.apply_managed_service(
        "gaori",
        host_root,
        ready["plan"]["plan_token"],
        approve_service=True,
    )
    assert (host_root / "current/gaori").resolve().name == second_sha
    assert not (host_root / "pending/gaori").exists()
    assert not (host_root / "artifacts/gaori" / first_sha).exists()


def test_new_pending_generation_cleans_superseded_pending(tmp_path):
    host_root = tmp_path / "host"
    (host_root / "artifacts/gaori").mkdir(parents=True)
    first_sha = "1" * 40
    second_sha = "2" * 40
    third_sha = "3" * 40
    first, first_manifest = managed_staging(tmp_path, first_sha)
    second, second_manifest = managed_staging(tmp_path, second_sha)
    third, third_manifest = managed_staging(tmp_path, third_sha)
    dev_manager._publish(host_root, first, first_manifest)
    _, first_plan = dev_manager.plan_managed_service("gaori", host_root)
    dev_manager.apply_managed_service(
        "gaori",
        host_root,
        first_plan["plan"]["plan_token"],
        approve_service=True,
    )
    dev_manager._publish(host_root, second, second_manifest)

    _, published = dev_manager._publish(host_root, third, third_manifest)

    assert (host_root / "current/gaori").resolve().name == first_sha
    assert (host_root / "pending/gaori").resolve().name == third_sha
    assert published["superseded_pending_git_sha"] == second_sha
    assert not (host_root / "artifacts/gaori" / second_sha).exists()


def test_failed_service_activation_preserves_current_and_pending(tmp_path):
    host_root = tmp_path / "host"
    (host_root / "artifacts/gaori").mkdir(parents=True)
    first_sha = "1" * 40
    second_sha = "2" * 40
    first, first_manifest = managed_staging(tmp_path, first_sha)
    second, second_manifest = managed_staging(tmp_path, second_sha)
    dev_manager._publish(host_root, first, first_manifest)
    _, first_plan = dev_manager.plan_managed_service("gaori", host_root)
    dev_manager.apply_managed_service(
        "gaori",
        host_root,
        first_plan["plan"]["plan_token"],
        approve_service=True,
    )
    dev_manager._publish(host_root, second, second_manifest)
    _, second_plan = dev_manager.plan_managed_service("gaori", host_root)
    runtime = host_root / "runtime/gaori"
    (runtime / "fail-apply").write_text("fail\n", encoding="utf-8")

    with pytest.raises(dev_manager.ManagerError) as failure:
        dev_manager.apply_managed_service(
            "gaori",
            host_root,
            second_plan["plan"]["plan_token"],
            approve_service=True,
        )

    assert failure.value.code == "service_activation_failed"
    assert (host_root / "current/gaori").resolve().name == first_sha
    assert (host_root / "pending/gaori").resolve().name == second_sha
    assert (host_root / "bin/gaori").resolve() == (
        host_root / "artifacts/gaori" / first_sha / "bundle/bin/gaori"
    )


def test_managed_bundle_requires_executable_controller(tmp_path):
    git_sha = "1" * 40
    staging, manifest = managed_staging(tmp_path, git_sha)
    controller = staging / "bundle/libexec/aquarium-dev-service"
    controller.chmod(0o644)
    manifest["sha256"] = dev_manager.artifact_digest(staging / "bundle")

    with pytest.raises(dev_manager.ManagerError) as failure:
        dev_manager._validate_managed_service_bundle(staging / "bundle", manifest)

    assert failure.value.code == "artifact_invalid"


def test_launcher_requires_matching_ready_managed_service(
    tmp_path, monkeypatch, capsys
):
    home = tmp_path / "home"
    host_root = home / ".aquarium-dev"
    (host_root / "artifacts/gaori").mkdir(parents=True)
    git_sha = "1" * 40
    staging, manifest = managed_staging(tmp_path, git_sha)
    dev_manager._publish(host_root, staging, manifest)
    _, planned = dev_manager.plan_managed_service("gaori", host_root)
    dev_manager.apply_managed_service(
        "gaori",
        host_root,
        planned["plan"]["plan_token"],
        approve_service=True,
    )
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    observed = {}

    def fake_execve(executable, arguments, environment):
        observed.update(executable=executable, arguments=arguments)
        raise OSError("captured")

    monkeypatch.setattr(os, "execve", fake_execve)
    assert launcher.main(["gaori", "status"]) == 127
    assert "captured" in capsys.readouterr().err
    assert (
        observed["executable"]
        == host_root / "artifacts/gaori" / git_sha / "bundle/bin/gaori"
    )
    assert observed["arguments"] == ["gaori", "status"]

    (host_root / "runtime/gaori/active").write_text("f" * 40, encoding="utf-8")
    observed.clear()
    assert launcher.main(["gaori", "status"]) == 127
    assert not observed
