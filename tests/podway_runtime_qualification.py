"""Exercise official Podway binaries in disposable release-qualification runtimes."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import signal
import socket
import struct
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Self

OUTPUT_SCHEMA = "podway.output/v3"
ERROR_SCHEMA = "podway.error/v1"
OBSERVATION_SCHEMA = "podway.observation-result/v3"
RUNTIME_SCHEMA = "podway.managed-runtime/v3"
RUNTIME_MODE = "release-qa"
COMMAND_TIMEOUT_SECONDS = 20
READINESS_TIMEOUT_SECONDS = 20
PROCESS_EXIT_TIMEOUT_SECONDS = 10
RUN_TIMEOUT_SECONDS = 240
REPEAT_COUNT = 2
CONTRACT_MANIFEST_DIGEST = (
    "sha256:bff8af8f57f1390446333cc56775ca71209e99bd3ff6fd556c39906b77a90635"
)

SUCCESS_OPTIONS = {
    "approve-closeout": "approved",
    "approve-stopped-closeout": "approved",
    "approve-diff": "approved",
    "classify-scope": "task",
    "decide-cause": "established",
    "decide-evidence": "clean",
    "decide-goal-rework-authority": "remediation",
    "decide-low-handling": "settle",
    "decide-low-completion": "completed",
    "decide-low-result": "passed",
    "decide-operational-evidence": "passed",
    "decide-review-basis": "native-review",
    "decide-final-review": "validated",
    "confirm-final-review-route-binding": "bound",
    "decide-final-review-operation": "assessed",
    "confirm-final-assessment-ordinal": "admitted",
    "confirm-assessed-final-review-provenance": "valid",
    "confirm-unassessed-final-review-provenance": "valid",
    "determine-final-backend-applicability": "required",
    "confirm-final-route-settlement": "change-safe",
    "choose-current-route-direction": "resume-current",
    "choose-settled-route-direction": "recover",
    "decide-final-backend-check": "passed",
    "decide-final-review-readiness": "passed",
    "confirm-final-review-findings": "resolved",
    "confirm-completion-assessment": "complete",
    "confirm-review-completion": "complete",
    "decide-required-evidence": "complete",
    "decide-current-blockers": "clear",
    "decide-validation-rework-authority": "remediation",
    "decide-gaps": "clean",
    "decide-quality": "passed",
    "decide-review": "clean",
    "validate-review-route-entry": "planned",
    "authorize-planned-review-route": "planned-mulgae",
    "enter-mulgae-review-route": "start",
    "enter-orca-review-route": "start",
    "enter-native-codex-review-route": "start",
    "enter-waived-review-route": "start",
    "confirm-goal-assessment-core": "ready",
    "confirm-stopped-goal-assessment-core": "ready",
    "confirm-stopped-goal-boundary": "confirmed",
    "confirm-review-route-binding": "mulgae",
    "decide-mulgae-review-operation": "assessed",
    "decide-orca-review-operation": "assessed",
    "decide-native-codex-review-operation": "assessed",
    "confirm-assessment-ordinal": "standard",
    "confirm-first-review-evidence": "mulgae",
    "confirm-extra-review-evidence": "mulgae",
    "confirm-mulgae-provenance": "delegated",
    "confirm-static-delegated-provenance": "delegated",
    "confirm-waived-provenance": "waived",
    "confirm-incomplete-mulgae-provenance": "delegated",
    "confirm-incomplete-static-delegated-provenance": "delegated",
    "decide-planned-mulgae-review-operation": "completed",
    "decide-planned-orca-review-operation": "completed",
    "decide-planned-native-codex-review-operation": "completed",
    "decide-planned-waiver-review-operation": "waived",
    "decide-changed-mulgae-review-operation": "completed",
    "decide-changed-orca-review-operation": "completed",
    "decide-changed-native-codex-review-operation": "completed",
    "decide-changed-waiver-review-operation": "waived",
    "confirm-completed-assessment-ordinal": "first",
    "confirm-waived-assessment-ordinal": "first",
    "confirm-extra-assessment-ordinal": "authorized-extra",
    "confirm-first-route-evidence": "mulgae-pass",
    "confirm-second-route-evidence": "mulgae-pass",
    "confirm-extra-route-evidence": "mulgae-pass",
    "confirm-hardening-review-eligibility": "eligible",
    "confirm-hardening-record": "recorded",
    "decide-backend-check": "non-failing",
    "decide-task-rework-authority": "remediation",
    "decide-implementation-owner": "clear",
    "decide-verification-owner": "clear",
    "decide-documentation-owner": "clear",
    "decide-verification": "passed",
    "confirm-review-findings": "resolved",
    "confirm-waived-review-findings": "resolved",
    "confirm-mulgae-pass-finding-validity": "resolved",
    "confirm-mulgae-fail-finding-validity": "resolved",
    "confirm-orca-finding-validity": "resolved",
    "confirm-native-codex-finding-validity": "resolved",
    "confirm-waived-finding-validity": "resolved",
    "assess-goal": "achieved",
    "assess-stopped-goal": "not-achieved",
}

TASK_OWNER_SCENARIOS = {
    "task-completion-implementation-owner": "implementation-rework-obligations",
    "task-completion-verification-owner": "verification-rework-obligations",
    "task-completion-documentation-owner": "documentation-rework-obligations",
}

COMPLETION_GAP_SCENARIOS = {
    "goal-completion-unmet": ("aquarium-goal-v2", "unmet"),
    "goal-completion-unverified": ("aquarium-goal-v2", "unverified"),
    "validation-completion-unmet": ("aquarium-validation-v2", "unmet"),
    "validation-completion-unverified": ("aquarium-validation-v2", "unverified"),
}

STOP_EVIDENCE_SCENARIOS = {
    "task-stop-preserves-completion": ("aquarium-task-v2", "review"),
    "goal-stop-preserves-completion": ("aquarium-goal-v2", "record-evidence"),
    "validation-stop-preserves-completion": (
        "aquarium-validation-v2",
        "final-review",
    ),
}
TASK_CONFIRMATION_SCENARIOS = {
    "task-confirmation-only-wait",
    "task-stop-preserves-completion",
}
GOAL_CLOSEOUT_GAP_SCENARIOS = {
    "goal-closeout-unmet-wait",
    "goal-stop-preserves-completion",
}
VALIDATION_CONFIRMATION_SCENARIOS = {
    "validation-medium-wait",
    "validation-stop-preserves-completion",
}


def completed_low_settlement_destination(procedure_id: str) -> str:
    return "confirm-goal-assessment-core"


GOAL_OPERATIONAL_VARIANTS = (
    ("verification-fail-review-pass", "fail", "pass", "verification-incomplete"),
    (
        "verification-inconclusive-review-pass",
        "inconclusive",
        "pass",
        "verification-incomplete",
    ),
    ("verification-pass-review-fail", "pass", "fail", "review-incomplete"),
    (
        "verification-pass-review-inconclusive",
        "pass",
        "inconclusive",
        "review-incomplete",
    ),
    ("verification-pass-review-pass", "pass", "pass", "passed"),
)

VALIDATION_FINAL_REVIEW_SCENARIOS = {
    "validation-review-fail": ("fail", None, "review-operation-incomplete"),
    "validation-review-inconclusive": (
        "inconclusive",
        None,
        "review-operation-incomplete",
    ),
    "validation-review-pass-gaps-1": ("pass", 1, "incomplete"),
    "validation-review-pass-gaps-0": ("pass", 0, "validated"),
}

LOW_BLOCKER_SCENARIOS = {
    "low-blocker-wait": {
        "source_kind": "review",
        "source_id": "fixture:review:goal:01",
        "frozen_low_ids": ["fixture:goal:low:01", "fixture:goal:low:02"],
        "blocker": {
            "id": "fixture:blocker:goal:01",
            "description": (
                "The goal fixture-owned acceptance invariant remains unsatisfied."
            ),
            "affected_scope": "fixture/goal-owned-component",
        },
    },
    "validation-low-blocker-wait": {
        "source_kind": "audit",
        "source_id": "audit:A1",
        "frozen_low_ids": ["audit:A1:L1", "audit:A1:L2"],
        "blocker": {
            "id": "fixture:blocker:validation:01",
            "description": (
                "The validation fixture-owned acceptance invariant remains unsatisfied."
            ),
            "affected_scope": "fixture/validation-owned-component",
        },
    },
}

GOAL_KIND_SCENARIOS = {
    "goal-kind-member-closeout": ("member-task", "validated-closeout"),
    "goal-kind-prevalidation-closeout": (
        "pre-validation-remediation",
        "validated-closeout",
    ),
    "goal-kind-epic-closeout": ("epic-closeout", "validated-closeout"),
    "goal-kind-member-native": ("member-task", "native-review"),
}

ROUTE_QUALIFICATION_SCENARIOS = {
    f"{procedure_id.removeprefix('aquarium-').removesuffix('-v2')}-route-{route}": (
        procedure_id,
        route,
    )
    for procedure_id in (
        "aquarium-task-v2",
        "aquarium-goal-v2",
        "aquarium-validation-v2",
    )
    for route in ("mulgae", "orca", "native-codex", "waived")
}

GOAL_RECOVERY_SCENARIOS = {
    "goal-resume-changed-orca-after-incomplete",
}

VALIDATION_RECOVERY_SCENARIOS = {
    "validation-resume-changed-orca-after-incomplete",
}

TASK_RESUME_SCENARIOS = {
    "task-resume-active-mulgae": {
        "route": "mulgae",
        "operation": "failed",
        "prior_state": "active-or-unknown",
        "readiness": "current-route-only",
        "direction": "resume-current",
    },
    "task-current-only-switch-rejected": {
        "route": "mulgae",
        "operation": "failed",
        "prior_state": "active-or-unknown",
        "readiness": "current-route-only",
        "direction": "switch-route",
    },
    "task-current-only-waive-rejected": {
        "route": "mulgae",
        "operation": "failed",
        "prior_state": "active-or-unknown",
        "readiness": "current-route-only",
        "direction": "waive",
    },
    "task-resume-terminal-orca": {
        "route": "orca",
        "operation": "incomplete",
        "prior_state": "terminal-incomplete-or-failed",
        "readiness": "safe-to-change",
        "direction": "resume-current",
    },
    "task-switch-with-waiver-basis-rejected": {
        "route": "mulgae",
        "effective_route": "waived",
        "operation": "failed",
        "prior_state": "terminal-incomplete-or-failed",
        "readiness": "safe-to-change",
        "direction": "switch-route",
        "checkpoint_basis": "explicit-waiver",
        "rejection_node": "validate-review-route-entry",
        "rejection_option": "changed",
    },
    "task-waive-with-route-change-basis-rejected": {
        "route": "mulgae",
        "effective_route": "orca",
        "operation": "failed",
        "prior_state": "terminal-incomplete-or-failed",
        "readiness": "safe-to-change",
        "direction": "waive",
        "checkpoint_basis": "explicit-route-change",
        "rejection_node": "validate-review-route-entry",
        "rejection_option": "changed",
    },
    "task-resume-with-explicit-change-rejected": {
        "route": "mulgae",
        "operation": "failed",
        "prior_state": "terminal-incomplete-or-failed",
        "readiness": "safe-to-change",
        "direction": "resume-current",
        "checkpoint_basis": "explicit-route-change",
        "rejection_node": "validate-review-route-entry",
        "rejection_option": "resumed",
    },
    "task-planned-with-direction-rejected": {
        "route": "orca",
        "operation": "failed",
        "prior_state": "not-applicable",
        "readiness": "not-applicable",
        "direction": "switch-route",
        "planned_only": True,
        "rejection_node": "authorize-planned-review-route",
        "rejection_option": "planned-orca",
    },
    "task-completed-switch-orca": {
        "route": "mulgae",
        "effective_route": "orca",
        "operation": "complete",
        "prior_operation": "completed",
        "prior_state": "terminal-complete",
        "readiness": "completed-checkpoint",
        "direction": "switch-route",
        "checkpoint_basis": "explicit-route-change",
        "completed_transition": True,
    },
    "task-completed-waiver": {
        "route": "mulgae",
        "effective_route": "waived",
        "operation": "complete",
        "prior_operation": "completed",
        "prior_state": "terminal-complete",
        "readiness": "completed-checkpoint",
        "direction": "waive",
        "checkpoint_basis": "explicit-waiver",
        "completed_transition": True,
    },
    "task-completed-switch-with-waiver-basis-rejected": {
        "route": "mulgae",
        "effective_route": "waived",
        "operation": "complete",
        "prior_operation": "completed",
        "prior_state": "terminal-complete",
        "readiness": "completed-checkpoint",
        "direction": "switch-route",
        "checkpoint_basis": "explicit-waiver",
        "completed_transition": True,
        "rejection_node": "validate-review-route-entry",
        "rejection_option": "changed",
    },
    "task-completed-waive-with-route-change-basis-rejected": {
        "route": "mulgae",
        "effective_route": "orca",
        "operation": "complete",
        "prior_operation": "completed",
        "prior_state": "terminal-complete",
        "readiness": "completed-checkpoint",
        "direction": "waive",
        "checkpoint_basis": "explicit-route-change",
        "completed_transition": True,
        "rejection_node": "validate-review-route-entry",
        "rejection_option": "changed",
    },
}

TASK_DIRECTION_MISMATCH_SCENARIOS = {
    scenario
    for scenario, configuration in TASK_RESUME_SCENARIOS.items()
    if "rejection_node" in configuration
}

TASK_COMPLETED_CHANGE_SCENARIOS = {
    scenario
    for scenario, configuration in TASK_RESUME_SCENARIOS.items()
    if configuration.get("completed_transition")
}

TASK_COMPLETED_CHANGE_SUCCESS_SCENARIOS = (
    TASK_COMPLETED_CHANGE_SCENARIOS - TASK_DIRECTION_MISMATCH_SCENARIOS
)


def route_qualification_provenance(route: str) -> str:
    return {
        "mulgae": "mulgae-reviewer:official-runtime",
        "orca": "orca-reviewer:official-runtime",
        "native-codex": "host-delegation:official-runtime",
        "waived": "coordinator-waiver",
    }[route]


def route_qualification_evidence_reference(route: str, scenario: str) -> str:
    kind = {
        "mulgae": "mulgae-root",
        "orca": "orca-lifecycle",
        "native-codex": "host-delegation",
        "waived": "coordinator-waiver",
    }[route]
    return f"{kind}:official-runtime:{scenario}"


EXPECTED_NATIVE_CASE_VARIANTS = {
    "C-01": {"audit-2-provider-0"},
    "C-02": {"audit-2-provider-1"},
    "C-03": {
        "aquarium-goal-v2",
        "aquarium-task-v2",
        "aquarium-validation-v2",
    },
    "C-04": {
        "verification-fail-review-pass",
        "verification-inconclusive-review-pass",
        "verification-pass-review-pass",
    },
    "C-05": {
        "verification-pass-review-fail",
        "verification-pass-review-inconclusive",
        "verification-pass-review-pass",
    },
    "C-06": {
        "aquarium-goal-v2",
        "aquarium-task-v2",
        "aquarium-validation-v2",
    },
    "C-07": {
        "aquarium-goal-v2",
        "aquarium-task-v2",
        "aquarium-validation-v2",
    },
    "C-08": {"goal-low-blocker-wait", "validation-low-blocker-wait"},
    "C-09": set(GOAL_KIND_SCENARIOS),
    "C-10": {
        "goal-closeout-unmet-wait",
        "goal-medium-wait",
        "goal-stop-preserves-completion",
        "task-confirmation-only-wait",
        "task-stop-preserves-completion",
        "validation-medium-wait",
        "validation-stop-preserves-completion",
    },
    "C-16": set(VALIDATION_FINAL_REVIEW_SCENARIOS),
}

CASE_ASSERTIONS = {
    "C-01": [
        "validated guard rejected pending audit Low obligations",
        "domain state unchanged after rejection",
        "audit-only settlement reached goal assessment",
    ],
    "C-02": [
        "audit and provider namespaces survived consolidation",
        "all source identities received fixture dispositions",
        "completed settlement preserved historical source counts",
    ],
    "C-03": ["completed Low settlement bypassed review and audit nodes"],
    "C-04": ["zero-finding verification failures rejected operational success"],
    "C-05": ["zero-finding review-readiness failures rejected operational success"],
    "C-06": ["failed Low verification rejected the passing route"],
    "C-07": ["pending Low dispositions rejected completion"],
    "C-08": [
        "exact current settlement source and blocker content was readable at the wait action",
        "current settlement blocker routed to an unset user choice",
    ],
    "C-09": ["goal kind independently constrained the closeout substitute"],
    "C-10": [
        "rework evidence routed to an unset user choice",
        "goal authority guards rejected the opposite remediation mode",
        "each exercised user decision authorized only one correction pass",
        "user stop preserved completion evidence and direction through goal assessment",
        "stopped work produced a not-achieved goal outcome",
    ],
    "C-16": [
        "validation final-review outcomes and evidence gaps selected distinct routes",
        "guard rejection preserved domain state",
    ],
}


class RuntimeQualificationError(RuntimeError):
    """One bounded external-artifact runtime assertion failed."""


class ExpectedCleanupProbe(RuntimeError):
    """Deliberately unwind one managed runtime to prove failure cleanup."""


def low_blocker_fixture(scenario: str, target: str) -> dict[str, Any]:
    try:
        definition = LOW_BLOCKER_SCENARIOS[scenario]
    except KeyError as error:
        raise RuntimeQualificationError(
            f"unsupported Low blocker fixture scenario: {scenario!r}"
        ) from error
    source_id = definition["source_id"]
    frozen_low_ids = list(definition["frozen_low_ids"])
    return {
        "source_basis": {
            "source_kind": definition["source_kind"],
            "source_id": source_id,
            "frozen_low_ids": frozen_low_ids,
            "target": target,
        },
        "disposition_summary": {
            "source_id": source_id,
            "dispositions": [
                {"id": identity, "disposition": "fixture-recorded"}
                for identity in frozen_low_ids
            ],
            "new_blocker": {
                **definition["blocker"],
                "source_id": source_id,
            },
        },
    }


def decoded_fixture_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, str):
        raise RuntimeQualificationError(f"{label} was not text")
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError as error:
        raise RuntimeQualificationError(
            f"{label} was not valid fixture JSON"
        ) from error
    if not isinstance(decoded, dict):
        raise RuntimeQualificationError(f"{label} was not a fixture object")
    return decoded


def assert_low_blocker_readback(
    expected: dict[str, Any],
    source_basis: Any,
    disposition_summary: Any,
    blockers: Any,
    after_target: Any,
) -> None:
    if (
        decoded_fixture_object(source_basis, "Low blocker source basis")
        != expected["source_basis"]
        or decoded_fixture_object(
            disposition_summary, "Low blocker disposition summary"
        )
        != expected["disposition_summary"]
        or type(blockers) is not int
        or blockers != 1
        or not isinstance(after_target, str)
        or after_target != expected["source_basis"]["target"]
    ):
        raise RuntimeQualificationError(
            "Low blocker wait did not preserve its exact settlement evidence"
        )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def exact_sibling_daemon(binary: Path) -> Path:
    daemon = binary.with_name("podwayd")
    if daemon.is_symlink() or daemon.resolve() != daemon:
        raise RuntimeQualificationError(
            "the sibling podwayd and its path components must not be symlinks"
        )
    if not daemon.is_file() or not os.access(daemon, os.X_OK):
        raise RuntimeQualificationError(
            "PODWAY_BIN must have an executable sibling podwayd"
        )
    return daemon


def bounded_process(
    arguments: list[str],
    *,
    cwd: Path,
    environment: dict[str, str] | None = None,
    stdin: bytes | None = None,
    timeout_seconds: float = COMMAND_TIMEOUT_SECONDS,
    expected_exit: int | None = 0,
) -> subprocess.CompletedProcess[bytes]:
    try:
        completed = subprocess.run(
            arguments,
            cwd=cwd,
            env=environment,
            input=stdin,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeQualificationError(
            f"command failed before completion: {Path(arguments[0]).name}: "
            f"{type(error).__name__}"
        ) from error
    if expected_exit is not None and completed.returncode != expected_exit:
        stdout = completed.stdout.decode("utf-8", errors="replace")[:1000]
        stderr = completed.stderr.decode("utf-8", errors="replace")[:1000]
        raise RuntimeQualificationError(
            f"command exited {completed.returncode}, expected {expected_exit}: "
            f"{Path(arguments[0]).name}; stdout={stdout!r}; stderr={stderr!r}"
        )
    return completed


def json_payload(completed: subprocess.CompletedProcess[bytes]) -> dict[str, Any]:
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        stdout = completed.stdout.decode("utf-8", errors="replace")[:1000]
        stderr = completed.stderr.decode("utf-8", errors="replace")[:1000]
        raise RuntimeQualificationError(
            "Podway did not return one JSON value: "
            f"stdout={stdout!r}; stderr={stderr!r}"
        ) from error
    if not isinstance(payload, dict):
        raise RuntimeQualificationError("Podway JSON output must be an object")
    return payload


def output_result(
    completed: subprocess.CompletedProcess[bytes],
    command: str,
    result_schema: str,
) -> dict[str, Any]:
    payload = json_payload(completed)
    result = payload.get("result")
    if (
        payload.get("schema") != OUTPUT_SCHEMA
        or payload.get("command") != command
        or not isinstance(result, dict)
        or result.get("schema") != result_schema
    ):
        raise RuntimeQualificationError(
            f"unexpected {command} result envelope or schema: "
            f"command={payload.get('command')!r}; "
            f"result_schema={result.get('schema') if isinstance(result, dict) else None!r}"
        )
    return result


def error_code(completed: subprocess.CompletedProcess[bytes]) -> str:
    payload = json_payload(completed)
    code = payload.get("code")
    if payload.get("schema") != ERROR_SCHEMA or not isinstance(code, str):
        raise RuntimeQualificationError("Podway failure did not use podway.error/v1")
    return code


def workspace_removal_result(
    completed: subprocess.CompletedProcess[bytes],
    worktree_root: str,
    workspace_uuid: str | None,
) -> dict[str, Any]:
    result = output_result(
        completed, "workspace.remove", "podway.workspace-removal-result/v1"
    )
    if result != {
        "schema": "podway.workspace-removal-result/v1",
        "worktree_root": worktree_root,
        "workspace_uuid": workspace_uuid,
        "registry_entry_removed": workspace_uuid is not None,
        "podway_directory_removed": workspace_uuid is not None,
        "already_absent": workspace_uuid is None,
    } or any(
        type(result.get(field)) is not bool
        for field in (
            "registry_entry_removed",
            "podway_directory_removed",
            "already_absent",
        )
    ):
        raise RuntimeQualificationError(
            "workspace removal did not return the exact expected result"
        )
    return result


def private_directory(path: Path) -> None:
    path.mkdir(mode=0o700)
    path.chmod(0o700)


def receive_exact(client: socket.socket, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        chunk = client.recv(remaining)
        if not chunk:
            raise RuntimeQualificationError(
                "daemon closed an incomplete response frame"
            )
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


class ManagedRuntime:
    """Own one exact official CLI/daemon pair and its disposable state."""

    def __init__(self, binary: Path, daemon: Path, procedures: Path, run_index: int):
        self.binary = binary
        self.daemon = daemon
        self.procedures = procedures
        self.run_index = run_index
        self.root: Path | None = None
        self.account: Path | None = None
        self.dev_home: Path | None = None
        self.sandbox: Path | None = None
        self.snapshot_binary: Path | None = None
        self.snapshot_daemon: Path | None = None
        self.environment: dict[str, str] | None = None
        self.process: subprocess.Popen[bytes] | None = None
        self.daemon_pid: int | None = None
        self.log = None
        self.deadline: float | None = None
        self.command_sequence = 0
        self.old_page_token: str | None = None
        self.task_verification_reworked = False
        self.task_review_reworked = False
        self.task_medium_reworked = False
        self.task_review_guard_failure = False
        self.task_evidence_reworked = False
        self.task_guard_failure = False
        self.task_required_failure = False
        self.task_list_limit = False
        self.task_stale_token = False
        self.task_snapshot_immutable = False
        self.low_settlement_procedures: set[str] = set()
        self.low_settlement_rounds: dict[str, int] = {}
        self.node_visits: dict[str, int] = {}
        self.goal_evidence_round = 0
        self.validation_review_round = 0
        self.completed_assessments: dict[str, int] = {}
        self.correction_case_variants: dict[str, set[str]] = {}
        self.validation_source_basis_verified = False
        self.low_blocker_readback_verified = False
        self.task_one_shot_decision_used = False
        self.goal_one_shot_decision_used = False
        self.fixture_target = ""
        self.current_procedure_id = ""
        self.scenario = "standard"

    def __enter__(self) -> Self:
        try:
            return self._enter()
        except BaseException as error:
            self.__exit__(type(error), error, error.__traceback__)
            raise

    def _enter(self) -> Self:
        uid = os.geteuid()
        root = Path(
            tempfile.mkdtemp(prefix=f"podway-release-{uid}-", dir="/private/tmp")
        )
        self.root = root
        root.chmod(0o700)
        self.deadline = time.monotonic() + RUN_TIMEOUT_SECONDS
        self.account = root / "account"
        self.dev_home = root
        self.sandbox = root / "sandbox"
        cache = root / "cache"
        temporary = root / "tmp"
        snapshot_id = sha256_file(self.daemon)[:16]
        snapshot = root / "snapshots" / snapshot_id
        private_directory(self.account)
        private_directory(self.sandbox)
        private_directory(cache)
        private_directory(temporary)
        private_directory(root / "snapshots")
        private_directory(snapshot)
        private_directory(root / "run")
        private_directory(root / "state")
        private_directory(root / "logs")

        self.snapshot_binary = snapshot / "podway"
        self.snapshot_daemon = snapshot / "podwayd"
        shutil.copyfile(self.binary, self.snapshot_binary)
        shutil.copyfile(self.daemon, self.snapshot_daemon)
        self.snapshot_binary.chmod(0o755)
        self.snapshot_daemon.chmod(0o755)
        metadata = {
            "schema": RUNTIME_SCHEMA,
            "metadata_version": 3,
            "purpose": "release-qualification",
            "euid": uid,
            "canonical_root": str(root),
            "mode": RUNTIME_MODE,
            "paths": {
                "lock": str(root / "run" / "podwayd.lock"),
                "socket": str(root / "run" / "podwayd.sock"),
                "service_state": str(root / "state" / "service.json"),
                "registry": str(root / "state" / "workspaces.json"),
                "recovery": str(root / "state" / "recovery.json"),
                "log": str(root / "logs" / "podwayd.log"),
                "bootstrap_log": str(root / "logs" / "podwayd-bootstrap.log"),
            },
            "sandbox_root": str(self.sandbox),
            "executables": {
                "cli": {
                    "path": str(self.snapshot_binary),
                    "sha256": f"sha256:{sha256_file(self.snapshot_binary)}",
                },
                "daemon": {
                    "path": str(self.snapshot_daemon),
                    "sha256": f"sha256:{sha256_file(self.snapshot_daemon)}",
                },
                "controller": None,
            },
            "generation": None,
        }
        metadata_path = root / "runtime.json"
        metadata_path.write_text(
            json.dumps(metadata, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        metadata_path.chmod(0o600)
        self.environment = {
            "HOME": str(self.account),
            "PATH": "/usr/bin:/bin",
            "PODWAY_DEV_HOME": str(self.dev_home),
            "TMPDIR": str(temporary),
            "XDG_CACHE_HOME": str(cache),
            "XDG_CONFIG_HOME": str(root / "config"),
            "XDG_STATE_HOME": str(root / "state"),
        }
        bounded_process(["git", "init", "-q"], cwd=self.sandbox)
        bounded_process(
            ["git", "config", "user.name", "Aquarium Qualification"],
            cwd=self.sandbox,
        )
        bounded_process(
            ["git", "config", "user.email", "aquarium@example.invalid"],
            cwd=self.sandbox,
        )
        bounded_process(
            ["git", "commit", "--allow-empty", "-q", "-m", "qualification fixture"],
            cwd=self.sandbox,
        )
        self.fixture_target = (
            bounded_process(["git", "rev-parse", "HEAD"], cwd=self.sandbox)
            .stdout.decode("utf-8")
            .strip()
        )
        daemon_log = root / "logs" / "qualification-harness.log"
        self.log = daemon_log.open("xb")
        self.process = subprocess.Popen(
            [str(self.snapshot_daemon), "--mode", RUNTIME_MODE],
            cwd=self.sandbox,
            env=self.environment,
            stdin=subprocess.DEVNULL,
            stdout=self.log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        self.wait_ready()
        initialized = output_result(
            self.raw(["--json", "init"]),
            "workspace.init",
            "podway.workspace-init-result/v1",
        )
        if initialized.get("initialized") is not True:
            raise RuntimeQualificationError("isolated workspace did not initialize")
        installed = self.sandbox / ".podway" / "procedures"
        installed.mkdir(parents=True, exist_ok=True)
        for source in self.procedures.glob("*.yaml"):
            target = installed / source.name
            target.write_bytes(source.read_bytes())
            if target.read_bytes() != source.read_bytes():
                raise RuntimeQualificationError(
                    "canonical Procedure copy changed bytes"
                )
        return self

    def __exit__(self, exc_type, exc, traceback) -> bool:
        cleanup_error: Exception | None = None
        try:
            self.terminate()
        except (
            OSError,
            RuntimeQualificationError,
            subprocess.SubprocessError,
        ) as error:  # cleanup must preserve the original failure
            cleanup_error = error
        finally:
            if self.log is not None:
                self.log.close()
            if cleanup_error is None and self.root is not None:
                shutil.rmtree(self.root)
                if self.root.exists():
                    cleanup_error = RuntimeQualificationError(
                        "release-qualification root survived cleanup"
                    )
        if cleanup_error is not None:
            raise RuntimeQualificationError(
                f"release-qualification cleanup failed: {cleanup_error}"
            ) from exc
        return False

    @property
    def socket(self) -> Path:
        assert self.dev_home is not None
        return self.dev_home / "run" / "podwayd.sock"

    def wait_ready(self) -> None:
        deadline = time.monotonic() + READINESS_TIMEOUT_SECONDS
        last_error: OSError | RuntimeQualificationError | None = None
        while time.monotonic() < deadline:
            if self.process is not None and self.process.poll() is not None:
                raise RuntimeQualificationError(
                    "official podwayd exited before reaching readiness"
                )
            try:
                result = self.daemon_status_probe()
            except (OSError, RuntimeQualificationError) as error:
                last_error = error
                time.sleep(0.05)
                continue
            pid = result.get("pid")
            if isinstance(pid, int) and pid > 0:
                self.daemon_pid = pid
            if (
                result.get("readiness_state") == "ready"
                and result.get("readiness_stage") == "ready"
                and result.get("mode") == RUNTIME_MODE
                and result.get("daemon_version") == "v0.2.10"
                and result.get("contract_manifest_digest") == CONTRACT_MANIFEST_DIGEST
                and (
                    result.get("in_flight_client_count") is None
                    or (
                        isinstance(result.get("in_flight_client_count"), int)
                        and not isinstance(result.get("in_flight_client_count"), bool)
                        and 0 <= result["in_flight_client_count"] <= 1024
                    )
                )
                and (
                    result.get("maintenance_operation_count") is None
                    or (
                        isinstance(result.get("maintenance_operation_count"), int)
                        and not isinstance(
                            result.get("maintenance_operation_count"), bool
                        )
                        and 0 <= result["maintenance_operation_count"] <= 10_000
                    )
                )
            ):
                if self.daemon_pid is None:
                    raise RuntimeQualificationError(
                        "ready daemon omitted its process identity"
                    )
                return
            time.sleep(0.05)
        detail = type(last_error).__name__ if last_error is not None else "not-ready"
        log_tail = ""
        runtime_files: list[str] = []
        if self.root is not None:
            for candidate in sorted(self.root.rglob("*")):
                if candidate.is_file():
                    runtime_files.append(candidate.relative_to(self.root).as_posix())
                    if candidate.name.endswith(".log"):
                        try:
                            log_tail += candidate.read_text(
                                encoding="utf-8", errors="replace"
                            )[-1000:]
                        except OSError:
                            pass
        raise RuntimeQualificationError(
            "daemon did not reach v0.2.10 release-qa readiness: "
            f"{detail}; files={runtime_files!r}; daemon_log={log_tail!r}"
        )

    def daemon_status_probe(self) -> dict[str, Any]:
        request = {
            "protocol": "podway.ipc/v1",
            "request_id": str(uuid.uuid4()),
            "client": {
                "name": "aquarium-release-qualification",
                "pid": os.getpid(),
                "product": "podway",
                "version": "v0.2.10",
                "contract_manifest_digest": CONTRACT_MANIFEST_DIGEST,
            },
            "operation": "control",
            "command": "daemon.status",
            "options": {"detach": False, "wait_timeout_ms": 0},
            "payload": {},
        }
        encoded = json.dumps(request, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(1.0)
            client.connect(str(self.socket))
            client.sendall(struct.pack(">I", len(encoded)) + encoded)
            client.shutdown(socket.SHUT_WR)
            size = struct.unpack(">I", receive_exact(client, 4))[0]
            if size <= 0 or size > 1024 * 1024:
                raise RuntimeQualificationError("invalid daemon response frame size")
            try:
                response = json.loads(receive_exact(client, size))
            except json.JSONDecodeError as error:
                raise RuntimeQualificationError(
                    "daemon status response is not JSON"
                ) from error
        if not isinstance(response, dict):
            raise RuntimeQualificationError("daemon status response is not an object")
        result = response.get("result")
        if (
            response.get("schema") != OUTPUT_SCHEMA
            or response.get("command") != "daemon.status"
            or not isinstance(result, dict)
            or result.get("schema") != "podway.daemon-status-result/v3"
        ):
            raise RuntimeQualificationError("invalid daemon status response")
        return result

    def terminate(self) -> None:
        if self.process is not None and self.process.poll() is None:
            try:
                os.killpg(self.process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                self.process.wait(timeout=PROCESS_EXIT_TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(self.process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                self.process.wait(timeout=PROCESS_EXIT_TIMEOUT_SECONDS)
        if self.daemon_is_alive() and self.daemon_pid is not None:
            try:
                os.kill(self.daemon_pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            deadline = time.monotonic() + PROCESS_EXIT_TIMEOUT_SECONDS
            while time.monotonic() < deadline and self.daemon_is_alive():
                time.sleep(0.05)
        if self.daemon_is_alive() and self.daemon_pid is not None:
            try:
                os.kill(self.daemon_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if self.daemon_is_alive():
            raise RuntimeQualificationError(
                "release-qualification daemon survived shutdown"
            )
        if self.dev_home is not None and self.socket.exists():
            raise RuntimeQualificationError(
                "release-qualification socket survived shutdown"
            )

    def daemon_is_alive(self) -> bool:
        if self.daemon_pid is None:
            return False
        try:
            os.kill(self.daemon_pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    def raw(
        self,
        arguments: list[str],
        *,
        stdin: bytes | None = None,
        expected_exit: int | None = 0,
        timeout_seconds: float = COMMAND_TIMEOUT_SECONDS,
    ) -> subprocess.CompletedProcess[bytes]:
        assert self.snapshot_binary is not None
        assert self.sandbox is not None
        assert self.environment is not None
        assert self.deadline is not None
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise RuntimeQualificationError(
                "isolated runtime exceeded overall deadline"
            )
        return bounded_process(
            [str(self.snapshot_binary), "--mode", RUNTIME_MODE, *arguments],
            cwd=self.sandbox,
            environment=self.environment,
            stdin=stdin,
            timeout_seconds=min(timeout_seconds, remaining),
            expected_exit=expected_exit,
        )

    def observe(self) -> dict[str, Any]:
        return output_result(
            self.raw(["observe", "--json", "--wait-for-idle"]),
            "session.observe",
            OBSERVATION_SCHEMA,
        )

    def next_key(self, label: str) -> str:
        self.command_sequence += 1
        return f"qualification-{self.run_index}-{self.command_sequence}-{label}"

    def invoke_template(
        self,
        observation: dict[str, Any],
        command: str,
        replacements: dict[str, str] | None = None,
        *,
        expected_exit: int | None = 0,
    ) -> subprocess.CompletedProcess[bytes]:
        templates = [
            template
            for template in observation.get("mutation_templates", [])
            if template.get("command") == command
        ]
        if not templates and command == "session.complete":
            status = observation["status"]
            current = status["current"]
            return self.raw(
                [
                    "complete",
                    "--if-workspace-uuid",
                    self.workspace_uuid(observation),
                    "--if-session-id",
                    status["session"]["id"],
                    "--if-session-revision",
                    str(status["session"]["revision"]),
                    "--if-attempt",
                    current["attempt"]["attempt_id"],
                    "--idempotency-key",
                    self.next_key("complete"),
                    "--json",
                ],
                expected_exit=expected_exit,
            )
        if not templates:
            raise RuntimeQualificationError(
                f"observation omitted {command} template: "
                f"node={observation.get('guidance', {}).get('node', {}).get('graph_node_id')!r}; "
                "commands="
                f"{[item.get('command') for item in observation.get('mutation_templates', [])]!r}"
            )
        argv = list(templates[0]["argv"])[1:]
        if "--json" not in argv:
            argv.insert(0, "--json")
        values = {"<idempotency-key>": self.next_key(command)}
        values.update(replacements or {})
        argv = [values.get(argument, argument) for argument in argv]
        if any(
            argument.startswith("<") and argument.endswith(">") for argument in argv
        ):
            raise RuntimeQualificationError(
                f"unresolved placeholder in {command} template"
            )
        return self.raw(argv, expected_exit=expected_exit)

    @staticmethod
    def workspace_uuid(observation: dict[str, Any]) -> str:
        for template in observation.get("mutation_templates", []):
            value = template.get("preconditions", {}).get("workspace_uuid")
            if isinstance(value, str):
                return value
        raise RuntimeQualificationError("observation omitted workspace UUID fences")

    def mark_case_variant(self, case_id: str, variant: str) -> None:
        if case_id not in EXPECTED_NATIVE_CASE_VARIANTS:
            raise RuntimeQualificationError(f"unknown correction case: {case_id}")
        self.correction_case_variants.setdefault(case_id, set()).add(variant)

    def domain_state(self, observation: dict[str, Any]) -> dict[str, Any]:
        status = observation["status"]
        current = status["current"]
        return {
            "workspace_uuid": self.workspace_uuid(observation),
            "session_id": status["session"]["id"],
            "session_lifecycle": status["session"]["lifecycle"],
            "session_revision": status["session"]["revision"],
            "graph_node_id": current["node"]["graph_node_id"],
            "attempt_id": current["attempt"]["attempt_id"],
            "goal_revision": status.get("goal_revision"),
        }

    def reject_guarded_decision(
        self, observation: dict[str, Any], option: str
    ) -> dict[str, Any]:
        before = self.domain_state(observation)
        rejected = self.decide(observation, option, expected_exit=None)
        if (
            rejected.returncode == 0
            or error_code(rejected) != "OPTION_GUARD_UNSATISFIED"
        ):
            raise RuntimeQualificationError(
                f"guarded option was not rejected: option={option!r}; "
                f"exit={rejected.returncode}"
            )
        after = self.observe()
        after_state = self.domain_state(after)
        if after_state != before:
            raise RuntimeQualificationError(
                "guard rejection changed domain state: "
                f"before={before!r}; after={after_state!r}"
            )
        return after

    def read_complete_evidence(
        self, observation: dict[str, Any], source: str, item: str
    ) -> Any:
        expected_digest = None
        for readback in observation.get("guidance", {}).get("readback", []):
            if readback.get("source_graph_node_id") != source:
                continue
            for selected in readback.get("items", []):
                if selected.get("item_id") == item:
                    expected_digest = selected.get("value_digest")
        if not isinstance(expected_digest, str):
            raise RuntimeQualificationError(
                f"evidence was not selected by the current consumer: {source}:{item}"
            )
        status = observation["status"]
        result = output_result(
            self.raw(
                [
                    "--json",
                    "evidence",
                    "read",
                    "--source",
                    source,
                    "--item",
                    item,
                    "--if-workspace-uuid",
                    self.workspace_uuid(observation),
                    "--if-session-id",
                    status["session"]["id"],
                ]
            ),
            "evidence.read",
            "podway.evidence-read-result/v1",
        )
        if (
            result.get("truncated") is not False
            or result.get("next_page_token") is not None
            or result.get("value_digest") != expected_digest
        ):
            raise RuntimeQualificationError(
                f"evidence read was incomplete or changed: {source}:{item}"
            )
        return result["page"]["data"]

    @staticmethod
    def decision_destination(
        completed: subprocess.CompletedProcess[bytes], expected: str
    ) -> None:
        result = output_result(completed, "session.decide", "podway.decision-result/v1")
        if result.get("target_graph_node_id") != expected:
            raise RuntimeQualificationError(
                "decision reached the wrong destination: "
                f"expected={expected!r}; "
                f"actual={result.get('target_graph_node_id')!r}"
            )

    def exercise_workspace_removal(self) -> dict[str, Any]:
        assert self.sandbox is not None
        podway_directory = self.sandbox / ".podway"
        git_directory = self.sandbox / ".git"
        sentinel = self.sandbox / "workspace-removal-sentinel.txt"
        sentinel_contents = b"preserve the Git worktree\n"
        sentinel.write_bytes(sentinel_contents)

        shown = json_payload(self.raw(["--json", "workspace", "show"]))
        workspace = shown.get("workspace")
        workspace_uuid = workspace.get("uuid") if isinstance(workspace, dict) else None
        if (
            shown.get("schema") != OUTPUT_SCHEMA
            or shown.get("command") != "workspace.show"
            or not isinstance(workspace_uuid, str)
        ):
            raise RuntimeQualificationError(
                "workspace show omitted the initialized workspace identity"
            )

        mismatched_uuid = str(uuid.uuid4())
        while mismatched_uuid == workspace_uuid:
            mismatched_uuid = str(uuid.uuid4())
        mismatch = self.raw(
            [
                "--json",
                "workspace",
                "remove",
                "--force",
                "--if-workspace-uuid",
                mismatched_uuid,
                "--yes",
            ],
            expected_exit=None,
        )
        if (
            mismatch.returncode == 0
            or error_code(mismatch) != "WORKSPACE_UUID_MISMATCH"
        ):
            raise RuntimeQualificationError(
                "workspace removal did not reject a mismatched UUID fence"
            )
        if not podway_directory.is_dir():
            raise RuntimeQualificationError(
                "mismatched workspace removal changed Podway state"
            )

        removal_arguments = [
            "--json",
            "workspace",
            "remove",
            "--force",
            "--if-workspace-uuid",
            workspace_uuid,
            "--yes",
        ]
        workspace_removal_result(
            self.raw(removal_arguments), str(self.sandbox.resolve()), workspace_uuid
        )
        if (
            podway_directory.exists()
            or not self.sandbox.is_dir()
            or not git_directory.exists()
            or sentinel.read_bytes() != sentinel_contents
        ):
            raise RuntimeQualificationError(
                "workspace removal did not preserve the Git worktree boundary"
            )

        replay = workspace_removal_result(
            self.raw(removal_arguments), str(self.sandbox.resolve()), None
        )
        post_removal_status = self.daemon_status_probe()
        if (
            podway_directory.exists()
            or not self.sandbox.is_dir()
            or not git_directory.exists()
            or sentinel.read_bytes() != sentinel_contents
            or post_removal_status.get("registered_worktree_count") != 0
        ):
            raise RuntimeQualificationError(
                "workspace removal replay did not preserve the verified terminal state"
            )

        return {
            "result_schema": "podway.workspace-removal-result/v1",
            "uuid_mismatch_rejected": True,
            "initial_removal_passed": True,
            "replay_result": replay,
            "replay_postcondition_verified": True,
            "podway_directory_absent": True,
            "registry_absent": True,
            "git_worktree_preserved": True,
        }

    def begin_goal(self, observation: dict[str, Any], procedure_id: str) -> None:
        templates = [
            template
            for template in observation.get("mutation_templates", [])
            if template.get("command") == "session.begin"
        ]
        if len(templates) != 1:
            raise RuntimeQualificationError(
                "prepared observation omitted one begin template"
            )
        argv = list(templates[0]["argv"])[1:]
        if "--json" not in argv:
            argv.insert(0, "--json")
        begin_index = argv.index("begin") + 1
        argv[begin_index:begin_index] = [
            "--goal",
            f"Complete isolated {procedure_id} qualification.",
            "--criterion",
            "runtime=The exact official artifact completes this Procedure.",
        ]
        output_result(self.raw(argv), "session.begin", "podway.session-begin-result/v1")

    def decide(
        self,
        observation: dict[str, Any],
        option: str,
        *,
        expected_exit: int | None = 0,
    ) -> subprocess.CompletedProcess[bytes]:
        templates = [
            template
            for template in observation.get("mutation_templates", [])
            if template.get("command") == "session.decide"
            and "--option" in template.get("argv", [])
            and template["argv"][template["argv"].index("--option") + 1] == option
        ]
        if not templates and expected_exit is None:
            status = observation["status"]
            current = status["current"]
            return self.raw(
                [
                    "decide",
                    "--option",
                    option,
                    "--reason",
                    f"qualification probed guarded option {option}",
                    "--if-workspace-uuid",
                    self.workspace_uuid(observation),
                    "--if-session-id",
                    status["session"]["id"],
                    "--if-session-revision",
                    str(status["session"]["revision"]),
                    "--if-attempt",
                    current["attempt"]["attempt_id"],
                    "--idempotency-key",
                    self.next_key(f"guarded-{option}"),
                    "--json",
                ],
                expected_exit=None,
            )
        if len(templates) != 1:
            node = observation["guidance"]["node"]["graph_node_id"]
            allowed = observation["guidance"].get("allowed_option_ids", [])
            raise RuntimeQualificationError(
                "observation omitted one decision template: "
                f"scenario={self.scenario}; node={node}; option={option}; "
                f"allowed={allowed}"
            )
        argv = list(templates[0]["argv"])[1:]
        if "--json" not in argv:
            argv.insert(0, "--json")
        values = {
            "<reason>": f"qualification selected {option}",
            "<idempotency-key>": self.next_key(f"decide-{option}"),
        }
        argv = [values.get(argument, argument) for argument in argv]
        return self.raw(argv, expected_exit=expected_exit)

    def rework_to(self, observation: dict[str, Any], target: str) -> None:
        templates = [
            template
            for template in observation.get("mutation_templates", [])
            if template.get("command") == "session.rework"
            and "--to" in template.get("argv", [])
            and template["argv"][template["argv"].index("--to") + 1] == target
        ]
        if not templates:
            status = observation["status"]
            current = status["current"]
            self.raw(
                [
                    "rework",
                    "--to",
                    target,
                    "--reason",
                    f"qualification rework to {target}",
                    "--if-workspace-uuid",
                    self.workspace_uuid(observation),
                    "--if-session-id",
                    status["session"]["id"],
                    "--if-session-revision",
                    str(status["session"]["revision"]),
                    "--if-attempt",
                    current["attempt"]["attempt_id"],
                    "--idempotency-key",
                    self.next_key(f"rework-{target}"),
                    "--json",
                ]
            )
            return
        if len(templates) != 1:
            raise RuntimeQualificationError(
                f"observation omitted one rework template for {target}"
            )
        argv = list(templates[0]["argv"])[1:]
        if "--json" not in argv:
            argv.insert(0, "--json")
        values = {
            "<reason>": f"qualification rework to {target}",
            "<idempotency-key>": self.next_key(f"rework-{target}"),
        }
        argv = [values.get(argument, argument) for argument in argv]
        self.raw(argv)

    def record(self, observation: dict[str, Any], records: dict[str, Any]) -> None:
        status = observation["status"]
        current = status["current"]
        items = {item["item_id"]: item for item in observation["active_items"]}
        document = {
            "schema": "podway.item-record-many-input/v1",
            "workspace_uuid": self.workspace_uuid(observation),
            "session_id": status["session"]["id"],
            "session_revision": status["session"]["revision"],
            "attempt_id": current["attempt"]["attempt_id"],
            "idempotency_key": self.next_key("record"),
            "operations": [
                {
                    "item_id": item_id,
                    "expected_item_revision": items[item_id]["revision"],
                    **({"clear": True} if value is None else {"record": value}),
                }
                for item_id, value in records.items()
            ],
        }
        output_result(
            self.raw(
                ["record", "--stdin", "--json"],
                stdin=json.dumps(document).encode("utf-8"),
            ),
            "item.record_many",
            "podway.item-record-many-result/v1",
        )

    def try_record_failure(
        self, observation: dict[str, Any], records: dict[str, Any]
    ) -> str:
        status = observation["status"]
        current = status["current"]
        items = {item["item_id"]: item for item in observation["active_items"]}
        document = {
            "schema": "podway.item-record-many-input/v1",
            "workspace_uuid": self.workspace_uuid(observation),
            "session_id": status["session"]["id"],
            "session_revision": status["session"]["revision"],
            "attempt_id": current["attempt"]["attempt_id"],
            "idempotency_key": self.next_key("rejected-record"),
            "operations": [
                {
                    "item_id": item_id,
                    "expected_item_revision": items[item_id]["revision"],
                    "record": value,
                }
                for item_id, value in records.items()
            ],
        }
        return error_code(
            self.raw(
                ["record", "--stdin", "--json"],
                stdin=json.dumps(document).encode("utf-8"),
                expected_exit=None,
            )
        )

    def value_for(self, item: dict[str, Any], node: str) -> dict[str, Any]:
        item_type = item["type"]
        item_id = item["item_id"]
        constraints = item.get("constraints", {})
        provider_low_ids = (
            ["provider:R1:L1"]
            if self.scenario == "standard"
            and self.current_procedure_id == "aquarium-validation-v2"
            and self.run_index == 2
            else []
        )
        audit_low_ids = (
            ["audit:A1:L1", "audit:A1:L2"]
            if self.current_procedure_id == "aquarium-validation-v2"
            and self.scenario in {"standard", "validation-low-blocker-wait"}
            else []
        )
        applicable_low_ids = [*audit_low_ids, *provider_low_ids]
        blocker_fixture = (
            low_blocker_fixture(self.scenario, self.fixture_target)
            if self.scenario in LOW_BLOCKER_SCENARIOS
            else None
        )
        route_qualification = ROUTE_QUALIFICATION_SCENARIOS.get(self.scenario)
        qualified_route = route_qualification[1] if route_qualification else None
        goal_recovery = self.scenario in GOAL_RECOVERY_SCENARIOS
        validation_recovery = self.scenario in VALIDATION_RECOVERY_SCENARIOS
        if item_type == "text":
            maximum = constraints.get("max_length", 256)
            if route_qualification and item_id == "assessment-provenance":
                value = route_qualification_provenance(qualified_route)
            elif route_qualification and item_id == "review-evidence-reference":
                value = route_qualification_evidence_reference(
                    qualified_route, self.scenario
                )
            elif route_qualification and item_id == "waiver-summary":
                value = (
                    "review waived by fixture authority for the exact target; "
                    "no delegated-review assurance is claimed"
                )
            elif item_id == "implementation-summary":
                value = (
                    f"runtime-{self.run_index}-{self.command_sequence}-" + "x" * 5000
                )[:maximum]
            elif item_id == "applicable-obligation-summary":
                value = json.dumps(
                    {
                        "audit_count": len(audit_low_ids),
                        "audit_low_ids": audit_low_ids,
                        "provider_count": len(provider_low_ids),
                        "provider_low_ids": provider_low_ids,
                        "pending_low_ids": applicable_low_ids,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
            elif node == "final-review" and item_id == "valid-finding-ids":
                value = json.dumps(
                    {"provider_low_ids": provider_low_ids},
                    sort_keys=True,
                    separators=(",", ":"),
                )
            elif node == "final-review" and item_id == "finding-disposition-summary":
                value = json.dumps(
                    {
                        "audit_low_ids": audit_low_ids,
                        "provider_low_ids": provider_low_ids,
                        "state": "pending-local-disposition",
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
            elif (
                blocker_fixture is not None
                and node == "record-low-disposition"
                and item_id == "source-review-basis"
            ):
                value = json.dumps(
                    blocker_fixture["source_basis"],
                    sort_keys=True,
                    separators=(",", ":"),
                )
            elif (
                blocker_fixture is not None
                and node == "record-low-disposition"
                and item_id == "low-disposition-summary"
            ):
                value = json.dumps(
                    blocker_fixture["disposition_summary"],
                    sort_keys=True,
                    separators=(",", ":"),
                )
            elif (
                self.current_procedure_id == "aquarium-validation-v2"
                and node == "record-low-disposition"
                and item_id == "source-review-basis"
            ):
                value = json.dumps(
                    {
                        "audit_low_ids": audit_low_ids,
                        "provider_low_ids": provider_low_ids,
                        "target": self.fixture_target,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
            elif (
                self.current_procedure_id == "aquarium-validation-v2"
                and node == "record-low-disposition"
                and item_id == "low-disposition-summary"
            ):
                value = json.dumps(
                    {
                        "dispositions": [
                            {"id": identity, "result": "fixture-corrected-and-verified"}
                            for identity in applicable_low_ids
                        ]
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
            elif item_id in {"audit-basis-target", "before-target", "after-target"}:
                value = self.fixture_target
            elif self.scenario == "goal-hardening-defer" and item_id in {
                "hardening-deferral-evidence-sha256",
                "hardening-deferral-native-target-sha256",
            }:
                value = (
                    "sha256:"
                    + hashlib.sha256(b"qualification-hardening-deferral").hexdigest()
                )
            else:
                value = f"qualification {node} {item_id}"
            return {"type": "text", "value": value}
        if item_type == "integer":
            low_counts = {
                ("audit", "confirmed-gap-count"),
                ("audit", "eligible-low-gap-count"),
                ("record-evidence", "effective-low-findings"),
                ("record-evidence", "unresolved-valid-findings"),
            }
            value = (
                2
                if (node, item_id) in low_counts
                and route_qualification is None
                and not goal_recovery
                and not validation_recovery
                else constraints.get("minimum", 0)
            )
            if (
                self.current_procedure_id == "aquarium-task-v2"
                and node == "prepare-review"
                and item_id == "prior-assessment-ordinal"
            ):
                value = (
                    1
                    if self.scenario in TASK_COMPLETED_CHANGE_SCENARIOS
                    else max(0, self.node_visits.get("review", 0))
                )
            if (
                self.current_procedure_id == "aquarium-task-v2"
                and node == "review"
                and item_id == "assessment-ordinal"
            ):
                value = (
                    0
                    if self.scenario in TASK_RESUME_SCENARIOS
                    and self.scenario not in TASK_COMPLETED_CHANGE_SCENARIOS
                    else 2
                    if self.scenario in TASK_COMPLETED_CHANGE_SCENARIOS
                    else max(1, self.node_visits.get("review", 1))
                )
            if (
                self.current_procedure_id == "aquarium-goal-v2"
                and node == "record-evidence"
                and item_id == "prior-assessment-ordinal"
            ):
                value = self.completed_assessments.get(self.current_procedure_id, 0)
            if (
                self.current_procedure_id == "aquarium-goal-v2"
                and node == "record-evidence"
                and item_id == "assessment-ordinal"
            ):
                value = (
                    0
                    if goal_recovery and self.goal_evidence_round == 0
                    else self.completed_assessments.get(self.current_procedure_id, 0)
                    + 1
                )
            if (
                self.current_procedure_id == "aquarium-validation-v2"
                and node == "final-review"
                and item_id == "prior-assessment-ordinal"
            ):
                value = self.completed_assessments.get(self.current_procedure_id, 0)
            if (
                self.current_procedure_id == "aquarium-validation-v2"
                and node == "final-review"
                and item_id == "assessment-ordinal"
            ):
                value = (
                    0
                    if validation_recovery and self.validation_review_round == 0
                    else self.completed_assessments.get(self.current_procedure_id, 0)
                    + 1
                )
            if (
                self.scenario in VALIDATION_FINAL_REVIEW_SCENARIOS
                and node == "final-review"
                and item_id == "required-evidence-gaps"
            ):
                expected_gaps = VALIDATION_FINAL_REVIEW_SCENARIOS[self.scenario][1]
                value = expected_gaps if expected_gaps is not None else 0
            if (
                self.scenario in VALIDATION_FINAL_REVIEW_SCENARIOS
                and node == "audit"
                and item_id
                in {
                    "confirmed-gap-count",
                    "blocking-gap-count",
                    "eligible-low-gap-count",
                    "confirmation-needed-gap-count",
                }
            ):
                value = 0
            if (
                self.scenario == "goal-operational-matrix"
                and node == "record-evidence"
                and item_id
                in {
                    "unresolved-valid-findings",
                    "effective-medium-or-higher-findings",
                    "effective-low-findings",
                    "confirmation-needed-findings",
                }
            ):
                value = 0
            if (
                self.scenario in GOAL_KIND_SCENARIOS
                and node == "record-evidence"
                and item_id
                in {
                    "unresolved-valid-findings",
                    "effective-medium-or-higher-findings",
                    "effective-low-findings",
                    "confirmation-needed-findings",
                }
            ):
                value = 0
            if (
                self.scenario.startswith("goal-completion-")
                and node == ("record-evidence")
                and item_id
                in {
                    "unresolved-valid-findings",
                    "effective-medium-or-higher-findings",
                    "effective-low-findings",
                    "confirmation-needed-findings",
                }
            ):
                value = 0
            if (
                self.scenario.startswith("validation-completion-")
                and node == ("audit")
                and item_id
                in {
                    "confirmed-gap-count",
                    "blocking-gap-count",
                    "eligible-low-gap-count",
                    "confirmation-needed-gap-count",
                }
            ):
                value = 0
            if self.scenario == "medium-wait" and node == "record-evidence":
                if item_id in {
                    "effective-medium-or-higher-findings",
                    "unresolved-valid-findings",
                }:
                    value = 1
                elif item_id == "effective-low-findings":
                    value = 0
            if (
                self.scenario == "goal-finding-inconsistent"
                and node == "record-evidence"
                and item_id
                in {
                    "unresolved-valid-findings",
                    "effective-medium-or-higher-findings",
                    "effective-low-findings",
                }
            ):
                inconsistent = self.node_visits.get(node) == 1
                value = (
                    2
                    if inconsistent and item_id == "unresolved-valid-findings"
                    else int(inconsistent and item_id == "effective-low-findings")
                )
            if self.scenario == "goal-hardening-defer" and node == "record-evidence":
                if item_id in {
                    "unresolved-valid-findings",
                    "effective-low-findings",
                }:
                    value = 1
                elif item_id == "effective-medium-or-higher-findings":
                    value = 0
            if self.scenario in VALIDATION_CONFIRMATION_SCENARIOS:
                if node == "audit" and item_id in {
                    "confirmed-gap-count",
                    "blocking-gap-count",
                    "eligible-low-gap-count",
                    "confirmation-needed-gap-count",
                }:
                    value = 0
                if self.scenario == "validation-medium-wait" and node == "final-review":
                    if item_id in {
                        "unresolved-valid-findings",
                        "medium-or-higher-findings",
                        "medium-findings",
                        "current-applicable-blockers",
                    }:
                        value = 1
                    elif item_id in {
                        "blocker-findings",
                        "critical-findings",
                        "high-findings",
                        "low-findings",
                        "confirmation-needed-findings",
                        "pending-applicable-low-dispositions",
                        "required-evidence-gaps",
                    }:
                        value = 0
            if (
                self.scenario == "validation-stop-preserves-completion"
                and node == "final-review"
                and item_id == "completion-unmet-criteria"
            ):
                value = 1
            if (
                self.scenario in {"standard", "validation-low-blocker-wait"}
                and node == "final-review"
                and item_id
                in {
                    "low-findings",
                    "unresolved-valid-findings",
                }
            ):
                value = len(provider_low_ids)
            if (
                self.scenario in {"standard", "validation-low-blocker-wait"}
                and node == "final-review"
                and item_id == "pending-applicable-low-dispositions"
            ):
                value = len(applicable_low_ids)
            if (
                self.scenario == "task-completion-unverified"
                and node == "review"
                and self.node_visits.get("review") == 2
                and item_id == "completion-unverified-criteria"
            ):
                value = 1
            if (
                self.scenario == "task-completion-mixed-owners"
                and node == "review"
                and self.node_visits.get("review") == 2
                and item_id
                in {
                    "completion-unmet-criteria",
                    "implementation-rework-obligations",
                    "verification-rework-obligations",
                    "documentation-rework-obligations",
                }
            ):
                value = 1
            if (
                self.scenario
                in {
                    *TASK_OWNER_SCENARIOS,
                    "task-completion-owner-inconsistent",
                    "task-finding-inconsistent",
                }
                and node == "review"
                and self.node_visits.get("review") == 2
            ):
                owned_item = TASK_OWNER_SCENARIOS.get(self.scenario)
                if self.scenario != "task-finding-inconsistent" and item_id in {
                    "completion-unmet-criteria",
                    owned_item,
                }:
                    value = 1
                if self.scenario == "task-finding-inconsistent" and item_id in {
                    "unresolved-valid-findings",
                    "effective-low-findings",
                }:
                    value = 2 if item_id == "unresolved-valid-findings" else 1
            if (
                self.scenario in TASK_CONFIRMATION_SCENARIOS
                and node == "review"
                and self.node_visits.get("review") in {2, 3}
                and item_id
                in {
                    "completion-unmet-criteria",
                    "implementation-rework-obligations",
                }
            ):
                value = 1
            if (
                self.scenario in GOAL_CLOSEOUT_GAP_SCENARIOS
                and node == "record-evidence"
                and item_id == "completion-unmet-criteria"
            ):
                value = 1
            if (
                self.scenario in COMPLETION_GAP_SCENARIOS
                and node
                == (
                    "record-evidence"
                    if self.current_procedure_id == "aquarium-goal-v2"
                    else "final-review"
                )
                and self.node_visits.get(node) == 1
            ):
                _procedure, gap = COMPLETION_GAP_SCENARIOS[self.scenario]
                if item_id == f"completion-{gap}-criteria":
                    value = 1
            if (
                node == "record-audit-low-basis"
                and item_id == "audit-low-finding-count"
            ):
                value = 2
            if node == "record-low-disposition":
                round_index = self.low_settlement_rounds.get(
                    self.current_procedure_id, 0
                )
                if self.scenario in {
                    "low-blocker-wait",
                    "validation-low-blocker-wait",
                }:
                    if item_id == "pending-low-dispositions":
                        value = 0
                    elif item_id == "current-blocking-findings":
                        value = 1
                elif item_id == "pending-low-dispositions":
                    value = 0 if round_index >= 2 else 1
                elif item_id == "current-blocking-findings":
                    value = 0
            if self.scenario == "standard" and node == "review":
                if not self.task_review_reworked and item_id == (
                    "implementation-rework-obligations"
                ):
                    value = 1
                elif (
                    self.task_review_reworked
                    and self.task_medium_reworked
                    and item_id
                    in {
                        "effective-low-findings",
                        "unresolved-valid-findings",
                    }
                ):
                    value = 2
                elif (
                    self.task_review_reworked
                    and not self.task_medium_reworked
                    and item_id
                    in {
                        "effective-medium-or-higher-findings",
                        "unresolved-valid-findings",
                        "unresolved-implementation-findings",
                        "implementation-rework-obligations",
                    }
                ):
                    value = 1
            return {"type": "integer", "value": value}
        if item_type == "choice":
            choices = constraints.get("choices", [])
            task_resume = TASK_RESUME_SCENARIOS.get(self.scenario)
            goal_kind = None
            review_evidence_kind = None
            if self.scenario in GOAL_KIND_SCENARIOS:
                goal_kind, review_evidence_kind = GOAL_KIND_SCENARIOS[self.scenario]
                if (
                    self.goal_evidence_round > 0
                    and review_evidence_kind == "validated-closeout"
                ):
                    review_evidence_kind = "native-review"
            preferred = {
                "review-route": (
                    "mulgae"
                    if goal_recovery and node == "complete-work"
                    else "orca"
                    if goal_recovery and node == "record-evidence"
                    else "mulgae"
                    if validation_recovery and node == "capture-baseline"
                    else "orca"
                    if validation_recovery and node == "final-review"
                    else task_resume.get("effective_route", task_resume["route"])
                    if task_resume
                    and (
                        task_resume.get("completed_transition")
                        or (node == "review" and self.node_visits.get("review", 0) > 1)
                    )
                    else task_resume["route"]
                    if task_resume
                    else qualified_route
                ),
                "effective-review-route": (
                    task_resume.get("effective_route", task_resume["route"])
                    if task_resume
                    and (
                        task_resume.get("completed_transition")
                        or (
                            node == "prepare-review"
                            and self.node_visits.get("prepare-review", 0) > 1
                        )
                    )
                    else task_resume["route"]
                    if task_resume
                    else qualified_route
                ),
                "review-operation": (
                    ("incomplete" if self.goal_evidence_round == 0 else "complete")
                    if goal_recovery
                    else (
                        "incomplete"
                        if self.validation_review_round == 0
                        else "complete"
                    )
                    if validation_recovery
                    else (
                        "waived"
                        if task_resume.get("effective_route") == "waived"
                        else "complete"
                    )
                    if task_resume
                    and task_resume.get("completed_transition")
                    and node == "review"
                    else task_resume["operation"]
                    if task_resume
                    else "waived"
                    if qualified_route == "waived"
                    else "complete"
                    if qualified_route is not None
                    else None
                ),
                "route-authorization-basis": (
                    "explicit-route-change"
                    if goal_recovery or validation_recovery
                    else task_resume.get("checkpoint_basis", "resume-current")
                    if task_resume
                    and node == "prepare-review"
                    and (
                        task_resume.get("completed_transition")
                        or self.node_visits.get("prepare-review", 0) > 1
                    )
                    else "approved-plan"
                    if (route_qualification or task_resume)
                    and self.current_procedure_id == "aquarium-task-v2"
                    else "approved-envelope"
                    if route_qualification
                    and self.current_procedure_id == "aquarium-goal-v2"
                    else None
                ),
                "checkpoint-requested-direction": (
                    task_resume["direction"]
                    if task_resume
                    and node == "prepare-review"
                    and (
                        task_resume.get("completed_transition")
                        or self.node_visits.get("prepare-review", 0) > 1
                        or task_resume.get("planned_only")
                    )
                    else "not-applicable"
                    if self.current_procedure_id == "aquarium-task-v2"
                    else None
                ),
                "prior-review-operation": (
                    "not-applicable"
                    if validation_recovery and self.validation_review_round == 0
                    else "incomplete"
                    if validation_recovery
                    else task_resume.get("prior_operation", task_resume["operation"])
                    if task_resume
                    and node == "prepare-review"
                    and (
                        task_resume.get("completed_transition")
                        or self.node_visits.get("prepare-review", 0) > 1
                    )
                    else "not-applicable"
                    if self.current_procedure_id == "aquarium-task-v2"
                    else None
                ),
                "prior-review-route": (
                    "mulgae"
                    if validation_recovery and self.validation_review_round == 0
                    else "orca"
                    if validation_recovery
                    else task_resume["route"]
                    if task_resume
                    and node == "prepare-review"
                    and (
                        task_resume.get("completed_transition")
                        or self.node_visits.get("prepare-review", 0) > 1
                    )
                    else "not-applicable"
                    if self.current_procedure_id == "aquarium-task-v2"
                    else None
                ),
                "prior-route-change-readiness": (
                    task_resume["readiness"]
                    if task_resume
                    and node == "prepare-review"
                    and (
                        task_resume.get("completed_transition")
                        or self.node_visits.get("prepare-review", 0) > 1
                    )
                    else "not-applicable"
                    if self.current_procedure_id == "aquarium-task-v2"
                    else None
                ),
                "prior-route-lifecycle-state": (
                    "terminal-incomplete-or-failed"
                    if goal_recovery
                    else "not-started"
                    if validation_recovery and self.validation_review_round == 0
                    else "terminal-incomplete-or-failed"
                    if validation_recovery
                    else task_resume["prior_state"]
                    if task_resume
                    else None
                ),
                "route-change-readiness": (
                    "safe-to-change"
                    if goal_recovery or validation_recovery
                    else task_resume["readiness"]
                    if task_resume
                    else None
                ),
                "requested-route-direction": (
                    task_resume["direction"] if task_resume else None
                ),
                "route-direction": (
                    "resume-current" if goal_recovery or validation_recovery else None
                ),
                "finding-count-consistency": (
                    "inconsistent"
                    if (
                        self.scenario == "goal-finding-inconsistent"
                        and node == "record-evidence"
                        and self.node_visits.get(node) == 1
                    )
                    or (
                        self.scenario == "task-finding-inconsistent"
                        and node == "review"
                        and self.node_visits.get(node) == 2
                    )
                    else "consistent"
                ),
                "assessment-provenance-kind": (
                    "coordinator-waiver"
                    if qualified_route == "waived"
                    or (
                        task_resume
                        and task_resume.get("completed_transition")
                        and node == "review"
                        and task_resume.get("effective_route") == "waived"
                    )
                    else "delegated-reviewer"
                ),
                "hardening-deferral-state": (
                    "recorded"
                    if self.scenario == "goal-hardening-defer"
                    else "not-applicable"
                ),
                "goal-kind": (
                    "epic-closeout"
                    if self.scenario in GOAL_CLOSEOUT_GAP_SCENARIOS
                    else goal_kind or "member-task"
                ),
                "review-evidence-kind": (
                    "validated-closeout"
                    if self.scenario in GOAL_CLOSEOUT_GAP_SCENARIOS
                    else review_evidence_kind or "native-review"
                ),
                "review-mode": (
                    "closeout-not-required"
                    if self.scenario in GOAL_CLOSEOUT_GAP_SCENARIOS
                    else (
                        "confirmation-only"
                        if self.current_procedure_id == "aquarium-validation-v2"
                        and node == "final-review"
                        and self.completed_assessments.get(self.current_procedure_id, 0)
                        > 0
                        else (
                            "hardening-deferral-eligible"
                            if self.current_procedure_id == "aquarium-goal-v2"
                            and node == "record-evidence"
                            and self.completed_assessments.get(
                                self.current_procedure_id, 0
                            )
                            > 0
                            else (
                                "confirmation-only"
                                if self.scenario in TASK_CONFIRMATION_SCENARIOS
                                else "remediation-eligible"
                            )
                        )
                    )
                ),
                "audit-basis-status": "applicable",
                "coverage-relationship": "review-predates-low-delta",
                "backend-check-result": (
                    "pass"
                    if qualified_route == "mulgae"
                    else "not-provided"
                    if goal_recovery or validation_recovery
                    else "not-provided"
                    if qualified_route is not None
                    else (
                        "fail"
                        if self.scenario == "standard"
                        and node == "review"
                        and not self.task_review_reworked
                        else "pass"
                    )
                ),
                "reproduction-state": "reproduced",
            }.get(item_id)
            value = preferred if preferred in choices else choices[0]
            return {"type": "choice", "value": value}
        if item_type == "confirm":
            return {"type": "confirm", "value": True}
        if item_type == "list":
            if item_id == "audit-low-finding-identities":
                return {"type": "list", "value": ["audit:A1:L1", "audit:A1:L2"]}
            return {"type": "list", "value": [f"qualification {item_id}"]}
        if item_type == "check_result":
            if (
                self.scenario in TASK_RESUME_SCENARIOS
                and item_id == "route-transition-admission"
            ):
                outcome = (
                    "fail"
                    if self.scenario
                    in {
                        "task-current-only-switch-rejected",
                        "task-current-only-waive-rejected",
                    }
                    else "pass"
                )
            elif (
                self.scenario in TASK_RESUME_SCENARIOS
                and item_id == "route-direction-continuity"
            ):
                outcome = (
                    "fail"
                    if self.scenario in TASK_DIRECTION_MISMATCH_SCENARIOS
                    else "pass"
                )
            elif (
                self.scenario in VALIDATION_FINAL_REVIEW_SCENARIOS
                and node == "final-review"
                and item_id == "final-review-result"
            ):
                outcome = VALIDATION_FINAL_REVIEW_SCENARIOS[self.scenario][0]
            elif (
                self.scenario == "goal-operational-matrix" and node == "record-evidence"
            ):
                variant = GOAL_OPERATIONAL_VARIANTS[self.goal_evidence_round]
                outcome = (
                    variant[1] if item_id == "goal-verification-result" else variant[2]
                )
            elif (node == "verify" and not self.task_verification_reworked) or (
                self.scenario == "standard"
                and node == "record-evidence"
                and item_id == "goal-verification-result"
                and self.goal_evidence_round == 0
            ):
                outcome = "fail"
            elif (
                self.scenario == "standard"
                and node == "record-evidence"
                and item_id == "goal-review-readiness-result"
                and self.goal_evidence_round == 1
            ):
                outcome = "inconclusive"
            elif (
                self.scenario == "standard"
                and node == "record-low-disposition"
                and self.low_settlement_rounds.get(self.current_procedure_id, 0) == 0
            ):
                outcome = "fail"
            else:
                outcome = "pass"
            return {
                "type": "check_result",
                "operation_id": constraints["operation_id"],
                "operation_digest": constraints["operation_digest"],
                "input_basis": {
                    "descriptor": "isolated official-artifact qualification",
                    "digest": "sha256:" + hashlib.sha256(b"input").hexdigest(),
                },
                "executor": {"name": "aquarium", "version": "v0.1.12"},
                "outcome": outcome,
                "summary": f"caller-supplied {outcome} result",
                "output_digest": "sha256:"
                + hashlib.sha256(outcome.encode()).hexdigest(),
            }
        raise RuntimeQualificationError(f"unsupported required item type: {item_type}")

    def fill_action(self, observation: dict[str, Any], procedure_id: str) -> None:
        node = observation["guidance"]["node"]["graph_node_id"]
        if (
            self.scenario in {"low-blocker-wait", "validation-low-blocker-wait"}
            and node == "await-user-direction"
        ):
            self.low_blocker_readback_verified = False
            expected = low_blocker_fixture(self.scenario, self.fixture_target)
            source_basis = self.read_complete_evidence(
                observation, "record-low-disposition", "source-review-basis"
            )
            disposition = self.read_complete_evidence(
                observation, "record-low-disposition", "low-disposition-summary"
            )
            blockers = self.read_complete_evidence(
                observation, "record-low-disposition", "current-blocking-findings"
            )
            after_target = self.read_complete_evidence(
                observation, "record-low-disposition", "after-target"
            )
            assert_low_blocker_readback(
                expected, source_basis, disposition, blockers, after_target
            )
            self.low_blocker_readback_verified = True
        required = [
            item
            for item in observation["active_items"]
            if item.get("required_now") and not item.get("satisfied")
        ]
        if (
            procedure_id == "aquarium-task-v2"
            and node == "verify"
            and not self.task_verification_reworked
        ):
            check = next(item for item in required if item["type"] == "check_result")
            self.record(observation, {check["item_id"]: self.value_for(check, node)})
            missing = self.observe()
            failed = self.invoke_template(
                missing, "session.complete", expected_exit=None
            )
            observed_code = error_code(failed) if failed.returncode != 0 else None
            if failed.returncode == 0 or observed_code != "REQUIRED_ITEMS_MISSING":
                raise RuntimeQualificationError(
                    "conditional verification observations were not required: "
                    f"exit={failed.returncode}; code={observed_code!r}"
                )
            self.task_required_failure = True
            observations = next(
                item
                for item in missing["active_items"]
                if item["item_id"] == "verification-observations"
            )
            twenty = [f"observation-{index:02d}" for index in range(20)]
            self.record(
                missing,
                {observations["item_id"]: {"type": "list", "value": twenty}},
            )
            full = self.observe()
            code = self.try_record_failure(
                full,
                {
                    observations["item_id"]: {
                        "type": "list",
                        "value": [*twenty, "observation-20"],
                    }
                },
            )
            if code != "ITEM_CONSTRAINT_FAILED":
                raise RuntimeQualificationError(
                    f"list max_items overrun was not rejected: code={code!r}"
                )
            self.task_list_limit = True
            return
        current = observation
        for _ in range(10):
            required = [
                item
                for item in current["active_items"]
                if item.get("required_now") and not item.get("satisfied")
            ]
            route_qualification = ROUTE_QUALIFICATION_SCENARIOS.get(self.scenario)
            if (
                procedure_id == "aquarium-goal-v2"
                and node == "complete-work"
            ):
                required.extend(
                    item
                    for item in current["active_items"]
                    if item["item_id"]
                    in {
                        "review-route",
                        "review-target-scope",
                        "review-selection-summary",
                    }
                    and not item.get("satisfied")
                    and item not in required
                )
            if (
                self.scenario in GOAL_RECOVERY_SCENARIOS
                and procedure_id == "aquarium-goal-v2"
                and node == "record-evidence"
            ):
                required.extend(
                    item
                    for item in current["active_items"]
                    if item["item_id"]
                    in {"route-change-authority-reference", "route-direction"}
                    and not item.get("satisfied")
                    and item not in required
                )
            if (
                self.scenario == "medium-wait"
                and procedure_id == "aquarium-goal-v2"
                and node == "record-evidence"
                and self.goal_evidence_round > 0
            ):
                required.extend(
                    item
                    for item in current["active_items"]
                    if item["item_id"] == "extra-assessment-authority-reference"
                    and not item.get("satisfied")
                    and item not in required
                )
            if (
                self.scenario in VALIDATION_RECOVERY_SCENARIOS
                and procedure_id == "aquarium-validation-v2"
                and node == "final-review"
            ):
                required.extend(
                    item
                    for item in current["active_items"]
                    if item["item_id"] == "route-direction"
                    and not item.get("satisfied")
                    and item not in required
                )
            if route_qualification and route_qualification[1] == "waived":
                required.extend(
                    item
                    for item in current["active_items"]
                    if item["item_id"] == "waiver-summary"
                    and not item.get("satisfied")
                    and item not in required
                )
            records = {
                item["item_id"]: self.value_for(item, node)
                for item in required
                if item["type"] != "artifact"
            }
            if (
                self.scenario == "task-resume-active-mulgae"
                and node == "review"
                and any(
                    item["item_id"] == "waiver-summary"
                    for item in current["active_items"]
                )
            ):
                records["waiver-summary"] = None
            if not records:
                if (
                    self.scenario == "standard"
                    and procedure_id == "aquarium-validation-v2"
                    and node == "final-review"
                ):
                    audit_count = self.read_complete_evidence(
                        current,
                        "record-audit-low-basis",
                        "audit-low-finding-count",
                    )
                    audit_ids = self.read_complete_evidence(
                        current,
                        "record-audit-low-basis",
                        "audit-low-finding-identities",
                    )
                    audit_target = self.read_complete_evidence(
                        current, "record-audit-low-basis", "audit-basis-target"
                    )
                    if (
                        audit_count != 2
                        or audit_ids != ["audit:A1:L1", "audit:A1:L2"]
                        or audit_target != self.fixture_target
                    ):
                        raise RuntimeQualificationError(
                            "validation Low audit basis was not preserved exactly"
                        )
                    self.validation_source_basis_verified = True
                return
            self.record(current, records)
            current = self.observe()
        raise RuntimeQualificationError(
            "conditional action requirements did not converge"
        )

    def assess_goal(
        self, observation: dict[str, Any], *, status: str = "satisfied"
    ) -> dict[str, Any]:
        goal = observation["guidance"].get("goal", {})
        for criterion in goal.get("criteria", []):
            if criterion.get("status") != "unassessed":
                continue
            completed = self.invoke_template(
                observation,
                "goal.assess_criterion",
                {
                    "<status>": status,
                    "<reason>": f"official-artifact runtime criterion {status}",
                },
            )
            payload = json_payload(completed)
            result = payload.get("result")
            if (
                payload.get("schema") != OUTPUT_SCHEMA
                or not isinstance(result, dict)
                or result.get("schema") != "podway.criterion-assessment-result/v1"
            ):
                raise RuntimeQualificationError(
                    "criterion assessment result is invalid"
                )
            observation = self.observe()
        return observation

    def exercise_pagination(self) -> None:
        """Exercise bounded multi-page list readback outside canonical digests."""
        assert self.sandbox is not None
        source_path = self.procedures / "aquarium-task-v2.yaml"
        source = source_path.read_bytes()
        conditional_list = b"".join(
            [
                b"        required: false\n        required_when:\n",
                b"          - item: verification-result\n",
                b"            field: outcome\n",
                b"            not_equals: pass\n        min_items: 1\n",
                b"        max_items: 20\n        max_item_length: 1000\n",
                b"        max_total_length: 20000\n",
            ]
        )
        paged_list = b"".join(
            [
                b"        required: true\n        min_items: 1\n",
                b"        max_items: 300\n        max_item_length: 1000\n",
                b"        max_total_length: 300000\n",
            ]
        )
        replacements = (
            (b"id: aquarium-task-v2\n", b"id: aquarium-pagination-v2\n"),
            (conditional_list, paged_list),
        )
        for old, new in replacements:
            if source.count(old) != 1:
                raise RuntimeQualificationError("pagination fixture source drifted")
            source = source.replace(old, new, 1)
        fixture = self.sandbox / ".podway/procedures/aquarium-pagination-v2.yaml"
        fixture.write_bytes(source)
        relative = ".podway/procedures/aquarium-pagination-v2.yaml"
        preview = output_result(
            self.raw(["--json", "procedure", "preview", relative]),
            "procedure.preview",
            "podway.procedure-preview-result/v1",
        )
        digest = preview["procedure_digest"]
        started = json_payload(
            self.raw(
                [
                    "--json",
                    "start",
                    "--procedure",
                    relative,
                    "--expect-procedure-digest",
                    digest,
                    "--task",
                    "qualify bounded evidence pagination",
                ]
            )
        )
        if started.get("result", {}).get("session_state") != "prepared":
            raise RuntimeQualificationError("pagination fixture did not prepare")
        self.begin_goal(self.observe(), "aquarium-pagination-v2")

        for expected_node in (
            "record-plan",
            "prepare-implementation",
            "implement",
            "refine",
        ):
            observation = self.observe()
            if observation["guidance"]["node"]["graph_node_id"] != expected_node:
                raise RuntimeQualificationError("pagination fixture path drifted")
            self.fill_action(observation, "aquarium-pagination-v2")
            self.invoke_template(self.observe(), "session.complete")

        verification = self.observe()
        if verification["guidance"]["node"]["graph_node_id"] != "verify":
            raise RuntimeQualificationError(
                "pagination fixture omitted verify: "
                f"node={verification['guidance']['node']['graph_node_id']!r}"
            )
        entries = [f"entry-{index:03d}-" + "x" * 880 for index in range(300)]
        required = {item["item_id"]: item for item in verification["active_items"]}
        self.record(
            verification,
            {
                "verification-result": self.value_for(
                    required["verification-result"], "verify"
                ),
                "verification-observations": {"type": "list", "value": entries},
            },
        )
        self.invoke_template(self.observe(), "session.complete")
        decision = self.observe()
        self.old_page_token = self.read_evidence_page(
            decision, "verify", "verification-observations"
        )
        self.rework_to(decision, "verify")
        verification = self.observe()
        required = {item["item_id"]: item for item in verification["active_items"]}
        entries[-1] = entries[-1] + "changed"
        self.record(
            verification,
            {
                "verification-result": self.value_for(
                    required["verification-result"], "verify"
                ),
                "verification-observations": {"type": "list", "value": entries},
            },
        )
        self.invoke_template(self.observe(), "session.complete")
        self.assert_stale_evidence_page(
            self.observe(), "verify", "verification-observations"
        )
        terminal = self.observe()
        status = terminal["status"]
        self.raw(
            [
                "cancel",
                "--reason",
                "pagination seam qualified",
                "--if-workspace-uuid",
                self.workspace_uuid(terminal),
                "--if-session-id",
                status["session"]["id"],
                "--if-session-revision",
                str(status["session"]["revision"]),
                "--if-attempt",
                status["current"]["attempt"]["attempt_id"],
                "--idempotency-key",
                self.next_key("cancel-pagination"),
                "--json",
            ]
        )

    def read_evidence_page(
        self, observation: dict[str, Any], source: str, item: str
    ) -> str:
        status = observation["status"]
        result = output_result(
            self.raw(
                [
                    "--json",
                    "evidence",
                    "read",
                    "--source",
                    source,
                    "--item",
                    item,
                    "--if-workspace-uuid",
                    self.workspace_uuid(observation),
                    "--if-session-id",
                    status["session"]["id"],
                ]
            ),
            "evidence.read",
            "podway.evidence-read-result/v1",
        )
        token = result.get("next_page_token")
        if result.get("truncated") is not True or not isinstance(token, str):
            raise RuntimeQualificationError("large list evidence did not paginate")
        return token

    def assert_stale_evidence_page(
        self, observation: dict[str, Any], source: str, item: str
    ) -> None:
        assert self.old_page_token is not None
        status = observation["status"]
        failed = self.raw(
            [
                "--json",
                "evidence",
                "read",
                "--source",
                source,
                "--item",
                item,
                "--page-token",
                self.old_page_token,
                "--if-workspace-uuid",
                self.workspace_uuid(observation),
                "--if-session-id",
                status["session"]["id"],
            ],
            expected_exit=None,
        )
        if failed.returncode == 0 or error_code(failed) != "EVIDENCE_PAGE_TOKEN_STALE":
            raise RuntimeQualificationError(
                "old list evidence page token was not stale"
            )
        self.task_stale_token = True

    def drive_procedure(
        self, name: str, *, scenario: str = "standard"
    ) -> dict[str, Any] | None:
        assert self.sandbox is not None
        relative = f".podway/procedures/{name}"
        preview = output_result(
            self.raw(["--json", "procedure", "preview", relative]),
            "procedure.preview",
            "podway.procedure-preview-result/v1",
        )
        procedure_id = preview["procedure_id"]
        self.current_procedure_id = procedure_id
        self.scenario = scenario
        route_qualification = ROUTE_QUALIFICATION_SCENARIOS.get(scenario)
        qualified_route = route_qualification[1] if route_qualification else None
        if route_qualification and route_qualification[0] != procedure_id:
            raise RuntimeQualificationError(
                f"route scenario {scenario!r} does not target {procedure_id!r}"
            )
        self.node_visits = {}
        if scenario in {"goal-hardening-defer", "medium-wait"}:
            self.completed_assessments[procedure_id] = 1
        digest = preview["procedure_digest"]
        suggestion = preview.get("start_suggestion", {}).get("argv")
        expected = [
            "podway",
            "start",
            "--procedure",
            relative,
            "--expect-procedure-digest",
            digest,
            "--task",
            "<title>",
        ]
        if suggestion != expected:
            raise RuntimeQualificationError(
                "preview omitted the exact digest-fenced start"
            )
        start = ["--json", "start", *suggestion[2:]]
        start[start.index("<title>")] = f"qualification {procedure_id}"
        start_payload = json_payload(self.raw(start))
        started = start_payload.get("result")
        if (
            start_payload.get("schema") != OUTPUT_SCHEMA
            or start_payload.get("command")
            not in {"session.start", "session.start_replace"}
            or not isinstance(started, dict)
            or started.get("schema") != "podway.session-start-result/v3"
        ):
            raise RuntimeQualificationError("digest-fenced start result is invalid")
        if started.get("session_state") != "prepared":
            raise RuntimeQualificationError("digest-fenced start was not prepared")
        prepared = self.observe()
        self.begin_goal(prepared, procedure_id)
        installed = self.sandbox / relative
        if procedure_id == "aquarium-task-v2":
            installed.write_bytes(
                installed.read_bytes() + b"unknown_runtime_field: true\n"
            )

        for _ in range(100):
            observation = self.observe()
            status = observation["status"]
            if status["procedure"]["digest"] != digest:
                raise RuntimeQualificationError(
                    "active Procedure snapshot digest changed"
                )
            if status["session"]["lifecycle"] == "completed":
                if procedure_id == "aquarium-task-v2":
                    self.task_snapshot_immutable = True
                break
            node = observation["guidance"]["node"]["graph_node_id"]
            node_type = observation["guidance"]["node"]["node_type"]
            self.node_visits[node] = self.node_visits.get(node, 0) + 1
            task_resume = TASK_RESUME_SCENARIOS.get(scenario)
            if (
                task_resume
                and not task_resume.get("completed_transition")
                and node == "review"
                and self.node_visits[node] == 2
            ):
                route = task_resume["route"]
                expected_entry = f"enter-{route}-review-route"
                wrong_entries = {
                    f"enter-{provider}-review-route"
                    for provider in {"mulgae", "orca", "native-codex"} - {route}
                    if self.node_visits.get(f"enter-{provider}-review-route", 0)
                }
                if self.node_visits.get(expected_entry) != 2 or wrong_entries:
                    raise RuntimeQualificationError(
                        "resume did not preserve the exact provider entry: "
                        f"expected={expected_entry!r}; wrong={sorted(wrong_entries)!r}"
                    )
                return {
                    "scenario": scenario,
                    "procedure_id": procedure_id,
                    "node": node,
                    "lifecycle": status["session"]["lifecycle"],
                    "same_provider_resume": route,
                }
            if (
                scenario == "task-confirmation-only-wait"
                and node == "choose-user-direction"
                and not self.task_one_shot_decision_used
            ):
                if (
                    node_type != "decision"
                    or status["session"]["lifecycle"] != "running"
                    or self.node_visits.get("decide-task-rework-authority") != 1
                ):
                    raise RuntimeQualificationError(
                        "task one-shot authorization did not begin at a fresh active decision"
                    )
                decision = self.decide(observation, "fix-and-review")
                self.decision_destination(decision, "decide-implementation-owner")
                self.task_one_shot_decision_used = True
                continue
            if scenario in STOP_EVIDENCE_SCENARIOS and node == "choose-user-direction":
                decision = self.decide(observation, "stop")
                expected_destination = (
                    "record-stopped"
                    if procedure_id == "aquarium-validation-v2"
                    else "confirm-stopped-goal-assessment-core"
                    if procedure_id == "aquarium-task-v2"
                    else "record-stopped-goal-boundary"
                )
                self.decision_destination(decision, expected_destination)
                continue
            if (
                scenario == "medium-wait"
                and node == "choose-user-direction"
                and not self.goal_one_shot_decision_used
            ):
                if (
                    node_type != "decision"
                    or status["session"]["lifecycle"] != "running"
                    or self.node_visits.get("decide-goal-rework-authority") != 1
                ):
                    raise RuntimeQualificationError(
                        "goal one-shot authorization did not begin at a fresh active decision"
                    )
                decision = self.decide(observation, "fix-and-review")
                self.decision_destination(decision, "complete-work")
                self.goal_one_shot_decision_used = True
                continue
            if scenario != "standard" and node == "choose-user-direction":
                if (
                    node_type != "decision"
                    or status["session"]["lifecycle"] != "running"
                ):
                    raise RuntimeQualificationError(
                        "user-direction scenario did not stop at an active choice: "
                        f"node_type={node_type!r}; "
                        f"lifecycle={status['session']['lifecycle']!r}"
                    )
                if scenario == "low-blocker-wait":
                    if not self.low_blocker_readback_verified:
                        raise RuntimeQualificationError(
                            "goal Low blocker wait skipped evidence readback"
                        )
                    self.mark_case_variant("C-08", "goal-low-blocker-wait")
                elif scenario == "validation-low-blocker-wait":
                    if not self.low_blocker_readback_verified:
                        raise RuntimeQualificationError(
                            "validation Low blocker wait skipped evidence readback"
                        )
                    self.mark_case_variant("C-08", "validation-low-blocker-wait")
                elif scenario == "medium-wait":
                    if (
                        not self.goal_one_shot_decision_used
                        or self.node_visits.get("choose-user-direction") != 2
                        or self.node_visits.get("decide-goal-rework-authority") != 2
                        or self.node_visits.get("complete-work") != 2
                    ):
                        raise RuntimeQualificationError(
                            "goal hardening authority was not consumed exactly once"
                        )
                    self.mark_case_variant("C-10", "goal-medium-wait")
                elif scenario == "validation-medium-wait":
                    self.mark_case_variant("C-10", "validation-medium-wait")
                elif scenario == "task-confirmation-only-wait":
                    if (
                        not self.task_one_shot_decision_used
                        or self.node_visits.get("choose-user-direction") != 2
                        or self.node_visits.get("decide-task-rework-authority") != 2
                        or self.node_visits.get("decide-implementation-owner") != 1
                    ):
                        raise RuntimeQualificationError(
                            "task confirmation-only authority was not consumed exactly once"
                        )
                    self.mark_case_variant("C-10", "task-confirmation-only-wait")
                elif scenario == "goal-closeout-unmet-wait":
                    if self.node_visits.get("decide-goal-rework-authority") != 1:
                        raise RuntimeQualificationError(
                            "goal closeout completion gap skipped its authority gate"
                        )
                    self.mark_case_variant("C-10", "goal-closeout-unmet-wait")
                else:
                    raise RuntimeQualificationError(
                        f"unexpected user-direction scenario: {scenario}"
                    )
                return {
                    "scenario": scenario,
                    "procedure_id": procedure_id,
                    "node": node,
                    "lifecycle": status["session"]["lifecycle"],
                    "decision_unset": True,
                    "one_shot_decision_used": (
                        self.task_one_shot_decision_used
                        or self.goal_one_shot_decision_used
                    ),
                }
            if node_type == "action":
                self.fill_action(observation, procedure_id)
                ready = self.observe()
                completed = self.invoke_template(ready, "session.complete")
                payload = json_payload(completed)
                result = payload.get("result")
                if (
                    payload.get("schema") != OUTPUT_SCHEMA
                    or not isinstance(result, dict)
                    or result.get("schema") != "podway.stage-transition-result/v2"
                ):
                    raise RuntimeQualificationError(
                        "action transition result is invalid"
                    )
                if procedure_id == "aquarium-goal-v2" and node == "record-evidence":
                    self.goal_evidence_round += 1
                if procedure_id == "aquarium-validation-v2" and node == "final-review":
                    self.validation_review_round += 1
                if node == "record-low-disposition":
                    self.low_settlement_rounds[procedure_id] = (
                        self.low_settlement_rounds.get(procedure_id, 0) + 1
                    )
                continue
            if node_type != "decision":
                raise RuntimeQualificationError(
                    f"unsupported graph node type: {node_type}"
                )

            if (
                task_resume
                and scenario in TASK_DIRECTION_MISMATCH_SCENARIOS
                and node == task_resume["rejection_node"]
            ):
                self.reject_guarded_decision(
                    observation, task_resume["rejection_option"]
                )
                if self.node_visits.get("review", 0) > (
                    0
                    if task_resume.get("planned_only")
                    or task_resume.get("completed_transition")
                    else 1
                ):
                    raise RuntimeQualificationError(
                        "direction mismatch reached provider or waiver review"
                    )
                return {
                    "scenario": scenario,
                    "procedure_id": procedure_id,
                    "node": node,
                    "lifecycle": status["session"]["lifecycle"],
                    "guard_rejected": task_resume["rejection_option"],
                    "before_provider_or_waiver_review": True,
                    "state_unchanged": True,
                }

            if task_resume and node == "choose-review-route-direction":
                if scenario in {
                    "task-current-only-switch-rejected",
                    "task-current-only-waive-rejected",
                }:
                    self.reject_guarded_decision(observation, "continue")
                    return {
                        "scenario": scenario,
                        "procedure_id": procedure_id,
                        "node": node,
                        "lifecycle": status["session"]["lifecycle"],
                        "guard_rejected": task_resume["direction"],
                        "state_unchanged": True,
                    }
                decision = self.decide(observation, "continue")
                self.decision_destination(decision, "prepare-review")
                continue

            if task_resume and node == "authorize-current-review-route-resume":
                route = task_resume["route"]
                if scenario == "task-resume-active-mulgae":
                    observation = self.reject_guarded_decision(observation, "orca")
                decision = self.decide(observation, route)
                self.decision_destination(decision, f"enter-{route}-review-route")
                continue

            if (
                scenario in TASK_COMPLETED_CHANGE_SUCCESS_SCENARIOS
                and node == "confirm-assessment-ordinal"
            ):
                transition = TASK_RESUME_SCENARIOS[scenario]
                target_route = transition["effective_route"]
                prior_ordinal = self.read_complete_evidence(
                    observation, "prepare-review", "prior-assessment-ordinal"
                )
                current_ordinal = self.read_complete_evidence(
                    observation, "review", "assessment-ordinal"
                )
                if (
                    self.node_visits.get("validate-review-route-entry") != 1
                    or self.node_visits.get("classify-review-route-change") != 1
                    or self.node_visits.get("authorize-completed-review-route") != 1
                    or self.node_visits.get(f"enter-{target_route}-review-route") != 1
                    or self.node_visits.get("review") != 1
                    or prior_ordinal != 1
                    or current_ordinal != 2
                ):
                    raise RuntimeQualificationError(
                        "completed-checkpoint transition skipped entry, "
                        "classification, authorization, or next-ordinal guards: "
                        f"scenario={scenario!r}; prior={prior_ordinal!r}; "
                        f"current={current_ordinal!r}; visits={self.node_visits!r}"
                    )
                decision = self.decide(observation, "standard")
                self.decision_destination(decision, "confirm-first-review-evidence")
                return {
                    "scenario": scenario,
                    "procedure_id": procedure_id,
                    "node": node,
                    "lifecycle": status["session"]["lifecycle"],
                    "completed_checkpoint_transition": target_route,
                    "prior_ordinal": prior_ordinal,
                    "current_ordinal": current_ordinal,
                }

            if (
                procedure_id == "aquarium-task-v2"
                and node == "decide-verification"
                and not self.task_verification_reworked
            ):
                observation = self.reject_guarded_decision(observation, "passed")
                self.task_guard_failure = True
                self.decide(observation, "failed")
                self.task_verification_reworked = True
                continue

            if (
                procedure_id == "aquarium-task-v2"
                and node == "assess-goal"
                and not self.task_evidence_reworked
            ):
                self.rework_to(observation, "implement")
                self.task_evidence_reworked = True
                continue

            if (
                procedure_id == "aquarium-task-v2"
                and node == "decide-backend-check"
                and not self.task_review_reworked
                and scenario == "standard"
            ):
                observation = self.reject_guarded_decision(observation, "passed")
                self.task_review_guard_failure = True
                self.decide(observation, "failed")
                self.task_review_reworked = True
                continue

            if (
                procedure_id == "aquarium-task-v2"
                and node == "decide-review"
                and not self.task_medium_reworked
                and scenario == "standard"
            ):
                self.decide(observation, "blocking")
                continue

            if (
                procedure_id == "aquarium-task-v2"
                and node == "decide-implementation-owner"
                and scenario == "standard"
                and self.node_visits.get("review") == 1
            ):
                self.decide(observation, "required")
                continue

            if (
                procedure_id == "aquarium-task-v2"
                and node == "decide-implementation-owner"
                and not self.task_medium_reworked
                and "required" in observation["guidance"]["allowed_option_ids"]
                and scenario in {"standard", "task-completion-mixed-owners"}
            ):
                self.decide(observation, "required")
                self.task_medium_reworked = True
                continue

            if (
                scenario in TASK_CONFIRMATION_SCENARIOS
                and node == "decide-implementation-owner"
            ):
                self.decide(observation, "required")
                continue

            if (
                scenario == "task-completion-unverified"
                and node == "confirm-review-completion"
                and self.node_visits.get("review") == 2
            ):
                observation = self.reject_guarded_decision(observation, "complete")
                self.decide(observation, "unverified")
                continue

            if (
                scenario == "task-completion-mixed-owners"
                and node == "confirm-review-completion"
                and self.node_visits.get("review") == 2
            ):
                observation = self.reject_guarded_decision(observation, "complete")
                self.decide(observation, "unmet")
                continue

            if (
                scenario
                in {
                    *TASK_OWNER_SCENARIOS,
                    "task-completion-owner-inconsistent",
                }
                and node == "confirm-review-completion"
                and self.node_visits.get("review") == 2
            ):
                observation = self.reject_guarded_decision(observation, "complete")
                self.decide(observation, "unmet")
                continue

            if (
                scenario in TASK_CONFIRMATION_SCENARIOS
                and node == "confirm-review-completion"
                and self.node_visits.get("review") in {2, 3}
            ):
                observation = self.reject_guarded_decision(observation, "complete")
                self.decide(observation, "unmet")
                continue

            if (
                scenario in TASK_CONFIRMATION_SCENARIOS
                and node == "decide-task-rework-authority"
            ):
                observation = self.reject_guarded_decision(observation, "remediation")
                self.decide(observation, "user-direction")
                continue

            if (
                scenario == "task-finding-inconsistent"
                and node == "decide-review"
                and self.node_visits.get("review") == 2
            ):
                observation = self.reject_guarded_decision(observation, "clean")
                observation = self.reject_guarded_decision(
                    observation, "low-disposition"
                )
                self.decide(observation, "inconsistent")
                continue

            if (
                scenario in COMPLETION_GAP_SCENARIOS
                and node == "confirm-completion-assessment"
                and self.node_visits.get(node) == 1
            ):
                _expected_procedure, gap = COMPLETION_GAP_SCENARIOS[scenario]
                observation = self.reject_guarded_decision(observation, "complete")
                self.decide(observation, gap)
                continue

            if (
                scenario in GOAL_CLOSEOUT_GAP_SCENARIOS
                and node == "confirm-completion-assessment"
            ):
                observation = self.reject_guarded_decision(observation, "complete")
                self.decide(observation, "unmet")
                continue

            if (
                procedure_id == "aquarium-goal-v2"
                and node == "decide-review-basis"
                and scenario
                in {"goal-kind-member-closeout", "goal-kind-prevalidation-closeout"}
                and self.goal_evidence_round == 1
            ):
                observation = self.reject_guarded_decision(
                    observation, "final-closeout"
                )
                invalid = self.decide(observation, "invalid-substitute")
                self.decision_destination(invalid, "record-evidence")
                continue

            if (
                scenario in GOAL_CLOSEOUT_GAP_SCENARIOS
                and node == "decide-review-basis"
            ):
                self.decide(observation, "final-closeout")
                continue

            if (
                scenario == "validation-stop-preserves-completion"
                and node == "confirm-completion-assessment"
            ):
                observation = self.reject_guarded_decision(observation, "complete")
                self.decide(observation, "unmet")
                continue

            if (
                scenario == "goal-finding-inconsistent"
                and node == "decide-evidence"
                and self.goal_evidence_round == 1
            ):
                observation = self.reject_guarded_decision(observation, "clean")
                observation = self.reject_guarded_decision(observation, "low-only")
                self.decide(observation, "inconsistent")
                continue

            if (
                scenario == "standard"
                and procedure_id == "aquarium-goal-v2"
                and node == "decide-operational-evidence"
            ):
                if self.goal_evidence_round == 1:
                    observation = self.reject_guarded_decision(observation, "passed")
                    self.decide(observation, "verification-incomplete")
                    continue
                if self.goal_evidence_round == 2:
                    observation = self.reject_guarded_decision(observation, "passed")
                    self.decide(observation, "review-incomplete")
                    continue

            if (
                scenario == "goal-operational-matrix"
                and procedure_id == "aquarium-goal-v2"
                and node == "decide-operational-evidence"
            ):
                variant, _verification, _review, expected_option = (
                    GOAL_OPERATIONAL_VARIANTS[self.goal_evidence_round - 1]
                )
                if expected_option != "passed":
                    observation = self.reject_guarded_decision(observation, "passed")
                    failure = self.decide(observation, expected_option)
                    expected_destination = (
                        "complete-work"
                        if expected_option == "verification-incomplete"
                        else "record-evidence"
                    )
                    self.decision_destination(failure, expected_destination)
                    case_id = (
                        "C-04"
                        if expected_option == "verification-incomplete"
                        else "C-05"
                    )
                    self.mark_case_variant(case_id, variant)
                    continue

            if (
                scenario in VALIDATION_FINAL_REVIEW_SCENARIOS
                and procedure_id == "aquarium-validation-v2"
            ):
                expected_outcome, expected_gaps, expected_option = (
                    VALIDATION_FINAL_REVIEW_SCENARIOS[scenario]
                )
                if node == "decide-final-review-readiness":
                    actual_outcome = self.read_complete_evidence(
                        observation, "final-review", "final-review-result"
                    ).get("outcome")
                    if actual_outcome != expected_outcome:
                        raise RuntimeQualificationError(
                            "validation final-review operation evidence changed"
                        )
                if (
                    node == "decide-final-review-readiness"
                    and expected_outcome != "pass"
                ):
                    observation = self.reject_guarded_decision(observation, "passed")
                    decision = self.decide(observation, "incomplete")
                    self.decision_destination(
                        decision, "record-review-operation-incomplete"
                    )
                    self.mark_case_variant("C-16", scenario)
                    continue
                if node == "decide-required-evidence" and expected_gaps is not None:
                    actual_gaps = self.read_complete_evidence(
                        observation, "final-review", "required-evidence-gaps"
                    )
                    if actual_gaps != expected_gaps:
                        raise RuntimeQualificationError(
                            "validation required-evidence fixture changed"
                        )
                if (
                    node == "decide-required-evidence"
                    and expected_gaps is not None
                    and expected_gaps > 0
                ):
                    observation = self.reject_guarded_decision(observation, "complete")
                    decision = self.decide(observation, "incomplete")
                    self.decision_destination(decision, "record-incomplete")
                    self.mark_case_variant("C-16", scenario)
                    continue
                if node == "decide-final-review" and expected_option == "validated":
                    decision = self.decide(observation, "validated")
                    self.decision_destination(decision, "confirm-goal-assessment-core")
                    self.mark_case_variant("C-16", scenario)
                    continue

            if (
                scenario == "standard"
                and node == "decide-low-result"
                and self.low_settlement_rounds.get(procedure_id) == 1
            ):
                observation = self.reject_guarded_decision(observation, "passed")
                self.decide(observation, "incomplete")
                self.mark_case_variant("C-06", procedure_id)
                continue

            if (
                scenario == "standard"
                and node == "decide-low-completion"
                and self.low_settlement_rounds.get(procedure_id) == 2
            ):
                observation = self.reject_guarded_decision(observation, "completed")
                self.decide(observation, "incomplete")
                self.mark_case_variant("C-07", procedure_id)
                continue

            if node in {"assess-goal", "assess-stopped-goal"}:
                if scenario in STOP_EVIDENCE_SCENARIOS:
                    expected_procedure, completion_source = STOP_EVIDENCE_SCENARIOS[
                        scenario
                    ]
                    if procedure_id != expected_procedure:
                        raise RuntimeQualificationError(
                            "stop-evidence scenario used the wrong Procedure"
                        )
                    summary = self.read_complete_evidence(
                        observation,
                        completion_source,
                        "completion-assessment-summary",
                    )
                    unmet = self.read_complete_evidence(
                        observation,
                        completion_source,
                        "completion-unmet-criteria",
                    )
                    unverified = self.read_complete_evidence(
                        observation,
                        completion_source,
                        "completion-unverified-criteria",
                    )
                    direction = self.read_complete_evidence(
                        observation,
                        "await-user-direction",
                        "direction-classification",
                    )
                    direction_summary = self.read_complete_evidence(
                        observation,
                        "await-user-direction",
                        "direction-summary",
                    )
                    if (
                        not summary
                        or unmet != 1
                        or unverified != 0
                        or not direction
                        or not direction_summary
                    ):
                        raise RuntimeQualificationError(
                            "stop path lost completion evidence or user direction"
                        )
                    if procedure_id != "aquarium-validation-v2":
                        consistency = self.read_complete_evidence(
                            observation,
                            completion_source,
                            "finding-count-consistency",
                        )
                        if consistency != "consistent":
                            raise RuntimeQualificationError(
                                "stop path lost finding-count consistency"
                            )
                    rejected_option = (
                        "invalid-not-stopped"
                        if procedure_id == "aquarium-task-v2"
                        else "achieved"
                    )
                    observation = self.reject_guarded_decision(
                        observation, rejected_option
                    )
                    self.mark_case_variant("C-10", scenario)
                if (
                    scenario == "task-completion-unverified"
                    and self.node_visits.get("review", 0) < 3
                ):
                    raise RuntimeQualificationError(
                        "unverified completion did not return to fresh review evidence"
                    )
                if scenario == "task-completion-mixed-owners" and (
                    self.node_visits.get("decide-implementation-owner") != 1
                    or self.node_visits.get("decide-verification-owner", 0) != 0
                    or self.node_visits.get("decide-documentation-owner", 0) != 0
                ):
                    raise RuntimeQualificationError(
                        "mixed task owners did not route to implementation first"
                    )
                if scenario in TASK_OWNER_SCENARIOS:
                    expected_node = {
                        "implementation-rework-obligations": "decide-implementation-owner",
                        "verification-rework-obligations": "decide-verification-owner",
                        "documentation-rework-obligations": "decide-documentation-owner",
                    }[TASK_OWNER_SCENARIOS[scenario]]
                    if self.node_visits.get(expected_node) != 1:
                        raise RuntimeQualificationError(
                            f"{scenario} did not visit its sole owner gate"
                        )
                if scenario == "task-completion-owner-inconsistent" and (
                    self.node_visits.get("decide-implementation-owner") != 1
                    or self.node_visits.get("decide-verification-owner") != 1
                    or self.node_visits.get("decide-documentation-owner") != 1
                    or self.node_visits.get("review", 0) < 3
                ):
                    raise RuntimeQualificationError(
                        "ownerless task completion gap did not return to review"
                    )
                if (
                    scenario == "task-finding-inconsistent"
                    and self.node_visits.get("review", 0) < 3
                ):
                    raise RuntimeQualificationError(
                        "inconsistent task finding evidence did not return to review"
                    )
                if (
                    scenario == "goal-finding-inconsistent"
                    and self.node_visits.get("record-evidence", 0) < 2
                ):
                    raise RuntimeQualificationError(
                        "inconsistent goal finding evidence did not return to evidence"
                    )
                if scenario == "goal-hardening-defer" and (
                    self.node_visits.get("record-hardening-deferral") != 1
                    or self.node_visits.get("decide-low-handling") != 1
                    or self.node_visits.get("confirm-hardening-review-eligibility") != 1
                    or self.node_visits.get("confirm-hardening-record") != 1
                    or self.node_visits.get("record-hardening-handoff") != 1
                ):
                    raise RuntimeQualificationError(
                        "goal hardening deferral did not traverse its complete handoff"
                    )
                if (
                    scenario == "standard"
                    and procedure_id == "aquarium-validation-v2"
                    and procedure_id in self.low_settlement_procedures
                ):
                    if not self.validation_source_basis_verified:
                        raise RuntimeQualificationError(
                            "validation settlement lost its source audit basis"
                        )
                    obligations = json.loads(
                        self.read_complete_evidence(
                            observation,
                            "final-review",
                            "applicable-obligation-summary",
                        )
                    )
                    provider_count = self.read_complete_evidence(
                        observation, "final-review", "low-findings"
                    )
                    settlement = json.loads(
                        self.read_complete_evidence(
                            observation,
                            "record-low-disposition",
                            "low-disposition-summary",
                        )
                    )
                    pending = self.read_complete_evidence(
                        observation,
                        "record-low-disposition",
                        "pending-low-dispositions",
                    )
                    blockers = self.read_complete_evidence(
                        observation,
                        "record-low-disposition",
                        "current-blocking-findings",
                    )
                    before_target = self.read_complete_evidence(
                        observation, "record-low-disposition", "before-target"
                    )
                    after_target = self.read_complete_evidence(
                        observation, "record-low-disposition", "after-target"
                    )
                    expected_ids = ["audit:A1:L1", "audit:A1:L2"]
                    if self.run_index == 2:
                        expected_ids.append("provider:R1:L1")
                    disposition_ids = [
                        item["id"] for item in settlement["dispositions"]
                    ]
                    if (
                        obligations.get("audit_count") != 2
                        or obligations.get("provider_count") != provider_count
                        or obligations.get("pending_low_ids") != expected_ids
                        or disposition_ids != expected_ids
                        or pending != 0
                        or blockers != 0
                        or before_target != self.fixture_target
                        or after_target != self.fixture_target
                        or self.node_visits.get("audit") != 1
                        or self.node_visits.get("re-audit", 0) != 0
                        or self.node_visits.get("final-review") != 1
                    ):
                        raise RuntimeQualificationError(
                            "completed validation settlement changed its source obligations: "
                            f"obligations={obligations!r}; dispositions={disposition_ids!r}; "
                            f"pending={pending!r}; blockers={blockers!r}; "
                            f"targets={(before_target, after_target)!r}; "
                            f"fixture_target={self.fixture_target!r}; "
                            f"node_visits={self.node_visits!r}"
                        )
                    case_id = "C-02" if self.run_index == 2 else "C-01"
                    variant = (
                        "audit-2-provider-1"
                        if self.run_index == 2
                        else "audit-2-provider-0"
                    )
                    self.mark_case_variant(case_id, variant)
                if scenario == "goal-operational-matrix":
                    self.mark_case_variant("C-04", "verification-pass-review-pass")
                    self.mark_case_variant("C-05", "verification-pass-review-pass")
                if scenario in GOAL_KIND_SCENARIOS:
                    self.mark_case_variant("C-09", scenario)
                observation = self.assess_goal(
                    observation,
                    status=(
                        "unsatisfied"
                        if scenario in STOP_EVIDENCE_SCENARIOS
                        else "satisfied"
                    ),
                )
            special_option = None
            if (
                scenario == "standard"
                and procedure_id == "aquarium-validation-v2"
                and node == "decide-final-review"
            ):
                final_result = self.read_complete_evidence(
                    observation, "final-review", "final-review-result"
                )
                pending = self.read_complete_evidence(
                    observation,
                    "final-review",
                    "pending-applicable-low-dispositions",
                )
                blockers = self.read_complete_evidence(
                    observation, "final-review", "current-applicable-blockers"
                )
                gaps = self.read_complete_evidence(
                    observation, "final-review", "required-evidence-gaps"
                )
                obligations = json.loads(
                    self.read_complete_evidence(
                        observation,
                        "final-review",
                        "applicable-obligation-summary",
                    )
                )
                expected_pending = 3 if self.run_index == 2 else 2
                if (
                    final_result.get("outcome") != "pass"
                    or pending != expected_pending
                    or blockers != 0
                    or gaps != 0
                    or obligations.get("audit_low_ids")
                    != ["audit:A1:L1", "audit:A1:L2"]
                    or obligations.get("provider_low_ids")
                    != (["provider:R1:L1"] if self.run_index == 2 else [])
                ):
                    raise RuntimeQualificationError(
                        "validation final-review fixture did not establish the intended basis"
                    )
                observation = self.reject_guarded_decision(observation, "validated")
            if (
                scenario
                in {
                    "low-blocker-wait",
                    "validation-low-blocker-wait",
                }
                and node == "decide-low-completion"
            ):
                observation = self.reject_guarded_decision(observation, "completed")
                special_option = "blocker-found"
            elif scenario == "medium-wait" and node == "decide-evidence":
                special_option = "blocking"
            elif node == "decide-goal-rework-authority" and scenario in {
                "medium-wait",
                "goal-closeout-unmet-wait",
                "goal-stop-preserves-completion",
            }:
                observation = self.reject_guarded_decision(observation, "remediation")
                special_option = "user-direction"
            elif (
                procedure_id == "aquarium-goal-v2"
                and node == "decide-goal-rework-authority"
            ):
                observation = self.reject_guarded_decision(
                    observation, "user-direction"
                )
            elif scenario == "goal-hardening-defer" and node == "decide-evidence":
                special_option = "low-only"
            elif scenario == "goal-hardening-defer" and node == "decide-low-handling":
                special_option = "defer"
            elif (
                scenario == "validation-medium-wait"
                and node == "decide-current-blockers"
            ):
                special_option = "blocking"
            elif (
                scenario == "validation-medium-wait"
                and node == "decide-validation-rework-authority"
            ):
                special_option = "user-direction"
            elif (
                scenario == "validation-stop-preserves-completion"
                and node == "decide-validation-rework-authority"
            ):
                observation = self.reject_guarded_decision(observation, "remediation")
                special_option = "user-direction"
            elif (
                scenario in TASK_OWNER_SCENARIOS
                and node
                == {
                    "implementation-rework-obligations": "decide-implementation-owner",
                    "verification-rework-obligations": "decide-verification-owner",
                    "documentation-rework-obligations": "decide-documentation-owner",
                }[TASK_OWNER_SCENARIOS[scenario]]
            ):
                special_option = "required"
            elif (scenario == "validation-medium-wait" and node == "decide-gaps") or (
                (
                    scenario == "goal-operational-matrix"
                    or scenario in GOAL_KIND_SCENARIOS
                )
                and node == "decide-evidence"
            ):
                special_option = "clean"
            elif (
                scenario == "goal-kind-epic-closeout" and node == "decide-review-basis"
            ):
                special_option = "final-closeout"
            elif scenario in STOP_EVIDENCE_SCENARIOS and node in {
                "assess-goal",
                "assess-stopped-goal",
            }:
                special_option = "not-achieved"
            elif (
                scenario == "standard"
                and procedure_id == "aquarium-task-v2"
                and node == "confirm-first-review-evidence"
                and not self.task_review_reworked
            ):
                special_option = "mulgae"
            elif (
                procedure_id == "aquarium-task-v2"
                and node == "confirm-assessment-ordinal"
            ):
                ordinal = self.node_visits.get("review", 1)
                special_option = "standard" if ordinal <= 4 else "authorized-extra"
            elif task_resume and node == "validate-review-route-entry":
                special_option = (
                    "changed"
                    if (
                        task_resume.get("completed_transition")
                        or self.node_visits.get("prepare-review", 0) > 1
                    )
                    and task_resume.get("checkpoint_basis")
                    in {"explicit-route-change", "explicit-waiver"}
                    else "resumed"
                    if self.node_visits.get("prepare-review", 0) > 1
                    else "planned"
                )
            elif task_resume and node == "authorize-planned-review-route":
                special_option = f"planned-{task_resume['route']}"
            elif task_resume and node == "classify-review-route-change":
                special_option = (
                    "completed"
                    if task_resume.get("completed_transition")
                    else "unsettled"
                )
            elif task_resume and node == "confirm-review-route-change-readiness":
                special_option = "safe"
            elif task_resume and node == "authorize-incomplete-review-route":
                target_route = task_resume.get("effective_route", task_resume["route"])
                special_option = (
                    "changed-waiver"
                    if target_route == "waived"
                    else f"changed-{target_route}"
                )
            elif task_resume and node == "authorize-completed-review-route":
                target_route = task_resume.get("effective_route", task_resume["route"])
                special_option = (
                    "completed-change-waiver"
                    if target_route == "waived"
                    else f"completed-change-{target_route}"
                )
            elif task_resume and node == "confirm-review-route-binding":
                special_option = (
                    task_resume.get("effective_route", task_resume["route"])
                    if task_resume.get("completed_transition")
                    or self.node_visits.get("review", 0) > 1
                    else task_resume["route"]
                )
            elif (
                task_resume
                and node.startswith("decide-")
                and node.endswith("-review-operation")
            ):
                special_option = (
                    "assessed"
                    if task_resume.get("completed_transition")
                    else "unsettled"
                )
            elif task_resume and node == "confirm-incomplete-review-evidence":
                special_option = (
                    "mulgae" if task_resume["route"] == "mulgae" else "static-delegated"
                )
            elif (
                task_resume
                and task_resume.get("completed_transition")
                and node
                in {"confirm-first-review-evidence", "confirm-extra-review-evidence"}
            ):
                target_route = (
                    task_resume.get("effective_route", task_resume["route"])
                    if task_resume.get("completed_transition")
                    or self.node_visits.get("review", 0) > 1
                    else task_resume["route"]
                )
                special_option = (
                    "mulgae"
                    if target_route == "mulgae"
                    else "waived"
                    if target_route == "waived"
                    else "static-delegated"
                )
            elif (
                procedure_id == "aquarium-goal-v2"
                and node == "confirm-review-route-binding"
            ):
                special_option = "planned-mulgae"
            if scenario in GOAL_RECOVERY_SCENARIOS:
                if node == "confirm-review-route-binding":
                    planned_route = self.read_complete_evidence(
                        observation, "complete-work", "review-route"
                    )
                    current_route = self.read_complete_evidence(
                        observation, "record-evidence", "review-route"
                    )
                    if planned_route != "mulgae" or current_route != "orca":
                        raise RuntimeQualificationError(
                            "Goal recovery changed its planned or current provider: "
                            f"planned={planned_route!r}; current={current_route!r}"
                        )
                    if self.goal_evidence_round == 2 and (
                        self.node_visits.get("decide-changed-orca-review-operation")
                        != 1
                        or self.node_visits.get("confirm-incomplete-route-evidence")
                        != 1
                        or self.node_visits.get(
                            "choose-terminal-review-route-direction"
                        )
                        != 1
                    ):
                        raise RuntimeQualificationError(
                            "Goal resume did not preserve the immediately preceding Orca operation"
                        )
                    special_option = "changed-orca"
                elif node == "decide-changed-orca-review-operation":
                    special_option = (
                        "unsuccessful" if self.goal_evidence_round == 1 else "completed"
                    )
                elif node == "confirm-incomplete-route-evidence":
                    special_option = "orca"
                elif node == "confirm-orca-review-route-settlement":
                    special_option = "terminal-safe"
                elif node == "choose-terminal-review-route-direction":
                    special_option = "resume-current"
                elif node == "confirm-completed-assessment-ordinal":
                    special_option = "first"
                elif node == "confirm-first-route-evidence":
                    special_option = "orca"
            if scenario in VALIDATION_RECOVERY_SCENARIOS:
                if node == "confirm-final-review-route-binding":
                    planned_route = self.read_complete_evidence(
                        observation, "capture-baseline", "review-route"
                    )
                    current_route = self.read_complete_evidence(
                        observation, "final-review", "review-route"
                    )
                    prior_route = self.read_complete_evidence(
                        observation, "final-review", "prior-review-route"
                    )
                    prior_operation = self.read_complete_evidence(
                        observation, "final-review", "prior-review-operation"
                    )
                    expected_prior = (
                        ("mulgae", "not-applicable")
                        if self.validation_review_round == 1
                        else ("orca", "incomplete")
                    )
                    if (
                        planned_route != "mulgae"
                        or current_route != "orca"
                        or (prior_route, prior_operation) != expected_prior
                    ):
                        raise RuntimeQualificationError(
                            "Validation recovery lost provider continuity: "
                            f"planned={planned_route!r}; current={current_route!r}; "
                            f"prior={(prior_route, prior_operation)!r}"
                        )
                    if self.validation_review_round == 2 and (
                        self.node_visits.get(
                            "confirm-unassessed-final-review-provenance"
                        )
                        != 1
                        or self.node_visits.get("choose-settled-route-direction") != 1
                    ):
                        raise RuntimeQualificationError(
                            "Validation resume skipped the prior Orca settlement"
                        )
                    special_option = "bound"
                elif node == "decide-final-review-operation":
                    special_option = (
                        "unassessed"
                        if self.validation_review_round == 1
                        else "assessed"
                    )
                elif node == "confirm-final-route-settlement":
                    special_option = "change-safe"
                elif node == "choose-settled-route-direction":
                    special_option = "recover"
                elif node == "determine-final-backend-applicability":
                    special_option = "not-required"
            elif procedure_id == "aquarium-goal-v2" and node in {
                "confirm-completed-assessment-ordinal",
                "confirm-waived-assessment-ordinal",
            }:
                ordinal = self.completed_assessments.get(procedure_id, 0) + 1
                special_option = (
                    "first"
                    if ordinal == 1
                    else "second"
                    if ordinal == 2
                    else "authorized-extra"
                )
            elif node == "confirm-extra-assessment-ordinal":
                special_option = "authorized-extra"
            if route_qualification:
                evidence_nodes = {
                    "confirm-first-review-evidence": "review",
                    "confirm-extra-review-evidence": "review",
                    "confirm-first-route-evidence": "record-evidence",
                    "confirm-second-route-evidence": "record-evidence",
                    "confirm-extra-route-evidence": "record-evidence",
                }
                evidence_node = evidence_nodes.get(node)
                if evidence_node is not None:
                    evidence_reference = self.read_complete_evidence(
                        observation, evidence_node, "review-evidence-reference"
                    )
                    provenance = self.read_complete_evidence(
                        observation, evidence_node, "assessment-provenance"
                    )
                    if evidence_reference != route_qualification_evidence_reference(
                        qualified_route, scenario
                    ) or provenance != route_qualification_provenance(qualified_route):
                        raise RuntimeQualificationError(
                            "route qualification provenance was not preserved"
                        )
                route_decisions = {
                    "validate-review-route-entry": "planned",
                    "authorize-planned-review-route": (
                        f"planned-{qualified_route}"
                        if qualified_route != "waived"
                        else "planned-waiver"
                    ),
                    "confirm-review-route-binding": (
                        f"planned-{qualified_route}"
                        if procedure_id == "aquarium-goal-v2"
                        and qualified_route != "waived"
                        else "planned-waiver"
                        if procedure_id == "aquarium-goal-v2"
                        else qualified_route
                    ),
                    "decide-final-review-operation": "assessed",
                    "confirm-first-review-evidence": (
                        "mulgae"
                        if qualified_route == "mulgae"
                        else "waived"
                        if qualified_route == "waived"
                        else "static-delegated"
                    ),
                    "confirm-extra-review-evidence": (
                        "mulgae"
                        if qualified_route == "mulgae"
                        else "waived"
                        if qualified_route == "waived"
                        else "static-delegated"
                    ),
                    "confirm-first-route-evidence": (
                        "mulgae-pass"
                        if qualified_route == "mulgae"
                        else qualified_route
                    ),
                    "confirm-second-route-evidence": (
                        "mulgae-pass"
                        if qualified_route == "mulgae"
                        else qualified_route
                    ),
                    "confirm-extra-route-evidence": (
                        "mulgae-pass"
                        if qualified_route == "mulgae"
                        else qualified_route
                    ),
                    "decide-backend-check": ("non-failing"),
                    "determine-final-backend-applicability": (
                        "required" if qualified_route == "mulgae" else "not-required"
                    ),
                    "decide-final-backend-check": "passed",
                }
                task_operation_nodes = {
                    "mulgae": "decide-mulgae-review-operation",
                    "orca": "decide-orca-review-operation",
                    "native-codex": "decide-native-codex-review-operation",
                }
                if node == task_operation_nodes.get(qualified_route):
                    special_option = "assessed"
                task_provenance_nodes = {
                    "mulgae": "confirm-mulgae-provenance",
                    "orca": "confirm-static-delegated-provenance",
                    "native-codex": "confirm-static-delegated-provenance",
                    "waived": "confirm-waived-provenance",
                }
                if node == task_provenance_nodes.get(qualified_route):
                    special_option = (
                        "waived" if qualified_route == "waived" else "delegated"
                    )
                goal_operation_node = (
                    "decide-planned-waiver-review-operation"
                    if qualified_route == "waived"
                    else f"decide-planned-{qualified_route}-review-operation"
                )
                if node == goal_operation_node:
                    special_option = (
                        "waived" if qualified_route == "waived" else "completed"
                    )
                special_option = route_decisions.get(node, special_option)
            option = (
                special_option
                or {
                    "decide-evidence": "low-only"
                    if procedure_id == "aquarium-goal-v2"
                    and scenario in {"standard", "low-blocker-wait"}
                    else None,
                    "decide-final-review": "low-disposition"
                    if procedure_id == "aquarium-validation-v2"
                    and scenario in {"standard", "validation-low-blocker-wait"}
                    else None,
                    "decide-gaps": "low-only"
                    if procedure_id == "aquarium-validation-v2"
                    and scenario in {"standard", "validation-low-blocker-wait"}
                    else None,
                    "decide-review": "low-disposition"
                    if procedure_id == "aquarium-task-v2" and scenario == "standard"
                    else None,
                }.get(node)
                or SUCCESS_OPTIONS.get(node)
            )
            if option is None:
                raise RuntimeQualificationError(
                    f"no successful qualification option for {procedure_id}:{node}"
                )
            decision = self.decide(observation, option)
            if (
                procedure_id == "aquarium-goal-v2"
                and node
                in {
                    "confirm-first-route-evidence",
                    "confirm-second-route-evidence",
                    "confirm-extra-route-evidence",
                }
            ) or (
                procedure_id == "aquarium-validation-v2"
                and node == "confirm-assessed-final-review-provenance"
            ):
                self.completed_assessments[procedure_id] = (
                    self.completed_assessments.get(procedure_id, 0) + 1
                )
            if (
                scenario == "standard"
                and procedure_id == "aquarium-validation-v2"
                and node == "decide-final-review"
            ):
                self.decision_destination(decision, "record-low-disposition")
            if node == "decide-low-completion" and option == "completed":
                self.decision_destination(
                    decision, completed_low_settlement_destination(procedure_id)
                )
                self.low_settlement_procedures.add(procedure_id)
                self.mark_case_variant("C-03", procedure_id)
            payload = json_payload(decision)
            result = payload.get("result")
            if (
                payload.get("schema") != OUTPUT_SCHEMA
                or not isinstance(result, dict)
                or result.get("schema") != "podway.decision-result/v1"
            ):
                raise RuntimeQualificationError("decision result is invalid")
        else:
            raise RuntimeQualificationError(f"{procedure_id} exceeded 100 graph steps")

        terminal = self.observe()
        terminal_status = terminal["status"]
        disposition = self.raw(
            [
                "--json",
                "disposition",
                "handed-off",
                "--summary",
                f"qualified {procedure_id}",
                "--reference",
                f"official-v0.2.10-run-{self.run_index}",
                "--if-workspace-uuid",
                self.workspace_uuid(terminal),
                "--if-session-id",
                terminal_status["session"]["id"],
                "--if-session-revision",
                str(terminal_status["session"]["revision"]),
            ]
        )
        output_result(
            disposition,
            "session.terminal_disposition",
            "podway.terminal-disposition-result/v1",
        )


def merge_case_variants(
    destination: dict[str, set[str]], source: dict[str, set[str]]
) -> None:
    for case_id, variants in source.items():
        destination.setdefault(case_id, set()).update(variants)


def qualify_runtime(binary: Path, daemon: Path, repository: Path) -> dict[str, Any]:
    """Run two fresh isolated official-artifact runtime passes."""
    procedures = repository / "plugins/aquarium/assets/podway/procedures"
    probe_root: Path | None = None
    try:
        with ManagedRuntime(binary, daemon, procedures, 0) as cleanup_probe:
            probe_root = cleanup_probe.root
            raise ExpectedCleanupProbe("deliberate failure cleanup probe")
    except ExpectedCleanupProbe:
        pass
    if probe_root is None or probe_root.exists():
        raise RuntimeQualificationError(
            "failure cleanup probe left its disposable runtime root"
        )
    with ManagedRuntime(binary, daemon, procedures, REPEAT_COUNT + 1) as runtime:
        workspace_removal = runtime.exercise_workspace_removal()
    wait_scenarios: list[dict[str, Any]] = []
    case_variants: dict[str, set[str]] = {}
    wait_specs = (
        ("aquarium-goal-v2.yaml", "low-blocker-wait"),
        ("aquarium-validation-v2.yaml", "validation-low-blocker-wait"),
        ("aquarium-goal-v2.yaml", "medium-wait"),
        ("aquarium-goal-v2.yaml", "goal-closeout-unmet-wait"),
        ("aquarium-validation-v2.yaml", "validation-medium-wait"),
        ("aquarium-task-v2.yaml", "task-confirmation-only-wait"),
        *(
            ("aquarium-task-v2.yaml", scenario)
            for scenario in TASK_RESUME_SCENARIOS
            if scenario not in TASK_COMPLETED_CHANGE_SUCCESS_SCENARIOS
        ),
    )
    for offset, (procedure_name, scenario) in enumerate(wait_specs, start=2):
        with ManagedRuntime(
            binary, daemon, procedures, REPEAT_COUNT + offset
        ) as runtime:
            result = runtime.drive_procedure(procedure_name, scenario=scenario)
            if result is None:
                raise RuntimeQualificationError(
                    f"{scenario} did not produce a bounded wait result"
                )
            wait_scenarios.append(result)
            merge_case_variants(case_variants, runtime.correction_case_variants)
    scenario_runs: list[dict[str, Any]] = []
    bounded_scenarios = (
        *(
            (scenario, f"{procedure_id}.yaml")
            for scenario, (procedure_id, _route) in (
                ROUTE_QUALIFICATION_SCENARIOS.items()
            )
        ),
        *(
            (scenario, "aquarium-goal-v2.yaml")
            for scenario in sorted(GOAL_RECOVERY_SCENARIOS)
        ),
        *(
            (scenario, "aquarium-validation-v2.yaml")
            for scenario in sorted(VALIDATION_RECOVERY_SCENARIOS)
        ),
        ("goal-operational-matrix", "aquarium-goal-v2.yaml"),
        ("task-completion-unverified", "aquarium-task-v2.yaml"),
        ("task-completion-mixed-owners", "aquarium-task-v2.yaml"),
        ("task-finding-inconsistent", "aquarium-task-v2.yaml"),
        ("goal-finding-inconsistent", "aquarium-goal-v2.yaml"),
        ("goal-hardening-defer", "aquarium-goal-v2.yaml"),
        *(
            (scenario, "aquarium-task-v2.yaml")
            for scenario in sorted(TASK_COMPLETED_CHANGE_SUCCESS_SCENARIOS)
        ),
        *(
            (scenario, "aquarium-task-v2.yaml")
            for scenario in (
                *TASK_OWNER_SCENARIOS,
                "task-completion-owner-inconsistent",
            )
        ),
        *(
            (scenario, f"{procedure_id}.yaml")
            for scenario, (procedure_id, _gap) in COMPLETION_GAP_SCENARIOS.items()
        ),
        *((scenario, "aquarium-goal-v2.yaml") for scenario in GOAL_KIND_SCENARIOS),
        *(
            (scenario, "aquarium-validation-v2.yaml")
            for scenario in VALIDATION_FINAL_REVIEW_SCENARIOS
        ),
        *(
            (scenario, f"{procedure_id}.yaml")
            for scenario, (procedure_id, _source) in STOP_EVIDENCE_SCENARIOS.items()
        ),
    )
    for offset, (scenario, procedure_name) in enumerate(
        bounded_scenarios, start=REPEAT_COUNT + len(wait_specs) + 2
    ):
        with ManagedRuntime(binary, daemon, procedures, offset) as runtime:
            runtime.drive_procedure(procedure_name, scenario=scenario)
            merge_case_variants(case_variants, runtime.correction_case_variants)
            scenario_runs.append(
                {
                    "scenario": scenario,
                    "procedure_id": procedure_name.removesuffix(".yaml"),
                    "cleanup": "pending-context-exit",
                }
            )
        scenario_runs[-1]["cleanup"] = "passed"
    receipts: list[dict[str, Any]] = []
    for run_index in range(1, REPEAT_COUNT + 1):
        started = time.monotonic()
        with ManagedRuntime(binary, daemon, procedures, run_index) as runtime:
            for name in sorted(path.name for path in procedures.glob("*.yaml")):
                runtime.drive_procedure(name)
            runtime.exercise_pagination()
            seam_results = {
                "conditional_required_item": runtime.task_required_failure,
                "list_scale_enforced": runtime.task_list_limit,
                "guarded_decision": runtime.task_guard_failure,
                "verification_rework": runtime.task_verification_reworked,
                "review_rework": runtime.task_review_reworked,
                "medium_confirmation": runtime.task_medium_reworked,
                "review_guard_failure": runtime.task_review_guard_failure,
                "manual_rework": runtime.task_evidence_reworked,
                "stale_page_token": runtime.task_stale_token,
                "immutable_snapshot": runtime.task_snapshot_immutable,
                "task_low_settlement": "aquarium-task-v2"
                in runtime.low_settlement_procedures,
                "goal_low_settlement": "aquarium-goal-v2"
                in runtime.low_settlement_procedures,
                "validation_low_settlement": "aquarium-validation-v2"
                in runtime.low_settlement_procedures,
            }
            if not all(seam_results.values()):
                missing = sorted(
                    name for name, passed in seam_results.items() if not passed
                )
                raise RuntimeQualificationError(
                    f"runtime seams were not exercised: {missing}"
                )
            merge_case_variants(case_variants, runtime.correction_case_variants)
            elapsed = time.monotonic() - started
            if elapsed > RUN_TIMEOUT_SECONDS:
                raise RuntimeQualificationError(
                    "isolated runtime exceeded overall deadline"
                )
            receipts.append(
                {
                    "run": run_index,
                    "procedure_count": 5,
                    "seams": sorted(seam_results),
                    "correction_matrix_cases": sorted(runtime.correction_case_variants),
                    "elapsed_seconds": round(elapsed, 3),
                    "cleanup": "pending-context-exit",
                }
            )
        receipts[-1]["cleanup"] = "passed"
    if case_variants != EXPECTED_NATIVE_CASE_VARIANTS:
        raise RuntimeQualificationError(
            "correction matrix scenarios were incomplete: "
            f"expected={EXPECTED_NATIVE_CASE_VARIANTS!r}; observed={case_variants!r}"
        )
    correction_matrix_results = [
        {
            "case_id": case_id,
            "scope": "native-procedure",
            "variants": sorted(case_variants[case_id]),
            "assertions": CASE_ASSERTIONS[case_id],
            "status": "passed",
        }
        for case_id in sorted(case_variants)
    ]
    return {
        "runtime_mode": RUNTIME_MODE,
        "daemon_status_schema": "podway.daemon-status-result/v3",
        "runtime_repeat_count": REPEAT_COUNT,
        "runtime_procedure_count": 5,
        "failure_cleanup": "passed",
        "workspace_removal": workspace_removal,
        "wait_scenarios": wait_scenarios,
        "scenario_runs": scenario_runs,
        "route_contract_scenarios": sorted(ROUTE_QUALIFICATION_SCENARIOS),
        "recovery_contract_scenarios": sorted(
            GOAL_RECOVERY_SCENARIOS | VALIDATION_RECOVERY_SCENARIOS
        ),
        "route_contract_scope": (
            "Procedure recording, guard rejection, and graph transitions only; "
            "provider dispatch, prerequisites, and side effects require observed-agent "
            "acceptance"
        ),
        "correction_matrix_cases": sorted(case_variants),
        "correction_matrix_results": correction_matrix_results,
        "runtime_runs": receipts,
    }
