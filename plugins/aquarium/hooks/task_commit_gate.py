"""Deny direct roadmap-repository commits that bypass task-commit."""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

GATE_ASSIGNMENT = "AQUARIUM_COMMIT_GATE=task-commit-v1"
LIFECYCLE_PATTERN = re.compile(
    r"\b(?:In[ \t]+Progress|In[ \t]+Review|Completed|Blocked|Deferred)\b"
)
SEPARATOR_CHARS = frozenset(";&|\n")
ASSIGNMENT_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=.*$", re.DOTALL)
OPTIONS_WITH_VALUES = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}


def heredoc_specs(
    line: str, initial_quote: str | None
) -> tuple[list[tuple[str, bool]], str | None]:
    specs: list[tuple[str, bool]] = []
    index = 0
    quote = initial_quote
    while index < len(line):
        char = line[index]
        if quote is not None:
            if char == "\\" and quote == '"' and index + 1 < len(line):
                index += 2
                continue
            if char == quote:
                quote = None
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            index += 1
            continue
        if char == "\\":
            index += 2
            continue
        if not line.startswith("<<", index) or line.startswith("<<<", index):
            index += 1
            continue

        cursor = index + 2
        strip_tabs = cursor < len(line) and line[cursor] == "-"
        cursor += int(strip_tabs)
        while cursor < len(line) and line[cursor] in " \t":
            cursor += 1
        if cursor >= len(line) or line[cursor] in "\r\n":
            index += 2
            continue

        delimiter_quote = line[cursor] if line[cursor] in {"'", '"'} else None
        if delimiter_quote is not None:
            cursor += 1
            end = cursor
            while end < len(line) and line[end] != delimiter_quote:
                end += 1
            if end >= len(line):
                index += 2
                continue
            delimiter = line[cursor:end]
            index = end + 1
        else:
            end = cursor
            while end < len(line) and line[end] not in " \t\r\n;&|<>()":
                end += 1
            delimiter = line[cursor:end].replace("\\", "")
            index = end
        if delimiter:
            specs.append((delimiter, strip_tabs))
    return specs, quote


def without_heredoc_bodies(command: str) -> str:
    output: list[str] = []
    pending: list[tuple[str, bool]] = []
    quote: str | None = None
    for line in command.splitlines(keepends=True):
        if pending:
            delimiter, strip_tabs = pending[0]
            body_line = line.rstrip("\r\n")
            comparison = body_line.lstrip("\t") if strip_tabs else body_line
            output.append("\n" if line.endswith(("\n", "\r")) else "")
            if comparison == delimiter:
                pending.pop(0)
            continue
        output.append(line)
        specs, quote = heredoc_specs(line, quote)
        pending.extend(specs)
    return "".join(output)


