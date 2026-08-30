import hashlib
import json
import os
import stat
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "plugins/aquarium/skills/dev-aquarium/scripts"
CLI = SCRIPT_DIR / "dev_aquarium.py"
sys.path.insert(0, str(SCRIPT_DIR))

from dev_aquarium import (  # isort: skip
    DOLGORAE_STABLE_SHA256,
    DOLGORAE_STABLE_VERSION,
    open_guarded_executable,
)
from dev_manager import (  # isort: skip
    _unseal_managed_tree,
    resolve_artifact,
    resolve_stable_dolgorae,
)


@pytest.fixture(autouse=True)
def clear_managed_immutable_flags(tmp_path):
    yield
    for current, directories, files in os.walk(tmp_path):
        os.chflags(current, 0)
        for name in (*directories, *files):
            target = Path(current) / name
            if not target.is_symlink():
                os.chflags(target, 0)


PRODUCER = r'''import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path

output = Path(os.environ["AQUARIUM_DEV_OUTPUT"])
sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
artifact = output / "bin/tool"
artifact.parent.mkdir()
artifact.write_text("""#!/bin/sh
if [ "$1" = hold ]; then
  : > "$AQUARIUM_TEST_READY"
  trap 'exit 0' TERM INT
  while :; do sleep 0.05; done
fi
printf '%s\\n' 'development tool'
""", encoding="utf-8")
artifact.chmod(0o755)
manifest = {
    "schema": "aquarium-dev-artifact-manifest/v1",
    "project_id": "podway",
    "git_sha": sha,
    "development_version": f"v0.2.7-dev.{sha[:12]}",
    "artifact_kind": "executable",
    "artifact_path": "bin/tool",
    "sha256": "sha256:" + hashlib.sha256(artifact.read_bytes()).hexdigest(),
}
print(json.dumps(manifest, sort_keys=True))
'''


def create_repository(path: Path) -> Path:
    path.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", path], check=True)
    subprocess.run(["git", "-C", path, "config", "user.name", "Test"], check=True)
    subprocess.run(
        ["git", "-C", path, "config", "user.email", "test@example.invalid"],
        check=True,
    )
    (path / "Makefile").write_text(
        """aquarium-dev-describe:
\t@printf '%s\\n' '{"schema":"aquarium-dev-producer-description/v1","project_id":"podway","next_version":"v0.2.7","artifact_kind":"executable","artifact_path":"bin/tool"}'

aquarium-dev-build:
\t@python3 producer.py
""",
        encoding="utf-8",
    )
    (path / "producer.py").write_text(PRODUCER, encoding="utf-8")
    subprocess.run(["git", "-C", path, "add", "."], check=True)
    subprocess.run(["git", "-C", path, "commit", "-q", "-m", "initial"], check=True)
    return path


def run_cli(host_root: Path, *arguments: str, environment=None):
    return subprocess.run(
        [sys.executable, CLI, "--host-root", host_root, *arguments],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )


def payload(result: subprocess.CompletedProcess[str]):
    return json.loads(result.stdout or result.stderr)


def enroll_and_build(repository: Path, host_root: Path) -> str:
    enrolled = run_cli(
        host_root,
        "enroll",
        "--repository",
        repository,
        "--approve-enrollment",
        "--approve-hook",
    )
    assert enrolled.returncode == 0, enrolled.stderr
    rebuilt = run_cli(
        host_root,
        "rebuild",
        "--repository",
        repository,
        "--approve-build",
    )
    assert rebuilt.returncode == 0, rebuilt.stderr
    return payload(rebuilt)["details"]["git_sha"]


def commit_next_revision(repository: Path) -> str:
    marker = repository / "revision.txt"
    marker.write_text(str(time.monotonic_ns()), encoding="utf-8")
    subprocess.run(["git", "-C", repository, "add", marker.name], check=True)
    subprocess.run(
        ["git", "-C", repository, "commit", "-q", "--no-verify", "-m", "next"],
        check=True,
    )
    return subprocess.check_output(
        ["git", "-C", repository, "rev-parse", "HEAD"], text=True
    ).strip()


def wait_missing(path: Path) -> None:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and path.exists():
        time.sleep(0.05)
    assert not path.exists()


def test_stable_fallback_is_allowed_only_without_enrollment(tmp_path):
    host_root = tmp_path / "host"
    stable = tmp_path / "stable"
    stable.write_text("stable", encoding="utf-8")

    result = run_cli(
        host_root,
        "resolve",
        "--project-id",
        "podway",
        "--stable",
        stable,
    )

    assert result.returncode == 0
    assert payload(result)["details"]["source"] == "stable"

    repository = create_repository(tmp_path / "repository")
    enrolled = run_cli(
        host_root,
        "enroll",
        "--repository",
        repository,
        "--approve-enrollment",
        "--approve-hook",
    )
    assert enrolled.returncode == 0
    rejected = run_cli(
        host_root,
        "resolve",
        "--project-id",
        "podway",
        "--stable",
        stable,
    )
    assert rejected.returncode == 1
    assert payload(rejected)["error"]["code"] == "artifact_missing"


