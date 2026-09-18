"""Read-only report joins for aquarium-status."""

from __future__ import annotations

import json
import os
import stat
import subprocess
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from status_contract import VERSION_RE, ContractError, version_tuple

LATEST_RELEASE_URL = "https://api.github.com/repos/irootkernel/aquarium/releases/latest"
MAX_EXTERNAL_BYTES = 1024 * 1024
KNOWN_PROJECT_IDS = (
    "aquarium",
    "dolgorae",
    "gaori",
    "mulgae",
    "podway",
    "sanho",
)


def version(
    value: str | None, source: str, status: str | None = None
) -> dict[str, Any]:
    selected = status or ("observed" if value is not None else "unknown")
    return {"value": value, "source": source, "status": selected}


def freshness(left: dict[str, Any], right: dict[str, Any]) -> str:
    if left["status"] == "not_checked" or right["status"] == "not_checked":
        return "not_checked"
    if left["status"] != "observed" or right["status"] != "observed":
        return "unknown"
    current = version_tuple(left["value"])
    target = version_tuple(right["value"])
    return (
        "current" if current == target else ("behind" if current < target else "ahead")
    )


def _git_identity(root: Path) -> tuple[str, str]:
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    top = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    ).stdout.strip()
    common = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--git-common-dir"],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    ).stdout.strip()
    common_path = Path(common)
    if not common_path.is_absolute():
        common_path = root / common_path
    return (
        unicodedata.normalize("NFC", str(Path(top).resolve(strict=True))),
        unicodedata.normalize("NFC", str(common_path.resolve(strict=True))),
    )


def root_state(row: dict[str, Any]) -> str:
    path = Path(row["git_root"])
    try:
        if not path.exists():
            return "missing"
        top, common = _git_identity(path)
        return (
            "present"
            if top == row["git_root"] and common == row["git_common_dir"]
            else "identity_mismatch"
        )
    except (OSError, subprocess.SubprocessError):
        return "unreadable"


def _bounded_json(path: Path) -> dict[str, Any] | None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    if (
        stat.S_ISLNK(info.st_mode)
        or not stat.S_ISREG(info.st_mode)
        or info.st_size > MAX_EXTERNAL_BYTES
    ):
        raise ValueError("external JSON path is unsafe")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("external JSON is not an object")
    return value


def enrollment(row: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    base = Path.home()
    try:
        for part in (".aquarium-dev", "enrollments"):
            base = base / part
            try:
                info = base.lstat()
            except FileNotFoundError:
                return {"state": "absent", "project_id": None}, None
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
                return (
                    {"state": "unreadable", "project_id": None},
                    "enrollment_unreadable",
                )
        expected = {
            "schema",
            "project_id",
            "checkout",
            "hook_path",
            "hook_block",
            "enrolled_at",
        }
        for project_id in KNOWN_PROJECT_IDS:
            try:
                value = _bounded_json(base / f"{project_id}.json")
            except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
                continue
            if value is None or value.get("checkout") != row["git_root"]:
                continue
            if (
                set(value) != expected
                or value.get("schema") != "aquarium-dev-enrollment/v1"
                or value.get("project_id") != project_id
            ):
                return (
                    {"state": "invalid", "project_id": None},
                    "enrollment_invalid",
                )
            return {"state": "enrolled", "project_id": project_id}, None
        return {"state": "absent", "project_id": None}, None
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
        return {"state": "unreadable", "project_id": None}, "enrollment_unreadable"


def release_version(refresh: bool) -> tuple[dict[str, Any], str | None]:
    if not refresh:
        return version(None, "not_requested", "not_checked"), None
    try:
        request = urllib.request.Request(
            LATEST_RELEASE_URL,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "aquarium-status",
            },
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = response.read(MAX_EXTERNAL_BYTES + 1)
        if len(payload) > MAX_EXTERNAL_BYTES:
            raise ValueError("release response is too large")
        tag = json.loads(payload).get("tag_name")
        if not isinstance(tag, str) or VERSION_RE.fullmatch(tag) is None:
            raise ValueError("release tag is invalid")
        return version(tag, "official_github_release"), None
    except (
        OSError,
        ValueError,
        AttributeError,
        json.JSONDecodeError,
        urllib.error.URLError,
    ):
        return version(None, "unavailable", "unknown"), "release_refresh_failed"


def _safe_source_file(root: Path, relative: str) -> Path:
    current = root
    for part in Path(relative).parts:
        current = current / part
        info = current.lstat()
        if stat.S_ISLNK(info.st_mode):
            raise ContractError(
                "invalid_source_root", "source root contains a symbolic link"
            )
    info = current.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_EXTERNAL_BYTES:
        raise ContractError("invalid_source_root", "source file is invalid")
    if root not in current.parents:
        raise ContractError(
            "invalid_source_root", "source file escapes the source root"
        )
    return current


def source_versions(
    source_root: str | None,
) -> tuple[dict[str, Any], dict[str, Any], str | None]:
    if source_root is None:
        missing = version(None, "not_requested", "not_checked")
        return missing, dict(missing), None
    try:
        root = Path(source_root)
        if not root.is_absolute() or root.is_symlink():
            raise ContractError("invalid_source_root", "source root must be canonical")
        resolved = root.resolve(strict=True)
        if str(resolved) != source_root:
            raise ContractError("invalid_source_root", "source root must be canonical")
        root = resolved
        top, _ = _git_identity(root)
        if top != str(root):
            raise ContractError(
                "invalid_source_root", "source root must be an exact Git worktree root"
            )
        manifest = json.loads(
            _safe_source_file(
                root, "plugins/aquarium/.codex-plugin/plugin.json"
            ).read_text()
        )
        changelog = _safe_source_file(root, "CHANGELOG.md").read_text(encoding="utf-8")
        if (
            manifest.get("name") != "aquarium"
            or VERSION_RE.fullmatch(f"v{manifest.get('version', '')}") is None
        ):
            raise ContractError(
                "invalid_source_root", "source manifest is not Aquarium"
            )
        candidates = [
            line.split()[1]
            for line in changelog.splitlines()
            if line.startswith("## v") and line.endswith(" - Unreleased")
        ]
        plugin = version(f"v{manifest['version']}", "source_root_manifest")
        unreleased = (
            version(candidates[0], "source_root_changelog")
            if len(candidates) == 1 and VERSION_RE.fullmatch(candidates[0])
            else version(None, "unavailable", "unknown")
        )
        return (
            plugin,
            unreleased,
            None
            if unreleased["status"] == "observed"
            else "source_observation_unavailable",
        )
    except ContractError:
        raise
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        AttributeError,
        subprocess.SubprocessError,
    ) as error:
        raise ContractError(
            "invalid_source_root", "source root cannot be inspected"
        ) from error
