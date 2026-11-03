#!/usr/bin/env python3
"""Submit Aquarium's sealed VM suites through the installed Haepari CLI.

The wrapper persists every request key and exact spec before the first
submission, observes through native blocking calls only, and reconnects an
existing Job from the saved private run directory without ever creating a
replacement Job. It never performs a VM power operation and never installs a
candidate on the host.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import posixpath
import queue
import re
import select
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

import host_bundle

REPOSITORY = Path(__file__).resolve().parents[2]
RUN_SCHEMA = "aquarium.vm-host-run/v1"
ENVELOPE_SCHEMA = "haepari.envelope/v1"
DOCTOR_SCHEMA = "haepari.doctor/v1"
VERDICT_EXITS = {"PASS": 0, "FAIL": 1, "INCOMPLETE": 3, "CANCELLED": 4}
EXIT_VERDICTS = {value: key for key, value in VERDICT_EXITS.items()}
EXIT2_CLASSIFICATIONS = {"RESULT_UNAVAILABLE", "CONFLICT", "INVALID_REQUEST"}
PROBE_KINDS = {"identical-replay", "changed-survivor-replay", "admit-despite-gap"}
KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
# The registered resource-v2 ceilings make 26100 s the longest possible Job
# (prepare 1800 + manual 21600 + collect 900 + cleanup 1800); the tagged queue
# rule requires queue_seconds >= (jobs ahead + 1) * that maximum.
MAX_JOB_SECONDS = 26100
QUEUE_CEILING = 86400
MAX_JOBS_AHEAD = 2


class Refusal(RuntimeError):
    def __init__(self, message: str, *, native: bool = False, exit_code: int = 2):
        super().__init__(message)
        self.native = native
        self.exit_code = exit_code


def save(path: Path, value: Any) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".save-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w") as stream:
            json.dump(value, stream, sort_keys=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def report(kind: str, **payload: Any) -> None:
    print(json.dumps({"kind": kind, **payload}, ensure_ascii=False), flush=True)


def invoke(binary: str, *args: str, timeout: int = 120) -> tuple[int, dict[str, Any]]:
    try:
        result = subprocess.run(
            [binary, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise Refusal(
            "Haepari caller deadline expired; reconnect with the original run "
            "directory, spec and key"
        ) from None
    if result.returncode < 0:
        raise Refusal(
            "Haepari CLI was interrupted; reconnect with the original run "
            "directory, spec and key"
        )
    try:
        envelope = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise Refusal(
            "Haepari response unavailable; select a compatible CLI/controller and "
            f"reconnect with the original run directory: {result.stderr[:400]}"
        ) from None
    if (
        not isinstance(envelope, dict)
        or envelope.get("schema") != ENVELOPE_SCHEMA
        or not isinstance(envelope.get("ok"), bool)
    ):
        raise Refusal(
            "unsupported Haepari response; select a compatible CLI/controller and "
            "retain the original run directory, spec and key"
        )
    payload = envelope.get("data" if envelope["ok"] else "error")
    if not isinstance(payload, dict):
        raise Refusal(
            "malformed Haepari payload; retain the original run directory and key"
        )
    return result.returncode, envelope


def require_run_dir(raw: str) -> Path:
    run = Path(raw)
    if not run.is_absolute() or run.is_symlink():
        raise Refusal("RUN_DIR must be an absolute physical directory")
    for parent in run.parents:
        if parent.is_symlink():
            raise Refusal("RUN_DIR must not have a symlink ancestor")
    if run.exists():
        info = run.lstat()
        if not stat.S_ISDIR(info.st_mode) or run.is_symlink():
            raise Refusal("RUN_DIR must be a regular directory")
        if stat.S_IMODE(info.st_mode) != 0o700 or info.st_uid != os.geteuid():
            raise Refusal("RUN_DIR must be owned by the current user with mode 0700")
    else:
        run.mkdir(mode=0o700, parents=False)
    return run.resolve()


def load_record(run: Path) -> dict[str, Any]:
    try:
        record = json.loads((run / "run.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise Refusal(
            "saved run.json is unreadable; retain the original run directory and "
            "inspect its keys and specs"
        ) from None
    if not isinstance(record, dict) or record.get("schema") != RUN_SCHEMA:
        raise Refusal(
            "saved run.json has an unsupported shape; retain the original run "
            "directory and inspect its keys and specs"
        )
    return record


def validate_record(record: dict[str, Any], args: Any) -> None:
    for key in ("resource", "suite"):
        if record.get(key) != getattr(args, key):
            raise Refusal(
                "resume requires the original resource and suite; select a "
                "new run directory for a new run"
            )
    if args.suite != "all" and record.get("mode") != args.mode:
        raise Refusal("resume requires the original mode; select a new run directory")
    names = record.get("declared_suites")
    entries = record.get("jobs")
    if (
        not isinstance(names, list)
        or not names
        or not all(isinstance(name, str) for name in names)
        or len(set(names)) != len(names)
        or (args.suite != "all" and names != [args.suite])
        or not isinstance(entries, list)
        or len(entries) != len(names)
    ):
        raise Refusal(
            "saved suite/Job membership is incomplete; retain and inspect the "
            "original run and keys"
        )
    keys: set[str] = set()
    job_ids: set[str] = set()
    for index, (name, entry) in enumerate(zip(names, entries)):
        if (
            not isinstance(entry, dict)
            or entry.get("suite") != name
            or entry.get("spec") != f"spec-{index}.json"
            or not isinstance(entry.get("request_key"), str)
            or not KEY_RE.fullmatch(entry["request_key"])
            or entry["request_key"] in keys
            or not isinstance(entry.get("submission_started"), bool)
            or not isinstance(entry.get("spec_sha256"), str)
        ):
            raise Refusal("saved Job binding is invalid; retain the original run")
        keys.add(entry["request_key"])
        if "job_id" in entry:
            if (
                not isinstance(entry["job_id"], str)
                or not KEY_RE.fullmatch(entry["job_id"])
                or entry["job_id"] in job_ids
                or not entry["submission_started"]
            ):
                raise Refusal("saved Job identity is invalid; no aggregate PASS exists")
            job_ids.add(entry["job_id"])


def verify_installation_binding(binary: str, record: dict[str, Any]) -> None:
    """Bind every operation to the recorded installation through the VM-free
    projection; reconnection never requires a guest-reaching probe."""
    waited, envelope = invoke(
        binary,
        "doctor",
        "--projection",
        "--section",
        "queue",
        "--limit",
        "1",
        "--json",
    )
    if waited != 0 or not envelope["ok"]:
        issue = envelope.get("error", {})
        raise Refusal(
            f"cannot confirm the recorded Haepari installation ({issue.get('code')}); "
            "reconnect later with the original run directory"
        )
    projection = envelope.get("data", {})
    if projection.get("installation_id") != record.get("installation_id"):
        raise Refusal(
            "the selected Haepari installation changed; do not replay this key "
            "against another installation"
        )


def queue_position(binary: str, resource: str) -> int:
    ahead = 0
    cursor: str | None = None
    while True:
        arguments = ["jobs", "list", "--resource", resource, "--state", "queued"]
        if cursor:
            arguments += ["--cursor", cursor]
        waited, envelope = invoke(binary, *arguments, "--json")
        if waited != 0 or not envelope["ok"]:
            raise Refusal(
                "queue position is unobservable; retry submission when the "
                "controller is reachable"
            )
        data = envelope.get("data", {})
        jobs = data.get("jobs")
        if not isinstance(jobs, list):
            raise Refusal("queue inventory is malformed; refuse speculative sizing")
        ahead += len(jobs)
        if not data.get("more"):
            break
        cursor = data.get("next_cursor")
        if not isinstance(cursor, str) or not cursor:
            raise Refusal("queue pagination is truncated; refuse speculative sizing")
    waited, envelope = invoke(binary, "resources", "list", "--json")
    if waited != 0 or not envelope["ok"]:
        raise Refusal(
            "resource occupancy is unobservable; retain the original run and "
            f"follow the native retry policy: {json.dumps(envelope.get('error', {}))}",
            native=True,
            exit_code=waited or 2,
        )
    for row in envelope.get("data", {}).get("resources", []):
        if isinstance(row, dict) and row.get("resource_id") == resource:
            occupancy = row.get("occupancy")
            if isinstance(occupancy, int) and occupancy > 0:
                ahead += 1
            break
    return ahead


def require_queue_budget(queue_seconds: int, ahead: int) -> None:
    if ahead > MAX_JOBS_AHEAD:
        raise Refusal(
            f"{ahead} Jobs are ahead; the queue ceiling never admits a third "
            "waiting Job safely"
        )
    if queue_seconds < (ahead + 1) * MAX_JOB_SECONDS:
        raise Refusal(
            f"queue_seconds {queue_seconds} is below the tagged minimum "
            f"{(ahead + 1) * MAX_JOB_SECONDS} for {ahead} Jobs ahead"
        )
    if queue_seconds > QUEUE_CEILING:
        raise Refusal(f"queue_seconds {queue_seconds} exceeds the 86400 ceiling")


def read_spec(run: Path, entry: dict[str, Any]) -> dict[str, Any]:
    path = run / entry["spec"]
    if path.parent != run or path.is_symlink() or not path.is_file():
        raise Refusal("saved spec is missing; preserve this run for inspection")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != entry["spec_sha256"]:
        raise Refusal(
            "the saved spec changed; preserve this run instead of constructing a "
            "new request"
        )
    spec = json.loads(raw)
    if not isinstance(spec, dict) or spec.get("resource_id") is None:
        raise Refusal("saved spec is malformed; preserve the original run")
    return spec


def submit_suite(
    binary: str, run: Path, record: dict[str, Any], entry: dict[str, Any], args: Any
) -> None:
    if entry.get("job_id"):
        # Reconnect observes the saved Job natively; a deliberate identical
        # same-key replay is a labelled probe, never the reconnect path.
        report("reconnect", suite=entry["suite"], job_id=entry["job_id"])
        return
    if not entry["submission_started"]:
        ahead = queue_position(binary, args.resource)
        require_queue_budget(read_spec(run, entry)["deadlines"]["queue_seconds"], ahead)
        entry["submission_started"] = True
        save(run / "run.json", record)
    waited, envelope = invoke(
        binary,
        "submit",
        "--spec",
        str(run / entry["spec"]),
        "--request-key",
        entry["request_key"],
        "--json",
    )
    if waited != 0 or not envelope["ok"]:
        issue = envelope.get("error", {})
        guidance = (
            "correct the declaration and select a new empty run directory; retain "
            "this original run for inspection"
            if issue.get("code") == "INVALID_REQUEST"
            else "retain this run directory without changing its key and follow the "
            "error retry policy"
        )
        raise Refusal(
            f"submission refused; {guidance}: {json.dumps(issue)[:600]}",
            native=True,
            exit_code=waited or 2,
        )
    receipt = envelope.get("data", {})
    job_id = receipt.get("job_id")
    if not isinstance(job_id, str) or not KEY_RE.fullmatch(job_id):
        raise Refusal("malformed Job receipt; retain the original spec and key")
    if entry.get("job_id") and entry["job_id"] != job_id:
        raise Refusal("replay returned a different Job; preserve the original run")
    entry["job_id"] = job_id
    save(run / "run.json", record)
    report("admission", suite=entry["suite"], job_id=job_id)


def classify_wait(
    waited: int, envelope: dict[str, Any]
) -> tuple[str, int, dict[str, Any]]:
    if envelope["ok"]:
        verdict = envelope.get("data", {}).get("final_verdict")
        expected = VERDICT_EXITS.get(verdict)
        if expected is None or waited != expected:
            raise Refusal(
                "terminal verdict and CLI exit disagree; no aggregate PASS exists"
            )
        return verdict, waited, envelope.get("data", {})
    issue = envelope.get("error", {})
    code = issue.get("code")
    if waited == 5:
        return "PENDING", 5, issue
    if waited == 2 and code in EXIT2_CLASSIFICATIONS:
        return "UNAVAILABLE", 2, issue
    if waited == 6:
        return "UNKNOWN", 6, issue
    raise Refusal(
        f"observation failed without a verdict ({code}); preserve the original "
        "run and reconcile the same key",
        native=True,
        exit_code=waited or 2,
    )


class Observer:
    """A `haepari events --follow` child in its own session, read without
    blocking (the reference observer lifecycle).

    Ownership is established at the first allocation: the pipe is created
    non-blocking before the spawn, a spawn failure closes both ends, the
    parent write end is closed right after a successful spawn, and a
    reader-start failure runs the full teardown before re-raising.
    """

    def __init__(self, arguments: list[str]) -> None:
        self.records: queue.Queue[str | None] = queue.Queue()
        self.stop_event = threading.Event()
        self.process: subprocess.Popen | None = None
        self.read_fd: int | None = None
        self.reader: threading.Thread | None = None
        self.returncode: int | None = None
        read_fd, write_fd = os.pipe()
        try:
            os.set_blocking(read_fd, False)
            self.process = subprocess.Popen(
                arguments,
                stdout=write_fd,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )
        except BaseException:
            os.close(read_fd)
            os.close(write_fd)
            raise
        # The child holds its own copy; the parent never writes.
        os.close(write_fd)
        self.read_fd = read_fd
        try:
            self.reader = threading.Thread(
                target=self._read, args=(read_fd,), daemon=True
            )
            self.reader.start()
        except BaseException:
            self.reader = None
            self.stop()  # tears the group down and closes the fd
            raise

    def _read(self, fd: int) -> None:
        pending = bytearray()
        try:
            while not self.stop_event.is_set():
                ready, _, _ = select.select([fd], [], [], 0.2)
                if not ready:
                    continue
                try:
                    chunk = os.read(fd, 65536)
                except (BlockingIOError, InterruptedError):
                    continue
                except OSError:
                    break
                if not chunk:
                    break
                pending += chunk
                while b"\n" in pending:
                    line, _, rest = pending.partition(b"\n")
                    self.records.put(line.decode("utf-8", errors="replace"))
                    pending = bytearray(rest)
        finally:
            self.records.put(None)

    def _leader_exited_unreaped(self, pid: int) -> bool:
        """True once the leader exited; it stays a zombie, pinning the pgid.

        Raises ChildProcessError when the child is no longer ours to
        observe; that is a reported problem, never confirmed exit.
        """
        result = os.waitid(os.P_PID, pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
        return result is not None and result.si_pid == pid

    def _signal_group(self, pid: int, sig: int, problems: list[str]) -> None:
        """Signal the owned group while its unreaped leader pins the id.

        macOS answers EPERM (not ESRCH) when the only member left is the
        zombie leader; that is "nothing live to signal" once the leader's
        exit is confirmed, otherwise a reported problem.
        """
        try:
            os.killpg(pid, sig)
        except ProcessLookupError:
            pass
        except PermissionError as error:
            try:
                exited = self._leader_exited_unreaped(pid)
            except ChildProcessError:
                exited = False
            if not exited:
                problems.append(f"signal {sig} to the observer group refused: {error}")
        except OSError as error:
            problems.append(f"signal {sig} to the observer group failed: {error}")

    def stop(
        self,
        *,
        grace: float = 10.0,
        reap_bound: float = 10.0,
        join_bound: float = 5.0,
    ) -> str | None:
        """Run the one teardown sequence; return None on verified teardown.

        Stop event, group SIGTERM, bounded unreaped waitid poll, always
        group SIGKILL while the unreaped leader pins the pgid, bounded
        WNOHANG reap loop, bounded reader join, then close the read fd only
        once the reader has exited. Any problem is returned verbatim.
        """
        problems: list[str] = []
        self.stop_event.set()
        process = self.process
        if process is not None and self.returncode is None:
            pid = process.pid
            owned = True
            self._signal_group(pid, signal.SIGTERM, problems)
            deadline = time.monotonic() + grace
            try:
                while time.monotonic() < deadline and not self._leader_exited_unreaped(
                    pid
                ):
                    time.sleep(0.05)
            except ChildProcessError:
                owned = False
                problems.append("observer leader is no longer an owned child")
            if owned:
                # Always escalate while the unreaped leader pins the pgid.
                self._signal_group(pid, signal.SIGKILL, problems)
                deadline = time.monotonic() + reap_bound
                reaped = False
                try:
                    while time.monotonic() < deadline:
                        waited, status = os.waitpid(pid, os.WNOHANG)
                        if waited == pid:
                            self.returncode = os.waitstatus_to_exitcode(status)
                            process.returncode = self.returncode
                            reaped = True
                            break
                        time.sleep(0.05)
                except ChildProcessError:
                    problems.append("observer leader status unavailable during reap")
                if not reaped and not any("status unavailable" in p for p in problems):
                    problems.append("observer leader not reaped within bounds")
        if self.reader is not None:
            self.reader.join(timeout=join_bound)
            if self.reader.is_alive():
                problems.append("reader thread did not terminate")
        if self.read_fd is not None and (
            self.reader is None or not self.reader.is_alive()
        ):
            try:
                os.close(self.read_fd)
            except OSError as error:
                problems.append(f"read end close failed: {error}")
            self.read_fd = None
        return "; ".join(problems) or None


def follow_to_awaiting(
    binary: str, job_id: str, budget: int
) -> dict[str, Any] | str | None:
    """Reach manual readiness through the native blocking event stream.

    The Observer owns the process, pipe, reader and teardown; this
    function keeps only the record parsing, the classification and the
    reconnect policy. A permanent error (parsed error code, or a known
    exit-2 condition) returns the error dictionary as a terminal
    classification; only transport loss without `end` or an exit-6
    uncertainty resumes with `--after`.
    """
    deadline = time.monotonic() + budget
    cursor: int | None = None
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            report("observer-stopped-locally", job_id=job_id, reason="budget")
            return None
        arguments = [binary, "events", job_id, "--follow", "--json"]
        if cursor is not None:
            arguments += ["--after", str(cursor)]
        observer = Observer(arguments)
        found: dict[str, Any] | None = None
        stream_error: dict[str, Any] | None = None
        saw_end = False
        budget_expired = False
        reader_eof = False
        try:
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    budget_expired = True
                    break
                try:
                    line = observer.records.get(timeout=min(remaining, 1.0))
                except queue.Empty:
                    continue
                if line is None:
                    reader_eof = True
                    break
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                if record.get("schema") != "haepari.observer/v1":
                    continue
                kind = record.get("type")
                events = record.get("events") or {}
                next_cursor = events.get("next_cursor")
                if isinstance(next_cursor, int):
                    cursor = next_cursor
                elif isinstance(record.get("cursor"), int):
                    cursor = record["cursor"]
                if kind == "error":
                    stream_error = dict(record.get("error") or {})
                    break
                if kind == "end":
                    saw_end = True
                    break
                snapshot = events.get("snapshot") or {}
                if snapshot.get("job_state") == "awaiting_manual":
                    found = snapshot
                    break
        finally:
            reason = (
                "readiness"
                if found is not None
                else "error"
                if stream_error is not None
                else "end"
                if saw_end
                else "budget"
                if budget_expired
                else "eof"
                if reader_eof
                else None
            )
            # One stop sequence for readiness, budget, error, end, EOF and
            # read-error alike.
            problem = observer.stop()
            if reason is not None:
                report("observer-stopped-locally", job_id=job_id, reason=reason)
            if problem is not None:
                report(
                    "observer-teardown-incomplete",
                    job_id=job_id,
                    problem=problem,
                )
        final_exit = observer.returncode
        if (
            observer.read_fd is not None
            or (observer.reader is not None and observer.reader.is_alive())
            or problem is not None
        ):
            # Teardown failed: never reconnect or report readiness with an
            # unverified observer lifecycle in this invocation.
            return {
                "code": "OBSERVER_TEARDOWN_INCOMPLETE",
                "exit": final_exit,
                "problem": problem,
            }
        if stream_error is not None:
            stream_error["exit"] = final_exit
            code = stream_error.get("code")
            if code not in {"TRANSPORT_UNCERTAIN", "STORAGE_UNAVAILABLE"} and (
                final_exit != 6
            ):
                # A permanent known error is a terminal classification.
                return stream_error
            report("event-stream-error", job_id=job_id, error=stream_error)
            continue
        if found is not None:
            return found
        if saw_end:
            return None
        if budget_expired:
            return None
        if final_exit in (0, 6):
            if final_exit == 0:
                report("event-stream-resumed", job_id=job_id, after=cursor)
            else:
                report(
                    "event-stream-uncertain",
                    job_id=job_id,
                    after=cursor,
                    exit=final_exit,
                )
            continue
        # A nonzero exit without a parsed error record and without `end`:
        # a known exit-2 condition is terminal; other losses resume.
        if final_exit == 2:
            return {"code": "STREAM_EXIT_2", "exit": final_exit}
        report("event-stream-resumed", job_id=job_id, after=cursor, exit=final_exit)


def manual_hold(
    binary: str, entry: dict[str, Any], args: Any, receipt: dict[str, Any]
) -> None:
    report(
        "manual-hold",
        suite=entry["suite"],
        job_id=entry["job_id"],
        state=receipt.get("job_state"),
        revision=receipt.get("job_revision"),
        scenario=(
            "stage case evidence in the Job's declared output paths, finish "
            "consumer cleanup and verify its inventory, then submit the closed "
            "haepari.manual-result/v1 record through: "
            f"{args.haepari} manual complete {entry['job_id']} --input <record.json> "
            f"--expected-revision <n> --json"
        ),
    )


def wait_for_suite(
    binary: str, entry: dict[str, Any], args: Any
) -> tuple[str, int, dict[str, Any]]:
    step = str(args.wait_timeout)
    rounds = 0
    while rounds < args.wait_rounds:
        rounds += 1
        waited, envelope = invoke(
            binary,
            "wait",
            entry["job_id"],
            "--timeout",
            f"{step}s",
            "--json",
            timeout=args.wait_timeout + 60,
        )
        outcome, code, detail = classify_wait(waited, envelope)
        if outcome != "PENDING":
            return outcome, code, detail
        if entry.get("mode", "auto") != "manual":
            continue
        snapshot = follow_to_awaiting(
            binary, entry["job_id"], max(args.wait_timeout, 30)
        )
        if (
            isinstance(snapshot, dict)
            and snapshot.get("code") == "OBSERVER_TEARDOWN_INCOMPLETE"
        ):
            # Teardown failed: do not reconnect or report readiness in this
            # invocation; the observer was not provably stopped.
            report(
                "follow-teardown-incomplete",
                suite=entry["suite"],
                job_id=entry["job_id"],
                code=snapshot["code"],
                problem=snapshot.get("problem"),
            )
            return "UNKNOWN", 2, snapshot
        if isinstance(snapshot, dict) and snapshot.get("code"):
            # Terminal follow error: report UNKNOWN with the native error,
            # never PENDING.
            report(
                "follow-terminal-error",
                suite=entry["suite"],
                job_id=entry["job_id"],
                error=snapshot,
            )
            return "UNKNOWN", 2, snapshot
        if isinstance(snapshot, dict):
            manual_hold(binary, entry, args, snapshot)
            return "PENDING", 5, {"job_state": "awaiting_manual"}
    report(
        "wait-rounds-exhausted",
        job_id=entry.get("job_id"),
        note="observation stays PENDING; reconnect with the original run directory",
    )
    return "PENDING", 5, {}


def export_artifact_path(destination: Path | str, relative: str) -> Path:
    """An exported Job-relative output lives under artifacts/."""
    return Path(destination) / "artifacts" / relative


def _allowed_export_path(path: str) -> bool:
    """Haepari's export files[] paths are exactly output.log, artifacts/<p>
    or recovery-<...>, mirroring the native client's rule."""
    return (
        path == "output.log"
        or (path.startswith("artifacts/") and len(path) > len("artifacts/"))
        or (path.startswith("recovery-") and len(path) > len("recovery-"))
    )