def test_resolution_fails_closed_on_corrupt_enrolled_artifact(tmp_path):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    enroll_and_build(repository, host_root)
    artifact = (host_root / "current/podway/bin/tool").resolve()
    _unseal_managed_tree(artifact.parents[1])
    artifact.chmod(0o700)
    artifact.write_text("corrupt", encoding="utf-8")

    result = run_cli(host_root, "resolve", "--project-id", "podway")

    assert result.returncode == 1
    assert payload(result)["error"]["code"] == "checksum_mismatch"


def test_shared_resolution_lease_defers_cleanup_until_release(tmp_path):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    first_sha = enroll_and_build(repository, host_root)
    first_generation = host_root / "artifacts/podway" / first_sha
    first_resolution = resolve_artifact("podway", host_root)
    first_execution = first_resolution.execution_path
    second_resolution = resolve_artifact("podway", host_root)
    second_sha = commit_next_revision(repository)

    rebuilt = run_cli(
        host_root,
        "rebuild",
        "--repository",
        repository,
        "--approve-build",
    )

    assert rebuilt.returncode == 0, rebuilt.stderr
    assert (host_root / "current/podway").resolve().name == second_sha
    assert first_generation.exists()
    assert first_resolution.git_sha == first_sha
    assert second_resolution.git_sha == first_sha
    first_resolution.close()
    assert first_generation.exists()
    second_resolution.close()
    wait_missing(first_generation)
    assert first_execution is not None
    assert not first_execution.exists()


def test_publication_immediately_removes_an_unleased_generation(tmp_path):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    first_sha = enroll_and_build(repository, host_root)
    first_generation = host_root / "artifacts/podway" / first_sha
    commit_next_revision(repository)

    rebuilt = run_cli(
        host_root,
        "rebuild",
        "--repository",
        repository,
        "--approve-build",
    )

    assert rebuilt.returncode == 0, rebuilt.stderr
    assert not first_generation.exists()


