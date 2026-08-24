#!/usr/bin/env python3
"""Inspect Aquarium release-note enrollment and structure without mutation."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import sys
from datetime import date
from pathlib import Path, PurePosixPath

SCHEMA_VERSION = "aquarium-release-notes-inspection/v1"
ERROR_SCHEMA_VERSION = "aquarium-release-notes-inspection-error/v1"
MAX_TEXT_BYTES = 1024 * 1024
PROJECT_CONFIGURATION_HEADING = "## Project Configuration"
AUTHORITY = re.compile(r"^(?:- )?Aquarium release notes: (.+)$", re.MULTILINE)
RELEASE_HEADING = re.compile(
    r"^## (v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)) - "
    r"(Unreleased|[0-9]{4}-[0-9]{2}-[0-9]{2})$",
    re.MULTILINE,
)
RELEASE_LIKE_HEADING = re.compile(r"^## v[0-9]")
RELEASE_SECTION_BOUNDARY = re.compile(r"^## v[0-9].*$", re.MULTILINE)
SEMVER = re.compile(r"^v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)$")
ALLOWED_CATEGORIES = ("Added", "Changed", "Fixed", "Removed")


class InspectionError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise InspectionError("invalid_arguments", "invalid command-line arguments")


def semver_key(version: str) -> tuple[int, int, int]:
    major, minor, patch = (int(part) for part in version.removeprefix("v").split("."))
    return major, minor, patch


def git_command(
    repository: Path, arguments: list[str]
) -> subprocess.CompletedProcess[bytes]:
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "LANG": "C",
        "LC_ALL": "C",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_PAGER": "cat",
    }
    return subprocess.run(
        ["git", "-c", "core.fsmonitor=false", "-C", str(repository), *arguments],
        check=False,
        capture_output=True,
        env=environment,
        timeout=30,
    )


def canonical_git_root(requested: Path) -> Path:
    result = git_command(requested, ["rev-parse", "--show-toplevel"])
    if result.returncode != 0:
        raise InspectionError("repository_not_git", "repository must be a Git worktree")
    try:
        root = Path(result.stdout.decode("utf-8").strip())
    except UnicodeError as error:
        raise InspectionError(
            "repository_path_invalid", "Git root is not valid UTF-8"
        ) from error
    if not root.is_absolute() or root != requested:
        raise InspectionError(
            "repository_not_root",
            "repository must be the exact canonical Git worktree root",
        )
    return root


def read_regular_text(path: Path) -> str:
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        try:
            mode = current.lstat().st_mode
        except OSError as error:
            raise InspectionError(
                "authority_unreadable", "authority file is unreadable"
            ) from error
        if stat.S_ISLNK(mode):
            raise InspectionError(
                "authority_symlinked", "authority path must not contain symlinks"
            )
    if not stat.S_ISREG(path.stat().st_mode):
        raise InspectionError(
            "authority_not_regular", "authority must be a regular file"
        )
    if path.stat().st_size > MAX_TEXT_BYTES:
        raise InspectionError("authority_oversized", "authority file is too large")
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise InspectionError(
            "authority_unreadable", "authority file is not readable UTF-8"
        ) from error


def project_configuration_text(agents_text: str) -> str:
    sections: list[list[str]] = []
    current: list[str] | None = None
    for line in agents_text.splitlines():
        if line == PROJECT_CONFIGURATION_HEADING:
            if current is not None:
                sections.append(current)
            current = []
            continue
        if current is not None and re.match(r"^#{1,2}(?:[ \t]+|$)", line):
            sections.append(current)
            current = None
            continue
        if current is not None:
            current.append(line)
    if current is not None:
        sections.append(current)
    return "\n".join(line for section in sections for line in section)


def release_notes_path(repository: Path, agents_text: str) -> PurePosixPath | None:
    matches = AUTHORITY.findall(project_configuration_text(agents_text))
    if not matches:
        return None
    if len(matches) != 1:
        raise InspectionError(
            "authority_ambiguous", "release-notes authority must be declared once"
        )
    value = matches[0]
    relative = PurePosixPath(value)
    if (
        not value.endswith(".md")
        or relative.is_absolute()
        or value != relative.as_posix()
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise InspectionError(
            "authority_path_invalid",
            "release-notes authority must be one repository-relative Markdown path",
        )
    candidate = repository.joinpath(*relative.parts)
    try:
        candidate.relative_to(repository)
    except ValueError as error:
        raise InspectionError(
            "authority_path_invalid", "release-notes authority escapes repository"
        ) from error
    return relative


def section_entry_count(text: str, match: re.Match[str], next_start: int) -> int:
    return sum(
        1
        for line in text[match.end() : next_start].splitlines()
        if line.startswith("- ")
    )


def section_end(
    boundaries: list[re.Match[str]], match: re.Match[str], text_length: int
) -> int:
    return next(
        (
            boundary.start()
            for boundary in boundaries
            if boundary.start() > match.start()
        ),
        text_length,
    )


def section_structure_findings(
    text: str, match: re.Match[str], next_start: int
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    category_lines: dict[str, int] = {}
    category_entries = {category: 0 for category in ALLOWED_CATEGORIES}
    current_category: str | None = None
    first_line = text.count("\n", 0, match.end()) + 1

    for offset, line in enumerate(text[match.end() : next_start].splitlines(), start=1):
        line_number = first_line + offset
        if line.startswith("### "):
            category = line[4:]
            if category not in ALLOWED_CATEGORIES:
                findings.append(
                    {
                        "code": "release_category_invalid",
                        "message": (
                            f"release category on line {line_number} must be Added, "
                            "Changed, Fixed, or Removed"
                        ),
                    }
                )
                current_category = None
            elif category in category_lines:
                findings.append(
                    {
                        "code": "release_category_duplicate",
                        "message": (
                            f"release category {category} is duplicated on line "
                            f"{line_number}"
                        ),
                    }
                )
                current_category = category
            else:
                category_lines[category] = line_number
                current_category = category
        elif line.startswith("- "):
            if current_category is None:
                findings.append(
                    {
                        "code": "release_entry_outside_category",
                        "message": (
                            f"release entry on line {line_number} must belong to an "
                            "allowed category"
                        ),
                    }
                )
            else:
                category_entries[current_category] += 1

    for category, line_number in category_lines.items():
        if category_entries[category] == 0:
            findings.append(
                {
                    "code": "release_category_empty",
                    "message": (
                        f"release category {category} on line {line_number} must "
                        "contain an entry"
                    ),
                }
            )
    return findings


def tracking_state(repository: Path, relative: PurePosixPath) -> str:
    path = relative.as_posix()
    tracked = git_command(
        repository,
        ["--literal-pathspecs", "ls-files", "--error-unmatch", "--", path],
    )
    if tracked.returncode == 0:
        return "tracked"
    if tracked.returncode not in {1}:
        raise InspectionError(
            "git_inventory_failed", "release-notes tracking check failed"
        )
    ignored = git_command(
        repository,
        ["check-ignore", "--quiet", "--", path],
    )
    if ignored.returncode == 0:
        return "ignored"
    if ignored.returncode != 1:
        raise InspectionError(
            "git_inventory_failed", "release-notes ignore check failed"
        )
    return "untracked"


def inspect(
    repository: Path,
    expected_version: str | None = None,
    previous_release: str | None = None,
    first_release: bool = False,
) -> dict[str, object]:
    if first_release and previous_release is not None:
        raise InspectionError(
            "baseline_ambiguous",
            "first release and previous release are mutually exclusive",
        )
    root = canonical_git_root(repository)
    agents_text = read_regular_text(root / "AGENTS.md")
    relative = release_notes_path(root, agents_text)
    if relative is None:
        return {
            "schema_version": SCHEMA_VERSION,
            "semantic_scope": "not_evaluated",
            "enrollment": "not_enrolled",
            "notes_path": None,
            "tracking": None,
            "baseline": (
                "first_release"
                if first_release
                else "previous_release"
                if previous_release is not None
                else "unspecified"
            ),
            "open_release": None,
            "released_versions": [],
            "findings": [],
        }

    notes_path = root.joinpath(*relative.parts)
    notes_text = read_regular_text(notes_path)
    tracking = tracking_state(root, relative)
    headings = list(RELEASE_HEADING.finditer(notes_text))
    boundaries = list(RELEASE_SECTION_BOUNDARY.finditer(notes_text))
    open_headings = [match for match in headings if match.group(2) == "Unreleased"]
    released = [match for match in headings if match.group(2) != "Unreleased"]
    findings: list[dict[str, str]] = []

    for line_number, line in enumerate(notes_text.splitlines(), start=1):
        if RELEASE_LIKE_HEADING.match(line) and RELEASE_HEADING.fullmatch(line) is None:
            findings.append(
                {
                    "code": "release_heading_invalid",
                    "message": (
                        f"release-like heading on line {line_number} must use "
                        "canonical "
                        "SemVer and Unreleased or YYYY-MM-DD format"
                    ),
                }
            )

    if tracking != "tracked":
        code = "authority_ignored" if tracking == "ignored" else "authority_untracked"
        findings.append(
            {
                "code": code,
                "message": "the enrolled release-notes authority must be tracked",
            }
        )

    if len(open_headings) != 1:
        findings.append(
            {
                "code": "open_release_count_invalid",
                "message": "release notes must contain exactly one Unreleased section",
            }
        )
    if open_headings and headings and open_headings[0] is not headings[0]:
        findings.append(
            {
                "code": "open_release_not_first",
                "message": "the Unreleased section must precede completed releases",
            }
        )
    if len({match.group(1) for match in headings}) != len(headings):
        findings.append(
            {
                "code": "release_version_duplicate",
                "message": "release versions must be unique",
            }
        )
    for match in released:
        try:
            date.fromisoformat(match.group(2))
        except ValueError:
            findings.append(
                {
                    "code": "release_date_invalid",
                    "message": "completed release dates must be valid calendar dates",
                }
            )

    for match in headings:
        next_start = section_end(boundaries, match, len(notes_text))
        findings.extend(section_structure_findings(notes_text, match, next_start))

    if first_release and released:
        findings.append(
            {
                "code": "first_release_has_completed_release",
                "message": "first-release notes must not contain a completed release",
            }
        )

    open_release: dict[str, object] | None = None
    if len(open_headings) == 1:
        match = open_headings[0]
        next_start = section_end(boundaries, match, len(notes_text))
        open_release = {
            "version": match.group(1),
            "line": notes_text.count("\n", 0, match.start()) + 1,
            "entry_count": section_entry_count(notes_text, match, next_start),
        }
        if expected_version is not None and match.group(1) != expected_version:
            findings.append(
                {
                    "code": "expected_version_mismatch",
                    "message": "the open release does not match the expected version",
                }
            )

    released_versions = [
        {
            "version": match.group(1),
            "date": match.group(2),
            "line": notes_text.count("\n", 0, match.start()) + 1,
        }
        for match in released
    ]
    if previous_release is not None and previous_release not in {
        match.group(1) for match in released
    }:
        findings.append(
            {
                "code": "previous_release_missing",
                "message": "the previous release is not recorded as completed",
            }
        )
    if (
        expected_version is not None
        and previous_release is not None
        and semver_key(expected_version) <= semver_key(previous_release)
    ):
        findings.append(
            {
                "code": "expected_version_not_newer",
                "message": (
                    "the expected version must be greater than the previous release"
                ),
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "semantic_scope": "not_evaluated",
        "enrollment": "enrolled",
        "notes_path": relative.as_posix(),
        "tracking": tracking,
        "baseline": (
            "first_release"
            if first_release
            else "previous_release"
            if previous_release is not None
            else "unspecified"
        ),
        "open_release": open_release,
        "released_versions": released_versions,
        "findings": findings,
    }


def parser() -> argparse.ArgumentParser:
    result = JsonArgumentParser()
    result.add_argument("--repository", required=True)
    result.add_argument("--expected-version")
    baseline = result.add_mutually_exclusive_group()
    baseline.add_argument("--previous-release")
    baseline.add_argument("--first-release", action="store_true")
    return result


def main() -> int:
    try:
        arguments = parser().parse_args()
        repository = Path(arguments.repository)
        if not repository.is_absolute():
            raise InspectionError(
                "repository_not_absolute", "repository must be an absolute path"
            )
        if arguments.expected_version and not SEMVER.fullmatch(
            arguments.expected_version
        ):
            raise InspectionError(
                "expected_version_invalid", "expected version must be stable SemVer"
            )
        if arguments.previous_release and not SEMVER.fullmatch(
            arguments.previous_release
        ):
            raise InspectionError(
                "previous_release_invalid", "previous release must be stable SemVer"
            )
        print(
            json.dumps(
                inspect(
                    repository,
                    arguments.expected_version,
                    arguments.previous_release,
                    arguments.first_release,
                ),
                sort_keys=True,
            )
        )
        return 0
    except InspectionError as error:
        print(
            json.dumps(
                {
                    "schema_version": ERROR_SCHEMA_VERSION,
                    "error": {"code": error.code, "message": str(error)},
                },
                sort_keys=True,
            )
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
