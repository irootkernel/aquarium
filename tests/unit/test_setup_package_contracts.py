"""Executable package containment and complete upstream inventory regressions."""

import copy
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
LINK_CHECK = ROOT / "tests/support/local_references.rb"
INVENTORY = (
    ROOT / "plugins/aquarium/skills/dev-setup-global/scripts/inspect_skill_inventory.py"
)
TREE_SHA = "a" * 40


def check_links(root):
    if shutil.which("ruby") is None:
        pytest.fail("Ruby is unavailable; install Ruby 3.3+ (macOS: brew install ruby)")
    return subprocess.run(
        ["ruby", str(LINK_CHECK), str(root)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_published_plugin_resolves_without_repository(tmp_path):
    target = tmp_path / "installed-plugin"
    shutil.copytree(ROOT / "plugins/aquarium", target, symlinks=True)
    result = check_links(target)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("target", ["../outside.md", "missing.md", "linked.md"])
def test_package_rejects_escape_missing_and_symlink(tmp_path, target):
    plugin = tmp_path / "plugin"
    plugin.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("outside\n")
    (plugin / "linked.md").symlink_to(outside)
    (plugin / "SKILL.md").write_text(f"[resource]({target})\n")
    assert check_links(plugin).returncode != 0


def metadata():
    return {
        "sha": TREE_SHA,
        "truncated": False,
        "tree": [
            {
                "path": "skills/use-example",
                "type": "tree",
                "mode": "040000",
                "sha": "b" * 40,
            },
            {
                "path": "skills/use-example/SKILL.md",
                "type": "blob",
                "mode": "100644",
                "sha": "c" * 40,
            },
            {
                "path": "skills/use-example/references",
                "type": "tree",
                "mode": "040000",
                "sha": "d" * 40,
            },
            {
                "path": "skills/use-example/references/new.md",
                "type": "blob",
                "mode": "100644",
                "sha": "e" * 40,
            },
        ],
    }


def run_inventory(
    document, tree_sha=TREE_SHA, skill_path="skills/use-example", raw=None
):
    import sys

    return subprocess.run(
        [
            sys.executable,
            str(INVENTORY),
            "--tree-sha",
            tree_sha,
            "--skill-path",
            skill_path,
        ],
        check=False,
        input=json.dumps(document) if raw is None else raw,
        capture_output=True,
        text=True,
    )


def test_inventory_includes_new_producer_files():
    result = run_inventory(metadata())
    assert result.returncode == 0, result.stdout
    assert json.loads(result.stdout)["files"] == [
        {"path": "SKILL.md", "blob_sha": "c" * 40, "mode": "100644"},
        {"path": "references/new.md", "blob_sha": "e" * 40, "mode": "100644"},
    ]


@pytest.mark.parametrize(
    "case",
    [
        "truncated",
        "wrong-tree",
        "duplicate",
        "escape",
        "symlink",
        "submodule",
        "missing-skill",
        "missing-directory",
        "invalid-blob",
        "mode-list",
    ],
)
def test_inventory_refuses_incomplete_or_unsafe_source(case):
    document = copy.deepcopy(metadata())
    if case == "truncated":
        document["truncated"] = True
    elif case == "wrong-tree":
        document["sha"] = "f" * 40
    elif case == "duplicate":
        document["tree"].append(document["tree"][-1])
    elif case == "escape":
        document["tree"][-1]["path"] = "skills/use-example/../escape"
    elif case == "symlink":
        document["tree"][-1]["mode"] = "120000"
    elif case == "submodule":
        document["tree"][-1].update(type="commit", mode="160000")
    elif case == "missing-directory":
        document["tree"].pop(0)
    elif case == "invalid-blob":
        document["tree"][-1]["sha"] = "short"
    elif case == "mode-list":
        document["tree"][-1]["mode"] = ["100644"]
    else:
        document["tree"].pop(1)
    result = run_inventory(document)
    assert result.returncode == 2
    assert "error" in json.loads(result.stdout)
    assert not result.stderr


def test_link_parent_traversal_cannot_hide_symlink(tmp_path):
    plugin = tmp_path / "plugin"
    plugin.mkdir()
    outside = tmp_path / "outside"
    (outside / "directory").mkdir(parents=True)
    (plugin / "link").symlink_to(outside / "directory", target_is_directory=True)
    (plugin / "target.md").write_text("inside\n")
    (outside / "target.md").write_text("outside\n")
    (plugin / "SKILL.md").write_text("[target](link/../target.md)\n")
    result = check_links(plugin)
    assert result.returncode != 0
    assert "symlink" in result.stderr


def test_nested_links_can_reach_package_root(tmp_path):
    (tmp_path / "skills/example").mkdir(parents=True)
    (tmp_path / "target.md").write_text("resource\n")
    (tmp_path / "skills/example/SKILL.md").write_text(
        "[target](../../target.md)\n[root](../../)\n"
    )
    result = check_links(tmp_path)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "arguments", [{"tree_sha": "abc"}, {"skill_path": "skills/use-example/.."}]
)
def test_inventory_invalid_selection_is_structured(arguments):
    result = run_inventory(metadata(), **arguments)
    assert result.returncode == 2
    assert json.loads(result.stdout)["error"]["code"] == "invalid_inventory"
    assert not result.stderr


def test_inventory_preserves_executable_mode():
    document = metadata()
    document["tree"][-1]["mode"] = "100755"
    result = run_inventory(document)
    assert result.returncode == 0
    assert json.loads(result.stdout)["schema_version"] == "aquarium-skill-inventory/v1"
    assert json.loads(result.stdout)["files"][-1]["mode"] == "100755"


def test_inventory_malformed_and_deep_json_errors_are_structured():
    for raw in (
        "{",
        "[" * 2000 + "]" * 2000,
        "[]",
        "null",
        json.dumps({**metadata(), "tree": {}}),
        json.dumps({**metadata(), "tree": [1]}),
    ):
        result = run_inventory(None, raw=raw)
        assert result.returncode == 2
        assert json.loads(result.stdout)["error"]["code"] == "invalid_inventory"
        assert not result.stderr
