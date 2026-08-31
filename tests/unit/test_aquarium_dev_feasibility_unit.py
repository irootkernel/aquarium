import fcntl
import os
import platform
import stat
import subprocess
import sys
import textwrap
from pathlib import Path


def run_python(program: str, *arguments: Path, env: dict[str, str] | None = None):
    return subprocess.run(
        [
            sys.executable,
            "-c",
            textwrap.dedent(program),
            *(str(arg) for arg in arguments),
        ],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def assert_supported_host() -> None:
    assert platform.system() == "Darwin"
    assert platform.machine() == "arm64"


def test_shared_and_exclusive_leases_follow_supported_host_contract(tmp_path):
    assert_supported_host()
    lock_path = tmp_path / "artifact.lock"
    lock_path.touch()
    probe = """
        import fcntl
        import sys

        mode = fcntl.LOCK_SH if sys.argv[2] == "shared" else fcntl.LOCK_EX
        with open(sys.argv[1], "rb") as lock:
            try:
                fcntl.flock(lock, mode | fcntl.LOCK_NB)
            except BlockingIOError:
                raise SystemExit(73)
    """

    with lock_path.open("rb") as shared:
        fcntl.flock(shared, fcntl.LOCK_SH)
        assert run_python(probe, lock_path, Path("shared")).returncode == 0
        assert run_python(probe, lock_path, Path("exclusive")).returncode == 73

    with lock_path.open("rb") as exclusive:
        fcntl.flock(exclusive, fcntl.LOCK_EX)
        assert run_python(probe, lock_path, Path("shared")).returncode == 73
        assert run_python(probe, lock_path, Path("exclusive")).returncode == 73


def test_artifact_promotion_and_current_selector_are_atomic(tmp_path):
    assert_supported_host()
    artifacts = tmp_path / "artifacts"
    staging = tmp_path / "staging"
    selectors = tmp_path / "current"
    artifacts.mkdir()
    staging.mkdir()
    selectors.mkdir()
    assert artifacts.stat().st_dev == staging.stat().st_dev

    candidate = staging / "sha-one"
    candidate.mkdir()
    (candidate / "tool").write_text("one", encoding="utf-8")
    published = artifacts / "sha-one"
    os.replace(candidate, published)
    assert (published / "tool").read_text(encoding="utf-8") == "one"

    old = artifacts / "sha-old"
    old.mkdir()
    current = selectors / "tool"
    current.symlink_to(old)
    replacement = selectors / ".tool.next"
    replacement.symlink_to(published)
    os.replace(replacement, current)
    assert current.is_symlink()
    assert current.resolve() == published.resolve()


def test_foreign_post_commit_hook_survives_and_failure_cannot_rollback_commit(tmp_path):
    assert_supported_host()
    repository = tmp_path / "repository"
    repository.mkdir()
    subprocess.run(["git", "init", "-q", repository], check=True)
    subprocess.run(
        ["git", "-C", repository, "config", "user.name", "Feasibility"], check=True
    )
    subprocess.run(
        [
            "git",
            "-C",
            repository,
            "config",
            "user.email",
            "feasibility@example.invalid",
        ],
        check=True,
    )
    hook = repository / ".git" / "hooks" / "post-commit"
    original = (
        b'#!/bin/sh\nprintf foreign >> "$(git rev-parse --git-dir)/foreign-ran"\n'
    )
    marker = b"""# BEGIN AQUARIUM DEV
printf 'request failed\\n' >&2
false
# END AQUARIUM DEV
"""
    hook.write_bytes(original + marker)
    hook.chmod(0o750)

    (repository / "tracked").write_text("content", encoding="utf-8")
    subprocess.run(["git", "-C", repository, "add", "tracked"], check=True)
    before = subprocess.run(
        ["git", "-C", repository, "rev-parse", "--verify", "HEAD"],
        capture_output=True,
        check=False,
    )
    commit = subprocess.run(
        ["git", "-C", repository, "commit", "-m", "exercise hook"],
        capture_output=True,
        text=True,
        check=False,
    )
    after = subprocess.run(
        ["git", "-C", repository, "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert before.returncode != 0
    assert commit.returncode == 0
    assert "request failed" in commit.stderr
    assert len(after.stdout.strip()) == 40
    assert (repository / ".git" / "foreign-ran").read_text(
        encoding="utf-8"
    ) == "foreign"
    assert hook.read_bytes().startswith(original)
    assert stat.S_IMODE(hook.stat().st_mode) == 0o750