def _valid_artifact_path(path: str) -> bool:
    """Haepari's native artifact-path validity: a clean relative POSIX path
    without traversal, backslashes, NUL or surrogate code points."""
    return (
        bool(path)
        and path not in {".", ".."}
        and not path.startswith("/")
        and not path.startswith("../")
        and "\\" not in path
        and "\x00" not in path
        and not any("\ud800" <= character <= "\udfff" for character in path)
        and posixpath.normpath(path) == path
    )


def _safe_export_file(destination: Path, relative: str) -> bool:
    """No symlink anywhere on the consumed path: the export directory, every
    intermediate directory (lstat) and the leaf regular file."""
    current = Path(destination)
    parts = relative.split("/")
    try:
        if stat.S_ISLNK(os.lstat(current).st_mode):
            return False
        for part in parts[:-1]:
            current = current / part
            if not stat.S_ISDIR(os.lstat(current).st_mode):
                return False
        return stat.S_ISREG(os.lstat(current / parts[-1]).st_mode)
    except (OSError, ValueError):
        return False


def _valid_listed_entry(item: Any) -> bool:
    """A files[] or result.artifacts[] entry: a dict with string path and
    digest, and an integer size_bytes that is never a bool."""
    return (
        isinstance(item, dict)
        and isinstance(item.get("path"), str)
        and isinstance(item.get("sha256"), str)
        and isinstance(item.get("size_bytes"), int)
        and not isinstance(item.get("size_bytes"), bool)
    )


