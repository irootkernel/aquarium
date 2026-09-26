#!/usr/bin/env python3
"""Select a complete paired-skill inventory from official Git tree metadata."""

import argparse
import json
import re
import sys

SCHEMA = "aquarium-skill-inventory/v1"


def git_sha(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None


def safe_path(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        and "\\" not in value
        and not any(ord(character) < 32 or ord(character) == 127 for character in value)
        and all(part not in {"", ".", ".."} for part in value.split("/"))
    )


def inventory(document: object, tree_sha: str, skill_path: str) -> list[dict[str, str]]:
    if not git_sha(tree_sha) or not safe_path(skill_path):
        raise ValueError("invalid selected tree or skill path")
    if (
        not isinstance(document, dict)
        or document.get("sha") != tree_sha
        or document.get("truncated") is not False
        or not isinstance(document.get("tree"), list)
    ):
        raise ValueError("complete metadata for the selected tree is required")
    seen = set()
    files = []
    directory_found = False
    for entry in document["tree"]:
        if not isinstance(entry, dict) or not safe_path(entry.get("path")):
            raise ValueError("invalid tree path")
        path = entry["path"]
        if path in seen:
            raise ValueError("duplicate tree path")
        seen.add(path)
        if path != skill_path and not path.startswith(skill_path + "/"):
            continue
        if not git_sha(entry.get("sha")):
            raise ValueError("invalid selected entry identity")
        kind, mode = entry.get("type"), entry.get("mode")
        if kind == "tree" and mode == "040000":
            directory_found |= path == skill_path
            continue
        if path == skill_path or kind != "blob" or mode not in ("100644", "100755"):
            raise ValueError("selected skill contains a non-regular input")
        files.append(
            {
                "path": path[len(skill_path) + 1 :],
                "blob_sha": entry["sha"],
                "mode": mode,
            }
        )
    if not directory_found or not any(row["path"] == "SKILL.md" for row in files):
        raise ValueError("selected skill directory or SKILL.md is missing")
    return sorted(files, key=lambda row: row["path"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tree-sha", required=True)
    parser.add_argument("--skill-path", required=True)
    arguments = parser.parse_args()
    try:
        files = inventory(
            json.load(sys.stdin), arguments.tree_sha, arguments.skill_path
        )
    except (ValueError, UnicodeError, RecursionError):
        print(
            json.dumps(
                {
                    "schema_version": SCHEMA,
                    "error": {
                        "code": "invalid_inventory",
                        "message": "Complete valid tree metadata and selection arguments are required.",
                    },
                }
            )
        )
        return 2
    print(
        json.dumps(
            {
                "schema_version": SCHEMA,
                "tree_sha": arguments.tree_sha,
                "skill_path": arguments.skill_path,
                "files": files,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
