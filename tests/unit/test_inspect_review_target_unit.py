from __future__ import annotations

import argparse
import importlib.util
import subprocess
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).parents[2]
    / "plugins/aquarium/skills/independent-review/scripts/inspect_review_target.py"
)
SPEC = importlib.util.spec_from_file_location("inspect_review_target", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
inspect_review_target = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inspect_review_target)


def git(repository: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def repository(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    root.mkdir()
    git(root, "init", "-q")
    git(root, "config", "user.name", "Aquarium Test")
    git(root, "config", "user.email", "aquarium@example.invalid")
    write(root / ".gitignore", ".cache/\n")
    write(root / "tracked.txt", "base\n")
    git(root, "add", ".gitignore", "tracked.txt")
    git(root, "commit", "-qm", "initial")
    return root


def arguments(**values: object) -> argparse.Namespace:
    defaults = {"staged": False, "head": False, "commit": None, "range": None}
    defaults.update(values)
    return argparse.Namespace(**defaults)


def test_staged_target_records_digest_and_dirty_remainder(tmp_path: Path) -> None:
    root = repository(tmp_path)
    write(root / "staged.txt", "staged\n")
    git(root, "add", "staged.txt")
    write(root / "tracked.txt", "dirty\n")
    write(root / "untracked.txt", "private\n")
    write(root / ".cache" / "ignored.txt", "ignored\n")

    result = inspect_review_target.inspect(root, arguments(staged=True))

    assert result["schema_version"] == "aquarium-independent-review-target/v1"
    assert result["semantic_scope"] == "not_evaluated"
    assert result["target"]["kind"] == "staged"
    assert len(result["target"]["diff_sha256"]) == 64
    assert len(result["target"]["target_digest"]) == 64
    assert result["state"]["staged"] == ["staged.txt"]
    assert result["state"]["unstaged"] == ["tracked.txt"]
    assert result["state"]["untracked"] == ["untracked.txt"]
    assert result["state"]["ignored"] == [".cache/"]
    assert result["state"]["conflicts"] == []


def test_empty_staged_target_is_rejected(tmp_path: Path) -> None:
    root = repository(tmp_path)

    with pytest.raises(inspect_review_target.InspectionError) as error:
        inspect_review_target.inspect(root, arguments(staged=True))

    assert error.value.code == "staged_target_empty"


def test_head_and_commit_resolve_to_exact_commits(tmp_path: Path) -> None:
    root = repository(tmp_path)
    first = git(root, "rev-parse", "HEAD")
    write(root / "tracked.txt", "second\n")
    git(root, "add", "tracked.txt")
    git(root, "commit", "-qm", "second")
    second = git(root, "rev-parse", "HEAD")

    head = inspect_review_target.inspect(root, arguments(head=True))["target"]
    commit = inspect_review_target.inspect(root, arguments(commit=first[:10]))["target"]

    assert head["kind"] == "head"
    assert head["commit"] == second
    assert commit["kind"] == "commit"
    assert commit["revision"] == first[:10]
    assert commit["commit"] == first
    assert len(commit["diff_sha256"]) == 64


def test_two_dot_range_preserves_endpoints_and_commit_order(tmp_path: Path) -> None:
    root = repository(tmp_path)
    base = git(root, "rev-parse", "HEAD")
    write(root / "one.txt", "one\n")
    git(root, "add", "one.txt")
    git(root, "commit", "-qm", "one")
    one = git(root, "rev-parse", "HEAD")
    write(root / "two.txt", "two\n")
    git(root, "add", "two.txt")
    git(root, "commit", "-qm", "two")
    two = git(root, "rev-parse", "HEAD")

    target = inspect_review_target.inspect(root, arguments(range=f"{base[:9]}..HEAD"))[
        "target"
    ]

    assert target["operator"] == ".."
    assert target["base_commit"] == base
    assert target["head_commit"] == two
    assert target["merge_base"] is None
    assert target["commits"] == [one, two]


def test_three_dot_range_uses_merge_base_for_diff_and_commits(tmp_path: Path) -> None:
    root = repository(tmp_path)
    base = git(root, "rev-parse", "HEAD")
    primary_branch = git(root, "branch", "--show-current")
    git(root, "checkout", "-qb", "feature")
    write(root / "feature.txt", "feature\n")
    git(root, "add", "feature.txt")
    git(root, "commit", "-qm", "feature")
    feature = git(root, "rev-parse", "HEAD")
    git(root, "checkout", "-q", primary_branch)
    write(root / "main.txt", "main\n")
    git(root, "add", "main.txt")
    git(root, "commit", "-qm", "main")

    target = inspect_review_target.inspect(
        root, arguments(range=f"{primary_branch}...feature")
    )["target"]

    assert target["operator"] == "..."
    assert target["base_commit"] == git(root, "rev-parse", primary_branch)
    assert target["head_commit"] == feature
    assert target["merge_base"] == base
    assert target["commits"] == [feature]


def test_invalid_range_and_conflict_status_are_bounded(tmp_path: Path) -> None:
    root = repository(tmp_path)

    with pytest.raises(inspect_review_target.InspectionError) as error:
        inspect_review_target.inspect(root, arguments(range="HEAD"))

    assert error.value.code == "range_invalid"
    state = inspect_review_target.parse_status(b"UU conflicted.txt\0")
    assert state["conflicts"] == ["conflicted.txt"]
    assert state["staged"] == []
    assert state["unstaged"] == []


def test_rename_and_copy_status_return_exact_paths_and_structured_changes() -> None:
    state = inspect_review_target.parse_status(
        b"R  staged-new.txt\0staged-old.txt\0"
        b" R dirty-new.txt\0dirty-old.txt\0"
        b"RM modified-new.txt\0modified-old.txt\0"
        b"C  copied.txt\0copy-source.txt\0"
    )

    assert state["staged"] == ["copied.txt", "modified-new.txt", "staged-new.txt"]
    assert state["unstaged"] == [
        "dirty-new.txt",
        "dirty-old.txt",
        "modified-new.txt",
    ]
    assert state["path_changes"] == [
        {
            "status": "C ",
            "kind": "copy",
            "source": "copy-source.txt",
            "destination": "copied.txt",
        },
        {
            "status": " R",
            "kind": "rename",
            "source": "dirty-old.txt",
            "destination": "dirty-new.txt",
        },
        {
            "status": "RM",
            "kind": "rename",
            "source": "modified-old.txt",
            "destination": "modified-new.txt",
        },
        {
            "status": "R ",
            "kind": "rename",
            "source": "staged-old.txt",
            "destination": "staged-new.txt",
        },
    ]


def test_unstaged_rename_paths_can_be_staged_exactly(tmp_path: Path) -> None:
    root = repository(tmp_path)
    (root / "tracked.txt").rename(root / "renamed.txt")

    state = inspect_review_target.repository_state(root)

    assert state["unstaged"] == ["tracked.txt"]
    assert state["untracked"] == ["renamed.txt"]
    dirty_paths = sorted(state["unstaged"] + state["untracked"])
    git(root, "add", "--", *dirty_paths)
    state = inspect_review_target.repository_state(root)
    assert state["unstaged"] == []
    assert state["untracked"] == []

    write(root / "renamed.txt", "modified after rename\n")
    state = inspect_review_target.repository_state(root)

    assert state["unstaged"] == ["renamed.txt"]
    git(root, "add", "--", *state["unstaged"])
    assert inspect_review_target.repository_state(root)["unstaged"] == []


@pytest.mark.parametrize("target_kind", ["staged", "commit", "range"])
def test_diff_inspection_never_runs_textconv(tmp_path: Path, target_kind: str) -> None:
    root = repository(tmp_path)
    sentinel = tmp_path / "textconv-ran"
    converter = tmp_path / "textconv.py"
    write(
        converter,
        "#!/usr/bin/env python3\n"
        "import pathlib, sys\n"
        "pathlib.Path(sys.argv[1]).write_text('ran', encoding='utf-8')\n"
        "sys.stdout.buffer.write(pathlib.Path(sys.argv[2]).read_bytes())\n",
    )
    converter.chmod(converter.stat().st_mode | 0o111)
    write(root / ".gitattributes", "*.bin diff=sentinel\n")
    write(root / "payload.bin", "base\n")
    git(root, "add", ".gitattributes", "payload.bin")
    git(root, "commit", "-qm", "binary baseline")
    base = git(root, "rev-parse", "HEAD")
    git(
        root,
        "config",
        "diff.sentinel.textconv",
        f"{converter} {sentinel}",
    )
    write(root / "payload.bin", "changed\n")
    git(root, "add", "payload.bin")

    if target_kind == "staged":
        target_arguments = arguments(staged=True)
    else:
        git(root, "commit", "-qm", "binary change")
        target_arguments = (
            arguments(commit="HEAD")
            if target_kind == "commit"
            else arguments(range=f"{base}..HEAD")
        )

    inspect_review_target.inspect(root, target_arguments)

    assert not sentinel.exists()
