"""Host-local lifecycle manager for dev-aquarium."""

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
from contextlib import ExitStack
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Self

from dev_contract import (
    PROJECT_IDS,
    SHA_RE,
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
MCP_ARGUMENTS = {
    "mulgae": lambda checkout: ["mcp", "--project-root", str(checkout)],
    "gaori": lambda checkout: ["--repo", str(checkout), "mcp"],
}
CODEX_COMMAND_TIMEOUT_SECONDS = 120


@dataclass
class ManagerError(Exception):
    code: str
    message: str
    action: str
    stage: str
    project_id: str | None = None
    git_sha: str | None = None


@dataclass
class ResolvedArtifact:
    project_id: str
    source: str
    path: Path
    git_sha: str | None
    development_version: str | None
    sha256: str | None
    artifact_kind: str | None
    execution_path: Path | None = None
    lease: Any = None

    def close(self) -> None:
        if self.lease is not None:
            fcntl.flock(self.lease.fileno(), fcntl.LOCK_UN)
            self.lease.close()
            self.lease = None

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


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


def _codex_environment(host_root: Path) -> dict[str, str]:
    environment = os.environ.copy()
    environment["CODEX_HOME"] = str(host_root / "codex")
    return environment


def _run_codex(
    codex_bin: str,
    host_root: Path,
    *arguments: str,
    json_output: bool = False,
    check: bool = True,
    timeout_seconds: float = CODEX_COMMAND_TIMEOUT_SECONDS,
) -> Any:
    command = [codex_bin, *arguments]
    process = subprocess.Popen(
        command,
        env=_codex_environment(host_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as error:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.communicate(timeout=1)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate(timeout=1)
        raise ManagerError(
            "codex_not_configured",
            f"Codex did not finish within {timeout_seconds:g} seconds.",
            "Inspect the isolated Codex home and retry approved configuration.",
            "configure-codex",
            "aquarium",
        ) from error
    result = subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
    if check and result.returncode != 0:
        raise ManagerError(
            "codex_not_configured",
            (
                result.stderr.strip()
                or result.stdout.strip()
                or "Codex rejected configuration."
            )[:1000],
            "Inspect the isolated Codex home and retry approved configuration.",
            "configure-codex",
            "aquarium",
        )
    if not json_output:
        return result
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise ManagerError(
            "codex_not_configured",
            "Codex did not return the expected JSON result.",
            "Use a supported Codex CLI and retry approved configuration.",
            "configure-codex",
            "aquarium",
        ) from error


def codex_diagnosis(host_root: Path, codex_bin: str) -> dict[str, Any]:
    codex_home = host_root / "codex"
    login_action = f"CODEX_HOME={codex_home} codex login"
    if not codex_home.exists():
        return {
            "home": str(codex_home),
            "configured": False,
            "login": "required",
            "login_action": login_action,
            "plugin": None,
            "paired_skills": None,
            "mcp_servers": [],
        }
    try:
        plugins = _run_codex(
            codex_bin, host_root, "plugin", "list", "--json", json_output=True
        )
        servers = _run_codex(
            codex_bin, host_root, "mcp", "list", "--json", json_output=True
        )
        installed = [
            {
                "plugin_id": item.get("pluginId"),
                "version": item.get("version"),
                "enabled": item.get("enabled"),
            }
            for item in plugins.get("installed", [])
            if item.get("pluginId") == "aquarium@root-kernel"
        ]
        mcp_names = sorted(
            item.get("name")
            for item in servers
            if item.get("name") in MCP_ARGUMENTS and item.get("enabled") is True
        )
        login = _run_codex(
            codex_bin, host_root, "login", "status", check=False
        ).returncode
        return {
            "home": str(codex_home),
            "configured": len(installed) == 1,
            "login": "ready" if login == 0 else "required",
            "login_action": None if login == 0 else login_action,
            "plugin": installed[0] if len(installed) == 1 else None,
            "paired_skills": (
                {
                    "source": "aquarium-plugin",
                    "version": installed[0]["version"],
                }
                if len(installed) == 1
                else None
            ),
            "mcp_servers": mcp_names,
        }
    except ManagerError as error:
        return {
            "home": str(codex_home),
            "configured": False,
            "login": "unknown",
            "login_action": login_action,
            "plugin": None,
            "paired_skills": None,
            "mcp_servers": [],
            "error": error.code,
        }


def _snapshot_codex_configuration(codex_home: Path, snapshot: Path) -> None:
    snapshot.chmod(0o700)
    for name in ("config.toml", "plugins", "fake-state.json"):
        source = codex_home / name
        if source.is_symlink():
            raise ManagerError(
                "codex_not_configured",
                f"The isolated Codex {name} state is a symbolic link.",
                "Replace the linked state before retrying approved configuration.",
                "configure-codex",
                "aquarium",
            )
        if not source.exists():
            continue
        target = snapshot / name
        if source.is_dir():
            shutil.copytree(source, target, symlinks=True)
        elif source.is_file():
            shutil.copy2(source, target)
        else:
            raise ManagerError(
                "codex_not_configured",
                f"The isolated Codex {name} state is not regular.",
                "Repair the isolated state before retrying approved configuration.",
                "configure-codex",
                "aquarium",
            )


def _restore_codex_configuration(codex_home: Path, snapshot: Path) -> None:
    for name in ("config.toml", "plugins", "fake-state.json"):
        current = codex_home / name
        saved = snapshot / name
        if current.is_symlink() or current.is_file():
            current.unlink()
        elif current.is_dir():
            shutil.rmtree(current)
        if saved.is_dir():
            shutil.copytree(saved, current, symlinks=True)
        elif saved.is_file():
            shutil.copy2(saved, current)


def _recover_codex_transaction(codex_home: Path, transaction: Path) -> None:
    if not transaction.is_dir() or transaction.is_symlink():
        return
    active = transaction / "active"
    if not active.is_file() or active.is_symlink():
        shutil.rmtree(transaction)
        return
    mode_file = transaction / "home-mode"
    if not mode_file.is_file() or mode_file.is_symlink():
        raise ManagerError(
            "codex_not_configured",
            "The interrupted Codex configuration has invalid recovery metadata.",
            "Inspect the isolated transaction before retrying configuration.",
            "configure-codex",
            "aquarium",
        )
    try:
        home_mode = int(mode_file.read_text(encoding="ascii"), 8)
    except ValueError as error:
        raise ManagerError(
            "codex_not_configured",
            "The interrupted Codex configuration has an invalid home mode.",
            "Inspect the isolated transaction before retrying configuration.",
            "configure-codex",
            "aquarium",
        ) from error
    codex_home.mkdir(parents=True, exist_ok=True, mode=home_mode)
    _restore_codex_configuration(codex_home, transaction)
    codex_home.chmod(home_mode)
    shutil.rmtree(transaction)


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
            if generation is None:
                projects.append({"project_id": project_id, "state": "artifact-missing"})
                continue
            artifact, manifest = _validate_generation(
                generation, project_id, description
            )
            projects.append(
                {
                    "project_id": project_id,
                    "state": "development",
                    "checkout": str(checkout),
                    "git_sha": manifest["git_sha"],
                    "development_version": manifest["development_version"],
                    "artifact": str(artifact),
                    "sha256": manifest["sha256"],
                }
            )
        except ManagerError as error:
            projects.append(
                {"project_id": project_id, "state": "broken", "error": error.code}
            )
    return projects


def diagnose(
    repository: Path, host_root: Path, codex_bin: str = "codex"
) -> dict[str, Any]:
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
            if generation is not None:
                artifact, manifest = _validate_generation(
                    generation, project_id, description
                )
                current = {
                    "state": "healthy",
                    "git_sha": manifest["git_sha"],
                    "development_version": manifest["development_version"],
                    "artifact": str(artifact),
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
        "codex": codex_diagnosis(host_root, codex_bin),
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

        if (
            existing is not None
            and Path(existing["checkout"]) == checkout
            and existing["hook_block"] == block
        ):
            return "no-change", diagnosis

        target = enrollment_path(host_root, project_id)
        managed_paths = {hook, target}
        if existing is not None:
            managed_paths.add(Path(existing["hook_path"]))
        snapshots = {path: _file_snapshot(path) for path in managed_paths}
        try:
            hook_changed = _install_block(hook, block)
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


def _publish(
    host_root: Path, staging: Path, manifest: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    project_id = manifest["project_id"]
    git_sha = manifest["git_sha"]
    destination = host_root / "artifacts" / project_id / git_sha
    current = host_root / "current" / project_id
    current.parent.mkdir(parents=True, exist_ok=True)
    previous_sha = None
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
            if manifest["artifact_kind"] == "executable":
                _execution_alias(
                    host_root,
                    project_id,
                    git_sha,
                    destination / manifest["artifact_path"],
                )
            _seal_generation(destination)
            temporary = current.parent / f".{project_id}.{os.getpid()}.tmp"
            temporary.unlink(missing_ok=True)
            os.symlink(os.path.relpath(destination, current.parent), temporary)
            os.replace(temporary, current)
        if (
            project_id != "aquarium"
            and previous_sha is not None
            and previous_sha != git_sha
        ):
            cleanup_status, cleanup = cleanup_generation(
                project_id, previous_sha, host_root, wait=False
            )
            if cleanup_status == "no-change" and cleanup.get("leased"):
                _spawn_cleanup(host_root, project_id, previous_sha)
        return status, {
            "project_id": project_id,
            "git_sha": git_sha,
            "development_version": manifest["development_version"],
            "artifact": str(destination / manifest["artifact_path"]),
            "current": str(current),
            "sha256": manifest["sha256"],
            "superseded_git_sha": previous_sha,
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


def _current_generation(host_root: Path, project_id: str) -> Path | None:
    current = host_root / "current" / project_id
    if not current.exists() and not current.is_symlink():
        return None
    if not current.is_symlink():
        raise ManagerError(
            "artifact_invalid",
            "The current selector is not a symbolic link.",
            "Repair the development channel by rebuilding the enrolled project.",
            "resolve",
            project_id,
        )
    try:
        generation = current.resolve(strict=True)
    except OSError as error:
        raise ManagerError(
            "artifact_missing",
            str(error),
            "Rebuild the enrolled project to restore its current artifact.",
            "resolve",
            project_id,
        ) from error
    expected_parent = (host_root / "artifacts" / project_id).resolve()
    if generation.parent != expected_parent:
        raise ManagerError(
            "artifact_invalid",
            "The current selector escapes the enrolled project's artifact root.",
            "Repair the development channel by rebuilding the enrolled project.",
            "resolve",
            project_id,
        )
    return generation


def _validate_generation(
    generation: Path,
    project_id: str,
    description: dict[str, Any],
) -> tuple[Path, dict[str, Any]]:
    git_sha = generation.name
    manifest = _manifest_from_generation(generation, project_id, git_sha)
    expected = {
        "project_id": project_id,
        "git_sha": git_sha,
        "development_version": f"{description['next_version']}-dev.{git_sha[:12]}",
        "artifact_kind": description["artifact_kind"],
        "artifact_path": description["artifact_path"],
    }
    if any(manifest[field] != value for field, value in expected.items()):
        raise ManagerError(
            "artifact_invalid",
            "The current generation does not match its enrollment or producer.",
            "Rebuild the enrolled project from its canonical local main.",
            "resolve",
            project_id,
            git_sha if len(git_sha) == 40 else None,
        )
    artifact = _contained_artifact(generation, manifest["artifact_path"])
    if artifact_digest(artifact) != manifest["sha256"]:
        raise ManagerError(
            "checksum_mismatch",
            "The current artifact checksum no longer matches its manifest.",
            "Rebuild the enrolled project from its canonical local main.",
            "resolve",
            project_id,
            git_sha,
        )
    return artifact, manifest


def _execution_alias(
    host_root: Path, project_id: str, git_sha: str, artifact: Path
) -> Path:
    root = host_root / "runtime" / project_id / git_sha
    target = root / "executable"
    try:
        if target.exists():
            if (
                target.is_symlink()
                or not target.is_file()
                or not os.path.samefile(artifact, target)
            ):
                raise OSError("the guarded execution alias has changed identity")
            if not target.stat().st_flags & stat.UF_IMMUTABLE:
                os.chflags(target, stat.UF_IMMUTABLE)
            if not root.stat().st_flags & stat.UF_IMMUTABLE:
                root.chmod(0o500)
                os.chflags(root, stat.UF_IMMUTABLE)
            return target
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chflags(root, 0)
        root.chmod(0o700)
        temporary = root / f".executable.{os.getpid()}.tmp"
        temporary.unlink(missing_ok=True)
        os.link(artifact, temporary, follow_symlinks=False)
        if not os.path.samefile(artifact, temporary):
            raise OSError("the guarded execution alias does not bind the artifact")
        os.replace(temporary, target)
        root.chmod(0o500)
        os.chflags(target, stat.UF_IMMUTABLE)
        os.chflags(root, stat.UF_IMMUTABLE)
        return target
    except OSError as error:
        raise ManagerError(
            "artifact_invalid",
            str(error),
            "Rebuild the enrolled project from its canonical local main.",
            "resolve",
            project_id,
            git_sha,
        ) from error


def resolve_artifact(
    project_id: str, host_root: Path, stable: Path | None = None
) -> ResolvedArtifact:
    if project_id not in PROJECT_IDS:
        raise ManagerError(
            "invalid_arguments",
            "The requested project ID is unsupported.",
            "Use one project ID from the shared development contract.",
            "resolve",
        )
    enrollment = read_enrollment(host_root, project_id)
    if enrollment is None:
        if stable is None:
            raise ManagerError(
                "enrollment_missing",
                "No development enrollment or stable fallback was supplied.",
                "Supply the stable tool path or enroll a canonical checkout.",
                "resolve",
                project_id,
            )
        try:
            path = stable.resolve(strict=True)
        except OSError as error:
            raise ManagerError(
                "artifact_missing",
                str(error),
                "Supply an existing stable tool path.",
                "resolve",
                project_id,
            ) from error
        return ResolvedArtifact(
            project_id, "stable", path, None, None, None, None, path
        )

    checkout = Path(enrollment["checkout"])
    diagnosed_checkout, _, _, _ = _repository_identity(checkout)
    description = _describe(diagnosed_checkout)
    if description["project_id"] != project_id:
        raise ManagerError(
            "enrollment_broken",
            "The enrolled checkout now describes a different project.",
            "Repair enrollment before resolving a development artifact.",
            "resolve",
            project_id,
        )
    generation = _current_generation(host_root, project_id)
    if generation is None:
        raise ManagerError(
            "artifact_missing",
            "The enrolled project has no current development artifact.",
            "Run an explicitly approved rebuild.",
            "resolve",
            project_id,
        )
    git_sha = generation.name
    if len(git_sha) != 40 or any(
        character not in "0123456789abcdef" for character in git_sha
    ):
        raise ManagerError(
            "artifact_invalid",
            "The selected generation name is not a full lowercase Git SHA.",
            "Run an explicitly approved rebuild.",
            "resolve",
            project_id,
        )
    try:
        lease = _artifact_lock(host_root, project_id, git_sha, fcntl.LOCK_SH)
    except OSError as error:
        raise ManagerError(
            "lease_unavailable",
            str(error),
            "Retry after inspecting host-local artifact locks.",
            "resolve",
            project_id,
            git_sha,
        ) from error
    try:
        artifact, manifest = _validate_generation(generation, project_id, description)
        execution_path = (
            _execution_alias(host_root, project_id, git_sha, artifact)
            if manifest["artifact_kind"] == "executable"
            else artifact
        )
    except Exception:
        lease.close()
        raise
    return ResolvedArtifact(
        project_id,
        "development",
        artifact,
        git_sha,
        manifest["development_version"],
        manifest["sha256"],
        manifest["artifact_kind"],
        execution_path,
        lease,
    )


def configure_codex(
    repository: Path,
    host_root: Path,
    *,
    approve_codex: bool,
    codex_bin: str = "codex",
) -> tuple[str, dict[str, Any]]:
    with _publisher_lock(host_root, "aquarium"):
        return _configure_codex_locked(
            repository,
            host_root,
            approve_codex=approve_codex,
            codex_bin=codex_bin,
        )


def _configure_codex_locked(
    repository: Path,
    host_root: Path,
    *,
    approve_codex: bool,
    codex_bin: str = "codex",
) -> tuple[str, dict[str, Any]]:
    checkout, _, description, git_sha = _require_enrolled_checkout(
        repository, host_root, require_clean=False
    )
    if description["project_id"] != "aquarium":
        raise ManagerError(
            "unsupported_project",
            "Isolated Codex configuration must be initiated from Aquarium.",
            "Run configuration from the enrolled Aquarium checkout.",
            "configure-codex",
            description["project_id"],
            git_sha,
        )
    if not approve_codex:
        raise ManagerError(
            "approval_required",
            "Isolated Codex configuration approval is required.",
            "Approve only configuration beneath the displayed Aquarium Codex home.",
            "configure-codex",
            "aquarium",
            git_sha,
        )
    codex_home = host_root / "codex"
    login_action = f"CODEX_HOME={codex_home} codex login"
    transaction_parent = host_root / "transactions"
    transaction = transaction_parent / "codex-config"
    _recover_codex_transaction(codex_home, transaction)
    if not codex_home.is_dir() or codex_home.is_symlink():
        raise ManagerError(
            "codex_login_required",
            "The isolated Codex home does not exist; configuration was not changed.",
            login_action,
            "configure-codex",
            "aquarium",
            git_sha,
        )
    if _run_codex(codex_bin, host_root, "login", "status", check=False).returncode != 0:
        raise ManagerError(
            "codex_login_required",
            "The isolated Codex home is not authenticated; configuration was not changed.",
            login_action,
            "configure-codex",
            "aquarium",
            git_sha,
        )
    home_mode = stat.S_IMODE(codex_home.stat().st_mode)
    transaction_parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    staging = Path(tempfile.mkdtemp(prefix=".codex-config-", dir=transaction_parent))
    try:
        _snapshot_codex_configuration(codex_home, staging)
        (staging / "home-mode").write_text(f"{home_mode:o}\n", encoding="ascii")
        (staging / "active").write_text("aquarium-codex-transaction/v1\n")
        os.replace(staging, transaction)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    with ExitStack() as stack:
        rollback = stack.enter_context(ExitStack())
        rollback.callback(_recover_codex_transaction, codex_home, transaction)
        codex_home.chmod(0o700)
        aquarium = stack.enter_context(resolve_artifact("aquarium", host_root))
        if aquarium.artifact_kind != "codex-plugin":
            raise ManagerError(
                "artifact_invalid",
                "The enrolled Aquarium artifact is not a Codex plugin marketplace.",
                "Rebuild Aquarium with its codex-plugin producer contract.",
                "configure-codex",
                "aquarium",
                aquarium.git_sha,
            )
        aquarium_generation = aquarium.path.parent
        _unseal_managed_tree(aquarium_generation)
        stack.callback(_seal_generation, aquarium_generation)
        plugins = _run_codex(
            codex_bin, host_root, "plugin", "list", "--json", json_output=True
        )
        if any(
            item.get("pluginId") == "aquarium@root-kernel"
            for item in plugins.get("installed", [])
        ):
            _run_codex(
                codex_bin,
                host_root,
                "plugin",
                "remove",
                "aquarium@root-kernel",
                "--json",
            )
        marketplaces = _run_codex(
            codex_bin,
            host_root,
            "plugin",
            "marketplace",
            "list",
            "--json",
            json_output=True,
        )
        if any(
            item.get("name") == "root-kernel"
            for item in marketplaces.get("marketplaces", [])
        ):
            _run_codex(
                codex_bin,
                host_root,
                "plugin",
                "marketplace",
                "remove",
                "root-kernel",
                "--json",
            )
        _run_codex(
            codex_bin,
            host_root,
            "plugin",
            "marketplace",
            "add",
            str(aquarium.path),
            "--json",
        )
        installed = _run_codex(
            codex_bin,
            host_root,
            "plugin",
            "add",
            "aquarium@root-kernel",
            "--json",
            json_output=True,
        )
        if artifact_digest(aquarium.path) != aquarium.sha256:
            raise ManagerError(
                "checksum_mismatch",
                "The Aquarium marketplace changed during isolated installation.",
                "Rebuild the exact generation before retrying configuration.",
                "configure-codex",
                "aquarium",
                aquarium.git_sha,
            )
        _seal_generation(aquarium_generation)
        installed_root = Path(installed.get("installedPath", ""))
        manager_script = installed_root / "skills/dev-aquarium/scripts/dev_aquarium.py"
        if (
            not installed_root.is_absolute()
            or not manager_script.is_file()
            or codex_home.resolve() not in installed_root.resolve().parents
        ):
            raise ManagerError(
                "codex_not_configured",
                "Codex did not install the Aquarium plugin beneath its isolated home.",
                "Inspect the isolated plugin cache and retry configuration.",
                "configure-codex",
                "aquarium",
                aquarium.git_sha,
            )
        existing_servers = _run_codex(
            codex_bin, host_root, "mcp", "list", "--json", json_output=True
        )
        existing_names = {item.get("name") for item in existing_servers}
        integrations = []
        for project_id in ("podway", "mulgae", "gaori", "sanho", "dolgorae"):
            enrollment = read_enrollment(host_root, project_id)
            if enrollment is None:
                integrations.append({"project_id": project_id, "state": "not-enrolled"})
                if project_id in MCP_ARGUMENTS and project_id in existing_names:
                    _run_codex(codex_bin, host_root, "mcp", "remove", project_id)
                continue
            resolved = stack.enter_context(resolve_artifact(project_id, host_root))
            integration = {
                "project_id": project_id,
                "state": "development",
                "git_sha": resolved.git_sha,
                "development_version": resolved.development_version,
                "sha256": resolved.sha256,
                "mcp": project_id in MCP_ARGUMENTS,
            }
            integrations.append(integration)
            if project_id not in MCP_ARGUMENTS:
                continue
            if project_id in existing_names:
                _run_codex(codex_bin, host_root, "mcp", "remove", project_id)
            checkout_path = Path(enrollment["checkout"])
            _run_codex(
                codex_bin,
                host_root,
                "mcp",
                "add",
                project_id,
                "--",
                os.fspath(Path(os.sys.executable).resolve()),
                str(manager_script),
                "--host-root",
                str(host_root),
                "launch",
                "--project-id",
                project_id,
                "--",
                *MCP_ARGUMENTS[project_id](checkout_path),
            )
        verification = codex_diagnosis(host_root, codex_bin)
        if not verification["configured"]:
            raise ManagerError(
                "codex_not_configured",
                "The isolated Aquarium plugin failed post-configuration diagnosis.",
                "Inspect the isolated Codex home and retry configuration.",
                "configure-codex",
                "aquarium",
                aquarium.git_sha,
            )
        details = {
            "checkout": str(checkout),
            "codex_home": str(codex_home),
            "plugin_git_sha": aquarium.git_sha,
            "plugin_version": aquarium.development_version,
            "plugin_sha256": aquarium.sha256,
            "paired_skills": {
                "source": "aquarium-plugin",
                "git_sha": aquarium.git_sha,
                "development_version": aquarium.development_version,
            },
            "integrations": integrations,
            "mcp_servers": verification["mcp_servers"],
            "login": verification["login"],
            "login_action": verification["login_action"],
        }
        if details["login"] != "ready":
            raise ManagerError(
                "codex_login_required",
                "The isolated Codex home lost authentication during configuration.",
                details["login_action"] or login_action,
                "configure-codex",
                "aquarium",
                git_sha,
            )
        (transaction / "active").unlink()
        rollback.pop_all()
    shutil.rmtree(transaction, ignore_errors=True)
    artifact_root = host_root / "artifacts" / "aquarium"
    try:
        if artifact_root.is_dir():
            for generation in sorted(artifact_root.iterdir()):
                if generation.name == details["plugin_git_sha"] or not SHA_RE.fullmatch(
                    generation.name
                ):
                    continue
                cleanup_status, cleanup = cleanup_generation(
                    "aquarium", generation.name, host_root, wait=False
                )
                if cleanup_status == "no-change" and cleanup.get("leased"):
                    _spawn_cleanup(host_root, "aquarium", generation.name)
    except Exception as error:  # noqa: BLE001
        details["cleanup_warning"] = type(error).__name__
    return "success", details


def _spawn_cleanup(host_root: Path, project_id: str, git_sha: str) -> None:
    subprocess.Popen(
        [
            os.fspath(Path(os.sys.executable).resolve()),
            os.fspath(Path(__file__).with_name("dev_aquarium.py").resolve()),
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
            for managed_path in (
                host_root / "runtime" / project_id / git_sha,
                generation,
            ):
                if not managed_path.exists() or managed_path.is_symlink():
                    continue
                _unseal_managed_tree(managed_path)
            shutil.rmtree(generation)
            runtime = host_root / "runtime" / project_id / git_sha
            if runtime.exists():
                shutil.rmtree(runtime)
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
    first_failure: ManagerError | None = None
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
                request_path.unlink(missing_ok=True)
            except ManagerError as error:
                _write_diagnostic(host_root, error)
                if first_failure is None:
                    first_failure = error
            except (OSError, json.JSONDecodeError) as error:
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
    if first_failure is not None:
        raise first_failure
    return "success", {
        "processed": processed,
        "published": published,
        **latest,
    }
