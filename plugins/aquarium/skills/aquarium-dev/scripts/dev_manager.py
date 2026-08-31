"""Host-local lifecycle manager for aquarium-dev."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import platform
import shlex
import shutil
import signal
import stat
import subprocess
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dev_contract import (
    PROJECT_IDS,
    SHA_RE,
    ContractError,
    validate_description,
    validate_manifest,
    validate_service_plan,
    validate_service_result,
    validate_service_status,
)

ENROLLMENT_SCHEMA = "aquarium-dev-enrollment/v1"
MARKER_START = "# BEGIN AQUARIUM DEV v1"
MARKER_END = "# END AQUARIUM DEV v1"
MANIFEST_NAME = ".aquarium-manifest.json"
QUEUE_SCHEMA = "aquarium-dev-build-request/v1"
DIAGNOSTIC_SCHEMA = "aquarium-dev-diagnostic/v1"
PRODUCER_BUILD_TIMEOUT_SECONDS = 600
PROCESS_TERMINATION_GRACE_SECONDS = 5
SERVICE_CONTROLLER_TIMEOUT_SECONDS = 60


@dataclass
class ManagerError(Exception):
    code: str
    message: str
    action: str
    stage: str
    project_id: str | None = None
    git_sha: str | None = None


def _terminate_process_bounded(process: subprocess.Popen[Any]) -> None:
    for termination_signal in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(process.pid, termination_signal)
        except OSError:
            if process.poll() is None:
                try:
                    process.send_signal(termination_signal)
                except OSError:
                    pass
        try:
            process.communicate(timeout=PROCESS_TERMINATION_GRACE_SECONDS)
            return
        except subprocess.TimeoutExpired:
            continue
    if process.stdout is not None:
        process.stdout.close()
    if process.stderr is not None:
        process.stderr.close()
    try:
        process.wait(timeout=PROCESS_TERMINATION_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        pass


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
            "Repair aquarium-dev-describe to emit one supported description.",
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


def _atomic_json(path: Path, value: dict[str, Any], mode: int = 0o600) -> None:
    _atomic_write(path, json.dumps(value, sort_keys=True, indent=2) + "\n", mode)


def install_launcher(
    source: Path, target: Path, *, approve_launcher: bool
) -> tuple[str, dict[str, Any]]:
    require_supported_host()
    if not approve_launcher:
        raise ManagerError(
            "approval_required",
            "Launcher installation approval is required.",
            "Approve only the displayed user-local aquarium-dev launcher target.",
            "install-launcher",
        )
    expected = Path.home() / ".local" / "bin" / "aquarium-dev"
    if target != expected or not target.is_absolute():
        raise ManagerError(
            "invalid_arguments",
            "The launcher target must be ~/.local/bin/aquarium-dev.",
            "Use the supported user-local launcher target.",
            "install-launcher",
        )
    if source.is_symlink() or not source.is_file():
        raise ManagerError(
            "artifact_missing",
            "The packaged aquarium-dev launcher is unavailable.",
            "Repair the Aquarium plugin installation and retry.",
            "install-launcher",
        )
    content = source.read_text(encoding="utf-8")
    if target.exists():
        if target.is_symlink() or not target.is_file():
            raise ManagerError(
                "artifact_invalid",
                "The launcher target is not a regular file.",
                "Move the conflicting target aside before retrying.",
                "install-launcher",
            )
        if (
            target.read_text(encoding="utf-8") == content
            and stat.S_IMODE(target.stat().st_mode) == 0o755
        ):
            return "no-change", {"target": str(target)}
    _atomic_write(target, content, 0o755)
    return "success", {"target": str(target)}


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


def _file_snapshot(path: Path) -> tuple[bool, str, int]:
    if not path.exists():
        return False, "", 0
    if path.is_symlink() or not path.is_file():
        raise ManagerError(
            "enrollment_broken",
            "A managed enrollment path is not a regular file.",
            "Restore the bounded hook or enrollment path before retrying.",
            "enrollment",
        )
    return True, path.read_text(encoding="utf-8"), stat.S_IMODE(path.stat().st_mode)


def _restore_file_snapshot(path: Path, snapshot: tuple[bool, str, int]) -> None:
    existed, content, mode = snapshot
    if existed:
        _atomic_write(path, content, mode)
    else:
        path.unlink(missing_ok=True)


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


def _validated_command_selector(
    host_root: Path,
    project_id: str,
    artifact: Path,
    manifest: dict[str, Any],
) -> Path | None:
    if manifest["artifact_kind"] not in {"executable", "managed-service"}:
        return None
    selector = host_root / "bin" / project_id
    if not selector.is_symlink():
        raise ManagerError(
            "artifact_missing",
            "The development command selector is missing.",
            "Rebuild the enrolled project to publish its command selector.",
            "diagnose",
            project_id,
            manifest["git_sha"],
        )
    try:
        resolved = selector.resolve(strict=True)
    except OSError as error:
        raise ManagerError(
            "artifact_missing",
            str(error),
            "Rebuild the enrolled project to restore its command selector.",
            "diagnose",
            project_id,
            manifest["git_sha"],
        ) from error
    expected = (
        artifact
        if manifest["artifact_kind"] == "executable"
        else artifact / manifest["command_path"]
    )
    if resolved != expected:
        raise ManagerError(
            "artifact_invalid",
            "The development command selector does not match the current artifact.",
            "Rebuild the enrolled project to repair its command selector.",
            "diagnose",
            project_id,
            manifest["git_sha"],
        )
    return selector


def resolved_project_diagnosis(host_root: Path) -> list[dict[str, Any]]:
    projects = []
    for project_id in sorted(PROJECT_IDS):
        try:
            enrollment = read_enrollment(host_root, project_id)
            if enrollment is None:
                projects.append({"project_id": project_id, "state": "not-enrolled"})
                continue
            checkout = Path(enrollment["checkout"])
            description = _describe(checkout)
            generation = _current_generation(host_root, project_id)
            pending_generation = _pending_generation(host_root, project_id)
            if generation is None:
                generation = pending_generation
                if generation is None:
                    projects.append(
                        {"project_id": project_id, "state": "artifact-missing"}
                    )
                    continue
                selected_state = "pending-service"
            else:
                selected_state = "development"
            artifact, manifest = _validate_generation(
                generation, project_id, description
            )
            pending = None
            if pending_generation is not None:
                pending_artifact, pending_manifest = _validate_generation(
                    pending_generation, project_id, description
                )
                pending = {
                    "git_sha": pending_manifest["git_sha"],
                    "development_version": pending_manifest["development_version"],
                    "artifact": str(pending_artifact),
                    "sha256": pending_manifest["sha256"],
                }
            command = (
                _validated_command_selector(host_root, project_id, artifact, manifest)
                if selected_state == "development"
                else None
            )
            service = None
            if manifest["artifact_kind"] == "managed-service":
                _, controller = _service_entrypoints(generation, manifest)
                service = _controller_json(
                    controller,
                    [
                        "status",
                        "--json",
                        "--runtime-root",
                        os.fspath(host_root / "runtime" / project_id),
                    ],
                    validate_service_status,
                    project_id,
                    generation.name,
                )
            projects.append(
                {
                    "project_id": project_id,
                    "state": selected_state,
                    "checkout": str(checkout),
                    "git_sha": manifest["git_sha"],
                    "development_version": manifest["development_version"],
                    "artifact": str(artifact),
                    "command": str(command) if command is not None else None,
                    "service": service,
                    "pending": pending,
                    "sha256": manifest["sha256"],
                }
            )
        except ManagerError as error:
            projects.append(
                {"project_id": project_id, "state": "broken", "error": error.code}
            )
    return projects


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
    current = {"state": "absent"}
    if enrollment_state == "healthy":
        try:
            generation = _current_generation(host_root, project_id)
            pending_generation = _pending_generation(host_root, project_id)
            selected_state = "healthy"
            if generation is None:
                generation = pending_generation
                selected_state = "pending-service"
            if generation is not None:
                artifact, manifest = _validate_generation(
                    generation, project_id, description
                )
                pending = None
                if pending_generation is not None:
                    pending_artifact, pending_manifest = _validate_generation(
                        pending_generation, project_id, description
                    )
                    pending = {
                        "git_sha": pending_manifest["git_sha"],
                        "development_version": pending_manifest["development_version"],
                        "artifact": str(pending_artifact),
                        "sha256": pending_manifest["sha256"],
                    }
                command = (
                    _validated_command_selector(
                        host_root, project_id, artifact, manifest
                    )
                    if selected_state == "healthy"
                    else None
                )
                service = None
                if manifest["artifact_kind"] == "managed-service":
                    _, controller = _service_entrypoints(generation, manifest)
                    service = _controller_json(
                        controller,
                        [
                            "status",
                            "--json",
                            "--runtime-root",
                            os.fspath(host_root / "runtime" / project_id),
                        ],
                        validate_service_status,
                        project_id,
                        generation.name,
                    )
                current = {
                    "state": selected_state,
                    "git_sha": manifest["git_sha"],
                    "development_version": manifest["development_version"],
                    "artifact": str(artifact),
                    "command": str(command) if command is not None else None,
                    "service": service,
                    "pending": pending,
                    "sha256": manifest["sha256"],
                }
        except ManagerError as error:
            current = {"state": "broken", "error": error.code}
    return {
        "checkout": str(checkout),
        "branch": branch,
        "git_sha": git_sha,
        "dirty": dirty,
        "description": description,
        "enrollment": enrollment_state,
        "hook": hook_state,
        "current": current,
        "resolved_projects": resolved_project_diagnosis(host_root),
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
    with _enrollment_lock(host_root, project_id):
        diagnosis = diagnose(repository, host_root)
        if diagnosis["description"]["project_id"] != project_id:
            raise ManagerError(
                "enrollment_broken",
                "The producer identity changed while enrollment was being admitted.",
                "Retry after restoring one stable producer description.",
                "enrollment",
                project_id,
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

        same_enrollment = (
            existing is not None
            and Path(existing["checkout"]) == checkout
            and existing["hook_block"] == block
        )
        same_checkout_migration = (
            existing is not None
            and Path(existing["checkout"]) == checkout
            and existing["hook_block"] != block
        )
        if same_checkout_migration and not approve_reenrollment:
            raise ManagerError(
                "enrollment_conflict",
                "This checkout is enrolled through an older Aquarium hook block.",
                "Approve migration of the exact recorded block to this manager generation.",
                "enrollment",
                project_id,
                diagnosis["git_sha"],
            )

        target = enrollment_path(host_root, project_id)
        managed_paths = {hook, target}
        if existing is not None:
            managed_paths.add(Path(existing["hook_path"]))
        snapshots = {path: _file_snapshot(path) for path in managed_paths}
        try:
            if same_checkout_migration:
                _remove_recorded_block(existing)
            hook_changed = _install_block(hook, block)
            if same_enrollment:
                diagnosis["hook_changed"] = hook_changed
                return ("success" if hook_changed else "no-change"), diagnosis
            if existing is not None and Path(existing["checkout"]) != checkout:
                _remove_recorded_block(existing)
            record = {
                "schema": ENROLLMENT_SCHEMA,
                "project_id": project_id,
                "checkout": str(checkout),
                "hook_path": str(hook),
                "hook_block": block,
                "enrolled_at": datetime.now(timezone.utc).isoformat(),
            }
            _atomic_write(
                target, json.dumps(record, sort_keys=True, indent=2) + "\n", 0o600
            )
            if read_enrollment(host_root, project_id) != record:
                raise ManagerError(
                    "enrollment_broken",
                    "The enrollment record changed while it was being committed.",
                    "Inspect the bounded enrollment path before retrying.",
                    "enrollment",
                    project_id,
                    diagnosis["git_sha"],
                )
        except BaseException:
            for path, snapshot in snapshots.items():
                _restore_file_snapshot(path, snapshot)
            raise
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
    if not approve_hook:
        raise ManagerError(
            "approval_required",
            "Hook repair approval is required.",
            "Approve the exact hook repair effect.",
            "hook",
            project_id,
        )
    with _enrollment_lock(host_root, project_id):
        diagnosis = diagnose(repository, host_root)
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


def _require_enrolled_checkout(
    repository: Path, host_root: Path, *, require_clean: bool
) -> tuple[Path, dict[str, Any], dict[str, Any], str]:
    checkout, _, git_sha, dirty = _repository_identity(repository)
    description = _describe(checkout)
    project_id = description["project_id"]
    enrollment = read_enrollment(host_root, project_id)
    if enrollment is None or Path(enrollment["checkout"]) != checkout:
        raise ManagerError(
            "enrollment_missing",
            "This checkout is not the enrolled canonical checkout.",
            "Enroll this exact checkout before requesting a development build.",
            "schedule",
            project_id,
            git_sha,
        )
    if require_clean and dirty:
        raise ManagerError(
            "dirty_worktree",
            "The enrolled checkout has uncommitted changes.",
            "Commit or remove every change before requesting a development build.",
            "schedule",
            project_id,
            git_sha,
        )
    return checkout, enrollment, description, git_sha


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_digest(path: Path) -> str:
    """Return the canonical digest for one regular file or directory tree."""
    if path.is_symlink():
        raise ManagerError(
            "artifact_invalid",
            "The artifact path is a symbolic link.",
            "Produce only regular files and directories.",
            "validate",
        )
    if path.is_file():
        return f"sha256:{_sha256_file(path)}"
    if not path.is_dir():
        raise ManagerError(
            "artifact_missing",
            "The declared artifact does not exist.",
            "Repair the producer output and rebuild.",
            "validate",
        )
    digest = hashlib.sha256()
    for candidate in sorted(path.rglob("*"), key=lambda item: item.as_posix()):
        if candidate.is_symlink() or (
            not candidate.is_dir() and not candidate.is_file()
        ):
            raise ManagerError(
                "artifact_invalid",
                "Directory artifacts may contain only regular files and directories.",
                "Remove symbolic links and special files from the producer output.",
                "validate",
            )
        if candidate.is_file():
            relative = candidate.relative_to(path).as_posix().encode("utf-8")
            digest.update(relative)
            digest.update(b"\0")
            digest.update(bytes.fromhex(_sha256_file(candidate)))
            digest.update(b"\n")
    return f"sha256:{digest.hexdigest()}"


def _producer_identity_fields(document: dict[str, Any]) -> tuple[str, ...]:
    fields = ("project_id", "artifact_kind", "artifact_path")
    if document["artifact_kind"] == "managed-service":
        return (*fields, "command_path", "controller_path")
    return fields


def _contained_executable(artifact: Path, relative: str, role: str) -> Path:
    candidate = artifact.joinpath(*relative.split("/"))
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as error:
        raise ManagerError(
            "artifact_missing",
            f"The managed-service {role} is unavailable: {error}",
            "Repair the producer bundle and rebuild.",
            "validate",
        ) from error
    if artifact.resolve() not in resolved.parents or candidate.is_symlink():
        raise ManagerError(
            "output_escape",
            f"The managed-service {role} escapes its bundle.",
            "Keep every managed-service entrypoint inside the declared bundle.",
            "validate",
        )
    if not resolved.is_file() or not os.access(resolved, os.X_OK):
        raise ManagerError(
            "artifact_invalid",
            f"The managed-service {role} is not one regular executable.",
            "Produce executable command and controller entrypoints.",
            "validate",
        )
    return resolved


def _validate_managed_service_bundle(
    artifact: Path, manifest: dict[str, Any]
) -> tuple[Path, Path] | None:
    if manifest["artifact_kind"] != "managed-service":
        return None
    if not artifact.is_dir():
        raise ManagerError(
            "artifact_invalid",
            "The managed-service artifact is not a bundle directory.",
            "Produce the complete managed-service bundle at artifact_path.",
            "validate",
            manifest["project_id"],
            manifest.get("git_sha"),
        )
    return (
        _contained_executable(artifact, manifest["command_path"], "command"),
        _contained_executable(artifact, manifest["controller_path"], "controller"),
    )


def _read_single_json(stdout: str, project_id: str, git_sha: str) -> dict[str, Any]:
    try:
        value = json.loads(stdout)
        return validate_manifest(value)
    except (json.JSONDecodeError, ContractError) as error:
        raise ManagerError(
            "producer_manifest_invalid",
            str(error),
            "Repair aquarium-dev-build to emit one supported manifest.",
            "validate",
            project_id,
            git_sha,
        ) from error


def _contained_artifact(staging: Path, relative: str) -> Path:
    artifact = staging.joinpath(*relative.split("/"))
    try:
        resolved = artifact.resolve(strict=True)
    except OSError as error:
        raise ManagerError(
            "artifact_missing",
            str(error),
            "Repair the declared producer artifact path.",
            "validate",
        ) from error
    if staging.resolve() not in resolved.parents:
        raise ManagerError(
            "output_escape",
            "The declared artifact resolves outside the staging directory.",
            "Keep producer output beneath AQUARIUM_DEV_OUTPUT.",
            "validate",
        )
    return resolved


@contextmanager
def _exact_build_checkout(
    checkout: Path, host_root: Path, project_id: str, git_sha: str
):
    build_root = host_root / "builds" / project_id
    build_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"{git_sha}.", dir=build_root) as raw:
        exact_checkout = Path(raw) / "source"
        clone = subprocess.run(
            [
                "git",
                "clone",
                "--quiet",
                "--no-hardlinks",
                "--no-checkout",
                "--",
                str(checkout),
                str(exact_checkout),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if clone.returncode != 0:
            raise ManagerError(
                "producer_build_failed",
                (
                    clone.stderr.strip()
                    or "Git could not isolate the admitted revision."
                )[:1000],
                "Repair the local repository and run an explicitly approved rebuild.",
                "build",
                project_id,
                git_sha,
            )
        selected = subprocess.run(
            [
                "git",
                "-C",
                str(exact_checkout),
                "checkout",
                "--quiet",
                "-B",
                "main",
                git_sha,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        observed_sha = run_git(exact_checkout, "rev-parse", "HEAD").stdout.strip()
        observed_branch = run_git(
            exact_checkout, "symbolic-ref", "--short", "HEAD"
        ).stdout.strip()
        if (
            selected.returncode != 0
            or observed_sha != git_sha
            or observed_branch != "main"
            or run_git(exact_checkout, "status", "--porcelain=v1").stdout
            or not (exact_checkout / ".git").is_dir()
        ):
            raise ManagerError(
                "sha_mismatch",
                selected.stderr.strip()
                or "The isolated build checkout does not match the admitted revision.",
                "Queue the current completed local-main revision again.",
                "build",
                project_id,
                git_sha,
            )
        yield exact_checkout


def _validated_build(
    checkout: Path,
    host_root: Path,
    description: dict[str, Any],
    git_sha: str,
) -> tuple[Path, dict[str, Any]]:
    project_id = description["project_id"]
    artifact_parent = host_root / "artifacts" / project_id
    artifact_parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".staging-", dir=artifact_parent))
    try:
        with _exact_build_checkout(checkout, host_root, project_id, git_sha) as source:
            process = subprocess.Popen(
                [
                    "make",
                    "-s",
                    "aquarium-dev-build",
                    f"AQUARIUM_DEV_OUTPUT={staging}",
                ],
                cwd=source,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
                env={**os.environ, "AQUARIUM_DEV_GIT_SHA": git_sha},
            )
            try:
                stdout, stderr = process.communicate(
                    timeout=PRODUCER_BUILD_TIMEOUT_SECONDS
                )
            except subprocess.TimeoutExpired as error:
                _terminate_process_bounded(process)
                raise ManagerError(
                    "producer_build_timeout",
                    "The producer build exceeded its bounded execution time.",
                    "Inspect the producer, then run an explicitly approved rebuild.",
                    "build",
                    project_id,
                    git_sha,
                ) from error
        result = subprocess.CompletedProcess(
            process.args, process.returncode, stdout, stderr
        )
        if result.returncode != 0:
            raise ManagerError(
                "producer_build_failed",
                (result.stderr.strip() or "The producer build failed.")[:1000],
                "Repair the producer and run an explicitly approved rebuild.",
                "build",
                project_id,
                git_sha,
            )
        manifest = _read_single_json(result.stdout, project_id, git_sha)
        expected_version = f"{description['next_version']}-dev.{git_sha[:12]}"
        compared = {
            field: description[field]
            for field in _producer_identity_fields(description)
        }
        compared.update(git_sha=git_sha, development_version=expected_version)
        if any(manifest[field] != expected for field, expected in compared.items()):
            raise ManagerError(
                "producer_manifest_invalid",
                "The build manifest does not match the admitted producer and revision.",
                "Repair the producer identity fields and rebuild.",
                "validate",
                project_id,
                git_sha,
            )
        artifact = _contained_artifact(staging, manifest["artifact_path"])
        _validate_managed_service_bundle(artifact, manifest)
        observed_digest = artifact_digest(artifact)
        if observed_digest != manifest["sha256"]:
            raise ManagerError(
                "checksum_mismatch",
                "The declared artifact checksum does not match its bytes.",
                "Repair the producer checksum and rebuild.",
                "validate",
                project_id,
                git_sha,
            )
        _atomic_json(staging / MANIFEST_NAME, manifest)
        return staging, manifest
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def _manifest_from_generation(
    generation: Path, project_id: str, git_sha: str
) -> dict[str, Any]:
    manifest_path = generation / MANIFEST_NAME
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ManagerError(
            "artifact_invalid",
            "The immutable generation has no regular manager manifest.",
            "Remove the corrupt generation and rebuild.",
            "publish",
            project_id,
            git_sha,
        )
    try:
        return validate_manifest(json.loads(manifest_path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, ContractError) as error:
        raise ManagerError(
            "artifact_invalid",
            str(error),
            "Remove the corrupt generation and rebuild.",
            "publish",
            project_id,
            git_sha,
        ) from error


def _seal_generation(generation: Path) -> None:
    paths = [generation, *generation.rglob("*")]
    if any(path.is_symlink() for path in paths):
        raise OSError("an immutable generation contains a symbolic link")
    for path in reversed(paths):
        if path.stat().st_flags & stat.UF_IMMUTABLE:
            continue
        if path.is_dir():
            path.chmod(0o500)
        elif path.is_file():
            executable = bool(path.stat().st_mode & 0o111)
            path.chmod(0o500 if executable else 0o400)
        else:
            raise OSError("an immutable generation contains a special file")
        os.chflags(path, stat.UF_IMMUTABLE)


def _unseal_managed_tree(root: Path) -> None:
    for path in [root, *root.rglob("*")]:
        if path.is_symlink():
            continue
        os.chflags(path, 0)
        if path.is_dir():
            path.chmod(0o700)


def _temporary_selector(selector: Path, target: Path) -> Path:
    selector.parent.mkdir(parents=True, exist_ok=True)
    temporary = selector.parent / f".{selector.name}.{os.getpid()}.tmp"
    temporary.unlink(missing_ok=True)
    os.symlink(os.path.relpath(target, selector.parent), temporary)
    return temporary


def _generation_selector(
    host_root: Path, directory: str, project_id: str
) -> Path | None:
    selector = host_root / directory / project_id
    if not selector.exists() and not selector.is_symlink():
        return None
    if not selector.is_symlink():
        raise ManagerError(
            "artifact_invalid",
            f"The {directory} selector is not a symbolic link.",
            "Repair the development channel before continuing.",
            "diagnose",
            project_id,
        )
    try:
        generation = selector.resolve(strict=True)
    except OSError as error:
        raise ManagerError(
            "artifact_missing",
            str(error),
            "Rebuild the enrolled project to restore its selected artifact.",
            "diagnose",
            project_id,
        ) from error
    expected_parent = (host_root / "artifacts" / project_id).resolve()
    if (
        generation.parent != expected_parent
        or SHA_RE.fullmatch(generation.name) is None
    ):
        raise ManagerError(
            "artifact_invalid",
            f"The {directory} selector escapes the project artifact root.",
            "Repair the development channel before continuing.",
            "diagnose",
            project_id,
        )
    return generation


def _pending_generation(host_root: Path, project_id: str) -> Path | None:
    return _generation_selector(host_root, "pending", project_id)


def _publish_pending(host_root: Path, project_id: str, destination: Path) -> Path:
    pending = host_root / "pending" / project_id
    if pending.exists() and not pending.is_symlink():
        raise OSError(f"managed pending selector is not a symbolic link: {pending}")
    temporary = _temporary_selector(pending, destination)
    try:
        os.replace(temporary, pending)
    finally:
        temporary.unlink(missing_ok=True)
    return pending


def _service_lock(host_root: Path, project_id: str, operation: int):
    path = host_root / "locks" / "services" / f"{project_id}.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = path.open("a+b")
    try:
        fcntl.flock(stream.fileno(), operation)
    except OSError:
        stream.close()
        raise
    return stream


def _service_entrypoints(
    generation: Path, manifest: dict[str, Any]
) -> tuple[Path, Path]:
    artifact = _contained_artifact(generation, manifest["artifact_path"])
    entrypoints = _validate_managed_service_bundle(artifact, manifest)
    if entrypoints is None:
        raise ManagerError(
            "service_unavailable",
            "The selected generation is not a managed service.",
            "Use a managed-service producer generation.",
            "service",
            manifest["project_id"],
            manifest["git_sha"],
        )
    return entrypoints


def _controller_json(
    controller: Path,
    arguments: list[str],
    validator,
    project_id: str,
    git_sha: str,
) -> dict[str, Any]:
    try:
        result = subprocess.run(
            [os.fspath(controller), *arguments],
            capture_output=True,
            text=True,
            check=False,
            timeout=SERVICE_CONTROLLER_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ManagerError(
            "service_unavailable",
            f"The managed-service controller could not run: {error}",
            "Repair the producer controller and retry.",
            "service",
            project_id,
            git_sha,
        ) from error
    if result.returncode != 0:
        raise ManagerError(
            "service_activation_failed",
            (result.stderr.strip() or "The managed-service controller failed.")[:1000],
            "Inspect the producer-owned service recovery state before retrying.",
            "service",
            project_id,
            git_sha,
        )
    try:
        value = json.loads(result.stdout)
        validator(value)
    except (json.JSONDecodeError, ContractError) as error:
        raise ManagerError(
            "service_contract_invalid",
            str(error),
            "Repair the producer-owned Aquarium service controller.",
            "service",
            project_id,
            git_sha,
        ) from error
    if value["project_id"] != project_id:
        raise ManagerError(
            "service_contract_invalid",
            "The controller result belongs to another project.",
            "Repair the producer-owned Aquarium service controller.",
            "service",
            project_id,
            git_sha,
        )
    return value


def _publish_selectors(
    host_root: Path,
    project_id: str,
    destination: Path,
    manifest: dict[str, Any],
) -> Path | None:
    current = host_root / "current" / project_id
    command = host_root / "bin" / project_id
    artifact = destination / manifest["artifact_path"]
    if manifest["artifact_kind"] == "executable" and (
        artifact.is_symlink()
        or not artifact.is_file()
        or not os.access(artifact, os.X_OK)
    ):
        raise ManagerError(
            "artifact_invalid",
            "The executable artifact cannot be exposed through the development bin directory.",
            "Repair the producer output and rebuild the enrolled project.",
            "publish",
            project_id,
        )
    if manifest["artifact_kind"] == "managed-service":
        _validate_managed_service_bundle(artifact, manifest)
    command_temporary = None
    try:
        if manifest["artifact_kind"] in {"executable", "managed-service"}:
            command_target = current / manifest["artifact_path"]
            if manifest["artifact_kind"] == "managed-service":
                command_target /= manifest["command_path"]
            expected_target = os.path.relpath(command_target, command.parent)
            if command.exists() and not command.is_symlink():
                raise OSError(f"managed command is not a symbolic link: {command}")
            if not command.is_symlink() or os.readlink(command) != expected_target:
                command_temporary = _temporary_selector(command, command_target)
                os.replace(command_temporary, command)
        current_temporary = _temporary_selector(current, destination)
        try:
            os.replace(current_temporary, current)
        finally:
            current_temporary.unlink(missing_ok=True)
        return (
            command
            if manifest["artifact_kind"] in {"executable", "managed-service"}
            else None
        )
    finally:
        if command_temporary is not None:
            command_temporary.unlink(missing_ok=True)


def _publish(
    host_root: Path, staging: Path, manifest: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    project_id = manifest["project_id"]
    git_sha = manifest["git_sha"]
    destination = host_root / "artifacts" / project_id / git_sha
    current = host_root / "current" / project_id
    current.parent.mkdir(parents=True, exist_ok=True)
    previous_sha = None
    superseded_pending_sha = None
    if current.is_symlink():
        try:
            previous = current.resolve(strict=True)
            expected_parent = (host_root / "artifacts" / project_id).resolve()
            if previous.parent == expected_parent:
                previous_sha = previous.name
        except OSError:
            pass
    try:
        with _artifact_lock(host_root, project_id, git_sha, fcntl.LOCK_EX):
            if destination.exists():
                existing = _manifest_from_generation(destination, project_id, git_sha)
                artifact = _contained_artifact(destination, existing["artifact_path"])
                _validate_managed_service_bundle(artifact, existing)
                if (
                    existing != manifest
                    or artifact_digest(artifact) != manifest["sha256"]
                ):
                    raise ManagerError(
                        "artifact_invalid",
                        "The existing immutable generation conflicts with the build.",
                        "Remove the corrupt generation and rebuild.",
                        "publish",
                        project_id,
                        git_sha,
                    )
                shutil.rmtree(staging)
                status = "no-change"
            else:
                os.replace(staging, destination)
                status = "success"
            _seal_generation(destination)
            if manifest["artifact_kind"] == "managed-service":
                with _service_lock(host_root, project_id, fcntl.LOCK_EX):
                    selected = _current_generation(host_root, project_id)
                    previous_sha = selected.name if selected is not None else None
                    previous_pending = _pending_generation(host_root, project_id)
                    if previous_pending is not None:
                        superseded_pending_sha = previous_pending.name
                    if previous_sha == git_sha:
                        command = _publish_selectors(
                            host_root, project_id, destination, manifest
                        )
                        existing_pending = host_root / "pending" / project_id
                        if (
                            existing_pending.is_symlink()
                            and existing_pending.resolve(strict=True) == destination
                        ):
                            existing_pending.unlink()
                        pending = None
                    else:
                        pending = _publish_pending(host_root, project_id, destination)
                        command = None
            else:
                pending = None
                command = _publish_selectors(
                    host_root, project_id, destination, manifest
                )
        if (
            manifest["artifact_kind"] == "executable"
            and previous_sha is not None
            and previous_sha != git_sha
        ):
            cleanup_status, cleanup = cleanup_generation(
                project_id, previous_sha, host_root, wait=False
            )
            if cleanup_status == "no-change" and cleanup.get("leased"):
                _spawn_cleanup(host_root, project_id, previous_sha)
        if (
            superseded_pending_sha is not None
            and superseded_pending_sha != git_sha
            and superseded_pending_sha != previous_sha
        ):
            cleanup_status, cleanup = cleanup_generation(
                project_id, superseded_pending_sha, host_root, wait=False
            )
            if cleanup_status == "no-change" and cleanup.get("leased"):
                _spawn_cleanup(host_root, project_id, superseded_pending_sha)
        return status, {
            "project_id": project_id,
            "git_sha": git_sha,
            "development_version": manifest["development_version"],
            "artifact": str(destination / manifest["artifact_path"]),
            "current": str(current),
            "pending": str(pending) if pending is not None else None,
            "command": str(command) if command is not None else None,
            "sha256": manifest["sha256"],
            "superseded_git_sha": previous_sha,
            "superseded_pending_git_sha": superseded_pending_sha,
        }
    except ManagerError:
        raise
    except OSError as error:
        raise ManagerError(
            "publication_failed",
            str(error),
            "Inspect the host-local artifact and selector directories, then rebuild.",
            "publish",
            project_id,
            git_sha,
        ) from error
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def _service_target(host_root: Path, project_id: str) -> Path:
    target = _pending_generation(host_root, project_id)
    if target is None:
        target = _current_generation(host_root, project_id)
    if target is None:
        raise ManagerError(
            "service_unavailable",
            "The project has no current or pending managed-service generation.",
            "Publish one managed-service producer generation first.",
            "service",
            project_id,
        )
    return target


def _service_plan_unlocked(
    host_root: Path, project_id: str, target: Path
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    manifest = _manifest_from_generation(target, project_id, target.name)
    _, controller = _service_entrypoints(target, manifest)
    runtime_root = host_root / "runtime" / project_id
    status = _controller_json(
        controller,
        ["status", "--json", "--runtime-root", os.fspath(runtime_root)],
        validate_service_status,
        project_id,
        target.name,
    )
    plan = _controller_json(
        controller,
        [
            "plan",
            "--json",
            "--runtime-root",
            os.fspath(runtime_root),
            "--generation-root",
            os.fspath(target),
        ],
        validate_service_plan,
        project_id,
        target.name,
    )
    if (
        plan["target_git_sha"] != target.name
        or plan["active_git_sha"] != status["active_git_sha"]
        or plan["busy"] != status["busy"]
    ):
        raise ManagerError(
            "service_contract_invalid",
            "The controller plan does not match its observed service status.",
            "Repair the producer-owned Aquarium service controller.",
            "service",
            project_id,
            target.name,
        )
    return manifest, status, plan


def plan_managed_service(
    project_id: str, host_root: Path
) -> tuple[str, dict[str, Any]]:
    if project_id not in PROJECT_IDS:
        raise ManagerError(
            "invalid_arguments",
            "The service project ID is unsupported.",
            "Use one project ID from the shared development contract.",
            "service",
        )
    target = _service_target(host_root, project_id)
    with _service_lock(host_root, project_id, fcntl.LOCK_SH):
        if _service_target(host_root, project_id) != target:
            raise ManagerError(
                "lease_unavailable",
                "The target generation changed while service planning began.",
                "Plan the managed service again.",
                "service",
                project_id,
                target.name,
            )
        _, status, plan = _service_plan_unlocked(host_root, project_id, target)
    return "diagnosed", {
        "project_id": project_id,
        "target_git_sha": target.name,
        "runtime_root": str(host_root / "runtime" / project_id),
        "status": status,
        "plan": plan,
    }


def apply_managed_service(
    project_id: str,
    host_root: Path,
    plan_token: str,
    *,
    approve_service: bool,
) -> tuple[str, dict[str, Any]]:
    if not approve_service:
        raise ManagerError(
            "approval_required",
            "Managed-service activation approval is required.",
            "Approve only the exact controller plan token displayed by service-plan.",
            "service",
            project_id if project_id in PROJECT_IDS else None,
        )
    if project_id not in PROJECT_IDS:
        raise ManagerError(
            "invalid_arguments",
            "The service project ID is unsupported.",
            "Use one project ID from the shared development contract.",
            "service",
        )
    target = _service_target(host_root, project_id)
    previous_sha = None
    with _service_lock(host_root, project_id, fcntl.LOCK_EX):
        if _service_target(host_root, project_id) != target:
            raise ManagerError(
                "lease_unavailable",
                "The target generation changed before service activation.",
                "Run service-plan again and approve its new exact token.",
                "service",
                project_id,
                target.name,
            )
        manifest, status, plan = _service_plan_unlocked(host_root, project_id, target)
        if plan["action"] == "defer":
            return "no-change", {
                "project_id": project_id,
                "target_git_sha": target.name,
                "deferred": True,
                "status": status,
                "plan": plan,
            }
        if plan["plan_token"] != plan_token:
            raise ManagerError(
                "approval_required",
                "The supplied service plan token is absent or stale.",
                "Run service-plan again and approve its exact current token.",
                "service",
                project_id,
                target.name,
            )
        current = _current_generation(host_root, project_id)
        previous_sha = current.name if current is not None else None
        if plan["action"] == "no-change":
            result = {
                "schema": "aquarium-dev-service-result/v1",
                "project_id": project_id,
                "status": "no-change",
                "active_git_sha": target.name,
                "recovery_required": False,
            }
        else:
            _, controller = _service_entrypoints(target, manifest)
            result = _controller_json(
                controller,
                [
                    "apply",
                    "--json",
                    "--runtime-root",
                    os.fspath(host_root / "runtime" / project_id),
                    "--generation-root",
                    os.fspath(target),
                    "--plan-token",
                    plan_token,
                ],
                validate_service_result,
                project_id,
                target.name,
            )
        if result["active_git_sha"] != target.name or result["recovery_required"]:
            raise ManagerError(
                "service_activation_failed",
                "The controller did not activate the exact target generation.",
                "Inspect the producer-owned service recovery state before retrying.",
                "service",
                project_id,
                target.name,
            )
        _, controller = _service_entrypoints(target, manifest)
        observed = _controller_json(
            controller,
            [
                "status",
                "--json",
                "--runtime-root",
                os.fspath(host_root / "runtime" / project_id),
            ],
            validate_service_status,
            project_id,
            target.name,
        )
        if (
            observed["active_git_sha"] != target.name
            or observed["state"] not in {"ready", "busy"}
            or observed["recovery_required"]
        ):
            raise ManagerError(
                "service_activation_failed",
                "The activated service did not become ready at the target generation.",
                "Inspect the producer-owned service recovery state before retrying.",
                "service",
                project_id,
                target.name,
            )
        command = _publish_selectors(host_root, project_id, target, manifest)
        pending = host_root / "pending" / project_id
        if pending.is_symlink() and pending.resolve(strict=True) == target:
            pending.unlink()
    if previous_sha is not None and previous_sha != target.name:
        cleanup_status, cleanup = cleanup_generation(
            project_id, previous_sha, host_root, wait=False
        )
        if cleanup_status == "no-change" and cleanup.get("leased"):
            _spawn_cleanup(host_root, project_id, previous_sha)
    return ("no-change" if plan["action"] == "no-change" else "success"), {
        "project_id": project_id,
        "git_sha": target.name,
        "command": str(command),
        "result": result,
        "status": observed,
        "superseded_git_sha": previous_sha,
    }


def _write_diagnostic(host_root: Path, error: ManagerError) -> None:
    if error.project_id is None:
        return
    _atomic_json(
        host_root / "diagnostics" / error.project_id / "latest.json",
        {
            "schema": DIAGNOSTIC_SCHEMA,
            "project_id": error.project_id,
            "git_sha": error.git_sha,
            "stage": error.stage,
            "code": error.code,
            "message": error.message[:1000],
            "action": error.action[:1000],
        },
    )


def _publisher_lock(host_root: Path, project_id: str):
    path = host_root / "locks" / "publisher" / f"{project_id}.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = path.open("a+b")
    fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
    return stream


def _enrollment_lock(host_root: Path, project_id: str):
    path = host_root / "locks" / "enrollment" / f"{project_id}.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = path.open("a+b")
    fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
    return stream


def _artifact_lock_path(host_root: Path, project_id: str, git_sha: str) -> Path:
    return host_root / "locks" / "artifacts" / project_id / f"{git_sha}.lock"


def _artifact_lock(host_root: Path, project_id: str, git_sha: str, operation: int):
    path = _artifact_lock_path(host_root, project_id, git_sha)
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = path.open("a+b")
    try:
        fcntl.flock(stream.fileno(), operation)
    except OSError:
        stream.close()
        raise
    return stream


@contextmanager
def lease_current_generation(host_root: Path, project_id: str):
    if project_id not in PROJECT_IDS:
        raise ManagerError(
            "invalid_arguments",
            "The lease project ID is unsupported.",
            "Use one enrolled development project ID.",
            "lease",
        )
    generation = _current_generation(host_root, project_id)
    if generation is None:
        raise ManagerError(
            "artifact_missing",
            "The enrolled project has no selected development generation.",
            "Publish the enrolled project before launching a consumer.",
            "lease",
            project_id,
        )
    lease = _artifact_lock(host_root, project_id, generation.name, fcntl.LOCK_SH)
    try:
        if _current_generation(host_root, project_id) != generation:
            raise ManagerError(
                "lease_unavailable",
                "The selected generation changed while its lease was acquired.",
                "Resolve the current generation again before launching the consumer.",
                "lease",
                project_id,
                generation.name,
            )
        yield generation
    finally:
        lease.close()


def _current_generation(host_root: Path, project_id: str) -> Path | None:
    return _generation_selector(host_root, "current", project_id)


def _validate_generation(
    generation: Path,
    project_id: str,
    description: dict[str, Any],
) -> tuple[Path, dict[str, Any]]:
    git_sha = generation.name
    manifest = _manifest_from_generation(generation, project_id, git_sha)
    expected = {
        field: description[field] for field in _producer_identity_fields(description)
    }
    expected.update(
        git_sha=git_sha,
        development_version=f"{description['next_version']}-dev.{git_sha[:12]}",
    )
    if any(manifest[field] != value for field, value in expected.items()):
        raise ManagerError(
            "artifact_invalid",
            "The current generation does not match its enrollment or producer.",
            "Rebuild the enrolled project from its canonical local main.",
            "diagnose",
            project_id,
            git_sha if len(git_sha) == 40 else None,
        )
    artifact = _contained_artifact(generation, manifest["artifact_path"])
    _validate_managed_service_bundle(artifact, manifest)
    if artifact_digest(artifact) != manifest["sha256"]:
        raise ManagerError(
            "checksum_mismatch",
            "The current artifact checksum no longer matches its manifest.",
            "Rebuild the enrolled project from its canonical local main.",
            "diagnose",
            project_id,
            git_sha,
        )
    return artifact, manifest


def _spawn_cleanup(host_root: Path, project_id: str, git_sha: str) -> None:
    subprocess.Popen(
        [
            os.fspath(Path(os.sys.executable).resolve()),
            os.fspath(Path(__file__).with_name("aquarium_dev.py").resolve()),
            "--host-root",
            os.fspath(host_root),
            "cleanup",
            "--project-id",
            project_id,
            "--git-sha",
            git_sha,
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )


def cleanup_generation(
    project_id: str, git_sha: str, host_root: Path, *, wait: bool
) -> tuple[str, dict[str, Any]]:
    if project_id not in PROJECT_IDS or not SHA_RE.fullmatch(git_sha):
        raise ManagerError(
            "invalid_arguments",
            "Cleanup requires one supported project ID and full lowercase Git SHA.",
            "Use identities returned by the development artifact manifest.",
            "cleanup",
        )
    operation = fcntl.LOCK_EX if wait else fcntl.LOCK_EX | fcntl.LOCK_NB
    try:
        lease = _artifact_lock(host_root, project_id, git_sha, operation)
    except BlockingIOError:
        return "no-change", {"git_sha": git_sha, "leased": True}
    with lease:
        current = _current_generation(host_root, project_id)
        if current is not None and current.name == git_sha:
            return "no-change", {"git_sha": git_sha, "current": True}
        pending = _pending_generation(host_root, project_id)
        if pending is not None and pending.name == git_sha:
            return "no-change", {"git_sha": git_sha, "pending": True}
        generation = host_root / "artifacts" / project_id / git_sha
        if generation.exists():
            if generation.is_symlink() or not generation.is_dir():
                raise ManagerError(
                    "artifact_invalid",
                    "The cleanup target is not an immutable generation directory.",
                    "Inspect the host-local artifact root before retrying cleanup.",
                    "cleanup",
                    project_id,
                    git_sha,
                )
            for managed_path in (generation,):
                if not managed_path.exists() or managed_path.is_symlink():
                    continue
                _unseal_managed_tree(managed_path)
            shutil.rmtree(generation)
            return "success", {"git_sha": git_sha, "removed": True}
        return "no-change", {"git_sha": git_sha, "removed": False}


def _build_current(repository: Path, host_root: Path) -> tuple[str, dict[str, Any]]:
    checkout, _, description, git_sha = _require_enrolled_checkout(
        repository, host_root, require_clean=True
    )
    project_id = description["project_id"]
    with _publisher_lock(host_root, project_id):
        checkout, _, description, observed_sha = _require_enrolled_checkout(
            checkout, host_root, require_clean=True
        )
        if observed_sha != git_sha:
            raise ManagerError(
                "sha_mismatch",
                "Local main changed after the build request was admitted.",
                "Queue the new completed local-main revision.",
                "schedule",
                project_id,
                git_sha,
            )
        staging, manifest = _validated_build(checkout, host_root, description, git_sha)
        return _publish(host_root, staging, manifest)


def rebuild(
    repository: Path, host_root: Path, *, approve_build: bool
) -> tuple[str, dict[str, Any]]:
    if not approve_build:
        raise ManagerError(
            "approval_required",
            "Explicit build approval is required.",
            "Approve one rebuild of the diagnosed current local-main revision.",
            "build",
        )
    try:
        return _build_current(repository, host_root)
    except ManagerError as error:
        _write_diagnostic(host_root, error)
        raise


def queue_request(
    repository: Path,
    host_root: Path,
    manager_script: Path,
    *,
    spawn_worker: bool = True,
) -> tuple[str, dict[str, Any]]:
    try:
        checkout, _, description, git_sha = _require_enrolled_checkout(
            repository, host_root, require_clean=True
        )
    except ManagerError as error:
        _write_diagnostic(host_root, error)
        raise
    project_id = description["project_id"]
    target = host_root / "queue" / project_id / f"{git_sha}.json"
    request = {
        "schema": QUEUE_SCHEMA,
        "project_id": project_id,
        "git_sha": git_sha,
        "checkout": str(checkout),
    }
    status = "no-change" if target.exists() else "success"
    if not target.exists():
        _atomic_json(target, request)
    if spawn_worker:
        subprocess.Popen(
            [
                os.fspath(Path(os.sys.executable).resolve()),
                os.fspath(manager_script.resolve()),
                "--host-root",
                os.fspath(host_root),
                "worker",
                "--project-id",
                project_id,
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True,
        )
    return status, {
        "project_id": project_id,
        "git_sha": git_sha,
        "queued": str(target),
    }


def _quarantine_build_request(
    host_root: Path, project_id: str, request_path: Path
) -> Path:
    quarantine = host_root / "queue-failures" / project_id
    quarantine.mkdir(parents=True, exist_ok=True)
    destination = quarantine / f"{request_path.stem}.{time.time_ns()}.json"
    os.replace(request_path, destination)
    return destination


def process_queue(project_id: str, host_root: Path) -> tuple[str, dict[str, Any]]:
    if project_id not in PROJECT_IDS:
        raise ManagerError(
            "invalid_arguments",
            "The worker project ID is unsupported.",
            "Use one project ID from the shared development contract.",
            "schedule",
        )
    queue = host_root / "queue" / project_id
    processed = 0
    published = 0
    quarantined = 0
    latest: dict[str, Any] = {}
    first_failure: ManagerError | None = None
    with _publisher_lock(host_root, project_id):
        for request_path in sorted(queue.glob("*.json")) if queue.exists() else []:
            processed += 1
            try:
                if request_path.is_symlink() or not request_path.is_file():
                    error = ManagerError(
                        "invalid_arguments",
                        "The queued build request is not one regular file.",
                        "Queue the current completed local-main revision again.",
                        "schedule",
                        project_id,
                    )
                    _quarantine_build_request(host_root, project_id, request_path)
                    quarantined += 1
                    raise error
                request = json.loads(request_path.read_text(encoding="utf-8"))
                expected_fields = {"schema", "project_id", "git_sha", "checkout"}
                if (
                    not isinstance(request, dict)
                    or set(request) != expected_fields
                    or request.get("schema") != QUEUE_SCHEMA
                    or request.get("project_id") != project_id
                    or not isinstance(request.get("checkout"), str)
                    or not request["checkout"]
                    or "\0" in request["checkout"]
                    or not isinstance(request.get("git_sha"), str)
                    or SHA_RE.fullmatch(request["git_sha"]) is None
                ):
                    error = ManagerError(
                        "invalid_arguments",
                        "The queued build request is invalid.",
                        "Remove the invalid request and queue the current revision again.",
                        "schedule",
                        project_id,
                        request.get("git_sha") if isinstance(request, dict) else None,
                    )
                    _quarantine_build_request(host_root, project_id, request_path)
                    quarantined += 1
                    raise error
                checkout, _, description, git_sha = _require_enrolled_checkout(
                    Path(request["checkout"]), host_root, require_clean=True
                )
                if description["project_id"] != project_id:
                    error = ManagerError(
                        "invalid_arguments",
                        "The queued checkout belongs to another enrolled project.",
                        "Queue the checkout through its matching project worker.",
                        "schedule",
                        project_id,
                        request["git_sha"],
                    )
                    _quarantine_build_request(host_root, project_id, request_path)
                    quarantined += 1
                    raise error
                if git_sha != request["git_sha"]:
                    error = ManagerError(
                        "sha_mismatch",
                        "The queued revision is no longer the completed local-main revision.",
                        "Queue the current completed local-main revision.",
                        "schedule",
                        project_id,
                        request["git_sha"],
                    )
                    _quarantine_build_request(host_root, project_id, request_path)
                    quarantined += 1
                    raise error
                staging, manifest = _validated_build(
                    checkout, host_root, description, git_sha
                )
                _, latest = _publish(host_root, staging, manifest)
                published += 1
                request_path.unlink(missing_ok=True)
            except ManagerError as error:
                _write_diagnostic(host_root, error)
                if first_failure is None:
                    first_failure = error
            except json.JSONDecodeError as error:
                try:
                    _quarantine_build_request(host_root, project_id, request_path)
                    quarantined += 1
                except OSError as quarantine_error:
                    wrapped = ManagerError(
                        "worker_failed",
                        str(quarantine_error),
                        "Inspect the queue path and retry the preserved request.",
                        "schedule",
                        project_id,
                    )
                    _write_diagnostic(host_root, wrapped)
                    if first_failure is None:
                        first_failure = wrapped
                    continue
                wrapped = ManagerError(
                    "invalid_arguments",
                    str(error),
                    "Queue the current completed local-main revision again.",
                    "schedule",
                    project_id,
                )
                _write_diagnostic(host_root, wrapped)
                if first_failure is None:
                    first_failure = wrapped
            except OSError as error:
                wrapped = ManagerError(
                    "worker_failed",
                    str(error),
                    "Inspect the worker diagnostic and retry the preserved request.",
                    "schedule",
                    project_id,
                )
                _write_diagnostic(host_root, wrapped)
                if first_failure is None:
                    first_failure = wrapped
    if first_failure is not None:
        raise first_failure
    return "success", {
        "processed": processed,
        "published": published,
        "quarantined": quarantined,
        **latest,
    }
