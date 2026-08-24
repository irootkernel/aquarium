from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "plugins/aquarium/skills/docs-setup/scripts/inspect_docs.py"
ROLES = (
    "specs",
    "architecture",
    "architecture-decision-records",
    "implementation-tips",
    "roadmap",
    "deferred-feedback",
    "todo",
)


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True)


def write(path: Path, content: str = "# Index\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def initialize(repository: Path) -> None:
    repository.mkdir()
    run(["git", "init", "-q"], repository)
    run(["git", "config", "user.email", "test@example.com"], repository)
    run(["git", "config", "user.name", "Test"], repository)


def commit_all(repository: Path) -> None:
    run(["git", "add", "."], repository)
    run(["git", "commit", "-qm", "fixture"], repository)


def inspect(
    repository: Path,
) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--repository", str(repository)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": ""},
    )
    return result, json.loads(result.stdout)


def roadmap(epic: str = "EPIC-001", task: str = "TASK-001") -> str:
    return f"""\
# Roadmap

## {epic}: First

**Status:** `Planned`

| Task | Title | Status |
| --- | --- | --- |
| {task} | Foundation | Planned |
"""


def make_single_scope(
    repository: Path, *, epic: str = "EPIC-001", task: str = "TASK-001"
) -> None:
    write(repository / "docs/README.md", "# Documentation\n")
    for role in ROLES:
        content = roadmap(epic, task) if role == "roadmap" else "# Index\n"
        write(repository / "docs" / role / "README.md", content)


def make_delivery_scope(repository: Path, scope: str) -> None:
    for role in ROLES:
        content = roadmap() if role == "roadmap" else "# Index\n"
        write(repository / "docs" / scope / role / "README.md", content)


