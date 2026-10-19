"""Capture one fully hydrated thread from an explicitly supplied existing socket.

capture_thread(socket_path, thread_id, timeout_seconds=15) uses the public
app-server Unix WebSocket endpoint. It sends only initialize, initialized, and
thread/read(includeTurns=true); it never discovers/starts a server or creates,
resumes, or dispatches a thread. Successful captures retain exact JSON objects,
not raw wire encodings. Notifications are tolerated but are not capture evidence.

The overall I/O deadline bounds reads without imposing an evidence-size quota.
HTTP headers are limited to 16 KiB. Full itemsView is required even for paginated
history. Captures prove the supplied server's returned projection, not journal
authenticity, configuration acceptance, semantic success, or worker settlement.
Failures return bounded rejection codes without native error text or transcripts.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import os
import socket
import stat
import struct
import time
from pathlib import Path

OUTPUT_SCHEMA = "aquarium.codex-thread-capture/v1"
MAX_HEADER_BYTES = 16 * 1024
GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


class CaptureError(ValueError):
    """Bounded public-protocol rejection, with no native payload in its message."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise CaptureError(code)


def _unique_keys(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        _require(key not in result, "INVALID_JSON")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise CaptureError("INVALID_JSON")


class _WebSocket:
    def __init__(self, connection: socket.socket, deadline: float):
        self.connection = connection
        self.deadline = deadline
        self.buffer = bytearray()
        self.upgraded = False

    def remaining(self) -> float:
        remaining = self.deadline - time.monotonic()
        _require(remaining > 0, "TIMEOUT")
        return remaining

    def _receive(self) -> None:
        self.connection.settimeout(self.remaining())
        chunk = self.connection.recv(65536)
        _require(bool(chunk), "UNEXPECTED_EOF")
        self.buffer.extend(chunk)

    def _take(self, length: int) -> bytes:
        while len(self.buffer) < length:
            self._receive()
        result = bytes(self.buffer[:length])
        del self.buffer[:length]
        return result

    def _send(self, value: bytes) -> None:
        self.connection.settimeout(self.remaining())
        self.connection.sendall(value)

    def upgrade(self) -> None:
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        self._send(
            (
                "GET / HTTP/1.1\r\nHost: localhost\r\nUpgrade: websocket\r\n"
                "Connection: Upgrade\r\nSec-WebSocket-Version: 13\r\n"
                f"Sec-WebSocket-Key: {key}\r\n\r\n"
            ).encode("ascii")
        )
        while b"\r\n\r\n" not in self.buffer:
            _require(len(self.buffer) <= MAX_HEADER_BYTES, "INVALID_UPGRADE")
            self._receive()
        header, self.buffer = self.buffer.split(b"\r\n\r\n", 1)
        _require(len(header) <= MAX_HEADER_BYTES, "INVALID_UPGRADE")
        lines = bytes(header).split(b"\r\n")
        status = lines[0].split(b" ", 2)
        _require(
            len(status) >= 2 and status[:2] == [b"HTTP/1.1", b"101"], "INVALID_UPGRADE"
        )
        headers = {}
        for line in lines[1:]:
            _require(
                b":" in line and not line.startswith((b" ", b"\t")), "INVALID_UPGRADE"
            )
            name, value = line.split(b":", 1)
            name = name.lower()
            _require(name not in headers, "INVALID_UPGRADE")
            headers[name] = value.strip()
        _require(
            headers.get(b"upgrade", b"").lower() == b"websocket", "INVALID_UPGRADE"
        )
        _require(
            b"upgrade"
            in [
                part.strip().lower()
                for part in headers.get(b"connection", b"").split(b",")
            ],
            "INVALID_UPGRADE",
        )
        expected = base64.b64encode(hashlib.sha1((key + GUID).encode("ascii")).digest())
        _require(headers.get(b"sec-websocket-accept") == expected, "INVALID_UPGRADE")
        _require(
            b"sec-websocket-extensions" not in headers
            and b"sec-websocket-protocol" not in headers,
            "INVALID_UPGRADE",
        )
        self.upgraded = True

    def send_frame(self, body: bytes, opcode: int = 1) -> None:
        length = len(body)
        mask = os.urandom(4)
        marker = length if length < 126 else 126 if length < 65536 else 127
        header = bytes([0x80 | opcode, 0x80 | marker])
        if marker == 126:
            header += struct.pack("!H", length)
        elif marker == 127:
            header += struct.pack("!Q", length)
        masked = bytes(value ^ mask[index % 4] for index, value in enumerate(body))
        self._send(header + mask + masked)

    def send_json(self, value: dict) -> None:
        self.send_frame(
            json.dumps(
                value, separators=(",", ":"), ensure_ascii=True, allow_nan=False
            ).encode("ascii")
        )

    def receive_json(self) -> dict:
        fragments = []
        fragmented = False
        while True:
            first, second = self._take(2)
            final, opcode = bool(first & 0x80), first & 0x0F
            _require(not first & 0x70 and not second & 0x80, "INVALID_FRAME")
            length = second & 0x7F
            if length == 126:
                length = struct.unpack("!H", self._take(2))[0]
                _require(length >= 126, "INVALID_FRAME")
            elif length == 127:
                length = struct.unpack("!Q", self._take(8))[0]
                _require(65536 <= length < 2**63, "INVALID_FRAME")
            _require(opcode in (0, 1, 8, 9, 10), "INVALID_FRAME")
            if opcode >= 8:
                _require(final and length <= 125, "INVALID_FRAME")
            body = self._take(length)
            if opcode == 8:
                _require(length != 1, "INVALID_FRAME")
                if length >= 2:
                    code = struct.unpack("!H", body[:2])[0]
                    _require(
                        code
                        in (
                            1000,
                            1001,
                            1002,
                            1003,
                            1007,
                            1008,
                            1009,
                            1010,
                            1011,
                            1012,
                            1013,
                            1014,
                        )
                        or 3000 <= code <= 4999,
                        "INVALID_FRAME",
                    )
                    try:
                        body[2:].decode("utf-8", errors="strict")
                    except UnicodeError as error:
                        raise CaptureError("INVALID_UTF8") from error
                raise CaptureError("SERVER_CLOSED")
            if opcode == 9:
                self.send_frame(body, 10)
                continue
            if opcode == 10:
                continue
            _require(
                (opcode == 0 and fragmented) or (opcode == 1 and not fragmented),
                "INVALID_FRAME_SEQUENCE",
            )
            fragmented = not final
            fragments.append(body)
            if final:
                try:
                    message = json.loads(
                        b"".join(fragments).decode("utf-8", errors="strict"),
                        object_pairs_hook=_unique_keys,
                        parse_constant=_reject_constant,
                    )
                except UnicodeError as error:
                    raise CaptureError("INVALID_UTF8") from error
                except json.JSONDecodeError as error:
                    raise CaptureError("INVALID_JSON") from error
                _require(isinstance(message, dict), "INVALID_RPC")
                self.remaining()
                return message

    def request(self, request: dict) -> dict:
        self.send_json(request)
        while True:
            response = self.receive_json()
            if "method" in response:
                _require("id" not in response, "UNEXPECTED_SERVER_REQUEST")
                _require(
                    isinstance(response["method"], str)
                    and bool(response["method"])
                    and "result" not in response
                    and "error" not in response,
                    "INVALID_RPC",
                )
                continue
            _require(
                "id" in response
                and type(response["id"]) is type(request["id"])
                and response["id"] == request["id"],
                "RESPONSE_ID_MISMATCH",
            )
            _require(("result" in response) != ("error" in response), "INVALID_RPC")
            _require("error" not in response, "NATIVE_ERROR")
            _require(isinstance(response["result"], dict), "INVALID_RPC")
            return response


def capture_thread(
    socket_path: Path, thread_id: str, timeout_seconds: float = 15
) -> dict:
    """Capture exact successful RPC objects, or return a bounded rejection."""
    connection = None
    transport = None
    try:
        _require(
            isinstance(socket_path, Path) and socket_path.is_absolute(),
            "INVALID_SOCKET_PATH",
        )
        _require(
            isinstance(thread_id, str) and bool(thread_id.strip()), "INVALID_THREAD_ID"
        )
        _require(
            isinstance(timeout_seconds, (int, float))
            and not isinstance(timeout_seconds, bool)
            and math.isfinite(timeout_seconds)
            and timeout_seconds > 0,
            "INVALID_TIMEOUT",
        )
        deadline = time.monotonic() + timeout_seconds
        _require(stat.S_ISSOCK(socket_path.stat().st_mode), "INVALID_SOCKET_PATH")
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        transport = _WebSocket(connection, deadline)
        connection.settimeout(transport.remaining())
        connection.connect(str(socket_path))
        transport.upgrade()
        initialize = {
            "id": 1,
            "method": "initialize",
            "params": {
                "clientInfo": {"name": "aquarium-read-codex-thread", "version": "1"},
                "capabilities": {"experimentalApi": True},
            },
        }
        initialize_response = transport.request(initialize)
        initialized = {"method": "initialized", "params": {}}
        transport.send_json(initialized)
        read = {
            "id": 2,
            "method": "thread/read",
            "params": {"threadId": thread_id, "includeTurns": True},
        }
        response = transport.request(read)
        thread = response["result"].get("thread")
        _require(
            isinstance(thread, dict) and thread.get("id") == thread_id,
            "THREAD_ID_MISMATCH",
        )
        turns = thread.get("turns")
        _require(isinstance(turns, list), "INCOMPLETE_HISTORY")
        for turn in turns:
            _require(
                isinstance(turn, dict)
                and turn.get("itemsView") == "full"
                and isinstance(turn.get("items"), list),
                "INCOMPLETE_HISTORY",
            )
        transport.remaining()
        return {
            "schema": OUTPUT_SCHEMA,
            "state": "captured",
            "initialize": {"request": initialize, "response": initialize_response},
            "initialized": initialized,
            "thread_read": {"request": read, "response": response},
        }
    except CaptureError as error:
        return {
            "schema": OUTPUT_SCHEMA,
            "state": "rejected",
            "error": {"code": error.code},
        }
    except TimeoutError:
        return {
            "schema": OUTPUT_SCHEMA,
            "state": "rejected",
            "error": {"code": "TIMEOUT"},
        }
    except OSError:
        return {
            "schema": OUTPUT_SCHEMA,
            "state": "rejected",
            "error": {"code": "TRANSPORT_ERROR"},
        }
    finally:
        if transport is not None and transport.upgraded:
            try:
                transport.send_frame(b"", 8)
            except (OSError, CaptureError):
                pass
        if connection is not None:
            try:
                connection.close()
            except OSError:
                pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--socket",
        required=True,
        type=Path,
        help="explicit existing absolute Unix socket path",
    )
    parser.add_argument("--thread-id", required=True, help="actual native thread ID")
    args = parser.parse_args()
    capture = capture_thread(args.socket, args.thread_id)
    print(
        json.dumps(
            capture,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    )
    return 0 if capture["state"] == "captured" else 2


if __name__ == "__main__":
    raise SystemExit(main())