def shell_segments(command: str) -> list[list[str]]:
    source = without_heredoc_bodies(command)
    source = source.replace("\\\r\n", "").replace("\\\n", "")
    lexer = shlex.shlex(source, posix=True, punctuation_chars=";&|\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    lexer.commenters = ""

    segments: list[list[str]] = []
    current: list[str] = []
    try:
        tokens = iter(lexer)
        for token in tokens:
            if token and all(char in SEPARATOR_CHARS for char in token):
                if current:
                    segments.append(current)
                    current = []
                continue
            current.append(token)
    except ValueError:
        if current:
            segments.append(current)
        return segments
    if current:
        segments.append(current)
    return segments


def git_commit_invocation(segment: list[str], cwd: Path) -> tuple[Path, bool] | None:
    index = 0
    assignments: list[str] = []
    while index < len(segment) and ASSIGNMENT_PATTERN.match(segment[index]):
        assignments.append(segment[index])
        index += 1

    if index < len(segment) and segment[index] == "env":
        index += 1
        while index < len(segment):
            token = segment[index]
            if token == "--":
                index += 1
                break
            if ASSIGNMENT_PATTERN.match(token):
                assignments.append(token)
                index += 1
                continue
            if token in {"-C", "--chdir"}:
                if index + 1 >= len(segment):
                    return None
                candidate = Path(segment[index + 1])
                cwd = candidate if candidate.is_absolute() else cwd / candidate
                index += 2
                continue
            if token.startswith("--chdir="):
                candidate = Path(token.split("=", 1)[1])
                cwd = candidate if candidate.is_absolute() else cwd / candidate
                index += 1
                continue
            if token in {"-u", "--unset", "-P", "--split-string"}:
                if index + 1 >= len(segment):
                    return None
                index += 2
                continue
            if token.startswith(("--unset=", "--split-string=")):
                index += 1
                continue
            if token.startswith("-"):
                index += 1
                continue
            break

    if index < len(segment) and segment[index] == "command":
        index += 1
    if index >= len(segment) or Path(segment[index]).name != "git":
        return None
    index += 1

    option_base = cwd
    probe_cwd = cwd
    git_dir: Path | None = None
    while index < len(segment):
        token = segment[index]
        if token == "commit":
            if git_dir is not None:
                try:
                    resolved_git_dir = git_dir.resolve()
                except OSError:
                    return None
                if resolved_git_dir.name == ".git":
                    probe_cwd = resolved_git_dir.parent
            return probe_cwd, GATE_ASSIGNMENT in assignments
        if token == "--":
            return None
        if token == "-C":
            if index + 1 >= len(segment):
                return None
            candidate = Path(segment[index + 1])
            probe_cwd = candidate if candidate.is_absolute() else probe_cwd / candidate
            index += 2
            continue
        if token in {"--git-dir", "--work-tree"}:
            if index + 1 >= len(segment):
                return None
            candidate = Path(segment[index + 1])
            candidate = (
                candidate if candidate.is_absolute() else option_base / candidate
            )
            if token == "--work-tree":
                probe_cwd = candidate
            else:
                git_dir = candidate
            index += 2
            continue
        if token.startswith("--work-tree="):
            candidate = Path(token.split("=", 1)[1])
            probe_cwd = (
                candidate if candidate.is_absolute() else option_base / candidate
            )
            index += 1
            continue
        if token.startswith("--git-dir="):
            candidate = Path(token.split("=", 1)[1])
            git_dir = candidate if candidate.is_absolute() else option_base / candidate
            index += 1
            continue
        if token in OPTIONS_WITH_VALUES or token.startswith("--namespace="):
            index += 2 if token in OPTIONS_WITH_VALUES else 1
            continue
        if token.startswith("-"):
            index += 1
            continue
        return None
    return None


def git_output(cwd: Path, *args: str) -> bytes | None:
    try:
        result = subprocess.run(
            ["git", "-C", os.fspath(cwd), *args],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout if result.returncode == 0 else None


def repository_root(cwd: Path) -> Path | None:
    output = git_output(cwd, "rev-parse", "--show-toplevel")
    if output is None:
        return None
    return Path(os.fsdecode(output).strip()).resolve()


def is_roadmap_repository(root: Path) -> bool:
    output = git_output(root, "ls-files", "-z")
    if output is None:
        return False
    for raw_path in output.split(b"\0"):
        if not raw_path:
            continue
        relative = os.fsdecode(raw_path)
        if not any(
            "roadmap" in part.casefold() for part in PurePosixPath(relative).parts
        ):
            continue
        candidate = root / relative
        try:
            if candidate.is_symlink() or not candidate.is_file():
                continue
            candidate.resolve().relative_to(root)
            with candidate.open(encoding="utf-8", errors="ignore") as roadmap_file:
                content = roadmap_file.read(2_000_000)
            if LIFECYCLE_PATTERN.search(content):
                return True
        except (OSError, ValueError):
            continue
    return False


def deny_payload() -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "This roadmap repository requires commits through "
                "$aquarium:task-commit. Resume the active Aquarium handler or "
                "invoke that skill to reconcile task status before committing."
            ),
        }
    }


def should_deny(payload: dict[str, Any]) -> bool:
    command = payload.get("tool_input", {}).get("command")
    if not isinstance(command, str):
        return False
    cwd_value = payload.get("cwd")
    cwd = Path(cwd_value) if isinstance(cwd_value, str) else Path.cwd()

    probe_base = cwd
    for segment in shell_segments(command):
        if segment and segment[0] == "cd" and len(segment) == 2:
            candidate = Path(segment[1])
            probe_base = (
                candidate if candidate.is_absolute() else probe_base / candidate
            )
            continue
        invocation = git_commit_invocation(segment, probe_base)
        if invocation is None:
            continue
        probe_cwd, gated = invocation
        if gated:
            continue
        root = repository_root(probe_cwd)
        if root is not None and is_roadmap_repository(root):
            return True
    return False


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0
    if isinstance(payload, dict) and should_deny(payload):
        json.dump(deny_payload(), sys.stdout, separators=(",", ":"))
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
