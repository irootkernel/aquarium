from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = (
    Path(__file__).parents[2]
    / "plugins/aquarium/skills/docs-setup/scripts/inspect_docs.py"
)
SPEC = importlib.util.spec_from_file_location("inspect_docs", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
inspect_docs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inspect_docs)


def test_header_states_the_bounded_inspector_purpose() -> None:
    header = "\n".join(SCRIPT.read_text(encoding="utf-8").splitlines()[:5])

    assert "conservative, read-only structural discovery" in header
    assert "Do not validate prose wording" in header


def test_field_parser_tolerates_markdown_and_line_endings() -> None:
    text = (
        "## EPIC-001: First\r\n"
        "\r\n"
        "- Detailed SOT:\r\n"
        "[Dossier](../todo/TODO-EPIC-001.md)\r\n"
    )
    _, lines = inspect_docs.epic_sections(text)[0]

    assert inspect_docs.field_links(lines, "Detailed SOT") == (
        1,
        ["../todo/TODO-EPIC-001.md"],
    )


def test_link_resolution_rejects_external_and_repository_escape() -> None:
    source = Path("docs/roadmap/README.md")

    assert inspect_docs.resolve_document_link(source, "/tmp/spec.md") is None
    assert (
        inspect_docs.resolve_document_link(source, "https://example.com/spec") is None
    )
    assert inspect_docs.resolve_document_link(source, "../../../outside.md") is None
    assert inspect_docs.resolve_document_link(
        source, "../specs/README.md#contract"
    ) == Path("docs/specs/README.md")


def test_epic_and_task_parser_extracts_only_explicit_roadmap_structure() -> None:
    text = """\
# Roadmap

## EPIC-001: First

**Status:** `In Progress`

| Task | Title | Status |
| --- | --- | --- |
| TASK-001 | Foundation | Completed |

## Notes

TASK-999 is prose, not a task definition.
"""
    identifier, lines = inspect_docs.epic_sections(text)[0]

    assert identifier == "EPIC-001"
    assert inspect_docs.status_value(lines) == "In Progress"
    assert inspect_docs.task_rows(lines) == [{"id": "TASK-001", "status": "Completed"}]


def test_sensitive_paths_are_excluded_without_reading_values() -> None:
    assert inspect_docs.sensitive_path(Path(".env.example"))
    assert inspect_docs.sensitive_path(Path("docs/ops/key-rotation.md"))
    assert inspect_docs.sensitive_path(Path("docs/todo/TODO-SECRETS.md"))
    assert not inspect_docs.sensitive_path(Path("docs/specs/product.md"))


def test_owner_containment_is_component_aware() -> None:
    owner = Path("docs/todo")

    assert inspect_docs.within_owner(Path("docs/todo/TODO-ONE.md"), owner)
    assert not inspect_docs.within_owner(Path("docs/todo-other/TODO-ONE.md"), owner)