def test_launch_holds_lease_through_child_interruption(tmp_path):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    first_sha = enroll_and_build(repository, host_root)
    first_generation = host_root / "artifacts/podway" / first_sha
    ready = tmp_path / "ready"
    environment = os.environ.copy()
    environment["AQUARIUM_TEST_READY"] = str(ready)
    child = subprocess.Popen(
        [
            sys.executable,
            CLI,
            "--host-root",
            host_root,
            "launch",
            "--project-id",
            "podway",
            "--",
            "hold",
        ],
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and not ready.exists():
        time.sleep(0.05)
    assert ready.exists(), child.stderr.read() if child.poll() is not None else ""
    commit_next_revision(repository)

    rebuilt = run_cli(
        host_root,
        "rebuild",
        "--repository",
        repository,
        "--approve-build",
    )

    assert rebuilt.returncode == 0, rebuilt.stderr
    assert first_generation.exists()
    child.terminate()
    child.wait(timeout=5)
    wait_missing(first_generation)


def test_guarded_launch_accepts_only_the_complete_exact_generation(tmp_path):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    git_sha = enroll_and_build(repository, host_root)
    manifest = json.loads(
        (
            host_root / "artifacts/podway" / git_sha / ".aquarium-manifest.json"
        ).read_text(encoding="utf-8")
    )

    launched = run_cli(
        host_root,
        "launch",
        "--project-id",
        "podway",
        "--expected-git-sha",
        manifest["git_sha"],
        "--expected-development-version",
        manifest["development_version"],
        "--expected-sha256",
        manifest["sha256"],
    )

    assert launched.returncode == 0, launched.stderr
    assert launched.stdout == "development tool\n"

    mismatched = run_cli(
        host_root,
        "launch",
        "--project-id",
        "podway",
        "--expected-git-sha",
        "0" * 40,
        "--expected-development-version",
        manifest["development_version"],
        "--expected-sha256",
        manifest["sha256"],
    )
    assert mismatched.returncode == 1
    assert payload(mismatched)["error"]["code"] == "artifact_invalid"


def test_guarded_launch_rejects_partial_or_stable_identity(tmp_path):
    host_root = tmp_path / "host"
    partial = run_cli(
        host_root,
        "launch",
        "--project-id",
        "podway",
        "--expected-git-sha",
        "0" * 40,
    )
    assert partial.returncode == 2
    assert payload(partial)["error"]["code"] == "invalid_arguments"

    stable = tmp_path / "stable"
    stable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    stable.chmod(0o700)
    guarded_stable = run_cli(
        host_root,
        "launch",
        "--project-id",
        "podway",
        "--stable",
        stable,
        "--expected-git-sha",
        "0" * 40,
        "--expected-development-version",
        "v0.2.7-dev.000000000000",
        "--expected-sha256",
        "sha256:" + "0" * 64,
    )
    assert guarded_stable.returncode == 1
    assert payload(guarded_stable)["error"]["code"] == "artifact_invalid"


def test_execution_alias_rejects_source_path_replacement(tmp_path):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    enroll_and_build(repository, host_root)
    resolved = resolve_artifact("podway", host_root)
    assert resolved.execution_path is not None
    expected = resolved.execution_path.read_bytes()
    replacement = tmp_path / "replacement"
    replacement.write_text("replaced", encoding="utf-8")
    with pytest.raises(OSError):
        os.replace(replacement, resolved.path)

    assert resolved.execution_path.read_bytes() == expected
    assert resolved.execution_path != resolved.path
    assert not os.path.samefile(resolved.execution_path, resolved.path)
    assert stat.S_IMODE(resolved.path.stat().st_mode) == 0o500
    assert stat.S_IMODE(resolved.execution_path.stat().st_mode) == 0o500
    resolved.close()
    os.chflags(resolved.execution_path, 0)
    os.chflags(resolved.execution_path.parent, 0)


def test_guarded_descriptor_revalidation_rejects_alias_replacement(tmp_path):
    repository = create_repository(tmp_path / "repository")
    host_root = tmp_path / "host"
    enroll_and_build(repository, host_root)
    resolved = resolve_artifact("podway", host_root)
    descriptor = open_guarded_executable(resolved, resolved.sha256)
    assert not os.get_inheritable(descriptor)
    alias = resolved.execution_path
    replacement = alias.parent / "replacement"
    with pytest.raises(OSError):
        alias.parent.chmod(0o700)
        replacement.write_text("replaced", encoding="utf-8")
        replacement.chmod(0o700)
        os.replace(replacement, alias)

    os.close(descriptor)
    resolved.close()
    os.chflags(alias, 0)
    os.chflags(alias.parent, 0)


@pytest.mark.parametrize(
    "operation",
    (
        ("specialist", "review"),
        ("review-target", "capture"),
        ("review-target", "settle"),
    ),
)
def test_dolgorae_source_bearing_launch_requires_exact_guards(tmp_path, operation):
    result = run_cli(
        tmp_path / "host",
        "launch",
        "--project-id",
        "dolgorae",
        "--",
        *operation,
    )

    assert result.returncode == 2
    assert payload(result)["error"]["code"] == "invalid_arguments"


@pytest.mark.parametrize(
    "guards",
    (
        ("--expected-git-sha", "0" * 40),
        (
            "--expected-development-version",
            "v0.1.0-dev.000000000000",
            "--expected-sha256",
            "sha256:" + "0" * 64,
        ),
        (
            "--expected-sha256",
            "sha256:invalid",
            "--expected-development-version",
            "v0.1.0-dev.000000000000",
            "--expected-git-sha",
            "0" * 40,
        ),
        (
            "--expected-git-sha",
            "",
            "--expected-development-version",
            "v0.1.0-dev.000000000000",
            "--expected-sha256",
            "sha256:" + "0" * 64,
        ),
        (
            "--expected-development-version",
            "v0.1.0-dev." + "0" * 13,
            "--expected-git-sha",
            "0" * 40,
            "--expected-sha256",
            "sha256:" + "0" * 64,
        ),
        (
            "--expected-sha256",
            "sha256:" + "0" * 65,
            "--expected-development-version",
            "v0.1.0-dev.000000000000",
            "--expected-git-sha",
            "0" * 40,
        ),
    ),
)
@pytest.mark.parametrize(
    "operation",
    (
        ("specialist", "review"),
        ("review-target", "capture"),
        ("review-target", "settle"),
    ),
)
def test_dolgorae_review_launch_rejects_partial_and_malformed_guards(
    tmp_path, guards, operation
):
    result = run_cli(
        tmp_path / "host",
        "launch",
        "--project-id",
        "dolgorae",
        *guards,
        "--",
        *operation,
    )

    assert result.returncode == 2
    assert payload(result)["error"]["code"] == "invalid_arguments"


def test_dolgorae_review_launch_accepts_reordered_complete_guard_options(tmp_path):
    result = run_cli(
        tmp_path / "host",
        "launch",
        "--project-id",
        "dolgorae",
        "--expected-sha256",
        "sha256:" + "0" * 64,
        "--expected-git-sha",
        "0" * 40,
        "--expected-development-version",
        "v0.1.0-dev.000000000000",
        "--",
        "review-target",
        "settle",
    )

    assert result.returncode == 1
    assert payload(result)["error"]["code"] == "enrollment_missing"


def stable_dolgorae(path: Path) -> str:
    path.write_text(
        """#!/bin/sh
if [ "$1" = "--version" ]; then
  printf '%s\\n' '{"schema_version":1,"ok":true,"command":"version","invocation_id":"019d0000-0000-7000-8000-000000000000","data":{"text":"dolgorae 0.1.0"}}'
else
  printf '%s\\n' 'stable dolgorae'
fi
""",
        encoding="utf-8",
    )
    path.chmod(0o700)
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def test_dolgorae_stable_resolver_creates_immutable_private_copy(tmp_path):
    host_root = tmp_path / "host"
    stable = tmp_path / "dolgorae"
    digest = stable_dolgorae(stable)

    resolved = resolve_stable_dolgorae(
        host_root,
        stable,
        "v0.1.0",
        digest,
    )

    assert resolved.source == "stable"
    assert resolved.stable_version == "v0.1.0"
    assert resolved.sha256 == digest
    runtime = host_root / "runtime/dolgorae"
    execution_paths = list(runtime.glob("stable-0.1.0-*/executable"))
    assert len(execution_paths) == 1
    assert execution_paths[0].read_bytes() == stable.read_bytes()
    assert not os.path.samefile(execution_paths[0], stable)
    resolved.close()


@pytest.mark.parametrize(
    "arguments",
    (
        ("--expected-stable-version", "v0.1.0"),
        ("--expected-stable-sha256", "sha256:" + "0" * 64),
        (
            "--expected-stable-version",
            "0.1.0",
            "--expected-stable-sha256",
            "sha256:" + "0" * 64,
        ),
    ),
)
def test_dolgorae_stable_guard_rejects_partial_or_malformed_identity(
    tmp_path, arguments
):
    stable = tmp_path / "dolgorae"
    stable_dolgorae(stable)

    result = run_cli(
        tmp_path / "host",
        "launch",
        "--project-id",
        "dolgorae",
        "--stable",
        stable,
        *arguments,
        "--",
        "review-target",
        "capture",
    )

    assert result.returncode == 2
    assert payload(result)["error"]["code"] == "invalid_arguments"


def test_dolgorae_stable_guard_rejects_unpinned_checksum_and_version(tmp_path):
    stable = tmp_path / "dolgorae"
    digest = stable_dolgorae(stable)
    host_root = tmp_path / "host"

    checksum_mismatch = run_cli(
        host_root,
        "launch",
        "--project-id",
        "dolgorae",
        "--stable",
        stable,
        "--expected-stable-version",
        "v0.1.0",
        "--expected-stable-sha256",
        "sha256:" + "0" * 64,
    )
    version_mismatch = run_cli(
        host_root,
        "launch",
        "--project-id",
        "dolgorae",
        "--stable",
        stable,
        "--expected-stable-version",
        "v0.1.1",
        "--expected-stable-sha256",
        digest,
    )

    assert checksum_mismatch.returncode == 2
    assert payload(checksum_mismatch)["error"]["code"] == "invalid_arguments"
    assert version_mismatch.returncode == 2
    assert payload(version_mismatch)["error"]["code"] == "invalid_arguments"


def test_dolgorae_stable_guard_rejects_nonofficial_binary(tmp_path):
    stable = tmp_path / "dolgorae"
    stable_dolgorae(stable)
    result = run_cli(
        tmp_path / "host",
        "launch",
        "--project-id",
        "dolgorae",
        "--stable",
        stable,
        "--expected-stable-version",
        DOLGORAE_STABLE_VERSION,
        "--expected-stable-sha256",
        DOLGORAE_STABLE_SHA256,
    )

    assert result.returncode == 1
    assert payload(result)["error"]["code"] == "artifact_invalid"


def test_dolgorae_stable_and_development_guards_are_mutually_exclusive(tmp_path):
    stable = tmp_path / "dolgorae"
    stable_dolgorae(stable)
    result = run_cli(
        tmp_path / "host",
        "launch",
        "--project-id",
        "dolgorae",
        "--stable",
        stable,
        "--expected-stable-version",
        DOLGORAE_STABLE_VERSION,
        "--expected-stable-sha256",
        DOLGORAE_STABLE_SHA256,
        "--expected-git-sha",
        "0" * 40,
        "--expected-development-version",
        "v0.1.0-dev.000000000000",
        "--expected-sha256",
        DOLGORAE_STABLE_SHA256,
    )

    assert result.returncode == 2
    assert payload(result)["error"]["code"] == "invalid_arguments"
