#!/usr/bin/env python3
"""Facts-shaped fake Podway v0.2.14 for the offline guest simulation.

Shapes follow the guest facts: `--version` is invalid syntax (the version
route is `podway version [--json] [--identity]`), observe returns
`podway.observation-result/v5` only for a worktree with an admitted session,
and a missing session fails with a top-level error code and a failure exit —
native Error v2, never a nested code inside an exit-0 envelope.
"""

from __future__ import annotations

import json
import os
import sys
import uuid

arguments = sys.argv[1:]
GENERATION = 2 if "--contract-generation" in arguments else 1
VERSION = "v0.2.17" if GENERATION == 2 else "v0.2.14"


def state_path() -> str:
    value = os.environ.get("FAKE_PODWAY_STATE", "")
    if not value or not os.path.isabs(value):
        raise SystemExit("FAKE_PODWAY_STATE must be a non-empty absolute path")
    return value


def load_sessions() -> dict:
    if os.path.isfile(state_path()):
        with open(state_path()) as stream:
            return json.load(stream)
    return {}


def save_sessions(sessions: dict) -> None:
    with open(state_path(), "w") as stream:
        json.dump(sessions, stream)


def envelope(result):
    return {"schema": "podway.output/v4", "result": result}


def fail(code: str, message: str) -> int:
    # Native Error v2: top-level code with a failure exit.
    print(json.dumps({"code": code, "message": message}))
    return 2


def worktree_argument() -> str | None:
    for index, value in enumerate(arguments):
        if value == "--worktree" and index + 1 < len(arguments):
            return arguments[index + 1]
    return None


def json_flag() -> bool:
    return "--json" in arguments


def main() -> int:
    if arguments[:1] == ["--version"] or arguments[:2] == ["version", "--help"]:
        print("invalid command syntax", file=sys.stderr)
        return 2
    if arguments[:1] == ["help"]:
        print("podway help [<route>]")
        print("podway version [--json] [--identity]")
        print("podway start --preset sw-dev-v2 --task '<task>' --idempotency-key <key>")
        return 0
    if "version" in arguments:
        # The global `--json` flag before the route yields the envelope the
        # driver's versions() reads; `podway version --json` prints the bare
        # reported shape.
        if arguments[0] == "--json" or (GENERATION == 2 and "--json" in arguments):
            identity = {
                "schema": "podway.version-identity/v1",
                "version": VERSION,
                "commit": "fa29dba929777b020377bc9803cb0a3954d219b1",
            }
            result = {
                "schema": "podway.version-result/v2",
                "version": VERSION,
                "source_commit": "sim-podway-16",
                "contract_manifest_digest": "sim-manifest-16",
            }
            if "--identity" in arguments:
                result["identity"] = identity
            print(json.dumps(envelope(result)))
        else:
            print(json.dumps({"name": "podway", "version": VERSION}))
        return 0
    if "procedure" in arguments and "check" in arguments:
        path = next(
            (value for value in arguments if value.endswith((".yaml", ".yml"))),
            None,
        )
        if path is None or not os.path.isfile(path):
            return fail("INVALID_REQUEST", "procedure file is unavailable")
        print(
            json.dumps(
                envelope(
                    {
                        "schema": "podway.procedure-check-result/v1",
                        "ok": True,
                        "warnings": [],
                    }
                )
            )
        )
        return 0
    if "start" in arguments:
        worktree = worktree_argument()
        if worktree is None:
            return fail("INVALID_REQUEST", "start needs --worktree")
        preset = (
            arguments[arguments.index("--preset") + 1]
            if "--preset" in arguments
            else None
        )
        task = (
            arguments[arguments.index("--task") + 1] if "--task" in arguments else None
        )
        key = (
            arguments[arguments.index("--idempotency-key") + 1]
            if "--idempotency-key" in arguments
            else None
        )
        if preset != "sw-dev-v2" or not task or not key:
            return fail("INVALID_REQUEST", "start needs preset, task and key")
        sessions = load_sessions()
        existing = sessions.get(worktree)
        if existing is not None:
            print(
                json.dumps(
                    {
                        "schema": "podway.session-start-result/v4",
                        "session_id": existing["session_id"],
                        "idempotent_reuse": True,
                    }
                )
            )
            return 0
        session = {
            "session_id": "session-" + uuid.uuid4().hex[:12],
            "procedure": "aquarium-task-v2",
            "node": "intake",
            "revision": 1,
            "lifecycle": "admitted",
        }
        sessions[worktree] = session
        save_sessions(sessions)
        print(
            json.dumps(
                {
                    "schema": "podway.session-start-result/v4",
                    "session_id": session["session_id"],
                    "idempotent_reuse": False,
                }
            )
        )
        return 0
    if "observe" in arguments:
        worktree = worktree_argument()
        if worktree is None:
            return fail("INVALID_REQUEST", "observe needs --worktree")
        session = load_sessions().get(worktree)
        if session is None:
            return fail("SESSION_NOT_FOUND", f"no admitted session for {worktree}")
        print(
            json.dumps(
                envelope(
                    {
                        "schema": "podway.observation-result/v6"
                        if GENERATION == 2
                        else "podway.observation-result/v5",
                        "status": {
                            "session": {
                                "id": session["session_id"],
                                "revision": session.get("revision", 1),
                                "lifecycle": session.get("lifecycle", "admitted"),
                            },
                            "procedure": {
                                "id": session.get("procedure", "aquarium-task-v2"),
                                "digest": "0" * 64,
                            },
                        },
                        "guidance": {
                            "node": {"graph_node_id": session.get("node", "intake")}
                        },
                    }
                )
            )
        )
        return 0
    print(f"unsupported: {arguments}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
