from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "plugins/aquarium/tools/aquarium-status/aquarium_status.py"
MANIFEST = ROOT / "plugins/aquarium/.codex-plugin/plugin.json"


def run_cli(
    home: Path, *arguments: str, stdin: str | None = None
) -> subprocess.CompletedProcess[str]:
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    environment.update(
        {
            "HOME": str(home),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONNOUSERSITE": "1",
        }
    )
    return subprocess.run(
        [sys.executable, "-B", str(CLI), *arguments],
        input=stdin,
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )


def run_refresh_cli(home: Path, mode: str) -> subprocess.CompletedProcess[str]:
    program = """
import os
import sys
import urllib.error

class Response:
    def __enter__(self):
        return self

    def __exit__(self, *arguments):
        return False

    def read(self, limit):
        return os.environ["RELEASE_RESPONSE"].encode()

def open_release(request, timeout):
    if os.environ["REFRESH_MODE"] == "failure":
        raise urllib.error.URLError("offline fixture")
    return Response()

sys.path.insert(0, sys.argv[1])
import aquarium_status
aquarium_status.release_version.__globals__["_open_release_request"] = open_release
raise SystemExit(aquarium_status.main(["show", "--format", "json", "--refresh"]))
"""
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    environment.update(
        {
            "HOME": str(home),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONNOUSERSITE": "1",
            "REFRESH_MODE": mode,
            "RELEASE_RESPONSE": json.dumps(
                {
                    "tag_name": (
                        f"v{json.loads(MANIFEST.read_text(encoding='utf-8'))['version']}"
                    )
                }
            ),
        }
    )
    return subprocess.run(
        [sys.executable, "-B", "-c", program, str(CLI.parent)],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )


def init_repository(path: Path, home: Path) -> Path:
    path.mkdir()
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    environment["HOME"] = str(home)
    subprocess.run(
        ["git", "init", "--quiet", str(path)],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )
    return path.resolve()


def request(
    repository: Path,
    *,
    attempt: int,
    revision: int,
    outcome: str = "ready",
    scope: dict[str, Any] | None = None,
    components: dict[str, Any] | None = None,
    project: str = "Fixture",
) -> dict[str, Any]:
    return {
        "schema": "aquarium-production-status-record/v1",
        "attempt_id": f"00000000-0000-4000-8000-{attempt:012d}",
        "expected_row_revision": revision,
        "git_root": str(repository),
        "project": project,
        "started_at": "2026-09-18T00:00:00Z",
        "completed_at": "2026-09-18T00:01:00Z",
        "outcome": outcome,
        "scope": scope or {"kind": "full"},
        "components": components or {},
    }


def json_input(value: object) -> str:
    return json.dumps(value, ensure_ascii=False) + "\n"


