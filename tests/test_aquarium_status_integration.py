from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import textwrap
import unicodedata
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "plugins/aquarium/tools/aquarium-status/aquarium_status.py"
STATUS_MODULES = STATUS.parent
RECORD_SCHEMA = "aquarium-production-status-record/v1"
RECORD_RECEIPT_SCHEMA = "aquarium-production-status-record-receipt/v2"
REPORT_SCHEMA = "aquarium-production-status-report/v2"
FORGET_RECEIPT_SCHEMA = "aquarium-production-status-forget-receipt/v1"
ERROR_SCHEMA = "aquarium-production-status-error/v1"


def environment(home: Path) -> dict[str, str]:
    values = os.environ.copy()
    values["HOME"] = str(home)
    values["PYTHONDONTWRITEBYTECODE"] = "1"
    for name in tuple(values):
        if name.startswith("GIT_"):
            values.pop(name)
    return values


def git(
    *arguments: str, home: Path, cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        env=environment(home),
    )


def repository(path: Path, home: Path, *, commit: bool = False) -> Path:
    path.mkdir(parents=True)
    git("init", "-q", str(path), home=home)
    if commit:
        git("config", "user.name", "Aquarium Test", home=home, cwd=path)
        git("config", "user.email", "aquarium@example.invalid", home=home, cwd=path)
        (path / "tracked.txt").write_text("fixture\n", encoding="utf-8")
        git("add", "tracked.txt", home=home, cwd=path)
        git("commit", "-q", "-m", "fixture", home=home, cwd=path)
    return path.resolve()


def initialize_state(home: Path) -> None:
    state = home / ".aquarium"
    state.mkdir(mode=0o700)
    lock = state / "status.lock"
    lock.touch(mode=0o600)
    lock.chmod(0o600)


def request(
    root: Path,
    revision: int,
    *,
    attempt_id: str | None = None,
    project: str = "Fixture",
    outcome: str = "ready",
    scope: dict[str, Any] | None = None,
    components: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema": RECORD_SCHEMA,
        "attempt_id": attempt_id or str(uuid.uuid4()),
        "expected_row_revision": revision,
        "git_root": unicodedata.normalize("NFC", str(root)),
        "project": project,
        "started_at": "2026-09-18T00:00:00Z",
        "completed_at": "2026-09-18T00:01:00Z",
        "outcome": outcome,
        "scope": scope or {"kind": "full"},
        "components": components or {},
    }


def observation(value: str, outcome: str = "ready") -> dict[str, Any]:
    return {
        "outcome": outcome,
        "version": {
            "value": value,
            "source": "recorded_attempt",
            "status": "observed",
        },
    }


def invoke(
    home: Path,
    *arguments: str,
    stdin: dict[str, Any] | str | None = None,
    extra_environment: dict[str, str] | None = None,
    timeout: float | None = None,
) -> subprocess.CompletedProcess[str]:
    if isinstance(stdin, dict):
        input_text = json.dumps(stdin, ensure_ascii=False) + "\n"
    else:
        input_text = stdin
    process_environment = environment(home)
    process_environment.update(extra_environment or {})
    return subprocess.run(
        [sys.executable, str(STATUS), *arguments],
        input=input_text,
        capture_output=True,
        text=True,
        check=False,
        env=process_environment,
        timeout=timeout,
    )


def spawn_record(home: Path, payload: dict[str, Any]) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [sys.executable, str(STATUS), "record"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=environment(home),
    )


def complete_record(
    process: subprocess.Popen[str], payload: dict[str, Any]
) -> subprocess.CompletedProcess[str]:
    stdout, stderr = process.communicate(json.dumps(payload) + "\n", timeout=20)
    return subprocess.CompletedProcess(process.args, process.returncode, stdout, stderr)


def complete_records_concurrently(
    processes: list[subprocess.Popen[str]], payloads: list[dict[str, Any]]
) -> list[subprocess.CompletedProcess[str]]:
    with ThreadPoolExecutor(max_workers=len(processes)) as executor:
        return list(
            executor.map(
                lambda pair: complete_record(*pair),
                zip(processes, payloads, strict=True),
            )
        )


