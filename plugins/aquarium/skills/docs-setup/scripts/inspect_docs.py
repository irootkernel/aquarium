#!/usr/bin/env python3
"""Inspect documentation roles and roadmap identifiers without modifying a repository."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "aquarium-docs-inspection/v1"
ERROR_SCHEMA_VERSION = "aquarium-docs-inspection-error/v1"
MAX_TEXT_BYTES = 8 * 1024 * 1024
ROLES = (
    "specs",
    "architecture",
    "architecture-decision-records",
    "implementation-tips",
    "roadmap",
    "deferred-feedback",
    "todo",
)
ROLE_ALIASES = {
    "specs": ("specs",),
    "architecture": ("architecture",),
    "architecture-decision-records": ("architecture-decision-records", "adr"),
    "implementation-tips": ("implementation-tips", "guides"),
    "roadmap": ("roadmap", "ROADMAP.md", "roadmap.md"),
    "deferred-feedback": ("deferred-feedback", "deferred-feedback.md"),
    "todo": ("todo", "TODO.md", "todo.md"),
}
SENSITIVE_COMPONENT = re.compile(
    r"(?i)(?:^|[._-])(?:auth(?:entication)?|credentials?|keys?|secrets?|tokens?)(?:[._-]|$)"
)
CANONICAL_EPIC = re.compile(r"^EPIC-([0-9]{3,})$")
CANONICAL_TASK = re.compile(r"^TASK-([0-9]{3,})$")
ID_TOKEN = re.compile(
    r"(?<![A-Za-z0-9])(?:"
    r"(?:C?EPIC|C?TASK)-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*"
    r"|[A-Z][A-Z0-9]{2,}-[0-9]{1,}(?:-[A-Z0-9]+)*"
    r"|[a-z][a-z0-9]*(?:-[a-z0-9]+)*-[0-9]{3,}"
    r")(?![A-Za-z0-9])"
)
HEADING_ID = re.compile(
    r"^##\s+(`?)([A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*)\1(?:\s*[—:]|\s+-|\s*$)"
)
TABLE_ID = re.compile(r"^\|\s*`?([A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)+)`?\s*\|")
STATUS_LINE = re.compile(
    r"^\*\*(?:Status|상태):\*\*\s*`?([^`\n]+?)`?\s*$",
    re.IGNORECASE | re.MULTILINE,
)
LEVEL_TWO_HEADING = re.compile(r"(?m)^##\s+.*$")
LEGACY_EPIC_CODE = re.compile(r"^(?=.*[0-9])[A-Z][A-Z0-9]{2,}$")
ALLOWED_STATUSES = {
    "Planned",
    "In Progress",
    "In Review",
    "Completed",
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
    parts = absolute.parts
    current = Path(parts[0])
    for part in parts[1:]:
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
    command = [
        "git",
        "-c",
        "core.fsmonitor=false",
        "-c",
        "core.preloadindex=false",
        "-C",
        str(repository),
        *arguments,
    ]
    return subprocess.run(
        command,
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


def tracked_paths(repository: Path) -> list[Path]:
    result = git_command(
        repository, ["--literal-pathspecs", "ls-files", "-z", "--cached"]
    )
    if result.returncode != 0:
        raise InspectionError(
            "git_inventory_failed", "Git tracked-file inventory failed"
        )
    try:
        values = result.stdout.decode("utf-8").split("\0")
    except UnicodeError as error:
        raise InspectionError(
            "tracked_path_invalid", "a tracked path is not valid UTF-8"
        ) from error
    return [Path(value) for value in values if value]


def untracked_paths(repository: Path) -> list[Path]:
    result = git_command(
        repository,
        ["--literal-pathspecs", "ls-files", "-z", "--others", "--exclude-standard"],
    )
    if result.returncode != 0:
        raise InspectionError(
            "git_inventory_failed", "Git untracked-file inventory failed"
        )
    try:
        values = result.stdout.decode("utf-8").split("\0")
    except UnicodeError as error:
        raise InspectionError(
            "untracked_path_invalid", "an untracked path is not valid UTF-8"
        ) from error
    return [Path(value) for value in values if value]


def sensitive_path(relative: Path) -> bool:
    return any(
        part.lower().startswith(".env") or SENSITIVE_COMPONENT.search(part)
        for part in relative.parts
    )


def safe_regular_file(
    repository: Path, relative: Path
) -> tuple[Path | None, str | None]:
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
        mode = current.stat().st_mode
    except OSError:
        return None, "unreadable"
    if not stat.S_ISREG(mode):
        return None, "not_regular"
    return current, None


def read_repository_text(
    repository: Path, relative: Path
) -> tuple[str | None, str | None]:
    if sensitive_path(relative):
        return None, "sensitive"
    path, error = safe_regular_file(repository, relative)
    if error:
        return None, error
    assert path is not None
    try:
        if path.stat().st_size > MAX_TEXT_BYTES:
            return None, "oversized"
        data = path.read_bytes()
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
    for alias in ROLE_ALIASES[role]:
        relative = base / alias
        path = repository / relative
        if path.is_dir() and not lexical_path_symlinked(path):
            index = path / "README.md"
            if index.is_file() and not lexical_path_symlinked(index):
                candidates.append(relative.as_posix())
        elif path.is_file() and not lexical_path_symlinked(path):
            candidates.append(relative.as_posix())
    return candidates


def scope_record(repository: Path, name: str, kind: str, base: Path) -> dict[str, Any]:
    candidates = {role: path_role_candidates(repository, base, role) for role in ROLES}
    return {
        "name": name,
        "kind": kind,
        "base": base.as_posix(),
        "roles": {
            role: values[0] if len(values) == 1 else None
            for role, values in candidates.items()
        },
        "role_candidates": candidates,
    }


def discover_structure(repository: Path) -> dict[str, Any]:
    docs = repository / "docs"
    if not docs.is_dir() or docs.is_symlink():
        return {
            "profile": "none",
            "structural_profile": "none",
            "root_index": None,
            "scopes": [],
        }

    child_scopes: list[str] = []
    for child in sorted(docs.iterdir(), key=lambda item: item.name):
        if not child.is_dir() or child.is_symlink() or child.name.startswith("."):
            continue
        base = Path("docs") / child.name
        if child.name == "project":
            continue
        candidates = {
            role: path_role_candidates(repository, base, role) for role in ROLES
        }
        role_count = sum(bool(values) for values in candidates.values())
        if candidates["roadmap"] and role_count >= 3:
            child_scopes.append(child.name)

    scopes: list[dict[str, Any]] = []
    if child_scopes:
        structural_profile = "multi-scope"
        for name in child_scopes:
            base = Path("docs") / name
            scopes.append(scope_record(repository, name, "delivery", base))
        project_base = Path("docs/project")
        project = repository / project_base
        if project.is_dir() and not lexical_path_symlinked(project):
            scopes.insert(
                0, scope_record(repository, "project", "shared", project_base)
            )
    else:
        structural_profile = "single-scope"
        base = Path("docs")
        scopes.append(scope_record(repository, "default", "delivery", base))

    root_role_candidates = (
        {role: path_role_candidates(repository, Path("docs"), role) for role in ROLES}
        if structural_profile == "multi-scope"
        else {}
    )

    return {
        "profile": structural_profile,
        "structural_profile": structural_profile,
        "root_index": (
            "docs/README.md"
            if (docs / "README.md").is_file()
            and not lexical_path_symlinked(docs / "README.md")
            else None
        ),
        "scopes": scopes,
        "unselected_root_role_candidates": root_role_candidates,
    }


def all_role_candidates(structure: dict[str, Any]) -> set[Path]:
    result: set[Path] = set()
    for scope in structure["scopes"]:
        for candidates in scope["role_candidates"].values():
            result.update(Path(value) for value in candidates)
    for candidates in structure.get("unselected_root_role_candidates", {}).values():
        result.update(Path(value) for value in candidates)
    return result


def role_owner_file(repository: Path, owner: Path) -> Path:
    path = repository / owner
    return owner / "README.md" if path.is_dir() else owner


def canonical_untracked_paths(
    repository: Path, structure: dict[str, Any], untracked: list[Path]
) -> list[Path]:
    owners = all_role_candidates(structure)
    file_roadmap_migration_roots = {
        root.parent / "id-migrations"
        for _, root in roadmap_roots(structure)
        if (repository / root).is_file()
    }
    result: list[Path] = []
    for relative in untracked:
        if relative == Path("docs/README.md"):
            result.append(relative)
            continue
        for owner in owners:
            path = repository / owner
            if (path.is_dir() and relative.is_relative_to(owner)) or relative == owner:
                result.append(relative)
                break
        else:
            if any(
                relative.is_relative_to(root) for root in file_roadmap_migration_roots
            ):
                result.append(relative)
    return sorted(set(result), key=lambda path: path.as_posix())


def roadmap_roots(structure: dict[str, Any]) -> list[tuple[str, Path]]:
    result: list[tuple[str, Path]] = []
    for scope in structure["scopes"]:
        for value in scope["role_candidates"]["roadmap"]:
            result.append((scope["name"], Path(value)))
    return result


def path_belongs_to_roadmap(
    relative: Path, root: Path, repository: Path | None = None
) -> bool:
    is_file_root = root.suffix.lower() == ".md"
    if repository is not None:
        is_file_root = (repository / root).is_file()
    if is_file_root:
        return relative == root or relative.is_relative_to(
            root.parent / "id-migrations"
        )
    return relative == root or relative.is_relative_to(root)


def roadmap_paths(
    repository: Path, structure: dict[str, Any], inventory: list[Path]
) -> list[Path]:
    roots = [root for _, root in roadmap_roots(structure)]
    result: list[Path] = []
    for relative in inventory:
        for root in roots:
            if path_belongs_to_roadmap(relative, root, repository):
                if relative.suffix.lower() == ".md":
                    result.append(relative)
                break
    return sorted(set(result), key=lambda path: path.as_posix())


def roadmap_namespace(relative: Path, structure: dict[str, Any]) -> str:
    for namespace, root in roadmap_roots(structure):
        if path_belongs_to_roadmap(relative, root):
            return namespace
    return "unknown"


def path_namespace(relative: Path, structure: dict[str, Any]) -> str:
    for scope in structure["scopes"]:
        if scope["kind"] != "delivery":
            continue
        base = Path(scope["base"])
        if relative == base or relative.is_relative_to(base):
            return scope["name"]
    return "unknown"


def epic_blocks(text: str) -> list[tuple[str, int, str]]:
    headings = list(LEVEL_TWO_HEADING.finditer(text))
    result: list[tuple[str, int, str]] = []
    for index, heading in enumerate(headings):
        parsed = HEADING_ID.match(heading.group(0))
        if parsed is None or not (
            ID_TOKEN.fullmatch(parsed.group(2))
            or LEGACY_EPIC_CODE.fullmatch(parsed.group(2))
        ):
            continue
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        line = text.count("\n", 0, heading.start()) + 1
        result.append((parsed.group(2), line, text[heading.start() : end]))
    return result


def table_cells(line: str) -> list[str]:
    return [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]


def task_rows_with_lines(block: str, start_line: int = 1) -> list[tuple[str, str, int]]:
    rows: list[tuple[str, str, int]] = []
    in_task_table = False
    for offset, line in enumerate(block.splitlines()):
        if not line.startswith("|"):
            in_task_table = False
            continue
        cells = table_cells(line)
        first = cells[0] if cells else ""
        if first.lower() in {"task", "task id"}:
            in_task_table = True
            continue
        if not in_task_table or set(first) <= {"-", ":"}:
            continue
        if ID_TOKEN.fullmatch(first) is None:
            continue
        status = next(
            (cell for cell in cells[1:] if cell in ALLOWED_STATUSES), "unknown"
        )
        rows.append((first, status, start_line + offset))
    return rows


def definition_ids(text: str) -> list[tuple[str, int, str]]:
    result: list[tuple[str, int, str]] = []
    for identifier, line, block in epic_blocks(text):
        result.append((identifier, line, "heading"))
        result.extend(
            (task, task_line, "table")
            for task, _, task_line in task_rows_with_lines(block, line)
        )
    return result


def identifier_kind(identifier: str, source: str) -> str:
    if identifier.startswith(("EPIC-", "CEPIC-")):
        return "epic"
    if identifier.startswith(("TASK-", "CTASK-")):
        return "task"
    return "epic" if source == "heading" else "task"


def looks_like_roadmap_id(value: str) -> bool:
    return bool(
        re.fullmatch(r"[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*", value)
        and re.search(r"[0-9]", value)
    )


def preserved_paths(value: str) -> tuple[list[str], list[str]]:
    if not value or value == "-":
        return [], []
    accepted: list[str] = []
    rejected: list[str] = []
    for raw in re.split(r"(?i)<br\s*/?>", value):
        candidate = raw.strip().strip("`")
        path = Path(candidate)
        if (
            not candidate
            or path.is_absolute()
            or "\\" in candidate
            or any(character in candidate for character in "*?[]")
            or any(part in {"", ".", ".."} for part in path.parts)
        ):
            rejected.append(candidate)
        else:
            accepted.append(path.as_posix())
    return sorted(set(accepted)), sorted(set(rejected))


def migration_records(
    roadmap_files: list[Path], texts: dict[Path, str], structure: dict[str, Any]
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for relative in roadmap_files:
        if "id-migrations" not in relative.parts:
            continue
        text = texts.get(relative)
        if text is None:
            continue
        namespace = roadmap_namespace(relative, structure)
        for number, line in enumerate(text.splitlines(), start=1):
            if not line.startswith("|"):
                continue
            cells = [
                cell.strip().strip("`") for cell in line.strip().strip("|").split("|")
            ]
            if len(cells) < 2 or not all(
                looks_like_roadmap_id(value) for value in cells[:2]
            ):
                continue
            accepted, rejected = preserved_paths(cells[4] if len(cells) > 4 else "")
            records.append(
                {
                    "namespace": namespace,
                    "old_id": cells[0],
                    "new_id": cells[1],
                    "path": relative.as_posix(),
                    "line": number,
                    "preserved_historical_paths": accepted,
                    "invalid_preserved_historical_paths": rejected,
                }
            )
    return sorted(
        records,
        key=lambda item: (
            item["namespace"],
            item["old_id"],
            item["new_id"],
            item["path"],
            item["line"],
        ),
    )


def preserved_historical_reference(
    reference: dict[str, Any], record: dict[str, Any], structure: dict[str, Any]
) -> bool:
    relative = Path(reference["path"])
    if relative.as_posix() in record["preserved_historical_paths"]:
        return True
    for namespace, root in roadmap_roots(structure):
        if namespace != record["namespace"]:
            continue
        archive_base = root.parent if root.suffix.lower() == ".md" else root
        if relative.is_relative_to(archive_base):
            remainder = relative.relative_to(archive_base)
            if any(part in {"archive", "archives"} for part in remainder.parts):
                return True
    return False


def inspect_identifiers(
    roadmap_files: list[Path],
    texts: dict[Path, str],
    structure: dict[str, Any],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, str]],
    str,
]:
    definitions: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    kinds: dict[tuple[str, str], set[str]] = defaultdict(set)
    for relative in roadmap_files:
        if "id-migrations" in relative.parts:
            continue
        text = texts.get(relative)
        if text is None:
            continue
        namespace = roadmap_namespace(relative, structure)
        for identifier, line, source in definition_ids(text):
            kind = identifier_kind(identifier, source)
            key = (namespace, identifier)
            definitions[key].append(
                {"path": relative.as_posix(), "line": line, "source": source}
            )
            kinds[key].add(kind)

    records = migration_records(roadmap_files, texts, structure)
    known_ids = {identifier for _, identifier in definitions}
    known_ids.update(record["old_id"] for record in records)
    known_ids.update(record["new_id"] for record in records)
    reference_pattern = (
        re.compile(
            r"(?<![A-Za-z0-9])(?:"
            + "|".join(
                re.escape(identifier)
                for identifier in sorted(
                    known_ids, key=lambda value: (-len(value), value)
                )
            )
            + r")(?![A-Za-z0-9])"
        )
        if known_ids
        else None
    )
    id_namespaces: dict[str, set[str]] = defaultdict(set)
    for namespace, identifier in definitions:
        id_namespaces[identifier].add(namespace)
    for record in records:
        id_namespaces[record["old_id"]].add(record["namespace"])
        id_namespaces[record["new_id"]].add(record["namespace"])

    references: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    ambiguous_references: dict[str, list[dict[str, Any]]] = defaultdict(list)
    scope_names = {
        scope["name"] for scope in structure["scopes"] if scope["kind"] == "delivery"
    }
    for relative in sorted(texts, key=lambda path: path.as_posix()):
        for number, line in enumerate(texts[relative].splitlines(), start=1):
            if reference_pattern is None:
                continue
            for match in reference_pattern.finditer(line):
                identifier = match.group(0)
                namespace = path_namespace(relative, structure)
                for scope_name in scope_names:
                    if line[
                        max(0, match.start() - len(scope_name) - 1) : match.start()
                    ] == (scope_name + ":"):
                        namespace = scope_name
                        break
                if namespace == "unknown" and len(id_namespaces[identifier]) == 1:
                    namespace = next(iter(id_namespaces[identifier]))
                reference = {
                    "path": relative.as_posix(),
                    "line": number,
                    "namespace": namespace,
                }
                if namespace == "unknown":
                    ambiguous_references[identifier].append(reference)
                else:
                    references[(namespace, identifier)].append(reference)

    all_keys = sorted(definitions)
    identifiers: list[dict[str, Any]] = []
    noncanonical_defined = False
    for namespace, identifier in all_keys:
        key = (namespace, identifier)
        resolved_kinds = sorted(kinds.get(key, set()))
        kind = resolved_kinds[0] if len(resolved_kinds) == 1 else "unknown"
        canonical = bool(
            (kind == "epic" and CANONICAL_EPIC.fullmatch(identifier))
            or (kind == "task" and CANONICAL_TASK.fullmatch(identifier))
        )
        if key in definitions and not canonical:
            noncanonical_defined = True
        identifiers.append(
            {
                "namespace": namespace,
                "id": identifier,
                "kind": kind,
                "canonical_numeric": canonical,
                "definitions": definitions.get(key, []),
                "references": sorted(
                    references.get(key, []) + ambiguous_references.get(identifier, []),
                    key=lambda item: (item["path"], item["line"], item["namespace"]),
                ),
            }
        )

    findings: list[dict[str, str]] = []
    for identifier, values in sorted(ambiguous_references.items()):
        for reference in values:
            findings.append(
                finding(
                    "ambiguous_cross_scope_identifier_reference",
                    "unverifiable",
                    f"{identifier} matches multiple roadmap namespaces; qualify it as scope:{identifier}.",
                    reference["path"],
                )
            )
    for namespace, identifier in sorted(definitions):
        key = (namespace, identifier)
        locations = definitions[key]
        if len(locations) > 1:
            findings.append(
                finding(
                    "duplicate_roadmap_identifier",
                    "error",
                    f"{namespace}:{identifier} has {len(locations)} roadmap definitions.",
                )
            )
        if len(kinds[key]) > 1:
            findings.append(
                finding(
                    "ambiguous_roadmap_identifier",
                    "error",
                    f"{namespace}:{identifier} is used as both an epic and a task definition.",
                )
            )

    for record in records:
        for invalid in record.pop("invalid_preserved_historical_paths"):
            findings.append(
                finding(
                    "invalid_preserved_historical_path",
                    "error",
                    f"The preserved historical path {invalid!r} is not a safe repository-relative path.",
                    record["path"],
                )
            )
        stale = [
            reference
            for reference in references.get((record["namespace"], record["old_id"]), [])
            if "id-migrations" not in Path(reference["path"]).parts
            and not preserved_historical_reference(reference, record, structure)
        ]
        record["stale_references"] = stale
        for reference in stale:
            findings.append(
                finding(
                    "stale_migrated_id_reference",
                    "error",
                    f"{record['old_id']} remains outside its migration record at line {reference['line']}.",
                    reference["path"],
                )
            )

    migrations = migration_analysis(roadmap_files, texts)
    id_scheme = "legacy" if noncanonical_defined else "canonical-numeric"
    return identifiers, migrations, records, findings, id_scheme


def task_rows(block: str) -> list[tuple[str, str]]:
    return [
        (identifier, status) for identifier, status, _ in task_rows_with_lines(block)
    ]


def epic_status(block: str) -> str:
    status_match = STATUS_LINE.search(block)
    if status_match is None:
        return "unknown"
    value = status_match.group(1).strip()
    return value if value in ALLOWED_STATUSES else "unknown"


def migration_analysis(
    roadmap_files: list[Path], texts: dict[Path, str]
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for relative in roadmap_files:
        if (
            any(part in {"archive", "archives"} for part in relative.parts)
            or "id-migrations" in relative.parts
        ):
            continue
        text = texts.get(relative)
        if text is None:
            continue
        for identifier, _, block in epic_blocks(text):
            status = epic_status(block)
            tasks = task_rows(block)
            eligible = status == "Planned" and all(
                task_status == "Planned" for _, task_status in tasks
            )
            result.append(
                {
                    "epic": identifier,
                    "path": relative.as_posix(),
                    "status": status,
                    "tasks": [
                        {"id": task, "status": task_status}
                        for task, task_status in tasks
                    ],
                    "planned_only_eligible": eligible,
                    "reason": (
                        "planned_epic_without_child_tasks"
                        if eligible and not tasks
                        else "epic_and_all_tasks_planned"
                        if eligible
                        else "status_or_task_ownership_not_eligible"
                    ),
                }
            )
    return sorted(result, key=lambda item: (item["path"], item["epic"]))


def inspect_repository(repository: Path) -> dict[str, Any]:
    tracked = tracked_paths(repository)
    untracked = untracked_paths(repository)
    structure = discover_structure(repository)
    findings: list[dict[str, str]] = []
    texts: dict[Path, str] = {}
    exclusions = Counter()
    canonical_untracked = canonical_untracked_paths(repository, structure, untracked)
    inventory = sorted(
        set(tracked + canonical_untracked), key=lambda path: path.as_posix()
    )
    tracked_set = set(tracked)
    canonical_untracked_set = set(canonical_untracked)
    canonical_authorities = {
        role_owner_file(repository, owner) for owner in all_role_candidates(structure)
    }
    if structure["root_index"] is not None:
        canonical_authorities.add(Path(structure["root_index"]))

    for relative in inventory:
        text, error = read_repository_text(repository, relative)
        if text is not None:
            texts[relative] = text
            continue
        assert error is not None
        exclusions[error] += 1
        if relative in canonical_authorities:
            findings.append(
                finding(
                    "canonical_authority_excluded",
                    "unverifiable",
                    f"A canonical documentation authority was excluded as {error}.",
                    relative.as_posix(),
                )
            )
        elif error == "symlink":
            findings.append(
                finding(
                    "tracked_symlink_excluded",
                    "unverifiable",
                    "A tracked symlink was excluded from inspection.",
                    relative.as_posix(),
                )
            )

    inventory_set = set(inventory)
    for authority in sorted(canonical_authorities, key=lambda path: path.as_posix()):
        if authority not in inventory_set:
            findings.append(
                finding(
                    "canonical_authority_uninventoried",
                    "unverifiable",
                    "A canonical documentation authority is neither tracked nor non-ignored untracked input.",
                    authority.as_posix(),
                )
            )

    if structure["profile"] == "none":
        findings.append(
            finding("docs_missing", "error", "The docs directory is missing.")
        )
    elif structure["root_index"] is None:
        findings.append(
            finding("root_docs_index_missing", "error", "docs/README.md is missing.")
        )

    for scope in structure["scopes"]:
        for role, candidates in scope["role_candidates"].items():
            if len(candidates) > 1:
                findings.append(
                    finding(
                        "competing_role_owners",
                        "error",
                        f"Scope {scope['name']} has competing {role} owners: {', '.join(candidates)}.",
                    )
                )
        if scope["kind"] == "delivery":
            for role in ROLES:
                if scope["role_candidates"][role]:
                    continue
                findings.append(
                    finding(
                        "documentation_role_missing",
                        "error",
                        f"Scope {scope['name']} has no discoverable {role} owner.",
                    )
                )
        else:
            for role in ROLES[3:]:
                if scope["role_candidates"][role]:
                    findings.append(
                        finding(
                            "forbidden_shared_role",
                            "error",
                            f"Shared scope {scope['name']} must not own {role}.",
                            scope["role_candidates"][role][0],
                        )
                    )

    for role, candidates in structure.get(
        "unselected_root_role_candidates", {}
    ).items():
        for candidate in candidates:
            findings.append(
                finding(
                    "unselected_root_role_owner",
                    "error",
                    f"A multi-scope repository has an unselected root {role} owner.",
                    candidate,
                )
            )

    roadmaps = roadmap_paths(repository, structure, inventory)
    identifiers, migrations, migration_history, id_findings, id_scheme = (
        inspect_identifiers(roadmaps, texts, structure)
    )
    findings.extend(id_findings)

    if structure["profile"] != "none" and id_scheme == "legacy":
        structure["profile"] = "legacy-adopt"

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
        "roadmaps": [path.as_posix() for path in roadmaps],
        "id_scheme": id_scheme,
        "identifiers": identifiers,
        "migration": {
            "policy": "planned_epic_and_all_child_tasks_only",
            "epics": migrations,
            "records": migration_history,
            "semantic_scope": "conservative_markdown_only",
        },
        "tracked_text_files": sum(path in tracked_set for path in texts),
        "canonical_untracked_text_files": sum(
            path in canonical_untracked_set for path in texts
        ),
        "inspected_text_files": len(texts),
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
        "content_semantics": "not_evaluated",
        "runtime_truth": "not_evaluated",
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
        repository = requested.resolve()
        repository = canonical_git_root(repository)
        payload = inspect_repository(repository)
    except (InspectionError, subprocess.TimeoutExpired) as error:
        if isinstance(error, subprocess.TimeoutExpired):
            code = "git_timeout"
            message = "Git inspection timed out"
        else:
            code = error.code
            message = str(error)
        payload = {
            "schema_version": ERROR_SCHEMA_VERSION,
            "error": {"code": code, "message": message},
        }
        print(json.dumps(payload, sort_keys=True))
        return 2
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
