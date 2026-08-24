from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).parents[2]
    / "plugins/aquarium/skills/release-handler/scripts/inspect_release_notes.py"
)
SPEC = importlib.util.spec_from_file_location("inspect_release_notes", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
inspect_release_notes = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inspect_release_notes)


def make_repository(
    tmp_path: Path, changelog: str | None, *, track_changelog: bool = True
) -> Path:
    repository = tmp_path / "repository"
    repository.mkdir()
    subprocess.run(
        ["git", "init", "--quiet", str(repository)],
        check=True,
        capture_output=True,
    )
    authority = "- Aquarium release notes: CHANGELOG.md\n" if changelog else ""
    (repository / "AGENTS.md").write_text(
        f"# AGENTS.md\n\n## Project Configuration\n\n{authority}",
        encoding="utf-8",
    )
    if changelog is not None:
        (repository / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(repository), "add", "AGENTS.md"],
        check=True,
        capture_output=True,
    )
    if changelog is not None and track_changelog:
        subprocess.run(
            ["git", "-C", str(repository), "add", "CHANGELOG.md"],
            check=True,
            capture_output=True,
        )
    return repository


VALID_CHANGELOG = """\
# Changelog

## v0.1.11 - Unreleased

### Added

- Add release tracking.

## v0.1.10 - 2026-08-23

### Added

- Add the previous release.
"""


def test_valid_release_notes_report_open_and_previous_release(tmp_path: Path) -> None:
    repository = make_repository(tmp_path, VALID_CHANGELOG)

    result = inspect_release_notes.inspect(repository, "v0.1.11", "v0.1.10")

    assert result["enrollment"] == "enrolled"
    assert result["semantic_scope"] == "not_evaluated"
    assert result["notes_path"] == "CHANGELOG.md"
    assert result["tracking"] == "tracked"
    assert result["open_release"] == {
        "version": "v0.1.11",
        "line": 3,
        "entry_count": 1,
    }
    assert result["findings"] == []


def test_repository_without_declaration_is_not_enrolled(tmp_path: Path) -> None:
    repository = make_repository(tmp_path, None)

    result = inspect_release_notes.inspect(repository)

    assert result["enrollment"] == "not_enrolled"
    assert result["notes_path"] is None
    assert result["findings"] == []


def test_declaration_outside_project_configuration_does_not_enroll(
    tmp_path: Path,
) -> None:
    repository = make_repository(tmp_path, VALID_CHANGELOG)
    (repository / "AGENTS.md").write_text(
        "# AGENTS.md\n\n## Notes\n\n- Aquarium release notes: CHANGELOG.md\n",
        encoding="utf-8",
    )

    result = inspect_release_notes.inspect(repository)

    assert result["enrollment"] == "not_enrolled"


def test_external_example_does_not_make_internal_declaration_ambiguous(
    tmp_path: Path,
) -> None:
    repository = make_repository(tmp_path, VALID_CHANGELOG)
    (repository / "AGENTS.md").write_text(
        "# AGENTS.md\n\n"
        "## Example\n\n- Aquarium release notes: EXAMPLE.md\n\n"
        "## Project Configuration\n\n"
        "- Aquarium release notes: CHANGELOG.md\n",
        encoding="utf-8",
    )

    result = inspect_release_notes.inspect(repository)

    assert result["enrollment"] == "enrolled"
    assert result["notes_path"] == "CHANGELOG.md"


def test_duplicate_internal_declarations_are_ambiguous(tmp_path: Path) -> None:
    repository = make_repository(tmp_path, VALID_CHANGELOG)
    (repository / "AGENTS.md").write_text(
        "# AGENTS.md\n\n## Project Configuration\n\n"
        "- Aquarium release notes: CHANGELOG.md\n"
        "- Aquarium release notes: OTHER.md\n",
        encoding="utf-8",
    )

    with pytest.raises(inspect_release_notes.InspectionError) as error:
        inspect_release_notes.inspect(repository)

    assert error.value.code == "authority_ambiguous"


def test_duplicate_open_sections_are_structural_findings(tmp_path: Path) -> None:
    repository = make_repository(
        tmp_path,
        VALID_CHANGELOG.replace("## v0.1.10 - 2026-08-23", "## v0.1.12 - Unreleased"),
    )

    result = inspect_release_notes.inspect(repository)

    assert result["open_release"] is None
    assert [finding["code"] for finding in result["findings"]] == [
        "open_release_count_invalid"
    ]


def test_expected_and_previous_versions_are_checked(tmp_path: Path) -> None:
    repository = make_repository(tmp_path, VALID_CHANGELOG)

    result = inspect_release_notes.inspect(repository, "v0.2.0", "v0.1.9")

    assert [finding["code"] for finding in result["findings"]] == [
        "expected_version_mismatch",
        "previous_release_missing",
    ]


