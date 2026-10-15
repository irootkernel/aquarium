"""Read bounded public Codex evidence for one acceptance invocation."""

from __future__ import annotations

import json
import queue
import subprocess
import threading
import time


class ObservationError(RuntimeError):
    pass


class PublicReader:
    """One foreground native reader, with no provider turn or daemon."""

    def __init__(self, codex, cwd, timeout=60):
        self.process = subprocess.Popen(
            [codex, "app-server", "--listen", "stdio://"],
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        self.messages = queue.Queue()
        self.deadline = time.monotonic() + timeout
        self.serial = 0
        self.requests = []
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for line in self.process.stdout:
            try:
                self.messages.put(json.loads(line))
            except json.JSONDecodeError:
                continue
        self.messages.put(None)

    def __enter__(self):
        try:
            self.request(
                "initialize",
                {
                    "clientInfo": {"name": "aquarium-vm-observer", "version": "1"},
                    "capabilities": {"experimentalApi": True},
                },
            )
            self.process.stdin.write('{"method":"initialized","params":{}}\n')
            self.process.stdin.flush()
            return self
        except Exception:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, *_):
        self.process.stdin.close()
        self.process.terminate()
        try:
            self.process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        self.process.stdout.close()

    def request(self, method, params):
        self.serial += 1
        value = {"id": self.serial, "method": method, "params": params}
        self.requests.append(value)
        self.process.stdin.write(json.dumps(value) + "\n")
        self.process.stdin.flush()
        while True:
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                raise ObservationError(f"public read timed out: {method}")
            try:
                reply = self.messages.get(timeout=remaining)
            except queue.Empty as error:
                raise ObservationError(f"public read timed out: {method}") from error
            if reply is None:
                raise ObservationError("public reader exited before its response")
            if reply.get("id") != self.serial:
                continue
            if "error" in reply:
                raise ObservationError(f"{method}: {reply['error']}")
            return reply["result"]

    def pages(self, method, params):
        values = []
        while True:
            page = self.request(method, params)
            values.extend(page["data"])
            cursor = page.get("nextCursor")
            if not cursor:
                return values
            params = {**params, "cursor": cursor}

    def thread(self, identifier):
        thread = self.request(
            "thread/read", {"threadId": identifier, "includeTurns": False}
        )["thread"]
        metadata = {
            key: thread.get(key)
            for key in (
                "id",
                "parentThreadId",
                "cwd",
                "source",
                "status",
                "cliVersion",
                "agentRole",
            )
        }
        items = self.pages(
            "thread/items/list", {"threadId": identifier, "sortDirection": "asc"}
        )
        items = [entry.get("item", entry) for entry in items]
        # Public reasoning summaries and private journal paths are unnecessary.
        items = [
            item for item in items if item.get("type") not in {"reasoning", "plan"}
        ]
        turns = self.pages(
            "thread/turns/list",
            {"threadId": identifier, "itemsView": "full", "sortDirection": "asc"},
        )
        return {
            "metadata": metadata,
            "items": items,
            "turns": [
                {
                    **{key: turn.get(key) for key in ("id", "status", "error")},
                    "items": [
                        entry.get("item", entry)
                        for entry in turn.get("items", [])
                        if entry.get("item", entry).get("type")
                        not in {"reasoning", "plan"}
                    ],
                }
                for turn in turns
            ],
        }


def discover(codex, cwd):
    with PublicReader(codex, cwd) as reader:
        result = reader.request(
            "skills/list", {"cwds": [str(cwd)], "forceReload": True}
        )
    return result


def collect(codex, cwd, thread_id):
    with PublicReader(codex, cwd) as reader:
        root = reader.thread(thread_id)
        descendants = reader.pages(
            "thread/list",
            {
                "ancestorThreadId": thread_id,
                "cwd": root["metadata"]["cwd"],
                "sourceKinds": ["subAgent", "subAgentThreadSpawn", "subAgentOther"],
                "useStateDbOnly": True,
            },
        )
        identifiers = {thread["id"] for thread in descendants}
        identifiers.update(
            item["agentThreadId"]
            for item in root["items"]
            if item.get("type") == "subAgentActivity"
        )
        children = [reader.thread(identifier) for identifier in sorted(identifiers)]
        requests = reader.requests
    return {
        "schema": "aquarium.vm-native-observation/v1",
        "root": root,
        "descendants": children,
        "requests": requests,
        "reader_exit": reader.process.returncode,
    }
