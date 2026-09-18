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
RECORD_RECEIPT_SCHEMA = "aquarium-production-status-record-receipt/v1"
REPORT_SCHEMA = "aquarium-production-status-report/v1"
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
        "attempt_id": first["attempt_id"],
        "git_root": str(root),
        "file_revision": 1,
        "row_revision": 1,
    }
    assert replayed == {**recorded, "status": "replayed", "changed": False}
    assert path.read_bytes() == original_bytes
    assert path.stat().st_mtime_ns == original_mtime

    second = request(root, 1, outcome="partial")
    output(invoke(home, "record", stdin=second))
    error(invoke(home, "record", stdin=first), 3, "revision_conflict")

    changed = {**second, "project": "changed"}
    error(invoke(home, "record", stdin=changed), 3, "attempt_conflict")


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
