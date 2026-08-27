"""Host-local enrollment and hook lifecycle for dev-aquarium."""

from __future__ import annotations

import json
import os
import platform
import shlex
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dev_contract import ContractError, validate_description

ENROLLMENT_SCHEMA = "aquarium-dev-enrollment/v1"
MARKER_START = "# BEGIN AQUARIUM DEV v1"
MARKER_END = "# END AQUARIUM DEV v1"


@dataclass
class ManagerError(Exception):
    code: str
    message: str
    action: str
    stage: str
    project_id: str | None = None
    git_sha: str | None = None


def run_git(
    repository: Path, *arguments: str, check: bool = True
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise ManagerError(
            "not_git_root",
            result.stderr.strip() or "Git rejected the repository.",
            "Run the command from one supported canonical Git root.",
            "diagnose",
        )
    return result


def require_supported_host() -> None:
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise ManagerError(
            "unsupported_host",
            "The development channel supports Darwin arm64 only.",
            "Use a supported Apple Silicon macOS host.",
            "diagnose",
        )


def _repository_identity(repository: Path) -> tuple[Path, str, str, bool]:
    if repository.is_symlink():
        raise ManagerError(
            "symlink_git_root",
            "The repository argument is a symbolic link.",
            "Use the canonical real checkout path.",
            "diagnose",
        )
    try:
        resolved = repository.resolve(strict=True)
    except OSError as error:
        raise ManagerError(
            "not_git_root",
            str(error),
            "Use an existing canonical Git root.",
            "diagnose",
        ) from error
    top = Path(
        run_git(resolved, "rev-parse", "--show-toplevel").stdout.strip()
    ).resolve()
    git_dir = resolved / ".git"
    if top != resolved or not git_dir.is_dir() or git_dir.is_symlink():
        raise ManagerError(
            "not_git_root",
            "The path is not one regular canonical Git root.",
            "Run from the root of a non-linked primary checkout.",
            "diagnose",
        )
    branch = run_git(resolved, "symbolic-ref", "--short", "HEAD").stdout.strip()
    if branch != "main":
        raise ManagerError(
            "not_local_main",
            f"The checked-out branch is {branch or 'detached'}, not main.",
            "Check out the canonical local main branch.",
            "diagnose",
        )
    git_sha = run_git(resolved, "rev-parse", "HEAD").stdout.strip()
    main_sha = run_git(resolved, "rev-parse", "refs/heads/main").stdout.strip()
    if git_sha != main_sha:
        raise ManagerError(
            "sha_mismatch",
            "HEAD does not equal local refs/heads/main.",
            "Restore the canonical local main checkout.",
            "diagnose",
            git_sha=git_sha,
        )
    dirty = bool(run_git(resolved, "status", "--porcelain=v1").stdout)
    return resolved, branch, git_sha, dirty


def _describe(repository: Path) -> dict[str, Any]:
    result = subprocess.run(
        ["make", "-s", "aquarium-dev-describe"],
        cwd=repository,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ManagerError(
            "producer_contract_missing",
            result.stderr.strip() or "aquarium-dev-describe is unavailable.",
            "Implement both shared producer Make targets.",
            "diagnose",
        )
    try:
        description = json.loads(result.stdout)
        validate_description(description)
    except (json.JSONDecodeError, ContractError) as error:
        raise ManagerError(
            "producer_description_invalid",
            str(error),
            "Repair aquarium-dev-describe to emit one valid v1 object.",
            "diagnose",
        ) from error
    probe = subprocess.run(
        ["make", "-n", "aquarium-dev-build", f"AQUARIUM_DEV_OUTPUT={repository}"],
        cwd=repository,
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0:
        raise ManagerError(
            "producer_contract_missing",
            "aquarium-dev-build is unavailable.",
            "Implement both shared producer Make targets.",
            "diagnose",
            description["project_id"],
        )
    return description


def _hook_path(repository: Path) -> Path:
    configured = run_git(repository, "config", "--get", "core.hooksPath", check=False)
    if configured.returncode == 0 and configured.stdout.strip():
        raise ManagerError(
            "hook_conflict",
            "An external core.hooksPath is configured.",
            "Remove or explicitly integrate the external hook framework before enrollment.",
            "hook",
        )
    return repository / ".git" / "hooks" / "post-commit"


def marker_block(repository: Path, manager_script: Path) -> str:
    command = " ".join(
        shlex.quote(value)
        for value in (
            os.fspath(Path(os.sys.executable).resolve()),
            os.fspath(manager_script.resolve()),
            "request",
            "--repository",
            os.fspath(repository),
        )
    )
    return f"{MARKER_START}\n{command} >/dev/null 2>&1 &\n{MARKER_END}\n"


def _read_hook(hook: Path) -> tuple[str, int]:
    if not hook.exists():
        return "#!/bin/sh\n", 0o755
    if hook.is_symlink() or not hook.is_file():
        raise ManagerError(
            "hook_conflict",
            "post-commit is not a regular native hook.",
            "Replace the unsupported hook form before enrollment.",
            "hook",
        )
    return hook.read_text(encoding="utf-8"), stat.S_IMODE(hook.stat().st_mode)


def _atomic_write(path: Path, content: str, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(mode)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _install_block(hook: Path, block: str) -> bool:
    content, mode = _read_hook(hook)
    _validate_block_installable(content, block)
    if block in content:
        return False
    separator = "" if content.endswith("\n") else "\n"
    _atomic_write(hook, content + separator + block, mode | stat.S_IXUSR)
    return True


def _validate_block_installable(content: str, block: str) -> None:
    starts = content.count(MARKER_START)
    ends = content.count(MARKER_END)
    if starts or ends:
        if starts == 1 and ends == 1 and block in content:
            return
        raise ManagerError(
            "hook_conflict",
            "The Aquarium marker is duplicate, malformed, or changed.",
            "Run diagnosis and approve repair of the exact owned block.",
            "hook",
        )


def _remove_recorded_block(enrollment: dict[str, Any]) -> None:
    hook = Path(enrollment["hook_path"])
    block = enrollment["hook_block"]
    content, mode = _read_hook(hook)
    if (
        content.count(MARKER_START) != 1
        or content.count(MARKER_END) != 1
        or content.count(block) != 1
    ):
        raise ManagerError(
            "hook_conflict",
            "The previously owned hook block no longer matches enrollment metadata.",
            "Restore the recorded hook or approve a bounded manual repair.",
            "hook",
            enrollment["project_id"],
        )
    remaining = content.replace(block, "", 1)
    _atomic_write(hook, remaining, mode)


def enrollment_path(host_root: Path, project_id: str) -> Path:
    return host_root / "enrollments" / f"{project_id}.json"


def read_enrollment(host_root: Path, project_id: str) -> dict[str, Any] | None:
    path = enrollment_path(host_root, project_id)
    if not path.exists():
        return None
    if path.is_symlink() or not path.is_file():
        raise ManagerError(
            "enrollment_broken",
            "Enrollment metadata is not a regular file.",
            "Approve repair of the bounded enrollment record.",
            "enrollment",
            project_id,
        )
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ManagerError(
            "enrollment_broken",
            str(error),
            "Approve replacement of the invalid enrollment record.",
            "enrollment",
            project_id,
        ) from error
    expected = {
        "schema",
        "project_id",
        "checkout",
        "hook_path",
        "hook_block",
        "enrolled_at",
    }
    if (
        set(value) != expected
        or value.get("schema") != ENROLLMENT_SCHEMA
        or value.get("project_id") != project_id
    ):
        raise ManagerError(
            "enrollment_broken",
            "Enrollment metadata does not satisfy aquarium-dev-enrollment/v1.",
            "Approve replacement of the invalid enrollment record.",
            "enrollment",
            project_id,
        )
    return value


def diagnose(repository: Path, host_root: Path) -> dict[str, Any]:
    require_supported_host()
    checkout, branch, git_sha, dirty = _repository_identity(repository)
    description = _describe(checkout)
    project_id = description["project_id"]
    hook = _hook_path(checkout)
    hook_content, _ = _read_hook(hook)
    enrollment = read_enrollment(host_root, project_id)
    enrollment_state = "absent"
    hook_state = "absent" if not hook.exists() else "foreign"
    if enrollment is not None:
        enrollment_state = (
            "healthy" if Path(enrollment["checkout"]) == checkout else "other-checkout"
        )
        if enrollment_state == "healthy":
            hook_state = (
                "owned" if enrollment["hook_block"] in hook_content else "stale"
            )
    return {
        "checkout": str(checkout),
        "branch": branch,
        "git_sha": git_sha,
        "dirty": dirty,
        "description": description,
        "enrollment": enrollment_state,
        "hook": hook_state,
    }


def enroll(
    repository: Path,
    host_root: Path,
    manager_script: Path,
    *,
    approve_enrollment: bool,
    approve_hook: bool,
    approve_reenrollment: bool,
) -> tuple[str, dict[str, Any]]:
    diagnosis = diagnose(repository, host_root)
    project_id = diagnosis["description"]["project_id"]
    if not approve_enrollment:
        raise ManagerError(
            "approval_required",
            "Enrollment approval is required.",
            "Approve only the displayed enrollment metadata effect.",
            "enrollment",
            project_id,
            diagnosis["git_sha"],
        )
    if not approve_hook:
        raise ManagerError(
            "approval_required",
            "Hook approval is required separately.",
            "Approve only the displayed native hook marker effect.",
            "hook",
            project_id,
            diagnosis["git_sha"],
        )
    checkout = Path(diagnosis["checkout"])
    hook = _hook_path(checkout)
    block = marker_block(checkout, manager_script)
    existing = read_enrollment(host_root, project_id)
    if existing is not None and Path(existing["checkout"]) != checkout:
        if not approve_reenrollment:
            raise ManagerError(
                "enrollment_conflict",
                "Another canonical checkout is already enrolled.",
                "Approve re-enrollment from the diagnosed old checkout to this checkout.",
                "enrollment",
                project_id,
                diagnosis["git_sha"],
            )
        new_content, _ = _read_hook(hook)
        _validate_block_installable(new_content, block)
        _remove_recorded_block(existing)
    hook_changed = _install_block(hook, block)
    if (
        existing is not None
        and Path(existing["checkout"]) == checkout
        and existing["hook_block"] == block
    ):
        return "no-change", diagnosis
    record = {
        "schema": ENROLLMENT_SCHEMA,
        "project_id": project_id,
        "checkout": str(checkout),
        "hook_path": str(hook),
        "hook_block": block,
        "enrolled_at": datetime.now(timezone.utc).isoformat(),
    }
    target = enrollment_path(host_root, project_id)
    _atomic_write(target, json.dumps(record, sort_keys=True, indent=2) + "\n", 0o600)
    diagnosis["hook_changed"] = hook_changed
    return "success", diagnosis


def repair_hook(
    repository: Path,
    host_root: Path,
    manager_script: Path,
    *,
    approve_hook: bool,
) -> tuple[str, dict[str, Any]]:
    diagnosis = diagnose(repository, host_root)
    project_id = diagnosis["description"]["project_id"]
    enrollment = read_enrollment(host_root, project_id)
    if enrollment is None or Path(enrollment["checkout"]) != Path(
        diagnosis["checkout"]
    ):
        raise ManagerError(
            "enrollment_missing",
            "This checkout is not the canonical enrolled checkout.",
            "Enroll it before repairing its hook.",
            "hook",
            project_id,
        )
    if not approve_hook:
        raise ManagerError(
            "approval_required",
            "Hook repair approval is required.",
            "Approve the exact hook repair effect.",
            "hook",
            project_id,
        )
    expected = marker_block(Path(diagnosis["checkout"]), manager_script)
    if enrollment["hook_block"] != expected:
        raise ManagerError(
            "hook_conflict",
            "Recorded hook ownership does not match this manager generation.",
            "Re-enroll through the explicit transfer workflow.",
            "hook",
            project_id,
        )
    changed = _install_block(Path(enrollment["hook_path"]), expected)
    diagnosis["hook_changed"] = changed
    return ("success" if changed else "no-change"), diagnosis