def _verify_export(
    destination: Path,
    entry: dict[str, Any],
    required_outputs: list[str],
    sealed_candidate: dict[str, Any],
) -> bool:
    """A verified export binds the Job, the suite and the saved spec's
    complete required-output set in Haepari's real layout: outputs live
    under artifacts/, the manifest carries the original result, and every
    listed file exists with its listed digest. Verification fails closed:
    malformed or unreadable evidence returns False instead of raising."""
    destination = Path(destination)
    try:
        if not _safe_export_file(destination, "manifest.json"):
            return False
        manifest = json.loads((destination / "manifest.json").read_text())
        if not _safe_export_file(destination, "result.json"):
            return False
        exported_result = json.loads((destination / "result.json").read_text())
    except (OSError, ValueError):
        return False
    if not isinstance(manifest, dict):
        return False
    result = manifest.get("result")
    files = manifest.get("files")
    if (
        manifest.get("schema") != "haepari.artifact-manifest/v1"
        or manifest.get("job_id") != entry.get("job_id")
        or not isinstance(result, dict)
        or result.get("job_id") != entry.get("job_id")
        or not isinstance(files, list)
        or exported_result != result
    ):
        return False
    listed: dict[str, dict[str, Any]] = {}
    lowered: set[str] = set()
    for item in files:
        if not _valid_listed_entry(item):
            return False
        path = item["path"]
        if path.casefold() in lowered or not _allowed_export_path(path):
            return False
        lowered.add(path.casefold())
        listed[path] = item
    for path, item in listed.items():
        if not _valid_artifact_path(path):
            return False
        if not _safe_export_file(destination, path):
            return False
        try:
            content = (destination / path).read_bytes()
        except (OSError, ValueError):
            return False
        if len(content) != item["size_bytes"] or hashlib.sha256(
            content
        ).hexdigest() != item["sha256"].removeprefix("sha256:"):
            return False
    artifacts = result.get("artifacts")
    if not isinstance(artifacts, list):
        return False
    declared: dict[str, dict[str, Any]] = {}
    declared_lowered: set[str] = set()
    for item in artifacts:
        if not _valid_listed_entry(item):
            return False
        path = item["path"]
        if path.casefold() in declared_lowered or not _valid_artifact_path(path):
            return False
        declared_lowered.add(path.casefold())
        declared[path] = item
    # Every declared artifact must be delivered: files[] carries it under
    # artifacts/<path> with the same size and digest, required or not.
    for path, item in declared.items():
        listed_item = listed.get(f"artifacts/{path}")
        if listed_item is None:
            return False
        if (
            item["size_bytes"] != listed_item["size_bytes"]
            or item["sha256"] != listed_item["sha256"]
        ):
            return False
    logs = result.get("logs")
    if not isinstance(logs, list):
        return False
    declared_logs: dict[str, dict[str, Any]] = {}
    logs_lowered: set[str] = set()
    for item in logs:
        if not _valid_listed_entry(item):
            return False
        path = item["path"]
        if (
            path.casefold() in logs_lowered
            or not _valid_artifact_path(path)
            or not _allowed_export_path(path)
        ):
            return False
        logs_lowered.add(path.casefold())
        declared_logs[path] = item
    # Every declared log is delivered by files[] with the same size and
    # digest.
    for path, item in declared_logs.items():
        listed_item = listed.get(path)
        if listed_item is None:
            return False
        if (
            item["size_bytes"] != listed_item["size_bytes"]
            or item["sha256"] != listed_item["sha256"]
        ):
            return False
    # Closed mapping: each delivery is accepted when any membership holds —
    # a declared result.logs path (wherever it lives, even under
    # artifacts/), an artifacts/<p> delivery of a declared artifact, or a
    # recovery-<...> entry whose schema this Task never observed (prefix,
    # digest and size only). When a path satisfies more than one membership,
    # the agreement loops above already hold both declarations to the one
    # delivered file.
    for path in listed:
        if path in declared_logs:
            continue
        if path.startswith("artifacts/") and path[len("artifacts/") :] in declared:
            continue
        if path.startswith("recovery-"):
            continue
        return False
    for required in required_outputs:
        if not _valid_artifact_path(required):
            return False
        declared_item = declared.get(required)
        listed_item = listed.get(f"artifacts/{required}")
        if declared_item is None or listed_item is None:
            return False
        try:
            size = (destination / listed_item["path"]).stat().st_size
        except (OSError, ValueError):
            return False
        if (
            declared_item["size_bytes"] != size
            or listed_item["size_bytes"] != size
            or declared_item["sha256"] != listed_item["sha256"]
        ):
            return False
    # The consumed suite result is read only as one of the already-verified
    # listed files.
    consumed_relative = f"artifacts/results/{entry['suite']}/result.json"
    if consumed_relative not in listed:
        return False
    try:
        consumed = json.loads((destination / consumed_relative).read_text())
    except (OSError, ValueError):
        return False
    if not isinstance(consumed, dict):
        return False
    if consumed.get("suite") != entry["suite"]:
        return False
    candidate = consumed.get("candidate")
    if not isinstance(candidate, dict):
        return False
    return all(
        candidate.get(key) == sealed_candidate.get(key)
        for key in ("git_sha", "development_version", "artifact_tree_sha256")
    )


