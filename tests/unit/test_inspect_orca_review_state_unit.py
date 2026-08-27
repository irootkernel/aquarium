from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).parents[2]
    / "plugins/aquarium/skills/orca-review/scripts/inspect_repository_state.py"
)
SPEC = importlib.util.spec_from_file_location("inspect_repository_state", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
inspect_repository_state = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inspect_repository_state)


def git(repository: Path, *arguments: str) -> None:
    subprocess.run(["git", *arguments], cwd=repository, check=True)


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    root.mkdir()
    git(root, "init", "-q")
    git(root, "config", "user.name", "Test User")
    git(root, "config", "user.email", "test@example.com")
    (root / "tracked.txt").write_text("initial\n", encoding="utf-8")
    git(root, "add", "tracked.txt")
    git(root, "commit", "-qm", "initial")
    return root


def test_compare_accepts_unchanged_repository(repository: Path) -> None:
    baseline = inspect_repository_state.snapshot(repository)

    result = inspect_repository_state.compare(repository, baseline)

    assert result["drift"] is False
    assert result["changed"] == []


def test_compare_detects_tracked_worktree_and_status_drift(repository: Path) -> None:
    baseline = inspect_repository_state.snapshot(repository)
    (repository / "tracked.txt").write_text("changed\n", encoding="utf-8")

    result = inspect_repository_state.compare(repository, baseline)

    assert result["drift"] is True
    assert "tracked_worktree_sha256" in result["changed"]
    assert "status_sha256" in result["changed"]


def test_compare_detects_index_and_ref_drift(repository: Path) -> None:
    baseline = inspect_repository_state.snapshot(repository)
    (repository / "staged.txt").write_text("staged\n", encoding="utf-8")
    git(repository, "add", "staged.txt")
    git(repository, "branch", "unexpected-ref")

    result = inspect_repository_state.compare(repository, baseline)

    assert result["drift"] is True
    assert "index_sha256" in result["changed"]
    assert "refs_sha256" in result["changed"]


def test_compare_detects_untracked_path_set_drift(repository: Path) -> None:
    baseline = inspect_repository_state.snapshot(repository)
    (repository / "untracked.txt").write_text("untracked\n", encoding="utf-8")

    result = inspect_repository_state.compare(repository, baseline)

    assert result["drift"] is True
    assert "status_sha256" in result["changed"]


def test_compare_detects_existing_untracked_content_drift(repository: Path) -> None:
    path = repository / "untracked.txt"
    path.write_text("before\n", encoding="utf-8")
    baseline = inspect_repository_state.snapshot(repository)
    path.write_text("after\n", encoding="utf-8")

    result = inspect_repository_state.compare(repository, baseline)

    assert result["drift"] is True
    assert "status_sha256" in result["changed"]


def test_compare_detects_assume_unchanged_index_flag(repository: Path) -> None:
    baseline = inspect_repository_state.snapshot(repository)
    git(repository, "update-index", "--assume-unchanged", "tracked.txt")

    result = inspect_repository_state.compare(repository, baseline)

    assert result["drift"] is True
    assert "index_sha256" in result["changed"]


def test_compare_detects_content_hidden_by_assume_unchanged(repository: Path) -> None:
    git(repository, "update-index", "--assume-unchanged", "tracked.txt")
    baseline = inspect_repository_state.snapshot(repository)
    (repository / "tracked.txt").write_text("changed\n", encoding="utf-8")

    result = inspect_repository_state.compare(repository, baseline)

    assert result["drift"] is True
    assert "tracked_worktree_sha256" in result["changed"]


def test_compare_detects_content_hidden_by_skip_worktree(repository: Path) -> None:
    git(repository, "update-index", "--skip-worktree", "tracked.txt")
    baseline = inspect_repository_state.snapshot(repository)
    (repository / "tracked.txt").write_text("changed\n", encoding="utf-8")

    result = inspect_repository_state.compare(repository, baseline)

    assert result["drift"] is True
    assert "tracked_worktree_sha256" in result["changed"]


def test_compare_detects_submodule_content_despite_ignore_all(tmp_path: Path) -> None:
    child = tmp_path / "child"
    child.mkdir()
    git(child, "init", "-q")
    git(child, "config", "user.name", "Test User")
    git(child, "config", "user.email", "test@example.com")
    (child / "tracked.txt").write_text("initial\n", encoding="utf-8")
    git(child, "add", "tracked.txt")
    git(child, "commit", "-qm", "initial")

    parent = tmp_path / "parent"
    parent.mkdir()
    git(parent, "init", "-q")
    git(parent, "config", "user.name", "Test User")
    git(parent, "config", "user.email", "test@example.com")
    subprocess.run(
        [
            "git",
            "-c",
            "protocol.file.allow=always",
            "submodule",
            "add",
            "-q",
            str(child),
            "modules/child",
        ],
        cwd=parent,
        check=True,
    )
    git(parent, "commit", "-qam", "add submodule")
    git(parent, "config", "submodule.modules/child.ignore", "all")
    baseline = inspect_repository_state.snapshot(parent)
    (parent / "modules/child/tracked.txt").write_text("changed\n", encoding="utf-8")

    result = inspect_repository_state.compare(parent, baseline)

    assert result["drift"] is True
    assert "tracked_worktree_sha256" in result["changed"]


def test_baseline_requires_matching_repository_and_fingerprint(
    repository: Path, tmp_path: Path
) -> None:
    baseline = inspect_repository_state.snapshot(repository)
    baseline["repository"] = str(tmp_path)

    with pytest.raises(inspect_repository_state.InspectionError) as error:
        inspect_repository_state.parse_baseline(
            json.dumps(baseline).encode(), repository
        )

    assert error.value.code == "baseline_invalid"
