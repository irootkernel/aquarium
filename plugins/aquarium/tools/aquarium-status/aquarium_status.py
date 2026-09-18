#!/usr/bin/env python3
"""Production setup status ledger CLI."""

from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any

from status_contract import (
    ERROR_SCHEMA,
    FORGET_RECEIPT_SCHEMA,
    RECORD_RECEIPT_SCHEMA,
    REPORT_SCHEMA,
    SHA256_RE,
    ContractError,
    digest,
    safe_absent_path,
    validate_record,
)
from status_report import (
    enrollment,
    freshness,
    release_version,
    root_state,
    source_versions,
    version,
)
from status_store import locked, read_ledger, write_ledger

VERSION_OVERRIDE: tuple[str, str] | None = None


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ContractError("invalid_arguments", "invalid command arguments")


def plugin_version() -> tuple[str, str]:
    if VERSION_OVERRIDE is not None:
        return VERSION_OVERRIDE
    receipt = Path(__file__).resolve().parent / "runtime.json"
    if receipt.is_file() and not receipt.is_symlink():
        value = json.loads(receipt.read_text(encoding="utf-8"))["plugin_version"]
        if isinstance(value, str):
            return value, "installed_runtime_receipt"
    manifest = Path(__file__).resolve().parents[2] / ".codex-plugin/plugin.json"
    value = json.loads(manifest.read_text(encoding="utf-8"))["version"]
    return f"v{value}", "bundled_plugin_manifest"


