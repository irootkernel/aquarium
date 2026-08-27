import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "plugins/aquarium/skills/dev-aquarium/scripts/dev_aquarium.py"


def create_repository(path: Path) -> Path:
    path.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", path], check=True)
    subprocess.run(["git", "-C", path, "config", "user.name", "Test"], check=True)
    subprocess.run(
        ["git", "-C", path, "config", "user.email", "test@example.invalid"],
        check=True,
    )
    (path / "Makefile").write_text(
        """aquarium-dev-describe:
\t@printf '%s\\n' '{"schema":"aquarium-dev-producer-description/v1","project_id":"aquarium","next_version":"v0.1.14","artifact_kind":"codex-plugin","artifact_path":"plugin"}'

aquarium-dev-build:
\t@:
""",
        encoding="utf-8",
    )
    subprocess.run(["git", "-C", path, "add", "Makefile"], check=True)
    subprocess.run(["git", "-C", path, "commit", "-q", "-m", "initial"], check=True)
    return path


def run_cli(host_root: Path, *arguments: str):
    return subprocess.run(
        [sys.executable, CLI, "--host-root", host_root, *arguments],
        capture_output=True,
        text=True,
        check=False,
    )


def payload(result: subprocess.CompletedProcess[str]):
    return json.loads(result.stdout or result.stderr)


def test_diagnosis_is_read_only(tmp_path):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"

    result = run_cli(host_root, "diagnose", "--repository", repository)

    assert result.returncode == 0
    assert payload(result)["details"]["enrollment"] == "absent"
    assert not host_root.exists()
    assert not (repository / ".git/hooks/post-commit").exists()


@pytest.mark.parametrize(
    "approvals",
    [(), ("--approve-enrollment",), ("--approve-hook",)],
)
def test_enrollment_requires_separate_enrollment_and_hook_approvals(
    tmp_path, approvals
):
    repository = create_repository(tmp_path / "repository")
    result = run_cli(
        tmp_path / "host",
        "enroll",
        "--repository",
        repository,
        *approvals,
    )

    assert result.returncode == 2
    assert payload(result)["error"]["code"] == "approval_required"


def test_enrollment_preserves_foreign_hook_and_is_idempotent(tmp_path):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    hook = repository / ".git/hooks/post-commit"
    foreign = "#!/bin/sh\nprintf foreign\n"
    hook.write_text(foreign, encoding="utf-8")
    hook.chmod(0o750)

    first = run_cli(
        host_root,
        "enroll",
        "--repository",
        repository,
        "--approve-enrollment",
        "--approve-hook",
    )
    first_bytes = hook.read_bytes()
    enrollment = host_root / "enrollments/aquarium.json"
    first_record = enrollment.read_bytes()
    second = run_cli(
        host_root,
        "enroll",
        "--repository",
        repository,
        "--approve-enrollment",
        "--approve-hook",
    )

    assert first.returncode == 0
    assert payload(first)["status"] == "success"
    assert first_bytes.startswith(foreign.encode())
    assert first_bytes.count(b"BEGIN AQUARIUM DEV v1") == 1
    assert stat.S_IMODE(hook.stat().st_mode) == 0o750
    assert stat.S_IMODE(enrollment.stat().st_mode) == 0o600
    assert second.returncode == 0
    assert payload(second)["status"] == "no-change"
    assert hook.read_bytes() == first_bytes
    assert enrollment.read_bytes() == first_record


def test_reenrollment_requires_approval_and_transfers_only_owned_block(tmp_path):
    first_repository = create_repository(tmp_path / "first")
    second_repository = create_repository(tmp_path / "second")
    host_root = tmp_path / "host"
    for repository, word in (
        (first_repository, "first"),
        (second_repository, "second"),
    ):
        hook = repository / ".git/hooks/post-commit"
        hook.write_text(f"#!/bin/sh\nprintf {word}\n", encoding="utf-8")
        hook.chmod(0o755)
    assert (
        run_cli(
            host_root,
            "enroll",
            "--repository",
            first_repository,
            "--approve-enrollment",
            "--approve-hook",
        ).returncode
        == 0
    )

    rejected = run_cli(
        host_root,
        "enroll",
        "--repository",
        second_repository,
        "--approve-enrollment",
        "--approve-hook",
    )
    transferred = run_cli(
        host_root,
        "enroll",
        "--repository",
        second_repository,
        "--approve-enrollment",
        "--approve-hook",
        "--approve-reenrollment",
    )

    assert payload(rejected)["error"]["code"] == "enrollment_conflict"
    assert transferred.returncode == 0
    assert (
        first_repository / ".git/hooks/post-commit"
    ).read_text() == "#!/bin/sh\nprintf first\n"
    second_hook = (second_repository / ".git/hooks/post-commit").read_text()
    assert second_hook.startswith("#!/bin/sh\nprintf second\n")
    assert second_hook.count("BEGIN AQUARIUM DEV v1") == 1
    record = json.loads((host_root / "enrollments/aquarium.json").read_text())
    assert Path(record["checkout"]) == second_repository


def test_reenrollment_preflights_new_hook_before_removing_old_block(tmp_path):
    first_repository = create_repository(tmp_path / "first")
    second_repository = create_repository(tmp_path / "second")
    host_root = tmp_path / "host"
    run_cli(
        host_root,
        "enroll",
        "--repository",
        first_repository,
        "--approve-enrollment",
        "--approve-hook",
    )
    first_hook = first_repository / ".git/hooks/post-commit"
    owned = first_hook.read_bytes()
    second_hook = second_repository / ".git/hooks/post-commit"
    second_hook.write_text(
        "#!/bin/sh\n# BEGIN AQUARIUM DEV v1\ndrift\n", encoding="utf-8"
    )
    second_hook.chmod(0o755)

    result = run_cli(
        host_root,
        "enroll",
        "--repository",
        second_repository,
        "--approve-enrollment",
        "--approve-hook",
        "--approve-reenrollment",
    )

    assert payload(result)["error"]["code"] == "hook_conflict"
    assert first_hook.read_bytes() == owned


def test_external_or_symbolic_hook_configuration_fails_closed(tmp_path):
    repository = create_repository(tmp_path / "repository")
    subprocess.run(
        ["git", "-C", repository, "config", "core.hooksPath", "external-hooks"],
        check=True,
    )
    result = run_cli(tmp_path / "host", "diagnose", "--repository", repository)
    assert payload(result)["error"]["code"] == "hook_conflict"

    subprocess.run(
        ["git", "-C", repository, "config", "--unset", "core.hooksPath"], check=True
    )
    target = tmp_path / "foreign-hook"
    target.write_text("#!/bin/sh\n", encoding="utf-8")
    os.symlink(target, repository / ".git/hooks/post-commit")
    result = run_cli(tmp_path / "host", "diagnose", "--repository", repository)
    assert payload(result)["error"]["code"] == "hook_conflict"