def test_single_scope_reports_canonical_ids_and_planned_migration(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "single"
    initialize(repository)
    make_single_scope(repository)
    write(repository / "src/reference.txt", "EPIC-001 is implemented by TASK-001.\n")
    commit_all(repository)

    result, payload = inspect(repository)

    assert result.returncode == 0
    assert payload["schema_version"] == "aquarium-docs-inspection/v1"
    assert payload["structural_status"] == "conforming"
    assert payload["documentation"]["profile"] == "single-scope"
    assert payload["id_scheme"] == "canonical-numeric"
    assert payload["migration"]["epics"][0]["planned_only_eligible"] is True
    identifiers = {
        (item["namespace"], item["id"]): item for item in payload["identifiers"]
    }
    assert identifiers[("default", "TASK-001")]["canonical_numeric"] is True
    assert any(
        reference["path"] == "src/reference.txt"
        for reference in identifiers[("default", "EPIC-001")]["references"]
    )


def test_multi_scope_allows_same_numeric_ids_in_distinct_roadmaps(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "multi"
    initialize(repository)
    write(repository / "docs/README.md", "# Documentation\n")
    for role in ("specs", "architecture", "architecture-decision-records"):
        write(repository / "docs/project" / role / "README.md")
    make_delivery_scope(repository, "server")
    make_delivery_scope(repository, "app")
    commit_all(repository)

    result, payload = inspect(repository)

    assert result.returncode == 0
    assert payload["structural_status"] == "conforming"
    assert payload["documentation"]["profile"] == "multi-scope"
    assert {scope["name"] for scope in payload["documentation"]["scopes"]} == {
        "project",
        "server",
        "app",
    }
    definitions = [
        item
        for item in payload["identifiers"]
        if item["id"] == "EPIC-001" and item["definitions"]
    ]
    assert {item["namespace"] for item in definitions} == {"app", "server"}
    assert not any(
        finding["code"] == "duplicate_roadmap_identifier"
        for finding in payload["findings"]
    )


@pytest.mark.parametrize(
    ("epic", "task"),
    [("CEPIC-27", "CTASK-204"), ("V2GRD", "V2GRD-001")],
)
def test_legacy_identifiers_are_adopted_without_numeric_rewrite(
    tmp_path: Path, epic: str, task: str
) -> None:
    repository = tmp_path / task.lower()
    initialize(repository)
    make_single_scope(repository, epic=epic, task=task)
    commit_all(repository)

    result, payload = inspect(repository)

    assert result.returncode == 0
    assert payload["documentation"]["profile"] == "legacy-adopt"
    assert payload["documentation"]["structural_profile"] == "single-scope"
    assert payload["id_scheme"] == "legacy"
    assert any(
        item["id"] == task and item["canonical_numeric"] is False
        for item in payload["identifiers"]
    )


def test_excludes_sensitive_binary_and_symlinked_tracked_files(tmp_path: Path) -> None:
    repository = tmp_path / "excluded"
    initialize(repository)
    make_single_scope(repository)
    write(repository / ".env.example", "TASK-999=secret\n")
    binary = repository / "asset.bin"
    binary.write_bytes(b"TASK-998\0value")
    target = tmp_path / "outside.txt"
    target.write_text("TASK-997\n", encoding="utf-8")
    (repository / "linked.md").symlink_to(target)
    run(["git", "add", "."], repository)
    run(["git", "commit", "-qm", "fixture"], repository)

    result, payload = inspect(repository)

    assert result.returncode == 0
    assert payload["structural_status"] == "unverifiable"
    assert payload["excluded_files"]["sensitive"] == 1
    assert payload["excluded_files"]["binary"] == 1
    assert payload["excluded_files"]["symlink"] == 1
    serialized = json.dumps(payload)
    assert "TASK-999" not in serialized
    assert "TASK-998" not in serialized
    assert "TASK-997" not in serialized


def test_migration_record_reports_stale_old_id_references(tmp_path: Path) -> None:
    repository = tmp_path / "migration"
    initialize(repository)
    make_single_scope(repository)
    write(
        repository / "docs/roadmap/id-migrations/2026-08-24.md",
        """\
# ID Migration

| Old ID | New ID | Kind | Title |
| --- | --- | --- | --- |
| OLD-001 | TASK-001 | Task | Foundation |
""",
    )
    write(repository / "docs/specs/legacy.md", "OLD-001 remains stale.\n")
    commit_all(repository)

    result, payload = inspect(repository)

    assert result.returncode == 0
    assert payload["structural_status"] == "nonconforming"
    assert payload["migration"]["records"][0]["stale_references"] == [
        {"path": "docs/specs/legacy.md", "line": 1, "namespace": "default"}
    ]
    assert any(
        finding["code"] == "stale_migrated_id_reference"
        for finding in payload["findings"]
    )


def test_migration_record_rejects_unquoted_preserved_path(tmp_path: Path) -> None:
    repository = tmp_path / "migration-unquoted"
    initialize(repository)
    make_single_scope(repository)
    write(
        repository / "docs/roadmap/id-migrations/2026-08-24.md",
        """\
# ID Migration

| Old ID | New ID | Kind | Title | Preserved Historical Paths |
| --- | --- | --- | --- | --- |
| OLD-001 | TASK-001 | Task | Foundation | docs/specs/legacy.md |
""",
    )
    write(repository / "docs/specs/legacy.md", "OLD-001 remains stale.\n")
    commit_all(repository)

    result, payload = inspect(repository)

    assert result.returncode == 0
    assert payload["structural_status"] == "nonconforming"
    assert payload["migration"]["records"][0]["stale_references"] == [
        {"path": "docs/specs/legacy.md", "line": 1, "namespace": "default"}
    ]
    assert {finding["code"] for finding in payload["findings"]} >= {
        "invalid_preserved_historical_path",
        "stale_migrated_id_reference",
    }


def test_rejects_non_root_and_symlinked_repository_paths(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    initialize(repository)
    make_single_scope(repository)
    commit_all(repository)
    nested = repository / "nested"
    nested.mkdir()
    link = tmp_path / "repository-link"
    link.symlink_to(repository, target_is_directory=True)

    nested_result, nested_payload = inspect(nested)
    link_result, link_payload = inspect(link)

    assert nested_result.returncode == 2
    assert nested_payload["error"]["code"] == "repository_not_root"
    assert link_result.returncode == 2
    assert link_payload["error"]["code"] == "repository_symlinked"


def test_multi_scope_migration_does_not_rewrite_another_scope_same_id(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "multi-migration"
    initialize(repository)
    write(repository / "docs/README.md", "# Documentation\n")
    write(repository / "docs/project/specs/README.md")
    make_delivery_scope(repository, "app")
    make_delivery_scope(repository, "server")
    write(repository / "docs/server/roadmap/README.md", roadmap(task="TASK-101"))
    write(
        repository / "docs/server/roadmap/id-migrations/2026-08-24.md",
        """\
# ID Migration

| Old ID | New ID | Kind | Title | Preserved Historical Paths |
| --- | --- | --- | --- | --- |
| TASK-001 | TASK-101 | Task | Foundation | - |
""",
    )
    write(repository / "docs/app/specs/reference.md", "TASK-001 remains current.\n")
    commit_all(repository)

    result, payload = inspect(repository)

    assert result.returncode == 0
    record = payload["migration"]["records"][0]
    assert record["namespace"] == "server"
    assert record["stale_references"] == []
    app_identifier = next(
        item
        for item in payload["identifiers"]
        if item["namespace"] == "app" and item["id"] == "TASK-001"
    )
    assert any(
        reference["path"] == "docs/app/specs/reference.md"
        and reference["namespace"] == "app"
        for reference in app_identifier["references"]
    )


def test_multi_scope_bare_shared_reference_is_unverifiable(tmp_path: Path) -> None:
    repository = tmp_path / "ambiguous-reference"
    initialize(repository)
    write(
        repository / "docs/README.md",
        "TASK-001 is shared.\napp:TASK-001 is qualified.\n",
    )
    make_delivery_scope(repository, "app")
    make_delivery_scope(repository, "server")
    commit_all(repository)

    result, payload = inspect(repository)

    assert result.returncode == 0
    assert payload["structural_status"] == "unverifiable"
    assert any(
        finding["code"] == "ambiguous_cross_scope_identifier_reference"
        and finding["path"] == "docs/README.md"
        for finding in payload["findings"]
    )
    app_identifier = next(
        item
        for item in payload["identifiers"]
        if item["namespace"] == "app" and item["id"] == "TASK-001"
    )
    assert {
        "path": "docs/README.md",
        "line": 2,
        "namespace": "app",
    } in app_identifier["references"]


def test_untracked_canonical_documents_are_inspected_after_apply(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "untracked-docs"
    initialize(repository)
    make_single_scope(repository)

    result, payload = inspect(repository)

    assert result.returncode == 0
    assert payload["structural_status"] == "conforming"
    assert payload["canonical_untracked_text_files"] == 8
    assert any(item["id"] == "EPIC-001" for item in payload["identifiers"])


def test_shared_scope_roles_are_optional_and_delivery_roles_are_forbidden(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "shared-scope"
    initialize(repository)
    write(repository / "docs/README.md", "# Documentation\n")
    write(repository / "docs/project/specs/README.md")
    make_delivery_scope(repository, "app")
    make_delivery_scope(repository, "server")
    commit_all(repository)

    _, conforming = inspect(repository)

    assert conforming["structural_status"] == "conforming"
    write(repository / "docs/project/roadmap/README.md", roadmap())
    commit_all(repository)

    _, forbidden = inspect(repository)

    assert forbidden["structural_status"] == "nonconforming"
    assert any(
        finding["code"] == "forbidden_shared_role"
        and finding["path"] == "docs/project/roadmap"
        for finding in forbidden["findings"]
    )


def test_competing_roadmap_aliases_are_reported(tmp_path: Path) -> None:
    repository = tmp_path / "competing-roadmaps"
    initialize(repository)
    make_single_scope(repository)
    write(repository / "docs/ROADMAP.md", roadmap("EPIC-002", "TASK-002"))
    commit_all(repository)

    _, payload = inspect(repository)

    assert payload["structural_status"] == "nonconforming"
    assert any(
        finding["code"] == "competing_role_owners" for finding in payload["findings"]
    )


def test_file_roadmap_discovers_sibling_migration_records(tmp_path: Path) -> None:
    repository = tmp_path / "file-roadmap"
    initialize(repository)
    write(repository / "docs/README.md", "# Documentation\n")
    for role in ROLES:
        if role == "roadmap":
            continue
        write(repository / "docs" / role / "README.md")
    write(repository / "docs/ROADMAP.md", roadmap(task="TASK-101"))
    write(
        repository / "docs/id-migrations/2026-08-24.md",
        """\
# ID Migration

| Old ID | New ID | Kind | Title | Preserved Historical Paths |
| --- | --- | --- | --- | --- |
| TASK-001 | TASK-101 | Task | Foundation | - |
""",
    )
    commit_all(repository)

    _, payload = inspect(repository)

    assert payload["migration"]["records"][0]["namespace"] == "default"
    assert payload["migration"]["records"][0]["path"] == (
        "docs/id-migrations/2026-08-24.md"
    )


def test_excluded_canonical_roadmap_makes_result_unverifiable(tmp_path: Path) -> None:
    repository = tmp_path / "non-utf8-roadmap"
    initialize(repository)
    make_single_scope(repository)
    (repository / "docs/roadmap/README.md").write_bytes(b"# Roadmap\n\xff")
    commit_all(repository)

    _, payload = inspect(repository)

    assert payload["structural_status"] == "unverifiable"
    assert payload["excluded_files"]["non_utf8"] == 1
    assert any(
        finding["code"] == "canonical_authority_excluded"
        and finding["path"] == "docs/roadmap/README.md"
        for finding in payload["findings"]
    )


def test_historical_paths_are_scoped_to_the_owning_roadmap(tmp_path: Path) -> None:
    repository = tmp_path / "historical-paths"
    initialize(repository)
    make_single_scope(repository, task="TASK-101")
    write(
        repository / "docs/roadmap/id-migrations/2026-08-24.md",
        """\
# ID Migration

| Old ID | New ID | Kind | Title | Preserved Historical Paths |
| --- | --- | --- | --- | --- |
| TASK-001 | TASK-101 | Task | Foundation | `docs/architecture-decision-records/0001.md` |
""",
    )
    write(repository / "docs/roadmap/archives/old.md", "TASK-001\n")
    write(repository / "docs/architecture-decision-records/0001.md", "TASK-001\n")
    write(repository / "vendor/archive/notes.md", "TASK-001\n")
    commit_all(repository)

    _, payload = inspect(repository)

    stale = payload["migration"]["records"][0]["stale_references"]
    assert stale == [
        {"path": "vendor/archive/notes.md", "line": 1, "namespace": "default"}
    ]


def test_reports_missing_docs_roles_and_cli_error_envelopes(tmp_path: Path) -> None:
    repository = tmp_path / "missing-docs"
    initialize(repository)

    _, missing_docs = inspect(repository)

    assert any(
        finding["code"] == "docs_missing" for finding in missing_docs["findings"]
    )
    write(repository / "docs/specs/README.md")

    _, missing_root = inspect(repository)

    assert any(
        finding["code"] == "root_docs_index_missing"
        for finding in missing_root["findings"]
    )
    write(repository / "docs/README.md", "# Documentation\n")

    _, missing_roles = inspect(repository)

    assert any(
        finding["code"] == "documentation_role_missing"
        for finding in missing_roles["findings"]
    )
    non_git = tmp_path / "not-git"
    non_git.mkdir()
    non_git_result, non_git_payload = inspect(non_git)
    invalid_result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert non_git_result.returncode == 2
    assert non_git_payload["error"]["code"] == "repository_not_git"
    assert invalid_result.returncode == 2
    assert json.loads(invalid_result.stdout)["error"]["code"] == "invalid_arguments"


def test_ignored_canonical_documents_are_not_accepted_as_authority(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "ignored-docs"
    initialize(repository)
    write(repository / ".gitignore", "docs/\n")
    make_single_scope(repository)
    commit_all(repository)

    _, payload = inspect(repository)

    assert payload["structural_status"] == "unverifiable"
    assert payload["canonical_untracked_text_files"] == 0
    assert any(
        finding["code"] == "canonical_authority_uninventoried"
        for finding in payload["findings"]
    )


def test_reports_duplicate_and_ambiguous_semantic_identifier(tmp_path: Path) -> None:
    repository = tmp_path / "ambiguous-id"
    initialize(repository)
    make_single_scope(repository, epic="V2GRD-001", task="V2GRD-001")
    commit_all(repository)

    _, payload = inspect(repository)

    codes = {finding["code"] for finding in payload["findings"]}
    assert "duplicate_roadmap_identifier" in codes
    assert "ambiguous_roadmap_identifier" in codes


def test_multi_scope_reports_unselected_root_roadmap(tmp_path: Path) -> None:
    repository = tmp_path / "root-roadmap"
    initialize(repository)
    write(repository / "docs/README.md", "# Documentation\n")
    make_delivery_scope(repository, "app")
    make_delivery_scope(repository, "server")
    write(repository / "docs/roadmap/README.md", roadmap("EPIC-999", "TASK-999"))
    commit_all(repository)

    _, payload = inspect(repository)

    assert any(
        finding["code"] == "unselected_root_role_owner"
        and finding["path"] == "docs/roadmap"
        for finding in payload["findings"]
    )


def test_symlinked_role_ancestor_is_not_an_owner(tmp_path: Path) -> None:
    repository = tmp_path / "symlink-role"
    initialize(repository)
    make_single_scope(repository)
    target = tmp_path / "external-architecture"
    target.mkdir()
    write(target / "README.md")
    architecture = repository / "docs/architecture"
    for child in architecture.iterdir():
        child.unlink()
    architecture.rmdir()
    architecture.symlink_to(target, target_is_directory=True)
    run(["git", "add", "-A"], repository)
    run(["git", "commit", "-qm", "fixture"], repository)

    _, payload = inspect(repository)

    assert any(
        finding["code"] == "documentation_role_missing"
        and "architecture" in finding["message"]
        for finding in payload["findings"]
    )