def git_identity(raw: str) -> tuple[str, str]:
    try:
        requested = Path(raw)
        if not requested.is_absolute() or requested.is_symlink():
            raise OSError
        resolved = requested.resolve(strict=True)
        environment = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith("GIT_")
        }
        top = subprocess.run(
            ["git", "-C", str(resolved), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
            env=environment,
        ).stdout.strip()
        common = subprocess.run(
            ["git", "-C", str(resolved), "rev-parse", "--git-common-dir"],
            check=True,
            capture_output=True,
            text=True,
            env=environment,
        ).stdout.strip()
        top_path = Path(top).resolve(strict=True)
        common_path = Path(common)
        if not common_path.is_absolute():
            common_path = resolved / common_path
        common_path = common_path.resolve(strict=True)
        canonical_top = unicodedata.normalize("NFC", str(top_path))
        canonical_common = unicodedata.normalize("NFC", str(common_path))
        if canonical_top != unicodedata.normalize("NFC", raw):
            raise OSError
        return canonical_top, canonical_common
    except (OSError, subprocess.SubprocessError) as error:
        raise ContractError(
            "invalid_git_root", "git_root is not one canonical Git worktree"
        ) from error


def load_stdin() -> Any:
    try:
        decoder = json.JSONDecoder()
        text = sys.stdin.read()
        value, end = decoder.raw_decode(text)
        if text[end:].strip():
            raise ValueError
        return value
    except (UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise ContractError(
            "invalid_input", "standard input must contain exactly one JSON document"
        ) from error


def retained_attempts(row: dict[str, Any]) -> list[dict[str, Any]]:
    attempts = [row.get("last_attempt"), row.get("last_full_ready")]
    attempts.extend(row.get("components", {}).values())
    return [item for item in attempts if isinstance(item, dict)]


def record() -> dict[str, Any]:
    raw = load_stdin()
    if not isinstance(raw, dict) or not isinstance(raw.get("git_root"), str):
        raise ContractError("invalid_input", "record is invalid")
    with locked(True):
        root, common = git_identity(raw["git_root"])
        request = validate_record(raw, root)
        request_digest = digest(request)
        ledger, previous = read_ledger()
        rows = ledger["repositories"]
        row = next((item for item in rows if item["git_root"] == root), None)
        if (
            row is not None
            and row.get("last_attempt", {}).get("attempt_id") == request["attempt_id"]
        ):
            if row["git_common_dir"] != common:
                raise ContractError(
                    "git_identity_conflict", "recorded Git identity changed", 3
                )
            attempt = row["last_attempt"]
            if attempt.get("input_sha256") != request_digest:
                raise ContractError("attempt_conflict", "attempt_id payload changed", 3)
            return {
                "schema": RECORD_RECEIPT_SCHEMA,
                "status": "replayed",
                "changed": False,
                "attempt_id": request["attempt_id"],
                "git_root": root,
                "file_revision": attempt["recorded_file_revision"],
                "row_revision": attempt["recorded_row_revision"],
            }
        for other in rows:
            for retained in retained_attempts(other):
                if retained.get("attempt_id") == request["attempt_id"]:
                    raise ContractError(
                        "attempt_conflict", "attempt_id is already retained", 3
                    )
        current_revision = 0 if row is None else row["row_revision"]
        if request["expected_row_revision"] != current_revision:
            raise ContractError("revision_conflict", "row revision changed", 3)
        if row is not None and row["git_common_dir"] != common:
            raise ContractError(
                "git_identity_conflict", "recorded Git identity changed", 3
            )
        new_file_revision = (
            1 if ledger["file_revision"] == 0 else ledger["file_revision"] + 1
        )
        new_row_revision = 1 if row is None else row["row_revision"] + 1
        attempt = {
            "attempt_id": request["attempt_id"],
            "input_sha256": request_digest,
            "expected_row_revision": request["expected_row_revision"],
            "aquarium_version": version(*plugin_version()),
            "started_at": request["started_at"],
            "completed_at": request["completed_at"],
            "outcome": request["outcome"],
            "scope": request["scope"],
            "recorded_file_revision": new_file_revision,
            "recorded_row_revision": new_row_revision,
        }
        updated = (
            copy.deepcopy(row)
            if row is not None
            else {
                "git_root": root,
                "git_common_dir": common,
                "project": request["project"],
                "components": {},
            }
        )
        updated.update(
            {
                "project": request["project"],
                "row_revision": new_row_revision,
                "last_attempt": attempt,
            }
        )
        for name, observation in request["components"].items():
            updated["components"][name] = {
                "attempt_id": request["attempt_id"],
                **observation,
            }
        if request["scope"]["kind"] == "full" and request["outcome"] == "ready":
            updated["last_full_ready"] = copy.deepcopy(attempt)
        if row is None:
            rows.append(updated)
        else:
            rows[rows.index(row)] = updated
        rows.sort(key=lambda item: item["git_root"].encode("utf-8"))
        ledger["file_revision"] = new_file_revision
        write_ledger(ledger, previous)
        return {
            "schema": RECORD_RECEIPT_SCHEMA,
            "status": "recorded",
            "changed": True,
            "attempt_id": request["attempt_id"],
            "git_root": root,
            "file_revision": new_file_revision,
            "row_revision": new_row_revision,
        }


def reporter_version() -> dict[str, Any]:
    receipt = Path(__file__).resolve().parent / "runtime.json"
    try:
        value = json.loads(receipt.read_text(encoding="utf-8"))["plugin_version"]
        return version(value, "installed_runtime_receipt")
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        return version(*plugin_version())


def show(refresh: bool, source_root: str | None) -> dict[str, Any]:
    with locked(False):
        ledger, _ = read_ledger()
        report_version = reporter_version()
        latest, release_warning = release_version(refresh)
        source_plugin, source_unreleased, source_warning = source_versions(source_root)
        warnings = {item for item in (release_warning, source_warning) if item}
        repositories = []
        for stored in ledger["repositories"]:
            row = copy.deepcopy(stored)
            row["root_state"] = root_state(stored)
            row["configuration_freshness"] = freshness(
                stored.get("last_full_ready", {}).get(
                    "aquarium_version", version(None, "unavailable", "unknown")
                ),
                report_version,
            )
            row["enrollment"], warning = enrollment(stored)
            if warning:
                warnings.add(warning)
            repositories.append(row)
        return {
            "schema": REPORT_SCHEMA,
            "status": "partial" if warnings else "complete",
            "ledger": {
                "state": "present" if ledger["file_revision"] else "absent",
                "file_revision": ledger["file_revision"] or None,
            },
            "reporter": report_version,
            "latest_stable": latest,
            "source_plugin": source_plugin,
            "source_unreleased": source_unreleased,
            "release_freshness": freshness(report_version, latest),
            "repositories": repositories,
            "warnings": [{"code": code} for code in sorted(warnings)],
        }


def forget(
    root_value: str,
    file_revision: int | None,
    row_revision: int | None,
    row_sha256: str | None,
) -> dict[str, Any]:
    with locked(True):
        supplied = (file_revision, row_revision, row_sha256)
        if any(value is not None for value in supplied) and not all(
            value is not None for value in supplied
        ):
            raise ContractError(
                "invalid_arguments", "all deletion preconditions are required"
            )
        if any(
            value is not None and (type(value) is not int or value < 1)
            for value in (file_revision, row_revision)
        ):
            raise ContractError(
                "invalid_arguments", "deletion revisions must be positive integers"
            )
        if row_sha256 is not None and (
            not isinstance(row_sha256, str) or SHA256_RE.fullmatch(row_sha256) is None
        ):
            raise ContractError("invalid_arguments", "row digest is invalid")
        requested = Path(root_value)
        if requested.exists() or requested.is_symlink():
            root, common = git_identity(root_value)
        else:
            root = safe_absent_path(root_value)
            common = None
        ledger, previous = read_ledger()
        row = next(
            (item for item in ledger["repositories"] if item["git_root"] == root), None
        )
        if row is None:
            return {
                "schema": FORGET_RECEIPT_SCHEMA,
                "status": "absent",
                "changed": False,
                "git_root": root,
                "file_revision": ledger["file_revision"] or None,
                "previous_row_revision": None,
            }
        if file_revision is None or row_revision is None or row_sha256 is None:
            raise ContractError(
                "invalid_arguments", "all deletion preconditions are required"
            )
        if common is not None and common != row["git_common_dir"]:
            raise ContractError(
                "git_identity_conflict", "recorded Git identity changed", 3
            )
        if (
            file_revision != ledger["file_revision"]
            or row_revision != row["row_revision"]
            or row_sha256 != digest(row)
        ):
            raise ContractError("revision_conflict", "deletion precondition changed", 3)
        old_revision = row["row_revision"]
        ledger["repositories"].remove(row)
        ledger["file_revision"] += 1
        write_ledger(ledger, previous)
        return {
            "schema": FORGET_RECEIPT_SCHEMA,
            "status": "forgotten",
            "changed": True,
            "git_root": root,
            "file_revision": ledger["file_revision"],
            "previous_row_revision": old_revision,
        }


def text_report(report: dict[str, Any]) -> str:
    render = lambda value: json.dumps(
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


def parser() -> argparse.ArgumentParser:
    result = JsonArgumentParser(prog="aquarium-status")
    commands = result.add_subparsers(
        dest="command", required=True, parser_class=JsonArgumentParser
    )
    show_parser = commands.add_parser("show")
    show_parser.add_argument("--format", choices=("text", "json"), default="text")
    show_parser.add_argument("--refresh", action="store_true")
    show_parser.add_argument("--source-root")
    commands.add_parser("record")
    forget_parser = commands.add_parser("forget")
    forget_parser.add_argument("--git-root", required=True)
    forget_parser.add_argument("--if-file-revision", type=int)
    forget_parser.add_argument("--if-row-revision", type=int)
    forget_parser.add_argument("--if-row-sha256")
    return result


def main(argv: list[str] | None = None) -> int:
    try:
        arguments = parser().parse_args(argv)
        if arguments.command == "record":
            output = record()
            text = json.dumps(output, sort_keys=True, ensure_ascii=False) + "\n"
        elif arguments.command == "forget":
            output = forget(
                arguments.git_root,
                arguments.if_file_revision,
                arguments.if_row_revision,
                arguments.if_row_sha256,
            )
            text = json.dumps(output, sort_keys=True, ensure_ascii=False) + "\n"
        else:
            output = show(arguments.refresh, arguments.source_root)
            text = (
                text_report(output)
                if arguments.format == "text"
                else json.dumps(output, sort_keys=True, ensure_ascii=False) + "\n"
            )
        sys.stdout.write(text)
        return 0
    except ContractError as error:
        payload = {
            "schema": ERROR_SCHEMA,
            "error": {"code": error.code, "message": str(error)},
        }
        sys.stderr.write(json.dumps(payload, sort_keys=True, ensure_ascii=False) + "\n")
        return error.exit_code
    except Exception:  # noqa: BLE001 - keep the public error boundary JSON-only
        payload = {
            "schema": ERROR_SCHEMA,
            "error": {
                "code": "state_unreadable",
                "message": "aquarium-status failed safely",
            },
        }
        sys.stderr.write(json.dumps(payload, sort_keys=True) + "\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
