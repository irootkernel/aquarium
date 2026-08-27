#!/usr/bin/env python3
"""Produce Aquarium's exact committed development marketplace snapshot."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from dev_manager import artifact_digest

DESCRIPTION_SCHEMA = "aquarium-dev-producer-description/v1"
MANIFEST_SCHEMA = "aquarium-dev-artifact-manifest/v1"
ARTIFACT_PATH = "marketplace"
TRACKED_ROOTS = (".agents/plugins/marketplace.json", "plugins/aquarium")


class ProducerError(Exception):
    pass


def git(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ["git", *arguments],
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise ProducerError(
            result.stderr.decode("utf-8", errors="replace").strip()
            or "Git rejected the producer request."
        )
    return result


def repository_state(require_clean: bool) -> tuple[str, str]:
    root = Path(git("rev-parse", "--show-toplevel").stdout.decode().strip()).resolve()
    if root != Path.cwd().resolve() or not (root / ".git").is_dir():
        raise ProducerError("run the producer from Aquarium's canonical Git root")
    branch = git("symbolic-ref", "--short", "HEAD").stdout.decode().strip()
    if branch != "main":
        raise ProducerError("the producer requires the local main branch")
    git_sha = git("rev-parse", "HEAD").stdout.decode().strip()
    main_sha = git("rev-parse", "refs/heads/main").stdout.decode().strip()
    if git_sha != main_sha:
        raise ProducerError("HEAD must equal local refs/heads/main")
    if require_clean and git("status", "--porcelain=v1").stdout:
        raise ProducerError("the producer requires a clean working tree")
    return git_sha, root.as_posix()


def committed_plugin_version() -> str:
    raw = git("show", "HEAD:plugins/aquarium/.codex-plugin/plugin.json").stdout
    try:
        version = json.loads(raw)["version"]
    except (json.JSONDecodeError, KeyError, TypeError) as error:
        raise ProducerError(
            "the committed Aquarium plugin version is invalid"
        ) from error
    if not isinstance(version, str) or not version:
        raise ProducerError("the committed Aquarium plugin version is invalid")
    return version


def describe() -> dict[str, str]:
    repository_state(require_clean=False)
    return {
        "schema": DESCRIPTION_SCHEMA,
        "project_id": "aquarium",
        "next_version": f"v{committed_plugin_version()}",
        "artifact_kind": "codex-plugin",
        "artifact_path": ARTIFACT_PATH,
    }


def tracked_entries() -> list[tuple[int, str]]:
    output = git("ls-tree", "-r", "-z", "HEAD", "--", *TRACKED_ROOTS).stdout
    entries = []
    for record in output.split(b"\0"):
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        mode, object_kind, _ = metadata.decode().split(" ", 2)
        if object_kind != "blob" or mode not in {"100644", "100755"}:
            raise ProducerError("the plugin snapshot contains an unsupported Git entry")
        entries.append((int(mode, 8), raw_path.decode("utf-8")))
    if not entries:
        raise ProducerError("the committed plugin snapshot is empty")
    return entries


def require_output(value: str | None) -> Path:
    if value is None:
        raise ProducerError("AQUARIUM_DEV_OUTPUT is required")
    output = Path(value)
    if not output.is_absolute() or output.is_symlink() or not output.is_dir():
        raise ProducerError("AQUARIUM_DEV_OUTPUT must be an existing regular directory")
    if any(output.iterdir()):
        raise ProducerError("AQUARIUM_DEV_OUTPUT must be empty")
    return output


def build() -> dict[str, str]:
    git_sha, _ = repository_state(require_clean=True)
    version = committed_plugin_version()
    output = require_output(os.environ.get("AQUARIUM_DEV_OUTPUT"))
    artifact = output / ARTIFACT_PATH
    for mode, relative in tracked_entries():
        target = artifact / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(git("show", f"HEAD:{relative}").stdout)
        target.chmod(mode & 0o777)
    manifest_path = artifact / "plugins/aquarium/.codex-plugin/plugin.json"
    plugin_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    plugin_manifest["version"] = f"{version}-dev.{git_sha[:12]}"
    manifest_path.write_text(
        json.dumps(plugin_manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return {
        "schema": MANIFEST_SCHEMA,
        "project_id": "aquarium",
        "git_sha": git_sha,
        "development_version": f"v{version}-dev.{git_sha[:12]}",
        "artifact_kind": "codex-plugin",
        "artifact_path": ARTIFACT_PATH,
        "sha256": artifact_digest(artifact),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("describe", "build"))
    arguments = parser.parse_args()
    try:
        document = describe() if arguments.command == "describe" else build()
    except ProducerError as error:
        print(f"aquarium development producer: {error}", file=sys.stderr)
        return 2
    except (OSError, subprocess.SubprocessError) as error:
        print(f"aquarium development producer: {error}", file=sys.stderr)
        return 1
    print(json.dumps(document, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
