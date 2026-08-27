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
RUNTIME_SCHEMA = "podway.managed-dev-runtime/v2"
COMMAND_TIMEOUT_SECONDS = 20
READINESS_TIMEOUT_SECONDS = 20
PROCESS_EXIT_TIMEOUT_SECONDS = 10
RUN_TIMEOUT_SECONDS = 240
REPEAT_COUNT = 2
CONTRACT_MANIFEST_DIGEST = (
    "sha256:9ba166ebb634be16263f425b9967df784442354835b733c3f8579c11367539b5"
)

SUCCESS_OPTIONS = {
    "approve-closeout": "approved",
    "approve-diff": "approved",
    "classify-scope": "task",
    "decide-cause": "established",
    "decide-evidence": "supported",
    "decide-final-review": "validated",
    "decide-gaps": "clean",
    "decide-quality": "passed",
    "decide-review": "approved",
    "decide-verification": "passed",
    "assess-goal": "achieved",
}


class RuntimeQualificationError(RuntimeError):
    """One bounded external-artifact runtime assertion failed."""


class ExpectedCleanupProbe(RuntimeError):
    """Deliberately unwind one managed runtime to prove failure cleanup."""


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
        self.task_review_guard_failure = False
        self.task_evidence_reworked = False
        self.task_guard_failure = False
        self.task_required_failure = False
        self.task_list_limit = False
        self.task_stale_token = False
        self.task_snapshot_immutable = False

    def __enter__(self) -> Self:
        uid = os.geteuid()
        root = Path(
            tempfile.mkdtemp(prefix=f"podway-release-{uid}-", dir="/private/tmp")
        )
        root.chmod(0o700)
        self.root = root
        self.deadline = time.monotonic() + RUN_TIMEOUT_SECONDS
        self.account = root / "account"
        self.dev_home = root / "dev"
        self.sandbox = root / "sandbox"
        cache = root / "cache"
        temporary = root / "tmp"
        snapshot_id = sha256_file(self.daemon)[:16]
        snapshot = root / "snapshots" / snapshot_id
        private_directory(self.account)
        private_directory(self.dev_home)
        private_directory(self.sandbox)
        private_directory(cache)
        private_directory(temporary)
        private_directory(root / "snapshots")
        private_directory(snapshot)
        private_directory(self.account / ".podway")
        private_directory(self.account / ".podway" / "run")

        self.snapshot_binary = snapshot / "podway"
        self.snapshot_daemon = snapshot / "podwayd"
        shutil.copyfile(self.binary, self.snapshot_binary)
        shutil.copyfile(self.daemon, self.snapshot_daemon)
        self.snapshot_binary.chmod(0o755)
        self.snapshot_daemon.chmod(0o755)
        metadata = {
            "schema": RUNTIME_SCHEMA,
            "purpose": "release-qualification",
            "uid": uid,
            "root": str(root),
            "account_root": str(self.account),
            "dev_home": str(self.dev_home),
            "sandbox": str(self.sandbox),
            "snapshot": {
                "id": snapshot_id,
                "directory": str(snapshot),
                "podway": str(self.snapshot_binary),
                "podwayd": str(self.snapshot_daemon),
                "podway_sha256": sha256_file(self.snapshot_binary),
                "podwayd_sha256": sha256_file(self.snapshot_daemon),
            },
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
        daemon_log = root / "podwayd.log"
        self.log = daemon_log.open("xb")
        self.process = subprocess.Popen(
            [str(self.snapshot_daemon), "--dev"],
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
                and result.get("daemon_version") == "0.2.6"
                and result.get("contract_manifest_digest") == CONTRACT_MANIFEST_DIGEST
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
            "daemon did not reach v0.2.6 verified readiness: "
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
                "version": "v0.2.6",
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
            or result.get("schema") != "podway.daemon-status-result/v2"
        ):
            raise RuntimeQualificationError("invalid daemon status response")
        return result

    def terminate(self) -> None:
        assert self.snapshot_binary is not None
        assert self.sandbox is not None
        assert self.environment is not None
        if self.socket.exists():
            try:
                bounded_process(
                    [str(self.snapshot_binary), "--dev", "--json", "terminate"],
                    cwd=self.sandbox,
                    environment=self.environment,
                    timeout_seconds=PROCESS_EXIT_TIMEOUT_SECONDS,
                )
            except RuntimeQualificationError:
                pass
        if self.process is not None and self.process.poll() is None:
            try:
                self.process.wait(timeout=PROCESS_EXIT_TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired:
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
        if self.socket.exists():
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
            [str(self.snapshot_binary), "--dev", *arguments],
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
            raise RuntimeQualificationError(
                f"observation omitted one decision template for {option}"
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
                    "record": value,
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
        if item_type == "text":
            maximum = constraints.get("max_length", 256)
            if item_id == "implementation-summary":
                value = (
                    f"runtime-{self.run_index}-{self.command_sequence}-" + "x" * 5000
                )[:maximum]
            else:
                value = f"qualification {node} {item_id}"
            return {"type": "text", "value": value}
        if item_type == "integer":
            return {"type": "integer", "value": constraints.get("minimum", 0)}
        if item_type == "choice":
            choices = constraints.get("choices", [])
            preferred = {
                "hardening-deferral-state": "not-applicable",
                "review-mode": "remediation-eligible",
                "ci-decision": (
                    "fail"
                    if node == "review" and not self.task_review_reworked
                    else "pass"
                ),
                "reproduction-state": "reproduced",
            }.get(item_id)
            value = preferred if preferred in choices else choices[0]
            return {"type": "choice", "value": value}
        if item_type == "confirm":
            return {"type": "confirm", "value": True}
        if item_type == "list":
            return {"type": "list", "value": [f"qualification {item_id}"]}
        if item_type == "check_result":
            outcome = (
                "fail"
                if node == "verify" and not self.task_verification_reworked
                else "pass"
            )
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
            records = {
                item["item_id"]: self.value_for(item, node)
                for item in required
                if item["type"] != "artifact"
            }
            if not records:
                return
            self.record(current, records)
            current = self.observe()
        raise RuntimeQualificationError(
            "conditional action requirements did not converge"
        )

    def assess_goal(self, observation: dict[str, Any]) -> dict[str, Any]:
        goal = observation["guidance"].get("goal", {})
        for criterion in goal.get("criteria", []):
            if criterion.get("status") != "unassessed":
                continue
            completed = self.invoke_template(
                observation,
                "goal.assess_criterion",
                {
                    "<status>": "satisfied",
                    "<reason>": "official-artifact runtime criterion passed",
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

    def drive_procedure(self, name: str) -> None:
        assert self.sandbox is not None
        relative = f".podway/procedures/{name}"
        preview = output_result(
            self.raw(["--json", "procedure", "preview", relative]),
            "procedure.preview",
            "podway.procedure-preview-result/v1",
        )
        procedure_id = preview["procedure_id"]
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
                continue
            if node_type != "decision":
                raise RuntimeQualificationError(
                    f"unsupported graph node type: {node_type}"
                )

            if (
                procedure_id == "aquarium-task-v2"
                and node == "decide-verification"
                and not self.task_verification_reworked
            ):
                rejected = self.decide(observation, "passed", expected_exit=None)
                rejected_code = (
                    error_code(rejected) if rejected.returncode != 0 else None
                )
                if (
                    rejected.returncode == 0
                    or rejected_code != "OPTION_GUARD_UNSATISFIED"
                ):
                    raise RuntimeQualificationError(
                        "verification guard did not reject the passing route: "
                        f"exit={rejected.returncode}; code={rejected_code!r}"
                    )
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
                and node == "decide-review"
                and not self.task_review_reworked
            ):
                rejected = self.decide(observation, "approved", expected_exit=None)
                rejected_code = (
                    error_code(rejected) if rejected.returncode != 0 else None
                )
                if (
                    rejected.returncode == 0
                    or rejected_code != "OPTION_GUARD_UNSATISFIED"
                ):
                    raise RuntimeQualificationError(
                        "review CI guard did not reject approval: "
                        f"exit={rejected.returncode}; code={rejected_code!r}"
                    )
                self.task_review_guard_failure = True
                self.decide(observation, "ci-failed")
                self.task_review_reworked = True
                continue

            if node == "assess-goal":
                observation = self.assess_goal(observation)
            option = SUCCESS_OPTIONS.get(node)
            if option is None:
                raise RuntimeQualificationError(
                    f"no successful qualification option for {procedure_id}:{node}"
                )
            decision = self.decide(observation, option)
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
                f"official-v0.2.6-run-{self.run_index}",
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
                "review_guard_failure": runtime.task_review_guard_failure,
                "manual_rework": runtime.task_evidence_reworked,
                "stale_page_token": runtime.task_stale_token,
                "immutable_snapshot": runtime.task_snapshot_immutable,
            }
            if not all(seam_results.values()):
                missing = sorted(
                    name for name, passed in seam_results.items() if not passed
                )
                raise RuntimeQualificationError(
                    f"runtime seams were not exercised: {missing}"
                )
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
                    "elapsed_seconds": round(elapsed, 3),
                    "cleanup": "pending-context-exit",
                }
            )
        receipts[-1]["cleanup"] = "passed"
    return {
        "runtime_repeat_count": REPEAT_COUNT,
        "runtime_procedure_count": 5,
        "failure_cleanup": "passed",
        "runtime_runs": receipts,
    }