@pytest.mark.parametrize(
    ("target", "expected_codes"),
    [
        ("v0.1.9", ["expected_version_not_newer"]),
        (
            "v0.1.10",
            ["release_version_duplicate", "expected_version_not_newer"],
        ),
    ],
)
def test_expected_version_must_be_newer_than_previous_release(
    tmp_path: Path, target: str, expected_codes: list[str]
) -> None:
    changelog = VALID_CHANGELOG.replace(
        "v0.1.11 - Unreleased", f"{target} - Unreleased"
    )
    repository = make_repository(tmp_path, changelog)

    result = inspect_release_notes.inspect(repository, target, "v0.1.10")

    assert [finding["code"] for finding in result["findings"]] == expected_codes


def test_completed_release_date_must_be_a_calendar_date(tmp_path: Path) -> None:
    repository = make_repository(
        tmp_path,
        VALID_CHANGELOG.replace("2026-08-23", "2026-02-30"),
    )

    result = inspect_release_notes.inspect(repository)

    assert [finding["code"] for finding in result["findings"]] == [
        "release_date_invalid"
    ]


@pytest.mark.parametrize(
    "heading",
    [
        "## v0.1.10 - 2026/08/23",
        "## v0.1.10 - 2026-08-23 trailing",
        "## v0.1 - 2026-08-23",
        "## v0.1.11 - 2026/08/23",
    ],
)
def test_malformed_release_like_heading_is_a_structural_finding(
    tmp_path: Path, heading: str
) -> None:
    repository = make_repository(
        tmp_path,
        VALID_CHANGELOG.replace("## v0.1.10 - 2026-08-23", heading),
    )

    result = inspect_release_notes.inspect(repository)

    assert [finding["code"] for finding in result["findings"]] == [
        "release_heading_invalid"
    ]


def test_untracked_release_notes_are_a_structural_finding(tmp_path: Path) -> None:
    repository = make_repository(tmp_path, VALID_CHANGELOG, track_changelog=False)

    result = inspect_release_notes.inspect(repository)

    assert result["tracking"] == "untracked"
    assert [finding["code"] for finding in result["findings"]] == [
        "authority_untracked"
    ]


def test_ignored_release_notes_are_a_structural_finding(tmp_path: Path) -> None:
    repository = make_repository(tmp_path, VALID_CHANGELOG, track_changelog=False)
    (repository / ".gitignore").write_text("CHANGELOG.md\n", encoding="utf-8")

    result = inspect_release_notes.inspect(repository)

    assert result["tracking"] == "ignored"
    assert [finding["code"] for finding in result["findings"]] == ["authority_ignored"]


def test_release_notes_path_rejects_parent_traversal(tmp_path: Path) -> None:
    repository = make_repository(tmp_path, None)
    (repository / "AGENTS.md").write_text(
        "# AGENTS.md\n\n## Project Configuration\n\n"
        "- Aquarium release notes: ../CHANGELOG.md\n",
        encoding="utf-8",
    )

    with pytest.raises(inspect_release_notes.InspectionError) as error:
        inspect_release_notes.inspect(repository)

    assert error.value.code == "authority_path_invalid"


def test_release_notes_path_rejects_symlinks(tmp_path: Path) -> None:
    repository = make_repository(tmp_path, None)
    target = repository / "real-changelog.md"
    target.write_text(VALID_CHANGELOG, encoding="utf-8")
    (repository / "CHANGELOG.md").symlink_to(target.name)
    (repository / "AGENTS.md").write_text(
        "# AGENTS.md\n\n## Project Configuration\n\n"
        "- Aquarium release notes: CHANGELOG.md\n",
        encoding="utf-8",
    )

    with pytest.raises(inspect_release_notes.InspectionError) as error:
        inspect_release_notes.inspect(repository)

    assert error.value.code == "authority_symlinked"


def test_first_release_accepts_only_an_open_release(tmp_path: Path) -> None:
    first_release = VALID_CHANGELOG.split("## v0.1.10", 1)[0]
    repository = make_repository(tmp_path, first_release)

    result = inspect_release_notes.inspect(
        repository, expected_version="v0.1.11", first_release=True
    )

    assert result["baseline"] == "first_release"
    assert result["released_versions"] == []
    assert result["findings"] == []


def test_first_release_rejects_a_completed_release(tmp_path: Path) -> None:
    repository = make_repository(tmp_path, VALID_CHANGELOG)

    result = inspect_release_notes.inspect(repository, first_release=True)

    assert "first_release_has_completed_release" in {
        finding["code"] for finding in result["findings"]
    }


@pytest.mark.parametrize(
    ("replacement", "expected_codes"),
    [
        (
            "### Security\n\n- Describe security behavior.",
            ["release_category_invalid", "release_entry_outside_category"],
        ),
        (
            "### Added\n\n### Added\n\n- Add release tracking.",
            ["release_category_duplicate"],
        ),
        ("### Added", ["release_category_empty"]),
        ("- Add release tracking.", ["release_entry_outside_category"]),
    ],
)
def test_release_categories_are_structurally_validated(
    tmp_path: Path, replacement: str, expected_codes: list[str]
) -> None:
    changelog = VALID_CHANGELOG.replace(
        "### Added\n\n- Add release tracking.", replacement, 1
    )
    repository = make_repository(tmp_path, changelog)

    result = inspect_release_notes.inspect(repository)

    codes = [finding["code"] for finding in result["findings"]]
    assert codes == expected_codes
