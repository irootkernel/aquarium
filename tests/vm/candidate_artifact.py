"""Build a committed Aquarium payload without the retired development channel."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

MANIFEST_SCHEMA = "aquarium-dev-artifact-manifest/v1"
TRACKED_ROOTS = (".agents/plugins/marketplace.json", "plugins/aquarium")


class ArtifactError(ValueError):
    pass


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_digest(path: Path) -> str:
    if path.is_symlink():
        raise ArtifactError("artifact must not be a symbolic link")
    if path.is_file():
        return f"sha256:{_file_digest(path)}"
    if not path.is_dir():
        raise ArtifactError("artifact must be a regular file or directory")
    digest = hashlib.sha256()
    for candidate in sorted(path.rglob("*"), key=lambda item: item.as_posix()):
        if candidate.is_symlink() or not (candidate.is_file() or candidate.is_dir()):
            raise ArtifactError(
                "artifact may contain only regular files and directories"
            )
        if candidate.is_file():
            digest.update(candidate.relative_to(path).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(bytes.fromhex(_file_digest(candidate)))
            digest.update(b"\n")
    return f"sha256:{digest.hexdigest()}"


def build(repository: Path, git_sha: str, output: Path) -> dict[str, str]:
    def git(*arguments: str) -> bytes:
        result = subprocess.run(
            ["git", "-C", str(repository), *arguments], capture_output=True, check=False
        )
        if result.returncode:
            raise ArtifactError(result.stderr.decode("utf-8", errors="replace").strip())
        return result.stdout

    root = Path(git("rev-parse", "--show-toplevel").decode().strip()).resolve()
    if root != repository.resolve() or not (root / ".git").is_dir():
        raise ArtifactError("build requires a canonical disposable Git clone")
    if (
        git("symbolic-ref", "--short", "HEAD").decode().strip() != "main"
        or git("rev-parse", "HEAD").decode().strip() != git_sha
        or git("rev-parse", "refs/heads/main").decode().strip() != git_sha
        or git("status", "--porcelain=v1").strip()
    ):
        raise ArtifactError("build requires clean local main at the selected commit")
    if (
        not output.is_absolute()
        or output != output.resolve()
        or not output.is_dir()
        or any(output.iterdir())
    ):
        raise ArtifactError("output must be an empty physical absolute directory")
    plugin_relative = "plugins/aquarium/.codex-plugin/plugin.json"
    plugin = json.loads(git("show", f"HEAD:{plugin_relative}"))
    version = plugin["version"]
    if not isinstance(version, str) or not version:
        raise ArtifactError("committed plugin version must be a nonempty string")
    entries = []
    for record in git("ls-tree", "-r", "-z", "HEAD", "--", *TRACKED_ROOTS).split(b"\0"):
        if not record:
            continue
        metadata, relative = record.split(b"\t", 1)
        mode, kind, _ = metadata.decode().split(" ", 2)
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise ArtifactError("committed payload contains an unsupported Git entry")
        entries.append((int(mode, 8), relative.decode("utf-8")))
    if not entries:
        raise ArtifactError("committed payload is empty")
    artifact = output / "marketplace"
    for mode, relative in entries:
        target = artifact / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(git("show", f"HEAD:{relative}"))
        target.chmod(mode & 0o777)
    plugin["version"] = f"{version}-dev.{git_sha[:12]}"
    (artifact / plugin_relative).write_text(
        json.dumps(plugin, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return {
        "schema": MANIFEST_SCHEMA,
        "project_id": "aquarium",
        "git_sha": git_sha,
        "development_version": f"v{version}-dev.{git_sha[:12]}",
        "artifact_kind": "codex-plugin",
        "artifact_path": "marketplace",
        "sha256": artifact_digest(artifact),
    }