def export_results(
    binary: str,
    run: Path,
    entry: dict[str, Any],
    required_outputs: list[str],
    sealed_candidate: dict[str, Any],
) -> str:
    base = run / f"export-{entry['suite']}"
    destination = base
    ordinal = 1
    while destination.exists():
        if _verify_export(destination, entry, required_outputs, sealed_candidate):
            report(
                "export-reuse",
                suite=entry["suite"],
                destination=str(destination),
            )
            return str(destination)
        ordinal += 1
        destination = run / f"export-{entry['suite']}-r{ordinal}"
    waited, envelope = invoke(
        binary,
        "export",
        entry["job_id"],
        "--to",
        str(destination),
        "--json",
        timeout=300,
    )
    if waited != 0 or not envelope["ok"]:
        report(
            "export-unavailable",
            suite=entry["suite"],
            error=envelope.get("error", {}),
        )
        return ""
    if not _verify_export(destination, entry, required_outputs, sealed_candidate):
        report(
            "export-unverified",
            suite=entry["suite"],
            destination=str(destination),
        )
        return ""
    report("export", suite=entry["suite"], destination=str(destination))
    return str(destination)


def settle_suite_result(
    binary: str,
    run: Path,
    record: dict[str, Any],
    entry: dict[str, Any],
    outcome: str,
    code: int,
    detail: dict[str, Any],
) -> tuple[str, int]:
    entry["observation"] = {
        "outcome": outcome,
        "final_verdict": detail.get("final_verdict"),
        "workload_outcome": detail.get("workload_outcome"),
        "evidence_completeness": detail.get("evidence_completeness"),
        "cleanup_outcome": detail.get("cleanup_outcome"),
        "consumer_cleanup": (
            detail.get("consumer_cleanup")
            if isinstance(detail.get("consumer_cleanup"), str)
            else "unobserved"
        ),
    }
    save(run / "run.json", record)
    export_destination = ""
    if outcome in VERDICT_EXITS and entry.get("job_id"):
        spec = read_spec(run, entry)
        required_outputs = spec["workload"]["required_outputs"]
        binding = record.get("installation_binding", {})
        sealed_candidate = {
            "git_sha": binding.get("candidate_git_sha"),
            "development_version": binding.get("development_version"),
            "artifact_tree_sha256": binding.get("artifact_tree_sha256"),
        }
        export_destination = export_results(
            binary, run, entry, required_outputs, sealed_candidate
        )
    consumer = "unverified"
    if export_destination:
        evidence = export_artifact_path(
            export_destination, f"results/{entry['suite']}/result.json"
        )
        try:
            document = json.loads(evidence.read_text())
            if isinstance(document, dict):
                value = document.get("consumer_cleanup")
                if isinstance(value, str) and value in {
                    "verified",
                    "failed",
                    "unverified",
                }:
                    consumer = value
        except (OSError, ValueError):
            consumer = "unverified"
    entry["observation"]["consumer_cleanup"] = consumer
    if consumer != "verified" and outcome == "PASS":
        entry["observation"]["acceptance"] = "blocked"
        outcome, code = "ACCEPTANCE-BLOCKED", 3
    save(run / "run.json", record)
    report("result", suite=entry["suite"], **entry["observation"])
    return outcome, code