def output(result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert (
        result.stdout == json.dumps(payload, sort_keys=True, ensure_ascii=False) + "\n"
    )
    return payload


def error(
    result: subprocess.CompletedProcess[str], exit_code: int, code: str
) -> dict[str, Any]:
    assert result.returncode == exit_code
    assert result.stdout == ""
    payload = json.loads(result.stderr)
    assert (
        result.stderr == json.dumps(payload, sort_keys=True, ensure_ascii=False) + "\n"
    )
    assert set(payload) == {"schema", "error"}
    assert payload["schema"] == ERROR_SCHEMA
    assert set(payload["error"]) == {"code", "message"}
    assert payload["error"]["code"] == code
    assert isinstance(payload["error"]["message"], str)
    assert payload["error"]["message"]
    return payload


def report(home: Path) -> dict[str, Any]:
    payload = output(invoke(home, "show", "--format", "json"))
    assert payload["schema"] == REPORT_SCHEMA
    return payload


def ledger(home: Path) -> tuple[dict[str, Any], bytes]:
    raw = (home / ".aquarium/status.yaml").read_bytes()
    return yaml.safe_load(raw), raw


def canonical_digest(value: Any) -> str:
    content = (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode()
    return hashlib.sha256(content).hexdigest()


def injected_record(
    home: Path, payload: dict[str, Any], failure: str
) -> subprocess.CompletedProcess[str]:
    driver = textwrap.dedent(
        """
        import io
        import os
        import stat
        import sys
        from pathlib import Path

        sys.path.insert(0, os.environ["STATUS_MODULES"])
        import aquarium_status
        import status_store

        failure = os.environ["INJECT_FAILURE"]
        state = {
            "failed": False,
            "directory_fsyncs": 0,
            "temporary_descriptors": set(),
            "write_once_calls": 0,
        }
        original_fdopen = status_store.os.fdopen
        original_fsync = status_store.os.fsync
        original_mkstemp = status_store.tempfile.mkstemp
        original_open = status_store.os.open
        original_replace = status_store.os.replace
        original_write_once = status_store._write_once

        def fdopen(descriptor, *args, **kwargs):
            stream = original_fdopen(descriptor, *args, **kwargs)
            if (
                failure == "temp_write"
                and descriptor in state["temporary_descriptors"]
                and not state["failed"]
            ):
                return FailingWriter(stream)
            return stream

        def fsync(descriptor):
            kind = os.fstat(descriptor).st_mode
            if stat.S_ISDIR(kind):
                state["directory_fsyncs"] += 1
            selected = (
                failure == "file_fsync" and stat.S_ISREG(kind)
            ) or (
                failure == "parent_fsync"
                and stat.S_ISDIR(kind)
                and state["directory_fsyncs"] == 1
            )
            if selected and not state["failed"]:
                state["failed"] = True
                raise OSError("injected fsync failure")
            result = original_fsync(descriptor)
            if failure == "parent_fsync" and state["directory_fsyncs"] == 2:
                (Path.home() / "rollback-parent-fsynced").touch()
            return result

        def mkstemp(*args, **kwargs):
            descriptor, name = original_mkstemp(*args, **kwargs)
            state["temporary_descriptors"].add(descriptor)
            return descriptor, name

        def open_file(path, *args, **kwargs):
            if failure == "lock_open" and os.fspath(path).endswith("status.lock"):
                raise OSError("injected lock open failure")
            return original_open(path, *args, **kwargs)

        def replace(source, target):
            if failure == "replace" and not state["failed"]:
                state["failed"] = True
                raise OSError("injected replacement failure")
            return original_replace(source, target)

        class FailingWriter:
            def __init__(self, stream):
                self.stream = stream

            def __enter__(self):
                self.stream.__enter__()
                return self

            def __exit__(self, *arguments):
                return self.stream.__exit__(*arguments)

            def write(self, content):
                state["failed"] = True
                raise OSError("injected temporary write failure")

        def unexpected_writer(*arguments):
            (Path.home() / "writer-called").write_text("called", encoding="utf-8")
            raise AssertionError("validation reached the ledger writer")

        def failed_write_once(target, content):
            state["write_once_calls"] += 1
            if state["write_once_calls"] == 1:
                original_write_once(target, content)
                raise OSError("injected post-replacement failure")
            (Path.home() / "rollback-attempted").touch()
            raise OSError("injected rollback failure")

        status_store.os.fdopen = fdopen
        status_store.os.fsync = fsync
        status_store.tempfile.mkstemp = mkstemp
        status_store.os.open = open_file
        status_store.os.replace = replace
        if failure == "validation_writer":
            aquarium_status.write_ledger = unexpected_writer
        if failure == "rollback":
            status_store._write_once = failed_write_once
        sys.stdin = io.StringIO(os.environ["RECORD_JSON"] + "\\n")
        raise SystemExit(aquarium_status.main(["record"]))
        """
    )
    injected_environment = environment(home)
    injected_environment.update(
        {
            "STATUS_MODULES": str(STATUS_MODULES),
            "INJECT_FAILURE": failure,
            "RECORD_JSON": json.dumps(payload),
        }
    )
    return subprocess.run(
        [sys.executable, "-c", driver],
        capture_output=True,
        text=True,
        check=False,
        env=injected_environment,
    )


def test_concurrent_different_roots_merge_without_lost_update(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    initialize_state(home)
    roots = [repository(tmp_path / name, home) for name in ("alpha", "beta")]
    payloads = [request(root, 0, project=root.name) for root in roots]

    processes = [spawn_record(home, payload) for payload in payloads]
    results = complete_records_concurrently(processes, payloads)

    receipts = [output(result) for result in results]
    assert {item["schema"] for item in receipts} == {RECORD_RECEIPT_SCHEMA}
    assert {item["file_revision"] for item in receipts} == {1, 2}
    assert {item["row_revision"] for item in receipts} == {1}
    current = report(home)
    assert current["ledger"] == {"state": "present", "file_revision": 2}
    assert [item["git_root"] for item in current["repositories"]] == sorted(
        map(str, roots), key=lambda item: item.encode()
    )


def test_concurrent_same_root_has_one_revision_winner(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    initialize_state(home)
    root = repository(tmp_path / "repository", home)
    payloads = [request(root, 0, project=name) for name in ("first", "second")]

    processes = [spawn_record(home, payload) for payload in payloads]
    results = complete_records_concurrently(processes, payloads)

    assert sorted(item.returncode for item in results) == [0, 3]
    winner = next(item for item in results if item.returncode == 0)
    loser = next(item for item in results if item.returncode == 3)
    receipt = output(winner)
    assert receipt["file_revision"] == receipt["row_revision"] == 1
    error(loser, 3, "revision_conflict")
    current, _ = ledger(home)
    assert current["file_revision"] == 1
    assert current["repositories"][0]["row_revision"] == 1


def test_git_identity_ignores_repository_scoping_environment(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    root = repository(tmp_path / "repository", home)
    hostile = repository(tmp_path / "hostile", home)

    receipt = output(
        invoke(
            home,
            "record",
            stdin=request(root, 0),
            extra_environment={
                "GIT_DIR": str(hostile / ".git"),
                "GIT_WORK_TREE": str(hostile),
                "GIT_COMMON_DIR": str(hostile / ".git"),
            },
        )
    )

    assert receipt["git_root"] == str(root)
    assert report(home)["repositories"][0]["root_state"] == "present"


def test_exact_latest_replay_and_stale_historical_rejection(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    root = repository(tmp_path / "repository", home)
    first = request(root, 0, outcome="failed")

    recorded = output(invoke(home, "record", stdin=first))
    path = home / ".aquarium/status.yaml"
    original_bytes = path.read_bytes()
    original_mtime = path.stat().st_mtime_ns
    replayed = output(invoke(home, "record", stdin=first))

    assert recorded == {
        "schema": RECORD_RECEIPT_SCHEMA,
        "status": "recorded",
        "changed": True,
        "language_status": "observed",
        "attempt_id": first["attempt_id"],
        "git_root": str(root),
        "file_revision": 1,
        "row_revision": 1,
    }
    assert replayed == {
        **recorded,
        "status": "replayed",
        "changed": False,
        "language_status": "not_checked",
    }
    assert path.read_bytes() == original_bytes
    assert path.stat().st_mtime_ns == original_mtime

    second = request(root, 1, outcome="partial")
    output(invoke(home, "record", stdin=second))
    error(invoke(home, "record", stdin=first), 3, "revision_conflict")

    changed = {**second, "project": "changed"}
    error(invoke(home, "record", stdin=changed), 3, "attempt_conflict")


def test_language_declarations_are_recorded_and_explicitly_refreshed(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    root = repository(tmp_path / "repository", home)
    (root / "go.mod").write_text(
        "module example.invalid/root\ngo 1.26\ntoolchain go1.26.6\n"
    )
    (root / "rust-toolchain.toml").write_text('[toolchain]\nchannel = "1.97.1"\n')
    (root / "Cargo.toml").write_text(
        '[workspace]\nmembers = ["nested"]\n[workspace.package]\nrust-version = "1.97.1"\n'
    )
    (root / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.11"\n')
    (root / "package.json").write_text(
        json.dumps({"devDependencies": {"typescript": "~6.0.2"}})
    )
    (root / "pubspec.yaml").write_text("environment:\n  sdk: ^3.9.2\n")
    nested = root / "nested"
    nested.mkdir()
    (nested / "go.mod").write_text("module example.invalid/nested\ngo 1.25\n")
    (nested / "Cargo.toml").write_text(
        '[package]\nname = "nested"\nversion = "0.1.0"\nrust-version.workspace = true\n'
    )
    git("add", ".", home=home, cwd=root)

    attempt = request(root, 0)
    receipt = output(invoke(home, "record", stdin=attempt))
    assert receipt["language_status"] == "observed"
    before = report(home)["repositories"][0]
    languages = {
        item["name"]: item["declarations"]
        for item in before["language_inventory"]["languages"]
    }
    assert list(languages) == ["dart", "go", "python", "rust", "typescript"]
    assert [
        (item["path"], item["kind"], item["value"]) for item in languages["go"]
    ] == [
        ("go.mod", "go", "1.26"),
        ("go.mod", "toolchain", "go1.26.6"),
        ("nested/go.mod", "go", "1.25"),
    ]
    assert languages["rust"][0]["value"] == "1.97.1"
    assert languages["python"][0]["value"] == ">=3.11"
    assert languages["typescript"][0]["value"] == "~6.0.2"
    assert languages["dart"][0]["value"] == "^3.9.2"

    (root / "go.mod").write_text("module example.invalid/root\ngo 1.27\n")
    assert (
        report(home)["repositories"][0]["language_inventory"]
        == before["language_inventory"]
    )
    refreshed = output(invoke(home, "refresh-languages", "--git-root", str(root)))
    assert refreshed["status"] == "complete"
    assert refreshed["file_revision"] == 2
    after = report(home)["repositories"][0]
    assert after["row_revision"] == before["row_revision"]
    assert after["last_attempt"] == before["last_attempt"]
    assert (
        after["language_inventory"]["languages"][1]["declarations"][0]["value"]
        == "1.27"
    )
    assert (
        output(invoke(home, "record", stdin=attempt))["language_status"]
        == "not_checked"
    )

    (nested / "go.mod").unlink()
    output(invoke(home, "refresh-languages", "--git-root", str(root)))
    declarations = report(home)["repositories"][0]["language_inventory"]["languages"][
        1
    ]["declarations"]
    assert all(item["path"] != "nested/go.mod" for item in declarations)


@pytest.mark.parametrize(
    ("filename", "language"),
    (
        ("auth.py", "python"),
        ("token.ts", "typescript"),
        ("main.mts", "typescript"),
        ("main.cts", "typescript"),
    ),
)
def test_tracked_source_presence_without_declaration(
    tmp_path: Path, filename: str, language: str
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    root = repository(tmp_path / "repository", home)
    (root / filename).write_text("// source file\n")
    git("add", filename, home=home, cwd=root)

    receipt = output(invoke(home, "record", stdin=request(root, 0)))

    assert receipt["language_status"] == "observed"
    inventory = report(home)["repositories"][0]["language_inventory"]
    assert inventory["languages"] == [{"name": language, "declarations": []}]


def test_tracked_source_under_external_symlink_is_not_detected(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    root = repository(tmp_path / "repository", home)
    nested = root / "nested"
    nested.mkdir()
    (nested / "main.py").write_text("pass\n")
    git("add", "nested/main.py", home=home, cwd=root)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "main.py").write_text("pass\n")
    (nested / "main.py").unlink()
    nested.rmdir()
    nested.symlink_to(outside, target_is_directory=True)

    receipt = output(invoke(home, "record", stdin=request(root, 0)))

    assert receipt["language_status"] == "observed"
    assert report(home)["repositories"][0]["language_inventory"]["languages"] == []


def test_nonversion_declarations_do_not_block_other_languages(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    root = repository(tmp_path / "repository", home)
    (root / "package.json").write_text(
        json.dumps({"devDependencies": {"typescript": "file:../typescript"}})
    )
    (root / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.11"\n')
    (root / ".python-version").write_text("ghp_" + "A" * 40 + "\n")
    git("add", ".", home=home, cwd=root)

    receipt = output(invoke(home, "record", stdin=request(root, 0)))

    assert receipt["language_status"] == "observed"
    languages = report(home)["repositories"][0]["language_inventory"]["languages"]
    assert languages == [
        {
            "name": "python",
            "declarations": [
                {"kind": "requires-python", "path": "pyproject.toml", "value": ">=3.11"}
            ],
        },
        {"name": "typescript", "declarations": []},
    ]


def test_poetry_inline_python_version_is_recorded(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    root = repository(tmp_path / "repository", home)
    (root / "pyproject.toml").write_text(
        '[tool.poetry.dependencies]\npython = {version = "^3.11"}\n'
    )
    git("add", "pyproject.toml", home=home, cwd=root)

    receipt = output(invoke(home, "record", stdin=request(root, 0)))

    assert receipt["language_status"] == "observed"
    assert report(home)["repositories"][0]["language_inventory"]["languages"] == [
        {
            "name": "python",
            "declarations": [
                {"kind": "poetry-python", "path": "pyproject.toml", "value": "^3.11"}
            ],
        }
    ]


def test_v1_ledger_is_read_without_changes_and_migrated_on_refresh(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    root = repository(tmp_path / "repository", home)
    (root / "go.mod").write_text("module example.invalid/root\ngo 1.26\n")
    attempt = request(root, 0)
    output(invoke(home, "record", stdin=attempt))
    path = home / ".aquarium/status.yaml"
    legacy, _ = ledger(home)
    legacy["schema"] = "aquarium-production-status/v1"
    legacy.pop("language_inventory")
    raw = yaml.safe_dump(legacy, sort_keys=True).encode()
    path.write_bytes(raw)
    path.chmod(0o600)

    observed = report(home)
    assert observed["repositories"][0]["language_inventory"] is None
    assert path.read_bytes() == raw
    refreshed = output(invoke(home, "refresh-languages"))
    assert refreshed["file_revision"] == 2
    migrated, _ = ledger(home)
    assert migrated["schema"] == "aquarium-production-status/v2"
    assert migrated["repositories"] == legacy["repositories"]
    assert migrated["language_inventory"][0]["languages"][0]["name"] == "go"


def test_failed_language_refresh_preserves_previous_observation(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    root = repository(tmp_path / "repository", home)
    manifest = root / "pyproject.toml"
    manifest.write_text('[project]\nrequires-python = ">=3.11"\n')
    output(invoke(home, "record", stdin=request(root, 0)))
    old, raw = ledger(home)
    outside = tmp_path / "outside.toml"
    outside.write_text('[project]\nrequires-python = ">=3.12"\n')
    manifest.unlink()
    manifest.symlink_to(outside)

    refreshed = output(invoke(home, "refresh-languages", "--git-root", str(root)))
    assert refreshed["status"] == "partial"
    assert refreshed["changed"] is False
    assert ledger(home) == (old, raw)


def test_deep_pubspec_does_not_abort_recording_or_replace_observation(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    root = repository(tmp_path / "repository", home)
    manifest = root / "pubspec.yaml"
    manifest.write_text("environment:\n  sdk: ^3.9.2\n")
    output(invoke(home, "record", stdin=request(root, 0)))
    previous = report(home)["repositories"][0]["language_inventory"]
    manifest.write_text("environment:\n  sdk: " + "[" * 1500 + "0" + "]" * 1500)

    refresh = output(invoke(home, "refresh-languages", "--git-root", str(root)))
    assert refresh["status"] == "partial"
    assert refresh["changed"] is False
    recorded = output(invoke(home, "record", stdin=request(root, 1)))
    assert recorded["status"] == "recorded"
    assert recorded["language_status"] == "unavailable"
    assert report(home)["repositories"][0]["language_inventory"] == previous


def test_pubspec_merge_aliases_fail_without_holding_status_lock(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    root = repository(tmp_path / "repository", home)
    manifest = root / "pubspec.yaml"
    manifest.write_text("environment:\n  sdk: ^3.9.2\n")
    output(invoke(home, "record", stdin=request(root, 0)))
    previous = report(home)["repositories"][0]["language_inventory"]
    lines = ["a0: &a0 {k: 0}"]
    lines.extend(
        f"a{index}: &a{index} {{<<: [*a{index - 1}, *a{index - 1}]}}"
        for index in range(1, 26)
    )
    lines.append("environment: {<<: *a25, sdk: ^3.9.2}")
    manifest.write_text("\n".join(lines) + "\n")

    refreshed = output(
        invoke(home, "refresh-languages", "--git-root", str(root), timeout=3)
    )

    assert refreshed["status"] == "partial"
    assert refreshed["changed"] is False
    assert report(home)["repositories"][0]["language_inventory"] == previous


def test_language_presence_without_version_and_failed_record_scan(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    root = repository(tmp_path / "repository", home)
    (root / "main.rs").write_text("fn main() {}\n")
    git("add", "main.rs", home=home, cwd=root)
    first = output(invoke(home, "record", stdin=request(root, 0)))
    assert first["language_status"] == "observed"
    inventory = report(home)["repositories"][0]["language_inventory"]
    assert inventory["languages"] == [{"name": "rust", "declarations": []}]
    assert '"rust":"unknown"' in invoke(home, "show").stdout

    (root / "Cargo.toml").write_text("[package\n")
    second = output(invoke(home, "record", stdin=request(root, 1)))
    assert second["status"] == "recorded"
    assert second["language_status"] == "unavailable"
    current = report(home)["repositories"][0]
    assert current["row_revision"] == 2
    assert current["language_inventory"] == inventory


@pytest.mark.parametrize(
    "invalid", ("https://example.invalid/token", "ghp_" + "A" * 40)
)
def test_corrupt_language_declaration_is_rejected(tmp_path: Path, invalid: str) -> None:
    home = tmp_path / "home"
    home.mkdir()
    root = repository(tmp_path / "repository", home)
    (root / "go.mod").write_text("module example.invalid/root\ngo 1.26\n")
    output(invoke(home, "record", stdin=request(root, 0)))
    stored, _ = ledger(home)
    stored["language_inventory"][0]["languages"][0]["declarations"][0]["value"] = (
        invalid
    )
    path = home / ".aquarium/status.yaml"
    path.write_bytes(yaml.safe_dump(stored, sort_keys=True).encode())
    error(invoke(home, "show", "--format", "json"), 1, "state_corrupt")


def test_full_and_scoped_transitions_preserve_unsettled_state(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    root = repository(tmp_path / "repository", home)
    full_ready = request(
        root,
        0,
        components={"sanho": observation("v1.2.3")},
    )
    scoped = request(
        root,
        1,
        outcome="partial",
        scope={"kind": "scoped", "components": ["aquarium-dev"]},
        components={"aquarium_dev": observation("v2.0.0", "partial")},
    )
    full_failed = request(
        root,
        2,
        outcome="failed",
        components={"sanho": observation("v1.2.4", "failed")},
    )
    full_partial = request(root, 3, outcome="partial")
    full_declined = request(root, 4, outcome="declined")
    final_ready = request(root, 5)

    for expected, payload in enumerate(
        (
            full_ready,
            scoped,
            full_failed,
            full_partial,
            full_declined,
            final_ready,
        ),
        start=1,
    ):
        receipt = output(invoke(home, "record", stdin=payload))
        assert receipt["file_revision"] == receipt["row_revision"] == expected
        stored, _ = ledger(home)
        row = stored["repositories"][0]
        if expected < 6:
            assert row["last_full_ready"]["attempt_id"] == full_ready["attempt_id"]

    row = report(home)["repositories"][0]
    assert row["last_attempt"]["attempt_id"] == final_ready["attempt_id"]
    assert row["last_full_ready"]["attempt_id"] == final_ready["attempt_id"]
    assert row["components"]["sanho"] == {
        "attempt_id": full_failed["attempt_id"],
        **full_failed["components"]["sanho"],
    }
    assert row["components"]["aquarium_dev"] == {
        "attempt_id": scoped["attempt_id"],
        **scoped["components"]["aquarium_dev"],
    }


def test_linked_worktrees_are_distinct_rows_with_one_common_directory(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    primary = repository(tmp_path / "primary", home, commit=True)
    linked = (tmp_path / "linked").resolve()
    git(
        "worktree",
        "add",
        "-q",
        "-b",
        "linked-fixture",
        str(linked),
        home=home,
        cwd=primary,
    )

    output(invoke(home, "record", stdin=request(primary, 0, project="primary")))
    output(invoke(home, "record", stdin=request(linked, 0, project="linked")))

    rows = report(home)["repositories"]
    assert {row["git_root"] for row in rows} == {str(primary), str(linked)}
    assert len({row["git_common_dir"] for row in rows}) == 1
    assert all(row["root_state"] == "present" for row in rows)


def test_moved_and_deleted_roots_are_retained_until_exact_forget(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    original = repository(tmp_path / "original", home)
    output(invoke(home, "record", stdin=request(original, 0)))
    moved = tmp_path / "moved"
    original.rename(moved)
    moved = moved.resolve()

    first_report = report(home)
    assert first_report["repositories"][0]["root_state"] == "missing"
    output(invoke(home, "record", stdin=request(moved, 0, project="Moved")))
    second_report = report(home)
    assert [
        (row["git_root"], row["root_state"]) for row in second_report["repositories"]
    ] == [
        (str(moved), "present"),
        (str(original), "missing"),
    ]

    stored, before = ledger(home)
    old_row = next(
        row for row in stored["repositories"] if row["git_root"] == str(original)
    )
    forgotten = output(
        invoke(
            home,
            "forget",
            "--git-root",
            str(original),
            "--if-file-revision",
            str(stored["file_revision"]),
            "--if-row-revision",
            str(old_row["row_revision"]),
            "--if-row-sha256",
            canonical_digest(old_row),
        )
    )
    assert forgotten == {
        "schema": FORGET_RECEIPT_SCHEMA,
        "status": "forgotten",
        "changed": True,
        "git_root": str(original),
        "file_revision": 3,
        "previous_row_revision": 1,
    }
    assert (home / ".aquarium/status.yaml").read_bytes() != before
    assert [row["git_root"] for row in report(home)["repositories"]] == [str(moved)]

    absent_before = (home / ".aquarium/status.yaml").read_bytes()
    absent = output(invoke(home, "forget", "--git-root", str(original)))
    assert absent == {
        "schema": FORGET_RECEIPT_SCHEMA,
        "status": "absent",
        "changed": False,
        "git_root": str(original),
        "file_revision": 3,
        "previous_row_revision": None,
    }
    assert (home / ".aquarium/status.yaml").read_bytes() == absent_before


def test_reused_root_with_new_common_directory_conflicts_until_forget(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    primary = repository(tmp_path / "primary", home, commit=True)
    root = (tmp_path / "repository").resolve()
    git(
        "worktree",
        "add",
        "-q",
        "-b",
        "reuse-fixture",
        str(root),
        home=home,
        cwd=primary,
    )
    output(invoke(home, "record", stdin=request(root, 0)))
    stored, _ = ledger(home)
    row = stored["repositories"][0]
    git("worktree", "remove", "--force", str(root), home=home, cwd=primary)
    replacement = repository(root, home)

    error(
        invoke(home, "record", stdin=request(replacement, 1)),
        3,
        "git_identity_conflict",
    )
    forget_arguments = (
        "forget",
        "--git-root",
        str(root),
        "--if-file-revision",
        "1",
        "--if-row-revision",
        "1",
        "--if-row-sha256",
        canonical_digest(row),
    )
    error(invoke(home, *forget_arguments), 3, "git_identity_conflict")

    replacement.rename(tmp_path / "replacement")
    receipt = output(invoke(home, *forget_arguments))
    assert receipt["status"] == "forgotten"
    assert report(home)["repositories"] == []


@pytest.mark.parametrize("failure", ["replace", "parent_fsync"])
def test_failed_atomic_write_restores_exact_previous_ledger(
    tmp_path: Path, failure: str
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    root = repository(tmp_path / "repository", home)
    output(invoke(home, "record", stdin=request(root, 0)))
    previous = (home / ".aquarium/status.yaml").read_bytes()
    candidate = request(root, 1, project=f"failed {failure}")
    result = injected_record(home, candidate, failure)

    error(result, 1, "state_write_failed")
    assert (home / ".aquarium/status.yaml").read_bytes() == previous
    assert list((home / ".aquarium").glob(".status.*")) == []
    if failure == "parent_fsync":
        assert (home / "rollback-parent-fsynced").is_file()
    stored, _ = ledger(home)
    assert stored["file_revision"] == 1
    assert stored["repositories"][0]["project"] == "Fixture"


def test_validation_failure_does_not_call_ledger_writer(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    root = repository(tmp_path / "repository", home)
    output(invoke(home, "record", stdin=request(root, 0)))
    previous = (home / ".aquarium/status.yaml").read_bytes()
    invalid = request(root, 1)
    invalid["project"] = ""

    result = injected_record(home, invalid, "validation_writer")

    error(result, 2, "invalid_input")
    assert (home / ".aquarium/status.yaml").read_bytes() == previous
    assert not (home / "writer-called").exists()
    assert list((home / ".aquarium").glob(".status.*")) == []


def test_lock_open_failure_preserves_exact_ledger(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    root = repository(tmp_path / "repository", home)
    output(invoke(home, "record", stdin=request(root, 0)))
    previous = (home / ".aquarium/status.yaml").read_bytes()

    result = injected_record(home, request(root, 1), "lock_open")

    error(result, 1, "lock_failed")
    assert (home / ".aquarium/status.yaml").read_bytes() == previous
    assert list((home / ".aquarium").glob(".status.*")) == []


@pytest.mark.parametrize("failure", ["temp_write", "file_fsync"])
def test_pre_replacement_write_failure_rolls_back_and_removes_temporary_file(
    tmp_path: Path, failure: str
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    root = repository(tmp_path / "repository", home)
    output(invoke(home, "record", stdin=request(root, 0)))
    previous = (home / ".aquarium/status.yaml").read_bytes()

    result = injected_record(home, request(root, 1), failure)

    error(result, 1, "state_write_failed")
    assert (home / ".aquarium/status.yaml").read_bytes() == previous
    assert list((home / ".aquarium").glob(".status.*")) == []


def test_post_replacement_rollback_failure_reports_durability_failure(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    root = repository(tmp_path / "repository", home)
    output(invoke(home, "record", stdin=request(root, 0)))
    previous = (home / ".aquarium/status.yaml").read_bytes()

    result = injected_record(home, request(root, 1), "rollback")

    error(result, 1, "durability_failed")
    assert (home / "rollback-attempted").is_file()
    assert (home / ".aquarium/status.yaml").read_bytes() != previous
    stored, _ = ledger(home)
    assert stored["file_revision"] == 2
    assert list((home / ".aquarium").glob(".status.*")) == []


def test_public_streams_envelopes_and_exit_classes_are_exact(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()

    absent = report(home)
    assert set(absent) == {
        "schema",
        "status",
        "ledger",
        "reporter",
        "latest_stable",
        "source_plugin",
        "source_unreleased",
        "release_freshness",
        "repositories",
        "warnings",
    }
    assert absent["status"] == "complete"
    assert absent["ledger"] == {"state": "absent", "file_revision": None}
    assert absent["repositories"] == []
    assert not (home / ".aquarium").exists()

    invalid = error(invoke(home, "record", stdin="{}\n"), 2, "invalid_input")
    assert invalid["error"]["message"] == "record is invalid"

    state = home / ".aquarium"
    state.mkdir()
    state.chmod(0o755)
    unsafe = error(invoke(home, "show", "--format", "json"), 1, "state_unsafe")
    assert unsafe["error"]["message"].startswith("unsafe owned directory:")
