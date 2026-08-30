#!/usr/bin/env python3
# Purpose: provide conservative, read-only structural discovery for docs-setup.
# Keep only facts provable from repository paths and explicit roadmap fields.
# Do not validate prose wording, semantic completeness, implementation, or runtime truth.
"""Inspect the minimum documentation structure needed by docs-setup."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "aquarium-docs-inspection/v2"
ERROR_SCHEMA_VERSION = "aquarium-docs-inspection-error/v2"
MAX_TEXT_BYTES = 8 * 1024 * 1024

ROLES = (
    "specs",
    "architecture",
    "architecture-decision-records",
    "implementation-tips",
    "ops",
    "roadmap",
    "deferred-feedback",
    "todo",
)
SHARED_ROLES = {"specs", "architecture", "architecture-decision-records"}
ROLE_ALIASES = {
    "specs": ("specs",),
    "architecture": ("architecture",),
    "architecture-decision-records": ("architecture-decision-records", "adr"),
    "implementation-tips": ("implementation-tips", "guides"),
    "ops": ("ops", "operations", "runbooks"),
    "roadmap": ("roadmap", "ROADMAP.md", "roadmap.md"),
    "deferred-feedback": ("deferred-feedback", "deferred-feedback.md"),
    "todo": ("todo", "TODO.md", "todo.md"),
}

SENSITIVE_COMPONENT = re.compile(
    r"(?i)(?:^|[._-])(?:auth(?:entication)?|credentials?|keys?|secrets?|tokens?)(?:[._-]|$)"
)
LEVEL_TWO_HEADING = re.compile(r"^##\s+`?([A-Za-z][A-Za-z0-9-]*)`?(?:\s*(?:[—:-]|$))")
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
FIELD_LINE = re.compile(
    r"^\s*(?:[-*]\s+)?(?:\*\*)?([^:*]+):(?:\*\*)?\s*(.*)$",
    re.IGNORECASE,
)
TASK_TABLE_HEADERS = {
    "task",
    "tasks",
    "task id",
    "task identifier",
    "work item",
    "work unit",
    "작업",
    "태스크",
}
ACTIVE_EPIC_STATUSES = {
    "Planned",
    "In Progress",
    "In Review",
    "Deferred",
    "Blocked",
}


class InspectionError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise InspectionError("invalid_arguments", "invalid command-line arguments")


def finding(
    code: str, severity: str, message: str, path: str | None = None
) -> dict[str, str]:
    result = {"code": code, "severity": severity, "message": message}
    if path is not None:
        result["path"] = path
    return result


def lexical_path_symlinked(path: Path) -> bool:
    absolute = Path(os.path.abspath(path))
    current = Path(absolute.parts[0])
    for part in absolute.parts[1:]:
        current /= part
        try:
            if stat.S_ISLNK(current.lstat().st_mode):
                return True
        except FileNotFoundError:
            return False
    return False


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
        [
            "git",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.preloadindex=false",
            "-C",
            str(repository),
            *arguments,
        ],
        check=False,
        capture_output=True,
        env=environment,
        timeout=30,
    )


def canonical_git_root(requested_repository: Path) -> Path:
    result = git_command(requested_repository, ["rev-parse", "--show-toplevel"])
    if result.returncode != 0:
        raise InspectionError("repository_not_git", "repository must be a Git worktree")
    try:
        root = Path(result.stdout.decode("utf-8").strip())
    except UnicodeError as error:
        raise InspectionError(
            "repository_path_invalid", "Git root is not valid UTF-8"
        ) from error
    if not root.is_absolute() or root != requested_repository:
        raise InspectionError(
            "repository_not_root",
            "repository must be the exact canonical Git worktree root",
        )
    return root


def git_paths(repository: Path, arguments: list[str], error_code: str) -> list[Path]:
    result = git_command(repository, arguments)
    if result.returncode != 0:
        raise InspectionError(error_code, "Git file inventory failed")
    try:
        values = result.stdout.decode("utf-8").split("\0")
    except UnicodeError as error:
        raise InspectionError(
            error_code, "a repository path is not valid UTF-8"
        ) from error
    return [Path(value) for value in values if value]


def tracked_paths(repository: Path) -> list[Path]:
    return git_paths(
        repository,
        ["--literal-pathspecs", "ls-files", "-z", "--cached"],
        "tracked_path_invalid",
    )


def untracked_paths(repository: Path) -> list[Path]:
    return git_paths(
        repository,
        ["--literal-pathspecs", "ls-files", "-z", "--others", "--exclude-standard"],
        "untracked_path_invalid",
    )


def ignored_paths(repository: Path) -> list[Path]:
    return git_paths(
        repository,
        [
            "--literal-pathspecs",
            "ls-files",
            "-z",
            "--others",
            "--ignored",
            "--exclude-standard",
        ],
        "ignored_path_invalid",
    )


def sensitive_path(relative: Path) -> bool:
    return any(
        part.lower().startswith(".env") or SENSITIVE_COMPONENT.search(part)
        for part in relative.parts
    )


def read_repository_text(
    repository: Path, relative: Path
) -> tuple[str | None, str | None]:
    if sensitive_path(relative):
        return None, "sensitive"
    current = repository
    for part in relative.parts:
        current /= part
        try:
            mode = current.lstat().st_mode
        except OSError:
            return None, "missing"
        if stat.S_ISLNK(mode):
            return None, "symlink"
    try:
        if not stat.S_ISREG(current.stat().st_mode):
            return None, "not_regular"
        if current.stat().st_size > MAX_TEXT_BYTES:
            return None, "oversized"
        data = current.read_bytes()
    except OSError:
        return None, "unreadable"
    if b"\0" in data:
        return None, "binary"
    try:
        return data.decode("utf-8"), None
    except UnicodeError:
        return None, "non_utf8"


def path_role_candidates(repository: Path, base: Path, role: str) -> list[str]:
    candidates: list[str] = []
    seen: set[tuple[int, int]] = set()
    for alias in ROLE_ALIASES[role]:
        relative = base / alias
        path = repository / relative
        if path.is_dir() and not lexical_path_symlinked(path):
            authority = path / "README.md"
            if not authority.is_file() or lexical_path_symlinked(authority):
                continue
        elif path.is_file() and not lexical_path_symlinked(path):
            authority = path
        else:
            continue
        try:
            metadata = authority.stat()
        except OSError:
            continue
        identity = (metadata.st_dev, metadata.st_ino)
        if identity in seen:
            continue
        seen.add(identity)
        candidates.append(relative.as_posix())
    return candidates


def scope_record(repository: Path, name: str, kind: str, base: Path) -> dict[str, Any]:
    return {
        "name": name,
        "kind": kind,
        "base": base.as_posix(),
        "role_candidates": {
            role: path_role_candidates(repository, base, role) for role in ROLES
        },
    }


def discover_structure(repository: Path) -> dict[str, Any]:
    docs = repository / "docs"
    if not docs.is_dir() or docs.is_symlink():
        return {"profile": "none", "root_index": None, "scopes": []}

    child_scopes: list[str] = []
    for child in sorted(docs.iterdir(), key=lambda item: item.name):
        if not child.is_dir() or child.is_symlink() or child.name.startswith("."):
            continue
        if child.name == "project":
            continue
        base = Path("docs") / child.name
        candidates = {
            role: path_role_candidates(repository, base, role) for role in ROLES
        }
        if (
            candidates["roadmap"]
            and sum(bool(value) for value in candidates.values()) >= 3
        ):
            child_scopes.append(child.name)

    scopes: list[dict[str, Any]] = []
    if child_scopes:
        profile = "multi-scope"
        project = repository / "docs/project"
        if project.is_dir() and not project.is_symlink():
            scopes.append(
                scope_record(repository, "project", "shared", Path("docs/project"))
            )
        scopes.extend(
            scope_record(repository, name, "delivery", Path("docs") / name)
            for name in child_scopes
        )
    else:
        profile = "single-scope"
        scopes.append(scope_record(repository, "default", "delivery", Path("docs")))

    return {
        "profile": profile,
        "root_index": (
            "docs/README.md"
            if (docs / "README.md").is_file()
            and not lexical_path_symlinked(docs / "README.md")
            else None
        ),
        "scopes": scopes,
    }


def owner_file(repository: Path, owner: Path) -> Path:
    return owner / "README.md" if (repository / owner).is_dir() else owner


def documentation_inventory(tracked: list[Path], untracked: list[Path]) -> list[Path]:
    return sorted(
        {path for path in tracked + untracked if path.suffix.lower() == ".md"},
        key=lambda path: path.as_posix(),
    )


def table_cells(line: str) -> list[str]:
    return [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]


def looks_like_identifier(value: str) -> bool:
    return bool(
        re.fullmatch(
            r"(?:[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*|[a-z][a-z0-9-]*-[0-9]{3,})",
            value,
        )
    )


def field_values(lines: list[str], label: str) -> list[str]:
    values: list[str] = []
    for index, line in enumerate(lines):
        match = FIELD_LINE.match(line)
        if match is None or match.group(1).strip().casefold() != label.casefold():
            continue
        value = match.group(2).strip()
        if not value:
            for following in lines[index + 1 :]:
                if following.strip():
                    value = following.strip()
                    break
        values.append(value)
    return values


def field_links(lines: list[str], label: str) -> tuple[int, list[str]]:
    values = field_values(lines, label)
    return len(values), [
        target for value in values for target in MARKDOWN_LINK.findall(value)
    ]


def status_value(lines: list[str]) -> str:
    values = field_values(lines, "Status") + field_values(lines, "상태")
    if len(values) != 1:
        return "unknown"
    return values[0].strip().strip("`").strip()


def task_rows(lines: list[str]) -> list[dict[str, str]]:
    tasks: list[dict[str, str]] = []
    headers: list[str] | None = None
    for line in lines:
        if not line.lstrip().startswith("|"):
            headers = None
            continue
        cells = table_cells(line)
        if not cells:
            continue
        if headers is None:
            headers = [cell.casefold() for cell in cells]
            continue
        if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        if not headers or headers[0] not in TASK_TABLE_HEADERS:
            continue
        identifier = cells[0]
        if not looks_like_identifier(identifier):
            continue
        status_index = next(
            (
                index
                for index, header in enumerate(headers)
                if header in {"status", "상태"}
            ),
            None,
        )
        status = (
            cells[status_index]
            if status_index is not None and status_index < len(cells)
            else "unknown"
        )
        tasks.append({"id": identifier, "status": status})
    return tasks


def epic_sections(text: str) -> list[tuple[str, list[str]]]:
    lines = text.splitlines()
    headings: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        match = LEVEL_TWO_HEADING.match(line)
        if match is not None and looks_like_identifier(match.group(1)):
            headings.append((index, match.group(1)))
    result: list[tuple[str, list[str]]] = []
    for position, (start, identifier) in enumerate(headings):
        end = headings[position + 1][0] if position + 1 < len(headings) else len(lines)
        result.append((identifier, lines[start:end]))
    return result


def resolve_document_link(source: Path, raw_target: str) -> Path | None:
    target = re.sub(r"""\s+(?:"[^"]*"|'[^']*')\s*$""", "", raw_target.strip())
    target = target.strip().strip("<>").split("#", 1)[0].split("?", 1)[0]
    if not target or "://" in target or target.startswith(("/", "\\")):
        return None
    parts: list[str] = []
    for part in (source.parent / target).parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if not parts:
                return None
            parts.pop()
        else:
            parts.append(part)
    return Path(*parts) if parts else None


