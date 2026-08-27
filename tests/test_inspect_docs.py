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
    "ops",
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


def roadmap(
    *,
    status: str = "Planned",
    task: bool = True,
    detailed_sot: str | None = "../todo/TODO-EPIC-001.md",
    outcomes: str | None = None,
    newline: str = "\n",
) -> str:
    lines = ["# Roadmap", "", "## EPIC-001: First", "", f"**Status:** `{status}`"]
    if detailed_sot is not None:
        lines.extend(["", f"**Detailed SOT:** [Dossier]({detailed_sot})"])
    if outcomes is not None:
        lines.extend(["", f"**Canonical Outcomes:** [Outcome]({outcomes})"])
    if task:
        lines.extend(
            [
                "",
                "| Task | Title | Status |",
                "| --- | --- | --- |",
                f"| TASK-001 | Foundation | {status} |",
            ]
        )
    return newline.join(lines) + newline


def make_scope(repository: Path, base: Path = Path("docs")) -> None:
    for role in ROLES:
        content = roadmap() if role == "roadmap" else "# Index\n"
        write(repository / base / role / "README.md", content)
    write(repository / base / "todo/TODO-EPIC-001.md", "# Dossier\n")


def make_single_scope(repository: Path) -> None:
    write(repository / "docs/README.md", "# Documentation\n")
    make_scope(repository)


def finding_codes(payload: dict[str, object]) -> set[str]:
    findings = payload["findings"]
    assert isinstance(findings, list)
    return {item["code"] for item in findings}


def test_v2_reports_only_minimum_structural_contract(tmp_path: Path) -> None:
    repository = tmp_path / "single"
    initialize(repository)
    make_single_scope(repository)
    write(repository / "src/reference.txt", "EPIC-001 TASK-001\n")
    commit_all(repository)

    result, payload = inspect(repository)

    assert result.returncode == 0
    assert payload["schema_version"] == "aquarium-docs-inspection/v2"
    assert payload["structural_status"] == "conforming"
    assert set(payload) == {
        "schema_version",
        "repository",
        "structural_status",
        "documentation",
        "roadmaps",
        "excluded_files",
        "findings",
    }
    assert payload["documentation"]["profile"] == "single-scope"
    assert payload["roadmaps"][0]["epics"][0]["tasks"] == [
        {"id": "TASK-001", "status": "Planned"}
    ]


def test_multi_scope_discovers_independent_delivery_owners(tmp_path: Path) -> None:
    repository = tmp_path / "multi"
    initialize(repository)
    write(repository / "docs/README.md", "# Documentation\n")
    for role in ("specs", "architecture", "architecture-decision-records"):
        write(repository / "docs/project" / role / "README.md")
    make_scope(repository, Path("docs/server"))
    make_scope(repository, Path("docs/app"))
    commit_all(repository)

    _, payload = inspect(repository)

    assert payload["structural_status"] == "conforming"
    assert payload["documentation"]["profile"] == "multi-scope"
    assert {scope["name"] for scope in payload["documentation"]["scopes"]} == {
        "project",
        "server",
        "app",
    }
    assert {roadmap["scope"] for roadmap in payload["roadmaps"]} == {"server", "app"}


def test_missing_and_competing_role_owners_are_nonconforming(tmp_path: Path) -> None:
    repository = tmp_path / "roles"
    initialize(repository)
    make_single_scope(repository)
    (repository / "docs/ops/README.md").unlink()
    write(repository / "docs/ROADMAP.md", roadmap())
    commit_all(repository)

    _, payload = inspect(repository)

    assert payload["structural_status"] == "nonconforming"
    assert finding_codes(payload) >= {
        "documentation_role_missing",
        "competing_role_owners",
    }


def test_runbooks_alias_can_own_operations(tmp_path: Path) -> None:
    repository = tmp_path / "runbooks"
    initialize(repository)
    make_single_scope(repository)
    (repository / "docs/ops/README.md").unlink()
    write(repository / "docs/runbooks/README.md")
    commit_all(repository)

    _, payload = inspect(repository)

    assert payload["structural_status"] == "conforming"
    roles = payload["documentation"]["scopes"][0]["role_candidates"]
    assert roles["ops"] == ["docs/runbooks"]


def test_active_epic_with_tasks_requires_dossier(tmp_path: Path) -> None:
    repository = tmp_path / "missing-dossier"
    initialize(repository)
    make_single_scope(repository)
    write(repository / "docs/roadmap/README.md", roadmap(detailed_sot=None))
    commit_all(repository)

    _, payload = inspect(repository)

    assert payload["structural_status"] == "nonconforming"
    assert "active_epic_dossier_missing" in finding_codes(payload)


