"""Verify one exact Podway v0.2.6 binary against Aquarium Procedures."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

RUNTIME_SCRIPT = Path(__file__).with_name("podway_runtime_qualification.py")
RUNTIME_SPEC = importlib.util.spec_from_file_location(
    "podway_runtime_qualification", RUNTIME_SCRIPT
)
if RUNTIME_SPEC is None or RUNTIME_SPEC.loader is None:
    raise RuntimeError("cannot load Podway runtime qualification helper")
podway_runtime_qualification = importlib.util.module_from_spec(RUNTIME_SPEC)
RUNTIME_SPEC.loader.exec_module(podway_runtime_qualification)

EXPECTED_VERSION = "v0.2.6"
OUTPUT_SCHEMA = "podway.output/v3"
DIAGNOSTICS_SCHEMA = "podway.procedure-diagnostics-result/v1"
SOURCE_SCHEMA = "podway.procedure-source-result/v1"
PREVIEW_SCHEMA = "podway.procedure-preview-result/v1"
RESULT_SCHEMA = "aquarium-podway-compatibility.v2"
COMMAND_TIMEOUT_SECONDS = 30
PROCEDURE_NAMES = (
    "aquarium-design-v2.yaml",
    "aquarium-goal-v2.yaml",
    "aquarium-task-v2.yaml",
    "aquarium-validation-v2.yaml",
    "aquarium-war-room-v2.yaml",
)


class CompatibilityError(RuntimeError):
    """A bounded Podway compatibility check failed."""


def exact_binary(value: str | None) -> Path:
    if not value:
        raise CompatibilityError("PODWAY_BIN is required")
    path = Path(value)
    if not path.is_absolute():
        raise CompatibilityError("PODWAY_BIN must be an absolute path")
    if path.is_symlink() or path.resolve() != path:
        raise CompatibilityError(
            "PODWAY_BIN and its path components must not be symlinks"
        )
    if not path.is_file():
        raise CompatibilityError("PODWAY_BIN must be a regular file")
    if not os.access(path, os.X_OK):
        raise CompatibilityError("PODWAY_BIN must be executable")
    return path


def run(binary: Path, arguments: list[str], repository: Path) -> tuple[int, Any]:
    try:
        completed = subprocess.run(
            [str(binary), *arguments],
            cwd=repository,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise CompatibilityError(
            f"Podway execution failed: {type(error).__name__}"
        ) from error
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise CompatibilityError("Podway did not return one JSON value") from error
    return completed.returncode, payload


def require_version(binary: Path, repository: Path, name: str = "podway") -> None:
    exit_code, payload = run(binary, ["version", "--json"], repository)
    if exit_code != 0 or payload != {"name": name, "version": EXPECTED_VERSION}:
        raise CompatibilityError(f"{name} must report exactly {EXPECTED_VERSION}")


def procedure_result(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise CompatibilityError("Podway procedure output must be an object")
    if (
        payload.get("schema") != OUTPUT_SCHEMA
        or payload.get("command") != "procedure.check"
    ):
        raise CompatibilityError("Podway procedure output envelope is incompatible")
    result = payload.get("result")
    if not isinstance(result, dict) or result.get("schema") != DIAGNOSTICS_SCHEMA:
        raise CompatibilityError("Podway procedure diagnostics schema is incompatible")
    return result


def require_valid_procedure(binary: Path, repository: Path, procedure: Path) -> None:
    relative = procedure.relative_to(repository).as_posix()
    stages = (
        ("format", ["--check"], SOURCE_SCHEMA),
        ("validate", [], DIAGNOSTICS_SCHEMA),
        ("vet", [], DIAGNOSTICS_SCHEMA),
        ("lint", ["--warnings-as-errors"], DIAGNOSTICS_SCHEMA),
        ("check", ["--warnings-as-errors"], DIAGNOSTICS_SCHEMA),
        ("preview", [], PREVIEW_SCHEMA),
    )
    results: dict[str, dict[str, Any]] = {}
    for stage, flags, schema in stages:
        exit_code, payload = run(
            binary,
            ["--json", "procedure", stage, *flags, relative],
            repository,
        )
        if (
            exit_code != 0
            or not isinstance(payload, dict)
            or payload.get("schema") != OUTPUT_SCHEMA
            or payload.get("command") != f"procedure.{stage}"
        ):
            raise CompatibilityError(
                f"canonical Procedure failed {stage}: {procedure.name}"
            )
        result = payload.get("result")
        if not isinstance(result, dict) or result.get("schema") != schema:
            raise CompatibilityError(
                f"canonical Procedure returned an incompatible {stage} result: "
                f"{procedure.name}"
            )
        if (
            stage in {"validate", "vet", "lint", "check"}
            and result.get("valid") is not True
        ):
            raise CompatibilityError(
                f"canonical Procedure was rejected by {stage}: {procedure.name}"
            )
        results[stage] = result
    preview = results["preview"]
    digest = preview.get("procedure_digest")
    suggestion = preview.get("start_suggestion", {}).get("argv")
    if (
        preview.get("admissible") is not True
        or preview.get("procedure_id") != procedure.stem
        or not isinstance(digest, str)
        or suggestion
        != [
            "podway",
            "start",
            "--procedure",
            relative,
            "--expect-procedure-digest",
            digest,
            "--task",
            "<title>",
        ]
    ):
        raise CompatibilityError(
            f"canonical Procedure preview was not exactly digest-fenced: {procedure.name}"
        )


def require_rejected_procedure(
    binary: Path, repository: Path, procedure: Path, contract: str
) -> None:
    exit_code, payload = run(
        binary,
        ["--json", "procedure", "check", "--warnings-as-errors", str(procedure)],
        repository,
    )
    result = procedure_result(payload)
    diagnostics = result.get("diagnostics")
    if (
        exit_code == 0
        or result.get("valid") is not False
        or not isinstance(diagnostics, list)
        or not diagnostics
    ):
        raise CompatibilityError(f"Podway did not reject {contract}")


def replace_once(source: bytes, old: bytes, new: bytes, contract: str) -> bytes:
    if source.count(old) != 1:
        raise CompatibilityError(f"canonical fixture drifted for {contract}")
    return source.replace(old, new, 1)


def repository_identity(repository: Path) -> tuple[str, bool]:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository,
        capture_output=True,
        text=True,
        timeout=COMMAND_TIMEOUT_SECONDS,
        check=False,
    )
    status = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=repository,
        capture_output=True,
        text=True,
        timeout=COMMAND_TIMEOUT_SECONDS,
        check=False,
    )
    revision = head.stdout.strip()
    if head.returncode != 0 or len(revision) != 40 or status.returncode != 0:
        raise CompatibilityError("cannot bind compatibility evidence to Aquarium Git")
    return revision, not status.stdout


def verify(binary: Path, repository: Path) -> dict[str, Any]:
    aquarium_head, aquarium_worktree_clean = repository_identity(repository)
    require_version(binary, repository)
    try:
        daemon = podway_runtime_qualification.exact_sibling_daemon(binary)
        require_version(daemon, repository, "podwayd")
    except podway_runtime_qualification.RuntimeQualificationError as error:
        raise CompatibilityError(str(error)) from error
    procedures = repository / "plugins/aquarium/assets/podway/procedures"
    for name in PROCEDURE_NAMES:
        require_valid_procedure(binary, repository, procedures / name)

    goal = (procedures / "aquarium-goal-v2.yaml").read_bytes()
    negative_fixtures = {
        "max_item_length=8193": replace_once(
            goal,
            b"        max_item_length: 128\n",
            b"        max_item_length: 8193\n",
            "max_item_length",
        ),
        "max_total_length=1000001": replace_once(
            goal,
            b"        max_total_length: 1000000\n",
            b"        max_total_length: 1000001\n",
            "max_total_length",
        ),
        "unknown_top_level_field": b"unknown_field: true\n" + goal,
    }
    with tempfile.TemporaryDirectory(prefix="aquarium-podway-compat-") as directory:
        fixture_root = Path(directory)
        for index, (contract, contents) in enumerate(negative_fixtures.items()):
            fixture = fixture_root / f"negative-{index}.yaml"
            fixture.write_bytes(contents)
            require_rejected_procedure(binary, repository, fixture, contract)

    try:
        runtime = podway_runtime_qualification.qualify_runtime(
            binary, daemon, repository
        )
    except podway_runtime_qualification.RuntimeQualificationError as error:
        raise CompatibilityError(str(error)) from error

    return {
        "schema": RESULT_SCHEMA,
        "podway_version": EXPECTED_VERSION,
        "aquarium_head": aquarium_head,
        "aquarium_worktree_clean": aquarium_worktree_clean,
        "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "daemon_sha256": hashlib.sha256(daemon.read_bytes()).hexdigest(),
        "canonical_procedure_count": len(PROCEDURE_NAMES),
        "negative_declaration_contracts": list(negative_fixtures),
        **runtime,
    }


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    try:
        result = verify(exact_binary(os.environ.get("PODWAY_BIN")), repository)
    except (CompatibilityError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
