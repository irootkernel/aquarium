from __future__ import annotations

import importlib.util
import os
from pathlib import Path

SCRIPT = (
    Path(__file__).parents[2]
    / "plugins/aquarium/skills/docs-setup/scripts/inspect_docs.py"
)
SPEC = importlib.util.spec_from_file_location("inspect_docs", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
inspect_docs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inspect_docs)


def test_definition_ids_distinguishes_epic_summary_from_definitions() -> None:
    text = """\
| Epic | Title |
| --- | --- |
| EPIC-001 | First |

## EPIC-001: First

| Task | Title | Status |
| --- | --- | --- |
| TASK-001 | Foundation | Planned |
"""

    assert inspect_docs.definition_ids(text) == [
        ("EPIC-001", 5, "heading"),
        ("TASK-001", 9, "table"),
    ]


def test_migration_requires_planned_epic_and_all_planned_tasks() -> None:
    eligible = """\
## EPIC-002: Future

**Status:** `Planned`

| Task | Title | Status |
| --- | --- | --- |
| TASK-003 | One | Planned |
| TASK-004 | Two | Planned |
"""
    blocked = eligible.replace("EPIC-002", "EPIC-003").replace(
        "| TASK-004 | Two | Planned |", "| TASK-004 | Two | In Progress |"
    )
    path = Path("docs/roadmap/README.md")

    result = inspect_docs.migration_analysis([path], {path: eligible + blocked})

    assert [item["planned_only_eligible"] for item in result] == [True, False]
    assert result[0]["tasks"] == [
        {"id": "TASK-003", "status": "Planned"},
        {"id": "TASK-004", "status": "Planned"},
    ]


def test_sensitive_paths_are_excluded_without_inspecting_values() -> None:
    assert inspect_docs.sensitive_path(Path(".env.example"))
    assert inspect_docs.sensitive_path(Path("config/auth-token.txt"))
    assert inspect_docs.sensitive_path(Path("docs/credentials/README.md"))
    assert not inspect_docs.sensitive_path(Path("docs/specs/product.md"))


def test_identifier_patterns_preserve_legacy_shapes() -> None:
    values = {
        match.group(0)
        for match in inspect_docs.ID_TOKEN.finditer(
            "EPIC-001 TASK-003-A CEPIC-27 CTASK-204 V2GRD-001 sched-022"
        )
    }

    assert values == {
        "EPIC-001",
        "TASK-003-A",
        "CEPIC-27",
        "CTASK-204",
        "V2GRD-001",
        "sched-022",
    }


def test_semantic_epic_and_compact_completed_task_are_preserved() -> None:
    text = """\
## WIKRET: Preserve identity

**Status:** `Planned`

| Task ID | Status |
| --- | --- |
| CTASK204 | Completed |
"""
    path = Path("docs/ROADMAP.md")

    assert inspect_docs.definition_ids(text) == [
        ("WIKRET", 1, "heading"),
        ("CTASK204", 7, "table"),
    ]
    result = inspect_docs.migration_analysis([path], {path: text})
    assert result[0]["tasks"] == [{"id": "CTASK204", "status": "Completed"}]
    assert result[0]["planned_only_eligible"] is False


def test_unrecognized_task_row_blocks_planned_only_prefilter() -> None:
    text = """\
## EPIC-001: Preserve unknown child

**Status:** `Planned`

| Task ID | Status |
| --- | --- |
| ??? | Planned |
"""
    path = Path("docs/roadmap/README.md")

    result = inspect_docs.migration_analysis([path], {path: text})
    assert result[0]["planned_only_eligible"] is False


def test_definition_ids_uses_epic_containment_and_ignores_numeric_prose_headings() -> (
    None
):
    text = """\
| Epic | Title |
| --- | --- |
| V2GRD | Legacy |

## V2GRD: Legacy

| Task | Title | Status |
| --- | --- | --- |
| V2GRD-001 | Foundation | Planned |

## Q3-2026: Delivery window

| Task | Title | Status |
| --- | --- | --- |
| TASK-999 | Not adopted | Planned |
"""

    assert inspect_docs.definition_ids(text) == [
        ("V2GRD", 5, "heading"),
        ("V2GRD-001", 9, "table"),
    ]


def test_migration_block_stops_at_any_level_two_heading() -> None:
    text = """\
## EPIC-001: Missing status

## Notes

**Status:** `Planned`

| Task | Title | Status |
| --- | --- | --- |
| TASK-001 | Not contained | Planned |
"""
    path = Path("docs/roadmap/README.md")

    result = inspect_docs.migration_analysis([path], {path: text})

    assert result == [
        {
            "epic": "EPIC-001",
            "path": "docs/roadmap/README.md",
            "status": "unknown",
            "tasks": [],
            "planned_only_eligible": False,
            "reason": "status_or_task_ownership_not_eligible",
        }
    ]


def test_planned_epic_without_tasks_is_epic_only_migration_eligible() -> None:
    text = """\
## EPIC-002: Empty planned epic

**Status:** `Planned`
"""
    path = Path("docs/roadmap/README.md")

    result = inspect_docs.migration_analysis([path], {path: text})

    assert result[0]["planned_only_eligible"] is True
    assert result[0]["reason"] == "planned_epic_without_child_tasks"


def test_preserved_paths_accepts_only_exact_repository_relative_paths() -> None:
    accepted, rejected = inspect_docs.preserved_paths(
        "`docs/architecture-decisions/0001.md`<br>`../outside.md`<br>`/tmp/file`"
        "<br>`docs/*.md`<br>`docs\\legacy.md`<br>docs/unquoted.md"
    )

    assert accepted == ["docs/architecture-decisions/0001.md"]
    assert rejected == [
        "../outside.md",
        "/tmp/file",
        "docs/*.md",
        "docs/unquoted.md",
        "docs\\legacy.md",
    ]


def test_role_candidates_deduplicate_aliases_for_one_filesystem_object(
    tmp_path: Path, monkeypatch: object
) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    roadmap = docs / "ROADMAP.md"
    roadmap.write_text("# Roadmap\n", encoding="utf-8")
    os.link(roadmap, docs / "roadmap-alias.md")
    monkeypatch.setitem(
        inspect_docs.ROLE_ALIASES,
        "roadmap",
        ("ROADMAP.md", "roadmap-alias.md"),
    )

    assert inspect_docs.path_role_candidates(tmp_path, Path("docs"), "roadmap") == [
        "docs/ROADMAP.md"
    ]


def test_epic_status_emits_only_allowlisted_values() -> None:
    assert inspect_docs.epic_status("**Status:** `In Review`\n") == "In Review"
    assert inspect_docs.epic_status("**상태:** `Planned`\n") == "Planned"
    assert inspect_docs.epic_status("**Status:** owner@example.com\n") == "unknown"
