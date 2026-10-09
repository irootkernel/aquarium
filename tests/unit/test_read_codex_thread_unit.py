from __future__ import annotations

import base64
import contextlib
import hashlib
import importlib.util
import json
import os
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).parents[2]
    / "plugins/aquarium/skills/goal-judge/scripts/read_codex_thread.py"
)
SPEC = importlib.util.spec_from_file_location("read_codex_thread", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
reader = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reader)


def frame(body: bytes, opcode=1, *, final=True) -> bytes:
    length = len(body)
    header = bytes(
        [
            (0x80 if final else 0) | opcode,
            length if length < 126 else 126 if length < 65536 else 127,
        ]
    )
    if length >= 126:
        header += struct.pack("!H" if length < 65536 else "!Q", length)
    return header + body


def wire(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()


def receive(connection, count):
    value = b""
    while len(value) < count:
        chunk = connection.recv(count - len(value))
        if not chunk:
            raise EOFError
        value += chunk
    return value


def client_frame(connection):
    first, second = receive(connection, 2)
    assert first & 128 and second & 128, "client frames must be final and masked"
    length = second & 127
    if length == 126:
        length = struct.unpack("!H", receive(connection, 2))[0]
    elif length == 127:
        length = struct.unpack("!Q", receive(connection, 8))[0]
    mask = receive(connection, 4)
    body = receive(connection, length)
    return first & 15, bytes(
        value ^ mask[index % 4] for index, value in enumerate(body)
    )


@contextlib.contextmanager
def server(mode="normal", *, response=None):
    volume = Path("/Volumes/RootKernel")
    base = (
        volume / "tmp"
        if os.path.ismount(volume) and os.access(volume, os.W_OK)
        else Path(tempfile.gettempdir())
    )
    with tempfile.TemporaryDirectory(prefix="aqws-", dir=base) as directory:
        path = Path(directory) / "s"
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        listener.bind(str(path))
        listener.listen(1)
        state = {"operations": [], "closed": False, "pong": None, "errors": []}

        def serve():
            try:
                with listener.accept()[0] as connection:
                    connection.settimeout(2)
                    header = b""
                    while not header.endswith(b"\r\n\r\n"):
                        header += receive(connection, 1)
                    key = next(
                        line.split(b":", 1)[1].strip()
                        for line in header.split(b"\r\n")
                        if line.lower().startswith(b"sec-websocket-key:")
                    )
                    accept = base64.b64encode(
                        hashlib.sha1(key + reader.GUID.encode()).digest()
                    )
                    upgrade = (
                        b"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: keep-alive, Upgrade\r\nSec-WebSocket-Accept: "
                        + accept
                        + b"\r\n\r\n"
                    )
                    if mode.startswith("upgrade_"):
                        kind = mode.removeprefix("upgrade_")
                        if kind == "status":
                            upgrade = upgrade.replace(b"101", b"200", 1)
                        elif kind == "accept":
                            upgrade = upgrade.replace(accept, b"invalid")
                        elif kind == "connection":
                            upgrade = upgrade.replace(
                                b"keep-alive, Upgrade", b"keep-alive"
                            )
                        elif kind == "upgrade":
                            upgrade = upgrade.replace(
                                b"Upgrade: websocket", b"Upgrade: h2c"
                            )
                        elif kind == "duplicate":
                            upgrade = upgrade[:-2] + b"Upgrade: websocket\r\n\r\n"
                    if mode == "split":
                        for byte in upgrade:
                            connection.sendall(bytes([byte]))
                    elif mode == "coalesced":
                        connection.sendall(
                            upgrade
                            + frame(
                                wire({"method": "early/notification", "params": {}})
                            )
                        )
                    else:
                        connection.sendall(upgrade)
                    while len(state["operations"]) < 3:
                        opcode, body = client_frame(connection)
                        if opcode == 8:
                            state["closed"] = True
                            return
                        if opcode == 10:
                            state["pong"] = body
                            continue
                        operation = json.loads(body)
                        state["operations"].append(operation)
                        if operation["method"] == "initialize":
                            if mode == "init_error":
                                connection.sendall(
                                    frame(
                                        wire(
                                            {
                                                "id": 1,
                                                "error": {
                                                    "code": -1,
                                                    "message": "secret native path",
                                                },
                                            }
                                        )
                                    )
                                )
                            else:
                                connection.sendall(
                                    frame(
                                        wire(
                                            {
                                                "id": 1,
                                                "result": {"userAgent": "fake-server"},
                                            }
                                        )
                                    )
                                )
                    value = (
                        response
                        if response is not None
                        else {
                            "id": 2,
                            "result": {
                                "thread": {
                                    "id": "thread-1",
                                    "historyMode": "paginated",
                                    "turns": [
                                        {
                                            "id": "turn-1",
                                            "status": "completed",
                                            "itemsView": "full",
                                            "items": [
                                                {
                                                    "id": "final-1",
                                                    "type": "agentMessage",
                                                    "text": "Original \u00e9\r\nresult",
                                                }
                                            ],
                                        }
                                    ],
                                }
                            },
                        }
                    )
                    body = wire(value)
                    if mode == "fragmented":
                        split = body.index("\u00e9".encode()) + 1
                        connection.sendall(
                            frame(body[:split], final=False)
                            + frame(b"ping", 9)
                            + frame(body[split:], 0)
                        )
                    elif mode == "split":
                        for byte in frame(body):
                            connection.sendall(bytes([byte]))
                    elif mode == "notifications":
                        connection.sendall(
                            frame(wire({"method": "thread/updated", "params": {}}))
                            + frame(body)
                        )
                    elif mode == "timeout":
                        pass
                    elif mode == "eof":
                        connection.shutdown(socket.SHUT_WR)
                    elif mode == "binary":
                        connection.sendall(frame(body, 2))
                    elif mode == "continuation":
                        connection.sendall(frame(body, 0))
                    elif mode == "nested_start":
                        connection.sendall(frame(b"{", final=False) + frame(body))
                    elif mode == "fragmented_ping":
                        connection.sendall(frame(b"ping", 9, final=False))
                    elif mode == "invalid_utf8":
                        connection.sendall(frame(b"\xff"))
                    elif mode == "invalid_json":
                        connection.sendall(frame(b"{broken"))
                    elif mode == "duplicate_json":
                        connection.sendall(frame(b'{"id":2,"id":2,"result":{}}'))
                    elif mode == "nan":
                        connection.sendall(frame(b'{"id":2,"result":{"value":NaN}}'))
                    elif mode == "masked_server":
                        connection.sendall(bytes([0x81, 0x80]))
                    elif mode == "reserved_bits":
                        connection.sendall(bytes([0xC1, 0]))
                    elif mode == "noncanonical_length":
                        connection.sendall(
                            bytes([0x81, 126]) + struct.pack("!H", 1) + b"x"
                        )
                    elif mode == "huge_length":
                        connection.sendall(
                            bytes([0x81, 127])
                            + struct.pack("!Q", reader.MAX_RECEIVED_BYTES + 1)
                        )
                    elif mode == "server_close":
                        connection.sendall(frame(struct.pack("!H", 1000), 8))
                    elif mode == "invalid_close":
                        connection.sendall(frame(b"x", 8))
                    else:
                        connection.sendall(frame(body))
                    while True:
                        opcode, body = client_frame(connection)
                        if opcode == 10:
                            state["pong"] = body
                        elif opcode == 8:
                            state["closed"] = True
                            return
            except EOFError:
                state["closed"] = True
            except (OSError, AssertionError) as error:
                state["errors"].append(error)

        worker = threading.Thread(target=serve, daemon=True)
        worker.start()
        try:
            yield path, state
        finally:
            listener.close()
            worker.join(timeout=3)
            assert not worker.is_alive(), "fake server did not terminate"


@pytest.mark.parametrize(
    "mode", ["normal", "split", "coalesced", "fragmented", "notifications"]
)
def test_captures_full_paginated_history_and_emits_only_fixed_read_operations(
    mode,
) -> None:
    with server(mode) as (path, state):
        result = reader.capture_thread(path, "thread-1")
    assert result["state"] == "captured"
    assert result["schema"] == reader.OUTPUT_SCHEMA
    assert [op["method"] for op in state["operations"]] == [
        "initialize",
        "initialized",
        "thread/read",
    ]
    assert state["operations"][0] == result["initialize"]["request"]
    assert state["operations"][1] == result["initialized"]
    assert state["operations"][2] == result["thread_read"]["request"]
    assert state["operations"][0]["params"] == {
        "clientInfo": {"name": "aquarium-read-codex-thread", "version": "1"},
        "capabilities": {"experimentalApi": True},
    }
    assert state["operations"][2]["params"] == {
        "threadId": "thread-1",
        "includeTurns": True,
    }
    thread = result["thread_read"]["response"]["result"]["thread"]
    assert thread["historyMode"] == "paginated"
    assert thread["turns"][0]["items"][0]["text"] == "Original \u00e9\r\nresult"
    assert state["closed"] is True
    assert state["errors"] == []
    if mode == "fragmented":
        assert state["pong"] == b"ping"


@pytest.mark.parametrize(
    "mode,code",
    [
        ("upgrade_status", "INVALID_UPGRADE"),
        ("upgrade_accept", "INVALID_UPGRADE"),
        ("upgrade_connection", "INVALID_UPGRADE"),
        ("upgrade_upgrade", "INVALID_UPGRADE"),
        ("upgrade_duplicate", "INVALID_UPGRADE"),
        ("binary", "INVALID_FRAME"),
        ("continuation", "INVALID_FRAME_SEQUENCE"),
        ("nested_start", "INVALID_FRAME_SEQUENCE"),
        ("fragmented_ping", "INVALID_FRAME"),
        ("invalid_utf8", "INVALID_UTF8"),
        ("invalid_json", "INVALID_JSON"),
        ("duplicate_json", "INVALID_JSON"),
        ("nan", "INVALID_JSON"),
        ("masked_server", "INVALID_FRAME"),
        ("reserved_bits", "INVALID_FRAME"),
        ("noncanonical_length", "INVALID_FRAME"),
        ("huge_length", "BYTE_LIMIT_EXCEEDED"),
        ("server_close", "SERVER_CLOSED"),
        ("invalid_close", "INVALID_FRAME"),
        ("eof", "UNEXPECTED_EOF"),
        ("init_error", "NATIVE_ERROR"),
    ],
)
def test_rejects_protocol_failures_without_native_secrets_and_closes(
    mode, code
) -> None:
    with server(mode) as (path, state):
        result = reader.capture_thread(path, "thread-1")
    assert result == {
        "schema": reader.OUTPUT_SCHEMA,
        "state": "rejected",
        "error": {"code": code},
    }
    assert "secret" not in json.dumps(result)
    assert state["closed"] is True


@pytest.mark.parametrize(
    "response,code",
    [
        ({"id": True, "result": {}}, "RESPONSE_ID_MISMATCH"),
        ({"id": "2", "result": {}}, "RESPONSE_ID_MISMATCH"),
        ({"id": 3, "result": {}}, "RESPONSE_ID_MISMATCH"),
        ({"id": 2, "result": {}, "error": None}, "INVALID_RPC"),
        ({"id": 2}, "INVALID_RPC"),
        ({"id": 2, "result": None}, "INVALID_RPC"),
        (
            {
                "id": 2,
                "error": {"code": -1, "message": "secret transcript /private/path"},
            },
            "NATIVE_ERROR",
        ),
        (
            {"id": 7, "method": "server/action", "params": {}},
            "UNEXPECTED_SERVER_REQUEST",
        ),
        (
            {"id": 2, "result": {"thread": {"id": "wrong", "turns": []}}},
            "THREAD_ID_MISMATCH",
        ),
        ({"id": 2, "result": {"thread": {"id": "thread-1"}}}, "INCOMPLETE_HISTORY"),
        (
            {
                "id": 2,
                "result": {
                    "thread": {
                        "id": "thread-1",
                        "turns": [{"itemsView": "summary", "items": []}],
                    }
                },
            },
            "INCOMPLETE_HISTORY",
        ),
        (
            {
                "id": 2,
                "result": {"thread": {"id": "thread-1", "turns": [{"items": []}]}},
            },
            "INCOMPLETE_HISTORY",
        ),
    ],
)
def test_rejects_ambiguous_rpc_native_errors_and_incomplete_projections(
    response, code
) -> None:
    with server(response=response) as (path, state):
        result = reader.capture_thread(path, "thread-1")
    assert result["state"] == "rejected"
    assert result["error"]["code"] == code
    assert state["closed"] is True
    assert "secret transcript" not in json.dumps(result)
    assert "thread_read" not in result


def test_overall_deadline_closes_even_when_close_frame_cannot_be_sent() -> None:
    with server("timeout") as (path, state):
        start = time.monotonic()
        result = reader.capture_thread(path, "thread-1", timeout_seconds=0.05)
        elapsed = time.monotonic() - start
    assert result["error"]["code"] == "TIMEOUT"
    assert elapsed < 0.5
    assert state["closed"] is True


def test_received_byte_limit_fails_without_truncation(monkeypatch) -> None:
    monkeypatch.setattr(reader, "MAX_RECEIVED_BYTES", 128)
    with server() as (path, state):
        result = reader.capture_thread(path, "thread-1")
    assert result["error"]["code"] == "BYTE_LIMIT_EXCEEDED"
    assert "thread_read" not in result
    assert state["closed"] is True


@pytest.mark.parametrize("timeout", [0, -1, True, float("nan"), float("inf")])
def test_invalid_timeout_rejected_without_connecting(timeout, tmp_path) -> None:
    result = reader.capture_thread(tmp_path.resolve() / "absent", "thread-1", timeout)
    assert result["error"]["code"] == "INVALID_TIMEOUT"


def test_path_and_thread_validation_are_bounded(tmp_path) -> None:
    assert (
        reader.capture_thread(Path("relative"), "thread-1")["error"]["code"]
        == "INVALID_SOCKET_PATH"
    )
    assert (
        reader.capture_thread(tmp_path.resolve(), "thread-1")["error"]["code"]
        == "INVALID_SOCKET_PATH"
    )
    assert (
        reader.capture_thread(tmp_path.resolve() / "absent", "")["error"]["code"]
        == "INVALID_THREAD_ID"
    )
    result = reader.capture_thread(tmp_path.resolve() / "secret-absent", "thread-1")
    assert result["error"]["code"] == "TRANSPORT_ERROR"
    assert "secret-absent" not in json.dumps(result)


def test_cli_captures_exact_read_response() -> None:
    with server() as (path, state):
        process = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--socket",
                str(path),
                "--thread-id",
                "thread-1",
            ],
            capture_output=True,
            check=False,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
    assert process.returncode == 0
    assert json.loads(process.stdout)["state"] == "captured"
    assert process.stderr == b""
    assert state["closed"] is True