def cancel_run(binary: str, run: Path, record: dict[str, Any], args: Any) -> int:
    verify_installation_binding(binary, record)
    pending = [entry for entry in record["jobs"] if entry.get("job_id")]
    if not pending:
        raise Refusal("cancellation needs an existing admitted Job in this run")
    outcome, code = "PENDING", 5
    for entry in pending:
        saved = entry.get("cancellation")
        if saved is None:
            waited, envelope = invoke(
                binary, "inspect", entry["job_id"], "--json", timeout=60
            )
            if waited != 0 or not envelope["ok"]:
                raise Refusal("cannot inspect the Job before cancellation")
            # The real inspect envelope nests the receipt: data.receipt.
            data = envelope.get("data")
            receipt = data.get("receipt") if isinstance(data, dict) else None
            revision = (
                receipt.get("job_revision") if isinstance(receipt, dict) else None
            )
            if not isinstance(revision, int) or isinstance(revision, bool):
                raise Refusal("the Job receipt carries no job_revision")
            saved = {
                "expected_revision": revision,
                "request_key": entry["request_key"],
                "state": "prepared",
            }
            entry["cancellation"] = saved
            save(run / "run.json", record)
        if saved.get("state") in {"prepared", "prepared-uncertain"}:
            # Byte-identical replay: the persisted revision and key are reused.
            waited, envelope = invoke(
                binary,
                "cancel",
                entry["job_id"],
                "--expected-revision",
                str(saved["expected_revision"]),
                "--request-key",
                saved["request_key"],
                "--json",
            )
            if envelope["ok"]:
                saved.update(
                    {"state": "acknowledged", "response": envelope.get("data")}
                )
                save(run / "run.json", record)
            else:
                issue = envelope.get("error", {})
                code = issue.get("code")
                if code in {"STALE_REVISION", "CONFLICT"}:
                    saved.update({"state": "refused", "error": issue})
                    save(run / "run.json", record)
                    report(
                        "cancel-refused",
                        suite=entry["suite"],
                        job_id=entry["job_id"],
                        error=issue,
                        note="the refused cancellation never reports cancelled; "
                        "the terminal disposition follows",
                    )
                elif waited == 6 or code in {
                    "TRANSPORT_UNCERTAIN",
                    "STORAGE_UNAVAILABLE",
                }:
                    # Uncertain outcome: keep the original payload for
                    # byte-identical replay or native reconciliation.
                    saved.update({"state": "prepared-uncertain", "error": issue})
                    save(run / "run.json", record)
                    report(
                        "cancel-uncertain",
                        suite=entry["suite"],
                        job_id=entry["job_id"],
                        error=issue,
                        note="the cancellation outcome is uncertain; the "
                        "original payload is retained for replay",
                    )
                else:
                    saved.update({"state": "prepared", "error": issue})
                    save(run / "run.json", record)
                    raise Refusal(
                        f"cancellation failed ({code}); the Job continues and "
                        "the payload is retained for replay",
                        native=True,
                        exit_code=waited or 2,
                    )
        outcome, code, detail = wait_for_suite(binary, entry, args)
        native_outcome = outcome
        outcome, code = settle_suite_result(
            binary, run, record, entry, outcome, code, detail
        )
        report(
            "cancel-settled",
            suite=entry["suite"],
            job_id=entry["job_id"],
            cancellation=entry["cancellation"].get("state"),
            outcome=native_outcome,
        )
    report("aggregate", status=outcome, run_dir=str(run))
    return code


