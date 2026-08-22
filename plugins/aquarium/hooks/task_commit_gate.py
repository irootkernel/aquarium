"""Deny direct roadmap-repository commits that bypass task-commit."""

from __future__ import annotations

import fnmatch
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


def executable_control_fragments(command: str) -> tuple[str, list[str]]:
    fragments: list[str] = []

    def single_quoted(source: str, stop: int) -> bool:
        quote: str | None = None
        escaped = False
        for char in source[:stop]:
            if escaped:
                escaped = False
            elif char == "\\" and quote != "'":
                escaped = True
            elif char in {"'", '"'}:
                if quote == char:
                    quote = None
                elif quote is None:
                    quote = char
        return quote == "'"

    function_pattern = re.compile(
        r"(?ms)\b([A-Za-z_][A-Za-z0-9_]*)\s*\(\)\s*\{(.*?)\}\s*;?"
    )

    def remove_function(match: re.Match[str]) -> str:
        if single_quoted(command, match.start()):
            return match.group(0)
        name, body = match.group(1), match.group(2)
        if re.search(
            rf"(?:^|[;&|\s]){re.escape(name)}(?:$|[;&|\s])", command[match.end() :]
        ):
            fragments.append(body)
        return " "

    remaining = function_pattern.sub(remove_function, command)

    case_pattern = re.compile(r"(?ms)\bcase\s+(\S+)\s+in\s+(.*?)\s+esac\b")

    def resolve_case(match: re.Match[str]) -> str:
        if single_quoted(remaining, match.start()):
            return match.group(0)
        word = match.group(1).strip("'\"")
        for arm in re.finditer(r"(?ms)([^)]+)\)(.*?)(?:;;|;&|;;&|$)", match.group(2)):
            patterns = [value.strip().strip("'\"") for value in arm.group(1).split("|")]
            if any(fnmatch.fnmatchcase(word, pattern) for pattern in patterns):
                fragments.append(arm.group(2))
                break
        return " "

    remaining = case_pattern.sub(resolve_case, remaining)

    substitution_pattern = re.compile(r"`([^`]*)`|\$\(([^()]*)\)", re.DOTALL)

    def remove_substitution(match: re.Match[str]) -> str:
        if single_quoted(remaining, match.start()):
            return match.group(0)
        fragments.append(match.group(1) or match.group(2))
        return " substitution "

    remaining = substitution_pattern.sub(remove_substitution, remaining)
    return remaining, fragments


def git_commit_invocation(segment: list[str], cwd: Path) -> tuple[Path, bool] | None:
    segment = list(segment)
    index = 0
    split_expansions = 0
    shell_prefixes = {"!", "(", "{", "do", "else", "if", "then", "until", "while"}
    while index < len(segment) and segment[index] in shell_prefixes:
        index += 1
    assignments: list[str] = []
    while index < len(segment) and ASSIGNMENT_PATTERN.match(segment[index]):
        assignments.append(segment[index])
        index += 1

    wrappers = {"builtin", "command", "exec", "nohup"}
    while index < len(segment) and (
        segment[index] in wrappers or segment[index] == "time"
    ):
        if segment[index] == "time":
            index += 1
            while index < len(segment) and segment[index].startswith("-"):
                index += 1
        else:
            index += 1

    while index < len(segment) and segment[index] == "env":
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
            if token.startswith("-C") and len(token) > 2:
                candidate = Path(token[2:])
                cwd = candidate if candidate.is_absolute() else cwd / candidate
                index += 1
                continue
            if token.startswith("-iC") and len(token) > 3:
                candidate = Path(token[3:])
                cwd = candidate if candidate.is_absolute() else cwd / candidate
                index += 1
                continue
            if token in {"-S", "--split-string"}:
                if index + 1 >= len(segment) or split_expansions >= 16:
                    return None
                try:
                    replacement = shlex.split(segment[index + 1], posix=True)
                except ValueError:
                    return None
                segment[index : index + 2] = replacement
                split_expansions += 1
                continue
            if token.startswith("--split-string="):
                if split_expansions >= 16:
                    return None
                try:
                    replacement = shlex.split(token.split("=", 1)[1], posix=True)
                except ValueError:
                    return None
                segment[index : index + 1] = replacement
                split_expansions += 1
                continue
            if token.startswith("-S") and len(token) > 2:
                if split_expansions >= 16:
                    return None
                try:
                    replacement = shlex.split(token[2:], posix=True)
                except ValueError:
                    return None
                segment[index : index + 1] = replacement
                split_expansions += 1
                continue
            if token in {"-u", "--unset", "-P"}:
                if index + 1 >= len(segment):
                    return None
                index += 2
                continue
            if token.startswith("--unset="):
                index += 1
                continue
            if token.startswith("-"):
                index += 1
                continue
            break

    while index < len(segment) and (
        segment[index] in wrappers or segment[index] == "time"
    ):
        if segment[index] == "time":
            index += 1
            while index < len(segment) and segment[index].startswith("-"):
                index += 1
        else:
            index += 1
    if index < len(segment) and segment[index] == "env":
        nested = git_commit_invocation(segment[index:], cwd)
        if nested is None:
            return None
        nested_cwd, nested_gated = nested
        return nested_cwd, nested_gated or GATE_ASSIGNMENT in assignments
    if index >= len(segment) or Path(segment[index]).name != "git":
        return None
    index += 1

    git_path_base = cwd
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
            git_path_base = (
                candidate if candidate.is_absolute() else git_path_base / candidate
            )
            probe_cwd = git_path_base
            index += 2
            continue
        if token in {"--git-dir", "--work-tree"}:
            if index + 1 >= len(segment):
                return None
            candidate = Path(segment[index + 1])
            candidate = (
                candidate if candidate.is_absolute() else git_path_base / candidate
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
                candidate if candidate.is_absolute() else git_path_base / candidate
            )
            index += 1
            continue
        if token.startswith("--git-dir="):
            candidate = Path(token.split("=", 1)[1])
            git_dir = (
                candidate if candidate.is_absolute() else git_path_base / candidate
            )
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

    command, fragments = executable_control_fragments(command)
    if any(
        should_deny({"tool_input": {"command": fragment}, "cwd": str(cwd)})
        for fragment in fragments
    ):
        return True

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
