from __future__ import annotations

import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import types
import unittest
from pathlib import Path
from unittest import mock

REPOSITORY = Path(__file__).resolve().parents[2]
WRAPPER_PATH = REPOSITORY / "tests/vm/host_wrapper.py"
EXPORT_SKELETON_PATH = (
    REPOSITORY
    / "tests/unit/fixtures/vm_host/haepari-v0.1.0-export-manifest-skeleton.json"
)
INSPECT_SKELETON_PATH = (
    REPOSITORY
    / "tests/unit/fixtures/vm_host/haepari-v0.1.0-inspect-queued-skeleton.json"
)


def inspect_envelope(job_revision: int) -> dict:
    """A real-shaped queued-Job inspect envelope: data.receipt."""
    return envelope(
        "inspect",
        {
            "receipt": {
                "admission": {
                    "admitted_at": "2026-10-24T00:00:00Z",
                    "environment_profile_digest": "a" * 64,
                    "environment_profile_id": "synthetic-profile",
                    "input_digest": "b" * 64,
                    "object_id": "c" * 64,
                    "request_key": "rk-synthetic",
                    "resource_config_revision": 1,
                    "resource_id": "synthetic-resource",
                    "sequence": 1,
                    "submitted_digest": "d" * 64,
                },
                "capacity_delta": 1,
                "event_cursor": 0,
                "global_occupancy": 1,
                "job_id": "job-synthetic-1",
                "job_revision": job_revision,
                "job_state": "queued",
                "lease_generation": 1,
                "resource_availability": "available",
                "resource_availability_revision": 1,
                "resource_config_revision": 1,
                "resource_id": "synthetic-resource",
                "resource_occupancy": 1,
                "slot": 0,
            }
        },
    )


def export_manifest_skeleton(value):
    """The committed real-manifest skeleton: dict → the same keys
    recursively, non-empty list → the skeleton of element 0, empty list →
    [], scalar → its Python type name."""
    if isinstance(value, dict):
        return {key: export_manifest_skeleton(item) for key, item in value.items()}
    if isinstance(value, list):
        return [export_manifest_skeleton(value[0])] if value else []
    return type(value).__name__


GUEST_CONTEXT = {
    "schema": "aquarium.vm-guest-context/v1",
    "expected_guest_uuid": "11111111-2222-3333-4444-555555555555",
    "guest_home": "/Users/synthetic",
    "guest_path": "/Users/synthetic/.local/bin:/usr/bin:/bin",
    "guest_python": "/Users/synthetic/.local/bin/python3.14",
    "guest_codex": "/Users/synthetic/.local/bin/codex",
    "guest_podway": "/Users/synthetic/.local/bin/podway",
    "guest_marketplace_name": "synthetic-market",
}

FAKE_CLI = """#!/usr/bin/env python3
import json
import os
import sys

arguments = sys.argv[1:]
state = os.environ["FAKE_HAEPARI_STATE"]
run_dir = os.environ.get("AQUARIUM_VM_RUN_DIR", "")
entry = {"argv": arguments}
if arguments[:2] == ["submit", "--spec"]:
    entry["spec_exists"] = os.path.isfile(arguments[2])
    entry["run_json_exists"] = os.path.isfile(os.path.join(run_dir, "run.json"))
with open(os.path.join(state, "log.jsonl"), "a") as stream:
    stream.write(json.dumps(entry) + "\\n")
defaults = {
    "doctor": {
        "schema": "haepari.envelope/v1", "operation": "doctor", "ok": True,
        "data": {"schema": "haepari.doctor/v1", "installation_id": "local-synthetic",
                 "ready": True, "gaps": []},
    },
    "events-heartbeat": [
        {
            "schema": "haepari.observer/v1",
            "type": "page",
            "job_id": "job-synthetic-1",
            "events": {
                "events": [],
                "current_cursor": 4,
                "next_cursor": 4,
                "snapshot": {
                    "job_id": "job-synthetic-1",
                    "job_revision": 6,
                    "job_state": "running",
                },
                "more": False,
            },
            "cursor": 4,
        },
    ],
    "events-awaiting": [
        {
            "schema": "haepari.observer/v1",
            "type": "page",
            "job_id": "job-synthetic-1",
            "events": {
                "events": [],
                "current_cursor": 9,
                "next_cursor": 9,
                "snapshot": {
                    "job_id": "job-synthetic-1",
                    "job_revision": 6,
                    "job_state": "awaiting_manual",
                    "result_status": "available",
                },
                "more": False,
            },
            "cursor": 9,
        },
    ],
    "events-finished": [
        {
            "schema": "haepari.observer/v1",
            "type": "page",
            "job_id": "job-synthetic-1",
            "events": {
                "events": [],
                "current_cursor": 9,
                "next_cursor": 9,
                "snapshot": {
                    "job_id": "job-synthetic-1",
                    "job_revision": 6,
                    "job_state": "finished",
                    "result_status": "available",
                },
                "more": False,
            },
            "cursor": 9,
        },
        {
            "schema": "haepari.observer/v1",
            "type": "end",
            "job_id": "job-synthetic-1",
            "reason": "finished",
            "cursor": 9,
        },
    ],
    "jobs": {
        "schema": "haepari.envelope/v1", "operation": "jobs-list", "ok": True,
        "data": {"jobs": [], "more": False},
    },
    "resources": {
        "schema": "haepari.envelope/v1", "operation": "resources-list", "ok": True,
        "data": {"resources": [{"resource_id": "synthetic-resource", "occupancy": 0}],
                 "more": False},
    },
}
if "events" not in defaults:
    defaults["events"] = defaults["events-finished"]

queue = sorted(name for name in os.listdir(state) if name.startswith("response-"))
selected = None
for name in queue:
    with open(os.path.join(state, name)) as handle:
        scripted = json.load(handle)
    if scripted.get("match", arguments[0]) == arguments[0]:
        selected = (name, scripted)
        break
if selected is not None:
    os.unlink(os.path.join(state, selected[0]))
    payload = selected[1]["stdout"]
    if isinstance(payload, dict) and "__stream__" in payload:
        stream_name = payload["__stream__"]
        for record in defaults[stream_name]:
            print(json.dumps(record), flush=True)
        import time as _time
        while True:
            _time.sleep(0.2)
            print(
                json.dumps(
                    {
                        "schema": "haepari.observer/v1",
                        "type": "heartbeat",
                        "job_id": "job-synthetic-1",
                        "cursor": 9,
                    }
                ),
                flush=True,
            )
    for record in payload if isinstance(payload, list) else [payload]:
        print(json.dumps(record))
    raise SystemExit(selected[1]["exit"])
if arguments[0] == "export" and "--to" in arguments:
    import hashlib
    destination = arguments[arguments.index("--to") + 1]
    os.makedirs(os.path.join(destination, "artifacts"), exist_ok=True)
    record_path = os.path.join(run_dir, "run.json")
    suites = []
    if os.path.isfile(record_path):
        record = json.load(open(record_path))
        suites = [entry["suite"] for entry in record.get("jobs", [])]
    files = []
    result_artifacts = []
    consumer = os.environ.get("FAKE_EXPORT_CONSUMER", "verified")
    if os.environ.get("FAKE_EXPORT_CONSUMER_LIST"):
        # Fixture-side fault: a malformed claim value in the suite result.
        consumer = []
    elif os.environ.get("FAKE_EXPORT_CONSUMER_DICT"):
        consumer = {}
    incomplete = os.environ.get("FAKE_EXPORT_INCOMPLETE")
    binding = record.get("installation_binding", {}) if record else {}
    candidate = {
        "git_sha": binding.get("candidate_git_sha"),
        "development_version": binding.get("development_version"),
        "artifact_tree_sha256": binding.get("artifact_tree_sha256"),
    }
    mismatch = os.environ.get("FAKE_EXPORT_CANDIDATE_MISMATCH")
    missing_artifact = os.environ.get("FAKE_EXPORT_MISSING_ARTIFACT")
    digest_drift = os.environ.get("FAKE_EXPORT_DIGEST_DRIFT")
    disagree = os.environ.get("FAKE_EXPORT_DISAGREE")
    bad_prefix = os.environ.get("FAKE_EXPORT_BAD_PREFIX")
    symlinked = os.environ.get("FAKE_EXPORT_SYMLINK")
    result_mismatch = os.environ.get("FAKE_EXPORT_RESULT_JOB_MISMATCH")
    for index, suite in enumerate(suites):
        spec_path = os.path.join(run_dir, f"spec-{index}.json")
        spec = json.load(open(spec_path)) if os.path.isfile(spec_path) else {}
        outputs = spec.get("workload", {}).get("required_outputs", [])
        if incomplete is not None and index == 0 and len(outputs) > 1:
            outputs = outputs[:-1]
        for position, relative in enumerate(outputs):
            if relative.endswith("result.json"):
                carried = dict(candidate)
                if mismatch:
                    carried["git_sha"] = "0" * 40
                content = json.dumps(
                    {
                        "suite": suite,
                        "consumer_cleanup": consumer,
                        "candidate": carried,
                    }
                )
            else:
                content = json.dumps({"synthetic": relative})
            export_path = os.path.join(destination, "artifacts", relative)
            os.makedirs(os.path.dirname(export_path), exist_ok=True)
            open(export_path, "w").write(content)
            digest = hashlib.sha256(content.encode()).hexdigest()
            size_bytes = len(content.encode())
            first = not position and not index
            files.append(
                {
                    "path": "artifacts/" + relative,
                    "sha256": "0" * 64 if digest_drift and first else digest,
                    "size_bytes": size_bytes,
                }
            )
            if not (missing_artifact and first):
                result_artifacts.append(
                    {
                        "path": relative,
                        "size_bytes": size_bytes + 1 if disagree and first else size_bytes,
                        "sha256": digest,
                    }
                )
            if symlinked and first:
                os.unlink(export_path)
                os.symlink("output.log", export_path)
    log = "synthetic workload log\\n"
    open(os.path.join(destination, "output.log"), "w").write(log)
    log_digest = hashlib.sha256(log.encode()).hexdigest()
    log_size = len(log.encode())
    files.append(
        {"path": "output.log", "sha256": log_digest, "size_bytes": log_size}
    )
    if bad_prefix:
        body = "flatly exported file\\n"
        open(os.path.join(destination, "flat-output.txt"), "w").write(body)
        files.append(
            {
                "path": "flat-output.txt",
                "sha256": hashlib.sha256(body.encode()).hexdigest(),
                "size_bytes": len(body.encode()),
            }
        )
    result = {
        "schema": "haepari.result/v2",
        "job_id": "job-someone-else" if result_mismatch else arguments[1],
        "job_state": "finished",
        "final_verdict": "pass",
        "workload_outcome": "pass",
        "cleanup_outcome": "verified",
        "evidence_completeness": "complete",
        "resource_availability": "available",
        "resource_id": "synthetic-resource",
        "lease_generation": 1,
        "native_exit_code": 0,
        "resource_revision": 1,
        "artifacts": result_artifacts,
        "logs": [
            {"path": "output.log", "sha256": log_digest, "size_bytes": log_size}
        ],
        "timings": {
            "admitted_at": "2026-10-24T00:00:00Z",
            "reserved_at": "2026-10-24T00:00:00Z",
            "adapter_steps": [{"step": "ssh-ready", "duration_millis": 1}],
            "phases": [
                {
                    "phase": "run",
                    "started_at": "2026-10-24T00:00:00Z",
                    "ended_at": "2026-10-24T00:00:01Z",
                }
            ],
        },
    }
    open(os.path.join(destination, "result.json"), "w").write(json.dumps(result))
    manifest = {
        "schema": "haepari.artifact-manifest/v1",
        "job_id": arguments[1],
        "result": result,
        "files": files,
        "supplementary": [],
    }
    open(os.path.join(destination, "manifest.json"), "w").write(
        json.dumps(manifest))
    print(json.dumps({"schema": "haepari.envelope/v1", "operation": "export",
                      "ok": True, "data": {"destination": destination}}))
    raise SystemExit(0)
default = defaults.get(arguments[0])
if default is not None:
    import sys as _sys
    import time as _time
    if (
        arguments[0] == "events"
        and "--follow" in arguments
        and os.environ.get("FAKE_RESISTANT_GRANDCHILD")
    ):
        # A grandchild that ignores SIGTERM and inherits stdout; only the
        # always-SIGKILL escalation with an unreaped leader can end it.
        import signal as _signal
        import subprocess as _sp

        ready = os.path.join(run_dir, "resistant-grandchild.ready")
        resistant = _sp.Popen(
            [
                _sys.executable,
                "-c",
                "import os, signal, time"
                + chr(10)
                + "signal.signal(signal.SIGTERM, signal.SIG_IGN)"
                + chr(10)
                + "open(r'"
                + ready
                + "', 'w').close()"
                + chr(10)
                + "while True: time.sleep(0.2)",
            ],
            stdout=_sys.stdout,
            stderr=_sys.stderr,
        )
        with open(os.path.join(run_dir, "resistant-grandchild.pid"), "w") as pidf:
            pidf.write(str(resistant.pid))
        # Do not report readiness before the SIG_IGN handler is installed,
        # so teardown signals always land after it.
        import time as _rtime

        for _ in range(50):
            if os.path.exists(ready):
                break
            _rtime.sleep(0.1)
        print(
            json.dumps(
                {
                    "schema": "haepari.observer/v1",
                    "type": "page",
                    "job_id": "job-synthetic-1",
                    "events": {
                        "events": [],
                        "current_cursor": 8,
                        "next_cursor": 8,
                        "snapshot": {
                            "job_id": "job-synthetic-1",
                            "job_revision": 6,
                            "job_state": "awaiting_manual",
                        },
                        "more": False,
                    },
                    "cursor": 8,
                }
            ),
            flush=True,
        )
        while True:
            _time.sleep(0.2)
    if (
        arguments[0] == "events"
        and "--follow" in arguments
        and os.environ.get("FAKE_GRANDCHILD_STREAM")
    ):
        # Spawn a grandchild that inherits stdout and keeps it open after
        # this process exits; only a group-wide teardown closes the pipe.
        import subprocess as _sp

        _sp.Popen(
            [_sys.executable, "-c", "import time" + chr(10) + "while True: time.sleep(0.2)"],
            stdout=_sys.stdout,
            stderr=_sys.stderr,
        )
        print(
            json.dumps(
                {
                    "schema": "haepari.observer/v1",
                    "type": "page",
                    "job_id": "job-synthetic-1",
                    "events": {
                        "events": [],
                        "current_cursor": 8,
                        "next_cursor": 8,
                        "snapshot": {
                            "job_id": "job-synthetic-1",
                            "job_revision": 6,
                            "job_state": "awaiting_manual",
                        },
                        "more": False,
                    },
                    "cursor": 8,
                }
            ),
            flush=True,
        )
        while True:
            _time.sleep(0.2)
    if (
        arguments[0] == "events"
        and "--follow" in arguments
        and os.environ.get("FAKE_EOF_STREAM")
    ):
        # Close stdout, then stay alive: EOF without process exit.
        import os as _os
        import time as _eof_time

        _os.close(1)
        while True:
            _eof_time.sleep(0.2)
    if arguments[0] == "events" and "--follow" in arguments:
        if os.environ.get("FAKE_SILENT_STREAM"):
            # A truly silent open stream: emit nothing, ever.
            import time as _silent_time

            while True:
                _silent_time.sleep(0.2)
    for record in default if isinstance(default, list) else [default]:
        print(json.dumps(record), flush=True)
    if arguments[0] == "events" and "--follow" in arguments:
        if default is defaults.get("events-awaiting"):
            while True:
                _time.sleep(0.2)
                print(
                    json.dumps(
                        {
                            "schema": "haepari.observer/v1",
                            "type": "heartbeat",
                            "job_id": "job-synthetic-1",
                            "cursor": 9,
                        }
                    ),
                    flush=True,
                )
    raise SystemExit(0)
print(json.dumps({"schema": "haepari.envelope/v1", "operation": "fallback", "ok": False,
                  "error": {"code": "INVALID_REQUEST", "message": "no scripted response",
                            "retry": "none"}}))
raise SystemExit(2)
"""