@pytest.mark.parametrize(
    "target",
    ["../../outside.md", "/absolute.md", "../specs/README.md", "../todo/missing.md"],
)
def test_active_epic_rejects_unsafe_or_non_todo_dossier(
    tmp_path: Path, target: str
) -> None:
    repository = tmp_path / target.replace("/", "-")
    initialize(repository)
    make_single_scope(repository)
    write(repository / "docs/roadmap/README.md", roadmap(detailed_sot=target))
    commit_all(repository)

    _, payload = inspect(repository)

    assert "active_epic_dossier_invalid" in finding_codes(payload)


def test_active_epic_rejects_todo_owner_index_as_dossier(tmp_path: Path) -> None:
    repository = tmp_path / "todo-owner-dossier"
    initialize(repository)
    make_single_scope(repository)
    write(
        repository / "docs/roadmap/README.md", roadmap(detailed_sot="../todo/README.md")
    )
    commit_all(repository)

    _, payload = inspect(repository)

    assert "active_epic_dossier_invalid" in finding_codes(payload)


def test_taskless_placeholder_needs_no_dossier(tmp_path: Path) -> None:
    repository = tmp_path / "placeholder"
    initialize(repository)
    make_single_scope(repository)
    write(repository / "docs/roadmap/README.md", roadmap(task=False, detailed_sot=None))
    (repository / "docs/todo/TODO-EPIC-001.md").unlink()
    commit_all(repository)

    _, payload = inspect(repository)

    assert payload["structural_status"] == "conforming"