def excluded_target(
    target: Path | None, inventory: set[Path], readable: set[Path]
) -> bool:
    return target is not None and target in inventory and target not in readable


def inspect_epic_lifecycle(
    epic: dict[str, Any],
    roadmap: Path,
    inventory: set[Path],
    readable: set[Path],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    detailed_count = epic.pop("_detailed_count")
    outcome_count = epic.pop("_outcome_count")
    detailed_raw = epic.pop("_detailed_raw")
    outcome_raw = epic.pop("_outcome_raw")
    status = epic["status"]
    tasks = epic["tasks"]
    contract_evidence = bool(detailed_count or outcome_count)

    if status == "unknown":
        if tasks or contract_evidence:
            findings.append(
                finding(
                    "epic_lifecycle_unverifiable",
                    "unverifiable",
                    f"{epic['id']} has no single recognized status.",
                    roadmap.as_posix(),
                )
            )
        return findings

    if status != "Completed" and status not in ACTIVE_EPIC_STATUSES:
        if tasks or contract_evidence:
            findings.append(
                finding(
                    "epic_lifecycle_unverifiable",
                    "unverifiable",
                    f"{epic['id']} uses lifecycle status {status!r}, whose active or completed meaning is not known.",
                    roadmap.as_posix(),
                )
            )
        return findings

    declared_fields = (
        (
            "Detailed SOT",
            detailed_count,
            detailed_raw,
            "epic_detailed_sot_invalid",
            "epic_detailed_sot_unverifiable",
        ),
        (
            "Canonical Outcomes",
            outcome_count,
            outcome_raw,
            "epic_canonical_outcomes_invalid",
            "epic_canonical_outcomes_unverifiable",
        ),
    )
    for label, count, raw_values, invalid_code, unverifiable_code in declared_fields:
        if count == 0:
            continue
        targets = [resolve_document_link(roadmap, value) for value in raw_values]
        valid = (
            count == 1
            and bool(targets)
            and all(
                target is not None
                and target.suffix.lower() == ".md"
                and target in inventory
                for target in targets
            )
        )
        if not valid:
            findings.append(
                finding(
                    invalid_code,
                    "error",
                    f"{epic['id']} declares {label} but does not link existing in-repository Markdown documents.",
                    roadmap.as_posix(),
                )
            )
            continue
        excluded = next(
            (
                target
                for target in targets
                if excluded_target(target, inventory, readable)
            ),
            None,
        )
        if excluded is not None:
            findings.append(
                finding(
                    unverifiable_code,
                    "unverifiable",
                    f"{epic['id']} links {label} content that was excluded.",
                    excluded.as_posix(),
                )
            )
    return findings


def inspect_roadmap(
    path: Path,
    scope: dict[str, Any],
    text: str,
    inventory: set[Path],
    readable: set[Path],
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    findings: list[dict[str, str]] = []
    epics: list[dict[str, Any]] = []
    seen: set[str] = set()
    for identifier, lines in epic_sections(text):
        detailed_count, detailed_raw = field_links(lines, "Detailed SOT")
        outcome_count, outcome_raw = field_links(lines, "Canonical Outcomes")
        epic = {
            "id": identifier,
            "status": status_value(lines),
            "tasks": task_rows(lines),
            "detailed_sot": detailed_raw,
            "canonical_outcomes": outcome_raw,
            "_detailed_count": detailed_count,
            "_outcome_count": outcome_count,
            "_detailed_raw": detailed_raw,
            "_outcome_raw": outcome_raw,
        }
        identifiers = [identifier] + [task["id"] for task in epic["tasks"]]
        counts = Counter(identifiers)
        duplicates = {value for value, count in counts.items() if count > 1}
        duplicates.update(value for value in identifiers if value in seen)
        for duplicate in sorted(duplicates):
            findings.append(
                finding(
                    "duplicate_roadmap_identifier",
                    "error",
                    f"{duplicate} is defined more than once in this roadmap.",
                    path.as_posix(),
                )
            )
        seen.update(identifiers)
        findings.extend(inspect_epic_lifecycle(epic, path, inventory, readable))
        epics.append(epic)
    return {
        "scope": scope["name"],
        "path": path.as_posix(),
        "epics": epics,
    }, findings


def inspect_repository(repository: Path) -> dict[str, Any]:
    tracked = tracked_paths(repository)
    untracked = untracked_paths(repository)
    ignored = documentation_inventory([], ignored_paths(repository))
    inventory = documentation_inventory(tracked, untracked)
    inventory_set = set(inventory)
    structure = discover_structure(repository)
    texts: dict[Path, str] = {}
    exclusions: Counter[str] = Counter()
    exclusions["ignored"] = sum(path.suffix.lower() == ".md" for path in ignored)
    findings: list[dict[str, str]] = []

    for path in inventory:
        if path.suffix.lower() != ".md":
            continue
        text, error = read_repository_text(repository, path)
        if text is not None:
            texts[path] = text
        elif error is not None:
            exclusions[error] += 1

    if structure["profile"] == "none":
        findings.append(
            finding("docs_missing", "error", "The docs directory is missing.")
        )
    elif structure["root_index"] is None:
        findings.append(
            finding("root_docs_index_missing", "error", "docs/README.md is missing.")
        )

    for scope in structure["scopes"]:
        candidates = scope["role_candidates"]
        for role, owners in candidates.items():
            if len(owners) > 1:
                findings.append(
                    finding(
                        "competing_role_owners",
                        "error",
                        f"Scope {scope['name']} has competing {role} owners.",
                    )
                )
        if scope["kind"] == "delivery":
            for role in ROLES:
                if not candidates[role]:
                    findings.append(
                        finding(
                            "documentation_role_missing",
                            "error",
                            f"Scope {scope['name']} has no discoverable {role} owner.",
                        )
                    )
        else:
            for role in set(ROLES) - SHARED_ROLES:
                if candidates[role]:
                    findings.append(
                        finding(
                            "forbidden_shared_role",
                            "error",
                            f"Shared scope {scope['name']} must not own {role}.",
                            candidates[role][0],
                        )
                    )

        for owners in candidates.values():
            for owner in owners:
                authority = owner_file(repository, Path(owner))
                if authority not in inventory_set:
                    findings.append(
                        finding(
                            "canonical_authority_uninventoried",
                            "unverifiable",
                            "A role owner is not tracked or visible as non-ignored input.",
                            authority.as_posix(),
                        )
                    )
                elif authority not in texts:
                    findings.append(
                        finding(
                            "canonical_authority_excluded",
                            "unverifiable",
                            "A role owner could not be read safely.",
                            authority.as_posix(),
                        )
                    )

    roadmaps: list[dict[str, Any]] = []
    readable = set(texts)
    for scope in structure["scopes"]:
        for owner in scope["role_candidates"]["roadmap"]:
            path = owner_file(repository, Path(owner))
            text = texts.get(path)
            if text is None:
                continue
            record, roadmap_findings = inspect_roadmap(
                path, scope, text, inventory_set, readable
            )
            roadmaps.append(record)
            findings.extend(roadmap_findings)

    if any(item["severity"] == "error" for item in findings):
        status = "nonconforming"
    elif any(item["severity"] == "unverifiable" for item in findings):
        status = "unverifiable"
    else:
        status = "conforming"

    return {
        "schema_version": SCHEMA_VERSION,
        "repository": str(repository),
        "structural_status": status,
        "documentation": structure,
        "roadmaps": roadmaps,
        "excluded_files": dict(sorted(exclusions.items())),
        "findings": sorted(
            findings,
            key=lambda item: (
                item["severity"],
                item["code"],
                item.get("path", ""),
                item["message"],
            ),
        ),
    }


def parse_arguments(arguments: list[str]) -> argparse.Namespace:
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    return parser.parse_args(arguments)


def main(arguments: list[str] | None = None) -> int:
    try:
        options = parse_arguments(arguments if arguments is not None else sys.argv[1:])
        requested = Path(options.repository).expanduser()
        if lexical_path_symlinked(requested):
            raise InspectionError(
                "repository_symlinked",
                "repository and its lexical ancestors must not be symlinks",
            )
        if not requested.is_dir():
            raise InspectionError(
                "repository_not_found", "repository must be an existing directory"
            )
        repository = canonical_git_root(requested.resolve())
        payload = inspect_repository(repository)
    except (InspectionError, OSError, subprocess.SubprocessError) as error:
        code = error.code if isinstance(error, InspectionError) else "inspection_failed"
        message = (
            str(error) if isinstance(error, InspectionError) else "inspection failed"
        )
        print(
            json.dumps(
                {
                    "schema_version": ERROR_SCHEMA_VERSION,
                    "error": {"code": code, "message": message},
                },
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
