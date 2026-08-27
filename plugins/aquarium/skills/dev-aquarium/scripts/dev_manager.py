"""Host-local lifecycle manager for dev-aquarium."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import platform
import shlex
import shutil
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dev_contract import (
    PROJECT_IDS,
    ContractError,
    validate_description,
    validate_manifest,
)

ENROLLMENT_SCHEMA = "aquarium-dev-enrollment/v1"
MARKER_START = "# BEGIN AQUARIUM DEV v1"
MARKER_END = "# END AQUARIUM DEV v1"
MANIFEST_NAME = ".aquarium-manifest.json"
QUEUE_SCHEMA = "aquarium-dev-build-request/v1"
DIAGNOSTIC_SCHEMA = "aquarium-dev-diagnostic/v1"


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


def _atomic_json(path: Path, value: dict[str, Any], mode: int = 0o600) -> None:
    _atomic_write(path, json.dumps(value, sort_keys=True, indent=2) + "\n", mode)


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
    """Return the v1 digest for one regular file or canonical directory tree."""
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


def _read_single_json(stdout: str, project_id: str, git_sha: str) -> dict[str, Any]:
    try:
        value = json.loads(stdout)
        return validate_manifest(value)
    except (json.JSONDecodeError, ContractError) as error:
        raise ManagerError(
            "producer_manifest_invalid",
            str(error),
            "Repair aquarium-dev-build to emit one valid v1 manifest.",
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
        result = subprocess.run(
            [
                "make",
                "-s",
                "aquarium-dev-build",
                f"AQUARIUM_DEV_OUTPUT={staging}",
            ],
            cwd=checkout,
            capture_output=True,
            text=True,
            check=False,
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
            "project_id": project_id,
            "git_sha": git_sha,
            "development_version": expected_version,
            "artifact_kind": description["artifact_kind"],
            "artifact_path": description["artifact_path"],
        }
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


def _publish(
    host_root: Path, staging: Path, manifest: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    project_id = manifest["project_id"]
    git_sha = manifest["git_sha"]
    destination = host_root / "artifacts" / project_id / git_sha
    current = host_root / "current" / project_id
    current.parent.mkdir(parents=True, exist_ok=True)
    try:
        if destination.exists():
            existing = _manifest_from_generation(destination, project_id, git_sha)
            artifact = _contained_artifact(destination, existing["artifact_path"])
            if existing != manifest or artifact_digest(artifact) != manifest["sha256"]:
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
        temporary = current.parent / f".{project_id}.{os.getpid()}.tmp"
        temporary.unlink(missing_ok=True)
        os.symlink(os.path.relpath(destination, current.parent), temporary)
        os.replace(temporary, current)
        return status, {
            "project_id": project_id,
            "git_sha": git_sha,
            "development_version": manifest["development_version"],
            "artifact": str(destination / manifest["artifact_path"]),
            "current": str(current),
            "sha256": manifest["sha256"],
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
    latest: dict[str, Any] = {}
    with _publisher_lock(host_root, project_id):
        for request_path in sorted(queue.glob("*.json")) if queue.exists() else []:
            processed += 1
            try:
                request = json.loads(request_path.read_text(encoding="utf-8"))
                expected_fields = {"schema", "project_id", "git_sha", "checkout"}
                if (
                    not isinstance(request, dict)
                    or set(request) != expected_fields
                    or request.get("schema") != QUEUE_SCHEMA
                    or request.get("project_id") != project_id
                ):
                    raise ManagerError(
                        "invalid_arguments",
                        "The queued build request is invalid.",
                        "Remove the invalid request and queue the current revision again.",
                        "schedule",
                        project_id,
                        request.get("git_sha") if isinstance(request, dict) else None,
                    )
                checkout, _, description, git_sha = _require_enrolled_checkout(
                    Path(request["checkout"]), host_root, require_clean=True
                )
                if git_sha != request["git_sha"]:
                    raise ManagerError(
                        "sha_mismatch",
                        "The queued revision is no longer the completed local-main revision.",
                        "Queue the current completed local-main revision.",
                        "schedule",
                        project_id,
                        request["git_sha"],
                    )
                staging, manifest = _validated_build(
                    checkout, host_root, description, git_sha
                )
                _, latest = _publish(host_root, staging, manifest)
                published += 1
            except ManagerError as error:
                _write_diagnostic(host_root, error)
            except (OSError, json.JSONDecodeError) as error:
                wrapped = ManagerError(
                    "invalid_arguments",
                    str(error),
                    "Queue the current completed local-main revision again.",
                    "schedule",
                    project_id,
                )
                _write_diagnostic(host_root, wrapped)
            finally:
                request_path.unlink(missing_ok=True)
    return "success", {
        "processed": processed,
        "published": published,
        **latest,
    }