def envelope(operation: str, data: dict) -> dict:
    return {
        "schema": "haepari.envelope/v1",
        "operation": operation,
        "ok": True,
        "data": data,
    }


def error_envelope(code: str, retry: str = "none") -> dict:
    return {
        "schema": "haepari.envelope/v1",
        "operation": "error",
        "ok": False,
        "error": {"code": code, "message": code, "retry": retry},
    }


class HostWrapperTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix="vm-host-wrapper-")).resolve()
        cls.addClassCleanup(shutil.rmtree, cls.work, True)
        cls.fake = cls.work / "fake-haepari"
        cls.fake.write_text(FAKE_CLI)
        cls.fake.chmod(0o755)
        cls.context = cls.work / "guest-context.json"
        cls.context.write_text(json.dumps(GUEST_CONTEXT))
        cls.git_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPOSITORY,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        cls.artifact = cls.work / "artifact/marketplace"
        plugin = cls.artifact / "plugins/aquarium/.codex-plugin"
        plugin.mkdir(parents=True)
        (plugin / "plugin.json").write_text(
            json.dumps({"version": f"0.1.21-dev.{cls.git_sha[:12]}"}, indent=2) + "\n"
        )
        (cls.artifact / ".agents/plugins").mkdir(parents=True)
        (cls.artifact / ".agents/plugins/marketplace.json").write_text(
            '{"name": "synthetic-market"}\n'
        )
        cls.manifest = {
            "schema": "aquarium-dev-artifact-manifest/v1",
            "git_sha": cls.git_sha,
            "development_version": f"v0.1.21-dev.{cls.git_sha[:12]}",
            "artifact_path": "marketplace",
        }
        cls.manifest_path = cls.work / "artifact-manifest.json"
        cls.manifest_path.write_text(json.dumps(cls.manifest))

    def scenario(self, name: str) -> tuple[Path, Path]:
        run_dir = Path(tempfile.mkdtemp(prefix=f"run-{name}-", dir=str(self.work)))
        run_dir.chmod(0o700)
        state = Path(tempfile.mkdtemp(prefix=f"state-{name}-", dir=str(self.work)))
        return run_dir, state

    def respond(
        self, state: Path, exit_code: int, stdout: dict, match: str | None = None
    ) -> None:
        index = len(list(state.glob("response-*")))
        (state / f"response-{index:03d}.json").write_text(
            json.dumps(
                {"exit": exit_code, "stdout": stdout, "match": match or "scripted"}
            )
        )

    def invoke_wrapper(
        self,
        run_dir: Path,
        state: Path,
        *,
        suite_declarations: Path | None = None,
        **overrides,
    ) -> subprocess.CompletedProcess:
        environment = {
            **os.environ,
            "HAEPARI": str(self.fake),
            "FAKE_HAEPARI_STATE": str(state),
            "AQUARIUM_VM_RESOURCE": "synthetic-resource",
            "AQUARIUM_VM_MODE": "auto",
            "AQUARIUM_VM_SUITE": "install",
            "AQUARIUM_VM_RUN_DIR": str(run_dir),
            "AQUARIUM_VM_GUEST_CONTEXT": str(self.context),
            "AQUARIUM_VM_ARTIFACT_DIR": str(self.artifact),
            "AQUARIUM_VM_ARTIFACT_MANIFEST": str(self.manifest_path),
            "AQUARIUM_VM_WAIT_TIMEOUT": "1",
            "AQUARIUM_VM_WAIT_ROUNDS": "2",
            "AQUARIUM_VM_FIXTURE_REQUIREMENTS": "",
            "AQUARIUM_VM_PODWAY_RELEASE": "",
            "AQUARIUM_VM_CANDIDATE_SHA": "",
            "AQUARIUM_VM_QUEUE_SECONDS": "",
            "AQUARIUM_VM_PROBE": "",
            "AQUARIUM_VM_CANCEL": "",
        }
        environment.update({key: str(value) for key, value in overrides.items()})
        command = [sys.executable, "-B", str(WRAPPER_PATH)]
        if suite_declarations is not None:
            # Isolate generic queue behavior from release-input provisioning.
            command = [
                sys.executable,
                "-B",
                "-c",
                (
                    "import sys; from pathlib import Path; "
                    f"sys.path.insert(0, {str(WRAPPER_PATH.parent)!r}); "
                    "import host_bundle, host_wrapper; "
                    "load_suites = host_bundle.load_suites; "
                    f"host_bundle.load_suites = lambda: load_suites(Path({str(suite_declarations)!r})); "
                    "sys.exit(host_wrapper.main())"
                ),
            ]
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            env=environment,
            timeout=600,
            check=False,
        )

    def doctor_ok(self, state: Path, ready: bool = True, exit_code: int = 0) -> None:
        self.respond(
            state,
            exit_code,
            envelope(
                "doctor",
                {
                    "schema": "haepari.doctor/v1",
                    "installation_id": "local-synthetic",
                    "ready": ready,
                    "gaps": []
                    if ready
                    else [
                        {
                            "code": "running_vm_unavailable",
                            "message": (
                                "The registered VM is not currently running; "
                                "select an already-running authorized VM. No VM "
                                "or environment repair was performed."
                            ),
                        }
                    ],
                },
            ),
            match="doctor",
        )

    def submit_ok(self, state: Path, job_id: str = "job-synthetic-1") -> None:
        self.respond(state, 0, envelope("submit", {"job_id": job_id}), match="submit")

    def log_entries(self, state: Path) -> list[dict]:
        log = state / "log.jsonl"
        if not log.is_file():
            return []
        return [json.loads(line) for line in log.read_text().splitlines() if line]

    def test_fresh_submission_persisted_before_submit(self):
        run_dir, state = self.scenario("fresh")
        self.doctor_ok(state)
        self.submit_ok(state)
        self.respond(
            state, 0, envelope("wait", {"final_verdict": "PASS"}), match="wait"
        )
        result = self.invoke_wrapper(run_dir, state)
        self.assertEqual(result.returncode, 0, result.stderr)
        submits = [e for e in self.log_entries(state) if e["argv"][0] == "submit"]
        self.assertEqual(len(submits), 1)
        self.assertTrue(submits[0]["spec_exists"])
        self.assertTrue(submits[0]["run_json_exists"])
        record = json.loads((run_dir / "run.json").read_text())
        self.assertEqual(record["jobs"][0]["job_id"], "job-synthetic-1")
        self.assertEqual(record["installation_id"], "local-synthetic")

    def test_reconnect_reuses_job_without_resubmission(self):
        run_dir, state = self.scenario("reconnect")
        self.doctor_ok(state)
        self.submit_ok(state)
        self.respond(state, 5, error_envelope("WAIT_TIMEOUT", "none"), match="wait")
        first = self.invoke_wrapper(run_dir, state, AQUARIUM_VM_WAIT_ROUNDS="1")
        self.assertEqual(first.returncode, 5)
        self.doctor_ok(state)
        self.respond(
            state, 0, envelope("wait", {"final_verdict": "PASS"}), match="wait"
        )
        second = self.invoke_wrapper(run_dir, state)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(
            len([e for e in self.log_entries(state) if e["argv"][0] == "submit"]), 1
        )

    def test_verdict_and_exit_mapping(self):
        for verdict, expected in (
            ("FAIL", 1),
            ("INCOMPLETE", 3),
            ("CANCELLED", 4),
        ):
            run_dir, state = self.scenario(f"verdict-{verdict}")
            self.doctor_ok(state)
            self.submit_ok(state)
            self.respond(
                state,
                expected,
                envelope("wait", {"final_verdict": verdict}),
                match="wait",
            )
            self.respond(
                state,
                0,
                envelope("export", {"destination": "synthetic"}),
                match="export",
            )
            result = self.invoke_wrapper(run_dir, state)
            self.assertEqual(result.returncode, expected, verdict)

    def test_uncertain_observation_preserves_native_exit(self):
        run_dir, state = self.scenario("unknown")
        self.doctor_ok(state)
        self.submit_ok(state)
        self.respond(
            state, 6, error_envelope("TRANSPORT_UNCERTAIN", "reconcile"), match="wait"
        )
        result = self.invoke_wrapper(run_dir, state)
        self.assertEqual(result.returncode, 6)
        self.assertIn('"UNKNOWN"', result.stdout)

    def test_result_unavailable_is_classified_not_uncertain(self):
        run_dir, state = self.scenario("unavailable")
        self.doctor_ok(state)
        self.submit_ok(state)
        self.respond(
            state,
            2,
            error_envelope("RESULT_UNAVAILABLE", "reconcile"),
            match="wait",
        )
        result = self.invoke_wrapper(run_dir, state)
        self.assertEqual(result.returncode, 2)
        self.assertIn('"UNAVAILABLE"', result.stdout)
        self.assertNotIn('"UNKNOWN"', result.stdout)

    def test_all_reports_skipped_suites_after_failure(self):
        run_dir, state = self.scenario("all")
        declarations = json.loads(
            (REPOSITORY / "tests/vm/host_suites.json").read_text()
        )
        declarations["suites"] = {
            name: declarations["suites"][name] for name in ("baseline", "manual-hold")
        }
        suites = state / "suites.json"
        suites.write_text(json.dumps(declarations))
        self.doctor_ok(state)
        self.submit_ok(state)
        self.respond(
            state, 1, envelope("wait", {"final_verdict": "FAIL"}), match="wait"
        )
        result = self.invoke_wrapper(
            run_dir, state, suite_declarations=suites, AQUARIUM_VM_SUITE="all"
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout.count('"kind": "skipped"'), 1)
        record = json.loads((run_dir / "run.json").read_text())
        self.assertEqual(record["declared_suites"], ["baseline", "manual-hold"])

    def test_all_missing_podway_release_refuses_before_submission(self):
        run_dir, state = self.scenario("all-missing-podway")
        self.doctor_ok(state)
        result = self.invoke_wrapper(run_dir, state, AQUARIUM_VM_SUITE="all")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((run_dir / "run.json").exists())
        self.assertFalse(
            any(row["argv"][:1] == ["submit"] for row in self.log_entries(state))
        )

    def test_changed_survivor_probe_conflicts_and_stays_pending(self):
        run_dir, state = self.scenario("conflict")
        self.doctor_ok(state)
        self.submit_ok(state)
        self.respond(state, 2, error_envelope("CONFLICT", "none"), match="submit")
        result = self.invoke_wrapper(
            run_dir, state, AQUARIUM_VM_PROBE="changed-survivor-replay"
        )
        self.assertEqual(result.returncode, 5)
        self.assertIn('"changed-survivor-replay"', result.stdout)
        record = json.loads((run_dir / "run.json").read_text())
        self.assertTrue(record["probe_class"])

    def test_cancel_refusal_keeps_terminal_disposition(self):
        run_dir, state = self.scenario("cancel-refused")
        self.doctor_ok(state)
        self.submit_ok(state)
        self.respond(state, 5, error_envelope("WAIT_TIMEOUT", "none"), match="wait")
        pending = self.invoke_wrapper(run_dir, state, AQUARIUM_VM_WAIT_ROUNDS="1")
        self.assertEqual(pending.returncode, 5)
        self.doctor_ok(state)
        self.respond(state, 0, inspect_envelope(3), match="inspect")
        self.respond(state, 2, error_envelope("STALE_REVISION", "none"), match="cancel")
        self.respond(
            state, 0, envelope("wait", {"final_verdict": "PASS"}), match="wait"
        )
        result = self.invoke_wrapper(run_dir, state, AQUARIUM_VM_CANCEL="1")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("cancel-refused", result.stdout)
        self.assertIn('"cancellation": "refused", "outcome": "PASS"', result.stdout)
        self.assertNotIn('"CANCELLED"', result.stdout)
        record = json.loads((run_dir / "run.json").read_text())
        self.assertEqual(record["jobs"][0]["cancellation"]["state"], "refused")
        self.assertEqual(record["jobs"][0]["cancellation"]["expected_revision"], 3)
        self.assertEqual(
            record["jobs"][0]["observation"]["consumer_cleanup"], "verified"
        )
        self.assertTrue(
            (run_dir / f"export-{record['jobs'][0]['suite']}/manifest.json").is_file()
        )

    def test_cancel_race_blocks_missing_or_failed_consumer_evidence(self):
        for fault in ("unavailable", "incomplete", "failed"):
            with self.subTest(fault=fault):
                run_dir, state = self.scenario(f"cancel-consumer-{fault}")
                self.doctor_ok(state)
                self.submit_ok(state)
                self.respond(
                    state, 5, error_envelope("WAIT_TIMEOUT", "none"), match="wait"
                )
                pending = self.invoke_wrapper(
                    run_dir, state, AQUARIUM_VM_WAIT_ROUNDS="1"
                )
                self.assertEqual(pending.returncode, 5)
                self.doctor_ok(state)
                self.respond(state, 0, inspect_envelope(3), match="inspect")
                self.respond(
                    state, 2, error_envelope("STALE_REVISION", "none"), match="cancel"
                )
                self.respond(
                    state, 0, envelope("wait", {"final_verdict": "PASS"}), match="wait"
                )
                environment = {}
                if fault == "unavailable":
                    self.respond(
                        state, 2, error_envelope("RESULT_UNAVAILABLE"), match="export"
                    )
                elif fault == "incomplete":
                    environment["FAKE_EXPORT_INCOMPLETE"] = "1"
                else:
                    environment["FAKE_EXPORT_CONSUMER"] = "failed"
                result = self.invoke_wrapper(
                    run_dir, state, AQUARIUM_VM_CANCEL="1", **environment
                )
                self.assertEqual(result.returncode, 3, result.stdout)
                self.assertIn('"status": "ACCEPTANCE-BLOCKED"', result.stdout)
                record = json.loads((run_dir / "run.json").read_text())
                observation = record["jobs"][0]["observation"]
                self.assertEqual(observation["outcome"], "PASS")
                self.assertEqual(observation["acceptance"], "blocked")
                self.assertEqual(
                    observation["consumer_cleanup"],
                    "failed" if fault == "failed" else "unverified",
                )

    def test_cancel_uncertainty_preserves_replay_payload(self):
        run_dir, state = self.scenario("cancel-uncertain")
        self.doctor_ok(state)
        self.submit_ok(state)
        self.respond(state, 5, error_envelope("WAIT_TIMEOUT", "none"), match="wait")
        pending = self.invoke_wrapper(run_dir, state, AQUARIUM_VM_WAIT_ROUNDS="1")
        self.assertEqual(pending.returncode, 5)
        self.doctor_ok(state)
        self.respond(state, 0, inspect_envelope(5), match="inspect")
        self.respond(
            state,
            6,
            error_envelope("TRANSPORT_UNCERTAIN", "reconcile"),
            match="cancel",
        )
        self.respond(state, 5, error_envelope("WAIT_TIMEOUT", "none"), match="wait")
        uncertain = self.invoke_wrapper(
            run_dir, state, AQUARIUM_VM_CANCEL="1", AQUARIUM_VM_WAIT_ROUNDS="1"
        )
        self.assertEqual(uncertain.returncode, 5, uncertain.stdout)
        self.assertIn("cancel-uncertain", uncertain.stdout)
        record = json.loads((run_dir / "run.json").read_text())
        self.assertEqual(
            record["jobs"][0]["cancellation"]["state"], "prepared-uncertain"
        )
        self.assertEqual(record["jobs"][0]["cancellation"]["expected_revision"], 5)
        # Byte-identical replay after uncertainty: same revision and key.
        self.respond(
            state, 0, envelope("cancel", {"acknowledged": True}), match="cancel"
        )
        self.respond(
            state, 4, envelope("wait", {"final_verdict": "CANCELLED"}), match="wait"
        )
        settled = self.invoke_wrapper(run_dir, state, AQUARIUM_VM_CANCEL="1")
        self.assertEqual(settled.returncode, 4, settled.stdout)
        log = [
            entry for entry in self.log_entries(state) if entry["argv"][0] == "cancel"
        ]
        self.assertEqual(len(log), 2)
        self.assertEqual(
            log[0]["argv"][log[0]["argv"].index("--expected-revision") + 1 :],
            log[1]["argv"][log[1]["argv"].index("--expected-revision") + 1 :],
        )

    def test_export_failure_blocks_acceptance(self):
        run_dir, state = self.scenario("export-fail")
        self.doctor_ok(state)
        self.submit_ok(state)
        self.respond(
            state, 0, envelope("wait", {"final_verdict": "PASS"}), match="wait"
        )
        self.respond(
            state, 2, error_envelope("STORAGE_UNAVAILABLE", "reconcile"), match="export"
        )
        result = self.invoke_wrapper(run_dir, state)
        self.assertEqual(result.returncode, 3, result.stdout)
        self.assertIn('"final_verdict": "PASS"', result.stdout)
        self.assertIn('"acceptance": "blocked"', result.stdout)

    def test_cancel_terminates_admitted_job(self):
        run_dir, state = self.scenario("cancel")
        self.doctor_ok(state)
        self.submit_ok(state)
        self.respond(state, 5, error_envelope("WAIT_TIMEOUT", "none"), match="wait")
        pending = self.invoke_wrapper(run_dir, state, AQUARIUM_VM_WAIT_ROUNDS="1")
        self.assertEqual(pending.returncode, 5)
        self.respond(state, 0, inspect_envelope(4), match="inspect")
        self.respond(
            state, 0, envelope("cancel", {"acknowledged": True}), match="cancel"
        )
        self.respond(
            state, 4, envelope("wait", {"final_verdict": "CANCELLED"}), match="wait"
        )
        cancelled = self.invoke_wrapper(run_dir, state, AQUARIUM_VM_CANCEL="1")
        self.assertEqual(cancelled.returncode, 4, cancelled.stdout)

    def test_c35_cancel_record_carries_full_native_observation(self):
        run_dir, state = self.scenario("c35-cancel-record")
        self.doctor_ok(state)
        self.submit_ok(state)
        self.respond(state, 5, error_envelope("WAIT_TIMEOUT", "none"), match="wait")
        pending = self.invoke_wrapper(run_dir, state, AQUARIUM_VM_WAIT_ROUNDS="1")
        self.assertEqual(pending.returncode, 5)
        self.doctor_ok(state)
        self.respond(state, 0, inspect_envelope(7), match="inspect")
        self.respond(
            state, 0, envelope("cancel", {"acknowledged": True}), match="cancel"
        )
        self.respond(
            state,
            4,
            envelope(
                "wait",
                {
                    "final_verdict": "CANCELLED",
                    "workload_outcome": "cancelled",
                    "evidence_completeness": "not_needed",
                    "cleanup_outcome": "not_needed",
                },
            ),
            match="wait",
        )
        cancelled = self.invoke_wrapper(run_dir, state, AQUARIUM_VM_CANCEL="1")
        self.assertEqual(cancelled.returncode, 4, cancelled.stdout)
        record = json.loads((run_dir / "run.json").read_text())
        observation = record["jobs"][0]["observation"]
        self.assertEqual(observation["outcome"], "CANCELLED")
        self.assertEqual(observation["final_verdict"], "CANCELLED")
        self.assertEqual(observation["workload_outcome"], "cancelled")
        self.assertEqual(observation["evidence_completeness"], "not_needed")
        self.assertEqual(observation["cleanup_outcome"], "not_needed")

    def test_c35_probe_observations_accumulate_on_one_run(self):
        run_dir, state = self.scenario("c35-probes")
        self.doctor_ok(state)
        self.submit_ok(state)
        self.respond(
            state, 0, envelope("wait", {"final_verdict": "PASS"}), match="wait"
        )
        ordinary = self.invoke_wrapper(run_dir, state)
        self.assertEqual(ordinary.returncode, 0, ordinary.stdout)
        record = json.loads((run_dir / "run.json").read_text())
        self.assertFalse(record.get("probe_class"))
        self.assertNotIn("probe_observations", record["jobs"][0])
        # Identical replay on the same run: the run becomes probe-class and
        # keeps its first observation.
        self.doctor_ok(state)
        self.respond(
            state,
            0,
            envelope("submit", {"job_id": "job-synthetic-1"}),
            match="submit",
        )
        replay = self.invoke_wrapper(
            run_dir, state, AQUARIUM_VM_PROBE="identical-replay"
        )
        self.assertEqual(replay.returncode, 0, replay.stdout)
        record = json.loads((run_dir / "run.json").read_text())
        self.assertTrue(record["probe_class"])
        self.assertEqual(len(record["jobs"][0]["probe_observations"]), 1)
        # Changed survivor on the same run: the earlier observation stays
        # and the conflict appends after it.
        self.doctor_ok(state)
        self.respond(state, 2, error_envelope("CONFLICT", "none"), match="submit")
        conflict = self.invoke_wrapper(
            run_dir, state, AQUARIUM_VM_PROBE="changed-survivor-replay"
        )
        self.assertEqual(conflict.returncode, 0, conflict.stdout)
        record = json.loads((run_dir / "run.json").read_text())
        self.assertTrue(record["probe_class"])
        self.assertEqual(
            [item["probe"] for item in record["jobs"][0]["probe_observations"]],
            ["identical-replay", "changed-survivor-replay"],
        )

    def test_manual_hold_reports_pending_with_completion_guidance(self):
        run_dir, state = self.scenario("manual")
        self.doctor_ok(state)
        self.submit_ok(state)
        self.respond(state, 5, error_envelope("WAIT_TIMEOUT", "none"), match="wait")
        # The stream stays open (heartbeats) after the awaiting snapshot;
        # readiness must return promptly via the intentional local stop.
        self.respond(
            state,
            0,
            {"__stream__": "events-awaiting"},
            match="events",
        )
        result = self.invoke_wrapper(
            run_dir,
            state,
            AQUARIUM_VM_MODE="manual",
            AQUARIUM_VM_SUITE="manual-hold",
            AQUARIUM_VM_WAIT_ROUNDS="1",
        )
        self.assertEqual(result.returncode, 5)
        self.assertIn("manual complete", result.stdout)
        self.assertIn("manual-hold", result.stdout)

    def test_admit_despite_gap_probe_proceeds(self):
        run_dir, state = self.scenario("gap")
        self.doctor_ok(state, ready=False, exit_code=2)
        self.submit_ok(state)
        self.respond(
            state, 0, envelope("wait", {"final_verdict": "PASS"}), match="wait"
        )
        result = self.invoke_wrapper(
            run_dir, state, AQUARIUM_VM_PROBE="admit-despite-gap"
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        record = json.loads((run_dir / "run.json").read_text())
        self.assertEqual(record["installation_id"], "local-synthetic")
        self.assertTrue(record["probe_class"])
        observations = record["jobs"][0]["probe_observations"]
        self.assertEqual(len(observations), 1)
        observation = observations[0]
        self.assertEqual(observation["probe"], "admit-despite-gap")
        self.assertEqual(observation["doctor_exit"], 2)
        self.assertTrue(observation["doctor_ok"])
        self.assertFalse(observation["ready"])
        self.assertEqual(observation["gaps"][0]["code"], "running_vm_unavailable")
        self.assertEqual(
            observation["gaps"][0]["message"],
            "The registered VM is not currently running; select an "
            "already-running authorized VM. No VM or environment repair was "
            "performed.",
        )
        self.assertTrue(observation["ok"])
        self.assertIn('"probe": "admit-despite-gap"', result.stdout)
        self.assertIn('"doctor_exit": 2', result.stdout)
        self.assertIn("running_vm_unavailable", result.stdout)

    def test_c40_admit_despite_gap_without_gap_refused(self):
        run_dir, state = self.scenario("c40-ready")
        self.doctor_ok(state)
        result = self.invoke_wrapper(
            run_dir, state, AQUARIUM_VM_PROBE="admit-despite-gap"
        )
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn(
            "the probe needs a doctor gap or error to admit despite", result.stdout
        )
        self.assertIn(
            "an ordinary run is submitted without AQUARIUM_VM_PROBE", result.stdout
        )
        self.assertFalse((run_dir / "run.json").exists())

    def test_c39_admit_despite_gap_error_envelope_recorded(self):
        run_dir, state = self.scenario("c39-gap-error")
        self.respond(
            state,
            2,
            {
                "schema": "haepari.envelope/v1",
                "operation": "doctor",
                "ok": False,
                "error": {"code": "DIAGNOSTIC_FAILED", "message": "unreachable"},
            },
            match="doctor",
        )
        result = self.invoke_wrapper(
            run_dir, state, AQUARIUM_VM_PROBE="admit-despite-gap"
        )
        # The probe line records the error envelope before the existing
        # identity-binding refusal stops the submission.
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn('"probe": "admit-despite-gap"', result.stdout)
        self.assertFalse(json.loads(result.stdout.splitlines()[1])["doctor_ok"])
        self.assertIn("DIAGNOSTIC_FAILED", result.stdout)
        self.assertIn("installation identity", result.stdout)

    def test_c39_gap_without_probe_still_refused(self):
        run_dir, state = self.scenario("c39-gap-refused")
        self.doctor_ok(state, ready=False, exit_code=2)
        result = self.invoke_wrapper(run_dir, state)
        self.assertEqual(result.returncode, 2)
        self.assertIn("PREREQUISITE_UNAVAILABLE", result.stdout)
        record_path = run_dir / "run.json"
        self.assertFalse(record_path.exists())

    def test_missing_guest_context_refuses_at_host_boundary(self):
        run_dir, state = self.scenario("nocontext")
        self.doctor_ok(state)
        result = self.invoke_wrapper(run_dir, state, AQUARIUM_VM_GUEST_CONTEXT="")
        self.assertEqual(result.returncode, 2)
        self.assertIn("GUEST_CONTEXT", result.stdout)

    def test_insecure_run_dir_refuses(self):
        run_dir, state = self.scenario("mode")
        run_dir.chmod(0o755)
        result = self.invoke_wrapper(run_dir, state)
        self.assertEqual(result.returncode, 2)
        run_dir.chmod(0o700)

    def test_queue_budget_refuses_when_two_jobs_are_ahead(self):
        run_dir, state = self.scenario("queue")
        self.doctor_ok(state)
        self.respond(
            state,
            0,
            envelope("jobs-list", {"jobs": [{"job_id": "a"}], "more": False}),
            match="jobs",
        )
        self.respond(
            state,
            0,
            envelope(
                "resources-list",
                {"resources": [{"resource_id": "synthetic-resource", "occupancy": 1}]},
            ),
            match="resources",
        )
        result = self.invoke_wrapper(run_dir, state)
        self.assertEqual(result.returncode, 2)
        self.assertIn("tagged minimum", result.stdout)
        self.assertEqual(
            len([e for e in self.log_entries(state) if e["argv"][0] == "submit"]), 0
        )

    def test_unavailable_resource_inventory_preserves_unsubmitted_request(self):
        module = self._load_host_wrapper_module("hw_resource_inventory_error")
        for exit_code, code in (
            (6, "STORAGE_UNAVAILABLE"),
            (6, "TRANSPORT_UNCERTAIN"),
            (2, "INVALID_REQUEST"),
        ):
            with self.subTest(code=code):
                run = Path(tempfile.mkdtemp(prefix="queue-unavailable-", dir=self.work))
                spec = run / "spec-0.json"
                spec.write_text(
                    json.dumps(
                        {
                            "resource_id": "synthetic-resource",
                            "deadlines": {"queue_seconds": 26100},
                        }
                    )
                )
                entry = {
                    "suite": "release-acceptance",
                    "spec": spec.name,
                    "spec_sha256": hashlib.sha256(spec.read_bytes()).hexdigest(),
                    "request_key": "saved-queue-request",
                    "submission_started": False,
                }
                record = {"jobs": [entry]}
                module.save(run / "run.json", record)
                before = (run / "run.json").read_bytes()
                native_error = error_envelope(
                    code, "reconcile" if exit_code == 6 else "none"
                )
                responses = [
                    (0, envelope("jobs.list", {"jobs": [], "more": False})),
                    (exit_code, native_error),
                ]
                with (
                    mock.patch.object(module, "invoke", side_effect=responses) as calls,
                    self.assertRaises(module.Refusal) as raised,
                ):
                    module.submit_suite(
                        "fixture-haepari",
                        run,
                        record,
                        entry,
                        types.SimpleNamespace(resource="synthetic-resource"),
                    )
                self.assertTrue(raised.exception.native)
                self.assertEqual(raised.exception.exit_code, exit_code)
                message = str(raised.exception)
                self.assertEqual(
                    json.loads(message[message.index("{") :]), native_error["error"]
                )
                self.assertNotIn(
                    "submit", [call.args[1] for call in calls.call_args_list]
                )
                self.assertFalse(entry["submission_started"])
                self.assertNotIn("job_id", entry)
                self.assertEqual((run / "run.json").read_bytes(), before)

    def test_s5_2_kill_and_reconnect_same_job_and_export_reuse(self):
        run_dir, state = self.scenario("reconnect-hold")
        self.doctor_ok(state)
        self.submit_ok(state)
        self.respond(state, 5, error_envelope("WAIT_TIMEOUT", "none"), match="wait")
        self.respond(state, 0, {"__stream__": "events-awaiting"}, match="events")
        first = self.invoke_wrapper(
            run_dir,
            state,
            AQUARIUM_VM_MODE="manual",
            AQUARIUM_VM_SUITE="manual-hold",
            AQUARIUM_VM_WAIT_ROUNDS="1",
        )
        self.assertEqual(first.returncode, 5)
        self.assertIn("manual complete", first.stdout)
        # The operator completes the manual scenario natively; the wrapper is
        # "killed" (its process ended above) and reconnects with the same
        # RUN_DIR: same Job ID, no new submission, terminal verdict + export.
        self.doctor_ok(state)
        self.respond(
            state, 3, envelope("wait", {"final_verdict": "INCOMPLETE"}), match="wait"
        )
        second = self.invoke_wrapper(
            run_dir,
            state,
            AQUARIUM_VM_MODE="manual",
            AQUARIUM_VM_SUITE="manual-hold",
            AQUARIUM_VM_WAIT_ROUNDS="1",
        )
        self.assertEqual(second.returncode, 3, second.stdout)
        self.assertIn('"kind": "reconnect"', second.stdout)
        self.assertIn('"kind": "export"', second.stdout)
        submits = [
            entry for entry in self.log_entries(state) if entry["argv"][0] == "submit"
        ]
        self.assertEqual(len(submits), 1)
        # A third invocation reconnects to the settled Job and reuses the
        # receipt-verified export from the second invocation.
        self.doctor_ok(state)
        self.respond(
            state, 3, envelope("wait", {"final_verdict": "INCOMPLETE"}), match="wait"
        )
        third = self.invoke_wrapper(
            run_dir,
            state,
            AQUARIUM_VM_MODE="manual",
            AQUARIUM_VM_SUITE="manual-hold",
            AQUARIUM_VM_WAIT_ROUNDS="1",
        )
        self.assertEqual(third.returncode, 3, third.stdout)
        self.assertIn('"kind": "reconnect"', third.stdout)
        self.assertIn("export-reuse", third.stdout)

    def test_c8_f1_heartbeat_stream_past_budget_returns(self):
        import time

        run_dir, state = self.scenario("budget-heartbeat")
        self.doctor_ok(state)
        self.submit_ok(state)
        self.respond(state, 5, error_envelope("WAIT_TIMEOUT", "none"), match="wait")
        # Heartbeats forever; no awaiting snapshot, no end.
        self.respond(state, 0, {"__stream__": "events-heartbeat"}, match="events")
        started = time.monotonic()
        result = self.invoke_wrapper(
            run_dir,
            state,
            AQUARIUM_VM_MODE="manual",
            AQUARIUM_VM_SUITE="manual-hold",
            AQUARIUM_VM_WAIT_TIMEOUT="2",
            AQUARIUM_VM_WAIT_ROUNDS="1",
        )
        elapsed = time.monotonic() - started
        # Budget expiry ends observation with PENDING; the wrapper returns
        # within the budget plus a small margin, never hanging.
        self.assertEqual(result.returncode, 5, result.stdout)
        self.assertLess(elapsed, 60)
        self.assertIn('"reason": "budget"', result.stdout)

    def test_c8_f1_silent_stream_returns_within_budget(self):
        import time

        run_dir, state = self.scenario("budget-silent")
        self.doctor_ok(state)
        self.submit_ok(state)
        self.respond(state, 5, error_envelope("WAIT_TIMEOUT", "none"), match="wait")
        # A truly silent stream: the fake emits nothing and stays open
        # until terminated; the wrapper must still return within budget.
        started = time.monotonic()
        result = self.invoke_wrapper(
            run_dir,
            state,
            AQUARIUM_VM_MODE="manual",
            AQUARIUM_VM_SUITE="manual-hold",
            AQUARIUM_VM_WAIT_TIMEOUT="2",
            AQUARIUM_VM_WAIT_ROUNDS="1",
            FAKE_SILENT_STREAM="1",
        )
        elapsed = time.monotonic() - started
        self.assertEqual(result.returncode, 5, result.stdout)
        self.assertLess(elapsed, 60)

    def test_c9_f1_eof_before_process_exit_returns_within_bounds(self):
        import time

        run_dir, state = self.scenario("eof-stall")
        self.doctor_ok(state)
        self.submit_ok(state)
        self.respond(state, 5, error_envelope("WAIT_TIMEOUT", "none"), match="wait")
        started = time.monotonic()
        result = self.invoke_wrapper(
            run_dir,
            state,
            AQUARIUM_VM_MODE="manual",
            AQUARIUM_VM_SUITE="manual-hold",
            AQUARIUM_VM_WAIT_TIMEOUT="2",
            AQUARIUM_VM_WAIT_ROUNDS="1",
            FAKE_EOF_STREAM="1",
        )
        elapsed = time.monotonic() - started
        self.assertEqual(result.returncode, 5, result.stdout)
        self.assertLess(elapsed, 60)
        self.assertIn('"reason": "eof"', result.stdout)

    def test_c10_f3_reader_lifecycle_verified_on_stop_paths(self):
        # Readiness path: reader ended, stream closed, no teardown report.
        run_dir, state = self.scenario("lifecycle-ready")
        self.doctor_ok(state)
        self.submit_ok(state)
        self.respond(state, 5, error_envelope("WAIT_TIMEOUT", "none"), match="wait")
        self.respond(state, 0, {"__stream__": "events-awaiting"}, match="events")
        result = self.invoke_wrapper(
            run_dir,
            state,
            AQUARIUM_VM_MODE="manual",
            AQUARIUM_VM_SUITE="manual-hold",
            AQUARIUM_VM_WAIT_ROUNDS="1",
        )
        self.assertEqual(result.returncode, 5, result.stdout)
        self.assertIn("observer-stopped-locally", result.stdout)
        self.assertNotIn("observer-teardown-incomplete", result.stdout)

    def test_c10_f3_budget_stop_reader_lifecycle_verified(self):
        run_dir, state = self.scenario("lifecycle-budget")
        self.doctor_ok(state)
        self.submit_ok(state)
        self.respond(state, 5, error_envelope("WAIT_TIMEOUT", "none"), match="wait")
        self.respond(state, 0, {"__stream__": "events-heartbeat"}, match="events")
        result = self.invoke_wrapper(
            run_dir,
            state,
            AQUARIUM_VM_MODE="manual",
            AQUARIUM_VM_SUITE="manual-hold",
            AQUARIUM_VM_WAIT_TIMEOUT="2",
            AQUARIUM_VM_WAIT_ROUNDS="1",
        )
        self.assertEqual(result.returncode, 5, result.stdout)
        self.assertIn('"reason": "budget"', result.stdout)
        self.assertNotIn("observer-teardown-incomplete", result.stdout)

    def test_c10_f3_grandchild_stdout_tears_down_cleanly(self):
        run_dir, state = self.scenario("lifecycle-grandchild")
        self.doctor_ok(state)
        self.submit_ok(state)
        self.respond(state, 5, error_envelope("WAIT_TIMEOUT", "none"), match="wait")
        result = self.invoke_wrapper(
            run_dir,
            state,
            AQUARIUM_VM_MODE="manual",
            AQUARIUM_VM_SUITE="manual-hold",
            AQUARIUM_VM_WAIT_ROUNDS="1",
            FAKE_GRANDCHILD_STREAM="1",
        )
        # Group-aware teardown: readiness returns promptly, the reader ended
        # and the stream closed — no teardown-incomplete classification.
        self.assertEqual(result.returncode, 5, result.stdout)
        self.assertIn("manual complete", result.stdout)
        self.assertIn('"reason": "readiness"', result.stdout)
        self.assertNotIn("observer-teardown-incomplete", result.stdout)
        self.assertNotIn("follow-teardown-incomplete", result.stdout)

    def test_c11_d10_sigterm_ignoring_grandchild_torn_down(self):
        run_dir, state = self.scenario("lifecycle-resistant")
        self.doctor_ok(state)
        self.submit_ok(state)
        self.respond(state, 5, error_envelope("WAIT_TIMEOUT", "none"), match="wait")
        started = time.time()
        result = self.invoke_wrapper(
            run_dir,
            state,
            AQUARIUM_VM_MODE="manual",
            AQUARIUM_VM_SUITE="manual-hold",
            AQUARIUM_VM_WAIT_ROUNDS="1",
            FAKE_RESISTANT_GRANDCHILD="1",
        )
        elapsed = time.time() - started
        # The always-SIGKILL escalation (leader unreaped, pgid pinned)
        # kills the resistant grandchild: bounded completion, reader ended,
        # stream closed, readiness still reported.
        self.assertEqual(result.returncode, 5, result.stdout)
        self.assertLess(elapsed, 60)
        self.assertIn('"reason": "readiness"', result.stdout)
        self.assertNotIn("observer-teardown-incomplete", result.stdout)
        self.assertNotIn("follow-teardown-incomplete", result.stdout)
        # Behavioral assertion: the SIGTERM-ignoring grandchild is dead —
        # the always-SIGKILL escalation reached it while the unreaped
        # leader still pinned the process group.
        pid_file = run_dir / "resistant-grandchild.pid"
        self.assertTrue(pid_file.is_file())
        grandchild = int(pid_file.read_text())
        deadline = time.time() + 10
        while time.time() < deadline:
            try:
                os.kill(grandchild, 0)
            except (ProcessLookupError, PermissionError):
                break
            time.sleep(0.2)
        else:
            os.kill(grandchild, signal.SIGKILL)
            raise AssertionError(f"resistant grandchild {grandchild} survived teardown")

    def _kill_unreaped_children(self, processes):
        # Ownership-aware test cleanup: a child whose returncode is set was
        # already reaped (by Observer.stop() or an earlier cleanup pass) and
        # is never signalled — its pid may already have been reused.
        for process in processes:
            if process.returncode is not None:
                continue
            try:
                os.kill(process.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            deadline = time.time() + 5
            while time.time() < deadline:
                try:
                    waited, status = os.waitpid(process.pid, os.WNOHANG)
                except (ChildProcessError, OSError):
                    break
                if waited == process.pid:
                    process.returncode = os.waitstatus_to_exitcode(status)
                    break
                time.sleep(0.05)

    def _join_observers(self, observers):
        # Join each production reader and close any fd teardown retained.
        for observer in observers:
            if observer.reader is not None:
                observer.reader.join(timeout=5)
            if observer.read_fd is not None:
                os.close(observer.read_fd)
                observer.read_fd = None

    def _close_open_fds(self, fds):
        # Fallback for a regression: close recorded descriptors still open.
        for fd in fds:
            try:
                os.fstat(fd)
            except OSError:
                continue
            try:
                os.close(fd)
            except OSError:
                pass

    def test_c11_d10_blocked_reader_real_pipe_incomplete(self):
        # Blocked reader via the production code path: the reader blocks
        # inside its patched select() call on the real pipe (fault
        # injection in the module namespace, never substituting the reader
        # or the teardown); teardown must report the incomplete
        # classification and keep the fd open.
        import threading as _threading

        module = self._load_host_wrapper_module("hw_blocked_reader")

        state = self.work / "blocked-reader-fake"
        state.mkdir(exist_ok=True)
        os.environ["HAEPARI"] = str(self.fake)
        os.environ["FAKE_HAEPARI_STATE"] = str(state)
        self.addCleanup(os.environ.pop, "HAEPARI", None)
        self.addCleanup(os.environ.pop, "FAKE_HAEPARI_STATE", None)
        self.respond(state, 0, {"__stream__": "events-awaiting"}, match="events")

        release = _threading.Event()
        entered = _threading.Event()
        observer_holder = {}
        real_select = module.select.select
        real_observer = module.Observer
        real_thread = module.threading.Thread

        def stuck_select(*args, **kwargs):
            # Block only the production reader inside its real select call;
            # the main thread's selects pass through. entered records that
            # the reader verifiably reached this call.
            if _threading.current_thread() is observer_holder.get("reader_thread"):
                entered.set()
                release.wait()
            return real_select(*args, **kwargs)

        def capturing_thread(*args, **kwargs):
            # Record the reader object before it starts, so its very first
            # select call is identified — no start-up race.
            thread = real_thread(*args, **kwargs)
            observer_holder["reader_thread"] = thread
            return thread

        def capturing_observer(arguments):
            observer = real_observer(arguments)
            observer_holder["observer"] = observer
            # Return only once the reader sits inside the patched select,
            # so the stop below always meets a blocked reader.
            if not entered.wait(timeout=5):
                raise AssertionError("production reader never entered select")
            return observer

        def cleanup_blocked_reader():
            release.set()
            observer = observer_holder.get("observer")
            if observer is None:
                return
            if observer.reader is not None:
                observer.reader.join(timeout=5)
            if observer.read_fd is not None:
                os.close(observer.read_fd)
                observer.read_fd = None

        # Registered before the fault path: a failing assertion below still
        # releases, joins and closes what the test created.
        self.addCleanup(cleanup_blocked_reader)
        module.select.select = stuck_select
        module.Observer = capturing_observer
        try:
            with mock.patch.object(module.threading, "Thread", capturing_thread):
                outcome = module.follow_to_awaiting(
                    str(self.fake), "job-synthetic-1", 3
                )
        finally:
            module.select.select = real_select
            module.Observer = real_observer
        observer = observer_holder.get("observer")
        self.assertIsNotNone(observer)
        self.assertIsInstance(outcome, dict)
        self.assertEqual(outcome.get("code"), "OBSERVER_TEARDOWN_INCOMPLETE")
        self.assertIn("reader thread did not terminate", outcome.get("problem", ""))
        self.assertIsNotNone(observer.read_fd, "fd closed under a live reader")

    def _load_host_wrapper_module(self, name: str):
        import importlib.util

        spec = importlib.util.spec_from_file_location(name, WRAPPER_PATH)
        module = importlib.util.module_from_spec(spec)
        tests_vm = str(WRAPPER_PATH.parent)
        if tests_vm not in sys.path:
            sys.path.insert(0, tests_vm)
            self.addCleanup(sys.path.remove, tests_vm)
        spec.loader.exec_module(module)
        return module

    def test_c12_d11_spawn_failure_closes_both_fds(self):
        # Behavioral through the production entry: a spawn failure must not
        # leak the allocated pipe descriptors.
        module = self._load_host_wrapper_module("hw_spawn_fail")
        created = []
        real_pipe = os.pipe

        def recording_pipe():
            fds = real_pipe()
            created.extend(fds)
            return fds

        def fd_open(fd):
            try:
                os.fstat(fd)
                return True
            except OSError:
                return False

        # Registered before the fault path: a failing assertion below still
        # closes descriptors a regression leaked.
        self.addCleanup(self._close_open_fds, created)
        with (
            mock.patch.object(module.os, "pipe", recording_pipe),
            mock.patch.object(
                module.subprocess, "Popen", side_effect=OSError("spawn failed")
            ),
            self.assertRaises(OSError),
        ):
            module.follow_to_awaiting(str(self.fake), "job-s", 2)
        self.assertTrue(created)
        leaked = [fd for fd in created if fd_open(fd)]
        self.assertEqual(leaked, [])

    def test_c12_d11_reader_start_failure_tears_observer_down(self):
        module = self._load_host_wrapper_module("hw_reader_fail")
        started = []
        created = []
        real_popen = module.subprocess.Popen
        real_pipe = os.pipe

        def recording_popen(*args, **kwargs):
            process = real_popen(*args, **kwargs)
            started.append(process)
            return process

        def recording_pipe():
            fds = real_pipe()
            created.extend(fds)
            return fds

        def failing_start(self_thread):
            raise RuntimeError("no thread")

        # Registered before the fault path: a failing assertion below still
        # reaps the observer child and closes anything left open.
        self.addCleanup(self._close_open_fds, created)
        self.addCleanup(self._kill_unreaped_children, started)
        with (
            mock.patch.object(module.os, "pipe", recording_pipe),
            mock.patch.object(module.subprocess, "Popen", recording_popen),
            mock.patch.object(module.threading.Thread, "start", failing_start),
            self.assertRaises(RuntimeError),
        ):
            module.follow_to_awaiting(str(self.fake), "job-r", 2)
        self.assertEqual(len(started), 1)
        # The observer must have been torn down: reaped (returncode set),
        # not left running.
        self.assertIsNotNone(started[0].returncode)

    def test_c12_d11_bounded_reap_failure_reported(self):
        module = self._load_host_wrapper_module("hw_reap_fail")
        observers = []
        real_observer = getattr(module, "Observer", None)
        if real_observer is not None:
            real = real_observer

            def capturing(arguments):
                observer = real(arguments)
                observers.append(observer)
                return observer

            module.Observer = capturing
            self.addCleanup(setattr, module, "Observer", real)
        started = []
        real_popen = module.subprocess.Popen

        def recording_popen(*args, **kwargs):
            process = real_popen(*args, **kwargs)
            started.append(process)
            return process

        # Registered before the fault path: a failing assertion below still
        # reaps the observer child, joins its reader and closes the fd.
        self.addCleanup(self._join_observers, observers)
        self.addCleanup(self._kill_unreaped_children, started)
        with (
            mock.patch.object(module.subprocess, "Popen", recording_popen),
            mock.patch.object(module.os, "waitpid", return_value=(0, 0)),
        ):
            outcome = module.follow_to_awaiting(str(self.fake), "job-b", 2)
        self.assertIsInstance(outcome, dict)
        self.assertEqual(outcome.get("code"), "OBSERVER_TEARDOWN_INCOMPLETE")
        self.assertIn("not reaped within bounds", outcome.get("problem", ""))

    def test_c12_d11_lost_ownership_reported(self):
        module = self._load_host_wrapper_module("hw_owner_lost")
        observers = []
        real_observer = getattr(module, "Observer", None)
        if real_observer is not None:
            real = real_observer

            def capturing(arguments):
                observer = real(arguments)
                observers.append(observer)
                return observer

            module.Observer = capturing
            self.addCleanup(setattr, module, "Observer", real)
        started = []
        real_popen = module.subprocess.Popen

        def recording_popen(*args, **kwargs):
            process = real_popen(*args, **kwargs)
            started.append(process)
            return process

        # Registered before the fault path: a failing assertion below still
        # reaps the observer child, joins its reader and closes the fd.
        self.addCleanup(self._join_observers, observers)
        self.addCleanup(self._kill_unreaped_children, started)
        with (
            mock.patch.object(module.subprocess, "Popen", recording_popen),
            mock.patch.object(
                module.os, "waitid", side_effect=ChildProcessError("gone")
            ),
        ):
            outcome = module.follow_to_awaiting(str(self.fake), "job-o", 2)
        self.assertIsInstance(outcome, dict)
        self.assertEqual(outcome.get("code"), "OBSERVER_TEARDOWN_INCOMPLETE")
        self.assertIn("no longer an owned child", outcome.get("problem", ""))

    def test_c10_f3_forced_teardown_failure_classified(self):
        # In-process fault injection: import the wrapper module and call
        # follow_to_awaiting directly with a monkeypatched reader that can
        # never finish — no environment hook the production code reads.
        import importlib.util
        import threading as _threading

        tests_vm = str(WRAPPER_PATH.parent)
        if tests_vm not in sys.path:
            sys.path.insert(0, tests_vm)
            self.addCleanup(sys.path.remove, tests_vm)
        spec = importlib.util.spec_from_file_location(
            "host_wrapper_under_test", WRAPPER_PATH
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        state = self.work / "stuck-reader-fake"
        state.mkdir(exist_ok=True)
        os.environ["HAEPARI"] = str(self.fake)
        os.environ["FAKE_HAEPARI_STATE"] = str(state)
        self.addCleanup(os.environ.pop, "HAEPARI", None)
        self.addCleanup(os.environ.pop, "FAKE_HAEPARI_STATE", None)
        self.respond(state, 0, {"__stream__": "events-awaiting"}, match="events")
        original_thread = module.threading.Thread
        release = _threading.Event()

        def stuck_reader(*args, **kwargs):
            kwargs["target"] = lambda *a, **k: release.wait()
            return original_thread(*args, **kwargs)

        module.threading.Thread = stuck_reader
        try:
            outcome = module.follow_to_awaiting(str(self.fake), "job-synthetic-1", 3)
        finally:
            module.threading.Thread = original_thread
            release.set()
        self.assertIsInstance(outcome, dict)
        self.assertEqual(outcome.get("code"), "OBSERVER_TEARDOWN_INCOMPLETE")
        self.assertIn("reader thread did not terminate", outcome.get("problem", ""))

    def test_c8_f3_real_sigterm_reconnect_same_job_no_resubmit(self):
        self._c8_kill_and_reconnect(signal.SIGTERM)

    def test_c8_f3_real_sigkill_reconnect_same_job_no_resubmit(self):
        self._c8_kill_and_reconnect(signal.SIGKILL)

    def _c8_kill_and_reconnect(self, sig):
        run_dir, state = self.scenario(f"kill-{sig.name}")
        self.doctor_ok(state)
        self.submit_ok(state)
        # Long wait so the wrapper is still blocking when we signal it.
        self.respond_many(
            state,
            "wait",
            [(5, error_envelope("WAIT_TIMEOUT", "none")) for _ in range(50)],
        )
        environment = self._environment_for(run_dir, state)
        process = subprocess.Popen(
            [sys.executable, "-B", str(WRAPPER_PATH)],
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        try:
            deadline = time.time() + 420
            record_path = run_dir / "run.json"
            while time.time() < deadline:
                if record_path.is_file():
                    try:
                        record = json.loads(record_path.read_text())
                    except ValueError:
                        record = None
                    if record and record.get("jobs", [{}])[0].get("job_id"):
                        break
                time.sleep(0.2)
            else:
                self.fail("wrapper never persisted the Job ID")
            killed = record["jobs"][0]["job_id"]
            key = record["jobs"][0]["request_key"]
            process.send_signal(sig)
            process.wait(timeout=30)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=10)
        # Drain any leftover wait responses from the killed phase (a fake
        # child of the killed wrapper may consume one late), then queue the
        # settled sequence for the reconnection.
        time.sleep(1.0)
        for response in sorted(state.glob("response-*")):
            response.unlink()
        # Reconnect with the same RUN_DIR: same Job, no new submit.
        self.doctor_ok(state)
        self.respond(
            state,
            3,
            envelope("wait", {"final_verdict": "INCOMPLETE"}),
            match="wait",
        )
        settled = self.invoke_wrapper(
            run_dir,
            state,
            AQUARIUM_VM_WAIT_ROUNDS="1",
        )
        self.assertEqual(settled.returncode, 3, settled.stdout)
        after = json.loads(record_path.read_text())
        self.assertEqual(after["jobs"][0]["job_id"], killed)
        self.assertEqual(after["jobs"][0]["request_key"], key)
        submits = [
            entry for entry in self.log_entries(state) if entry["argv"][0] == "submit"
        ]
        self.assertEqual(len(submits), 1)
        # Third invocation reuses the receipt-verified export.
        for response in sorted(state.glob("response-*")):
            response.unlink()
        self.doctor_ok(state)
        self.respond(
            state,
            3,
            envelope("wait", {"final_verdict": "INCOMPLETE"}),
            match="wait",
        )
        third = self.invoke_wrapper(run_dir, state, AQUARIUM_VM_WAIT_ROUNDS="1")
        self.assertEqual(third.returncode, 3, third.stdout)
        self.assertIn("export-reuse", third.stdout)

    def respond_many(self, state: Path, match: str, responses):
        for exit_code, payload in responses:
            self.respond(state, exit_code, payload, match=match)

    def _environment_for(self, run_dir: Path, state: Path):
        environment = dict(os.environ)
        environment.update(
            {
                "HAEPARI": str(self.fake),
                "FAKE_HAEPARI_STATE": str(state),
                "AQUARIUM_VM_RESOURCE": "synthetic-resource",
                "AQUARIUM_VM_MODE": "auto",
                "AQUARIUM_VM_SUITE": "install",
                "AQUARIUM_VM_RUN_DIR": str(run_dir),
                "AQUARIUM_VM_GUEST_CONTEXT": str(self.context),
                "AQUARIUM_VM_ARTIFACT_DIR": str(self.artifact),
                "AQUARIUM_VM_ARTIFACT_MANIFEST": str(self.manifest_path),
                "AQUARIUM_VM_WAIT_TIMEOUT": "1",
                "AQUARIUM_VM_WAIT_ROUNDS": "480",
                "AQUARIUM_VM_FIXTURE_REQUIREMENTS": "",
                "AQUARIUM_VM_CANDIDATE_SHA": "",
                "AQUARIUM_VM_QUEUE_SECONDS": "",
                "AQUARIUM_VM_PROBE": "",
                "AQUARIUM_VM_CANCEL": "",
            }
        )
        return environment

    def test_c6_f3_readiness_returns_promptly_with_open_stream(self):
        import time

        run_dir, state = self.scenario("readiness-open")
        self.doctor_ok(state)
        self.submit_ok(state)
        self.respond(state, 5, error_envelope("WAIT_TIMEOUT", "none"), match="wait")
        # The stream heartbeats forever after the awaiting_manual snapshot.
        self.respond(state, 0, {"__stream__": "events-awaiting"}, match="events")
        started = time.monotonic()
        result = self.invoke_wrapper(
            run_dir,
            state,
            AQUARIUM_VM_MODE="manual",
            AQUARIUM_VM_SUITE="manual-hold",
            AQUARIUM_VM_WAIT_ROUNDS="1",
        )
        elapsed = time.monotonic() - started
        self.assertEqual(result.returncode, 5, result.stdout)
        self.assertLess(elapsed, 30, "readiness must return promptly")
        self.assertIn("manual complete", result.stdout)
        self.assertIn("observer-stopped-locally", result.stdout)
        self.assertIn('"reason": "readiness"', result.stdout)

    def test_c5_f6_follow_permanent_error_is_terminal(self):
        run_dir, state = self.scenario("follow-error")
        self.doctor_ok(state)
        self.submit_ok(state)
        self.respond(state, 5, error_envelope("WAIT_TIMEOUT", "none"), match="wait")
        # The follow stream emits a permanent error record and exits 2.
        self.respond(
            state,
            2,
            [
                {
                    "schema": "haepari.observer/v1",
                    "type": "error",
                    "job_id": "job-synthetic-1",
                    "error": {"code": "RESULT_UNAVAILABLE", "message": "gone"},
                    "cursor": 3,
                }
            ],
            match="events",
        )
        result = self.invoke_wrapper(
            run_dir,
            state,
            AQUARIUM_VM_MODE="manual",
            AQUARIUM_VM_SUITE="manual-hold",
            AQUARIUM_VM_WAIT_ROUNDS="1",
        )
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("follow-terminal-error", result.stdout)
        self.assertIn("RESULT_UNAVAILABLE", result.stdout)

    def test_c5_f5_export_candidate_mismatch_blocks_acceptance(self):
        run_dir, state = self.scenario("candidate-mismatch")
        self.doctor_ok(state)
        self.submit_ok(state)
        self.respond(
            state, 0, envelope("wait", {"final_verdict": "PASS"}), match="wait"
        )
        result = self.invoke_wrapper(run_dir, state, FAKE_EXPORT_CANDIDATE_MISMATCH="1")
        self.assertEqual(result.returncode, 3, result.stdout)
        self.assertIn("export-unverified", result.stdout)
        self.assertIn('"final_verdict": "PASS"', result.stdout)

    def test_incomplete_export_manifest_blocks_acceptance(self):
        run_dir, state = self.scenario("export-incomplete")
        self.doctor_ok(state)
        self.submit_ok(state)
        self.respond(
            state,
            0,
            envelope("wait", {"final_verdict": "PASS"}),
            match="wait",
        )
        result = self.invoke_wrapper(
            run_dir,
            state,
            AQUARIUM_VM_SUITE="manual-hold",
            AQUARIUM_VM_MODE="manual",
            FAKE_EXPORT_INCOMPLETE="1",
            AQUARIUM_VM_WAIT_ROUNDS="1",
        )
        self.assertEqual(result.returncode, 3, result.stdout)
        self.assertIn("export-unverified", result.stdout)
        self.assertIn('"final_verdict": "PASS"', result.stdout)
        self.assertIn('"acceptance": "blocked"', result.stdout)

    def test_failed_consumer_cleanup_blocks_acceptance(self):
        run_dir, state = self.scenario("consumer")
        self.doctor_ok(state)
        self.submit_ok(state)
        self.respond(
            state, 0, envelope("wait", {"final_verdict": "PASS"}), match="wait"
        )
        result = self.invoke_wrapper(run_dir, state, FAKE_EXPORT_CONSUMER="failed")
        self.assertEqual(result.returncode, 3)
        self.assertIn('"consumer_cleanup": "failed"', result.stdout)
        self.assertIn('"final_verdict": "PASS"', result.stdout)
        self.assertIn('"acceptance": "blocked"', result.stdout)

    def test_c32_fake_inspect_envelopes_match_haepari_skeleton(self):
        # Every fake inspect envelope the tests use is built by
        # inspect_envelope and must carry the real v0.1.0 queued shape.
        skeleton = json.loads(INSPECT_SKELETON_PATH.read_text())
        for revision in (3, 4, 5):
            self.assertEqual(
                export_manifest_skeleton(inspect_envelope(revision)), skeleton
            )

    def _real_layout_export(self, name: str) -> tuple[Path, dict, list, dict]:
        """A trimmed static export of the real J-BASE #2 v0.1.0 layout."""
        destination = self.work / f"export-fixture-{name}"
        (destination / "artifacts/results/baseline").mkdir(parents=True)
        sealed = {
            "git_sha": "1" * 40,
            "development_version": "v0.1.21-dev.synthetic",
            "artifact_tree_sha256": "2" * 64,
        }
        entries = [
            (
                "results/baseline/result.json",
                json.dumps(
                    {
                        "schema": "aquarium.vm-suite-result/v1",
                        "suite": "baseline",
                        "outcome": "pass",
                        "consumer_cleanup": "verified",
                        "candidate": sealed,
                    }
                ),
            ),
            (
                "results/baseline/inventory-before.json",
                json.dumps({"synthetic": "inventory-before"}),
            ),
        ]
        files = []
        result_artifacts = []
        for relative, content in entries:
            (destination / "artifacts" / relative).write_text(content)
            digest = hashlib.sha256(content.encode()).hexdigest()
            size_bytes = len(content.encode())
            files.append(
                {
                    "path": f"artifacts/{relative}",
                    "sha256": digest,
                    "size_bytes": size_bytes,
                }
            )
            result_artifacts.append(
                {"path": relative, "sha256": digest, "size_bytes": size_bytes}
            )
        log = "synthetic workload log\n"
        log_digest = hashlib.sha256(log.encode()).hexdigest()
        log_size = len(log.encode())
        (destination / "output.log").write_text(log)
        files.append(
            {"path": "output.log", "sha256": log_digest, "size_bytes": log_size}
        )
        result = {
            "schema": "haepari.result/v2",
            "job_id": "job-fixture-synthetic",
            "job_state": "finished",
            "final_verdict": "pass",
            "workload_outcome": "pass",
            "cleanup_outcome": "verified",
            "evidence_completeness": "complete",
            "resource_availability": "available",
            "resource_id": "synthetic-resource",
            "lease_generation": 1,
            "native_exit_code": 0,
            "resource_revision": 1,
            "artifacts": result_artifacts,
            "logs": [
                {"path": "output.log", "sha256": log_digest, "size_bytes": log_size}
            ],
            "timings": {
                "admitted_at": "2026-10-24T00:00:00Z",
                "reserved_at": "2026-10-24T00:00:00Z",
                "adapter_steps": [{"step": "ssh-ready", "duration_millis": 1}],
                "phases": [
                    {
                        "phase": "run",
                        "started_at": "2026-10-24T00:00:00Z",
                        "ended_at": "2026-10-24T00:00:01Z",
                    }
                ],
            },
        }
        (destination / "result.json").write_text(json.dumps(result))
        (destination / "manifest.json").write_text(
            json.dumps(
                {
                    "schema": "haepari.artifact-manifest/v1",
                    "job_id": "job-fixture-synthetic",
                    "result": result,
                    "files": files,
                    "supplementary": [],
                }
            )
        )
        entry = {"job_id": "job-fixture-synthetic", "suite": "baseline"}
        return destination, entry, [relative for relative, _ in entries], sealed

    def test_c21_real_layout_export_fixture_accepted(self):
        module = self._load_host_wrapper_module("hw_export_verify")
        destination, entry, required, sealed = self._real_layout_export("accept")
        self.assertTrue(module._verify_export(destination, entry, required, sealed))

    def test_c22_export_manifests_match_haepari_skeleton(self):
        # The committed skeleton is the real v0.1.0 manifest's key shape;
        # both the static fixture and the fake CLI's export must match it
        # exactly, so the offline tests stay bound to the real layout.
        skeleton = json.loads(EXPORT_SKELETON_PATH.read_text())
        destination, _entry, _required, _sealed = self._real_layout_export("skeleton")
        fixture_manifest = json.loads((destination / "manifest.json").read_text())
        self.assertEqual(export_manifest_skeleton(fixture_manifest), skeleton)
        run_dir = self.work / "skeleton-fake-run"
        run_dir.mkdir()
        run_dir.joinpath("run.json").write_text(
            json.dumps(
                {
                    "jobs": [{"suite": "baseline", "job_id": "job-skeleton"}],
                    "installation_binding": {},
                }
            )
        )
        run_dir.joinpath("spec-0.json").write_text(
            json.dumps(
                {"workload": {"required_outputs": ["results/baseline/result.json"]}}
            )
        )
        state = self.work / "skeleton-fake-state"
        state.mkdir(exist_ok=True)
        export_dir = self.work / "skeleton-fake-export"
        environment = dict(
            os.environ,
            HAEPARI=str(self.fake),
            FAKE_HAEPARI_STATE=str(state),
            AQUARIUM_VM_RUN_DIR=str(run_dir),
        )
        result = subprocess.run(
            [
                sys.executable,
                str(self.fake),
                "export",
                "job-skeleton",
                "--to",
                str(export_dir),
                "--json",
            ],
            env=environment,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        fake_manifest = json.loads((export_dir / "manifest.json").read_text())
        self.assertEqual(export_manifest_skeleton(fake_manifest), skeleton)

    def _rewrite_manifest(self, destination: Path, mutate) -> None:
        path = destination / "manifest.json"
        manifest = json.loads(path.read_text())
        mutate(manifest)
        path.write_text(json.dumps(manifest))

    def _verify_fixture(self, name: str, plant=None) -> bool:
        module = self._load_host_wrapper_module(f"hw_reject_{name}")
        destination, entry, required, sealed = self._real_layout_export(name)
        if plant is not None:
            plant(destination)
        return module._verify_export(destination, entry, required, sealed)

    def _append_file_entry(self, destination: Path, entry: dict) -> None:
        self._rewrite_manifest(
            destination, lambda manifest: manifest["files"].append(entry)
        )

    def test_c23_traversal_path_rejected(self):
        def plant(destination):
            outside = destination.parent / "outside.json"
            outside.write_text("outside\n")
            self.addCleanup(outside.unlink)
            self._append_file_entry(
                destination,
                {
                    "path": "artifacts/../../outside.json",
                    "sha256": hashlib.sha256(b"outside\n").hexdigest(),
                    "size_bytes": len(b"outside\n"),
                },
            )

        self.assertFalse(self._verify_fixture("c23-traversal", plant))

    def test_c23_artifacts_directory_symlink_rejected(self):
        def plant(destination):
            tree = destination / "artifacts"
            moved = destination.parent / f"{destination.name}-moved-artifacts"
            tree.rename(moved)
            (destination / "artifacts").symlink_to(moved)

        self.assertFalse(self._verify_fixture("c23-dirsymlink", plant))

    def test_c23_symlinked_leaf_rejected(self):
        def plant(destination):
            leaf = destination / "artifacts/results/baseline/inventory-before.json"
            leaf.unlink()
            leaf.symlink_to("../../../../output.log")

        self.assertFalse(self._verify_fixture("c23-leafsym", plant))

    def test_c23_absolute_path_rejected(self):
        self.assertFalse(
            self._verify_fixture(
                "c23-absolute",
                lambda destination: self._append_file_entry(
                    destination,
                    {"path": "/outside.json", "sha256": "0" * 64, "size_bytes": 1},
                ),
            )
        )

    def test_c23_backslash_path_rejected(self):
        self.assertFalse(
            self._verify_fixture(
                "c23-backslash",
                lambda destination: self._append_file_entry(
                    destination,
                    {
                        "path": "artifacts/Results\\Baseline\\result.json",
                        "sha256": "0" * 64,
                        "size_bytes": 1,
                    },
                ),
            )
        )

    def test_c23_nul_path_rejected(self):
        self.assertFalse(
            self._verify_fixture(
                "c23-nul",
                lambda destination: self._append_file_entry(
                    destination,
                    {
                        "path": "artifacts/Results\x00Baseline/result.json",
                        "sha256": "0" * 64,
                        "size_bytes": 1,
                    },
                ),
            )
        )

    def test_c23_dot_slash_path_rejected(self):
        self.assertFalse(
            self._verify_fixture(
                "c23-dotslash",
                lambda destination: self._append_file_entry(
                    destination,
                    {
                        "path": "artifacts/./baseline/result.json",
                        "sha256": "0" * 64,
                        "size_bytes": 1,
                    },
                ),
            )
        )

    def test_c23_trailing_slash_path_rejected(self):
        self.assertFalse(
            self._verify_fixture(
                "c23-trailing",
                lambda destination: self._append_file_entry(
                    destination,
                    {
                        "path": "artifacts/results/baseline/result.json/",
                        "sha256": "0" * 64,
                        "size_bytes": 1,
                    },
                ),
            )
        )

    def test_c23_case_folded_duplicate_paths_rejected(self):
        self.assertFalse(
            self._verify_fixture(
                "c23-casedup",
                lambda destination: self._append_file_entry(
                    destination,
                    {
                        "path": "artifacts/Results/baseline/result.json",
                        "sha256": "0" * 64,
                        "size_bytes": 1,
                    },
                ),
            )
        )

    def test_c23_list_manifest_rejected(self):
        def plant(destination):
            (destination / "manifest.json").write_text("[]")

        self.assertFalse(self._verify_fixture("c23-listmanifest", plant))

    def test_c23_null_file_entry_rejected(self):
        self.assertFalse(
            self._verify_fixture(
                "c23-nullentry",
                lambda destination: self._rewrite_manifest(
                    destination, lambda manifest: manifest.__setitem__("files", [None])
                ),
            )
        )

    def test_c23_non_dict_result_rejected(self):
        self.assertFalse(
            self._verify_fixture(
                "c23-badresult",
                lambda destination: self._rewrite_manifest(
                    destination,
                    lambda manifest: manifest.__setitem__("result", "not-a-dict"),
                ),
            )
        )

    def test_c23_string_size_bytes_rejected(self):
        def plant(destination):
            self._rewrite_manifest(
                destination,
                lambda manifest: manifest["files"][1].__setitem__("size_bytes", "12"),
            )

        self.assertFalse(self._verify_fixture("c23-strsize", plant))

    def test_c23_bool_size_bytes_rejected(self):
        def plant(destination):
            self._rewrite_manifest(
                destination,
                lambda manifest: manifest["result"]["artifacts"][1].__setitem__(
                    "size_bytes", True
                ),
            )
            # Keep the exported result equal so the rejection comes from
            # the entry's type check, not from result equality.
            manifest = json.loads((destination / "manifest.json").read_text())
            (destination / "result.json").write_text(json.dumps(manifest["result"]))

        self.assertFalse(self._verify_fixture("c23-boolsize", plant))

    def test_c25_invalid_artifact_path_rejected(self):
        # An invalid result.artifacts[] path is rejected even when no
        # required output uses it.
        def plant(destination):
            def mutate(manifest):
                manifest["result"]["artifacts"].append(
                    {"path": "../outside.json", "sha256": "0" * 64, "size_bytes": 1}
                )

            self._rewrite_manifest(destination, mutate)
            manifest = json.loads((destination / "manifest.json").read_text())
            (destination / "result.json").write_text(json.dumps(manifest["result"]))

        self.assertFalse(self._verify_fixture("c25-badartpath", plant))

    def test_c25_case_folded_duplicate_artifact_paths_rejected(self):
        def plant(destination):
            def mutate(manifest):
                manifest["result"]["artifacts"].append(
                    {
                        "path": "Results/baseline/inventory-before.json",
                        "sha256": "0" * 64,
                        "size_bytes": 1,
                    }
                )

            self._rewrite_manifest(destination, mutate)
            manifest = json.loads((destination / "manifest.json").read_text())
            (destination / "result.json").write_text(json.dumps(manifest["result"]))

        self.assertFalse(self._verify_fixture("c25-artcasedup", plant))

    def test_c26_non_required_file_size_mismatch_rejected(self):
        # output.log carries a correct digest but a wrong size_bytes: the
        # manifest is inconsistent evidence even for non-required files.
        def plant(destination):
            self._rewrite_manifest(
                destination,
                lambda manifest: next(
                    item for item in manifest["files"] if item["path"] == "output.log"
                ).__setitem__("size_bytes", 999999),
            )

        self.assertFalse(self._verify_fixture("c26-logsiz", plant))

    def test_c26_undeclared_delivery_missing_from_files_rejected(self):
        # A declared non-required artifact that files[] does not deliver is
        # inconsistent evidence.
        def plant(destination):
            def mutate(manifest):
                manifest["result"]["artifacts"].append(
                    {
                        "path": "results/baseline/extra.json",
                        "sha256": "0" * 64,
                        "size_bytes": 1,
                    }
                )

            self._rewrite_manifest(destination, mutate)
            manifest = json.loads((destination / "manifest.json").read_text())
            (destination / "result.json").write_text(json.dumps(manifest["result"]))

        self.assertFalse(self._verify_fixture("c26-undelivered", plant))

    def test_c26_artifact_digest_disagreement_rejected(self):
        # A declared non-required artifact is delivered by files[] with the
        # matching on-disk digest, but result.artifacts[] disagrees with it.
        def plant(destination):
            content = "extra output\n"
            leaf = destination / "artifacts/results/baseline/extra.json"
            leaf.write_text(content)
            digest = hashlib.sha256(content.encode()).hexdigest()
            size = len(content.encode())

            def mutate(manifest):
                manifest["files"].append(
                    {
                        "path": "artifacts/results/baseline/extra.json",
                        "sha256": digest,
                        "size_bytes": size,
                    }
                )
                manifest["result"]["artifacts"].append(
                    {
                        "path": "results/baseline/extra.json",
                        "sha256": "0" * 64,
                        "size_bytes": size,
                    }
                )

            self._rewrite_manifest(destination, mutate)
            manifest = json.loads((destination / "manifest.json").read_text())
            (destination / "result.json").write_text(json.dumps(manifest["result"]))

        self.assertFalse(self._verify_fixture("c26-artdisagree", plant))

    def test_c27_undeclared_artifact_delivery_rejected(self):
        # files[] delivers an artifact with a correct digest and size that
        # result.artifacts[] never declared: not a closed mapping.
        def plant(destination):
            content = "undeclared output\n"
            leaf = destination / "artifacts/results/baseline/extra.json"
            leaf.write_text(content)

            self._append_file_entry(
                destination,
                {
                    "path": "artifacts/results/baseline/extra.json",
                    "sha256": hashlib.sha256(content.encode()).hexdigest(),
                    "size_bytes": len(content.encode()),
                },
            )

        self.assertFalse(self._verify_fixture("c27-undeclared-art", plant))

    def test_c27_undeclared_log_delivery_rejected(self):
        # files[] carries output.log while result.logs declares nothing:
        # an undeclared delivery.
        def plant(destination):
            self._rewrite_manifest(
                destination,
                lambda manifest: manifest["result"].__setitem__("logs", []),
            )
            manifest = json.loads((destination / "manifest.json").read_text())
            (destination / "result.json").write_text(json.dumps(manifest["result"]))

        self.assertFalse(self._verify_fixture("c27-undeclared-log", plant))

    def test_c27_declared_log_missing_from_files_rejected(self):
        # A declared log that files[] does not deliver.
        def plant(destination):
            def mutate(manifest):
                manifest["result"]["logs"].append(
                    {
                        "path": "recovery-scratch.log",
                        "sha256": "0" * 64,
                        "size_bytes": 1,
                    }
                )

            self._rewrite_manifest(destination, mutate)
            manifest = json.loads((destination / "manifest.json").read_text())
            (destination / "result.json").write_text(json.dumps(manifest["result"]))

        self.assertFalse(self._verify_fixture("c27-missing-log", plant))

    def test_c27_declared_log_digest_disagreement_rejected(self):
        # A declared log is delivered by files[] with the matching on-disk
        # digest and size, but result.logs[] disagrees with the digest.
        def plant(destination):
            content = "scratch log\n"
            (destination / "recovery-scratch.log").write_text(content)
            digest = hashlib.sha256(content.encode()).hexdigest()
            size = len(content.encode())

            def mutate(manifest):
                manifest["files"].append(
                    {
                        "path": "recovery-scratch.log",
                        "sha256": digest,
                        "size_bytes": size,
                    }
                )
                manifest["result"]["logs"].append(
                    {
                        "path": "recovery-scratch.log",
                        "sha256": "0" * 64,
                        "size_bytes": size,
                    }
                )

            self._rewrite_manifest(destination, mutate)
            manifest = json.loads((destination / "manifest.json").read_text())
            (destination / "result.json").write_text(json.dumps(manifest["result"]))

        self.assertFalse(self._verify_fixture("c27-logdisagree", plant))

    def test_c27_non_list_logs_rejected(self):
        def plant(destination):
            self._rewrite_manifest(
                destination,
                lambda manifest: manifest["result"].__setitem__("logs", "none"),
            )
            manifest = json.loads((destination / "manifest.json").read_text())
            (destination / "result.json").write_text(json.dumps(manifest["result"]))

        self.assertFalse(self._verify_fixture("c27-badlogs", plant))

    def test_c28_declared_log_under_artifacts_accepted(self):
        # A log declared at artifacts/extra.log and delivered with matching
        # size and digest is a permitted membership: accepted.
        def plant(destination):
            content = "extra log\n"
            (destination / "artifacts/extra.log").write_text(content)
            digest = hashlib.sha256(content.encode()).hexdigest()
            size = len(content.encode())

            def mutate(manifest):
                manifest["files"].append(
                    {
                        "path": "artifacts/extra.log",
                        "sha256": digest,
                        "size_bytes": size,
                    }
                )
                manifest["result"]["logs"].append(
                    {
                        "path": "artifacts/extra.log",
                        "sha256": digest,
                        "size_bytes": size,
                    }
                )

            self._rewrite_manifest(destination, mutate)
            manifest = json.loads((destination / "manifest.json").read_text())
            (destination / "result.json").write_text(json.dumps(manifest["result"]))

        self.assertTrue(self._verify_fixture("c28-logunderart", plant))

    def test_c28_malformed_consumer_claim_records_unverified(self):
        # A bound, checksummed suite result with a non-string
        # consumer_cleanup claim records unverified and blocks acceptance
        # through the normal result path (exit 3), never exit 2.
        for index, knob in enumerate(
            ("FAKE_EXPORT_CONSUMER_LIST", "FAKE_EXPORT_CONSUMER_DICT")
        ):
            with self.subTest(knob=knob):
                run_dir, state = self.scenario(f"c28-claim{index}")
                self.doctor_ok(state)
                self.submit_ok(state)
                self.respond(
                    state,
                    0,
                    envelope("wait", {"final_verdict": "PASS"}),
                    match="wait",
                )
                result = self.invoke_wrapper(run_dir, state, **{knob: "1"})
                self.assertEqual(result.returncode, 3, result.stdout)
                self.assertIn('"consumer_cleanup": "unverified"', result.stdout)
                self.assertIn('"final_verdict": "PASS"', result.stdout)
                self.assertIn('"acceptance": "blocked"', result.stdout)

    def test_c25_surrogate_path_rejected(self):
        # A lone surrogate passes lexical checks but cannot be encoded for
        # the filesystem; verification must reject it without raising.
        self.assertFalse(
            self._verify_fixture(
                "c25-surrogate",
                lambda destination: self._append_file_entry(
                    destination,
                    {
                        "path": "artifacts/\ud800",
                        "sha256": "0" * 64,
                        "size_bytes": 1,
                    },
                ),
            )
        )

    def test_c25_surrogate_manifest_reconnect_falls_back_to_fresh(self):
        run_dir, state = self.scenario("c25-fallback")
        self.doctor_ok(state)
        self.submit_ok(state)
        self.respond(
            state, 0, envelope("wait", {"final_verdict": "PASS"}), match="wait"
        )
        first = self.invoke_wrapper(run_dir, state)
        self.assertEqual(first.returncode, 0, first.stdout)
        # Plant a lone-surrogate path in the verified export's manifest,
        # then reconnect: the wrapper must preserve it untouched and export
        # fresh to -r2 instead of crashing.
        rejected = run_dir / "export-install"
        self._append_file_entry(
            rejected,
            {"path": "artifacts/\ud800", "sha256": "0" * 64, "size_bytes": 1},
        )
        before = sorted(
            path.read_bytes() for path in rejected.rglob("*") if path.is_file()
        )
        self.doctor_ok(state)
        self.respond(
            state, 0, envelope("wait", {"final_verdict": "PASS"}), match="wait"
        )
        result = self.invoke_wrapper(run_dir, state)
        self.assertEqual(result.returncode, 0, result.stdout)
        after = sorted(
            path.read_bytes() for path in rejected.rglob("*") if path.is_file()
        )
        self.assertEqual(after, before)
        fresh = run_dir / "export-install-r2"
        self.assertTrue((fresh / "manifest.json").is_file())
        self.assertIn("export-install-r2", result.stdout)
        self.assertIn('"final_verdict": "PASS"', result.stdout)

    def test_c35_changed_spec_on_reconnect_refused(self):
        run_dir, state = self.scenario("c35-spec-drift")
        self.doctor_ok(state)
        self.submit_ok(state)
        self.respond(
            state, 0, envelope("wait", {"final_verdict": "PASS"}), match="wait"
        )
        result = self.invoke_wrapper(run_dir, state)
        self.assertEqual(result.returncode, 0, result.stdout)
        entry = json.loads((run_dir / "run.json").read_text())["jobs"][0]
        spec_path = run_dir / entry["spec"]
        spec_path.write_text(spec_path.read_text() + "\n")
        module = self._load_host_wrapper_module("hw_refusal_spec")
        with self.assertRaises(module.Refusal) as raised:
            module.read_spec(run_dir, entry)
        self.assertIn("the saved spec changed", str(raised.exception))

    def test_c35_resume_and_record_mismatches_refused(self):
        module = self._load_host_wrapper_module("hw_refusal_record")
        args = types.SimpleNamespace(
            resource="synthetic-resource", suite="install", mode="auto"
        )
        record = {
            "resource": "synthetic-resource",
            "suite": "install",
            "mode": "auto",
            "declared_suites": ["install"],
            "jobs": [
                {
                    "suite": "install",
                    "spec": "spec-0.json",
                    "request_key": "key-0",
                    "submission_started": True,
                    "spec_sha256": "a" * 64,
                }
            ],
        }
        module.validate_record(record, args)
        mismatched = dict(record, resource="another-resource")
        with self.assertRaises(module.Refusal) as raised:
            module.validate_record(mismatched, args)
        self.assertIn("resume requires the original resource", str(raised.exception))
        incomplete = dict(record, declared_suites=["install", "baseline"])
        with self.assertRaises(module.Refusal) as raised:
            module.validate_record(incomplete, args)
        self.assertIn("membership is incomplete", str(raised.exception))
        broken_binding = json.loads(json.dumps(record))
        broken_binding["jobs"][0]["request_key"] = "not a key!"
        with self.assertRaises(module.Refusal) as raised:
            module.validate_record(broken_binding, args)
        self.assertIn("saved Job binding is invalid", str(raised.exception))

    def test_optional_baseline_profile_keeps_exact_sealed_bytes_on_resume(self):
        module = self._load_host_wrapper_module("hw_baseline_profile")
        root = Path(tempfile.mkdtemp(dir=self.work)).resolve()
        source = root / "baseline.json"
        source.write_bytes(b'{"explicitly":"synthetic profile"}\n')
        sealed = root / "bundle/profile/stable.json"
        sealed.parent.mkdir(parents=True)
        sealed.write_bytes(source.read_bytes())
        args = types.SimpleNamespace(
            resource="r",
            suite="manual-hold",
            mode="manual",
            run_dir=str(root),
            baseline_profile=str(source),
        )
        record = {
            "resource": "r",
            "suite": "manual-hold",
            "mode": "manual",
            "declared_suites": ["manual-hold"],
            "jobs": [
                {
                    "suite": "manual-hold",
                    "spec": "spec-0.json",
                    "request_key": "saved-key",
                    "submission_started": True,
                    "spec_sha256": "a" * 64,
                }
            ],
        }
        module.validate_record(record, args)
        source.write_bytes(source.read_bytes() + b" ")
        with self.assertRaises(module.Refusal):
            module.validate_record(record, args)
        with mock.patch.dict(
            os.environ,
            {
                "AQUARIUM_VM_BASELINE_PROFILE": str(source),
                "AQUARIUM_VM_MODE": "manual",
                "AQUARIUM_VM_SUITE": "manual-hold",
            },
        ):
            self.assertEqual(module.parse_arguments().baseline_profile, str(source))

    def test_c35_run_dir_symlink_and_wrong_mode_refused(self):
        module = self._load_host_wrapper_module("hw_refusal_rundir")
        real = tempfile.mkdtemp(prefix="vm-real-", dir=str(self.work))
        linked = self.work / "c35-run-link"
        linked.symlink_to(real)
        self.addCleanup(linked.unlink)
        try:
            module.require_run_dir(str(linked))
        except module.Refusal as error:
            self.assertIn("absolute physical directory", str(error))
        else:
            self.fail("a symlinked RUN_DIR was accepted")
        wrong_mode = self.work / "c35-run-mode"
        wrong_mode.mkdir(mode=0o755)
        try:
            module.require_run_dir(str(wrong_mode))
        except module.Refusal as error:
            self.assertIn("mode 0700", str(error))
        else:
            self.fail("a wrong-mode RUN_DIR was accepted")
        physical = self.work / "c35-run-ok"
        physical.mkdir(mode=0o700)
        self.assertEqual(module.require_run_dir(str(physical)), physical)

    def test_c35_caller_lock_contention_refused(self):
        import fcntl

        run_dir = Path(tempfile.mkdtemp(prefix="vm-lock-", dir=str(self.work)))
        run_dir.chmod(0o700)
        state = self.work / "state-c35-lock"
        state.mkdir()
        lock_path = run_dir / "caller.lock"
        with open(lock_path, "a+") as holder:
            fcntl.flock(holder, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = self.invoke_wrapper(run_dir, state)
            fcntl.flock(holder, fcntl.LOCK_UN)
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("another caller owns this run", result.stdout)

    def test_c35_queue_ceiling_and_minimum_refused(self):
        module = self._load_host_wrapper_module("hw_refusal_queue")
        with self.assertRaises(module.Refusal) as raised:
            module.require_queue_budget(78300, 3)
        self.assertIn("queue ceiling never admits a third", str(raised.exception))
        with self.assertRaises(module.Refusal) as raised:
            module.require_queue_budget(52200, 2)
        self.assertIn("below the tagged minimum", str(raised.exception))
        with self.assertRaises(module.Refusal) as raised:
            module.require_queue_budget(86401, 0)
        self.assertIn("exceeds the 86400 ceiling", str(raised.exception))
        module.require_queue_budget(78300, 2)

    def test_c35_invoke_malformed_envelopes_refused(self):
        cases = {
            "multi-line stdout": [
                {"schema": "haepari.envelope/v1"},
                {"schema": "haepari.envelope/v1"},
            ],
            "wrong schema": {"schema": "wrong/v1", "operation": "doctor"},
            "payload not a dict": {
                "schema": "haepari.envelope/v1",
                "operation": "doctor",
                "ok": True,
                "data": "not-a-dict",
            },
        }
        needles = {
            "multi-line stdout": "response unavailable",
            "wrong schema": "unsupported Haepari response",
            "payload not a dict": "malformed Haepari payload",
        }
        for label, payload in cases.items():
            with self.subTest(case=label):
                run_dir, state = self.scenario(f"c35-envelope-{abs(hash(label))}")
                index = len(list(state.glob("response-*")))
                (state / f"response-{index:03d}.json").write_text(
                    json.dumps({"exit": 0, "stdout": payload, "match": "doctor"})
                )
                result = self.invoke_wrapper(run_dir, state)
                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertIn(needles[label], result.stdout)

    def test_c24_non_dict_consumed_result_rejected(self):
        # The consumed suite result is listed with correct sizes and
        # digests but its content is a JSON list: verification must return
        # False without raising.
        def plant(destination):
            leaf = destination / "artifacts/results/baseline/result.json"
            content = "[]"
            leaf.write_text(content)
            digest = hashlib.sha256(content.encode()).hexdigest()
            size = len(content.encode())

            def update(item):
                if item["path"].endswith("results/baseline/result.json"):
                    item["sha256"] = digest
                    item["size_bytes"] = size

            def mutate(manifest):
                for item in manifest["files"]:
                    update(item)
                for item in manifest["result"]["artifacts"]:
                    update(item)

            self._rewrite_manifest(destination, mutate)
            # Keep the exported result equal to the mutated manifest result
            # so the rejection comes from the consumed document's shape.
            manifest = json.loads((destination / "manifest.json").read_text())
            (destination / "result.json").write_text(json.dumps(manifest["result"]))

        self.assertFalse(self._verify_fixture("c24-listresult", plant))

    def test_c23_malformed_existing_export_falls_back_to_fresh(self):
        run_dir, state = self.scenario("c23-fallback")
        self.doctor_ok(state)
        self.submit_ok(state)
        self.respond(
            state, 0, envelope("wait", {"final_verdict": "PASS"}), match="wait"
        )
        first = self.invoke_wrapper(run_dir, state)
        self.assertEqual(first.returncode, 0, first.stdout)
        # Corrupt the verified export, then reconnect: the wrapper must
        # preserve it untouched and export fresh to -r2.
        rejected = run_dir / "export-install"
        (rejected / "manifest.json").write_text("[]")
        before = sorted(
            path.read_bytes() for path in rejected.rglob("*") if path.is_file()
        )
        self.doctor_ok(state)
        self.respond(
            state, 0, envelope("wait", {"final_verdict": "PASS"}), match="wait"
        )
        result = self.invoke_wrapper(run_dir, state)
        self.assertEqual(result.returncode, 0, result.stdout)
        after = sorted(
            path.read_bytes() for path in rejected.rglob("*") if path.is_file()
        )
        # The rejected directory is preserved untouched.
        self.assertEqual(after, before)
        fresh = run_dir / "export-install-r2"
        self.assertTrue((fresh / "manifest.json").is_file())
        self.assertIn("export-install-r2", result.stdout)
        self.assertIn('"final_verdict": "PASS"', result.stdout)

    def _export_probe(self, name: str, knob: str):
        run_dir, state = self.scenario(name)
        self.doctor_ok(state)
        self.submit_ok(state)
        self.respond(
            state, 0, envelope("wait", {"final_verdict": "PASS"}), match="wait"
        )
        return self.invoke_wrapper(run_dir, state, **{knob: "1"})

    def _assert_export_rejected(self, result):
        self.assertEqual(result.returncode, 3, result.stdout)
        self.assertIn("export-unverified", result.stdout)
        self.assertIn('"final_verdict": "PASS"', result.stdout)
        self.assertIn('"acceptance": "blocked"', result.stdout)

    def test_c21_export_missing_result_artifact_rejected(self):
        self._assert_export_rejected(
            self._export_probe("c21-missing", "FAKE_EXPORT_MISSING_ARTIFACT")
        )

    def test_c21_export_digest_drift_rejected(self):
        self._assert_export_rejected(
            self._export_probe("c21-drift", "FAKE_EXPORT_DIGEST_DRIFT")
        )

    def test_c21_export_list_disagreement_rejected(self):
        self._assert_export_rejected(
            self._export_probe("c21-disagree", "FAKE_EXPORT_DISAGREE")
        )

    def test_c21_export_path_outside_prefixes_rejected(self):
        self._assert_export_rejected(
            self._export_probe("c21-prefix", "FAKE_EXPORT_BAD_PREFIX")
        )

    def test_c21_export_symlinked_file_rejected(self):
        self._assert_export_rejected(
            self._export_probe("c21-symlink", "FAKE_EXPORT_SYMLINK")
        )

    def test_c21_export_result_job_mismatch_rejected(self):
        self._assert_export_rejected(
            self._export_probe("c21-jobmismatch", "FAKE_EXPORT_RESULT_JOB_MISMATCH")
        )

    def test_nested_guest_context_refuses(self):
        run_dir, state = self.scenario("nested")
        result = self.invoke_wrapper(
            run_dir, state, HAEPARI_PARENT_CONTEXT='[{"job_id": "x"}]'
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("managed guest context", result.stdout)


if __name__ == "__main__":
    unittest.main()