def test_active_epic_rejects_canonical_outcomes_even_without_tasks(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "active-outcomes"
    initialize(repository)
    make_single_scope(repository)
    write(
        repository / "docs/roadmap/README.md",
        roadmap(task=False, detailed_sot=None, outcomes="../specs/README.md"),
    )
    commit_all(repository)

    _, payload = inspect(repository)

    assert "active_epic_canonical_outcomes_present" in finding_codes(payload)


def test_completed_contract_rejects_retained_dossier_and_missing_outcome(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "completed-invalid"
    initialize(repository)
    make_single_scope(repository)
    write(repository / "docs/roadmap/README.md", roadmap(status="Completed"))
    commit_all(repository)

    _, payload = inspect(repository)

    assert finding_codes(payload) >= {
        "completed_epic_dossier_retained",
        "completed_epic_canonical_outcomes_missing",
    }


def test_completed_contract_accepts_existing_repository_outcome(tmp_path: Path) -> None:
    repository = tmp_path / "completed-valid"
    initialize(repository)
    make_single_scope(repository)
    write(
        repository / "docs/roadmap/README.md",
        roadmap(
            status="Completed",
            detailed_sot=None,
            outcomes="../specs/README.md",
        ),
    )
    (repository / "docs/todo/TODO-EPIC-001.md").unlink()
    commit_all(repository)

    _, payload = inspect(repository)

    assert payload["structural_status"] == "conforming"


def test_completed_contract_rejects_todo_outcome(tmp_path: Path) -> None:
    repository = tmp_path / "completed-todo-outcome"
    initialize(repository)
    make_single_scope(repository)
    write(
        repository / "docs/roadmap/README.md",
        roadmap(
            status="Completed",
            detailed_sot=None,
            outcomes="../todo/TODO-EPIC-001.md",
        ),
    )
    commit_all(repository)

    _, payload = inspect(repository)

    assert "completed_epic_canonical_outcomes_missing" in finding_codes(payload)


def test_historical_completed_epic_is_grandfathered(tmp_path: Path) -> None:
    repository = tmp_path / "historical"
    initialize(repository)
    make_single_scope(repository)
    write(
        repository / "docs/roadmap/README.md",
        roadmap(status="Completed", detailed_sot=None, outcomes=None),
    )
    (repository / "docs/todo/TODO-EPIC-001.md").unlink()
    commit_all(repository)

    _, payload = inspect(repository)

    assert payload["structural_status"] == "conforming"
    assert not any(
        code.startswith("completed_epic_") for code in finding_codes(payload)
    )


def test_legacy_completion_status_is_unverifiable_not_active(tmp_path: Path) -> None:
    repository = tmp_path / "legacy-completed"
    initialize(repository)
    make_single_scope(repository)
    write(
        repository / "docs/roadmap/README.md",
        roadmap(
            status="Done",
            detailed_sot=None,
            outcomes="../specs/README.md",
        ),
    )
    (repository / "docs/todo/TODO-EPIC-001.md").unlink()
    commit_all(repository)

    _, payload = inspect(repository)

    assert payload["structural_status"] == "unverifiable"
    assert "epic_lifecycle_unverifiable" in finding_codes(payload)
    assert not any(code.startswith("active_epic_") for code in finding_codes(payload))


def test_crlf_and_relaxed_markdown_produce_the_same_structure(tmp_path: Path) -> None:
    repository = tmp_path / "crlf"
    initialize(repository)
    make_single_scope(repository)
    content = roadmap(newline="\r\n").replace(
        "**Detailed SOT:** [Dossier]", "- Detailed SOT:\r\n[Dossier]"
    )
    (repository / "docs/roadmap/README.md").write_bytes(content.encode("utf-8"))
    commit_all(repository)

    _, payload = inspect(repository)

    assert payload["structural_status"] == "conforming"
    assert payload["roadmaps"][0]["epics"][0]["detailed_sot"] == [
        "../todo/TODO-EPIC-001.md"
    ]


def test_duplicate_current_roadmap_identifier_is_nonconforming(tmp_path: Path) -> None:
    repository = tmp_path / "duplicate"
    initialize(repository)
    make_single_scope(repository)
    path = repository / "docs/roadmap/README.md"
    path.write_text(
        path.read_text(encoding="utf-8")
        + "\n## EPIC-002: Second\n\n**Status:** `Planned`\n\n"
        + "| Task | Title | Status |\n| --- | --- | --- |\n"
        + "| TASK-001 | Duplicate | Planned |\n",
        encoding="utf-8",
    )
    commit_all(repository)

    _, payload = inspect(repository)

    assert payload["structural_status"] == "nonconforming"
    assert "duplicate_roadmap_identifier" in finding_codes(payload)


def test_dependency_table_does_not_define_tasks(tmp_path: Path) -> None:
    repository = tmp_path / "dependency-table"
    initialize(repository)
    make_single_scope(repository)
    path = repository / "docs/roadmap/README.md"
    path.write_text(
        path.read_text(encoding="utf-8")
        + "\n| Dependency | Reason |\n| --- | --- |\n"
        + "| EPIC-002 | Required first |\n"
        + "\n## EPIC-002: Second\n\n**Status:** `Planned`\n",
        encoding="utf-8",
    )
    commit_all(repository)

    _, payload = inspect(repository)

    assert "duplicate_roadmap_identifier" not in finding_codes(payload)


def test_excluded_linked_document_is_unverifiable_not_missing(tmp_path: Path) -> None:
    repository = tmp_path / "excluded"
    initialize(repository)
    make_single_scope(repository)
    dossier = repository / "docs/todo/TODO-KEY-ROTATION.md"
    write(dossier, "# Dossier\n")
    write(
        repository / "docs/roadmap/README.md",
        roadmap(detailed_sot="../todo/TODO-KEY-ROTATION.md"),
    )
    (repository / "docs/todo/TODO-EPIC-001.md").unlink()
    commit_all(repository)

    _, payload = inspect(repository)

    assert payload["structural_status"] == "unverifiable"
    assert "active_epic_dossier_unverifiable" in finding_codes(payload)
    assert payload["excluded_files"]["sensitive"] == 1


def test_ignored_documents_are_counted_without_reading_contents(tmp_path: Path) -> None:
    repository = tmp_path / "ignored"
    initialize(repository)
    make_single_scope(repository)
    write(repository / ".gitignore", "docs/private/\n")
    commit_all(repository)
    write(repository / "docs/private/SECRET.md", "credential-marker\n")

    _, payload = inspect(repository)

    assert payload["excluded_files"]["ignored"] == 1
    assert "credential-marker" not in json.dumps(payload)


def test_untracked_canonical_documents_are_inspected(tmp_path: Path) -> None:
    repository = tmp_path / "untracked"
    initialize(repository)
    write(repository / "README.md", "# Product\n")
    commit_all(repository)
    make_single_scope(repository)

    _, payload = inspect(repository)

    assert payload["structural_status"] == "conforming"
    assert payload["roadmaps"][0]["epics"][0]["id"] == "EPIC-001"


def test_repository_must_be_exact_non_symlink_git_root(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    initialize(repository)
    make_single_scope(repository)
    commit_all(repository)
    nested = repository / "nested"
    nested.mkdir()

    result, payload = inspect(nested)

    assert result.returncode == 2
    assert payload["schema_version"] == "aquarium-docs-inspection-error/v2"
    assert payload["error"]["code"] == "repository_not_root"