def exact_json_output(completed: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    payload = json.loads(completed.stdout)
    assert completed.returncode == 0
    assert completed.stderr == ""
    assert (
        completed.stdout
        == json.dumps(payload, sort_keys=True, ensure_ascii=False) + "\n"
    )
    return payload


def exact_error(
    completed: subprocess.CompletedProcess[str], exit_code: int, code: str
) -> dict[str, Any]:
    payload = json.loads(completed.stderr)
    assert completed.returncode == exit_code
    assert completed.stdout == ""
    assert (
        completed.stderr
        == json.dumps(payload, sort_keys=True, ensure_ascii=False) + "\n"
    )
    assert payload["schema"] == "aquarium-production-status-error/v1"
    assert set(payload) == {"schema", "error"}
    assert set(payload["error"]) == {"code", "message"}
    assert payload["error"]["code"] == code
    return payload


def text_report(report: dict[str, Any]) -> str:
    def render(value: object) -> str:
        return json.dumps(
            value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        )

    lines = [
        f"Status: {report['status']}",
        f"Ledger: {render(report['ledger'])}",
        f"Reporter: {render(report['reporter'])}",
        f"Latest stable: {render(report['latest_stable'])}",
        f"Source plugin: {render(report['source_plugin'])}",
        f"Source unreleased: {render(report['source_unreleased'])}",
        f"Release freshness: {report['release_freshness']}",
        f"Warnings: {render(report['warnings'])}",
    ]
    for row in report["repositories"]:
        lines.extend(
            [
                f"Repository: {render(row['git_root'])}",
                f"  Git common directory: {render(row['git_common_dir'])}",
                f"  Project: {render(row['project'])}",
                f"  Row revision: {row['row_revision']}",
                f"  Root state: {row['root_state']}",
                f"  Configuration freshness: {row['configuration_freshness']}",
                f"  Enrollment: {render(row['enrollment'])}",
                f"  Last attempt: {render(row['last_attempt'])}",
                f"  Last full ready: {render(row.get('last_full_ready'))}",
                f"  Components: {render(row['components'])}",
            ]
        )
    return "\n".join(lines) + "\n"


def stored_row(report_row: dict[str, Any]) -> dict[str, Any]:
    row = dict(report_row)
    for key in ("root_state", "configuration_freshness", "enrollment"):
        row.pop(key)
    return row


def row_digest(row: dict[str, Any]) -> str:
    canonical = (
        json.dumps(
            row,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def test_absent_show_is_exact_and_does_not_create_owned_state(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    version = f"v{json.loads(MANIFEST.read_text(encoding='utf-8'))['version']}"
    expected = {
        "schema": "aquarium-production-status-report/v1",
        "status": "complete",
        "ledger": {"state": "absent", "file_revision": None},
        "reporter": {
            "value": version,
            "source": "bundled_plugin_manifest",
            "status": "observed",
        },
        "latest_stable": {
            "value": None,
            "source": "not_requested",
            "status": "not_checked",
        },
        "source_plugin": {
            "value": None,
            "source": "not_requested",
            "status": "not_checked",
        },
        "source_unreleased": {
            "value": None,
            "source": "not_requested",
            "status": "not_checked",
        },
        "release_freshness": "not_checked",
        "repositories": [],
        "warnings": [],
    }

    json_result = run_cli(home, "show", "--format", "json")
    assert exact_json_output(json_result) == expected
    assert not (home / ".aquarium").exists()

    text_result = run_cli(home, "show")
    assert text_result.returncode == 0
    assert text_result.stderr == ""
    assert text_result.stdout == text_report(expected)
    assert not (home / ".aquarium").exists()


def test_refresh_and_exact_source_root_preserve_report_contract(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()

    refreshed = exact_json_output(run_refresh_cli(home, "success"))
    assert refreshed["status"] == "complete"
    assert refreshed["latest_stable"]["status"] == "observed"
    assert refreshed["release_freshness"] == "current"
    assert refreshed["warnings"] == []

    unavailable = exact_json_output(run_refresh_cli(home, "failure"))
    assert unavailable["status"] == "partial"
    assert unavailable["latest_stable"] == {
        "value": None,
        "source": "unavailable",
        "status": "unknown",
    }
    assert unavailable["release_freshness"] == "unknown"
    assert unavailable["warnings"] == [{"code": "release_refresh_failed"}]

    source = init_repository(tmp_path / "source", home)
    manifest = source / "plugins/aquarium/.codex-plugin/plugin.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps({"name": "aquarium", "version": "9.8.7"}) + "\n",
        encoding="utf-8",
    )
    (source / "CHANGELOG.md").write_text(
        "# Changelog\n\n## v9.9.0 - Unreleased\n",
        encoding="utf-8",
    )
    observed = exact_json_output(
        run_cli(
            home,
            "show",
            "--format",
            "json",
            "--source-root",
            str(source),
        )
    )
    assert observed["source_plugin"] == {
        "value": "v9.8.7",
        "source": "source_root_manifest",
        "status": "observed",
    }
    assert observed["source_unreleased"] == {
        "value": "v9.9.0",
        "source": "source_root_changelog",
        "status": "observed",
    }
    assert observed["warnings"] == []


def test_record_replay_show_and_exit_classes_have_exact_streams(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    repository = init_repository(tmp_path / "repository", home)
    value = request(
        repository,
        attempt=1,
        revision=0,
        project="Fixture \u001b Ω\n",
    )

    recorded = exact_json_output(run_cli(home, "record", stdin=json_input(value)))
    assert recorded == {
        "schema": "aquarium-production-status-record-receipt/v1",
        "status": "recorded",
        "changed": True,
        "attempt_id": value["attempt_id"],
        "git_root": str(repository),
        "file_revision": 1,
        "row_revision": 1,
    }
    ledger = home / ".aquarium/status.yaml"
    before = ledger.read_bytes()
    before_mtime = ledger.stat().st_mtime_ns

    replayed = exact_json_output(run_cli(home, "record", stdin=json_input(value)))
    assert replayed == {**recorded, "status": "replayed", "changed": False}
    assert ledger.read_bytes() == before
    assert ledger.stat().st_mtime_ns == before_mtime

    report = exact_json_output(run_cli(home, "show", "--format", "json"))
    assert report["ledger"] == {"state": "present", "file_revision": 1}
    assert report["repositories"][0]["project"] == "Fixture \u001b Ω\n"
    assert report["repositories"][0]["root_state"] == "present"
    text = run_cli(home, "show")
    assert text.returncode == 0
    assert text.stderr == ""
    assert text.stdout == text_report(report)
    assert "Ω" not in text.stdout
    assert "\x1b" not in text.stdout

    exact_error(run_cli(home, "record", stdin="{}\n"), 2, "invalid_input")
    stale = request(repository, attempt=2, revision=0)
    exact_error(
        run_cli(home, "record", stdin=json_input(stale)),
        3,
        "revision_conflict",
    )
    assert ledger.read_bytes() == before


def test_forget_requires_and_applies_exact_row_preconditions(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    repository = init_repository(tmp_path / "repository", home)
    value = request(repository, attempt=3, revision=0)
    exact_json_output(run_cli(home, "record", stdin=json_input(value)))
    report = exact_json_output(run_cli(home, "show", "--format", "json"))
    row = stored_row(report["repositories"][0])
    ledger = home / ".aquarium/status.yaml"
    before = ledger.read_bytes()

    exact_error(
        run_cli(home, "forget", "--git-root", str(repository)),
        2,
        "invalid_arguments",
    )
    exact_error(
        run_cli(
            home,
            "forget",
            "--git-root",
            str(repository),
            "--if-file-revision",
            "1",
            "--if-row-revision",
            "1",
            "--if-row-sha256",
            "0" * 64,
        ),
        3,
        "revision_conflict",
    )
    assert ledger.read_bytes() == before

    forgotten = exact_json_output(
        run_cli(
            home,
            "forget",
            "--git-root",
            str(repository),
            "--if-file-revision",
            "1",
            "--if-row-revision",
            "1",
            "--if-row-sha256",
            row_digest(row),
        )
    )
    assert forgotten == {
        "schema": "aquarium-production-status-forget-receipt/v1",
        "status": "forgotten",
        "changed": True,
        "git_root": str(repository),
        "file_revision": 2,
        "previous_row_revision": 1,
    }
    after = ledger.read_bytes()
    empty = exact_json_output(run_cli(home, "show", "--format", "json"))
    assert empty["ledger"] == {"state": "present", "file_revision": 2}
    assert empty["repositories"] == []

    absent = exact_json_output(run_cli(home, "forget", "--git-root", str(repository)))
    assert absent == {
        "schema": "aquarium-production-status-forget-receipt/v1",
        "status": "absent",
        "changed": False,
        "git_root": str(repository),
        "file_revision": 2,
        "previous_row_revision": None,
    }
    assert ledger.read_bytes() == after


def test_show_rejects_corrupt_and_unsafe_owned_state(tmp_path: Path) -> None:
    corrupt_home = tmp_path / "corrupt-home"
    state = corrupt_home / ".aquarium"
    state.mkdir(parents=True, mode=0o700)
    lock = state / "status.lock"
    lock.write_bytes(b"")
    lock.chmod(0o600)
    ledger = state / "status.yaml"
    ledger.write_text("not: the canonical ledger\n", encoding="utf-8")
    ledger.chmod(0o600)
    exact_error(
        run_cli(corrupt_home, "show", "--format", "json"),
        1,
        "state_corrupt",
    )

    unsafe_home = tmp_path / "unsafe-home"
    unsafe_state = unsafe_home / ".aquarium"
    unsafe_state.mkdir(parents=True, mode=0o700)
    unsafe_ledger = unsafe_state / "status.yaml"
    unsafe_ledger.write_text(
        "file_revision: 1\nrepositories: []\nschema: aquarium-production-status/v1\n",
        encoding="utf-8",
    )
    unsafe_ledger.chmod(0o600)
    exact_error(
        run_cli(unsafe_home, "show", "--format", "json"),
        1,
        "state_unsafe",
    )


def test_scoped_ready_is_promoted_only_by_later_full_ready(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    repository = init_repository(tmp_path / "repository", home)
    observed = {
        "outcome": "ready",
        "version": {
            "value": "v1.2.3",
            "source": "recorded_attempt",
            "status": "observed",
        },
    }
    scoped = request(
        repository,
        attempt=4,
        revision=0,
        scope={"kind": "scoped", "components": ["sanho"]},
        components={"sanho": observed},
    )
    exact_json_output(run_cli(home, "record", stdin=json_input(scoped)))

    scoped_report = exact_json_output(run_cli(home, "show", "--format", "json"))
    scoped_row = scoped_report["repositories"][0]
    assert "last_full_ready" not in scoped_row
    assert scoped_row["configuration_freshness"] == "unknown"
    assert scoped_row["components"]["sanho"] == {
        "attempt_id": scoped["attempt_id"],
        **observed,
    }

    full = request(repository, attempt=5, revision=1)
    receipt = exact_json_output(run_cli(home, "record", stdin=json_input(full)))
    assert receipt["file_revision"] == 2
    assert receipt["row_revision"] == 2

    promoted = exact_json_output(run_cli(home, "show", "--format", "json"))
    row = promoted["repositories"][0]
    assert row["last_attempt"] == row["last_full_ready"]
    assert row["last_full_ready"]["attempt_id"] == full["attempt_id"]
    assert row["last_full_ready"]["scope"] == {"kind": "full"}
    assert row["configuration_freshness"] == "current"
    assert row["components"] == scoped_row["components"]