def run_probe(binary: str, run: Path, record: dict[str, Any], args: Any) -> int:
    verify_installation_binding(binary, record)
    # Persist the probe classification before the deliberate submit so an
    # existing run keeps its probe-class marking even if the probe fails.
    if not record.get("probe_class"):
        record["probe_class"] = True
        save(run / "run.json", record)
    entry = next(item for item in record["jobs"] if item.get("job_id"))
    if args.probe == "identical-replay":
        waited, envelope = invoke(
            binary,
            "submit",
            "--spec",
            str(run / entry["spec"]),
            "--request-key",
            entry["request_key"],
            "--json",
        )
        replayed = envelope.get("data", {}).get("job_id") if envelope["ok"] else None
        observation = {
            "probe": "identical-replay",
            "ok": bool(envelope["ok"] and replayed == entry["job_id"]),
            "cli_exit": waited,
            "error": envelope.get("error"),
        }
    else:
        target = run / "bundle/harness/tests/vm/recipes/guest_entry.sh"
        if target.is_symlink() or not target.is_file():
            raise Refusal("probe needs a sealed harness input to mutate")
        with target.open("ab") as stream:
            stream.write(b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        waited, envelope = invoke(
            binary,
            "submit",
            "--spec",
            str(run / entry["spec"]),
            "--request-key",
            entry["request_key"],
            "--json",
        )
        code = envelope.get("error", {}).get("code")
        observation = {
            "probe": "changed-survivor-replay",
            "ok": bool(not envelope["ok"] and code == "CONFLICT"),
            "cli_exit": waited,
            "error": envelope.get("error"),
        }
    # Retain every probe observation on the entry, in order.
    entry.setdefault("probe_observations", []).append(observation)
    save(run / "run.json", record)
    report("probe", **observation)
    return 0 if observation["ok"] else 2


def main() -> int:
    args = parse_arguments()
    if os.environ.get("HAEPARI_PARENT_CONTEXT"):
        raise Refusal("the host wrapper cannot enqueue from a managed guest context")
    if not args.haepari or not args.resource or not args.run_dir:
        raise Refusal("HAEPARI, RESOURCE and RUN_DIR are required")
    binary = shutil.which(args.haepari)
    if binary is None:
        raise Refusal("PREREQUISITE_UNAVAILABLE: select an installed Haepari CLI")
    args.haepari = str(Path(binary).resolve())
    run = require_run_dir(args.run_dir)
    report("run", run_dir=str(run))
    lock = os.open(run / "caller.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(lock, "a+") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Refusal("another caller owns this run; reconnect after it exits")
        saved = run / "run.json"
        if saved.exists():
            record = load_record(run)
            validate_record(record, args)
            if args.cancel:
                return cancel_run(args.haepari, run, record, args)
            verify_installation_binding(args.haepari, record)
            if args.probe in {"identical-replay", "changed-survivor-replay"}:
                return run_probe(args.haepari, run, record, args)
        else:
            if any(path.name != "caller.lock" for path in run.iterdir()):
                raise Refusal(
                    "unfinished run preparation is retained; inspect it and select "
                    "a new empty run directory"
                )
            if not args.guest_context:
                raise Refusal(
                    "GUEST_CONTEXT is mandatory for a live submission; supply the "
                    "private guest context file"
                )
            waited, envelope = invoke(
                args.haepari, "doctor", "--resource", args.resource, "--json"
            )
            gap_observation = None
            if args.probe == "admit-despite-gap":
                # Record the very gap this probe admits despite: the CLI
                # exit, the envelope's ok, readiness, each gap's code and
                # message, and the error envelope when ok is false.
                doctor_data = envelope.get("data", {}) if envelope.get("ok") else {}
                gap_observation = {
                    "probe": "admit-despite-gap",
                    "doctor_exit": waited,
                    "doctor_ok": bool(envelope.get("ok")),
                    "ready": bool(doctor_data.get("ready")) if doctor_data else False,
                    "gaps": [
                        {
                            "code": gap.get("code"),
                            "message": gap.get("message"),
                        }
                        for gap in doctor_data.get("gaps", [])
                        if isinstance(gap, dict)
                    ],
                    "error": envelope.get("error") if not envelope.get("ok") else None,
                }
                gap_observation["ok"] = bool(
                    (not doctor_data.get("ready") and gap_observation["gaps"])
                    or gap_observation["error"]
                )
                if not gap_observation["ok"]:
                    raise Refusal(
                        "the probe needs a doctor gap or error to admit "
                        "despite; doctor reported neither, and an ordinary "
                        "run is submitted without AQUARIUM_VM_PROBE"
                    )
                report("probe", **gap_observation)
            elif waited != 0 or not envelope["ok"]:
                issue = envelope.get("error", {})
                raise Refusal(
                    f"{issue.get('code', 'PREREQUISITE_UNAVAILABLE')}: "
                    f"{issue.get('message', 'inspect the controller and HAEPARI_HOME')}"
                )
            doctor = envelope.get("data", {}) if envelope["ok"] else {}
            if doctor and doctor.get("schema") != DOCTOR_SCHEMA:
                raise Refusal("the selected controller lacks the preflight contract")
            if doctor and args.probe != "admit-despite-gap" and not doctor.get("ready"):
                gaps = "; ".join(
                    str(gap.get("message", "")) for gap in doctor.get("gaps", [])
                )
                raise Refusal(f"PREREQUISITE_UNAVAILABLE: {gaps}")
            installation_id = doctor.get("installation_id", "unobserved")
            if args.probe == "admit-despite-gap" and not doctor:
                raise Refusal(
                    "the probe path still needs an installation identity to bind"
                )
            built = host_bundle.build_bundle(
                run,
                Path(args.guest_context),
                args.suite,
                args.resource,
                args.mode,
                candidate_sha=args.candidate_sha,
                artifact_dir=Path(args.artifact_dir) if args.artifact_dir else None,
                artifact_manifest=(
                    json.loads(Path(args.artifact_manifest).read_text(encoding="utf-8"))
                    if args.artifact_manifest
                    else None
                ),
                fixture_requirements=(
                    Path(args.fixture_requirements)
                    if args.fixture_requirements
                    else None
                ),
                queue_override=args.queue_seconds,
                podway_previous_release=Path(args.podway_previous_release)
                if getattr(args, "podway_previous_release", None)
                else None,
                podway_release=Path(args.podway_release)
                if getattr(args, "podway_release", None)
                else None,
            )
            record = {
                "schema": RUN_SCHEMA,
                "installation_id": installation_id,
                "resource": args.resource,
                "suite": args.suite,
                "mode": args.mode,
                "probe_class": bool(args.probe),
                **built,
            }
            if gap_observation is not None:
                # The admitted entry keeps the doctor-gap observation in the
                # probe record list.
                record["jobs"][0]["probe_observations"] = [gap_observation]
            save(saved, record)
        outcome, code = "PASS", 0
        for entry in record["jobs"]:
            if code:
                report(
                    "skipped",
                    suite=entry["suite"],
                    reason=f"earlier suite status is {outcome}",
                )
                continue
            submit_suite(args.haepari, run, record, entry, args)
            if args.probe == "changed-survivor-replay":
                probe_code = run_probe(args.haepari, run, record, args)
                if probe_code != 0:
                    return probe_code
                report(
                    "aggregate",
                    status="PENDING",
                    run_dir=str(run),
                    job_ids=[entry["job_id"]],
                )
                return 5
            outcome, code, detail = wait_for_suite(args.haepari, entry, args)
            outcome, code = settle_suite_result(
                args.haepari, run, record, entry, outcome, code, detail
            )
        report(
            "aggregate",
            status=outcome,
            run_dir=str(run),
            job_ids=[
                entry["job_id"] for entry in record["jobs"] if entry.get("job_id")
            ],
        )
        return code
    return 2


def parse_arguments() -> Any:
    class Arguments:
        pass

    arguments = Arguments()
    arguments.haepari = os.environ.get("HAEPARI", "")
    arguments.resource = os.environ.get("AQUARIUM_VM_RESOURCE", "")
    arguments.mode = os.environ.get("AQUARIUM_VM_MODE", "")
    arguments.suite = os.environ.get("AQUARIUM_VM_SUITE", "")
    arguments.run_dir = os.environ.get("AQUARIUM_VM_RUN_DIR", "")
    arguments.guest_context = os.environ.get("AQUARIUM_VM_GUEST_CONTEXT", "")
    arguments.probe = os.environ.get("AQUARIUM_VM_PROBE", "")
    arguments.cancel = bool(os.environ.get("AQUARIUM_VM_CANCEL"))
    arguments.wait_timeout = int(os.environ.get("AQUARIUM_VM_WAIT_TIMEOUT", "900"))
    arguments.wait_rounds = int(os.environ.get("AQUARIUM_VM_WAIT_ROUNDS", "480"))
    arguments.queue_seconds = (
        int(os.environ["AQUARIUM_VM_QUEUE_SECONDS"])
        if os.environ.get("AQUARIUM_VM_QUEUE_SECONDS")
        else None
    )
    arguments.podway_previous_release = (
        os.environ.get("AQUARIUM_VM_PODWAY_PREVIOUS_RELEASE") or None
    )
    arguments.podway_release = os.environ.get("AQUARIUM_VM_PODWAY_RELEASE") or None
    arguments.candidate_sha = os.environ.get("AQUARIUM_VM_CANDIDATE_SHA") or None
    arguments.artifact_dir = os.environ.get("AQUARIUM_VM_ARTIFACT_DIR") or None
    arguments.artifact_manifest = (
        os.environ.get("AQUARIUM_VM_ARTIFACT_MANIFEST") or None
    )
    arguments.fixture_requirements = (
        os.environ.get("AQUARIUM_VM_FIXTURE_REQUIREMENTS") or None
    )
    if arguments.probe and arguments.probe not in PROBE_KINDS:
        raise Refusal(f"unknown probe kind: {arguments.probe}")
    if arguments.mode not in {"auto", "manual"}:
        raise Refusal("MODE must be auto or manual")
    if not arguments.suite:
        raise Refusal("SUITE is required")
    return arguments


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (Refusal, OSError, ValueError, KeyError, TypeError) as error:
        native = getattr(error, "native", False)
        report("refusal", source="native" if native else "wrapper", message=str(error))
        sys.exit(getattr(error, "exit_code", 2))
